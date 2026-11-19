import io
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


if __name__ == "__main__":
    unittest.main()
