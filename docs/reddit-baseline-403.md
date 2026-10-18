# Baseline: Reddit 403 Blocked (2026-10-18)

Fork: `polynux/variety` from `varietywalls/variety@master (0.9.2, commit 8446011)`

## Flow
1. `variety/plugins/builtin/downloaders/RedditDownloader.py:33 build_json_url(url)`:
   `https://www.reddit.com/r/wallpaper` -> `https://www.reddit.com/r/wallpaper.json?limit=100`
2. `RedditDownloader.fill_queue():47-52` calls `Util.fetch_json(json_url)`
3. `variety/Util.py:63 USER_AGENT = "Variety Wallpaper Changer " + get_version()` (0.9.2)
4. `Util.request():671-693` sets `headers={"User-Agent": USER_AGENT, "Cache-Control": "max-age=0"}` then `requests.request(...).raise_for_status()`
5. `Util.fetch_json():712-713` returns `.json()`

No custom headers/cookies/OAuth supported. `RedditSource.py` registers type `reddit`.

## Repro (from fork source)
```
PYTHONPATH=~/dev/variety python3 repro_reddit_403.py
# or: from variety.Util import Util; Util.request("https://www.reddit.com/r/wallpaper.json?limit=100")
```
Result 2026-10-18:
- `https://www.reddit.com/r/wallpaper.json?limit=100` -> `HTTPError 403 Client Error: Blocked`
- `https://www.reddit.com/r/wallpapers.json?limit=100` -> same 403
- Body is Reddit `theme-beta` Blocked HTML (`whoa there, pardner! ... network policy ... register/sign in with developer credentials`), not JSON.
- Same with browser UA. `old.reddit.com/*.json` -> 404. `*.rss` intermittently 200 then Blocked (see task 1.2 fixtures).

## Conclusion
Unauthenticated JSON is dead. Phase 2 needs RSS fallback + optional `Cookie`/`Bearer` passthrough.

## Auth passthrough (task 2.2)
- `RedditDownloader.get_auth_headers()` reads (no secrets in repo):
  - `VARIETY_REDDIT_TOKEN` / `VARIETY_REDDIT_TOKEN_FILE` (default `~/.config/variety/reddit_token`) -> `Authorization: Bearer <token>`, auto-switches `www.reddit.com` -> `oauth.reddit.com`
  - `VARIETY_REDDIT_COOKIE` / `VARIETY_REDDIT_COOKIE_FILE` (default `~/.config/variety/reddit_cookie`) -> `Cookie: ...`
  - `VARIETY_REDDIT_USER_AGENT` overrides UA
- `fill_queue()` = JSON-first with headers, fallback to RSS on 403/429/Blocked; `RedditSource.create_downloader()` unchanged (already returns `RedditDownloader`).
