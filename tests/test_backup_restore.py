import io
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import catalog_backup
from app import create_app


class BackupRestoreTests(unittest.TestCase):
    video_id = "fixture0001"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.app = self.open_app()
        self.archive = self.app.extensions["archive"]
        self.client = self.app.test_client()
        self.client.post("/api/downloads", json={"url": f"https://youtu.be/{self.video_id}"})
        self.playlist = self.client.post("/api/playlists", json={"name": "Saved", "video": self.video_id}).json["id"]
        with self.archive.db() as db:
            db.execute("UPDATE video SET title='Backup video',position=42 WHERE id=?", (self.video_id,))
        with self.client.get("/api/system/backup") as response:
            self.backup = response.data

    def open_app(self):
        return create_app(self.root / "data", self.root / "archive", workers=False)

    def prepare_restore(self):
        response = self.client.post("/api/system/backup/preview",
                                    data={"backup": (io.BytesIO(self.backup), "gridtube-backup.jsonl")})
        self.assertEqual(response.status_code, 200, response.json)
        token = response.json["token"]
        with self.archive.db() as db:
            db.execute("UPDATE video SET title='Current video',position=7 WHERE id=?", (self.video_id,))
            db.execute("DELETE FROM playlist_item")
        response = self.client.post("/api/system/backup/restore", json={"token": token})
        self.assertEqual(response.status_code, 202, response.json)
        self.assertEqual(self.client.get(f"/api/system/backup/status/{token}").json["status"], "pending")
        return token

    def test_restore_is_verified_after_restart(self):
        token = self.prepare_restore()
        restored = self.open_app().test_client()
        self.assertEqual(restored.get(f"/api/system/backup/status/{token}").json["status"], "verified")
        video = restored.get(f"/api/videos?state=jobs&scope=playlist:{self.playlist}").json["videos"][0]
        self.assertEqual((video["id"], video["title"], video["position"]), (self.video_id, "Backup video", 42))
        self.assertFalse(self.archive.pending_maintenance.exists())

    def test_a_mismatched_copy_rolls_back_and_reports_failure(self):
        token = self.prepare_restore()
        original_copy = catalog_backup.replace_catalog

        def mismatched_copy(db, candidate):
            original_copy(db, candidate)
            db.execute("DELETE FROM playlist_item")

        with patch.object(catalog_backup, "replace_catalog", side_effect=mismatched_copy), self.assertLogs(level="ERROR"):
            restored = self.open_app().test_client()
        self.assertEqual(restored.get(f"/api/system/backup/status/{token}").json["status"], "failed")
        video = restored.get("/api/videos?state=jobs").json["videos"][0]
        self.assertEqual((video["title"], video["position"]), ("Current video", 7))

    def test_invalid_backup_keeps_current_data_and_does_not_stage_restore(self):
        response = self.client.post("/api/system/backup/preview",
                                    data={"backup": (io.BytesIO(self.backup[:-12]), "broken.jsonl")})
        self.assertEqual(response.json["error"], "backup_invalid")
        self.assertFalse(self.archive.pending_maintenance.exists())
        video = self.client.get("/api/videos?state=jobs").json["videos"][0]
        self.assertEqual(video["position"], 42)

    def test_unrelated_restore_token_is_never_reported_as_success(self):
        token = self.prepare_restore()
        restored = self.open_app().test_client()
        self.assertEqual(restored.get(f"/api/system/backup/status/{token}").json["status"], "verified")
        self.assertEqual(restored.get("/api/system/backup/status/" + "f" * 32).json["status"], "unknown")

    def test_local_channel_and_playlist_appearance_survive_backup_restore(self):
        style = {"icon": "book", "color": "#78a8e5"}
        channel = self.client.post("/api/channels", json={"name": "Knowledge", "appearance": style}).json["id"]
        response = self.client.put(f"/api/playlists/{self.playlist}/appearance",
                                   json={"appearance": {"icon": "gamepad", "color": "#85b98a"}})
        self.assertEqual(response.status_code, 200)
        with self.archive.db() as db:
            folder = self.archive.channel(db, channel)["folder"]
        response = self.client.put(f"/api/channels/{channel}",
                                   json={"name": "Knowledge", "appearance": {"icon": "compass", "color": "#e0b565"}})
        self.assertEqual(response.status_code, 200)
        with self.client.get("/api/system/backup") as response:
            self.backup = response.data
        self.prepare_restore()
        restored = self.open_app()
        state = restored.test_client().get("/api/state").json
        self.assertEqual(state["channels"][0]["appearance"], {"icon": "compass", "color": "#e0b565"})
        self.assertEqual(state["playlists"][0]["appearance"], {"icon": "gamepad", "color": "#85b98a"})
        with restored.extensions["archive"].db() as db:
            self.assertEqual(db.execute("SELECT folder FROM channel WHERE id=?", (channel,)).fetchone()[0], folder)

    def test_old_backup_and_pending_database_restore_without_style_tables(self):
        rows = [json.loads(line) for line in self.backup.splitlines()]
        self.backup = b"".join((json.dumps(row)+"\n").encode() for row in rows
                               if row.get("table") not in catalog_backup.STYLE_TABLES)
        token = self.prepare_restore()
        with sqlite3.connect(self.archive.backup_candidate(token)) as db:
            db.execute("DROP TABLE channel_style")
            db.execute("DROP TABLE playlist_style")
        self.client.put(f"/api/playlists/{self.playlist}/appearance",
                        json={"appearance": {"icon": "music", "color": "#67c8bc"}})
        restored = self.open_app().test_client()
        self.assertEqual(restored.get(f"/api/system/backup/status/{token}").json["status"], "verified")
        self.assertEqual(restored.get("/api/state").json["playlists"][0]["appearance"],
                         {"icon": "list", "color": "#bebebe"})

    def test_remote_channels_use_their_source_identity(self):
        source = "https://www.youtube.com/@creator"
        style = {"icon": "star", "color": "#e0b565"}
        response = self.client.post("/api/channels", json={"name": "Creator", "source": source, "appearance": style})
        self.assertEqual(response.status_code, 201)
        channel = response.json["id"]
        self.client.put(f"/api/channels/{channel}", json={"name": "Creator", "appearance": style})
        self.assertIsNone(self.client.get("/api/state").json["channels"][0]["appearance"])
        with self.archive.db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM channel_style").fetchone()[0], 0)
        local = self.client.post("/api/channels", json={"name": "Local", "appearance": style}).json["id"]
        with patch.object(self.archive.catalog, "submit"):
            self.client.put(f"/api/channels/{local}",
                            json={"name": "Linked", "source": "https://www.youtube.com/@other", "appearance": style})
        with self.archive.db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM channel_style").fetchone()[0], 0)

    def test_invalid_collection_appearance_is_rejected(self):
        for style in ({"icon": ["book"], "color": "#78a8e5"},
                      {"icon": "unknown", "color": "#78a8e5"},
                      {"icon": "book", "color": "red;display:none"}):
            response = self.client.put(f"/api/playlists/{self.playlist}/appearance", json={"appearance": style})
            self.assertEqual(response.json["error"], "invalid_appearance")
        self.assertEqual(self.client.get("/api/state").json["playlists"][0]["appearance"]["icon"], "list")

    def test_restore_and_profile_refresh_keep_the_cached_avatar(self):
        source = "https://www.youtube.com/@creator"
        self.client.post("/api/channels", json={"name": "Creator", "source": source})
        key = hashlib.sha256(source.encode()).hexdigest()
        directory = self.archive.branding / key
        directory.mkdir()
        (directory / "avatar.jpg").write_bytes(b"cached avatar")
        with self.archive.db() as db:
            db.execute("INSERT INTO channel_profile VALUES (?,?,?)",
                       (source, json.dumps({"name": "Creator", "avatar": "avatar.jpg"}), key))
        with patch("collector.save_channel_image", return_value=None):
            self.archive.save_profile(source, {"name": "Creator", "avatar": None, "banner": None})
        with self.client.get("/api/system/backup") as response:
            self.backup = response.data
        self.prepare_restore()
        restored = self.open_app().test_client()
        channel = restored.get("/api/state").json["channels"][0]
        self.assertEqual(channel["profile"]["avatar"], "avatar.jpg")
        with restored.get(f"/branding/{channel['id']}/avatar.jpg") as response:
            self.assertEqual(response.data, b"cached avatar")


if __name__ == "__main__":
    unittest.main()
