#!/usr/bin/env bash
# glassy installer
#   bash <(curl -fsSL https://raw.githubusercontent.com/pratik11500/glassy/main/install.sh)
# Options: -y  (do not ask questions)
set -euo pipefail

REPO="pratik11500/glassy"
BRANCH="main"
APP="$HOME/.local/share/glassy"
BIN="$HOME/.local/bin"
FONTS="$HOME/.local/share/fonts/glassy"
CONFIG_DIR="$HOME/.config/glassy"
AUTOSTART="$HOME/.config/autostart"
ASSUME_YES=0
[ "${1:-}" = "-y" ] && ASSUME_YES=1

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m  %s\n' "$*"; }
die()  { printf '\033[1;31mxx\033[0m  %s\n' "$*" >&2; exit 1; }

ask() {  # ask "question"  -> returns 0 for yes
  [ "$ASSUME_YES" = 1 ] && return 0
  local reply=""
  if [ -r /dev/tty ]; then
    read -r -p "$1 [Y/n] " reply < /dev/tty || true
  fi
  case "$reply" in n|N|no|NO) return 1 ;; *) return 0 ;; esac
}

[ "$(id -u)" -eq 0 ] && die "Do not run this as root. Run it as your normal user (it will ask for sudo when needed)."
[ "$(uname -s)" = "Linux" ] || die "glassy only works on Linux."

# ---------- 1. get the files ----------
SRC=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  [ -d "$d/widgets" ] && SRC="$d"
fi
if [ -z "$SRC" ]; then
  command -v curl >/dev/null 2>&1 || die "curl is needed. Install it first (for example: sudo apt install curl)."
  command -v tar  >/dev/null 2>&1 || die "tar is needed."
  say "Downloading glassy from GitHub..."
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" -o "$TMP/glassy.tar.gz" \
    || die "Could not download glassy. Check your internet connection (and that github.com/$REPO is public)."
  tar -xzf "$TMP/glassy.tar.gz" -C "$TMP" || die "Downloaded file is broken. Try again."
  SRC="$(find "$TMP" -maxdepth 1 -mindepth 1 -type d | head -n 1)"
  [ -d "$SRC/widgets" ] || die "Download failed or repository layout is wrong."
fi

# ---------- 2. session check ----------
SESSION="${XDG_SESSION_TYPE:-unknown}"
if [ "$SESSION" = "wayland" ]; then
  warn "You are on a Wayland session. glassy needs X11 to place the widgets correctly."
  warn "After install, log out and choose the 'Xorg' / 'X11' session on the login screen."
fi

# ---------- 3. dependencies ----------
deps_ok() {
  command -v python3 >/dev/null 2>&1 || return 1
  command -v wmctrl  >/dev/null 2>&1 || return 1
  command -v conky   >/dev/null 2>&1 || return 1
  python3 - >/dev/null 2>&1 <<'PY'
import gi, psutil, cairo
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Rsvg", "2.0")
from gi.repository import Gtk, Gdk, Rsvg
PY
}

install_deps() {
  if command -v apt-get >/dev/null 2>&1; then
    say "Detected apt (Debian / Ubuntu / Mint family)"
    sudo apt-get update
    sudo apt-get install -y python3 python3-gi python3-gi-cairo python3-psutil \
      gir1.2-gtk-3.0 gir1.2-rsvg-2.0 wmctrl conky-all curl
    sudo apt-get install -y fonts-noto-color-emoji || warn "Emoji font not installed (weather icon may look plain)."
  elif command -v dnf >/dev/null 2>&1; then
    say "Detected dnf (Fedora family)"
    sudo dnf install -y python3 python3-gobject python3-cairo python3-psutil \
      gtk3 librsvg2 wmctrl conky curl
    sudo dnf install -y google-noto-color-emoji-fonts || warn "Emoji font not installed (weather icon may look plain)."
  elif command -v pacman >/dev/null 2>&1; then
    say "Detected pacman (Arch family)"
    sudo pacman -S --needed --noconfirm python python-gobject python-cairo python-psutil \
      gtk3 librsvg wmctrl conky curl
    sudo pacman -S --needed --noconfirm noto-fonts-emoji || warn "Emoji font not installed (weather icon may look plain)."
  elif command -v zypper >/dev/null 2>&1; then
    say "Detected zypper (openSUSE family)"
    sudo zypper install -y python3 python3-gobject python3-gobject-cairo python3-cairo python3-psutil \
      typelib-1_0-Gtk-3_0 typelib-1_0-Rsvg-2_0 wmctrl conky curl
    sudo zypper install -y noto-coloremoji-fonts || warn "Emoji font not installed (weather icon may look plain)."
  else
    die "Could not find apt, dnf, pacman or zypper. Install these yourself, then run this script again:
     python3, PyGObject (gi), pycairo, psutil, GTK 3, librsvg (Rsvg typelib), wmctrl, conky, curl"
  fi
}

if deps_ok; then
  say "All dependencies are already installed."
else
  say "Some dependencies are missing. They will be installed with sudo."
  ask "Continue?" || die "Cancelled."
  install_deps
  deps_ok || die "Dependencies still look incomplete. Check the messages above."
fi

# ---------- 4. copy files ----------
say "Installing files to $APP"
mkdir -p "$APP" "$BIN" "$FONTS" "$CONFIG_DIR" "$AUTOSTART"
rm -rf "$APP/catsprites"
cp -r "$SRC/widgets/." "$APP/"
chmod +x "$APP/start_clock.py"
install -m 755 "$SRC/bin/glassy" "$BIN/glassy"

say "Installing fonts (Anurati, Ubuntu Sans)"
cp "$SRC"/fonts/*.otf "$SRC"/fonts/*.ttf "$SRC"/fonts/*.txt "$FONTS/" 2>/dev/null || true
command -v fc-cache >/dev/null 2>&1 && fc-cache -f "$HOME/.local/share/fonts" >/dev/null 2>&1 || true

if [ ! -f "$CONFIG_DIR/config.ini" ]; then
  cat > "$CONFIG_DIR/config.ini" <<'CFG'
[glassy]
# City used for the weather (any city name wttr.in understands)
city = Delhi
# Text shown under the temperature
label = Delhi, IN
# "auto" fits your screen. Or use a number like 1.0, 1.25, 1.5
scale = auto
CFG
  say "Created config: $CONFIG_DIR/config.ini"
else
  say "Keeping your existing config: $CONFIG_DIR/config.ini"
fi

# ---------- 5. autostart ----------
cat > "$AUTOSTART/glassy.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=glassy
Comment=Glass desktop widgets
Exec=$BIN/glassy boot 5
Terminal=false
X-GNOME-Autostart-enabled=true
DESK
say "Autostart enabled (widgets will load every time you log in)"

# ---------- 6. start now ----------
if [ -n "${DISPLAY:-}" ]; then
  say "Starting the widgets..."
  "$BIN/glassy" restart
else
  warn "No graphical session detected here. Log in to your desktop and the widgets will start."
fi

echo
say "Done! Commands:  glassy start | stop | restart | status"
case ":$PATH:" in
  *":$BIN:"*) ;;
  *) warn "$BIN is not in your PATH yet. Log out and in again, or run: $BIN/glassy status" ;;
esac
if [ -f "$HOME/.conkyrc" ]; then
  warn "You also have ~/.conkyrc. If another Conky clock starts at login, you will see two clocks. Remove the old one."
fi
