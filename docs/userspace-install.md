# Userspace install evaluation (task 3.1)

Goal: `~/.local/bin/variety` without sudo, from fork `/home/polynux/dev/variety`.

## Options evaluated

### 1. PyInstaller single binary — rejected
- Would need to bundle PyGObject, PangoCairo, Gdk, GExiv2, dbus, PIL + GI typelibs (`/usr/lib/x86_64-linux-gnu/girepository-1.0/*`).
- Result >200MB, fragile across GTK/Hyprland updates, still needs system `libgtk-3`, `libgexiv2`, crashes on missing `GdkPixbuf` loaders.
- Variety upstream never ships PyInstaller; no spec for it.

### 2. zipapp / pex single file — rejected
- Pure-python zip cannot carry C extensions (`gi._gi`, `cairo`, `GExiv2`) nor GI typelibs.
- Would still require system `python3-gi` + `PYTHONPATH`, so not single-file in practice.

### 3. `uv tool install` / `pipx` — rejected for GI app
- `uv tool install` creates isolated venv **without** `--system-site-packages` (no flag in `uv tool install --help`).
- Isolated venv cannot `import gi` / `GExiv2` (system `python3-gi`, `gir1.2-gexiv2` only in `/usr/lib/python3/dist-packages`).
- Verified: system python has `GExiv2 OK`, isolated venv would fail.

### 4. Manual venv with `--system-site-packages` + wrapper — chosen
- `uv venv --system-site-packages ~/.local/share/variety-fork-venv`
- `uv pip install --python <venv> -e /home/polynux/dev/variety`
- Wrapper `~/.local/bin/variety` execs venv binary. Single entry, no sudo, survives system python GI updates.
- Matches existing user pattern (`~/.local/share/uv/tools/*` + symlinks in `~/.local/bin`).

## Auth files (no secrets in repo)
- `~/.config/variety/reddit_token` or `$VARIETY_REDDIT_TOKEN` -> Bearer
- `~/.config/variety/reddit_cookie` or `$VARIETY_REDDIT_COOKIE` -> Cookie
- `VARIETY_REDDIT_USER_AGENT` override
