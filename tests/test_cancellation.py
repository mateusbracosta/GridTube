import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import collector
from app import create_app


class CancellationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.app = create_app(self.root / "data", self.root / "archive", workers=False)
        self.archive = self.app.extensions["archive"]
        self.client = self.app.test_client()

    def queue(self, video_id):
        response = self.client.post("/api/downloads", json={"url": f"https://youtu.be/{video_id}",
                                                         "overrides": {"subtitles": "none"}})
        self.assertEqual(response.json["queued"], 1)

    def test_cancel_queued_and_remove_failed_preserve_ready_media(self):
        for video_id, state in (("fixture0001", "queued"), ("fixture0002", "failed")):
            self.queue(video_id)
            inputs = self.archive.work / "inputs" / video_id
            inputs.mkdir(parents=True)
            (inputs / "partial.mp4.part").write_bytes(b"partial")
            with self.archive.db() as db:
                db.execute("UPDATE video SET state=? WHERE id=?", (state, video_id))
            self.assertEqual(self.client.delete(f"/api/downloads/{video_id}", json={}).json,
                             {"cancelling": False})
            self.assertFalse(inputs.exists())
            self.assertEqual(self.client.get("/api/videos?state=jobs").json["total"], 0)
            self.queue(video_id)
            self.client.delete(f"/api/downloads/{video_id}", json={})

        video_id = "fixture0003"
        self.queue(video_id)
        with self.archive.db() as db:
            db.execute("UPDATE video SET state='ready' WHERE id=?", (video_id,))
        response = self.client.delete(f"/api/downloads/{video_id}", json={})
        self.assertEqual(response.json["error"], "download_finished")
        self.assertEqual(self.client.get("/api/videos").json["total"], 1)

    def test_running_cancellation_stops_capture_and_the_next_download_finishes(self):
        first, second = "fixture0001", "fixture0002"
        self.queue(first)
        self.queue(second)
        transferring = threading.Event()
        proceed = threading.Event()
        failures = []

        class StopWorker(Exception):
            pass

        def download(url, prefs, inputs, bundle, progress, *, on_title, cancel=None):
            if url.endswith(first):
                (inputs / "partial.mp4.part").write_bytes(b"partial")
                transferring.set()
                if not proceed.wait(timeout=5):
                    raise TimeoutError("Test did not release the active download")
                cancel()
                self.fail("Cancelled capture continued")
            (bundle / "Fixture.mp4").write_bytes(b"second video")
            return {"id": second, "title": "Second", "filename": "Fixture.mp4"}

        def worker():
            try:
                self.archive.download_loop()
            except StopWorker:
                pass
            except Exception as exc:
                failures.append(exc)

        with (
            patch.object(collector, "download", side_effect=download),
            patch.object(self.archive, "schedule_video_origin"),
            patch.object(self.archive.changed, "wait", side_effect=StopWorker),
        ):
            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
            try:
                self.assertTrue(transferring.wait(timeout=5))
                response = self.client.delete(f"/api/downloads/{first}", json={})
                self.assertTrue(response.json["cancelling"])
                jobs = self.client.get("/api/videos?state=jobs").json["videos"]
                self.assertEqual(next(job["state"] for job in jobs if job["id"] == first), "cancelling")
                self.assertEqual(self.client.post(f"/api/videos/{first}/retry", json={}).status_code, 404)
            finally:
                proceed.set()
                thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(failures, [])
        self.assertFalse((self.archive.work / "inputs" / first).exists())
        self.assertEqual(list(self.archive.work.glob(first + "-*")), [])
        self.assertEqual(self.client.get("/api/videos?state=jobs").json["total"], 0)
        self.assertEqual(self.client.get("/api/videos").json["videos"][0]["id"], second)

    def test_restart_finishes_a_pending_cancellation(self):
        video_id = "fixture0001"
        self.queue(video_id)
        orphan = self.archive.work / f"{video_id}-interrupted"
        orphan.mkdir()
        (orphan / "partial.webm").write_bytes(b"unfinished")
        with self.archive.db() as db:
            db.execute("UPDATE video SET state='cancelling' WHERE id=?", (video_id,))
        restarted = create_app(self.root / "data", self.root / "archive", workers=False)
        self.assertEqual(restarted.test_client().get("/api/state").json["counts"], {})
        self.assertFalse(orphan.exists())

    def test_cancel_redownload_keeps_original_bundle_progress_and_playlist(self):
        video_id = "fixture0001"
        self.queue(video_id)
        folder = self.archive.library / "Avulsos" / f"Fixture [{video_id}]"
        folder.mkdir(parents=True)
        (folder / "notes.txt").write_bytes(b"retained")
        metadata = {"title": "Fixture", "filename": "missing.mp4"}
        with self.archive.db() as db:
            db.execute("UPDATE video SET folder=?,metadata=?,position=35 WHERE id=?",
                       (str(folder.relative_to(self.archive.library)), json.dumps(metadata), video_id))
            db.execute("INSERT INTO playlist VALUES ('abc1230001','Saved')")
            db.execute("INSERT INTO playlist_item VALUES ('abc1230001',?)", (video_id,))
        self.client.delete(f"/api/downloads/{video_id}", json={})
        removed = self.client.get("/api/videos?state=removed").json["videos"][0]
        self.assertEqual((removed["position"], removed["error"]), (35, "external_media_missing"))
        self.assertEqual((folder / "notes.txt").read_bytes(), b"retained")
        with self.archive.db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM playlist_item").fetchone()[0], 1)

    def test_cleanup_failure_is_visible_and_can_be_retried(self):
        video_id = "fixture0001"
        self.queue(video_id)
        inputs = self.archive.work / "inputs" / video_id
        inputs.mkdir(parents=True)
        with patch("app.shutil.rmtree", side_effect=PermissionError("read only")):
            response = self.client.delete(f"/api/downloads/{video_id}", json={})
        self.assertEqual(response.json["error"], "cancel_cleanup_failed")
        failed = self.client.get("/api/videos?state=jobs").json["videos"][0]
        self.assertEqual((failed["state"], failed["error"]), ("failed", "cancel_cleanup_failed"))
        self.assertEqual(self.client.delete(f"/api/downloads/{video_id}", json={}).status_code, 200)
        self.assertFalse(inputs.exists())

    def test_ffmpeg_cancellation_terminates_the_process(self):
        active = threading.Event()
        processes = []
        original_popen = subprocess.Popen

        def spawn(*args, **kwargs):
            process = original_popen(*args, **kwargs)
            processes.append(process)
            return process

        def cancelled():
            if active.is_set():
                raise collector.DownloadCancelled()

        started = time.monotonic()
        with patch("collector.subprocess.Popen", side_effect=spawn), self.assertRaises(collector.DownloadCancelled):
            collector.ffmpeg("-re", "-f", "lavfi", "-i", "color=s=64x64:d=60",
                             "-f", "null", "-", progress=lambda _: active.set(), cancel=cancelled)
        self.assertLess(time.monotonic() - started, 5)
        self.assertIsNotNone(processes[0].poll())


if __name__ == "__main__":
    unittest.main()
