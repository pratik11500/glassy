import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import psutil
import cairo
import math

from common import MARGIN, get_scale, get_workarea, place

S = get_scale()
TITLE = "GlassyRight"
RED = (1.0, 0.27, 0.4)
GREEN = (0.0, 1.0, 0.6)
VIOLET = (0.66, 0.47, 1.0)


def px(n):
    return max(1, int(round(n * S)))


def get_battery():
    """Returns (percent, plugged) or None when the machine has no battery (PC)."""
    try:
        b = psutil.sensors_battery()
    except Exception:
        return None
    if b is None:
        return None
    return int(b.percent), bool(b.power_plugged)


def draw_plug(cr, x, y, u):
    """Small white power-plug icon centred on (x, y); u is the unit size."""
    cr.set_source_rgba(1, 1, 1, 1)
    # two prongs
    for dx in (-3.2, 3.2):
        cr.rectangle(x + dx * u - 1.2 * u, y - 9 * u, 2.4 * u, 6.2 * u)
    cr.fill()
    # body (rounded rectangle)
    left, right, top, bottom, r = x - 6.5 * u, x + 6.5 * u, y - 3.2 * u, y + 4 * u, 2 * u
    cr.new_sub_path()
    cr.arc(right - r, top + r, r, -math.pi / 2, 0)
    cr.arc(right - r, bottom - r, r, 0, math.pi / 2)
    cr.arc(left + r, bottom - r, r, math.pi / 2, math.pi)
    cr.arc(left + r, top + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()
    cr.fill()
    # cord
    cr.set_line_width(2.4 * u)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.move_to(x, y + 4 * u)
    cr.line_to(x, y + 9 * u)
    cr.stroke()
    cr.set_line_cap(cairo.LINE_CAP_BUTT)


class GlassWidget(Gtk.Window):
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
        self.win_w = px(90)
        self.win_h = px(380)
        self.set_default_size(self.win_w, self.win_h)
        wa_x, wa_y, wa_w, wa_h = get_workarea()
        self.pos_x = wa_x + wa_w - self.win_w - px(MARGIN)
        self.pos_y = wa_y + (wa_h - self.win_h) // 2
        self.move(self.pos_x, self.pos_y)
        self.build_ui()
        GLib.timeout_add(2000, self.update)
        self.show_all()
        GLib.timeout_add(800, self.force_position)

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

    def build_ui(self):
        overlay = Gtk.Overlay()
        bg = Gtk.DrawingArea()
        bg.connect("draw", self.draw_glass_bg)
        overlay.add(bg)
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(8))
        main.set_margin_top(px(12))
        main.set_margin_bottom(px(12))
        main.set_margin_start(px(8))
        main.set_margin_end(px(8))
        main.set_halign(Gtk.Align.CENTER)
        overlay.add_overlay(main)
        self.add(overlay)
        self.ring_area = Gtk.DrawingArea()
        self.ring_area.set_size_request(px(74), px(360))
        self.ring_area.connect("draw", self.draw_rings)
        main.pack_start(self.ring_area, False, False, 0)

    def draw_rings(self, widget, cr):
        w = widget.get_allocated_width()
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cpu = int(psutil.cpu_percent())
        ram = int(psutil.virtual_memory().percent)
        disk = int(psutil.disk_usage("/").percent)
        batt = get_battery()
        cx = w // 2
        if batt is None:
            # Desktop PC: no battery, so show a "plugged in" ring
            last = (cx, px(315), 100, GREEN, "AC", True)
        else:
            pct, plugged = batt
            label = "CHG" if (plugged and pct < 100) else "BAT"
            last = (cx, px(315), pct, GREEN if plugged else RED, label, False)
        items = [
            (cx, px(45),  cpu,  (0.0, 0.8, 1.0),  "CPU", False),
            (cx, px(135), ram,  VIOLET,  "RAM", False),
            (cx, px(225), disk, (1.0, 0.6, 0.0),  "DISK", False),
            last,
        ]
        for x, y, val, color, label, is_plug in items:
            r = 28 * S
            cr.set_source_rgba(0.2, 0.2, 0.2, 0.8)
            cr.set_line_width(7 * S)
            cr.new_path()
            cr.arc(x, y, r, 0, 2*math.pi)
            cr.stroke()
            cr.set_source_rgba(*color, 1.0)
            cr.set_line_width(7 * S)
            if val > 0:
                cr.new_path()
                if val >= 100:
                    cr.arc(x, y, r, 0, 2*math.pi)
                else:
                    cr.arc(x, y, r, -math.pi/2, -math.pi/2 + (2*math.pi*val/100))
                cr.stroke()
            if is_plug:
                draw_plug(cr, x, y, 1.15 * S)
            else:
                cr.set_source_rgba(1, 1, 1, 1)
                cr.select_font_face("Ubuntu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                cr.set_font_size(9 * S)
                text = f"{val}%"
                ext = cr.text_extents(text)
                cr.move_to(x - ext[2]/2 - ext[0], y - ext[3]/2 - ext[1])
                cr.show_text(text)
            cr.set_source_rgba(0.6, 0.6, 0.6, 1)
            cr.select_font_face("Ubuntu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(8 * S)
            ext = cr.text_extents(label)
            cr.move_to(x - ext[2]/2 - ext[0], y + r + 13 * S)
            cr.show_text(label)

    def update(self):
        self.ring_area.queue_draw()
        return True


if __name__ == "__main__":
    w = GlassWidget()
    Gtk.main()
