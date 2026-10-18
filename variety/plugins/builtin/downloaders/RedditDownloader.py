# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (c) 2012, Peter Levi <peterlevi@peterlevi.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import logging
import random
import re
import urllib.parse
import xml.etree.ElementTree as ET

from variety.plugins.downloaders.DefaultDownloader import DefaultDownloader
from variety.Util import Util

logger = logging.getLogger("variety")

ATOM_NS = "{http://www.w3.org/2005/Atom}"
MEDIA_NS = "{http://search.yahoo.com/mrss/}"

# Markers observed in live fixtures 2026-10-18 (see fixtures/*.meta.json):
# - 403 HTML body contains "whoa there, pardner!" + "blocked due to a network policy"
# - 429 with empty body (rate-limited)
# - old.reddit 200 login HTML ("Welcome to Reddit", "Log in or sign up")
BLOCKED_MARKERS = (
    "whoa there, pardner",
    "blocked due to a network policy",
    "Your request has been blocked",
)


def is_blocked_response(status=None, content_type="", text=""):
    """Detect Reddit anti-bot Blocked / rate-limit / login-wall responses.

    Used to decide JSON-first -> RSS-fallback and to return empty queue
    instead of raising on expected network-policy blocks.
    """
    if status in (403, 429):
        return True
    t = (text or "")[:8000].lower()
    for m in BLOCKED_MARKERS:
        if m.lower() in t:
            return True
    # old.reddit 200 login wall: HTML page, not JSON/RSS
    if status == 200 and "text/html" in (content_type or ""):
        if "welcome to reddit" in t or "log in or sign up" in t:
            return True
    return False


