import io
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import collector
from app import create_app


class FeedSettingsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.app = create_app(self.root / "data", self.root / "archive", workers=False)
        self.client = self.app.test_client()
        self.archive = self.app.extensions["archive"]
        self.channel = self.client.post("/api/channels", json={"name": "Fixture"}).json["id"]

    def add(self, n, state="ready", date="20261120", age=0, watched=0, new=0, downloaded=None):
        video_id = f"item{n:07d}"
        self.client.post("/api/downloads", json={"url": f"https://youtu.be/{video_id}", "channel": self.channel})
        folder = self.archive.library / f"Avulsos/Video [{video_id}]"
        folder.mkdir(parents=True)
        (folder / "main.mp4").write_bytes(b"fixture media")
        (folder / "main.en.vtt").write_bytes(b"WEBVTT\n")
        meta = {"id": video_id, "title": f"Video {n}", "upload_date": date, "duration": 120,
                "filename": "main.mp4", "subtitles": {"en": "main.en.vtt"}}
        if downloaded is not None:
            meta["downloaded_at"] = downloaded
        collector.write_manifest(folder, meta)
        with self.archive.db() as db:
            db.execute("UPDATE video SET state=?,metadata=?,folder=?,created=?,position=15,watched=?,unopened_auto=?,percent=16,progress_phase='video' WHERE id=?",
                       (state, json.dumps(meta), str(folder.relative_to(self.archive.library)), int(time.time())-age*86400, watched, new, video_id))
        return video_id, folder

    def test_new_settings_default_to_no_limit_never_and_open_only(self):
        prefs = self.client.get("/api/state").json["settings"]
        self.assertEqual([prefs[k] for k in ("max_duration", "auto_delete_days", "new_badge_days")], [0, 0, 0])
        _, folder = self.add(1, age=500)
        self.assertEqual(self.archive.expire_videos(), 0)
        self.assertTrue((folder / "main.mp4").exists())
        for value in (-1, True, 0.5, "12"):
            self.assertEqual(self.client.put("/api/settings", json={"max_duration": value}).status_code, 400)

    def test_duration_limit_is_enforced_before_transfer_including_unknown_duration(self):
        self.client.put("/api/settings", json={"max_duration": 2})
        for n, duration, error in ((1, 121, "duration_limit_exceeded"), (2, None, "duration_unavailable")):
            self.client.post("/api/downloads", json={"url": f"https://youtu.be/item{n:07d}"})
            with self.archive.db() as db:
                row = dict(db.execute("SELECT * FROM video WHERE id=?", (f"item{n:07d}",)).fetchone())
            with patch("collector.read_video", return_value={"id": row["id"], "title": "Fixture", "duration": duration}), patch("collector.format_choice") as choose:
                with self.assertRaisesRegex(ValueError, error):
                    self.archive.capture(row)
                choose.assert_not_called()
        collector.require_capture_allowed("videos", {"max_duration": 2}, 120, require_duration=True)
        self.assertTrue(collector.capture_allowed("videos", {"max_duration": 0}, 999999))

    def test_channel_can_override_duration_with_zero_for_no_limit(self):
        self.client.put("/api/settings", json={"max_duration": 2})
        self.client.put(f"/api/channels/{self.channel}", json={"name": "Fixture", "overrides": {"max_duration": 0}})
        with self.archive.db() as db:
            prefs = self.archive.effective(db, self.archive.channel(db, self.channel))
        self.assertEqual(prefs["max_duration"], 0)
        self.assertTrue(collector.capture_allowed("videos", prefs, 900))

    def test_retention_deletes_old_bundles_but_keeps_recent_downloads_and_queue(self):
        old, folder = self.add(1, age=3)
        recent, recent_folder = self.add(2, age=20, downloaded=int(time.time()))
        queued, queued_folder = self.add(3, state="queued", age=10)
        self.client.put("/api/settings", json={"auto_delete_days": 2})
        self.assertEqual(self.archive.expire_videos(), 1)
        self.assertFalse(folder.exists())
        self.assertTrue(recent_folder.exists())
        self.assertTrue(queued_folder.exists())
        with self.archive.db() as db:
            self.assertIsNone(db.execute("SELECT id FROM video WHERE id=?", (old,)).fetchone())
        self.assertEqual(self.client.get("/api/videos").json["videos"][0]["id"], recent)

    def test_retention_respects_export_in_use_and_reports_failure(self):
        video_id, folder = self.add(1, age=5)
        self.archive.exporting[video_id] = 1
        self.client.put("/api/settings", json={"auto_delete_days": 1})
        self.assertEqual(self.archive.expire_videos(), 0)
        self.assertTrue(folder.exists())
        with self.archive.db() as db:
            self.assertTrue(db.execute("SELECT 1 FROM system_event WHERE code='retention_failed'").fetchone())

    def test_new_badge_default_waits_for_open_and_custom_duration_expires(self):
        old, folder = self.add(1, age=90, new=1)
        current, _ = self.add(2, age=90, new=1, downloaded=int(time.time()))
        self.assertTrue(all(v["is_new"] for v in self.client.get("/api/videos").json["videos"]))
        self.client.put("/api/settings", json={"new_badge_days": 2})
        videos = {v["id"]: v for v in self.client.get("/api/videos").json["videos"]}
        self.assertFalse(videos[old]["is_new"])
        self.assertTrue(videos[current]["is_new"])
        self.assertTrue(folder.exists())
        self.client.post(f"/api/videos/{current}/opened", json={})
        self.assertFalse(self.client.get("/api/videos?filter=new").json["total"])

    def test_manual_watched_state_persists_and_preserves_progress(self):
        first, _ = self.add(1, new=1)
        self.add(2)
        self.assertEqual(self.client.post(f"/api/videos/{first}/watched", json={"watched": True}).status_code, 200)
        row = self.client.get("/api/videos?scope=watched").json["videos"][0]
        self.assertEqual((row["id"], row["watched"], row["position"], row["is_new"]), (first, True, 15, False))
        restored = create_app(self.root / "data", self.root / "archive", workers=False).test_client()
        self.assertEqual(restored.get("/api/videos?filter=unwatched").json["total"], 1)
        self.assertEqual(restored.get("/api/videos").json["total"], 2)
        self.assertEqual(restored.post(f"/api/videos/{first}/watched", json={"watched": "yes"}).status_code, 400)
        restored.post(f"/api/videos/{first}/watched", json={"watched": False})
        self.assertEqual(restored.get("/api/videos?scope=watched").json["total"], 0)

    def test_library_includes_pending_cards_and_filters_before_counting(self):
        self.add(1, new=1)
        self.add(2, date="20261118", watched=1)
        self.add(3, date="20261115")
        self.add(4, state="running")
        self.add(5, state="failed")
        self.add(6, state="removed")
        result = self.client.get(f"/api/videos?state=library&scope=channel:{self.channel}&summary=1").json
        self.assertEqual(result["total"], 5)
        pending = next(v for v in result["videos"] if v["state"] == "running")
        self.assertEqual((pending["percent"], pending["duration"]), (16, 120))
        self.assertTrue(pending["preview_thumbnail"].endswith('/item0000004/hqdefault.jpg'))
        today = "&today=20261120"
        query = "/api/videos?state=library"
        self.assertEqual(self.client.get(query+"&filter=week"+today).json["total"], 4)
        self.assertEqual(self.client.get(query+"&filter=today&filter=unwatched"+today).json["total"], 3)
        self.assertEqual(self.client.get(query+"&filter=new&filter=unwatched").json["total"], 1)
        self.assertEqual(self.client.get(query+"&filter=progress&filter=today"+today).json["total"], 2)
        oldest = self.client.get(query+"&sort=oldest").json["videos"]
        newest = self.client.get(query+"&sort=newest").json["videos"]
        self.assertEqual([v["id"] for v in oldest], list(reversed([v["id"] for v in newest])))
        for suffix in ("&sort=bad", "&filter=bad", "&filter=today&today=20261399"):
            self.assertEqual(self.client.get(query+suffix).status_code, 400)

    def test_old_backup_without_watched_flag_is_restorable(self):
        self.client.post("/api/downloads", json={"url": "https://youtu.be/item0000001"})
        records = [json.loads(line) for line in self.client.get("/api/system/backup").data.splitlines()]
        for record in records:
            if record.get("table") == "video":
                record["row"].pop("watched")
                record["row"].pop("unopened_auto")
        payload = "\n".join(json.dumps(r) for r in records).encode()+b"\n"
        preview = self.client.post("/api/system/backup/preview", data={"backup": (io.BytesIO(payload), "old.jsonl")})
        self.assertEqual(preview.status_code, 200, preview.json)

    def test_old_database_migrates_watched_without_changing_media(self):
        _, folder = self.add(1)
        with sqlite3.connect(self.root / "data/library.sqlite") as db:
            db.execute("DROP INDEX video_watched_publication")
            db.execute("ALTER TABLE video DROP COLUMN watched")
        restored = create_app(self.root / "data", self.root / "archive", workers=False).test_client()
        self.assertFalse(restored.get("/api/videos").json["videos"][0]["watched"])
        self.assertEqual((folder / "main.mp4").read_bytes(), b"fixture media")

    def test_ignored_video_is_hidden_without_losing_media_progress_or_memberships(self):
        video_id, folder = self.add(1, new=1, watched=1)
        playlist = self.client.post("/api/playlists", json={"name": "Saved", "video": video_id}).json["id"]
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        response = self.client.post(f"/api/videos/{video_id}/ignored", json={"ignored": True})
        self.assertEqual(response.status_code, 200, response.json)
        for query in ("", f"scope=channel:{self.channel}", f"scope=playlist:{playlist}", "scope=watched", "scope=continue"):
            self.assertEqual(self.client.get("/api/videos?"+query).json["total"], 0)
        row = self.client.get("/api/videos?scope=ignored").json["videos"][0]
        self.assertEqual((row["id"], row["position"], row["watched"], row["ignored"]), (video_id, 15, True, True))
        self.assertEqual({p.name: p.read_bytes() for p in folder.iterdir()}, before)
        with self.archive.db() as db:
            self.assertTrue(db.execute("SELECT 1 FROM playlist_item WHERE video_id=?", (video_id,)).fetchone())
        restored = create_app(self.root / "data", self.root / "archive", workers=False).test_client()
        self.assertEqual(restored.get("/api/videos?scope=ignored").json["total"], 1)
        restored.post(f"/api/videos/{video_id}/ignored", json={"ignored": False})
        self.assertEqual(restored.get(f"/api/videos?scope=playlist:{playlist}").json["total"], 1)
        self.assertEqual(restored.post(f"/api/videos/{video_id}/ignored", json={"ignored": "yes"}).status_code, 400)

    def test_backup_restore_preserves_watched_ignored_and_custom_preferences(self):
        self.add(1, watched=1)
        self.client.post("/api/videos/item0000001/ignored", json={"ignored": True})
        self.client.put("/api/settings", json={"max_duration": 30, "new_badge_days": 5})
        backup = self.client.get("/api/system/backup").data
        preview = self.client.post("/api/system/backup/preview", data={"backup": (io.BytesIO(backup), "current.jsonl")})
        self.assertEqual(preview.status_code, 200, preview.json)
        token = preview.json["token"]
        self.client.post("/api/videos/item0000001/ignored", json={"ignored": False})
        self.client.post("/api/system/backup/restore", json={"token": token})
        restored = create_app(self.root / "data", self.root / "archive", workers=False).test_client()
        self.assertEqual(restored.get(f"/api/system/backup/status/{token}").json["status"], "verified")
        row = restored.get("/api/videos?scope=ignored").json["videos"][0]
        self.assertTrue(row["watched"] and row["ignored"])
        prefs = restored.get("/api/state").json["settings"]
        self.assertEqual((prefs["max_duration"], prefs["new_badge_days"], prefs["auto_delete_days"]), (30, 5, 0))
