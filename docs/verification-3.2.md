# Verification 3.2 (2026-10-18)

## Userspace binary
- `~/.local/bin/variety` -> wrapper execs `~/.local/share/variety-fork-venv/bin/variety` (uv venv `--system-site-packages --python 3.14`, editable fork install).
- `which variety` = `~/.local/bin/variety` (PATH before `/usr/bin`), `--version` = `0.9.2`.
- Shadowing fix (real blocker hit): system `/usr/lib/python3.14/site-packages/variety` shadowed fork because `PathFinder` precedes editable finder in `sys.meta_path`. Fixed with `zz-fork-first.pth` (`/home/polynux/dev/variety`) + `PYTHONPATH` export in wrapper. Verified from `/tmp`: `VarietyWindow.__file__` = fork path.

## Wallpaper (Hyprland DP-1 + DP-2, hyprpaper 0.8.4)
- Switched user config (backup `variety.conf.bak.2026-10-18_0333`) from `set_wallpaper_arco`/`get_wallpaper_arco` to `set_wallpaper`/`get_wallpaper`.
- `set_wallpaper` new script: silent, exit 0, `listactive` shows both monitors on Variety wallpaper.
- `timeout 12 ~/.local/bin/variety`: `CLEAN: no invalid hyprpaper request`, `listactive` DP-1+DP-2 on `wallpaper-auto-rotated-*.jpg`.
- Pre-existing unrelated: `image_ok() Error ... Favorites/wallhaven-2136ly.jpg Not an image` (bad favorite file, not Reddit/hyprpaper).

## Reddit (fork code proven in userspace run)
- `variety.log` paths = `/home/polynux/dev/variety/variety/...` (fork, not `/usr/lib`).
- Explicit: `Reddit JSON blocked (403), falling back to RSS` -> `RSS blocked (403), returning empty queue`, `len=0`, 0 tracebacks (system code raised 403 tracebacks).
- `pytest tests/TestRedditRssFallback.py` 5 passed; `test_build_json_url` 1 passed.
