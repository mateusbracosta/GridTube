import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collector
from app import create_app


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.root = Path(work.name)
        self.open_archive()

    def open_archive(self):
        app = create_app(self.root / "data", self.root / "archive", workers=False)
        self.archive = app.extensions["archive"]
        self.client = app.test_client()

    def queue_video(self, video_id):
        response = self.client.post("/api/downloads", json={"url": "https://youtu.be/" + video_id,
                                                            "overrides": {"subtitles": "none"}})
        self.assertEqual(response.get_json()["queued"], 1)

    def test_incomplete_publication_preserves_the_folder_and_allows_retry(self):
        video_id = "fixture0001"
        self.queue_video(video_id)
        relative = f"Avulsos/Fixture [{video_id}]"
        folder = self.archive.library / relative
        folder.mkdir(parents=True)
        collector.write_manifest(folder, {"filename": "missing.mp4", "title": "Fixture"})
        (folder / "retained.txt").write_text("previous bundle", encoding="utf-8")
        with self.archive.db() as db:
            db.execute("UPDATE video SET state='running', pending_folder=? WHERE id=?", (relative, video_id))

        self.open_archive()
        self.assertEqual(self.client.get("/healthz").status_code, 204)
        self.assertEqual(self.client.get("/api/videos?state=jobs").json["videos"][0]["error"], "publish_incomplete")
        self.assertEqual(self.client.post(f"/api/videos/{video_id}/retry", json={}).status_code, 200)
        with self.archive.db() as db:
            item = dict(db.execute("SELECT * FROM video WHERE id=?", (video_id,)).fetchone())

        def download(url, prefs, work, bundle, progress, *, on_title):
            on_title("Fixture")
            (bundle / "Fixture.mp4").write_bytes(b"retry")
            return {"title": "Fixture", "filename": "Fixture.mp4"}

        with patch.object(collector, "download", side_effect=download), patch.object(self.archive, "schedule_video_origin"):
            self.archive.capture(item)
        self.assertEqual((folder / "retained.txt").read_text(encoding="utf-8"), "previous bundle")
        self.assertEqual((folder.parent / f"Fixture (2) [{video_id}]" / "Fixture.mp4").read_bytes(), b"retry")
        self.assertEqual(self.client.get("/api/state").json["counts"]["ready"], 1)

    def test_temporary_database_failure_requeues_interrupted_work(self):
        video_id = "fixture0002"
        self.queue_video(video_id)
        with self.archive.db() as db:
            db.execute("UPDATE video SET state='running' WHERE id=?", (video_id,))

        class StopTest(Exception):
            pass

        with patch.object(self.archive, "download_loop", side_effect=[sqlite3.OperationalError("database is locked"), StopTest]), \
             patch("app.time.sleep"), self.assertLogs(level="WARNING"):
            with self.assertRaises(StopTest):
                self.archive.worker()
        self.assertEqual(self.client.get("/api/state").json["counts"], {"queued": 1})

    def test_queued_title_lookup_backfills_old_urls_without_starting_downloads(self):
        legacy, unavailable = "fixture0001", "fixture0002"
        self.queue_video(legacy)
        self.queue_video(unavailable)
        with self.archive.db() as db:
            db.execute("UPDATE video SET title=url WHERE id=?", (legacy,))
            db.execute("UPDATE video SET state='failed' WHERE id=?", (unavailable,))
        with patch.object(collector, "read_video_title", side_effect=lambda vid: "Título de teste" if vid == legacy else None):
            self.archive.backfill_download_titles()
            self.archive.titles.shutdown(wait=True)
        jobs = {job["id"]: job for job in self.client.get("/api/videos?state=jobs").json["videos"]}
        self.assertEqual((jobs[legacy]["title"], jobs[legacy]["state"]), ("Título de teste", "queued"))
        self.assertEqual((jobs[unavailable]["title"], jobs[unavailable]["state"]), (unavailable, "failed"))

    def test_capture_saves_title_before_selecting_formats(self):
        video_id = "fixture0001"
        self.queue_video(video_id)
        with self.archive.db() as db:
            item = dict(db.execute("SELECT * FROM video WHERE id=?", (video_id,)).fetchone())
        with patch.object(collector, "read_video", return_value={"id": video_id, "title": "Título da captura"}), \
             patch.object(collector, "format_choice", side_effect=ValueError("formats unavailable")):
            with self.assertRaisesRegex(ValueError, "formats unavailable"):
                self.archive.capture(item)
        self.assertEqual(self.client.get("/api/videos?state=jobs").json["videos"][0]["title"], "Título da captura")

    def test_playlist_projection_failure_isolated(self):
        with self.archive.db() as db:
            db.executemany("INSERT INTO playlist VALUES (?,?)", [("abc1230001", "Blocked"), ("abc1230002", "Good")])
        (self.archive.playlist_directory / "Blocked [abc1230001]").write_text("fixture", encoding="utf-8")
        with self.assertLogs(level="ERROR"):
            self.archive.refresh_playlist_files(["abc1230001", "abc1230002"])
        self.assertEqual((self.archive.playlist_directory / "Good [abc1230002]" / "playlist.m3u8").read_text(), "#EXTM3U\n")
        self.assertEqual(self.client.get("/api/system").json["events"][0]["code"], "playlist_write_failed")


if __name__ == "__main__":
    unittest.main()
