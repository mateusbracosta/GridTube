import json
import tempfile
import threading
import unittest
from http.cookiejar import CookieJar
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import collector
from app import create_app


class ProfileLocaleTests(unittest.TestCase):
    source = "https://www.youtube.com/@fixture"

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.app = create_app(self.root / "data", self.root / "archive", workers=False)
        self.archive = self.app.extensions["archive"]
        self.client = self.app.test_client()
        self.channel = self.client.post("/api/channels", json={"source": self.source, "name": "My label"}).json["id"]

    def save(self, locale, description):
        self.archive.save_profile(self.source, {"name": "Creator", "description": description,
                                               "handle": "@fixture", "avatar": None, "banner": None}, locale)

    def description(self, locale):
        response = self.client.get("/api/state", headers={"X-GridTube-Locale": locale})
        channel = response.json["channels"][0]
        self.assertEqual(channel["name"], "My label")
        return channel["profile"]

    def test_translations_are_selected_per_request_and_survive_restart(self):
        self.save("pt-BR", "Bem-vindo ao canal")
        self.save("en-US", "Welcome to the channel")
        self.assertEqual(self.description("pt-BR")["description"], "Bem-vindo ao canal")
        self.assertEqual(self.description("en")["description"], "Welcome to the channel")
        self.assertEqual(self.description("pt-BR")["description"], "Bem-vindo ao canal")
        restarted = create_app(self.root / "data", self.root / "archive", workers=False).test_client()
        self.assertEqual(restarted.get("/api/state", headers={"Accept-Language": "en-US"}).json[
            "channels"][0]["profile"]["description"], "Welcome to the channel")

    def test_missing_locale_falls_back_and_empty_refresh_keeps_saved_text(self):
        self.save("pt-BR", "Descrição disponível")
        fallback = self.description("en-GB")
        self.assertFalse(fallback["locale_available"])
        self.assertEqual(fallback["description"], "Descrição disponível")
        self.save("en-GB", "Welcome")
        self.save("en-GB", "")
        self.assertEqual(self.description("en-GB")["description"], "Welcome")

    def test_legacy_profile_and_custom_description_are_preserved(self):
        with self.archive.db() as db:
            db.execute("INSERT INTO channel_profile VALUES (?,?,?)",
                       (self.source, json.dumps({"name": "Creator", "description": "Original bio"}), "fixture"))
            db.execute("INSERT INTO channel_description VALUES (?,?)", (self.channel, "My own bio"))
        response = self.client.get("/api/state", headers={"X-GridTube-Locale": "en-US"})
        channel = response.json["channels"][0]
        self.assertEqual(channel["profile"]["description"], "Original bio")
        self.assertEqual(channel["custom_description"], "My own bio")
        self.assertFalse(channel["profile"]["locale_available"])

    def test_extractor_receives_supported_language_region_and_session_cookie(self):
        for locale, language, region in (("pt-BR", "pt", "BR"), ("en-GB", "en-GB", "GB"), ("en-BR", "en", "BR")):
            downloader = MagicMock()
            downloader.cookiejar = CookieJar()
            downloader.extract_info.return_value = {"channel": "Creator", "description": "Bio"}
            with patch("collector.YoutubeDL") as factory:
                factory.return_value.__enter__.return_value = downloader
                profile = collector.fetch_channel_profile(self.source, locale)
            options = factory.call_args.args[0]
            self.assertEqual(options["extractor_args"]["youtube"]["lang"], [language])
            self.assertTrue(options["http_headers"]["Accept-Language"].startswith(locale))
            query = parse_qs(urlsplit(downloader.extract_info.call_args.args[0]).query)
            self.assertEqual(query, {"hl": [language], "gl": [region]})
            cookie = list(downloader.cookiejar)[0]
            self.assertTrue(cookie.discard)
            self.assertEqual(parse_qs(cookie.value)["gl"], [region])
            self.assertEqual(profile["description"], "Bio")

    def test_background_profile_requests_are_deduplicated_and_can_be_forced(self):
        started, release = threading.Event(), threading.Event()

        def fetch(*args):
            started.set()
            if not release.wait(5):
                raise TimeoutError("Test did not release the profile fetch")

        with patch.object(self.archive, "refresh_profile", side_effect=fetch) as refresh:
            self.assertTrue(self.archive.schedule_profile(self.source, "pt-BR"))
            try:
                self.assertTrue(started.wait(3))
                self.assertFalse(self.archive.schedule_profile(self.source, "pt-BR", force=True))
            finally:
                release.set()
            self.archive.catalog.submit(lambda: None).result(timeout=5)
            self.assertFalse(self.archive.schedule_profile(self.source, "pt-BR"))
            self.assertTrue(self.archive.schedule_profile(self.source, "pt-BR", force=True))
            self.archive.catalog.submit(lambda: None).result(timeout=5)
            self.assertEqual(refresh.call_count, 2)

    def test_profile_endpoint_uses_client_locale_and_rejects_cross_origin(self):
        url = f"/api/channels/{self.channel}/profile"
        with patch.object(self.archive, "schedule_profile", return_value=True) as schedule:
            response = self.client.post(url, json={"force": True}, headers={"X-GridTube-Locale": "en-GB"})
            self.assertEqual(response.status_code, 202)
            schedule.assert_called_once_with(self.source, "en-GB", True)
            response = self.client.post(url, json={}, headers={"Origin": "https://other.example"})
            self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
