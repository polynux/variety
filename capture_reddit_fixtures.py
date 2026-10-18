"""Capture live Blocked vs RSS responses as fixtures for offline tests (task 1.2).
Saves raw bodies + meta JSON under fixtures/. No secrets.
"""
import json, os, re, sys
sys.path.insert(0, "/home/polynux/dev/variety")
from variety.Util import Util

OUT = "/home/polynux/dev/variety/fixtures"
os.makedirs(OUT, exist_ok=True)

TARGETS = [
  ("reddit_json_wallpaper", "https://www.reddit.com/r/wallpaper.json?limit=5"),
  ("reddit_json_wallpapers", "https://www.reddit.com/r/wallpapers.json?limit=5"),
  ("reddit_rss_wallpaper", "https://www.reddit.com/r/wallpaper/.rss"),
  ("reddit_rss_wallpapers", "https://www.reddit.com/r/wallpapers/.rss"),
  ("reddit_old_json_wallpaper", "https://old.reddit.com/r/wallpaper.json?limit=5"),
  ("reddit_oauth_hot", "https://oauth.reddit.com/r/wallpaper/hot?limit=2"),
]

def classify(status, ctype, text):
    if status in (403, 429):
        if "whoa there, pardner" in text or "Blocked" in text or "blocked" in text.lower():
            return "blocked"
        return f"http-{status}"
    if status == 404:
        return "not-found"
    if ctype and "atom" in ctype or "<feed" in text[:2000]:
        return "rss-feed"
    if ctype and "json" in ctype:
        return "json"
    if text.lstrip().startswith("{") or text.lstrip().startswith("["):
        return "json"
    if "<html" in text[:2000].lower():
        return "html-block-or-login"
    return "unknown"

for name, url in TARGETS:
    print(f"\n=== {name}: {url}")
    try:
        r = Util.request(url, timeout=20)
        status, ctype, text = r.status_code, r.headers.get("Content-Type",""), r.text
        err = None
    except Exception as e:
        resp = getattr(e, "response", None)
        if resp is not None:
            status, ctype, text = resp.status_code, resp.headers.get("Content-Type",""), resp.text
            err = f"{type(e).__name__}: {e}"
        else:
            status, ctype, text, err = -1, "", "", f"{type(e).__name__}: {e}"
    kind = classify(status, ctype, text or "")
    print(f"  -> status={status} ctype={ctype!r} len={len(text or '')} kind={kind} err={err}")
    # save body (cap 500k) + meta
    body_path = os.path.join(OUT, f"{name}.body.txt")
    meta_path = os.path.join(OUT, f"{name}.meta.json")
    with open(body_path, "w", encoding="utf-8", errors="replace") as f:
        f.write((text or "")[:500000])
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"name": name, "url": url, "status": status, "content_type": ctype,
                   "kind": kind, "error": err, "body_len": len(text or ""),
                   "body_head": (text or "")[:600]}, f, indent=2)
print("\nDone. Files in fixtures/")
