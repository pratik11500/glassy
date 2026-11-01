import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Rsvg", "2.0")
from gi.repository import Gtk, Gdk, GLib, Rsvg
import psutil
import cairo
import math
import os
import random
import urllib.parse
import urllib.request
import json

from common import MARGIN, get_scale, get_workarea, load_config, place

HERE = os.path.dirname(os.path.abspath(__file__))
S = get_scale()
CFG = load_config()
TITLE = "GlassyLeft"


def fs(n):
    """Scaled font size for Pango markup."""
    return f"{n * S:.1f}"


def px(n):
    return max(1, int(round(n * S)))


def get_weather():
    try:
        url = "https://wttr.in/" + urllib.parse.quote(CFG["city"]) + "?format=j1"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
            temp = data["current_condition"][0]["temp_C"]
            desc = data["current_condition"][0]["weatherDesc"][0]["value"]
            return f"{temp}C", desc[:15]
    except Exception:
        return "N/A", "Unavailable"


class LeftWidget(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_title(TITLE)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)
        self.stick()
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)
        self.connect("draw", self.on_draw)
        self.win_w = px(110)
        self.win_h = px(380)
        self.set_default_size(self.win_w, self.win_h)
        wa_x, wa_y, wa_w, wa_h = get_workarea()
        self.pos_x = wa_x + px(MARGIN)
        self.pos_y = wa_y + (wa_h - self.win_h) // 2
        self.move(self.pos_x, self.pos_y)
        self.sprites = []
        for i in range(5):
            path = os.path.join(HERE, "catsprites", f"sprite-{i}-symbolic.svg")
            self.sprites.append(Rsvg.Handle.new_from_file(path))
        self.idle = Rsvg.Handle.new_from_file(
            os.path.join(HERE, "catsprites", "sprite-idle-symbolic.svg"))
        self.frame = 0
        self.sleeping = False
        self.sleep_counter = 0
        self.prev_net = psutil.net_io_counters()
        self.dl_speed = 0
        self.ul_speed = 0
        self.weather_temp = "..."
        self.weather_desc = "Loading"
        self.weather_tick = 0
        GLib.timeout_add(100, self.load_weather)
        self.build_ui()
        GLib.timeout_add(150, self.animate_cat)
        GLib.timeout_add(2000, self.update_stats)
        self.show_all()
        GLib.timeout_add(800, self.force_position)

    def load_weather(self):
        self.weather_temp, self.weather_desc = get_weather()
        if hasattr(self, "temp_label"):
            self.temp_label.set_markup(f'<span foreground="white" font="{fs(18)}" weight="bold">{self.weather_temp}</span>')
            self.desc_label.set_markup(f'<span foreground="#aaaaaa" font="{fs(7)}">{self.weather_desc}</span>')
        return False

    def force_position(self):
        place(TITLE, self.pos_x, self.pos_y, self.win_w, self.win_h)
        return False

    def on_draw(self, widget, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

    def draw_glass_bg(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        r = 14 * S
        cr.set_source_rgba(0.08, 0.08, 0.12, 0.78)
        cr.move_to(r, 0)
        cr.line_to(w-r, 0)
        cr.arc(w-r, r, r, -math.pi/2, 0)
        cr.line_to(w, h-r)
        cr.arc(w-r, h-r, r, 0, math.pi/2)
        cr.line_to(r, h)
        cr.arc(r, h-r, r, math.pi/2, math.pi)
        cr.line_to(0, r)
        cr.arc(r, r, r, math.pi, 3*math.pi/2)
        cr.close_path()
        cr.fill()
        cr.set_source_rgba(1, 1, 1, 0.08)
        cr.set_line_width(1)
        cr.move_to(r, 0)
        cr.line_to(w-r, 0)
        cr.arc(w-r, r, r, -math.pi/2, 0)
        cr.line_to(w, h-r)
        cr.arc(w-r, h-r, r, 0, math.pi/2)
        cr.line_to(r, h)
        cr.arc(r, h-r, r, math.pi/2, math.pi)
        cr.line_to(0, r)
        cr.arc(r, r, r, math.pi, 3*math.pi/2)
        cr.close_path()
        cr.stroke()

    def draw_cat(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        sprite = self.idle if self.sleeping else self.sprites[self.frame % 5]
        dim = sprite.get_dimensions()
        scale = min(w / dim.width, h / dim.height) * 0.9
        tx = (w - dim.width * scale) / 2
        ty = (h - dim.height * scale) / 2
        cr.save()
        cr.translate(tx, ty)
        cr.scale(scale, scale)
        cr.set_source_rgba(1, 1, 1, 1)
        sprite.render_cairo(cr)
        cr.restore()

    def fmt(self, b):
        if b > 1024*1024:
            return f"{b/1024/1024:.1f}MB"
        elif b > 1024:
            return f"{b/1024:.1f}KB"
        return f"{int(b)}B"

    def get_uptime(self):
        with open("/proc/uptime") as f:
            secs = int(float(f.read().split()[0]))
        h, m = divmod(secs // 60, 60)
        d, h = divmod(h, 24)
        if d > 0:
            return f"{d}d {h}h {m}m"
        return f"{h}h {m}m"

    def build_ui(self):
        overlay = Gtk.Overlay()
        bg = Gtk.DrawingArea()
        bg.connect("draw", self.draw_glass_bg)
        overlay.add(bg)
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(4))
        main.set_margin_top(px(10))
        main.set_margin_bottom(px(10))
        main.set_margin_start(px(8))
        main.set_margin_end(px(8))
        overlay.add_overlay(main)
        self.add(overlay)

        # Cat
        self.cat_area = Gtk.DrawingArea()
        self.cat_area.set_size_request(px(94), px(90))
        self.cat_area.connect("draw", self.draw_cat)
        main.pack_start(self.cat_area, False, False, 0)

        sep1 = Gtk.Separator()
        main.pack_start(sep1, False, False, px(2))

        # Network
        net_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(3))
        net_box.set_halign(Gtk.Align.CENTER)
        ntitle = Gtk.Label()
        ntitle.set_markup(f'<span foreground="#00ccff" font="{fs(8)}" weight="bold">NETWORK</span>')
        net_box.pack_start(ntitle, False, False, 0)
        self.dl_label = Gtk.Label()
        self.dl_label.set_markup(f'<span foreground="#00ff99" font="{fs(9)}">DL: 0B/s</span>')
        net_box.pack_start(self.dl_label, False, False, 0)
        self.ul_label = Gtk.Label()
        self.ul_label.set_markup(f'<span foreground="#ff9900" font="{fs(9)}">UL: 0B/s</span>')
        net_box.pack_start(self.ul_label, False, False, 0)
        main.pack_start(net_box, False, False, px(4))

        sep2 = Gtk.Separator()
        main.pack_start(sep2, False, False, px(2))

        # Weather
        weather_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        weather_box.set_halign(Gtk.Align.CENTER)
        wtitle = Gtk.Label()
        wtitle.set_markup(f'<span foreground="#00ccff" font="{fs(8)}" weight="bold">WEATHER</span>')
        weather_box.pack_start(wtitle, False, False, px(2))
        wicon = Gtk.Label()
        wicon.set_markup(f'<span font="{fs(20)}">🌤</span>')
        weather_box.pack_start(wicon, False, False, 0)
        self.temp_label = Gtk.Label()
        self.temp_label.set_markup(f'<span foreground="white" font="{fs(18)}" weight="bold">...</span>')
        weather_box.pack_start(self.temp_label, False, False, 0)
        self.desc_label = Gtk.Label()
        self.desc_label.set_markup(f'<span foreground="#aaaaaa" font="{fs(7)}">Loading</span>')
        self.desc_label.set_line_wrap(True)
        self.desc_label.set_justify(Gtk.Justification.CENTER)
        weather_box.pack_start(self.desc_label, False, False, 0)
        loc = Gtk.Label()
        loc.set_markup(f'<span foreground="#666666" font="{fs(7)}">{GLib.markup_escape_text(CFG["label"])}</span>')
        weather_box.pack_start(loc, False, False, 0)
        main.pack_start(weather_box, True, True, 0)

        sep3 = Gtk.Separator()
        main.pack_start(sep3, False, False, px(2))

        # Uptime
        uptime_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(2))
        uptime_box.set_halign(Gtk.Align.CENTER)
        utitle = Gtk.Label()
        utitle.set_markup(f'<span foreground="#00ccff" font="{fs(8)}" weight="bold">UPTIME</span>')
        uptime_box.pack_start(utitle, False, False, 0)
        self.uptime_label = Gtk.Label()
        self.uptime_label.set_markup(f'<span foreground="white" font="{fs(9)}">...</span>')
        uptime_box.pack_start(self.uptime_label, False, False, 0)
        main.pack_start(uptime_box, False, False, px(4))

    def animate_cat(self):
        if self.sleeping:
            self.sleep_counter -= 1
            if self.sleep_counter <= 0:
                self.sleeping = False
        else:
            self.frame = (self.frame + 1) % 5
            if random.randint(1, 100) <= 2:
                self.sleeping = True
                self.sleep_counter = random.randint(5, 15)
        self.cat_area.queue_draw()
        return True

    def update_stats(self):
        curr = psutil.net_io_counters()
        self.dl_speed = (curr.bytes_recv - self.prev_net.bytes_recv) / 2
        self.ul_speed = (curr.bytes_sent - self.prev_net.bytes_sent) / 2
        self.prev_net = curr
        self.dl_label.set_markup(f'<span foreground="#00ff99" font="{fs(9)}">DL: {self.fmt(self.dl_speed)}/s</span>')
        self.ul_label.set_markup(f'<span foreground="#ff9900" font="{fs(9)}">UL: {self.fmt(self.ul_speed)}/s</span>')
        self.uptime_label.set_markup(f'<span foreground="white" font="{fs(9)}">{self.get_uptime()}</span>')
        self.weather_tick += 1
        if self.weather_tick >= 150:
            self.weather_tick = 0
            GLib.timeout_add(100, self.load_weather)
        return True


if __name__ == "__main__":
    w = LeftWidget()
    Gtk.main()
