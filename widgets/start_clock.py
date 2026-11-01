#!/usr/bin/env python3
"""Writes a Conky config scaled to this screen, then starts Conky (the clock)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import get_scale  # noqa: E402

S = get_scale()
CACHE = os.path.expanduser("~/.cache/glassy")
CONF = os.path.join(CACHE, "conkyrc")

TEMPLATE = """conky.config = {
    alignment = "top_middle",
    background = true,
    own_window = true,
    own_window_type = "desktop",
    own_window_transparent = true,
    own_window_argb_visual = true,
    own_window_argb_value = 0,
    own_window_hints = "undecorated,below,sticky,skip_taskbar,skip_pager",
    use_xft = true,
    default_color = "ffffff",
    update_interval = 1.0,
    double_buffer = true,
    minimum_width = %(width)d,
    gap_y = %(gap)d,
};

conky.text = [[
${alignc}${font Anurati:size=%(day)d}${time %%^A}${font}
${alignc}${font Ubuntu Sans:size=%(date)d}${time %%d %%B, %%Y.}${font}
${alignc}${font Ubuntu Sans:size=%(clock)d}- ${time %%I:%%M %%p} -${font}
]];
"""

os.makedirs(CACHE, exist_ok=True)
with open(CONF, "w") as f:
    f.write(TEMPLATE % {
        "width": round(500 * S),
        "gap": round(10 * S),
        "day": round(50 * S),
        "date": round(13 * S),
        "clock": round(16 * S),
    })

os.execvp("conky", ["conky", "-c", CONF])
