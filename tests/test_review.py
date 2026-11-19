import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
import dependencies


class ReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.app = create_app(root / "data", root / "archive", workers=False)
        self.archive = self.app.extensions["archive"]
        self.client = self.app.test_client()

    def ready_video(self, video_id):
        self.client.post("/api/downloads", json={"url": f"https://youtu.be/{video_id}"})
        folder = self.archive.library / "Avulsos" / f"Fixture [{video_id}]"
        folder.mkdir(parents=True)
        (folder / "main.mp4").write_bytes(b"main media")
        (folder / "main.en.m4a").write_bytes(b"extra audio")
        metadata = {"title": "Fixture", "filename": "main.mp4", "audio_tracks": {"en": "main.en.m4a"}}
        with self.archive.db() as db:
            db.execute("UPDATE video SET state='ready',folder=?,metadata=? WHERE id=?",
                       (str(folder.relative_to(self.archive.library)), json.dumps(metadata), video_id))
        return folder

    def test_invalid_api_input_returns_validation_errors(self):
        for channel in (["invalid"], [], {}, False, 0):
            response = self.client.post("/api/downloads",
                                        json={"url": "https://youtu.be/fixture0001", "channel": channel})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json["error"], "invalid_channel")
        response = self.client.post("/api/playlists", json={"name": "Fixture", "video": ["invalid"]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/videos?page=" + "9" * 40).status_code, 200)

    def test_preparing_audio_keeps_other_media_and_cached_audio_available(self):
        first, second = "fixture0001", "fixture0002"
        self.ready_video(first)
        self.ready_video(second)
        with patch("collector.mux_video", side_effect=lambda source, target, *args, **kwargs: target.write_bytes(b"cached")):
            with self.client.get(f"/playback/{second}/en") as response:
                self.assertEqual(response.data, b"cached")

        started, release, base_ready, cached_ready = (threading.Event() for _ in range(4))
        failures = []

        def mux(source, target, *args, **kwargs):
            started.set()
            if not release.wait(8):
                raise TimeoutError("Test did not release audio preparation")
            target.write_bytes(b"prepared")

        def request(path, expected, finished=None):
            try:
                with self.app.test_client().get(path) as response:
                    if response.data != expected:
                        failures.append((path, response.status_code))
            except Exception as exc:
                failures.append(exc)
            finally:
                if finished:
                    finished.set()

        workers = []
        with patch("collector.mux_video", side_effect=mux):
            active = threading.Thread(target=request, args=(f"/playback/{first}/en", b"prepared"), daemon=True)
            active.start()
            workers.append(active)
            try:
                self.assertTrue(started.wait(5))
                for path, payload, finished in (
                    (f"/media/{first}/main.mp4", b"main media", base_ready),
                    (f"/playback/{second}/en", b"cached", cached_ready),
                ):
                    reader = threading.Thread(target=request, args=(path, payload, finished), daemon=True)
                    reader.start()
                    workers.append(reader)
                self.assertTrue(base_ready.wait(3), "Main media was blocked by audio preparation")
                self.assertTrue(cached_ready.wait(3), "Cached audio was blocked by another preparation")
                blocked = self.client.delete(f"/api/videos/{first}", json={"disk": True})
                self.assertEqual(blocked.json["error"], "playback_busy")
            finally:
                release.set()
                for worker in workers:
                    worker.join(timeout=5)
        self.assertFalse(any(worker.is_alive() for worker in workers))
        self.assertEqual(failures, [])
        self.assertFalse(self.archive.preparing_playback)

    def test_missing_saved_audio_returns_not_found(self):
        folder = self.ready_video("fixture0001")
        (folder / "main.en.m4a").unlink()
        self.assertEqual(self.client.get("/playback/fixture0001/en").status_code, 404)

    def test_dependency_probe_accepts_equivalent_date_versions(self):
        package = self.archive.work / "probe" / "yt_dlp"
        networking = package / "networking"
        networking.mkdir(parents=True)
        (package / "__init__.py").write_text(
            "class YoutubeDL:\n"
            "    def __init__(self, options): pass\n"
            "    def __enter__(self): return self\n"
            "    def __exit__(self, *args): pass\n", encoding="utf-8")
        (package / "version.py").write_text("__version__ = '2026.01.02'\n", encoding="utf-8")
        (networking / "__init__.py").write_text("class Request: pass\n", encoding="utf-8")
        (networking / "exceptions.py").write_text("class HTTPError(Exception): pass\n", encoding="utf-8")
        dependencies.probe(package.parent, "2026.1.2")
        with self.assertRaises(subprocess.CalledProcessError):
            dependencies.probe(package.parent, "2026.1.3")


if __name__ == "__main__":
    unittest.main()
