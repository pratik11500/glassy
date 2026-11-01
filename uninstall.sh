#!/usr/bin/env bash
# glassy uninstaller
#   bash <(curl -fsSL https://raw.githubusercontent.com/pratik11500/glassy/main/uninstall.sh)
# Add --purge to also delete your config file.
set -u

APP="$HOME/.local/share/glassy"
BIN="$HOME/.local/bin/glassy"
FONTS="$HOME/.local/share/fonts/glassy"
CONFIG_DIR="$HOME/.config/glassy"
AUTOSTART="$HOME/.config/autostart/glassy.desktop"
CACHE="$HOME/.cache/glassy"

say() { printf "\033[1;36m==>\033[0m %s\n" "$*"; }

say "Stopping widgets..."
[ -x "$BIN" ] && "$BIN" stop
pkill -f "$APP/left_widget.py" 2>/dev/null
pkill -f "$APP/right_widget.py" 2>/dev/null
pkill -f "conky .*glassy/conkyrc" 2>/dev/null

say "Removing files..."
rm -f "$AUTOSTART" "$BIN"
rm -rf "$APP" "$FONTS" "$CACHE"
command -v fc-cache >/dev/null 2>&1 && fc-cache -f "$HOME/.local/share/fonts" >/dev/null 2>&1

if [ "${1:-}" = "--purge" ]; then
  rm -rf "$CONFIG_DIR"
  say "Config removed."
else
  say "Your config was kept at $CONFIG_DIR (use --purge to delete it)."
fi

say "glassy removed. Installed packages (python3-gi, conky, wmctrl...) were left alone."
