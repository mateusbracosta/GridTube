import json
import tempfile
import unittest
from pathlib import Path

import collector
from app import create_app


class ResolutionModeTests(unittest.TestCase):
    def formats(self):
        audio = [
            {"format_id": "aac", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 128,
             "language": "pt-BR", "format_note": "original", "filesize": 100000},
            {"format_id": "opus", "vcodec": "none", "acodec": "opus", "abr": 128,
             "language": "pt-BR", "format_note": "original", "filesize": 70000},
        ]
        video = []
        for height in (360, 720, 1080, 2160):
            for compact in (True, False):
                video.append({"format_id": f"{height}-{'small' if compact else 'preferred'}",
                              "height": height, "width": height * 16 // 9, "fps": 30,
                              "dynamic_range": "SDR", "vcodec": "av01" if compact else "avc1",
                              "acodec": "none", "filesize": height * (1000 if compact else 3000)})
        return audio + video

    def test_resolution_cap_applies_to_both_modes(self):
        for mode in ("compact", "original"):
            for cap in (360, 720, 1080):
                with self.subTest(mode=mode, cap=cap):
                    picture, _ = collector.format_choice(self.formats(), str(cap), "original", mode)
                    self.assertEqual(picture["height"], cap)

    def test_modes_choose_different_variants_inside_the_same_resolution(self):
        compact, _ = collector.format_choice(self.formats(), "1080", "original", "compact")
        original, _ = collector.format_choice(self.formats(), "1080", "original", "original")
        self.assertEqual(compact["format_id"], "1080-small")
        self.assertEqual(original["format_id"], "1080-preferred")
        self.assertLess(compact["filesize"], original["filesize"])

    def test_best_available_removes_the_cap_in_both_modes(self):
        for mode in ("compact", "original"):
            picture, _ = collector.format_choice(self.formats(), "best", "original", mode)
            self.assertEqual(picture["height"], 2160)

    def test_portrait_uses_short_side_and_never_exceeds_the_cap(self):
        formats = [fmt.copy() for fmt in self.formats()]
        for fmt in formats:
            if fmt.get("height"):
                fmt["width"], fmt["height"] = fmt["height"], fmt["width"]
        for mode in ("compact", "original"):
            picture, _ = collector.format_choice(formats, "720", "original", mode)
            self.assertEqual(min(picture["height"], picture["width"]), 720)
            unavailable = [fmt for fmt in formats if not fmt.get("height") or fmt["width"] > 720]
            with self.assertRaisesRegex(ValueError, "no_audio_at_quality"):
                collector.format_choice(unavailable, "720", "original", mode)

    def test_global_channel_and_video_keep_mode_and_resolution_independent(self):
        with tempfile.TemporaryDirectory() as temp:
            app = create_app(Path(temp) / "data", Path(temp) / "archive", workers=False)
            client = app.test_client()
            archive = app.extensions["archive"]
            self.assertEqual(client.put("/api/settings", json={"download_mode": "compact", "quality": "720"}).status_code, 200)
            channel = client.post("/api/channels", json={"name": "Fixture", "overrides": {"quality": "1080"}}).json["id"]
            client.post("/api/downloads", json={"url": "https://youtu.be/fixture0001", "channel": channel})
            self.assertEqual(client.put(f"/api/channels/{channel}", json={
                "name": "Fixture", "overrides": {"download_mode": "original", "quality": "1080"}}).status_code, 200)
            client.post("/api/downloads", json={"url": "https://youtu.be/fixture0002", "channel": channel})
            client.post("/api/downloads", json={"url": "https://youtu.be/fixture0003", "channel": channel,
                                                "overrides": {"quality": "720"}})
            with archive.db() as db:
                for video_id, mode, cap in (("fixture0001", "compact", "1080"),
                                            ("fixture0002", "original", "1080"),
                                            ("fixture0003", "original", "720")):
                    prefs = json.loads(db.execute("SELECT prefs FROM video WHERE id=?", (video_id,)).fetchone()[0])
                    self.assertEqual((prefs["download_mode"], prefs["quality"]), (mode, cap))
                    picture, _ = collector.format_choice(self.formats(), cap, "original", mode)
                    self.assertEqual(picture["height"], int(cap))


if __name__ == "__main__":
    unittest.main()
