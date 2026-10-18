#!/bin/sh
# Userspace Variety entry (single entry in ~/.local/bin, no sudo)
exec "$HOME/.local/share/variety-fork-venv/bin/variety" "$@"
