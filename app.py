import hashlib
import json
import logging
import math
import os
import re
import shutil
import sqlite3
import stat
import tempfile
import threading
import time
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote

from flask import Flask, Response, abort, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest

import collector
import catalog_backup
import dependencies
import playlist_files


DEFAULTS = {"download_mode": "compact", "quality": "720", "shorts": "include", "audio": "original",
            "subtitles": "both", "auto_subtitles": True}
CHOICES = {"download_mode": {"compact", "original"},
           "quality": {"360", "480", "720", "1080", "1440", "2160", "best"},
           "shorts": {"include", "exclude", "only"}, "audio": {"original", "pt-BR", "en"},
           "subtitles": {"none", "pt-BR", "en", "both"}}
COLLECTION_ICONS = {"folder", "list", "book", "film", "music", "gamepad", "star", "compass", "tools"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), prefs TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS system_event (
    id INTEGER PRIMARY KEY, timestamp INTEGER NOT NULL, area TEXT NOT NULL,
    code TEXT NOT NULL, severity TEXT NOT NULL, detail TEXT
);
CREATE TABLE IF NOT EXISTS channel (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, folder TEXT NOT NULL, source TEXT UNIQUE,
    overrides TEXT NOT NULL, auto INTEGER DEFAULT 0, next_sync INTEGER NOT NULL DEFAULT 0,
    baseline INTEGER NOT NULL DEFAULT 0, title_filter TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS playlist (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS channel_style (
    id TEXT PRIMARY KEY REFERENCES channel(id) ON DELETE CASCADE,
    icon TEXT NOT NULL, color TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS playlist_style (
    id TEXT PRIMARY KEY REFERENCES playlist(id) ON DELETE CASCADE,
    icon TEXT NOT NULL, color TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS video (
    id TEXT PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL,
    channel_id TEXT REFERENCES channel(id), kind TEXT NOT NULL,
    state TEXT NOT NULL, prefs TEXT NOT NULL, capture_overrides TEXT NOT NULL DEFAULT '{}',
    metadata TEXT, folder TEXT,
    pending_folder TEXT, pending_channel TEXT, percent INTEGER DEFAULT 0, error TEXT,
    progress_phase TEXT, progress_estimated INTEGER NOT NULL DEFAULT 0,
    position REAL DEFAULT 0, watched_at INTEGER, created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS playlist_item (
    playlist_id TEXT NOT NULL REFERENCES playlist(id) ON DELETE CASCADE,
    video_id TEXT NOT NULL REFERENCES video(id) ON DELETE CASCADE,
    PRIMARY KEY(playlist_id, video_id)
);
CREATE TABLE IF NOT EXISTS scan (
    source TEXT PRIMARY KEY, name TEXT, state TEXT NOT NULL, error TEXT,
    playlists_state TEXT NOT NULL DEFAULT 'idle'
);
CREATE TABLE IF NOT EXISTS entry (
    source TEXT NOT NULL, id TEXT NOT NULL, title TEXT NOT NULL, kind TEXT NOT NULL,
    duration REAL, url TEXT NOT NULL, ordinal INTEGER NOT NULL, PRIMARY KEY(source,id)
);
CREATE TABLE IF NOT EXISTS source_playlist (
    source TEXT NOT NULL, id TEXT NOT NULL, title TEXT NOT NULL, ordinal INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'idle', error TEXT, PRIMARY KEY(source,id)
);
CREATE TABLE IF NOT EXISTS playlist_entry (
    source TEXT NOT NULL, playlist_id TEXT NOT NULL, video_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
    PRIMARY KEY(source,playlist_id,video_id)
);
CREATE INDEX IF NOT EXISTS playlist_entry_video ON playlist_entry(source,video_id);
CREATE INDEX IF NOT EXISTS playlist_item_video ON playlist_item(video_id,playlist_id);
CREATE TABLE IF NOT EXISTS seen (
    channel_id TEXT NOT NULL REFERENCES channel(id) ON DELETE CASCADE, id TEXT NOT NULL,
    PRIMARY KEY(channel_id,id)
);
CREATE TABLE IF NOT EXISTS channel_profile (
    source TEXT PRIMARY KEY, profile TEXT NOT NULL, asset_key TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS channel_description (
    channel_id TEXT PRIMARY KEY REFERENCES channel(id) ON DELETE CASCADE, description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS track_job (
    video_id TEXT NOT NULL REFERENCES video(id) ON DELETE CASCADE,
    kind TEXT NOT NULL, code TEXT NOT NULL, allow_auto INTEGER NOT NULL,
    exact INTEGER NOT NULL, state TEXT NOT NULL, resolved TEXT, error TEXT, retry_at INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(video_id,kind,code)
);
CREATE INDEX IF NOT EXISTS track_pending ON track_job(state);
CREATE INDEX IF NOT EXISTS video_state ON video(state,created);
CREATE INDEX IF NOT EXISTS video_channel_recent ON video(state,channel_id,created);
CREATE INDEX IF NOT EXISTS video_resume ON video(state,watched_at) WHERE position>0;
CREATE INDEX IF NOT EXISTS entry_order ON entry(source,ordinal);
"""


def encode(value):
    return json.dumps(value, ensure_ascii=False)


def preferences(data, partial=False):
    if not isinstance(data, dict):
        raise ValueError("invalid_preferences")
    values = {}
    for key, value in data.items():
        if key not in DEFAULTS:
            raise ValueError("invalid_preferences")
        if partial and value is None:
            continue
        if key == "auto_subtitles":
            valid = type(value) is bool
        else:
            valid = isinstance(value, str) and value in CHOICES[key]
        if not valid:
            raise ValueError("invalid_preferences")
        values[key] = value
    return values if partial else {**DEFAULTS, **values}


def capture_preferences(data):
    overrides = preferences(data, partial=True)
    if "shorts" in overrides:
        raise ValueError("invalid_preferences")
    return overrides


def label(value):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 100:
        raise ValueError("invalid_name")
    return value.strip()


def checked_rule(value):
    if not isinstance(value, str) or len(value) > 120:
        raise ValueError("invalid_title_filter")
    return value.strip()


def allowed(kind, mode):
    return mode == "include" or (kind == "shorts") == (mode == "only")


def valid_selection(items):
    return isinstance(items, list) and all(isinstance(item, str) and collector.VIDEO_ID.fullmatch(item)
                                           for item in items)


def timestamp():
    return int(time.time())


def collection_appearance(value, default_icon="folder"):
    if not isinstance(value, dict):
        raise ValueError("invalid_appearance")
    icon, color = value.get("icon", default_icon), value.get("color", "#bebebe")
    if (not isinstance(icon, str) or icon not in COLLECTION_ICONS
            or not isinstance(color, str) or not re.fullmatch(r"#[a-fA-F0-9]{6}", color)):
        raise ValueError("invalid_appearance")
    return {"icon": icon, "color": color.lower()}


def save_collection_appearance(db, table, item_id, value, default_icon="folder"):
    style = collection_appearance(value, default_icon)
    db.execute(f"""INSERT INTO {table} (id,icon,color) VALUES (?,?,?)
        ON CONFLICT(id) DO UPDATE SET icon=excluded.icon,color=excluded.color""",
               (item_id, style["icon"], style["color"]))


def system_event(db, area, code, detail=None, severity="info"):
    if detail:
        detail = re.sub(r"https?://\S+", "[URL]", str(detail))[-1200:]
    db.execute("INSERT INTO system_event(timestamp,area,code,severity,detail) VALUES (?,?,?,?,?)",
               (timestamp(), area, code, severity, detail))
    db.execute("DELETE FROM system_event WHERE id <= (SELECT max(id)-100 FROM system_event)")


class Archive:
    def __init__(self, data, root):
        self.data = Path(data).resolve()
        self.library = Path(root).resolve() / "library"
        self.work = self.library.parent / "work"
        self.playlist_directory = self.library.parent / "Playlists"
        self.exporting = Counter()
        self.preparing_playback = Counter()
        self.maintenance = self.data / "maintenance"
        self.pending_maintenance = self.maintenance / "pending.json"
        self.maintenance_lock = threading.Lock()
        self.branding = self.data / "branding"
        self.playback = self.work / "playback"
        self.playback_budget = max(1, int(os.environ.get("GRIDTUBE_PLAYBACK_CACHE_MIB", "4096"))) * 1024 ** 2
        self.playback_lock = threading.Lock()
        self.dependency_lock = threading.Lock()
        for path in (self.data, self.library, self.work, self.branding, self.playback):
            path.mkdir(parents=True, exist_ok=True)
        self.changed = threading.Event()
        self.capture_cancelled = threading.Event()
        self.catalog = ThreadPoolExecutor(max_workers=1, thread_name_prefix="catalog")
        self.playlist_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="playlist-scan")
        self.origins = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-origin")
        self.titles = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-title")
        self.origin_lock = threading.Lock()
        self.origin_attempts = {}
        self.files_lock = threading.Lock()
        with self.db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript(SCHEMA)
            if "title_filter" not in {row["name"] for row in db.execute("PRAGMA table_info(channel)")}:
                db.execute("ALTER TABLE channel ADD COLUMN title_filter TEXT NOT NULL DEFAULT ''")
            if "playlists_state" not in {row["name"] for row in db.execute("PRAGMA table_info(scan)")}:
                db.execute("ALTER TABLE scan ADD COLUMN playlists_state TEXT NOT NULL DEFAULT 'idle'")
                db.execute("UPDATE scan SET state='stale' WHERE state='ready'")
            db.execute("UPDATE scan SET playlists_state='idle' WHERE playlists_state='loading'")
            db.execute("UPDATE source_playlist SET state='idle' WHERE state='loading'")
            columns = {row["name"] for row in db.execute("PRAGMA table_info(video)")}
            if "capture_overrides" not in columns:
                db.execute("ALTER TABLE video ADD COLUMN capture_overrides TEXT NOT NULL DEFAULT '{}'")
            if "progress_phase" not in columns:
                db.execute("ALTER TABLE video ADD COLUMN progress_phase TEXT")
            if "progress_estimated" not in columns:
                db.execute("ALTER TABLE video ADD COLUMN progress_estimated INTEGER NOT NULL DEFAULT 0")
            track_columns = {row["name"] for row in db.execute("PRAGMA table_info(track_job)")}
            if "retry_at" not in track_columns:
                db.execute("ALTER TABLE track_job ADD COLUMN retry_at INTEGER NOT NULL DEFAULT 0")
            db.execute("INSERT OR IGNORE INTO settings VALUES (1,?)", (encode(DEFAULTS),))
            if collector.DEPENDENCY_STARTUP_ERROR:
                system_event(db, "dependency", collector.DEPENDENCY_STARTUP_ERROR, severity="error")
            db.execute("UPDATE scan SET state='error', error='interrupted' WHERE state='loading'")
            self.recover_downloads(db)
            db.execute("""UPDATE video SET state='queued',percent=0,error=NULL,progress_phase=NULL,progress_estimated=0
                          WHERE state='failed' AND (lower(error) LIKE '%unable to download video subtitles%'
                            OR error LIKE '%Postprocessing: Conversion failed!%')""")
        self.apply_pending_maintenance()
        self.refresh_playlist_files()

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.data / "library.sqlite", timeout=15)
        db.row_factory = sqlite3.Row
        db.create_function("fold", 1, str.casefold, deterministic=True)
        db.create_function("title_key", 1, collector.title_key, deterministic=True)
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def defaults(self, db):
        return {**DEFAULTS, **json.loads(db.execute("SELECT prefs FROM settings").fetchone()["prefs"])}

    def playlist_rows(self, db, playlist_id):
        return db.execute("""SELECT v.id,v.folder,v.metadata FROM playlist_item p
            JOIN video v ON v.id=p.video_id WHERE p.playlist_id=? AND v.state='ready'
            ORDER BY v.created DESC,v.rowid DESC""", (playlist_id,)).fetchall()

    @staticmethod
    def playlist_asset(bundle, filename):
        if not isinstance(filename, str) or not filename or filename in {".", ".."} or re.search(r"[/\\:\r\n\0]", filename):
            raise ValueError("playlist_media_missing")
        path = bundle / filename
        if path.resolve() != path:
            raise ValueError("playlist_media_missing")
        return path

    def refresh_playlist_files(self, playlist_ids=None):
        if playlist_ids == []:
            return
        try:
            self.playlist_directory.mkdir(exist_ok=True)
        except OSError:
            logging.exception("Could not create the on-disk playlist directory")
            with self.db() as db:
                system_event(db, "library", "playlist_write_failed", severity="error")
            return
        with self.db() as db:
            if playlist_ids is None:
                playlist_ids = [row["id"] for row in db.execute("SELECT id FROM playlist")]
            for playlist_id in playlist_ids:
                playlist = db.execute("SELECT name FROM playlist WHERE id=?", (playlist_id,)).fetchone()
                if not playlist:
                    continue
                try:
                    paths = []
                    for row in self.playlist_rows(db, playlist_id):
                        video = self.playlist_asset(self.video_bundle(row), json.loads(row["metadata"])["filename"])
                        paths.append((Path("../..") / video.relative_to(self.library.parent)).as_posix())
                    folder = self.playlist_directory / f"{collector.safe_name(playlist['name'])} [{playlist_id}]"
                    if folder.resolve() != folder:
                        raise ValueError("playlist_write_failed")
                    playlist_files.write_m3u(folder, paths)
                except (OSError, KeyError, ValueError, TypeError, RuntimeError):
                    logging.exception("Could not update the on-disk playlist %s", playlist_id)
                    system_event(db, "library", "playlist_write_failed", playlist_id, "error")

    def refresh_video_playlists(self, video_id):
        with self.db() as db:
            ids = [row["playlist_id"] for row in db.execute(
                "SELECT playlist_id FROM playlist_item WHERE video_id=?", (video_id,))]
        self.refresh_playlist_files(ids)

    def export_playlist(self, playlist_id):
        with self.files_lock, self.db() as db:
            if self.pending_maintenance.exists():
                raise ValueError("maintenance_pending")
            playlist = db.execute("SELECT name FROM playlist WHERE id=?", (playlist_id,)).fetchone()
            if not playlist:
                abort(404)
            paths, files, ids = [], [], []
            for row in self.playlist_rows(db, playlist_id):
                bundle = self.video_bundle(row)
                meta = json.loads(row["metadata"])
                video = self.playlist_asset(bundle, meta["filename"])
                if not video.is_file():
                    raise ValueError("playlist_media_missing")
                prefix = Path("Videos") / f"{len(ids) + 1:04d} - {bundle.name}"
                paths.append((prefix / video.name).as_posix())
                files.append((video, paths[-1]))
                sidecars = {"video.json", meta.get("thumbnail"), *meta.get("subtitles", {}).values(),
                            *meta.get("audio_tracks", {}).values()} - {None, video.name}
                for name in sorted(sidecars):
                    source = self.playlist_asset(bundle, name)
                    if source.is_file():
                        files.append((source, (prefix / name).as_posix()))
                ids.append(row["id"])
            self.exporting.update(ids)

        def release():
            with self.files_lock:
                self.exporting.subtract(ids)
                for video_id in ids:
                    if self.exporting[video_id] <= 0:
                        del self.exporting[video_id]

        filename = quote(collector.safe_name(playlist["name"]) + ".zip")
        response = Response(playlist_files.export_zip(paths, files), mimetype="application/zip",
                            headers={"Content-Disposition": f"attachment; filename=playlist.zip; filename*=UTF-8''{filename}",
                                     "Cache-Control": "no-store"})
        response.call_on_close(release)
        return response

    def validate_backup_row(self, table, row):
        if table == "settings":
            if row["id"] != 1:
                raise ValueError("backup_invalid")
            preferences(json.loads(row["prefs"]))
        elif table in {"channel", "playlist"}:
            if not re.fullmatch(r"[a-f0-9]{10}", row["id"]):
                raise ValueError("backup_invalid")
            label(row["name"])
            if table == "channel":
                folder = self.playlist_asset(self.library, row["folder"])
                if not folder.name.endswith(f" [{row['id']}]"):
                    raise ValueError("backup_invalid")
                if row["source"] and collector.youtube_url(row["source"], "channel")[0] != row["source"]:
                    raise ValueError("backup_invalid")
                preferences(json.loads(row["overrides"]), partial=True)
                checked_rule(row["title_filter"])
        elif table in {"channel_style", "playlist_style"}:
            collection_appearance(row)
        elif table == "track_job":
            if row["kind"] not in {"audio", "subtitle"} or not collector.LANGUAGE_TAG.fullmatch(row["code"]):
                raise ValueError("backup_invalid")
            if row["state"] == "running":
                row["state"] = "queued"
        elif table == "video":
            return self.validate_backup_video(row)
        return False

    def validate_backup_video(self, row):
        if collector.youtube_url(row["url"], "video")[1] != row["id"]:
            raise ValueError("backup_invalid")
        if row["state"] not in {"ready", "removed", "queued", "running", "failed", "cancelling"}:
            raise ValueError("backup_invalid")
        prefs = json.loads(row["prefs"])
        rule = checked_rule(prefs.pop("title_filter", ""))
        prefs = preferences(prefs)
        if rule:
            prefs["title_filter"] = rule
        row["prefs"] = encode(prefs)
        capture_preferences(json.loads(row["capture_overrides"]))
        row["pending_folder"] = row["pending_channel"] = None
        if row["state"] == "running":
            row.update(state="queued", percent=0, progress_phase=None, progress_estimated=0)
        if row["state"] == "cancelling":
            row.update(state="failed", error="download_cancelled", progress_phase=None, progress_estimated=0)
        if row["state"] in {"ready", "removed"}:
            bundle = self.video_bundle(row)
            meta = json.loads(row["metadata"])
            picture = self.playlist_asset(bundle, meta["filename"])
            for name in (meta.get("thumbnail"), *meta.get("audio_tracks", {}).values(), *meta.get("subtitles", {}).values()):
                if name is not None:
                    self.playlist_asset(bundle, name)
            source = meta.get("source_channel_url")
            if source and collector.youtube_url(source, "channel")[0] != source:
                raise ValueError("backup_invalid")
            if row["state"] == "ready" and not picture.is_file():
                row.update(state="removed", error="external_media_missing")
                return True
        return False

    def preview_backup(self, upload):
        with self.maintenance_lock:
            if self.pending_maintenance.exists():
                raise ValueError("maintenance_pending")
            self.maintenance.mkdir(exist_ok=True)
            token = uuid.uuid4().hex
            with tempfile.TemporaryDirectory(dir=self.maintenance) as scratch:
                candidate = Path(scratch) / "catalog.sqlite3"
                try:
                    counts = catalog_backup.load_backup(upload, candidate, SCHEMA, self.validate_backup_row)
                except (sqlite3.Error, ValueError, AttributeError, KeyError, TypeError) as exc:
                    raise ValueError("backup_invalid") from exc
                for previous in self.maintenance.glob("preview-*.sqlite3"):
                    previous.unlink(missing_ok=True)
                candidate.rename(self.maintenance / f"preview-{token}.sqlite3")
            return {"token": token, **counts}

    def stage_maintenance(self, operation):
        with self.maintenance_lock, self.files_lock:
            if self.pending_maintenance.exists():
                raise ValueError("maintenance_pending")
            if self.exporting:
                raise ValueError("playlist_export_busy")
            if self.preparing_playback:
                raise ValueError("playback_busy")
            token = operation.get("token")
            if operation["action"] == "restore" and not self.backup_candidate(token).is_file():
                raise ValueError("backup_preview_missing")
            self.maintenance.mkdir(exist_ok=True)
            staged = self.maintenance / "pending.tmp"
            staged.write_text(encode(operation), encoding="utf-8")
            staged.replace(self.pending_maintenance)

    def backup_candidate(self, token):
        if not isinstance(token, str) or not re.fullmatch(r"[a-f0-9]{32}", token):
            raise ValueError("backup_preview_missing")
        return self.maintenance / f"preview-{token}.sqlite3"

    def apply_pending_maintenance(self):
        if not self.pending_maintenance.is_file():
            return
        candidate = None
        operation = {}
        try:
            operation = json.loads(self.pending_maintenance.read_text(encoding="utf-8"))
            action = operation["action"]
            if action == "restore":
                candidate = self.backup_candidate(operation["token"])
                if not candidate.is_file():
                    raise ValueError("backup_preview_missing")
                targets = [self.playlist_directory]
            elif action == "reset":
                targets = [self.branding, self.playlist_directory, self.work]
                if operation["disk"] is True:
                    targets.append(self.library)
            else:
                raise ValueError("backup_invalid")
            if any(path.resolve() != path for path in targets):
                raise ValueError("maintenance_invalid_path")
            with self.db() as db:
                catalog_backup.replace_catalog(db, candidate)
                db.execute("INSERT OR IGNORE INTO settings VALUES (1,?)", (encode(DEFAULTS),))
                if candidate:
                    catalog_backup.verify_restored_catalog(db)
            for path in targets:
                if path.exists():
                    shutil.rmtree(path)
                path.mkdir()
            self.playback.mkdir(exist_ok=True)
            with self.db() as db:
                if candidate:
                    db.execute("ATTACH DATABASE ? AS restored", (str(candidate),))
                    catalog_backup.verify_restored_catalog(db)
                system_event(db, "system", "backup_restored" if action == "restore" else "data_reset",
                             operation.get("token"))
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
            logging.exception("Could not complete the staged maintenance operation")
            with self.db() as db:
                system_event(db, "system", "maintenance_failed", exc, "error")
                if isinstance(operation, dict) and operation.get("action") == "restore":
                    system_event(db, "system", "backup_restore_failed", operation.get("token"), "error")
        finally:
            self.pending_maintenance.unlink(missing_ok=True)
            for preview in self.maintenance.glob("preview-*.sqlite3"):
                preview.unlink(missing_ok=True)

    def update_dependency(self):
        try:
            selected = dependencies.install_latest(self.data, collector.YT_DLP_VERSION)
            with self.db() as db:
                system_event(db, "dependency", "dependency_staged" if selected else "dependency_current", selected)
        except Exception as exc:
            logging.exception("yt-dlp update failed")
            with self.db() as db:
                system_event(db, "dependency", "dependency_failed", getattr(exc, "stderr", None) or exc, "error")
        finally:
            self.dependency_lock.release()

    def dependency_status(self):
        selected, problem = None, collector.DEPENDENCY_STARTUP_ERROR
        try:
            selected = dependencies.installed(self.data)
        except (OSError, ValueError):
            problem = "dependency_load_failed"
        pending = selected if selected and dependencies.order(selected) > dependencies.order(collector.YT_DLP_VERSION) else None
        return {"active": collector.YT_DLP_VERSION, "bundled": dependencies.BUNDLED,
                "pending": pending, "problem": problem,
                "updating": self.dependency_lock.locked(),
                "can_restart": os.environ.get("GRIDTUBE_RESTART_IN_DOCKER") == "1"}

    def channel(self, db, channel_id):
        if channel_id is None or channel_id == "":
            return None
        if not isinstance(channel_id, str) or not re.fullmatch(r"[a-f0-9]{10}", channel_id):
            raise ValueError("invalid_channel")
        row = db.execute("SELECT * FROM channel WHERE id=?", (channel_id,)).fetchone()
        if row is None:
            abort(404)
        return row

    def effective(self, db, channel):
        prefs = {**self.defaults(db), **(json.loads(channel["overrides"]) if channel else {})}
        if channel and channel["title_filter"]:
            prefs["title_filter"] = channel["title_filter"]
        return prefs

    def create_channel(self, db, name, source=None, overrides=None, auto=False, title_filter=""):
        channel_id = uuid.uuid4().hex[:10]
        folder = f"{collector.safe_name(name)} [{channel_id}]"
        db.execute("INSERT INTO channel (id,name,folder,source,overrides,auto,title_filter) VALUES (?,?,?,?,?,?,?)",
                   (channel_id, name, folder, source, encode(overrides or {}), int(auto), title_filter))
        return self.channel(db, channel_id)

    def enqueue(self, db, entry, channel, prefs, capture_overrides=None):
        rule = prefs.get("title_filter")
        if (rule and entry["title"] not in {entry["url"], entry["id"]}
                and collector.title_key(rule) not in collector.title_key(entry["title"])):
            return 0
        cursor = db.execute(
            """INSERT INTO video (id,url,title,channel_id,kind,prefs,capture_overrides,state,created)
               VALUES (?,?,?,?,?,?,?,'queued',?) ON CONFLICT(id) DO NOTHING""",
            (entry["id"], entry["url"], entry["title"], channel["id"] if channel else None,
             entry["kind"], encode(prefs), encode(capture_overrides or {}), timestamp()))
        return cursor.rowcount

    def backfill_download_titles(self):
        with self.db() as db:
            pending = db.execute("""SELECT id FROM video WHERE state IN ('queued','running','failed')
                AND title IN (url,id) ORDER BY created,rowid""").fetchall()
        for row in pending:
            self.titles.submit(self.lookup_download_title, row["id"])

    def lookup_download_title(self, video_id):
        with self.db() as db:
            unresolved = db.execute("""SELECT 1 FROM video WHERE id=? AND state IN ('queued','running','failed')
                AND title IN (url,id)""", (video_id,)).fetchone()
        if unresolved and (title := collector.read_video_title(video_id)):
            self.remember_download_title(video_id, title)

    def remember_download_title(self, video_id, title):
        with self.db() as db:
            db.execute("""UPDATE video SET title=? WHERE id=? AND state IN ('queued','running','failed')
                AND title IN (url,id)""", (title, video_id))

    def scan_source(self, source):
        try:
            found_tab = False
            batch = []
            scanned_ids = []
            entries = collector.channel_entries(source, profile=lambda profile: self.save_profile(source, profile))
            for ordinal, (name, entry) in enumerate(entries):
                if entry is None:
                    found_tab = True
                    with self.db() as db:
                        db.execute("UPDATE scan SET name=? WHERE source=?", (name, source))
                else:
                    scanned_ids.append((entry["id"],))
                    batch.append((source, entry["id"], entry["title"], entry["kind"],
                                  entry["duration"], entry["url"], ordinal))
                    if len(batch) >= 25:
                        self.write_entries(batch)
                        batch.clear()
            if batch:
                self.write_entries(batch)
            with self.db() as db:
                if found_tab:
                    db.execute("CREATE TEMP TABLE scanned (id TEXT PRIMARY KEY)")
                    db.executemany("INSERT OR IGNORE INTO scanned VALUES (?)", scanned_ids)
                    db.execute("""DELETE FROM entry WHERE source=? AND id NOT IN (SELECT id FROM scanned)
                        AND NOT EXISTS (SELECT 1 FROM playlist_entry p WHERE p.source=entry.source AND p.video_id=entry.id)""",
                               (source,))
                db.execute("UPDATE scan SET state=?, error=? WHERE source=?",
                           ("ready" if found_tab else "error", None if found_tab else "empty_catalog", source))
        except Exception as exc:
            logging.exception("Catalog scan failed")
            with self.db() as db:
                db.execute("UPDATE scan SET state='error', error=? WHERE source=?", (str(exc)[-400:], source))
                system_event(db, "catalog", "catalog_failed", exc, "error")

    def discover_playlists(self, source):
        try:
            entries = list(dict.fromkeys(collector.channel_playlists(source)))
            with self.db() as db:
                db.executemany("""INSERT INTO source_playlist (source,id,title,ordinal)
                    VALUES (?,?,?,?) ON CONFLICT(source,id) DO UPDATE SET title=excluded.title,ordinal=excluded.ordinal""",
                    [(source, key, title, index) for index, (key,title) in enumerate(entries)])
                db.execute("UPDATE scan SET playlists_state='ready' WHERE source=?", (source,))
        except Exception as exc:
            logging.exception("Playlist listing failed")
            with self.db() as db:
                db.execute("UPDATE scan SET playlists_state='error' WHERE source=?", (source,))
                system_event(db, "catalog", "catalog_failed", exc, "error")

    def scan_playlist(self, source, playlist):
        try:
            items = list(collector.playlist_videos(playlist))
            with self.db() as db:
                db.execute("DELETE FROM playlist_entry WHERE source=? AND playlist_id=?", (source, playlist))
                db.executemany("""INSERT INTO entry (source,id,title,kind,duration,url,ordinal)
                      VALUES (?,?,?,?,?,?,?) ON CONFLICT(source,id) DO NOTHING""",
                    [(source, item["id"], item["title"], item["kind"], item["duration"], item["url"], 1000000 + index)
                     for index,item in enumerate(items)])
                db.executemany("INSERT OR IGNORE INTO playlist_entry VALUES (?,?,?,?)",
                               [(source, playlist, item["id"], index) for index,item in enumerate(items)])
                db.execute("UPDATE source_playlist SET state='ready',error=NULL WHERE source=? AND id=?", (source, playlist))
        except Exception as exc:
            logging.exception("Playlist scan failed")
            with self.db() as db:
                db.execute("UPDATE source_playlist SET state='error',error=? WHERE source=? AND id=?",
                           (str(exc)[-400:], source, playlist))
                system_event(db, "catalog", "catalog_failed", exc, "error")

    def save_profile(self, source, profile):
        key = hashlib.sha256(source.encode()).hexdigest()
        directory = self.branding / key
        directory.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            old = db.execute("SELECT profile FROM channel_profile WHERE source=?", (source,)).fetchone()
        previous = json.loads(old["profile"]) if old else {}
        profile = dict(profile)
        for name in ("avatar", "banner"):
            try:
                filename = collector.save_channel_image(profile[name], directory, name) if profile.get(name) else None
            except Exception:
                logging.warning("Could not cache channel %s for %s", name, source)
                filename = previous.get(name)
            profile[name] = filename or previous.get(name)
        with self.db() as db:
            db.execute("""INSERT INTO channel_profile VALUES (?,?,?) ON CONFLICT(source) DO UPDATE
                          SET profile=excluded.profile, asset_key=excluded.asset_key""",
                       (source, encode(profile), key))

    def refresh_profile(self, source):
        try:
            self.save_profile(source, collector.fetch_channel_profile(source))
        except Exception:
            logging.warning("Could not refresh channel profile for %s", source, exc_info=True)

    def backfill_profiles(self):
        with self.db() as db:
            missing = db.execute("""SELECT DISTINCT c.source FROM channel c
                LEFT JOIN channel_profile p ON c.source=p.source WHERE c.source IS NOT NULL AND p.source IS NULL""").fetchall()
        for row in missing:
            self.catalog.submit(self.refresh_profile, row["source"])

    def schedule_video_origin(self, video_id):
        now = time.monotonic()
        with self.origin_lock:
            if self.origin_attempts.get(video_id, 0) > now:
                return
            self.origin_attempts[video_id] = now + 600
        self.origins.submit(self.hydrate_video_origin, video_id)

    def backfill_video_origins(self):
        with self.db() as db:
            pending = db.execute("""SELECT v.id FROM video v LEFT JOIN channel_profile p
                ON p.source=json_extract(v.metadata,'$.source_channel_url')
                WHERE v.state='ready' AND (json_extract(v.metadata,'$.thumbnail_source') IS NOT 'youtube'
                    OR json_extract(v.metadata,'$.audio_label_source') IS NULL
                    OR json_extract(v.metadata,'$.source_channel_url') IS NULL OR p.source IS NULL)
                ORDER BY v.created DESC LIMIT 40""").fetchall()
        for row in pending:
            self.schedule_video_origin(row["id"])

    def hydrate_video_origin(self, video_id):
        try:
            self.update_video_thumbnail(video_id)
            with self.files_lock, self.db() as db:
                row = self.ready_video(db, video_id)
                metadata = json.loads(row["metadata"])
                if "audio_label_source" not in metadata:
                    prefs = json.loads(row["prefs"])
                    reported = metadata.get("audio")
                    preference = prefs.get("audio", "original")
                    preferred = preference != "original" and bool(collector.language_score(reported, preference))
                    path = self.library / row["folder"] / metadata["filename"]
                    metadata.update(collector.audio_label(path, reported, preferred))
                    self.save_video_metadata(db, row, metadata)
                url = row["url"]
            source = metadata.get("source_channel_url")
            if not source:
                remote = collector.video_metadata(collector.read_video(url))
                source = remote["source_channel_url"]
                if source:
                    with self.files_lock, self.db() as db:
                        row = self.ready_video(db, video_id)
                        current = json.loads(row["metadata"])
                        for field in ("source_channel", "source_channel_id", "source_channel_url"):
                            if remote[field]:
                                current[field] = remote[field]
                        self.save_video_metadata(db, row, current)
            if source:
                with self.db() as db:
                    cached = db.execute("SELECT 1 FROM channel_profile WHERE source=?", (source,)).fetchone()
                if cached is None:
                    self.refresh_profile(source)
        except Exception:
            logging.warning("Could not refresh saved video identity for %s", video_id, exc_info=True)

    def update_video_thumbnail(self, video_id):
        with self.db() as db:
            row = self.ready_video(db, video_id)
            if json.loads(row["metadata"]).get("thumbnail_source") == "youtube":
                return
        with tempfile.TemporaryDirectory(prefix="thumbnail-", dir=self.work) as temp:
            name = collector.save_video_thumbnail(video_id, Path(temp))
            if not name:
                return
            with self.files_lock:
                if self.exporting[video_id]:
                    return
                with self.db() as db:
                    row = self.ready_video(db, video_id)
                    metadata = json.loads(row["metadata"])
                    bundle = self.video_bundle(row)
                    previous = metadata.get("thumbnail")
                    (Path(temp) / name).replace(self.playlist_asset(bundle, name))
                    metadata.update(thumbnail=name, thumbnail_source="youtube")
                    self.save_video_metadata(db, row, metadata)
                if previous and previous != name and previous.endswith("-thumb.jpg"):
                    self.playlist_asset(bundle, previous).unlink(missing_ok=True)

    def ready_video(self, db, video_id):
        row = db.execute("SELECT * FROM video WHERE id=? AND state='ready'", (video_id,)).fetchone()
        if row is None:
            abort(404)
        return row

    def save_video_metadata(self, db, row, metadata):
        collector.write_manifest(self.library / row["folder"], metadata)
        db.execute("UPDATE video SET metadata=?,title=? WHERE id=?",
                   (encode(metadata), metadata["title"], row["id"]))

    def queue_default_subtitles(self, db, row):
        prefs = json.loads(row["prefs"])
        wanted = prefs["subtitles"]
        for code in (["pt-BR", "en"] if wanted == "both" else [] if wanted == "none" else [wanted]):
            db.execute("""INSERT OR IGNORE INTO track_job (video_id,kind,code,allow_auto,exact,state)
                          VALUES (?,'subtitle',?,?,0,'queued')""", (row["id"], code, int(prefs["auto_subtitles"])))

    def fetch_queued_track(self, job):
        with self.db() as db:
            row = self.ready_video(db, job["video_id"])
        with tempfile.TemporaryDirectory(prefix="track-", dir=self.work) as temp:
            resolved, path = collector.fetch_track(row["url"], job["kind"], job["code"], Path(temp),
                                                   bool(job["allow_auto"]), bool(job["exact"]))
            with self.files_lock, self.db() as db:
                row = self.ready_video(db, job["video_id"])
                metadata = json.loads(row["metadata"])
                folder = self.library / row["folder"]
                filename = f"{Path(metadata['filename']).stem}.{resolved}{path.suffix}"
                path.replace(folder / filename)
                key = "audio_tracks" if job["kind"] == "audio" else "subtitles"
                metadata.setdefault(key, {})[resolved] = filename
                if job["kind"] == "subtitle":
                    metadata["subtitles_missing"] = False
                self.save_video_metadata(db, row, metadata)
                db.execute("UPDATE track_job SET state='ready',resolved=?,error=NULL,retry_at=0 WHERE rowid=?",
                           (resolved, job["job_id"]))

    def remove_track(self, video_id, kind, code, saved):
        with self.files_lock:
            if not saved:
                with self.db() as db:
                    return bool(db.execute("""DELETE FROM track_job WHERE video_id=? AND kind=?
                        AND code=? AND state='failed'""", (video_id, kind, code)).rowcount)
            if self.exporting[video_id]:
                raise ValueError("playlist_export_busy")
            if self.preparing_playback[video_id]:
                raise ValueError("playback_busy")
            with tempfile.TemporaryDirectory(prefix="delete-track-", dir=self.work) as temp:
                staged = Path(temp) / "track"
                manifest_changed = False
                try:
                    with self.db() as db:
                        db.execute("BEGIN IMMEDIATE")
                        row = self.ready_video(db, video_id)
                        metadata = json.loads(row["metadata"])
                        key = "audio_tracks" if kind == "audio" else "subtitles"
                        tracks = metadata.get(key, {})
                        filename = tracks.get(code)
                        if not filename:
                            return False
                        active = db.execute("""SELECT code,exact FROM track_job
                            WHERE video_id=? AND kind=? AND state='running'""", (video_id, kind))
                        if any(job["code"] == code or not job["exact"] and collector.language_score(code, job["code"])
                               for job in active):
                            raise ValueError("track_active")
                        bundle = self.video_bundle(row)
                        source = self.playlist_asset(bundle, filename)
                        if (filename in {metadata["filename"], metadata.get("thumbnail")}
                                or source.suffix != (".m4a" if kind == "audio" else ".vtt")):
                            raise ValueError("invalid_track")
                        if kind == "audio":
                            self.clear_video_cache(row, bundle)
                        try:
                            source.rename(staged)
                        except FileNotFoundError:
                            pass
                        aliases = [tag for tag, asset in tracks.items() if asset == filename]
                        for tag in aliases:
                            del tracks[tag]
                            db.execute("""DELETE FROM track_job WHERE video_id=? AND kind=?
                                AND (code=? OR resolved=?)""", (video_id, kind, tag, tag))
                        self.save_video_metadata(db, row, metadata)
                        manifest_changed = True
                except Exception:
                    if staged.exists():
                        staged.rename(source)
                    if manifest_changed:
                        collector.write_manifest(bundle, json.loads(row["metadata"]))
                    raise
            return True

    def playback_files(self, video_id, code):
        with self.db() as db:
            row = self.ready_video(db, video_id)
            metadata = json.loads(row["metadata"])
        audio = metadata.get("audio_tracks", {}).get(code)
        if not audio:
            abort(404)
        folder = self.video_bundle(row)
        base_path = self.playlist_asset(folder, metadata["filename"])
        audio_path = self.playlist_asset(folder, audio)
        if not base_path.is_file() or not audio_path.is_file():
            abort(404)
        variant = self.playback / f"{video_id}-{self.playback_cache_name(video_id, code, base_path, audio_path)}"
        return base_path, audio_path, variant

    def serve_playback(self, variant):
        info = variant.stat()
        now = time.time_ns()
        if now - info.st_atime_ns >= 60 * 10**9:
            os.utime(variant, ns=(now, info.st_mtime_ns))
        return send_from_directory(self.playback, variant.name, conditional=True)

    def playback_variant(self, video_id, code):
        with self.files_lock:
            _, _, variant = self.playback_files(video_id, code)
            if variant.is_file():
                return self.serve_playback(variant)
        with self.playback_lock:
            with self.files_lock:
                if self.pending_maintenance.exists():
                    raise ValueError("maintenance_pending")
                base_path, audio_path, variant = self.playback_files(video_id, code)
                if variant.is_file():
                    return self.serve_playback(variant)
                self.preparing_playback[video_id] += 1
            try:
                with tempfile.TemporaryDirectory(prefix="mux-", dir=self.playback) as temp:
                    staged = Path(temp) / variant.name
                    codec = "libopus" if base_path.suffix == ".webm" else "copy"
                    collector.mux_video(base_path, staged, code, audio_path, audio_codec=codec)
                    with self.files_lock:
                        staged.replace(variant)
                        self.prune_playback(variant)
                        return self.serve_playback(variant)
            finally:
                with self.files_lock:
                    self.preparing_playback[video_id] -= 1
                    if not self.preparing_playback[video_id]:
                        del self.preparing_playback[video_id]

    @staticmethod
    def playback_cache_name(video_id, code, base_path, audio_path):
        signature = f"{video_id}:{code}:{base_path.stat().st_mtime_ns}:{audio_path.stat().st_mtime_ns}"
        return hashlib.sha256(signature.encode()).hexdigest() + base_path.suffix

    def prune_playback(self, current):
        cached = []
        for path in self.playback.iterdir():
            if path.suffix in {".mp4", ".webm"}:
                try:
                    info = path.stat()
                except OSError:
                    continue
                cached.append((info.st_atime_ns, info.st_size, path))
        used = sum(size for _, size, _ in cached)
        for _, size, path in sorted(cached):
            if used <= self.playback_budget:
                break
            if path != current:
                try:
                    path.unlink(missing_ok=True)
                    used -= size
                except OSError:
                    logging.warning("Could not clear playback cache file %s", path.name)

    def write_entries(self, batch):
        with self.db() as db:
            db.executemany("""INSERT INTO entry VALUES (?,?,?,?,?,?,?) ON CONFLICT(source,id) DO UPDATE
                              SET title=excluded.title, kind=excluded.kind, duration=excluded.duration,
                              url=excluded.url, ordinal=excluded.ordinal""", batch)

    def sync_channels(self):
        with self.db() as db:
            channels = db.execute("SELECT * FROM channel WHERE auto=1 AND source IS NOT NULL AND next_sync<=?",
                                  (timestamp(),)).fetchall()
        for channel in channels:
            try:
                entries = [entry for _, entry in collector.channel_entries(channel["source"], limit=30) if entry]
                with self.files_lock, self.db() as db:
                    current = db.execute("SELECT * FROM channel WHERE id=?", (channel["id"],)).fetchone()
                    if not current or not current["auto"]:
                        continue
                    prefs = self.effective(db, current)
                    for entry in entries:
                        new = db.execute("INSERT OR IGNORE INTO seen VALUES (?,?)",
                                         (current["id"], entry["id"])).rowcount
                        if new and current["baseline"] and allowed(entry["kind"], prefs["shorts"]):
                            self.enqueue(db, entry, current, prefs)
                    if entries:
                        db.execute("UPDATE channel SET baseline=1 WHERE id=?", (current["id"],))
            except Exception as exc:
                logging.exception("Subscription check failed")
                with self.db() as db:
                    system_event(db, "catalog", "catalog_failed", exc, "error")
            finally:
                with self.db() as db:
                    db.execute("UPDATE channel SET next_sync=? WHERE id=?", (timestamp() + 900, channel["id"]))

    def sync_loop(self):
        while True:
            try:
                self.sync_channels()
            except Exception:
                logging.exception("Subscription loop failed")
            time.sleep(20)

    def finish_publish(self, db, row):
        target = self.video_bundle({"folder": row["pending_folder"], "id": row["id"]})
        if not target.exists():
            db.execute("UPDATE video SET pending_folder=NULL,pending_channel=NULL WHERE id=?", (row["id"],))
            return None
        manifest = self.playlist_asset(target, "video.json")
        meta = json.loads(manifest.read_text(encoding="utf-8"))
        if not self.playlist_asset(target, meta["filename"]).is_file() or not isinstance(meta["title"], str):
            raise ValueError("publish_incomplete")
        db.execute("""UPDATE video SET folder=pending_folder, channel_id=pending_channel,
                      pending_folder=NULL,pending_channel=NULL,state='ready',metadata=?,
                      title=?,percent=100,error=NULL,progress_phase=NULL,progress_estimated=0 WHERE id=?""",
                   (encode(meta), meta["title"], row["id"]))
        if row["state"] != "ready":
            self.queue_default_subtitles(db, row)
            system_event(db, "downloads", "download_completed", meta["title"])
        return True

    def recover_publication(self, db, row):
        try:
            return self.finish_publish(db, row)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
            original_available = False
            if row["state"] == "ready":
                try:
                    original = self.video_bundle(row)
                    original_available = self.playlist_asset(original, json.loads(row["metadata"])["filename"]).is_file()
                except (OSError, ValueError, KeyError, TypeError, RuntimeError):
                    pass
            db.execute("""UPDATE video SET pending_folder=NULL,pending_channel=NULL,state=?,error=?
                          WHERE id=?""", ("ready" if original_available else "failed",
                                          None if original_available else "publish_incomplete", row["id"]))
            system_event(db, "downloads", "publish_incomplete", f"{row['id']} · {exc}", "error")
            return False

    def recover_downloads(self, db):
        for row in db.execute("SELECT * FROM video WHERE state='cancelling'").fetchall():
            self.finish_cancellation(db, row)
        pending = db.execute("SELECT * FROM video WHERE pending_folder IS NOT NULL").fetchall()
        for row in pending:
            self.recover_publication(db, row)
        db.execute("""UPDATE video SET state='queued',percent=0,progress_phase=NULL,progress_estimated=0
                      WHERE state='running'""")
        db.execute("UPDATE track_job SET state='queued' WHERE state='running'")
        return [row["id"] for row in pending]

    def check_capture_cancelled(self):
        if self.capture_cancelled.is_set():
            raise collector.DownloadCancelled()

    def finish_cancellation(self, db, row):
        inputs = self.work / "inputs" / row["id"]
        try:
            if not collector.VIDEO_ID.fullmatch(row["id"]) or inputs.resolve() != inputs:
                raise ValueError("delete_invalid_folder")
            for temporary in [inputs, *self.work.glob(f"{row['id']}-*")]:
                if temporary.resolve() != temporary:
                    raise ValueError("delete_invalid_folder")
                if temporary.exists():
                    shutil.rmtree(temporary)
        except (OSError, ValueError) as exc:
            db.execute("""UPDATE video SET state='failed',error='cancel_cleanup_failed',
                progress_phase=NULL,progress_estimated=0 WHERE id=?""", (row["id"],))
            system_event(db, "downloads", "cancel_cleanup_failed", f"{row['id']} · {exc}", "error")
            return False
        if row["folder"]:
            missing = not self.archived_picture_exists(row)
            db.execute("""UPDATE video SET state='removed',error=?,percent=0,
                pending_folder=NULL,pending_channel=NULL,progress_phase=NULL,progress_estimated=0 WHERE id=?""",
                       ("external_media_missing" if missing else None, row["id"]))
        else:
            if row["channel_id"]:
                db.execute("INSERT OR IGNORE INTO seen VALUES (?,?)", (row["channel_id"], row["id"]))
            db.execute("DELETE FROM video WHERE id=?", (row["id"],))
        system_event(db, "downloads", "download_cancelled", row["title"])
        return True

    def cancel_download(self, video_id):
        if not collector.VIDEO_ID.fullmatch(video_id):
            abort(404)
        cleanup_failed = False
        with self.files_lock, self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM video WHERE id=?", (video_id,)).fetchone()
            if row is None:
                return False
            if row["state"] == "cancelling":
                return True
            if row["state"] not in {"queued", "running", "failed"}:
                raise ValueError("download_finished")
            if row["pending_folder"]:
                self.recover_publication(db, row)
                row = db.execute("SELECT * FROM video WHERE id=?", (video_id,)).fetchone()
                if row["state"] == "ready":
                    return False
            if row["state"] == "running":
                db.execute("UPDATE video SET state='cancelling' WHERE id=?", (video_id,))
                self.capture_cancelled.set()
                return True
            cleanup_failed = not self.finish_cancellation(db, row)
        self.changed.set()
        if cleanup_failed:
            raise ValueError("cancel_cleanup_failed")
        return False

    def capture(self, item):
        video_id = item["id"]
        last_progress, last_write = (None, None, False), float("-inf")

        def progress(phase, percent=None, estimated=False):
            nonlocal last_progress, last_write
            self.check_capture_cancelled()
            current = (phase, percent, estimated)
            if current == last_progress:
                return
            now = time.monotonic()
            if phase != last_progress[0] or percent == 100 or last_progress[1] is None or now - last_write >= 1:
                with self.db() as db:
                    db.execute("UPDATE video SET progress_phase=?,percent=?,progress_estimated=? WHERE id=?",
                               (*current, video_id))
                last_progress, last_write = current, now

        inputs = self.work / "inputs" / video_id
        inputs.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"{video_id}-", dir=self.work) as scratch:
            bundle = Path(scratch) / "bundle"
            bundle.mkdir()
            progress("prepare")
            meta = collector.download(item["url"], json.loads(item["prefs"]), inputs, bundle, progress,
                                      on_title=lambda title: self.remember_download_title(video_id, title),
                                      cancel=self.check_capture_cancelled)
            progress("publish")
            collector.write_manifest(bundle, meta)
            with self.files_lock:
                self.check_capture_cancelled()
                with self.db() as db:
                    channel = self.channel(db, item["channel_id"])
                    parent = Path(channel["folder"] if channel else "Avulsos")
                    title = collector.safe_name(meta["title"])
                    folder = parent / f"{title} [{video_id}]"
                    suffix = 2
                    while (self.library / folder).exists() or (self.library / folder).is_symlink():
                        folder = parent / f"{title} ({suffix}) [{video_id}]"
                        suffix += 1
                    db.execute("UPDATE video SET pending_folder=?,pending_channel=? WHERE id=?",
                               (str(folder), item["channel_id"], video_id))
                target = self.library / folder
                target.parent.mkdir(parents=True, exist_ok=True)
                bundle.rename(target)
                with self.db() as db:
                    self.finish_publish(db, db.execute("SELECT * FROM video WHERE id=?", (video_id,)).fetchone())
                self.refresh_video_playlists(video_id)
        self.schedule_video_origin(video_id)
        try:
            shutil.rmtree(inputs)
        except OSError:
            logging.warning("Could not clear temporary inputs for %s", video_id)

    def worker(self):
        recovering = False
        while True:
            try:
                if recovering:
                    with self.files_lock:
                        with self.db() as db:
                            affected = self.recover_downloads(db)
                        for video_id in affected:
                            self.refresh_video_playlists(video_id)
                    recovering = False
                self.download_loop()
            except sqlite3.OperationalError:
                recovering = True
                logging.warning("Download worker interrupted by SQLite; retrying", exc_info=True)
                time.sleep(2)

    def download_loop(self):
        while True:
            self.changed.clear()
            with self.db() as db:
                track = db.execute("""UPDATE track_job SET state='running' WHERE rowid=(
                    SELECT t.rowid FROM track_job t JOIN video v ON v.id=t.video_id
                    WHERE t.state='queued' AND v.state='ready' ORDER BY t.exact DESC,t.rowid LIMIT 1
                ) RETURNING rowid AS job_id,*""").fetchone()
            if track:
                try:
                    self.fetch_queued_track(track)
                except sqlite3.OperationalError:
                    raise
                except Exception as exc:
                    error = str(exc) if str(exc) in {"track_unavailable", "track_invalid", "track_rate_limited"} else "track_failed"
                    logging.warning("Track job failed for %s (%s): %s", track["video_id"], track["code"], error)
                    with self.db() as db:
                        current = db.execute("SELECT state FROM video WHERE id=?", (track["video_id"],)).fetchone()
                        if not current or current["state"] in {"removed", "queued"}:
                            db.execute("UPDATE track_job SET state='queued' WHERE rowid=?", (track["job_id"],))
                            continue
                        retry_at = timestamp() + exc.seconds if isinstance(exc, collector.TrackRateLimited) else 0
                        db.execute("UPDATE track_job SET state='failed',error=?,retry_at=? WHERE rowid=?",
                                   (error, retry_at, track["job_id"]))
                        system_event(db, "tracks", error, f"{track['video_id']} · {track['code']}", "error")
                continue
            with self.files_lock:
                self.capture_cancelled.clear()
                with self.db() as db:
                    item = db.execute("""UPDATE video SET state='running',progress_phase='prepare',percent=NULL,
                        progress_estimated=0 WHERE id=(
                        SELECT id FROM video WHERE state='queued' ORDER BY created,rowid LIMIT 1
                    ) RETURNING *""").fetchone()
            if item is None:
                self.changed.wait(2)
                continue
            try:
                self.capture(item)
            except sqlite3.OperationalError:
                raise
            except Exception as exc:
                with self.files_lock:
                    with self.db() as db:
                        row = db.execute("SELECT * FROM video WHERE id=?", (item["id"],)).fetchone()
                        if row["state"] == "cancelling":
                            self.finish_cancellation(db, row)
                        elif not row["pending_folder"] or self.recover_publication(db, row) is None:
                            logging.exception("Capture failed for %s", item["id"])
                            db.execute("""UPDATE video SET state='failed',error=?,
                                          pending_folder=NULL,pending_channel=NULL WHERE id=?""",
                                       (str(exc)[-450:], item["id"]))
                            system_event(db, "downloads", "download_failed", f"{item['id']} · {exc}", "error")
                    self.refresh_video_playlists(item["id"])

    def move(self, video_id, target_id, new_name=None):
        with self.files_lock:
            if self.exporting[video_id]:
                raise ValueError("playlist_export_busy")
            if self.preparing_playback[video_id]:
                raise ValueError("playback_busy")
            with self.db() as db:
                row = db.execute("SELECT * FROM video WHERE id=? AND state='ready'", (video_id,)).fetchone()
                if row is None:
                    abort(404)
                channel = (self.create_channel(db, label(new_name)) if new_name is not None
                           else self.channel(db, target_id))
                target_id = channel["id"] if channel else None
                source = self.library / row["folder"]
                destination = Path(channel["folder"] if channel else "Avulsos") / source.name
                target = self.library / destination
                if source == target:
                    return
                if target.exists() or not source.is_dir():
                    abort(409)
                db.execute("UPDATE video SET pending_folder=?,pending_channel=? WHERE id=?",
                           (str(destination), target_id, video_id))
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                source.rename(target)
            except OSError:
                with self.db() as db:
                    db.execute("UPDATE video SET pending_folder=NULL,pending_channel=NULL WHERE id=?", (video_id,))
                    if new_name is not None:
                        db.execute("DELETE FROM channel WHERE id=?", (target_id,))
                raise
            with self.db() as db:
                self.finish_publish(db, db.execute("SELECT * FROM video WHERE id=?", (video_id,)).fetchone())
            self.refresh_video_playlists(video_id)

    def video_bundle(self, row):
        relative = Path(row["folder"] or "")
        target = self.library / relative
        if (len(relative.parts) != 2 or relative.is_absolute() or ".." in relative.parts
                or not relative.name.endswith(f" [{row['id']}]") or target.resolve() != target):
            raise ValueError("delete_invalid_folder")
        return target

    def archived_picture_exists(self, row):
        folder = self.video_bundle(row)
        filename = json.loads(row["metadata"])["filename"]
        picture = self.playlist_asset(folder, filename)
        try:
            return stat.S_ISREG(picture.stat().st_mode)
        except (FileNotFoundError, NotADirectoryError):
            return False

    def find_external_moves(self, channels, missing, occupied):
        matches = {}
        for directory, channel_id in channels.items():
            parent = self.library / directory
            if parent.resolve() != parent:
                continue
            try:
                folders = list(parent.iterdir())
            except (FileNotFoundError, NotADirectoryError):
                continue
            for folder in folders:
                video_id = folder.name[-12:-1]
                if video_id not in missing or not folder.name.endswith(f" [{video_id}]"):
                    continue
                relative = str(folder.relative_to(self.library))
                if relative in occupied:
                    continue
                row = {**dict(missing[video_id]), "folder": relative}
                try:
                    if not self.archived_picture_exists(row):
                        continue
                    manifest = self.playlist_asset(folder, "video.json")
                    with manifest.open(encoding="utf-8") as source:
                        identity = json.loads(source.read(1024 * 1024))
                    if (identity.get("id") == video_id
                            and identity.get("filename") == json.loads(row["metadata"])["filename"]):
                        matches.setdefault(video_id, []).append((relative, channel_id))
                except (FileNotFoundError, NotADirectoryError, ValueError, AttributeError):
                    continue
        return matches

    def reconcile_library(self):
        counts = {"moved": 0, "missing": 0, "restored": 0, "ambiguous": 0}
        playlists = set()
        with self.files_lock:
            if self.pending_maintenance.exists():
                raise ValueError("maintenance_pending")
            if self.library.resolve() != self.library or not self.library.is_dir():
                raise ValueError("library_check_failed")
            with self.db() as db:
                rows = db.execute("""SELECT id,folder,channel_id,state,error,metadata FROM video
                    WHERE pending_folder IS NULL AND
                    (state='ready' OR (state='removed' AND error='external_media_missing'))""").fetchall()
                missing = {}
                changes = []
                for row in rows:
                    if self.exporting[row["id"]] or self.preparing_playback[row["id"]]:
                        continue
                    if not self.archived_picture_exists(row):
                        missing[row["id"]] = row
                    elif row["state"] == "removed":
                        changes.append((row, row["folder"], row["channel_id"], "restored"))
                if missing:
                    channels = {row["folder"]: row["id"] for row in db.execute("SELECT id,folder FROM channel")}
                    channels["Avulsos"] = None
                    occupied = {str(Path(row["folder"])) for row in db.execute(
                        "SELECT folder FROM video WHERE folder IS NOT NULL")}
                    matches = self.find_external_moves(channels, missing, occupied)
                    for video_id, row in missing.items():
                        destinations = matches.get(video_id, [])
                        if len(destinations) == 1:
                            folder, channel_id = destinations[0]
                            changes.append((row, folder, channel_id, "moved"))
                        else:
                            counts["ambiguous"] += int(len(destinations) > 1)
                            if row["state"] == "ready":
                                changes.append((row, row["folder"], row["channel_id"], "missing"))
                for row, folder, channel_id, action in changes:
                    state, error = ("removed", "external_media_missing") if action == "missing" else ("ready", None)
                    db.execute("UPDATE video SET folder=?,channel_id=?,state=?,error=? WHERE id=?",
                               (folder, channel_id, state, error, row["id"]))
                    playlists.update(item[0] for item in db.execute(
                        "SELECT playlist_id FROM playlist_item WHERE video_id=?", (row["id"],)))
                    counts[action] += 1
                if changes:
                    system_event(db, "library", "library_reconciled", str(len(changes)))
            self.refresh_playlist_files(sorted(playlists))
        if changes:
            self.changed.set()
        return counts

    def remove_video(self, video_id, disk):
        if not collector.VIDEO_ID.fullmatch(video_id):
            abort(404)
        with self.files_lock:
            self.remove_video_locked(video_id, disk)

    def remove_video_locked(self, video_id, disk, refresh=True):
        if disk and self.exporting[video_id]:
            raise ValueError("playlist_export_busy")
        if disk and self.preparing_playback[video_id]:
            raise ValueError("playback_busy")
        with self.db() as db:
            row = db.execute("SELECT * FROM video WHERE id=? AND state IN ('ready','removed')",
                             (video_id,)).fetchone()
            if row is None:
                abort(404)
            db.execute("UPDATE video SET state='removed' WHERE id=?", (video_id,))
        if refresh:
            self.refresh_video_playlists(video_id)
        if not disk:
            return

        try:
            target = self.video_bundle(row)
            staged = self.work / "deleting" / video_id
            if staged.resolve() != staged:
                raise ValueError("delete_invalid_folder")
            if target.exists():
                if staged.exists() or not target.is_dir():
                    raise ValueError("delete_invalid_folder")
                staged.parent.mkdir(parents=True, exist_ok=True)
                target.rename(staged)
            self.clear_video_cache(row, staged)
            if staged.exists():
                shutil.rmtree(staged)
        except (OSError, ValueError) as exc:
            logging.exception("Disk removal failed for %s", video_id)
            with self.db() as db:
                system_event(db, "library", "delete_disk_failed", exc, "error")
            raise ValueError("delete_disk_failed") from exc

        with self.db() as db:
            if row["channel_id"]:
                db.execute("INSERT OR IGNORE INTO seen VALUES (?,?)", (row["channel_id"], video_id))
            db.execute("DELETE FROM video WHERE id=?", (video_id,))

    def collection_videos(self, db, kind, collection_id):
        if kind not in {"channel", "playlist"} or not re.fullmatch(r"[a-f0-9]{10}", collection_id):
            abort(404)
        collection = db.execute(f"SELECT * FROM {kind} WHERE id=?", (collection_id,)).fetchone()
        if collection is None:
            abort(404)
        if kind == "channel":
            rows = db.execute("SELECT * FROM video WHERE channel_id=? ORDER BY id", (collection_id,)).fetchall()
        else:
            rows = db.execute("""SELECT v.* FROM video v JOIN playlist_item p ON p.video_id=v.id
                WHERE p.playlist_id=? ORDER BY v.id""", (collection_id,)).fetchall()
        return collection, rows

    def deletion_preview(self, kind, collection_id):
        with self.files_lock, self.db() as db:
            collection, rows = self.collection_videos(db, kind, collection_id)
            shared = sum(bool(db.execute("SELECT 1 FROM playlist_item WHERE video_id=? AND playlist_id<>? LIMIT 1",
                                        (row["id"], collection_id if kind == "playlist" else "")).fetchone())
                         for row in rows)
            return {"name": collection["name"], "ids": [row["id"] for row in rows], "shared": shared}

    def remove_videos(self, ids, disk, collection=None):
        if type(disk) is not bool:
            raise ValueError("invalid_delete_option")
        if not valid_selection(ids) or len(ids) > 20000:
            raise ValueError("invalid_selection")
        ids = set(ids)
        with self.files_lock:
            if self.pending_maintenance.exists():
                raise ValueError("maintenance_pending")
            with self.db() as db:
                if collection:
                    kind, collection_id = collection
                    info, rows = self.collection_videos(db, kind, collection_id)
                    if any(row["id"] not in ids for row in rows):
                        raise ValueError("collection_changed")
                    if kind == "channel" and db.execute(
                            "SELECT 1 FROM video WHERE pending_channel=? LIMIT 1", (collection_id,)).fetchone():
                        raise ValueError("collection_busy")
                else:
                    rows = []
                    selected = sorted(ids)
                    for offset in range(0, len(selected), 500):
                        batch = selected[offset:offset + 500]
                        rows.extend(db.execute(f"SELECT * FROM video WHERE id IN ({','.join('?' for _ in batch)})", batch))
                if disk and any(self.exporting[row["id"]] for row in rows):
                    raise ValueError("playlist_export_busy")
                if disk and any(self.preparing_playback[row["id"]] for row in rows):
                    raise ValueError("playback_busy")
                active = [row for row in rows if row["state"] in {"running", "cancelling"}]
                if active:
                    for row in rows:
                        if row["state"] in {"queued", "failed"}:
                            self.finish_cancellation(db, row)
                    for row in active:
                        db.execute("UPDATE video SET state='cancelling' WHERE id=?", (row["id"],))
                    self.capture_cancelled.set()
                    return {"pending": True, "removed": 0}
                if any(row["pending_folder"] for row in rows):
                    raise ValueError("collection_busy")
            # Refresh playlist projections once, including after a partial disk failure.
            try:
                for row in rows:
                    if row["state"] not in {"ready", "removed"}:
                        with self.db() as db:
                            cancelled = self.finish_cancellation(db, row)
                        if not cancelled:
                            raise ValueError("cancel_cleanup_failed")
                        if not row["folder"]:
                            continue
                    self.remove_video_locked(row["id"], disk, refresh=False)
                if collection:
                    kind, collection_id = collection
                    if kind == "playlist":
                        folder = self.playlist_directory / f"{collector.safe_name(info['name'])} [{collection_id}]"
                        if folder.resolve() != folder:
                            raise ValueError("delete_invalid_folder")
                        (folder / "playlist.m3u8").unlink(missing_ok=True)
                        if folder.is_dir() and not any(folder.iterdir()):
                            folder.rmdir()
                    elif disk:
                        folder = self.library / info["folder"]
                        if folder.resolve() == folder and folder.is_dir() and not any(folder.iterdir()):
                            folder.rmdir()
                    with self.db() as db:
                        if kind == "channel":
                            db.execute("UPDATE video SET channel_id=NULL WHERE channel_id=?", (collection_id,))
                        db.execute(f"DELETE FROM {kind} WHERE id=?", (collection_id,))
            except OSError as exc:
                with self.db() as db:
                    system_event(db, "library", "delete_disk_failed", exc, "error")
                raise ValueError("delete_disk_failed") from exc
            finally:
                self.refresh_playlist_files()
                self.changed.set()
        return {"pending": False, "removed": len(rows)}

    def clear_video_cache(self, row, staged):
        if self.playback.resolve() != self.playback:
            raise ValueError("delete_invalid_folder")
        for cached in self.playback.glob(f"{row['id']}-*"):
            cached.unlink(missing_ok=True)
        metadata = json.loads(row["metadata"])
        picture = staged / metadata["filename"]
        if picture.is_file():
            for code, name in metadata.get("audio_tracks", {}).items():
                audio = staged / name
                if audio.is_file():
                    legacy = self.playback / self.playback_cache_name(row["id"], code, picture, audio)
                    legacy.unlink(missing_ok=True)

    def restore_video(self, video_id):
        with self.files_lock:
            with self.db() as db:
                row = db.execute("SELECT * FROM video WHERE id=? AND state='removed'", (video_id,)).fetchone()
                if row is None:
                    abort(404)
                if not (self.video_bundle(row) / json.loads(row["metadata"])["filename"]).is_file():
                    raise ValueError("restore_media_missing")
                db.execute("UPDATE video SET state='ready',error=NULL WHERE id=?", (video_id,))
            self.refresh_video_playlists(video_id)
        self.changed.set()


def library_video(row, db, profiles=None, summary=False):
    meta = json.loads(row["metadata"]) if row["metadata"] else {}
    source = meta.get("source_channel_url")
    if summary:
        meta = {key: meta[key] for key in ("duration", "thumbnail", "upload_date", "source_channel") if key in meta}
    if source:
        if profiles is None:
            profiles = {}
        if source not in profiles:
            result = db.execute("SELECT profile FROM channel_profile WHERE source=?", (source,)).fetchone()
            profiles[source] = json.loads(result["profile"]) if result else None
        profile = profiles[source]
        if profile:
            meta["source_profile"] = {"name": profile.get("name")} if summary else profile
    if row["state"] != "ready":
        meta["capture_overrides"] = json.loads(row["capture_overrides"])
    return {**meta, **{key: row[key] for key in
                      ("id", "title", "url", "channel_id", "kind", "state", "position",
                       "percent", "progress_phase", "progress_estimated", "error", "watched_at", "created")}}


def create_app(data=None, root=None, workers=True):
    app = Flask(__name__, static_folder="static")
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    archive = Archive(data or os.environ.get("DATA_DIR", "./data"),
                      root or os.environ.get("ARCHIVE_DIR", "./archive"))
    app.extensions["archive"] = archive
    if workers:
        threading.Thread(target=archive.worker, daemon=True, name="download").start()
        threading.Thread(target=archive.sync_loop, daemon=True, name="subscription").start()
        archive.backfill_profiles()
        archive.backfill_video_origins()
        archive.backfill_download_titles()

    def body():
        value = request.get_json()
        if not isinstance(value, dict):
            raise BadRequest()
        return value

    def check_origin():
        origin = request.headers.get("Origin")
        if origin and origin != request.host_url.rstrip("/"):
            abort(403)

    def local_change():
        check_origin()
        return body()

    def restart_process():
        timer = threading.Timer(1.5, os._exit, args=(0,))
        timer.daemon = True
        timer.start()

    def prepare_system_change(operation):
        if not archive.dependency_lock.acquire(blocking=False):
            return jsonify(error="dependency_busy"), 409
        try:
            archive.stage_maintenance(operation)
        finally:
            archive.dependency_lock.release()
        restarting = workers and os.environ.get("GRIDTUBE_RESTART_IN_DOCKER") == "1"
        if restarting:
            restart_process()
        return jsonify(ok=True, restarting=restarting), 202

    @app.errorhandler(ValueError)
    def invalid(exc):
        return jsonify(error=str(exc)), 400

    @app.errorhandler(sqlite3.IntegrityError)
    def conflict(_):
        return jsonify(error="already_exists"), 409

    @app.get("/")
    @app.get("/watch/<video_id>")
    def index(video_id=None):
        if video_id is not None and not collector.VIDEO_ID.fullmatch(video_id):
            abort(404)
        return app.send_static_file("index.html")

    @app.get("/favicon.ico")
    def favicon():
        return app.send_static_file("favicon.ico")

    @app.get("/healthz")
    def health():
        return "", 204

    @app.get("/api/state")
    def state():
        with archive.db() as db:
            channels = []
            for row in db.execute("""SELECT c.*,p.profile,d.description AS custom_description,s.icon,s.color FROM channel c
                     LEFT JOIN channel_profile p ON c.source=p.source
                     LEFT JOIN channel_description d ON c.id=d.channel_id
                     LEFT JOIN channel_style s ON c.id=s.id ORDER BY c.name COLLATE NOCASE"""):
                channel = dict(row)
                channel["overrides"] = json.loads(row["overrides"])
                channel["profile"] = json.loads(row["profile"]) if row["profile"] else {}
                style = {"icon": channel.pop("icon") or "folder", "color": channel.pop("color") or "#bebebe"}
                channel["appearance"] = None if channel["source"] else style
                channels.append(channel)
            playlists = [{"id": row["id"], "name": row["name"],
                          "appearance": {"icon": row["icon"] or "list", "color": row["color"] or "#bebebe"}}
                         for row in db.execute("""SELECT p.*,s.icon,s.color FROM playlist p
                             LEFT JOIN playlist_style s ON p.id=s.id ORDER BY p.name COLLATE NOCASE""")]
            counts = dict(db.execute("SELECT state,count(*) FROM video GROUP BY state"))
            return jsonify(settings=archive.defaults(db), channels=channels, playlists=playlists, counts=counts)

    @app.put("/api/settings")
    def save_settings():
        prefs = preferences(body())
        with archive.db() as db:
            db.execute("UPDATE settings SET prefs=? WHERE id=1", (encode(prefs),))
        return jsonify(prefs)

    @app.get("/api/system")
    def system_status():
        with archive.db() as db:
            events = [dict(row) for row in db.execute("SELECT * FROM system_event ORDER BY id DESC LIMIT 50")]
        return jsonify(yt_dlp=archive.dependency_status(), events=events,
                       maintenance_pending=archive.pending_maintenance.exists())

    @app.post("/api/system/library/check")
    def check_library():
        local_change()
        try:
            return jsonify(archive.reconcile_library())
        except (OSError, KeyError, TypeError, RuntimeError):
            logging.exception("Could not check the archive files")
            return jsonify(error="library_check_failed"), 409

    @app.get("/api/system/backup")
    def backup_catalog():
        def download():
            with archive.db() as db:
                yield from catalog_backup.export_lines(db)

        return Response(download(), mimetype="application/x-ndjson",
                        headers={"Content-Disposition": "attachment; filename=gridtube-backup.jsonl",
                                 "Cache-Control": "no-store"})

    @app.post("/api/system/backup/preview")
    def preview_backup():
        check_origin()
        request.max_content_length = 512 * 1024 ** 2
        upload = request.files.get("backup")
        if upload is None:
            raise ValueError("backup_invalid")
        return jsonify(archive.preview_backup(upload.stream))

    @app.post("/api/system/backup/restore")
    def restore_backup():
        data = local_change()
        return prepare_system_change({"action": "restore", "token": data.get("token")})

    @app.get("/api/system/backup/status/<token>")
    def backup_restore_status(token):
        archive.backup_candidate(token)
        with archive.db() as db:
            result = db.execute("""SELECT code FROM system_event WHERE area='system' AND detail=?
                AND code IN ('backup_restored','backup_restore_failed') ORDER BY id DESC LIMIT 1""", (token,)).fetchone()
        if result:
            return jsonify(status="verified" if result["code"] == "backup_restored" else "failed")
        return jsonify(status="pending" if archive.pending_maintenance.exists() else "unknown")

    @app.post("/api/system/reset")
    def reset_data():
        data = local_change()
        disk = data.get("disk")
        if type(disk) is not bool or data.get("confirmation") != ("RESET MEDIA" if disk else "RESET"):
            raise ValueError("reset_confirmation_invalid")
        return prepare_system_change({"action": "reset", "disk": disk})

    @app.post("/api/system/yt-dlp")
    def update_yt_dlp():
        local_change()
        if not archive.dependency_lock.acquire(blocking=False):
            return jsonify(error="dependency_busy"), 409
        if archive.pending_maintenance.exists():
            archive.dependency_lock.release()
            return jsonify(error="maintenance_pending"), 409
        threading.Thread(target=archive.update_dependency, daemon=True, name="yt-dlp-update").start()
        return jsonify(ok=True), 202

    @app.post("/api/system/yt-dlp/restart")
    def restart_yt_dlp():
        local_change()
        status = archive.dependency_status()
        if not status["can_restart"] or not status["pending"] or not archive.dependency_lock.acquire(blocking=False):
            return jsonify(error="restart_unavailable"), 409
        if archive.pending_maintenance.exists():
            archive.dependency_lock.release()
            return jsonify(error="maintenance_pending"), 409
        restart_process()
        return jsonify(ok=True), 202

    @app.post("/api/scans")
    def start_scan():
        source, _ = collector.youtube_url(body().get("url"), "channel")
        with archive.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM scan WHERE source=?", (source,)).fetchone()
            if row and row["state"] == "loading":
                return jsonify(source=source)
            db.execute("""INSERT INTO scan (source,state) VALUES (?,'loading')
                          ON CONFLICT(source) DO UPDATE SET state='loading',error=NULL""", (source,))
        archive.catalog.submit(archive.scan_source, source)
        return jsonify(source=source)

    @app.post("/api/scans/playlists")
    def start_playlist_scan():
        data = body()
        source, _ = collector.youtube_url(data.get("source"), "channel")
        key = data.get("playlist")
        with archive.db() as db:
            db.execute("BEGIN IMMEDIATE")
            scan = db.execute("SELECT playlists_state FROM scan WHERE source=?", (source,)).fetchone()
            if not scan:
                abort(404)
            force = data.get("force") is True
            if key:
                if not isinstance(key, str) or not collector.PLAYLIST_ID.fullmatch(key):
                    raise ValueError("invalid_selection")
                row = db.execute("SELECT state FROM source_playlist WHERE source=? AND id=?", (source,key)).fetchone()
                if not row:
                    abort(404)
                if row["state"] == "loading" or (row["state"] == "ready" and not force):
                    return jsonify(ok=True)
                db.execute("UPDATE source_playlist SET state='loading',error=NULL WHERE source=? AND id=?", (source,key))
            else:
                if scan["playlists_state"] == "loading" or (scan["playlists_state"] == "ready" and not force):
                    return jsonify(ok=True)
                db.execute("UPDATE scan SET playlists_state='loading' WHERE source=?", (source,))
        if key:
            archive.playlist_worker.submit(archive.scan_playlist, source,key)
        else:
            archive.playlist_worker.submit(archive.discover_playlists, source)
        return jsonify(ok=True)

    @app.get("/api/scans")
    def scan_results():
        source = request.args.get("source", "")
        query = request.args.get("q", "").strip()
        rule = checked_rule(request.args.get("rule", ""))
        kind = request.args.get("kind", "all")
        key = request.args.get("playlist")
        page = max(1, min(1000000, request.args.get("page", 1, type=int)))
        limit = min(50000, max(1, request.args.get("limit", 40, type=int)))
        with archive.db() as db:
            scan = db.execute("SELECT * FROM scan WHERE source=?", (source,)).fetchone()
            if not scan:
                abort(404)
            playlist = (db.execute("SELECT * FROM source_playlist WHERE source=? AND id=?", (source,key)).fetchone()
                        if key else None)
            if key and not playlist:
                abort(404)
            clause = "e.source=?"
            args = [source]
            for term in dict.fromkeys(map(collector.title_key, (query, rule))):
                if term:
                    clause += " AND instr(title_key(e.title),?)>0"
                    args.append(term)
            if kind != "all":
                clause += " AND e.kind=?"
                args.append(kind)
            source_join = "entry e"
            order = "e.ordinal,e.id"
            if playlist:
                source_join += " JOIN playlist_entry p ON p.source=e.source AND p.video_id=e.id"
                clause += " AND p.playlist_id=?"
                args.append(key)
                order = "p.ordinal,e.id"
            join = source_join + " LEFT JOIN video v ON v.id=e.id"
            if request.args.get("ids") == "1":
                ids = [row["id"] for row in db.execute(f"SELECT e.id FROM {join} WHERE {clause} AND v.id IS NULL ORDER BY {order}", args)]
                return jsonify(ids=ids)
            count = db.execute(f"SELECT count(*),sum(v.id IS NULL) FROM {join} WHERE {clause}", args).fetchone()
            rows = db.execute(f"""SELECT e.*,v.state AS saved FROM {join} WHERE {clause}
                                 ORDER BY {order} LIMIT ? OFFSET ?""", (*args,limit,limit*(page-1)))
            playlists = [dict(row) for row in db.execute(
                "SELECT id,title,state FROM source_playlist WHERE source=? ORDER BY ordinal,id", (source,))]
            return jsonify(**dict(scan), total=count[0], selectable=count[1] or 0, entries=[dict(row) for row in rows],
                           playlists=playlists, playlist=dict(playlist) if playlist else None)


    @app.post("/api/channels")
    def add_channel():
        data = body()
        source = collector.youtube_url(data["source"], "channel")[0] if data.get("source") else None
        selected = data.get("selected", [])
        if not valid_selection(selected):
            raise ValueError("invalid_selection")
        with archive.files_lock, archive.db() as db:
            scan = db.execute("SELECT * FROM scan WHERE source=?", (source,)).fetchone() if source else None
            name = label(data.get("name") or (scan["name"] if scan else None))
            channel = archive.create_channel(db, name, source,
                                             preferences(data.get("overrides", {}), partial=True),
                                             bool(source and data.get("auto") is True),
                                             checked_rule(data.get("title_filter", "")))
            if not source and "appearance" in data:
                save_collection_appearance(db, "channel_style", channel["id"], data["appearance"])
            if data.get("description"):
                description = data["description"]
                if not isinstance(description, str) or len(description) > 5000:
                    raise ValueError("invalid_description")
                db.execute("INSERT INTO channel_description VALUES (?,?)", (channel["id"], description.strip()))
            prefs = archive.effective(db, channel)
            queued = 0
            for item in dict.fromkeys(selected):
                entry = db.execute("SELECT * FROM entry WHERE source=? AND id=?", (source, item)).fetchone()
                if entry is None:
                    raise ValueError("invalid_selection")
                queued += archive.enqueue(db, entry, channel, prefs)
        archive.changed.set()
        return jsonify(id=channel["id"], queued=queued), 201

    @app.put("/api/channels/<channel_id>")
    def update_channel(channel_id):
        data = body()
        with archive.files_lock, archive.db() as db:
            channel = archive.channel(db, channel_id)
            auto = int(bool(channel["source"]) and data.get("auto") is True)
            db.execute("""UPDATE channel SET name=?,overrides=?,auto=?,
                          next_sync=CASE WHEN auto<>? THEN 0 ELSE next_sync END,
                          baseline=CASE WHEN auto<>? THEN 0 ELSE baseline END WHERE id=?""",
                       (label(data.get("name")), encode(preferences(data.get("overrides", {}), partial=True)),
                        auto, auto, auto, channel_id))
            if "title_filter" in data:
                db.execute("UPDATE channel SET title_filter=? WHERE id=?",
                           (checked_rule(data["title_filter"]), channel_id))
            if "description" in data:
                description = data["description"]
                if not isinstance(description, str) or len(description) > 5000:
                    raise ValueError("invalid_description")
                db.execute("""INSERT INTO channel_description VALUES (?,?) ON CONFLICT(channel_id)
                    DO UPDATE SET description=excluded.description""", (channel_id, description.strip()))
            if "source" in data:
                source = collector.youtube_url(data["source"], "channel")[0] if data["source"] else None
                if source != channel["source"]:
                    db.execute("UPDATE channel SET source=?,next_sync=0,baseline=0,auto=? WHERE id=?",
                               (source, int(bool(source) and data.get("auto") is True), channel_id))
                    db.execute("DELETE FROM seen WHERE channel_id=?", (channel_id,))
                    if source:
                        archive.catalog.submit(archive.refresh_profile, source)
            current = archive.channel(db, channel_id)
            if current["source"]:
                db.execute("DELETE FROM channel_style WHERE id=?", (channel_id,))
            elif "appearance" in data:
                save_collection_appearance(db, "channel_style", channel_id, data["appearance"])
        return jsonify(ok=True)

    @app.post("/api/channels/<channel_id>/profile")
    def refresh_channel_profile(channel_id):
        with archive.db() as db:
            row = archive.channel(db, channel_id)
        if not row["source"]:
            abort(404)
        archive.catalog.submit(archive.refresh_profile, row["source"])
        return jsonify(ok=True), 202

    @app.get("/source-branding/<video_id>/<asset>")
    def source_image(video_id, asset):
        with archive.db() as db:
            video = archive.ready_video(db, video_id)
            metadata = json.loads(video["metadata"])
            row = db.execute("SELECT * FROM channel_profile WHERE source=?",
                             (metadata.get("source_channel_url"),)).fetchone()
        if not row:
            abort(404)
        profile = json.loads(row["profile"])
        if asset != profile.get("avatar"):
            abort(404)
        return send_from_directory(archive.branding / row["asset_key"], asset, conditional=True)

    @app.get("/branding/<channel_id>/<asset>")
    def channel_image(channel_id, asset):
        with archive.db() as db:
            channel = archive.channel(db, channel_id)
            row = db.execute("SELECT * FROM channel_profile WHERE source=?", (channel["source"],)).fetchone()
        if not row:
            abort(404)
        profile = json.loads(row["profile"])
        if asset not in (profile.get("avatar"), profile.get("banner")):
            abort(404)
        return send_from_directory(archive.branding / row["asset_key"], asset, conditional=True)

    @app.post("/api/channels/<channel_id>/queue")
    def queue_selection(channel_id):
        selected = body().get("selected")
        if not valid_selection(selected):
            raise ValueError("invalid_selection")
        with archive.files_lock, archive.db() as db:
            channel = archive.channel(db, channel_id)
            prefs = archive.effective(db, channel)
            count = 0
            for item in dict.fromkeys(selected):
                entry = db.execute("SELECT * FROM entry WHERE source=? AND id=?", (channel["source"], item)).fetchone()
                if not entry:
                    raise ValueError("invalid_selection")
                count += archive.enqueue(db, entry, channel, prefs)
        archive.changed.set()
        return jsonify(queued=count)

    @app.post("/api/downloads")
    def queue_url():
        data = body()
        url, video_id = collector.youtube_url(data.get("url"), "video")
        overrides = capture_preferences(data.get("overrides", {}))
        kind = "shorts" if "/shorts/" in url else "videos"
        with archive.files_lock, archive.db() as db:
            channel = archive.channel(db, data.get("channel"))
            prefs = {**archive.effective(db, channel), **overrides}
            queued = archive.enqueue(db, {"id": video_id, "url": url, "title": video_id, "kind": kind},
                                     channel, prefs, overrides)
            if not queued:
                queued = db.execute("""UPDATE video SET state='queued',percent=0,error=NULL,
                    progress_phase=NULL,progress_estimated=0,title=CASE WHEN title=url THEN id ELSE title END,url=?,kind=?,
                    channel_id=?,prefs=?,capture_overrides=? WHERE id=? AND state='failed'""",
                                    (url, kind, channel["id"] if channel else None, encode(prefs),
                                     encode(overrides), video_id)).rowcount
                if not queued and db.execute("SELECT 1 FROM video WHERE id=? AND state='removed'", (video_id,)).fetchone():
                    return jsonify(error="restore_removed_first"), 409
        archive.changed.set()
        if workers and queued:
            archive.titles.submit(archive.lookup_download_title, video_id)
        return jsonify(id=video_id, queued=queued)

    @app.delete("/api/downloads/<video_id>")
    def cancel_download(video_id):
        local_change()
        return jsonify(cancelling=archive.cancel_download(video_id))

    @app.get("/api/videos")
    def videos():
        state = request.args.get("state", "ready")
        scope = request.args.get("scope", "")
        term = request.args.get("q", "").strip()
        summary = request.args.get("summary") == "1"
        states = {"jobs": ("queued", "running", "failed", "cancelling"), "removed": ("removed",)}.get(state, ("ready",))
        params = list(states)
        where = f"state IN ({','.join('?' for _ in states)})"
        if term:
            where += " AND instr(fold(title),?)>0"
            params.append(term.casefold())
        order = "created DESC,rowid DESC"
        if scope == "inbox":
            where += " AND channel_id IS NULL"
        elif scope == "continue":
            where += " AND position>0"
            order = "watched_at DESC,rowid DESC"
        elif scope.startswith("channel:"):
            where += " AND channel_id=?"
            params.append(scope.split(":", 1)[1])
        elif scope.startswith("playlist:"):
            where += " AND id IN (SELECT video_id FROM playlist_item WHERE playlist_id=?)"
            params.append(scope.split(":", 1)[1])
        page = min(1000000, max(1, request.args.get("page", 1, type=int)))
        with archive.db() as db:
            db.execute("BEGIN")
            total = db.execute(f"SELECT count(*) FROM video WHERE {where}", params).fetchone()[0]
            rows = db.execute(f"SELECT * FROM video WHERE {where} ORDER BY {order} LIMIT 60 OFFSET ?",
                              (*params, 60 * (page - 1)))
            profiles = {}
            return jsonify(total=total, videos=[library_video(row, db, profiles, summary) for row in rows])

    @app.delete("/api/videos/<video_id>")
    def remove_video(video_id):
        disk = local_change().get("disk")
        if type(disk) is not bool:
            raise ValueError("invalid_delete_option")
        archive.remove_video(video_id, disk)
        return jsonify(ok=True)

    @app.post("/api/videos/delete")
    def remove_selected_videos():
        data = local_change()
        result = archive.remove_videos(data.get("ids"), data.get("disk"))
        return jsonify(result), 202 if result["pending"] else 200

    @app.get("/api/channels/<collection_id>/delete-preview")
    @app.get("/api/playlists/<collection_id>/delete-preview")
    def collection_delete_preview(collection_id):
        kind = "channel" if request.path.startswith("/api/channels/") else "playlist"
        return jsonify(archive.deletion_preview(kind, collection_id))

    @app.delete("/api/channels/<collection_id>")
    @app.delete("/api/playlists/<collection_id>")
    def remove_collection(collection_id):
        data = local_change()
        kind = "channel" if request.path.startswith("/api/channels/") else "playlist"
        result = archive.remove_videos(data.get("ids"), data.get("disk"), (kind, collection_id))
        return jsonify(result), 202 if result["pending"] else 200

    @app.post("/api/videos/<video_id>/restore")
    def restore_video(video_id):
        local_change()
        archive.restore_video(video_id)
        return jsonify(ok=True)

    @app.get("/api/videos/<video_id>/tracks")
    def saved_tracks(video_id):
        with archive.db() as db:
            row = archive.ready_video(db, video_id)
            jobs = [dict(job) for job in db.execute(
                "SELECT kind,code,state,resolved,error,retry_at FROM track_job WHERE video_id=? ORDER BY rowid", (video_id,))]
            video = library_video(row, db)
        if workers and (video.get("thumbnail_source") != "youtube"
                        or not video.get("audio_label_source") or not video.get("source_profile")):
            archive.schedule_video_origin(video_id)
        return jsonify(video=video, jobs=jobs)

    @app.post("/api/videos/<video_id>/tracks/discover")
    def discover_tracks(video_id):
        with archive.db() as db:
            row = archive.ready_video(db, video_id)
        try:
            info = collector.read_tracks(row["url"])
        except Exception as exc:
            return jsonify(error="track_rate_limited" if "429" in str(exc) else "track_failed"), 502
        with archive.files_lock, archive.db() as db:
            current = archive.ready_video(db, video_id)
            metadata = json.loads(current["metadata"])
            for field, value in collector.video_metadata(info).items():
                if value:
                    metadata[field] = value
            archive.save_video_metadata(db, current, metadata)
        return jsonify(collector.available_tracks(info))

    @app.post("/api/videos/<video_id>/tracks")
    def download_track(video_id):
        data = body()
        kind, code = data.get("kind"), data.get("code")
        if kind not in ("audio", "subtitle") or not isinstance(code, str) or not collector.LANGUAGE_TAG.fullmatch(code):
            raise ValueError("invalid_track")
        with archive.db() as db:
            row = archive.ready_video(db, video_id)
            metadata = json.loads(row["metadata"])
            saved = metadata.get("audio_tracks", {}) if kind == "audio" else metadata.get("subtitles", {})
            if code in saved or (kind == "audio" and code.casefold() == (metadata.get("audio") or "").casefold()):
                return jsonify(queued=False)
            retry = db.execute("SELECT retry_at FROM track_job WHERE video_id=? AND kind=? AND code=?",
                               (video_id, kind, code)).fetchone()
            if retry and retry["retry_at"] > timestamp():
                return jsonify(error="track_rate_limited"), 429
            if data.get("retry") is True:
                cursor = db.execute("""UPDATE track_job SET state='queued',error=NULL,retry_at=0
                    WHERE video_id=? AND kind=? AND code=? AND state='failed'""", (video_id, kind, code))
            else:
                cursor = db.execute("""INSERT INTO track_job (video_id,kind,code,allow_auto,exact,state)
               VALUES (?,?,?,1,1,'queued') ON CONFLICT(video_id,kind,code) DO UPDATE
               SET state='queued',allow_auto=1,exact=1,resolved=NULL,error=NULL,retry_at=0 WHERE track_job.state='failed'""",
                          (video_id, kind, code))
        archive.changed.set()
        return jsonify(queued=bool(cursor.rowcount))

    @app.delete("/api/videos/<video_id>/tracks/<kind>/<code>")
    def remove_track(video_id, kind, code):
        saved = local_change().get("saved")
        if (kind not in {"audio", "subtitle"} or not collector.LANGUAGE_TAG.fullmatch(code)
                or not collector.VIDEO_ID.fullmatch(video_id) or type(saved) is not bool):
            raise ValueError("invalid_track")
        try:
            return jsonify(removed=archive.remove_track(video_id, kind, code, saved))
        except OSError:
            logging.exception("Could not delete an audio or subtitle track")
            return jsonify(error="track_delete_failed"), 409

    @app.get("/playback/<video_id>/<code>")
    def alternate_playback(video_id, code):
        return archive.playback_variant(video_id, code)

    @app.post("/api/videos/<video_id>/retry")
    def retry(video_id):
        check_origin()
        data = body() if request.is_json else {}
        with archive.files_lock, archive.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("""SELECT * FROM video WHERE id=? AND
                (state='failed' OR (state='removed' AND error='external_media_missing'))""", (video_id,)).fetchone()
            if not row:
                abort(404)
            if row["state"] == "removed":
                if archive.archived_picture_exists(row):
                    raise ValueError("external_media_returned")
                db.execute("""UPDATE track_job SET state='queued',resolved=NULL,error=NULL,retry_at=0
                    WHERE video_id=? AND state='ready'""", (video_id,))
            overrides = (capture_preferences(data["overrides"]) if "overrides" in data
                         else json.loads(row["capture_overrides"]))
            prefs = {**archive.effective(db, archive.channel(db, row["channel_id"])), **overrides}
            db.execute("""UPDATE video SET state='queued',percent=0,error=NULL,
                progress_phase=NULL,progress_estimated=0,prefs=?,
                capture_overrides=? WHERE id=?""", (encode(prefs), encode(overrides), video_id))
        archive.changed.set()
        if workers and row["title"] in {row["url"], row["id"]}:
            archive.titles.submit(archive.lookup_download_title, video_id)
        return jsonify(ok=True)

    @app.post("/api/videos/<video_id>/progress")
    def progress(video_id):
        position = body().get("position")
        if type(position) not in (int, float) or not math.isfinite(position) or position < 0:
            raise ValueError("invalid_position")
        with archive.db() as db:
            db.execute("UPDATE video SET position=?,watched_at=? WHERE id=? AND state='ready'",
                       (position, timestamp(), video_id))
        return jsonify(ok=True)

    @app.post("/api/videos/<video_id>/move")
    def move(video_id):
        data = body()
        archive.move(video_id, data.get("channel"), data.get("name"))
        return jsonify(ok=True)

    @app.post("/api/playlists")
    def add_playlist():
        data = body()
        video_id = data.get("video")
        if video_id is not None and video_id != "" and (not isinstance(video_id, str) or not collector.VIDEO_ID.fullmatch(video_id)):
            raise ValueError("invalid_selection")
        playlist_id = uuid.uuid4().hex[:10]
        with archive.files_lock:
            with archive.db() as db:
                db.execute("INSERT INTO playlist VALUES (?,?)", (playlist_id, label(data.get("name"))))
                if "appearance" in data:
                    save_collection_appearance(db, "playlist_style", playlist_id, data["appearance"], "list")
                if video_id:
                    db.execute("INSERT INTO playlist_item VALUES (?,?)", (playlist_id, video_id))
            archive.refresh_playlist_files([playlist_id])
        return jsonify(id=playlist_id), 201

    @app.put("/api/playlists/<playlist_id>/appearance")
    def update_playlist_appearance(playlist_id):
        data = local_change()
        with archive.db() as db:
            if not db.execute("SELECT 1 FROM playlist WHERE id=?", (playlist_id,)).fetchone():
                abort(404)
            save_collection_appearance(db, "playlist_style", playlist_id, data.get("appearance"), "list")
        return jsonify(ok=True)

    @app.put("/api/playlists/<playlist_id>/videos/<video_id>")
    def add_to_playlist(playlist_id, video_id):
        with archive.files_lock:
            with archive.db() as db:
                db.execute("INSERT OR IGNORE INTO playlist_item VALUES (?,?)", (playlist_id, video_id))
            archive.refresh_playlist_files([playlist_id])
        return jsonify(ok=True)

    @app.delete("/api/playlists/<playlist_id>/videos/<video_id>")
    def remove_from_playlist(playlist_id, video_id):
        with archive.files_lock:
            with archive.db() as db:
                db.execute("DELETE FROM playlist_item WHERE playlist_id=? AND video_id=?", (playlist_id, video_id))
            archive.refresh_playlist_files([playlist_id])
        return jsonify(ok=True)

    @app.get("/api/playlists/<playlist_id>/export")
    def export_playlist(playlist_id):
        return archive.export_playlist(playlist_id)

    @app.get("/media/<video_id>/<asset>")
    def media(video_id, asset):
        with archive.files_lock, archive.db() as db:
            row = db.execute("SELECT * FROM video WHERE id=? AND state='ready'", (video_id,)).fetchone()
            if not row:
                abort(404)
            meta = json.loads(row["metadata"])
            if asset not in {meta["filename"], meta.get("thumbnail"), *meta.get("subtitles", {}).values()}:
                abort(404)
            folder = archive.video_bundle(row)
            archive.playlist_asset(folder, asset)
            return send_from_directory(folder, asset, conditional=True)

    return app


if __name__ == "__main__":
    from waitress import serve

    logging.basicConfig(level=logging.INFO)
    serve(create_app(), host="0.0.0.0", port=8080, threads=8)
