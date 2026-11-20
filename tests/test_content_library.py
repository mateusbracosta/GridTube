import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collector
from app import PUBLICATION_ORDER, create_app


class ContentLibraryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.app = create_app(self.root / "data", self.root / "archive", workers=False)
        self.archive = self.app.extensions["archive"]
        self.client = self.app.test_client()
        self.channel = self.client.post("/api/channels", json={"name": "Saved"}).json["id"]

    def add(self, number, kind="videos", date="20260101", created=1700000000, automatic=False):
        entry = {"id": f"item{number:07d}", "title": f"Video {number}", "kind": kind,
                 "url": f"https://youtu.be/item{number:07d}"}
        with self.archive.db() as db:
            channel = self.archive.channel(db, self.channel)
            self.archive.enqueue(db, entry, channel, self.archive.effective(db, channel), automatic=automatic)
            folder = self.archive.library / channel["folder"] / f"Video [{entry['id']}]"
            folder.mkdir(parents=True)
            (folder / "main.mp4").write_bytes(b"fixture")
            metadata = {"title": entry["title"], "filename": "main.mp4", "upload_date": date}
            collector.write_manifest(folder, metadata)
            db.execute("UPDATE video SET state='ready',created=?,metadata=?,folder=? WHERE id=?",
                       (created, json.dumps(metadata), str(folder.relative_to(self.archive.library)), entry["id"]))
        return entry["id"]

    def rows(self, **params):
        response = self.client.get("/api/videos", query_string=params)
        self.assertEqual(response.status_code, 200, response.json)
        return response.json

    def test_kind_filter_applies_before_count_and_pagination(self):
        for number in range(65):
            self.add(number, "shorts")
        self.add(100, "videos")
        self.add(101, "streams")
        result = self.rows(kind="shorts", page=2, summary=1)
        self.assertEqual((result["total"], len(result["videos"])), (65, 5))
        self.assertTrue(all(row["kind"] == "shorts" for row in result["videos"]))
        for kind in ("videos", "streams"):
            self.assertEqual(self.rows(kind=kind)["total"], 1)
        self.assertEqual(self.rows()["total"], 67)
        self.assertEqual(self.client.get("/api/videos?kind=invalid").status_code, 400)

    def test_channel_search_and_playlist_keep_correct_type_and_count(self):
        first = self.add(1)
        self.add(2, "shorts")
        self.add(3, "streams")
        playlist = self.client.post("/api/playlists", json={"name": "Mixed", "video": first}).json["id"]
        self.assertEqual(self.rows(scope=f"channel:{self.channel}", kind="videos", q="Video 1")["total"], 1)
        self.assertEqual(self.rows(scope=f"channel:{self.channel}", kind="shorts", q="Video 1")["total"], 0)
        self.assertEqual(self.rows(scope=f"playlist:{playlist}")["total"], 1)

    def test_publication_date_wins_over_capture_order_with_stable_fallback(self):
        older = self.add(1, date="20200101", created=1900000000)
        newer = self.add(2, date="20260101", created=1600000000)
        missing = self.add(3, date=None, created=1735689600)  # 2025-01-01 UTC
        invalid = self.add(4, date="invalid", created=1735689600)
        self.assertEqual([row["id"] for row in self.rows()["videos"]], [newer, invalid, missing, older])
        with self.archive.db() as db:
            plan = " ".join(str(tuple(row)) for row in db.execute(
                f"EXPLAIN QUERY PLAN SELECT * FROM video WHERE state='ready' AND kind='videos' ORDER BY {PUBLICATION_ORDER} LIMIT 60"))
        self.assertIn("video_kind_publication", plan)
        self.assertNotIn("TEMP B-TREE", plan)

    def test_playlist_exports_use_the_same_publication_order(self):
        first = self.add(1, date="20200101", created=1900000000)
        second = self.add(2, date="20260101", created=1600000000)
        playlist = self.client.post("/api/playlists", json={"name": "Order", "video": first}).json["id"]
        self.client.put(f"/api/playlists/{playlist}/videos/{second}")
        with self.archive.db() as db:
            self.assertEqual([row["id"] for row in self.archive.playlist_rows(db, playlist)], [second, first])

    def test_link_metadata_identifies_completed_lives_without_duration_guesses(self):
        for info, expected in (({"live_status": "was_live"}, "streams"),
                               ({"was_live": True}, "streams"),
                               ({"original_url": "https://youtube.com/shorts/item0000001"}, "shorts"),
                               ({"duration": 30, "width": 1920, "height": 1080}, None)):
            meta = collector.video_metadata({"id": "item0000001", **info})
            self.assertEqual(meta["kind"], expected)
        video_id = self.add(1)
        folder = self.archive.library / f"Avulsos/Live [{video_id}]"
        folder.mkdir(parents=True)
        (folder / "main.mp4").write_bytes(b"video")
        collector.write_manifest(folder, {"title": "Live", "filename": "main.mp4", "kind": "streams"})
        with self.archive.db() as db:
            db.execute("UPDATE video SET pending_folder=? WHERE id=?", (str(folder.relative_to(self.archive.library)), video_id))
            self.archive.finish_publish(db, db.execute("SELECT * FROM video WHERE id=?", (video_id,)).fetchone())
        self.assertEqual(self.rows(kind="streams")["videos"][0]["id"], video_id)

    def test_only_new_automatic_captures_receive_the_badge(self):
        manual = self.add(1)
        with self.archive.db() as db:
            db.execute("UPDATE channel SET source='https://www.youtube.com/@fixture',auto=1,baseline=1,next_sync=0 WHERE id=?", (self.channel,))
        entries = [{"id": f"item{n:07d}", "title": f"Video {n}", "kind": "videos", "duration": 60,
                    "url": f"https://youtu.be/item{n:07d}"} for n in (1, 2)]
        with patch("collector.channel_entries", return_value=iter([(None, entry) for entry in entries])):
            self.archive.sync_channels()
        with self.archive.db() as db:
            self.assertEqual(db.execute("SELECT unopened_auto FROM video WHERE id=?", (manual,)).fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT unopened_auto FROM video WHERE id='item0000002'").fetchone()[0], 1)
        self.assertFalse(self.rows(state="jobs")["videos"][0]["is_new"])

    def test_open_clears_new_badge_persistently_without_changing_progress(self):
        video_id = self.add(1, automatic=True)
        self.assertTrue(self.rows(summary=1)["videos"][0]["is_new"])
        self.assertTrue(self.rows()["videos"][0]["is_new"])  # Listing is read-only.
        self.assertEqual(self.client.post(f"/api/videos/{video_id}/opened", json={}).status_code, 200)
        self.assertEqual(self.client.post(f"/api/videos/{video_id}/opened", json={}).status_code, 200)
        restored = create_app(self.root / "data", self.root / "archive", workers=False).test_client()
        row = restored.get("/api/videos").json["videos"][0]
        self.assertFalse(row["is_new"])
        self.assertEqual(row["position"], 0)

    def test_old_backups_without_badge_column_remain_accepted(self):
        # A queued record does not require real media during backup validation.
        self.client.post("/api/downloads", json={"url": "https://youtu.be/item0000001"})
        backup = self.client.get("/api/system/backup").data
        records = [json.loads(line) for line in backup.splitlines()]
        for record in records:
            if record.get("table") == "video":
                record["row"].pop("unopened_auto")
        old = "\n".join(json.dumps(record) for record in records) + "\n"
        response = self.client.post("/api/system/backup/preview", data={"backup": (io.BytesIO(old.encode()), "old.jsonl")})
        self.assertEqual(response.status_code, 200, response.json)
        token = response.json["token"]
        self.assertEqual(self.client.post("/api/system/backup/restore", json={"token": token}).status_code, 202)
        restored = create_app(self.root / "data", self.root / "archive", workers=False).test_client()
        self.assertEqual(restored.get(f"/api/system/backup/status/{token}").json["status"], "verified")
        with self.archive.db() as db:
            self.assertEqual(db.execute("SELECT unopened_auto FROM video").fetchone()[0], 0)

    def test_existing_database_is_migrated_without_badging_old_downloads(self):
        self.add(1)
        with sqlite3.connect(self.root / "data/library.sqlite") as db:
            db.execute("ALTER TABLE video DROP COLUMN unopened_auto")
        restored = create_app(self.root / "data", self.root / "archive", workers=False).test_client()
        self.assertFalse(restored.get("/api/videos").json["videos"][0]["is_new"])

    def test_backup_restore_preserves_unopened_automatic_badges(self):
        video_id = self.add(1, automatic=True)
        backup = self.client.get("/api/system/backup").data
        self.client.post(f"/api/videos/{video_id}/opened", json={})
        preview = self.client.post("/api/system/backup/preview", data={"backup": (io.BytesIO(backup), "new.jsonl")})
        self.assertEqual(preview.status_code, 200, preview.json)
        token = preview.json["token"]
        self.client.post("/api/system/backup/restore", json={"token": token})
        restored = create_app(self.root / "data", self.root / "archive", workers=False).test_client()
        self.assertEqual(restored.get(f"/api/system/backup/status/{token}").json["status"], "verified")
        self.assertTrue(restored.get("/api/videos?summary=1").json["videos"][0]["is_new"])

    def test_visibility_exclusions_apply_to_mixed_lists_before_pagination(self):
        self.add(1)
        self.add(2, "shorts")
        self.add(3, "streams")
        result = self.client.get("/api/videos?exclude_kind=shorts&exclude_kind=streams").json
        self.assertEqual((result["total"], result["videos"][0]["kind"]), (1, "videos"))
        self.assertEqual(self.rows(exclude_kind="streams")["total"], 2)
        self.assertEqual(self.client.get("/api/videos?exclude_kind=videos").status_code, 400)
        self.assertEqual(self.rows(kind="shorts", exclude_kind="shorts")["total"], 0)

    def test_live_download_policy_is_inherited_and_channel_can_override_it(self):
        self.assertEqual(self.client.put("/api/settings", json={"lives": "exclude"}).status_code, 200)
        with self.archive.db() as db:
            db.execute("UPDATE channel SET source='https://www.youtube.com/@fixture',auto=1,baseline=1,next_sync=0 WHERE id=?", (self.channel,))
        def entry(number, kind):
            return {"id": f"item{number:07d}", "title": "Fixture", "kind": kind,
                    "url": f"https://youtu.be/item{number:07d}"}
        with patch("collector.channel_entries", return_value=iter([(None, entry(1, "streams")), (None, entry(2, "videos"))])):
            self.archive.sync_channels()
        self.assertEqual([row["kind"] for row in self.rows(state="jobs")["videos"]], ["videos"])
        with self.archive.db() as db:
            db.execute("UPDATE channel SET overrides=?,next_sync=0 WHERE id=?", (json.dumps({"lives": "include"}), self.channel))
        with patch("collector.channel_entries", return_value=iter([(None, entry(3, "streams"))])):
            self.archive.sync_channels()
        self.assertEqual(self.rows(state="jobs", kind="streams")["total"], 1)
        # An explicitly selected live is still allowed when monitoring excludes lives.
        with self.archive.db() as db:
            channel = self.archive.channel(db, self.channel)
            self.assertEqual(self.archive.enqueue(db, entry(4, "streams"), channel, {"lives": "exclude"}), 1)
