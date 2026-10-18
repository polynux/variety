# Fixtures 2026-10-18 (task 1.2)

Captured with fork `Util.request()` (UA `Variety Wallpaper Changer 0.9.2`).

| file | url | status | kind |
|------|-----|--------|------|
| `reddit_json_wallpaper.*` | `/r/wallpaper.json?limit=5` | 403 | blocked (`whoa there, pardner!` HTML) |
| `reddit_json_wallpapers.*` | `/r/wallpapers.json?limit=5` | 403 | blocked |
| `reddit_rss_wallpaper.*` | `/r/wallpaper/.rss` | 403 | blocked (was 200 atom earlier, now blocked) |
| `reddit_rss_wallpapers.*` | `/r/wallpapers/.rss` | 429 | rate-limited, empty body |
| `reddit_old_json_wallpaper.*` | `old.reddit/...json` | 200 | `html-block-or-login` (login page, not JSON) |
| `reddit_oauth_hot.*` | `oauth.reddit...` | 403 | blocked (no token) |

Each `*.meta.json` has `{status, content_type, kind, body_len, body_head}`.
`*.body.txt` is raw body (capped 500k).

`reddit_rss_sample.xml` is synthetic (offline) Atom feed mimicking pre-block Reddit RSS,
used for parser unit tests when live is blocked.
