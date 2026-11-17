import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collector
from app import create_app


class LibraryCheckTests(unittest.TestCase):
    video_id = "fixture0001"

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        app = create_app(self.root / "data", self.root / "archive", workers=False)
        self.client = app.test_client()
        self.archive = app.extensions["archive"]
        self.url = f"/api/videos/{self.video_id}"
        self.relative = Path("Avulsos") / f"Fixture [{self.video_id}]"
        self.folder = self.archive.library / self.relative
        self.folder.mkdir(parents=True)
        self.picture = self.folder / "Fixture.mp4"
        self.picture.write_bytes(b"fixture media")
        self.subtitle = self.folder / "Fixture.en.vtt"
        self.subtitle.write_bytes(b"WEBVTT")
        metadata = {"id": self.video_id, "title": "Fixture", "filename": self.picture.name,
                    "subtitles": {"en": self.subtitle.name}}
        collector.write_manifest(self.folder, metadata)
        self.client.post("/api/downloads", json={"url": f"https://youtu.be/{self.video_id}"})
        with self.archive.db() as db:
            db.execute("UPDATE video SET state='ready',folder=?,metadata=?,position=21 WHERE id=?",
                       (str(self.relative), json.dumps(metadata), self.video_id))
        self.playlist = self.client.post("/api/playlists", json={"name": "Saved", "video": self.video_id}).json["id"]
        self.m3u = self.archive.playlist_directory / f"Saved [{self.playlist}]" / "playlist.m3u8"

    def check(self):
        response = self.client.post("/api/system/library/check", json={})
        self.assertEqual(response.status_code, 200, response.json)
        return response.json

    def add_channel(self, name):
        with self.archive.db() as db:
            channel = dict(self.archive.create_channel(db, name))
        return channel["id"], self.archive.library / channel["folder"]

    def test_copies_are_unchanged_and_moved_folder_preserves_catalog(self):
        copy = self.root / self.picture.name
        copy.write_bytes(self.picture.read_bytes())
        self.assertEqual(sum(self.check().values()), 0)
        self.assertEqual(copy.read_bytes(), b"fixture media")

        channel, parent = self.add_channel("New channel")
        parent.mkdir()
        destination = parent / self.folder.name
        self.folder.rename(destination)
        self.assertEqual(self.check()["moved"], 1)
        self.assertIn(parent.name, self.m3u.read_text(encoding="utf-8"))
        row = self.client.get(f"/api/videos?scope=playlist:{self.playlist}").json["videos"][0]
        self.assertEqual((row["id"], row["channel_id"], row["position"]), (self.video_id, channel, 21))
        with self.client.get(f"/media/{self.video_id}/{self.picture.name}") as response:
            self.assertEqual(response.data, b"fixture media")
        with self.client.get(f"/media/{self.video_id}/{self.subtitle.name}") as response:
            self.assertEqual(response.data, b"WEBVTT")
        self.assertEqual(sum(self.check().values()), 0)

    def test_deleting_only_the_video_leaves_sidecars_and_preserves_playlist_on_restore(self):
        trash = self.root / self.picture.name
        self.picture.rename(trash)
        self.assertEqual(self.check()["missing"], 1)
        self.assertTrue(self.subtitle.is_file())
        self.assertEqual(self.client.get("/api/videos").json["total"], 0)
        self.assertEqual(self.client.get("/api/videos?state=removed").json["videos"][0]["error"],
                         "external_media_missing")
        self.assertEqual(self.m3u.read_text(encoding="utf-8"), "#EXTM3U\n")
        self.assertEqual(sum(self.check().values()), 0)
        trash.rename(self.picture)
        self.assertEqual(self.client.post(self.url + "/retry", json={}).json["error"], "external_media_returned")
        self.assertEqual(self.check()["restored"], 1)
        row = self.client.get(f"/api/videos?scope=playlist:{self.playlist}").json["videos"][0]
        self.assertEqual((row["id"], row["position"]), (self.video_id, 21))
        self.assertIn(self.picture.name, self.m3u.read_text(encoding="utf-8"))

    def test_duplicate_destinations_are_not_assigned_and_redownload_preserves_state(self):
        for name in ("First", "Second"):
            _, parent = self.add_channel(name)
            duplicate = parent / self.folder.name
            duplicate.mkdir(parents=True)
            (duplicate / self.picture.name).write_bytes(b"fixture media")
            (duplicate / "video.json").write_bytes((self.folder / "video.json").read_bytes())
        self.picture.unlink()
        result = self.check()
        self.assertEqual((result["moved"], result["missing"], result["ambiguous"]), (0, 1, 1))
        self.assertEqual(self.client.post(self.url + "/retry", json={}).status_code, 200)
        with self.archive.db() as db:
            association = db.execute("SELECT playlist_id FROM playlist_item WHERE video_id=?", (self.video_id,)).fetchone()
            self.assertEqual(association["playlist_id"], self.playlist)
        row = self.client.get("/api/videos?state=jobs").json["videos"][0]
        self.assertEqual((row["state"], row["position"]), ("queued", 21))

    def test_a_video_removed_in_gridtube_stays_removed(self):
        self.assertEqual(self.client.delete(self.url, json={"disk": False}).status_code, 200)
        self.assertEqual(sum(self.check().values()), 0)
        self.assertEqual(self.client.get("/api/videos?state=removed").json["total"], 1)
        self.assertTrue(self.picture.is_file())

    def test_delete_saved_subtitle_and_failed_attempt_independently(self):
        tracks = self.url + "/tracks"
        with self.archive.db() as db:
            db.execute("""INSERT INTO track_job (video_id,kind,code,allow_auto,exact,state,error)
                VALUES (?,'subtitle','en',1,1,'failed','track_rate_limited')""", (self.video_id,))
        self.assertTrue(self.client.delete(tracks + "/subtitle/en", json={"saved": False}).json["removed"])
        self.assertTrue(self.subtitle.is_file())
        self.assertEqual(self.client.get(tracks).json["jobs"], [])
        self.assertTrue(self.client.delete(tracks + "/subtitle/en", json={"saved": True}).json["removed"])
        self.assertFalse(self.subtitle.exists())
        self.assertTrue(self.picture.is_file())
        self.assertEqual(self.client.get(tracks).json["video"]["subtitles"], {})
        self.assertEqual(json.loads((self.folder / "video.json").read_text(encoding="utf-8"))["subtitles"], {})
        self.assertFalse(self.client.delete(tracks + "/subtitle/en", json={"saved": True}).json["removed"])

    def test_delete_audio_removes_cache_but_keeps_main_file(self):
        audio = self.folder / "Fixture.en.m4a"
        audio.write_bytes(b"extra audio")
        cache = self.archive.playback / f"{self.video_id}-example.mp4"
        cache.write_bytes(b"derived playback")
        with self.archive.db() as db:
            row = self.archive.ready_video(db, self.video_id)
            metadata = json.loads(row["metadata"])
            metadata["audio_tracks"] = {"en": audio.name}
            self.archive.save_video_metadata(db, row, metadata)
        self.assertTrue(self.client.delete(self.url + "/tracks/audio/en", json={"saved": True}).json["removed"])
        self.assertFalse(audio.exists())
        self.assertFalse(cache.exists())
        self.assertTrue(self.subtitle.is_file())
        self.assertTrue(self.picture.is_file())
        self.assertEqual(self.client.get(f"/playback/{self.video_id}/en").status_code, 404)

    def test_failed_manifest_write_restores_deleted_track(self):
        with patch.object(collector, "write_manifest", side_effect=OSError("read only")), self.assertLogs(level="ERROR"):
            response = self.client.delete(self.url + "/tracks/subtitle/en", json={"saved": True})
        self.assertEqual(response.json["error"], "track_delete_failed")
        self.assertTrue(self.subtitle.is_file())
        self.assertEqual(self.client.get(self.url + "/tracks").json["video"]["subtitles"], {"en": self.subtitle.name})

    def test_original_thumbnail_replaces_frame_and_is_stable_after_progress(self):
        fallback = self.folder / "Fixture-thumb.jpg"
        fallback.write_bytes(b"old frame")
        with self.archive.db() as db:
            row = self.archive.ready_video(db, self.video_id)
            metadata = json.loads(row["metadata"])
            metadata["thumbnail"] = fallback.name
            self.archive.save_video_metadata(db, row, metadata)

        def get_thumbnail(video_id, directory):
            name = "youtube-thumbnail.jpg"
            (directory / name).write_bytes(b"original cover")
            return name

        with patch.object(collector, "save_video_thumbnail", side_effect=get_thumbnail):
            self.archive.update_video_thumbnail(self.video_id)
        self.assertFalse(fallback.exists())
        before = self.client.get("/api/videos?summary=1").json["videos"][0]
        self.client.post(self.url + "/progress", json={"position": 75})
        after = self.client.get("/api/videos?summary=1").json["videos"][0]
        self.assertEqual(after["position"], 75)
        self.assertEqual(before["thumbnail"], after["thumbnail"])
        with self.client.get(f"/media/{self.video_id}/{after['thumbnail']}") as response:
            self.assertEqual(response.data, b"original cover")
