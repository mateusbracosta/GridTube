import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collector
from app import create_app


class BulkDeleteTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.app = create_app(self.root / "data", self.root / "archive", workers=False)
        self.client = self.app.test_client()
        self.archive = self.app.extensions["archive"]
        self.channel = self.client.post("/api/channels", json={"name": "Saved"}).json["id"]
        with self.archive.db() as db:
            self.parent = self.archive.channel(db, self.channel)["folder"]

    def video(self, number, ready=True):
        video_id = f"item{number:07d}"
        self.client.post("/api/downloads", json={"url": f"https://youtu.be/{video_id}", "channel": self.channel})
        folder = self.archive.library / self.parent / f"Video [{video_id}]"
        if ready:
            folder.mkdir(parents=True)
            (folder / "main.mp4").write_bytes(b"video")
            (folder / "main.en.vtt").write_bytes(b"WEBVTT")
            metadata = {"id": video_id, "title": video_id, "filename": "main.mp4", "subtitles": {"en": "main.en.vtt"}}
            collector.write_manifest(folder, metadata)
            with self.archive.db() as db:
                db.execute("UPDATE video SET state='ready',folder=?,metadata=?,position=23 WHERE id=?",
                           (str(folder.relative_to(self.archive.library)), json.dumps(metadata), video_id))
        return video_id, folder

    def playlist(self, name, ids):
        playlist_id = self.client.post("/api/playlists", json={"name": name}).json["id"]
        for video_id in ids:
            self.client.put(f"/api/playlists/{playlist_id}/videos/{video_id}")
        return playlist_id

    def delete_collection(self, kind, collection_id, disk):
        preview = self.client.get(f"/api/{kind}s/{collection_id}/delete-preview").json
        response = self.client.delete(f"/api/{kind}s/{collection_id}", json={"ids": preview["ids"], "disk": disk})
        self.assertEqual(response.status_code, 200, response.json)
        return preview

    def test_delete_entire_channel_keeps_files_and_videos_can_be_restored(self):
        first, folder = self.video(1)
        second, other = self.video(2)
        queued, _ = self.video(3, ready=False)
        playlist = self.playlist("Keep", [first, second])
        preview = self.delete_collection("channel", self.channel, False)
        self.assertEqual(set(preview["ids"]), {first, second, queued})
        self.assertEqual(preview["shared"], 2)
        self.assertTrue(folder.is_dir() and other.is_dir())
        self.assertFalse(self.client.get("/api/state").json["channels"])
        removed = self.client.get("/api/videos?state=removed").json["videos"]
        self.assertEqual({v["id"] for v in removed}, {first, second})
        self.assertTrue(all(v["channel_id"] is None and v["position"] == 23 for v in removed))
        self.assertEqual(self.client.post(f"/api/videos/{first}/restore", json={}).status_code, 200)
        self.assertEqual(self.client.get(f"/api/videos?scope=playlist:{playlist}").json["total"], 1)
        self.assertEqual(self.client.get("/api/videos?scope=inbox").json["total"], 1)
        with self.archive.db() as db:
            self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())

    def test_playlist_disk_deletion_removes_shared_videos_and_updates_other_playlist(self):
        first, folder = self.video(1)
        second, other = self.video(2)
        third, untouched = self.video(3)
        playlist = self.playlist("Delete", [first, second])
        shared = self.playlist("Shared", [first, third])
        manifest = self.archive.playlist_directory / f"Delete [{playlist}]" / "playlist.m3u8"
        preview = self.delete_collection("playlist", playlist, True)
        self.assertEqual(preview["shared"], 1)
        self.assertFalse(folder.exists() or other.exists() or manifest.exists())
        self.assertTrue(untouched.exists())
        self.assertEqual([v["id"] for v in self.client.get(f"/api/videos?scope=playlist:{shared}").json["videos"]], [third])
        m3u = (self.archive.playlist_directory / f"Shared [{shared}]" / "playlist.m3u8").read_text()
        self.assertNotIn(first, m3u)
        self.assertIn(third, m3u)
        self.assertEqual(len(self.client.get("/api/state").json["channels"]), 1)

    def test_playlist_keep_removes_all_pages_but_keeps_files_and_memberships_elsewhere(self):
        ids = [self.video(n)[0] for n in range(65)]
        playlist = self.playlist("All", ids)
        other = self.playlist("Other", [ids[0]])
        self.assertEqual(len(self.client.get(f"/api/videos?scope=playlist:{playlist}").json["videos"]), 60)
        self.assertEqual(len(self.delete_collection("playlist", playlist, False)["ids"]), 65)
        self.assertEqual(self.client.get("/api/videos?state=removed").json["total"], 65)
        self.client.post(f"/api/videos/{ids[0]}/restore", json={})
        self.assertEqual(self.client.get(f"/api/videos?scope=playlist:{other}").json["total"], 1)

    def test_selected_ids_only_and_bad_inputs_or_cross_origin_are_rejected(self):
        first, folder = self.video(1)
        second, other = self.video(2)
        for data in ({"ids": [first], "disk": "yes"}, {"ids": "all", "disk": True}, {"ids": ["../bad"], "disk": True}):
            self.assertEqual(self.client.post("/api/videos/delete", json=data).status_code, 400)
        self.assertEqual(self.client.post("/api/videos/delete", json={"ids": [first], "disk": True},
                                          headers={"Origin": "https://other.example"}).status_code, 403)
        response = self.client.post("/api/videos/delete", json={"ids": [first, first], "disk": True})
        self.assertEqual(response.json, {"pending": False, "removed": 1})
        self.assertFalse(folder.exists())
        self.assertTrue(other.is_dir())
        self.assertEqual(self.client.get("/api/videos").json["videos"][0]["id"], second)

    def test_changed_collection_requires_new_preview_before_deleting_anything(self):
        first, folder = self.video(1)
        self.video(2)
        response = self.client.delete(f"/api/channels/{self.channel}", json={"ids": [first], "disk": True})
        self.assertEqual(response.json["error"], "collection_changed")
        self.assertTrue(folder.exists())
        self.assertEqual(self.client.get("/api/videos").json["total"], 2)

    def test_export_and_preparation_preflight_protect_entire_batch(self):
        first, folder = self.video(1)
        second, other = self.video(2)
        for pins, error in ((self.archive.exporting, "playlist_export_busy"), (self.archive.preparing_playback, "playback_busy")):
            pins[second] += 1
            response = self.client.post("/api/videos/delete", json={"ids": [first, second], "disk": True})
            self.assertEqual(response.json["error"], error)
            self.assertTrue(folder.exists() and other.exists())
            self.assertEqual(self.client.get("/api/videos").json["total"], 2)
            pins.clear()

    def test_running_capture_is_cancelled_before_delete_and_other_jobs_cannot_start(self):
        first, _ = self.video(1, ready=False)
        second, _ = self.video(2, ready=False)
        saved, folder = self.video(3)
        with self.archive.db() as db:
            db.execute("UPDATE video SET state='running' WHERE id=?", (first,))
        ids = [first, second, saved]
        response = self.client.delete(f"/api/channels/{self.channel}", json={"ids": ids, "disk": True})
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.json["pending"])
        self.assertTrue(folder.exists())
        self.assertTrue(self.archive.capture_cancelled.is_set())
        with self.archive.db() as db:
            self.assertIsNone(db.execute("SELECT * FROM video WHERE id=?", (second,)).fetchone())
            row = db.execute("SELECT * FROM video WHERE id=?", (first,)).fetchone()
            self.assertEqual(row["state"], "cancelling")
            self.archive.finish_cancellation(db, row)
        response = self.client.delete(f"/api/channels/{self.channel}", json={"ids": ids, "disk": True})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertFalse(folder.exists())
        self.assertFalse(self.client.get("/api/state").json["channels"])

    def test_partial_disk_failure_keeps_collection_and_allows_retry(self):
        first, folder = self.video(1)
        second, other = self.video(2)
        original = self.archive.remove_video_locked

        def fail_second(video_id, disk, refresh=True):
            if video_id == second:
                raise ValueError("delete_disk_failed")
            original(video_id, disk, refresh)

        with patch.object(self.archive, "remove_video_locked", side_effect=fail_second):
            response = self.client.delete(f"/api/channels/{self.channel}", json={"ids": [first, second], "disk": True})
        self.assertEqual(response.json["error"], "delete_disk_failed")
        self.assertFalse(folder.exists())
        self.assertTrue(other.exists())
        self.assertEqual(len(self.client.get("/api/state").json["channels"]), 1)
        self.delete_collection("channel", self.channel, True)
        self.assertFalse(other.exists())

    def test_empty_collections_and_untracked_files_are_preserved_safely(self):
        playlist = self.playlist("Empty", [])
        folder = self.archive.playlist_directory / f"Empty [{playlist}]"
        (folder / "personal.txt").write_bytes(b"keep")
        self.delete_collection("playlist", playlist, True)
        self.assertEqual((folder / "personal.txt").read_bytes(), b"keep")
        self.assertFalse((folder / "playlist.m3u8").exists())
        self.delete_collection("channel", self.channel, True)


if __name__ == "__main__":
    unittest.main()
