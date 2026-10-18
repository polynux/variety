#!/bin/sh
# Reproducible userspace install, no sudo. Requires system python3-gi + gir1.2-gexiv2.
set -eu
FORK_DIR="${1:-$HOME/dev/variety}"
VENV="$HOME/.local/share/variety-fork-venv"
uv venv --system-site-packages --python 3.14 "$VENV"
uv pip install --python "$VENV/bin/python" -e "$FORK_DIR"
install -m755 "$FORK_DIR/packaging/userspace/variety-wrapper.sh" "$HOME/.local/bin/variety"
"$HOME/.local/bin/variety" --version
