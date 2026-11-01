"""Shared helpers for the glassy widgets: config, screen scale, positioning."""
import configparser
import os
import subprocess

import gi
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk

BASE_W = 1366
BASE_H = 768
MARGIN = 15  # gap from the screen edge, at scale 1.0
CONFIG_PATH = os.path.expanduser("~/.config/glassy/config.ini")

DEFAULTS = {"city": "Delhi", "label": "Delhi, IN", "scale": "auto"}


def load_config():
    cfg = dict(DEFAULTS)
    cp = configparser.ConfigParser()
    try:
        cp.read(CONFIG_PATH)
        if cp.has_section("glassy"):
            for key in DEFAULTS:
                val = cp.get("glassy", key, fallback="").strip()
                if val:
                    cfg[key] = val
    except Exception:
        pass
    return cfg


def get_monitor():
    display = Gdk.Display.get_default()
    return display.get_primary_monitor() or display.get_monitor(0)


def get_scale():
    """Scale factor relative to a 1366x768 screen. Config 'scale' overrides it."""
    cfg = load_config()
    if cfg["scale"].lower() != "auto":
        try:
            return max(0.5, min(4.0, float(cfg["scale"])))
        except ValueError:
            pass
    try:
        geo = get_monitor().get_geometry()
        s = min(geo.height / BASE_H, geo.width / BASE_W)
    except Exception:
        s = 1.0
    return max(0.7, min(2.5, s))


def get_workarea():
    """Usable screen area (x, y, w, h), excluding panels/taskbars."""
    try:
        wa = get_monitor().get_workarea()
        return wa.x, wa.y, wa.width, wa.height
    except Exception:
        return 0, 0, BASE_W, BASE_H - 34


def place(title, x, y, w, h):
    """Move/resize the window with wmctrl (X11 only). Coordinates are logical;
    they are multiplied by the monitor scale factor for HiDPI screens."""
    try:
        sf = get_monitor().get_scale_factor()
    except Exception:
        sf = 1
    geom = "0,%d,%d,%d,%d" % (x * sf, y * sf, w * sf, h * sf)
    try:
        subprocess.run(["wmctrl", "-r", title, "-e", geom],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass
