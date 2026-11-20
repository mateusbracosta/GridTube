import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collector
from app import create_app


class DownloadPolicyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.app = create_app(self.root / "data", self.root / "archive", workers=False)
        self.archive = self.app.extensions["archive"]
        self.client = self.app.test_client()

    def settings(self, **prefs):
        response = self.client.put("/api/settings", json=prefs)
        self.assertEqual(response.status_code, 200, response.json)

    def queue(self, number, route="watch?v=", channel=None):
        return self.client.post("/api/downloads", json={"url": f"https://youtube.com/{route}item{number:07d}", "channel": channel})

    def item(self, number):
        with self.archive.db() as db:
            return dict(db.execute("SELECT * FROM video WHERE id=?", (f"item{number:07d}",)).fetchone())

    def test_disabled_types_block_manual_links_and_keep_regular_videos_available(self):
        self.settings(shorts="exclude", lives="exclude")
        for number, route, error in ((1, "shorts/", "shorts_disabled"), (2, "live/", "lives_disabled")):
            response = self.queue(number, route)
            self.assertEqual((response.status_code, response.json["error"]), (400, error))
        self.assertEqual(self.queue(3).json["queued"], 1)
        self.assertEqual(self.client.get("/api/videos?state=jobs").json["total"], 1)

    def test_channel_rules_override_global_for_manual_downloads(self):
        self.settings(shorts="exclude", lives="exclude")
        channel = self.client.post("/api/channels", json={"name": "Allowed", "overrides": {"shorts": "include", "lives": "include"}}).json["id"]
        self.assertEqual(self.queue(1, "shorts/", channel).json["queued"], 1)
        self.assertEqual(self.queue(2, "live/", channel).json["queued"], 1)
        self.settings()
        blocked = self.client.post("/api/channels", json={"name": "Blocked", "overrides": {"shorts": "exclude", "lives": "exclude"}}).json["id"]
        self.assertEqual(self.queue(3, "shorts/", blocked).json["error"], "shorts_disabled")
        self.assertEqual(self.queue(4, "live/", blocked).json["error"], "lives_disabled")

    def test_manual_catalog_reports_blocked_items_without_rejecting_allowed_selection(self):
        source = "https://www.youtube.com/@fixture"
        with self.archive.db() as db:
            db.execute("INSERT INTO scan (source,name,state) VALUES (?,?,'ready')", (source, "Fixture"))
            db.executemany("INSERT INTO entry VALUES (?,?,?,?,?,?,?)", [
                (source, f"item{n:07d}", f"Video {n}", kind, 60, f"https://youtu.be/item{n:07d}", n)
                for n, kind in ((1, "videos"), (2, "shorts"), (3, "streams"))])
        self.settings(shorts="exclude", lives="exclude")
        created = self.client.post("/api/channels", json={"source": source, "selected": [f"item{n:07d}" for n in (1, 2, 3)]})
        self.assertEqual(created.status_code, 201, created.json)
        self.assertEqual((created.json["queued"], created.json["blocked"]), (1, 2))
        queued = self.client.post(f"/api/channels/{created.json['id']}/queue", json={"selected": ["item0000002", "item0000003"]})
        self.assertEqual((queued.json["queued"], queued.json["blocked"]), (0, 2))

    def test_watch_links_are_checked_against_youtube_media_type_before_transfer(self):
        for number, media_type, error in ((1, "short", "shorts_disabled"), (2, "livestream", "lives_disabled")):
            self.queue(number)
            self.settings(shorts="exclude", lives="exclude")
            info = {"id": f"item{number:07d}", "title": "Fixture", "media_type": media_type}
            with patch("collector.read_video", return_value=info), patch("collector.format_choice") as choose:
                with self.assertRaisesRegex(ValueError, error):
                    self.archive.capture(self.item(number))
                choose.assert_not_called()
            self.assertEqual(self.item(number)["kind"], "shorts" if media_type == "short" else "streams")
            self.settings()

    def test_queued_captures_obey_current_rules_instead_of_saved_preferences(self):
        self.queue(1, "shorts/")
        self.queue(2, "live/")
        self.settings(shorts="exclude", lives="exclude")
        for number, error in ((1, "shorts_disabled"), (2, "lives_disabled")):
            with patch("collector.download") as download:
                with self.assertRaisesRegex(ValueError, error):
                    self.archive.capture(self.item(number))
                download.assert_not_called()

    def test_short_only_policy_also_applies_to_manual_regular_videos(self):
        self.settings(shorts="only")
        self.queue(1)
        with patch("collector.read_video", return_value={"id": "item0000001", "title": "Long", "media_type": "video"}), patch("collector.format_choice") as choose:
            with self.assertRaisesRegex(ValueError, "shorts_only"):
                self.archive.capture(self.item(1))
            choose.assert_not_called()

    def test_policy_change_preserves_existing_media_progress_and_tracks(self):
        self.queue(1, "shorts/")
        folder = self.archive.library / "Avulsos/Fixture [item0000001]"
        folder.mkdir(parents=True)
        (folder / "main.mp4").write_bytes(b"existing media")
        (folder / "main.en.vtt").write_bytes(b"WEBVTT\n")
        metadata = {"title": "Saved short", "filename": "main.mp4", "subtitles": {"en": "main.en.vtt"}}
        collector.write_manifest(folder, metadata)
        with self.archive.db() as db:
            db.execute("UPDATE video SET state='ready',folder=?,metadata=?,position=12 WHERE id='item0000001'",
                       (str(folder.relative_to(self.archive.library)), json.dumps(metadata)))
        before = {path.name: path.read_bytes() for path in folder.iterdir()}
        self.settings(shorts="exclude", lives="exclude")
        self.assertEqual(self.queue(1, "shorts/").json["queued"], 0)
        row = self.client.get("/api/videos").json["videos"][0]
        self.assertEqual((row["state"], row["position"], row["subtitles"]), ("ready", 12, {"en": "main.en.vtt"}))
        self.assertEqual({path.name: path.read_bytes() for path in folder.iterdir()}, before)

    def test_retry_does_not_bypass_disabled_content_policy(self):
        self.queue(1, "live/")
        with self.archive.db() as db:
            db.execute("UPDATE video SET state='failed' WHERE id='item0000001'")
        self.settings(lives="exclude")
        response = self.client.post("/api/videos/item0000001/retry", json={})
        self.assertEqual((response.status_code, response.json["error"]), (400, "lives_disabled"))
        self.assertEqual(self.item(1)["state"], "failed")

    def test_blocked_waiting_job_reports_reason_and_can_be_retried_after_enabling(self):
        class StopLoop(Exception):
            pass

        self.queue(1, "shorts/")
        self.settings(shorts="exclude")
        with patch.object(self.archive.changed, "wait", side_effect=StopLoop), patch("collector.download") as download:
            with self.assertLogs(level="ERROR"), self.assertRaises(StopLoop):
                self.archive.download_loop()
            download.assert_not_called()
        self.assertEqual((self.item(1)["state"], self.item(1)["error"]), ("failed", "shorts_disabled"))
        self.settings(shorts="include")
        response = self.client.post("/api/videos/item0000001/retry", json={})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(self.item(1)["state"], "queued")

    def test_live_only_policy_is_available_globally_and_for_channels(self):
        self.settings(lives="only")
        self.assertEqual(self.queue(1, "live/").json["queued"], 1)
        self.assertEqual(self.queue(2, "shorts/").json["error"], "lives_only")
        self.queue(3)
        with patch("collector.read_video", return_value={"id": "item0000003", "title": "Regular", "media_type": "video"}), patch("collector.format_choice") as choose:
            with self.assertRaisesRegex(ValueError, "lives_only"):
                self.archive.capture(self.item(3))
            choose.assert_not_called()
        channel = self.client.post("/api/channels", json={"name": "Regular allowed", "overrides": {"lives": "include"}}).json["id"]
        self.assertEqual(self.queue(4, "shorts/", channel).json["queued"], 1)

    def test_both_only_modes_allow_shorts_and_lives_as_a_union(self):
        prefs = {"shorts": "only", "lives": "only"}
        self.assertTrue(collector.content_allowed("shorts", prefs))
        self.assertTrue(collector.content_allowed("streams", prefs))
        self.assertFalse(collector.content_allowed("videos", prefs))
        with self.assertRaisesRegex(ValueError, "selected_types_only"):
            collector.require_content_allowed("videos", prefs)