class RedditDownloader(DefaultDownloader):
    def __init__(self, source, url):
        DefaultDownloader.__init__(self, source=source, config=url)

    @staticmethod
    def build_json_url(url):
        p = urllib.parse.urlparse(url)
        return (
            p.scheme
            + "://"
            + p.netloc
            + p.path
            + ".json"
            + "?"
            + p.query
            + ("&" if p.query else "")
            + "limit=100"
        )

    @staticmethod
    def build_rss_url(url):
        """https://www.reddit.com/r/wallpaper -> .../r/wallpaper/.rss
        Preserves sort/query, e.g. /r/comics/top/?sort=top&t=week -> /top/.rss?sort=top&t=week
        """
        p = urllib.parse.urlparse(url)
        path = p.path.rstrip("/") + "/.rss"
        return p.scheme + "://" + p.netloc + path + (("?" + p.query) if p.query else "")

    @staticmethod
    def normalize_image_url(url):
        if not url:
            return None
        url = url.strip().replace("&amp;", "&")
        # imgur page -> direct image (legacy behavior, kept for parity with JSON path)
        if re.match(r"^https?://imgur\.com/\w+$", url):
            url = url.replace("://", "://i.") + ".jpg"
        # strip query/fragment for extension check, but keep full URL for download
        parsed = urllib.parse.urlparse(url)
        if parsed.path.lower().endswith((".jpg", ".jpeg", ".png")):
            return url
        return None

    @staticmethod
    def entry_is_nsfw(entry):
        # <category term="nsfw"> / over_18 variants + title markers
        for cat in entry.findall(f"{ATOM_NS}category"):
            term = (cat.attrib.get("term") or "").lower()
            if term in ("nsfw", "over_18", "over18", "over-18"):
                return True
        title_el = entry.find(f"{ATOM_NS}title")
        if title_el is not None and title_el.text:
            if re.search(r"\bnsfw\b", title_el.text, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def extract_candidates_from_entry(entry):
        """Collect candidate image URLs from an Atom <entry>, in priority order."""
        candidates = []

        def add(u):
            if u and u not in candidates:
                candidates.append(u)

        # media:thumbnail / media:content urls first (usually direct images)
        for tag in (f"{MEDIA_NS}thumbnail", f"{MEDIA_NS}content"):
            for el in entry.findall(f".//{tag}"):
                add(el.attrib.get("url"))

        # <link href="..."> is usually the comments page, but occasionally direct
        link_el = entry.find(f"{ATOM_NS}link")
        if link_el is not None:
            add(link_el.attrib.get("href"))

        # content HTML: <a href="..."> and <img src="...">
        content_el = entry.find(f"{ATOM_NS}content")
        html = content_el.text if content_el is not None and content_el.text else ""
        for m in re.finditer(r'href="([^"]+)"', html):
            add(m.group(1).replace("&amp;", "&"))
        for m in re.finditer(r'src="([^"]+)"', html):
            add(m.group(1).replace("&amp;", "&"))

        # fallback: bare https URLs in content text
        for m in re.finditer(r"https?://[^\s\"'<>]+", html):
            add(m.group(0).rstrip(".,);"))

        return candidates

    @staticmethod
    def parse_rss_content(content_bytes):
        """Parse Atom RSS bytes -> queue items [(origin_url, image_url, extra_metadata)]."""
        try:
            root = ET.fromstring(content_bytes)
        except ET.ParseError:
            logger.warning(lambda: "Reddit RSS: could not parse XML, probably Blocked HTML")
            return []
        queue = []
        # entries may be namespaced or bare depending on source
        entries = root.findall(f"{ATOM_NS}entry") or root.findall("entry")
        for entry in entries:
            try:
                link_el = entry.find(f"{ATOM_NS}link")
                if link_el is None:
                    link_el = entry.find("link")
                origin_url = link_el.attrib.get("href") if link_el is not None else None
                if not origin_url:
                    continue
                nsfw = RedditDownloader.entry_is_nsfw(entry)
                for cand in RedditDownloader.extract_candidates_from_entry(entry):
                    image_url = RedditDownloader.normalize_image_url(cand)
                    if image_url:
                        extra_metadata = {"sourceType": "reddit"}
                        if nsfw:
                            extra_metadata["sfwRating"] = 0
                        queue.append((origin_url, image_url, extra_metadata))
                        break  # one image per entry
            except Exception:
                logger.exception(lambda: "Could not process an item in the Reddit RSS result")
        random.shuffle(queue)
        return queue

    def fetch_rss_queue(self):
        rss_url = RedditDownloader.build_rss_url(self.config)
        logger.info(lambda: "Reddit RSS URL: " + rss_url)
        try:
            content = Util.fetch_bytes(rss_url)
        except Exception as e:
            resp = getattr(e, "response", None)
            status = resp.status_code if resp is not None else None
            body = resp.text if resp is not None else ""
            ctype = resp.headers.get("Content-Type", "") if resp is not None else ""
            if status in (403, 429) or is_blocked_response(status, ctype, body):
                logger.warning(
                    lambda: "Reddit RSS blocked/rate-limited (%s), returning empty queue" % status
                )
                return []
            raise
        # fetch_bytes succeeded but body may still be a login wall (old.reddit 200 HTML)
        head = content[:8000].decode("utf-8", errors="replace") if isinstance(content, bytes) else content[:8000]
        if is_blocked_response(200, "text/html" if head.lstrip().lower().startswith("<!doctype") else "application/atom+xml", head):
            # Only treat as blocked if it is clearly not XML feed
            if "<feed" not in head[:2000]:
                logger.warning(lambda: "Reddit RSS returned login/block wall, empty queue")
                return []
        return RedditDownloader.parse_rss_content(content)

    def fill_queue(self):
        logger.info(lambda: "Reddit URL: " + self.config)

        # JSON-first
        json_url = RedditDownloader.build_json_url(self.config)
        try:
            s = Util.fetch_json(json_url)
        except Exception as e:
            resp = getattr(e, "response", None)
            status = resp.status_code if resp is not None else None
            body = resp.text if resp is not None else ""
            ctype = resp.headers.get("Content-Type", "") if resp is not None else ""
            if status in (403, 429) or is_blocked_response(status, ctype, body):
                logger.warning(
                    lambda: "Reddit JSON blocked (%s), falling back to RSS" % status
                )
                return self.fill_queue_rss_fallback()
            # Non-block errors (DNS, timeout): also try RSS once before giving up
            logger.exception(lambda: "Reddit JSON fetch failed, trying RSS fallback")
            try:
                return self.fill_queue_rss_fallback()
            except Exception:
                raise e

        queue = []
        for item in s["data"]["children"]:
            try:
                data = item["data"]
                image_url = data["url"]
                if re.match(r"^http(s)?://imgur\.com/\w+$", image_url):
                    image_url = image_url.replace("://", "://i.") + ".jpg"

                if image_url.lower().endswith((".jpg", ".jpeg", ".png")):
                    src_url = "https://www.reddit.com" + data["permalink"]
                    extra_metadata = {"sourceType": "reddit"}
                    if data["over_18"]:
                        extra_metadata["sfwRating"] = 0
                        if self.is_safe_mode_enabled():
                            continue
                    queue.append((src_url, image_url, extra_metadata))
            except Exception:
                logger.exception(lambda: "Could not process an item in the Reddit json result")

        random.shuffle(queue)
        return queue

    def fill_queue_rss_fallback(self):
        queue = self.fetch_rss_queue()
        if self.is_safe_mode_enabled():
            queue = [q for q in queue if q[2].get("sfwRating", 5) != 0]
        return queue
