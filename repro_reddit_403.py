"""Reproduce Reddit 403 from fork source. Run: PYTHONPATH=~/dev/variety python3 repro_reddit_403.py"""
from variety.Util import Util
from variety.plugins.builtin.downloaders.RedditDownloader import RedditDownloader
for src in ["https://www.reddit.com/r/wallpaper", "https://www.reddit.com/r/wallpapers"]:
    json_url = RedditDownloader.build_json_url(src)
    print(f"\nSRC: {src}\nJSON_URL: {json_url}")
    try:
        r = Util.request(json_url)
        print(f"STATUS: {r.status_code} len={len(r.content)}")
    except Exception as e:
        print(f"REPRODUCED: {type(e).__name__}: {e}")
