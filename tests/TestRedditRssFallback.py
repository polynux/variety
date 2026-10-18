#!/usr/bin/python3
"""Offline + live tests for Reddit RSS fallback (task 2.3). Offline, no secrets."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock

from variety.plugins.builtin.downloaders.RedditDownloader import (
    RedditDownloader,
    is_blocked_response,
)

FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def load(name):
    with open(os.path.join(FIX, name), encoding="utf-8", errors="replace") as f:
        return f.read()


class TestRedditRssFallback(unittest.TestCase):
    def test_blocked_fixtures_detected(self):
        for meta_name in (
            "reddit_json_wallpaper.meta.json",
            "reddit_json_wallpapers.meta.json",
            "reddit_rss_wallpaper.meta.json",
            "reddit_rss_wallpapers.meta.json",
            "reddit_old_json_wallpaper.meta.json",
        ):
            with open(os.path.join(FIX, meta_name), encoding="utf-8") as f:
                m = json.load(f)
            body = load(meta_name.replace(".meta.json", ".body.txt"))
            self.assertTrue(
                is_blocked_response(m["status"], m["content_type"], body),
                f"{meta_name} should classify as blocked",
            )

    def test_build_rss_url(self):
        self.assertEqual(
            "https://www.reddit.com/r/wallpaper/.rss",
            RedditDownloader.build_rss_url("https://www.reddit.com/r/wallpaper"),
        )
        self.assertEqual(
            "http://www.reddit.com/r/comics/top/.rss?sort=top&t=week",
            RedditDownloader.build_rss_url("http://www.reddit.com/r/comics/top/?sort=top&t=week"),
        )

    def test_parse_synthetic_rss(self):
        data = open(os.path.join(FIX, "reddit_rss_sample.xml"), "rb").read()
        q = RedditDownloader.parse_rss_content(data)
        self.assertEqual(4, len(q))
        by_origin = {o: (i, m) for o, i, m in q}
        self.assertIn("https://i.imgur.com/def456.jpg", [i for _, i, _ in q])
        nsfw = [x for x in q if x[2].get("sfwRating") == 0]
        self.assertEqual(1, len(nsfw))

    def test_safe_mode_filters_nsfw(self):
        data = open(os.path.join(FIX, "reddit_rss_sample.xml"), "rb").read()
        q = RedditDownloader.parse_rss_content(data)

        class FakeOpts:
            safe_mode = True

        class FakeVariety:
            options = FakeOpts()

        dl = RedditDownloader(MagicMock(), "https://www.reddit.com/r/wallpaper")
        dl.get_variety = lambda: FakeVariety()
        filtered = [x for x in q if x[2].get("sfwRating", 5) != 0]
        self.assertEqual(3, len(filtered))

    def test_auth_headers_empty_by_default(self):
        for k in (
            "VARIETY_REDDIT_TOKEN",
            "VARIETY_REDDIT_TOKEN_FILE",
            "VARIETY_REDDIT_COOKIE",
            "VARIETY_REDDIT_COOKIE_FILE",
            "VARIETY_REDDIT_USER_AGENT",
        ):
            os.environ.pop(k, None)
        os.environ["VARIETY_REDDIT_TOKEN_FILE"] = "/tmp/nonexistent_token_123_xyz"
        os.environ["VARIETY_REDDIT_COOKIE_FILE"] = "/tmp/nonexistent_cookie_123_xyz"
        try:
            self.assertEqual({}, RedditDownloader.get_auth_headers())
        finally:
            os.environ.pop("VARIETY_REDDIT_TOKEN_FILE", None)
            os.environ.pop("VARIETY_REDDIT_COOKIE_FILE", None)


if __name__ == "__main__":
    unittest.main()
