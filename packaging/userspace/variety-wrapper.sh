#!/bin/sh
# Userspace Variety from fork ~/dev/variety (task 3.1)
# venv with --system-site-packages for GI/GExiv2 + PYTHONPATH so fork shadows /usr/lib system variety, no sudo
export PYTHONPATH="/home/polynux/dev/variety:${PYTHONPATH:-}"
exec "$HOME/.local/share/variety-fork-venv/bin/variety" "$@"
