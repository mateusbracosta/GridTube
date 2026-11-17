import hashlib
import json
import logging
import math
import os
import shutil
import sqlite3
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest

import collector


DEFAULTS = {"download_mode": "compact", "quality": "720", "shorts": "include", "audio": "original",
            "subtitles": "both", "auto_subtitles": True}
CHOICES = {"download_mode": {"compact", "original"},
           "quality": {"360", "480", "720", "1080", "1440", "2160", "best"},
           "shorts": {"include", "exclude", "only"}, "audio": {"original", "pt-BR", "en"},
           "subtitles": {"none", "pt-BR", "en", "both"}}
SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), prefs TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS channel (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, folder TEXT NOT NULL, source TEXT UNIQUE,
    overrides TEXT NOT NULL, auto INTEGER DEFAULT 0, next_sync INTEGER NOT NULL DEFAULT 0,
    baseline INTEGER NOT NULL DEFAULT 0, title_filter TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS playlist (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS video (
    id TEXT PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL,
    channel_id TEXT REFERENCES channel(id), kind TEXT NOT NULL,
    state TEXT NOT NULL, prefs TEXT NOT NULL, capture_overrides TEXT NOT NULL DEFAULT '{}',
    metadata TEXT, folder TEXT,
    pending_folder TEXT, pending_channel TEXT, percent INTEGER DEFAULT 0, error TEXT,
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


class Archive:
    def __init__(self, data, root):
        self.data = Path(data).resolve()
        self.library = Path(root).resolve() / "library"
        self.work = self.library.parent / "work"
        self.branding = self.data / "branding"
        self.playback = self.work / "playback"
        self.playback_lock = threading.Lock()
        for path in (self.data, self.library, self.work, self.branding, self.playback):
            path.mkdir(parents=True, exist_ok=True)
        self.changed = threading.Event()
        self.catalog = ThreadPoolExecutor(max_workers=1, thread_name_prefix="catalog")
        self.playlist_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="playlist-scan")
        self.origins = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-origin")
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
            track_columns = {row["name"] for row in db.execute("PRAGMA table_info(track_job)")}
            if "retry_at" not in track_columns:
                db.execute("ALTER TABLE track_job ADD COLUMN retry_at INTEGER NOT NULL DEFAULT 0")
            db.execute("INSERT OR IGNORE INTO settings VALUES (1,?)", (encode(DEFAULTS),))
            db.execute("UPDATE scan SET state='error', error='interrupted' WHERE state='loading'")
            pending = db.execute("SELECT * FROM video WHERE pending_folder IS NOT NULL").fetchall()
            for item in pending:
                self.finish_publish(db, item)
            db.execute("UPDATE video SET state='queued', percent=0 WHERE state='running'")
            db.execute("UPDATE track_job SET state='queued' WHERE state='running'")
            db.execute("""UPDATE video SET state='queued',percent=0,error=NULL
                          WHERE state='failed' AND (lower(error) LIKE '%unable to download video subtitles%'
                            OR error LIKE '%Postprocessing: Conversion failed!%')""")

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

    def channel(self, db, channel_id):
        if not channel_id:
            return None
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
        if rule and entry["title"] != entry["url"] and collector.title_key(rule) not in collector.title_key(entry["title"]):
            return 0
        cursor = db.execute(
            """INSERT INTO video (id,url,title,channel_id,kind,prefs,capture_overrides,state,created)
               VALUES (?,?,?,?,?,?,?,'queued',?) ON CONFLICT(id) DO NOTHING""",
            (entry["id"], entry["url"], entry["title"], channel["id"] if channel else None,
             entry["kind"], encode(prefs), encode(capture_overrides or {}), timestamp()))
        return cursor.rowcount

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

    def discover_playlists(self, source):
        try:
            entries = list(dict.fromkeys(collector.channel_playlists(source)))
            with self.db() as db:
                db.executemany("""INSERT INTO source_playlist (source,id,title,ordinal)
                    VALUES (?,?,?,?) ON CONFLICT(source,id) DO UPDATE SET title=excluded.title,ordinal=excluded.ordinal""",
                    [(source, key, title, index) for index, (key,title) in enumerate(entries)])
                db.execute("UPDATE scan SET playlists_state='ready' WHERE source=?", (source,))
        except Exception:
            logging.exception("Playlist listing failed")
            with self.db() as db:
                db.execute("UPDATE scan SET playlists_state='error' WHERE source=?", (source,))

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
            profile[name] = filename
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
                WHERE v.state='ready' AND (json_extract(v.metadata,'$.audio_label_source') IS NULL
                    OR json_extract(v.metadata,'$.source_channel_url') IS NULL OR p.source IS NULL)
                ORDER BY v.created DESC LIMIT 40""").fetchall()
        for row in pending:
            self.schedule_video_origin(row["id"])

    def hydrate_video_origin(self, video_id):
        try:
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

    def playback_variant(self, video_id, code):
        with self.playback_lock, self.files_lock:
            with self.db() as db:
                row = self.ready_video(db, video_id)
                metadata = json.loads(row["metadata"])
            audio = metadata.get("audio_tracks", {}).get(code)
            if not audio:
                abort(404)
            folder = self.library / row["folder"]
            base_path = folder / metadata["filename"]
            audio_path = folder / audio
            signature = f"{video_id}:{code}:{base_path.stat().st_mtime_ns}:{audio_path.stat().st_mtime_ns}"
            variant = self.playback / (hashlib.sha256(signature.encode()).hexdigest() + base_path.suffix)
            if not variant.exists():
                with tempfile.TemporaryDirectory(prefix="mux-", dir=self.playback) as temp:
                    staged = Path(temp) / variant.name
                    codec = "libopus" if base_path.suffix == ".webm" else "copy"
                    collector.mux_video(base_path, staged, code, audio_path, audio_codec=codec)
                    staged.replace(variant)
            os.utime(variant, ns=(time.time_ns(), variant.stat().st_mtime_ns))
            response = send_from_directory(self.playback, variant.name, conditional=True)
            self.prune_playback(variant)
            return response

    def prune_playback(self, current):
        budget = 4 * 1024 ** 3
        cached = sorted((path for path in self.playback.iterdir() if path.suffix in {".mp4", ".webm"}),
                        key=lambda path: path.stat().st_atime_ns, reverse=True)
        used = sum(path.stat().st_size for path in cached)
        for path in reversed(cached):
            if used <= budget:
                break
            if path != current:
                try:
                    size = path.stat().st_size
                    path.unlink()
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
                with self.db() as db:
                    current = self.channel(db, channel["id"])
                    if not current["auto"]:
                        continue
                    prefs = self.effective(db, current)
                    for entry in entries:
                        new = db.execute("INSERT OR IGNORE INTO seen VALUES (?,?)",
                                         (current["id"], entry["id"])).rowcount
                        if new and current["baseline"] and allowed(entry["kind"], prefs["shorts"]):
                            self.enqueue(db, entry, current, prefs)
                    if entries:
                        db.execute("UPDATE channel SET baseline=1 WHERE id=?", (current["id"],))
            except Exception:
                logging.exception("Subscription check failed")
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
        target = self.library / row["pending_folder"]
        if (target / "video.json").is_file():
            meta = json.loads((target / "video.json").read_text(encoding="utf-8"))
            if not (target / meta["filename"]).is_file():
                raise RuntimeError("Published bundle is missing its video")
            db.execute("""UPDATE video SET folder=pending_folder, channel_id=pending_channel,
                          pending_folder=NULL,pending_channel=NULL,state='ready',metadata=?,
                          title=?,percent=100,error=NULL WHERE id=?""",
                       (encode(meta), meta["title"], row["id"]))
            if row["state"] != "ready":
                self.queue_default_subtitles(db, row)
        else:
            db.execute("UPDATE video SET pending_folder=NULL,pending_channel=NULL WHERE id=?", (row["id"],))

    def capture(self, item):
        video_id = item["id"]
        last_progress = -1

        def progress(value):
            nonlocal last_progress
            if value > last_progress:
                with self.db() as db:
                    db.execute("UPDATE video SET percent=? WHERE id=?", (value, video_id))
                last_progress = value

        inputs = self.work / "inputs" / video_id
        inputs.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"{video_id}-", dir=self.work) as scratch:
            bundle = Path(scratch) / "bundle"
            bundle.mkdir()
            meta = collector.download(item["url"], json.loads(item["prefs"]), inputs, bundle, progress)
            collector.write_manifest(bundle, meta)
            with self.files_lock:
                with self.db() as db:
                    channel = self.channel(db, item["channel_id"])
                    folder = str(Path(channel["folder"] if channel else "Avulsos") /
                                 f"{collector.safe_name(meta['title'])} [{video_id}]")
                    db.execute("UPDATE video SET pending_folder=?,pending_channel=? WHERE id=?",
                               (folder, item["channel_id"], video_id))
                target = self.library / folder
                target.parent.mkdir(parents=True, exist_ok=True)
                bundle.rename(target)
                with self.db() as db:
                    self.finish_publish(db, db.execute("SELECT * FROM video WHERE id=?", (video_id,)).fetchone())
        self.schedule_video_origin(video_id)
        try:
            shutil.rmtree(inputs)
        except OSError:
            logging.warning("Could not clear temporary inputs for %s", video_id)

    def worker(self):
        while True:
            self.changed.clear()
            with self.db() as db:
                track = db.execute("""UPDATE track_job SET state='running' WHERE rowid=(
                    SELECT rowid FROM track_job WHERE state='queued' ORDER BY exact DESC,rowid LIMIT 1
                ) RETURNING rowid AS job_id,*""").fetchone()
            if track:
                try:
                    self.fetch_queued_track(track)
                except Exception as exc:
                    error = str(exc) if str(exc) in {"track_unavailable", "track_invalid", "track_rate_limited"} else "track_failed"
                    logging.warning("Track job failed for %s (%s): %s", track["video_id"], track["code"], error)
                    with self.db() as db:
                        retry_at = timestamp() + exc.seconds if isinstance(exc, collector.TrackRateLimited) else 0
                        db.execute("UPDATE track_job SET state='failed',error=?,retry_at=? WHERE rowid=?",
                                   (error, retry_at, track["job_id"]))
                continue
            with self.db() as db:
                item = db.execute("""UPDATE video SET state='running' WHERE id=(
                    SELECT id FROM video WHERE state='queued' ORDER BY created,rowid LIMIT 1
                ) RETURNING *""").fetchone()
            if item is None:
                self.changed.wait(2)
                continue
            try:
                self.capture(item)
            except Exception as exc:
                logging.exception("Capture failed for %s", item["id"])
                with self.db() as db:
                    row = db.execute("SELECT * FROM video WHERE id=?", (item["id"],)).fetchone()
                    if row["pending_folder"] and (self.library / row["pending_folder"]).is_dir():
                        self.finish_publish(db, row)
                    else:
                        db.execute("""UPDATE video SET state='failed',error=?,
                                      pending_folder=NULL,pending_channel=NULL WHERE id=?""",
                                   (str(exc)[-450:], item["id"]))

    def move(self, video_id, target_id, new_name=None):
        with self.files_lock:
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


def library_video(row, db):
    meta = json.loads(row["metadata"]) if row["metadata"] else {}
    if meta.get("source_channel_url"):
        profile = db.execute("SELECT profile FROM channel_profile WHERE source=?",
                             (meta["source_channel_url"],)).fetchone()
        if profile:
            meta["source_profile"] = json.loads(profile["profile"])
    if row["state"] != "ready":
        meta["capture_overrides"] = json.loads(row["capture_overrides"])
    return {**meta, **{key: row[key] for key in
                      ("id", "title", "url", "channel_id", "kind", "state", "position",
                       "percent", "error", "watched_at", "created")}}


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

    def body():
        value = request.get_json()
        if not isinstance(value, dict):
            raise BadRequest()
        return value

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

    @app.get("/api/state")
    def state():
        with archive.db() as db:
            channels = []
            for row in db.execute("""SELECT c.*,p.profile,d.description AS custom_description FROM channel c
                     LEFT JOIN channel_profile p ON c.source=p.source
                     LEFT JOIN channel_description d ON c.id=d.channel_id ORDER BY c.name COLLATE NOCASE"""):
                channel = dict(row)
                channel["overrides"] = json.loads(row["overrides"])
                channel["profile"] = json.loads(row["profile"]) if row["profile"] else {}
                channels.append(channel)
            playlists = [dict(row) for row in db.execute("SELECT * FROM playlist ORDER BY name COLLATE NOCASE")]
            counts = dict(db.execute("SELECT state,count(*) FROM video GROUP BY state"))
            return jsonify(settings=archive.defaults(db), channels=channels, playlists=playlists, counts=counts)

    @app.put("/api/settings")
    def save_settings():
        prefs = preferences(body())
        with archive.db() as db:
            db.execute("UPDATE settings SET prefs=? WHERE id=1", (encode(prefs),))
        return jsonify(prefs)

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
            clause = "e.source=? AND instr(title_key(e.title),title_key(?))>0 AND instr(title_key(e.title),title_key(?))>0 AND (?='all' OR e.kind=?)"
            args = [source, query, rule, kind, kind]
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
        with archive.db() as db:
            scan = db.execute("SELECT * FROM scan WHERE source=?", (source,)).fetchone() if source else None
            name = label(data.get("name") or (scan["name"] if scan else None))
            channel = archive.create_channel(db, name, source,
                                             preferences(data.get("overrides", {}), partial=True),
                                             bool(source and data.get("auto") is True),
                                             checked_rule(data.get("title_filter", "")))
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
        with archive.db() as db:
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
        with archive.db() as db:
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
        with archive.db() as db:
            channel = archive.channel(db, data.get("channel") or None)
            prefs = {**archive.effective(db, channel), **overrides}
            queued = archive.enqueue(db, {"id": video_id, "url": url, "title": url, "kind": kind},
                                     channel, prefs, overrides)
            if not queued:
                queued = db.execute("""UPDATE video SET state='queued',percent=0,error=NULL,url=?,kind=?,
                    channel_id=?,prefs=?,capture_overrides=? WHERE id=? AND state='failed'""",
                                    (url, kind, channel["id"] if channel else None, encode(prefs),
                                     encode(overrides), video_id)).rowcount
        archive.changed.set()
        return jsonify(id=video_id, queued=queued)

    @app.get("/api/videos")
    def videos():
        state = request.args.get("state", "ready")
        scope = request.args.get("scope", "")
        term = request.args.get("q", "").strip()
        states = ("queued", "running", "failed") if state == "jobs" else ("ready",)
        params = [*states, term]
        where = f"state IN ({','.join('?' for _ in states)}) AND instr(fold(title),fold(?))>0"
        order = "created DESC,rowid DESC"
        if scope == "inbox":
            where += " AND channel_id IS NULL"
        elif scope == "continue":
            where += " AND position>0"
            order = "watched_at DESC"
        elif scope.startswith("channel:"):
            where += " AND channel_id=?"
            params.append(scope.split(":", 1)[1])
        elif scope.startswith("playlist:"):
            where += " AND id IN (SELECT video_id FROM playlist_item WHERE playlist_id=?)"
            params.append(scope.split(":", 1)[1])
        page = max(1, request.args.get("page", 1, type=int))
        with archive.db() as db:
            total = db.execute(f"SELECT count(*) FROM video WHERE {where}", params).fetchone()[0]
            rows = db.execute(f"SELECT * FROM video WHERE {where} ORDER BY {order} LIMIT 60 OFFSET ?",
                              (*params, 60 * (page - 1)))
            return jsonify(total=total, videos=[library_video(row, db) for row in rows])

    @app.get("/api/videos/<video_id>/tracks")
    def saved_tracks(video_id):
        with archive.db() as db:
            row = archive.ready_video(db, video_id)
            jobs = [dict(job) for job in db.execute(
                "SELECT kind,code,state,resolved,error,retry_at FROM track_job WHERE video_id=? ORDER BY rowid", (video_id,))]
            video = library_video(row, db)
        if workers and (not video.get("audio_label_source") or not video.get("source_profile")):
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

    @app.get("/playback/<video_id>/<code>")
    def alternate_playback(video_id, code):
        return archive.playback_variant(video_id, code)

    @app.post("/api/videos/<video_id>/retry")
    def retry(video_id):
        data = body() if request.is_json else {}
        with archive.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM video WHERE id=? AND state='failed'", (video_id,)).fetchone()
            if not row:
                abort(404)
            overrides = (capture_preferences(data["overrides"]) if "overrides" in data
                         else json.loads(row["capture_overrides"]))
            prefs = {**archive.effective(db, archive.channel(db, row["channel_id"])), **overrides}
            db.execute("""UPDATE video SET state='queued',percent=0,error=NULL,prefs=?,
                capture_overrides=? WHERE id=?""", (encode(prefs), encode(overrides), video_id))
        archive.changed.set()
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
        archive.move(video_id, data.get("channel") or None, data.get("name"))
        return jsonify(ok=True)

    @app.post("/api/playlists")
    def add_playlist():
        data = body()
        playlist_id = uuid.uuid4().hex[:10]
        with archive.db() as db:
            db.execute("INSERT INTO playlist VALUES (?,?)", (playlist_id, label(data.get("name"))))
            if data.get("video"):
                db.execute("INSERT INTO playlist_item VALUES (?,?)", (playlist_id, data["video"]))
        return jsonify(id=playlist_id), 201

    @app.put("/api/playlists/<playlist_id>/videos/<video_id>")
    def add_to_playlist(playlist_id, video_id):
        with archive.db() as db:
            db.execute("INSERT OR IGNORE INTO playlist_item VALUES (?,?)", (playlist_id, video_id))
        return jsonify(ok=True)

    @app.delete("/api/playlists/<playlist_id>/videos/<video_id>")
    def remove_from_playlist(playlist_id, video_id):
        with archive.db() as db:
            db.execute("DELETE FROM playlist_item WHERE playlist_id=? AND video_id=?", (playlist_id, video_id))
        return jsonify(ok=True)

    @app.get("/media/<video_id>/<asset>")
    def media(video_id, asset):
        with archive.files_lock, archive.db() as db:
            row = db.execute("SELECT * FROM video WHERE id=? AND state='ready'", (video_id,)).fetchone()
            if not row:
                abort(404)
            meta = json.loads(row["metadata"])
            if asset not in {meta["filename"], meta.get("thumbnail"), *meta.get("subtitles", {}).values()}:
                abort(404)
            return send_from_directory(archive.library / row["folder"], asset, conditional=True)

    return app


if __name__ == "__main__":
    from waitress import serve

    logging.basicConfig(level=logging.INFO)
    serve(create_app(), host="0.0.0.0", port=8080, threads=8)
