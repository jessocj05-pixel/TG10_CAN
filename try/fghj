#!/usr/bin/env python3
"""
EKSMA TG10 Timing Generator Simulator — PySide6 desktop port.

Features (parity with the web version):
  - Internal (100 MHz, fixed) or External (10-100 MHz, user-set) reference clock
  - Output period/frequency, rise delay, fall delay controls
  - Single scope view: CH1 active clock, optional CH1b comparison clock, CH2 output pulse
  - Scroll to zoom, drag to pan, draggable X1/X2 measurement cursors
  - Hardware realization panel: clock-tick quantization + extra fall-path sync cycles
    (models the measured TG10-vs-scope pulse-width gap on external clocks)
  - Live mathematical relations panel

Run:
    pip install PySide6
    python3 tg10_simulator.py
"""
import sys
import math
from dataclasses import dataclass

from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPainterPath, QLinearGradient
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QComboBox, QPushButton, QRadioButton,
    QButtonGroup, QCheckBox, QSlider, QFrame, QScrollArea, QSizePolicy
)

# ----------------------------------------------------------------------------
# Colors (matches the web version's instrument-panel palette)
# ----------------------------------------------------------------------------
BG_SCREEN   = QColor(5, 10, 6)
GRID_LINE   = QColor(18, 48, 22)
GRID_STRONG = QColor(29, 74, 34)
CLK_COLOR   = QColor(51, 255, 176)
OUT_COLOR   = QColor(255, 180, 84)
C1_COLOR    = QColor(90, 217, 255)
C2_COLOR    = QColor(255, 90, 208)
CMP_COLOR   = QColor(180, 140, 255)
TEXT_DIM    = QColor(124, 156, 130)
TEXT_BRIGHT = QColor(214, 255, 228)
AMBER_TEXT  = QColor(255, 207, 138)
PANEL_LABEL = QColor(147, 168, 147)

DIVS = 10  # horizontal scope divisions


def fmt_ns(v: float) -> str:
    av = abs(v)
    if av >= 1e6:
        return f"{v/1e6:.3f} ms"
    if av >= 1e3:
        return f"{v/1e3:.3f} \u00b5s"
    return f"{v:.2f} ns"


def fmt_freq(hz: float) -> str:
    if not math.isfinite(hz):
        return "\u2014"
    a = abs(hz)
    if a >= 1e6:
        return f"{hz/1e6:.4f} MHz"
    if a >= 1e3:
        return f"{hz/1e3:.4f} kHz"
    return f"{hz:.3f} Hz"


def nice_step(span: float) -> float:
    raw = span / 10.0
    if raw <= 0:
        return 1.0
    mag = 10 ** math.floor(math.log10(raw))
    norm = raw / mag
    if norm < 1.5:
        step = 1 * mag
    elif norm < 3.5:
        step = 2 * mag
    elif norm < 7.5:
        step = 5 * mag
    else:
        step = 10 * mag
    return step


def nice_steps_1_2_5(lo=0.5, hi=1e7):
    seq = []
    for mag in range(-1, 8):
        for m in (1, 2, 5):
            v = m * (10 ** mag)
            if lo <= v <= hi:
                seq.append(v)
    return sorted(seq)


STEPS_1_2_5 = nice_steps_1_2_5()


# ----------------------------------------------------------------------------
# State
# ----------------------------------------------------------------------------
@dataclass
class State:
    clock_source: str = "internal"     # 'internal' | 'external'
    ext_clk_freq_mhz: float = 20.0     # 10..100
    compare_mode: bool = False
    quantize: bool = False
    sync_cycles: int = 1

    period: float = 1000.0             # ns
    rise: float = 30.0                 # ns
    fall: float = 230.0                # ns

    center: float = 500.0              # ns, scope view center
    ns_per_div: float = 100.0          # ns per division (timebase)

    cursor1: float = 30.0
    cursor2: float = 230.0

    @property
    def clk_period(self) -> float:
        if self.clock_source == "internal":
            return 10.0
        return 1000.0 / max(self.ext_clk_freq_mhz, 1e-6)

    def window_span(self) -> float:
        return self.ns_per_div * DIVS

    def window_start(self) -> float:
        return self.center - self.window_span() / 2

    def window_end(self) -> float:
        return self.window_start() + self.window_span()

    def other_clock(self):
        """Returns (source_label, freq_mhz, period_ns) of the clock NOT active, for comparison mode."""
        if self.clock_source == "internal":
            return "external", self.ext_clk_freq_mhz, 1000.0 / max(self.ext_clk_freq_mhz, 1e-6)
        return "internal", 100.0, 10.0

    def quantized_edges(self):
        T = self.clk_period
        nR = round(self.rise / T)
        nF = round(self.fall / T)
        extra = self.sync_cycles if self.clock_source == "external" else 0
        nF += extra
        rQ, fQ = nR * T, nF * T
        if fQ <= rQ:
            fQ = rQ + T
        return nR, nF, rQ, fQ, extra


def clock_val(t: float, period: float) -> int:
    m = t % period
    return 1 if m < period / 2 else 0


def output_val(t: float, period: float, rise: float, fall: float) -> int:
    m = t % period
    return 1 if rise <= m < fall else 0


# ----------------------------------------------------------------------------
# Scope widget
# ----------------------------------------------------------------------------
class ScopeWidget(QWidget):
    cursorsChanged = Signal()
    viewChanged = Signal()

    def __init__(self, state: State, parent=None):
        super().__init__(parent)
        self.s = state
        self.setMinimumHeight(420)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self._drag = None  # dict: type, start_x, start_center

    # ---- coordinate helpers ----
    def px_of(self, t_ns: float, w: float) -> float:
        wstart, wend = self.s.window_start(), self.s.window_end()
        return (t_ns - wstart) / (wend - wstart) * w

    def ns_of(self, x_px: float, w: float) -> float:
        wstart, wend = self.s.window_start(), self.s.window_end()
        return wstart + x_px / w * (wend - wstart)

    # ---- mouse interaction ----
    def mousePressEvent(self, ev):
        w = self.width()
        mx, my = ev.position().x(), ev.position().y()
        p1 = self.px_of(self.s.cursor1, w)
        p2 = self.px_of(self.s.cursor2, w)
        near_handle = my < 26
        if near_handle and abs(mx - p1) < 16 and abs(mx - p1) <= abs(mx - p2) + 0.001:
            self._drag = {"type": "c1"}
        elif near_handle and abs(mx - p2) < 16:
            self._drag = {"type": "c2"}
        elif abs(mx - p1) < 7:
            self._drag = {"type": "c1"}
        elif abs(mx - p2) < 7:
            self._drag = {"type": "c2"}
        else:
            self._drag = {"type": "pan", "start_x": ev.position().x(), "start_center": self.s.center}

    def mouseMoveEvent(self, ev):
        if not self._drag:
            return
        w = self.width()
        if self._drag["type"] == "pan":
            dpx = ev.position().x() - self._drag["start_x"]
            dns = dpx / w * self.s.window_span()
            self.s.center = self._drag["start_center"] - dns
            self.viewChanged.emit()
        elif self._drag["type"] == "c1":
            self.s.cursor1 = self.ns_of(ev.position().x(), w)
            self.cursorsChanged.emit()
        elif self._drag["type"] == "c2":
            self.s.cursor2 = self.ns_of(ev.position().x(), w)
            self.cursorsChanged.emit()
        self.update()

    def mouseReleaseEvent(self, ev):
        self._drag = None

    def wheelEvent(self, ev):
        w = self.width()
        mx = ev.position().x()
        pivot_ns = self.ns_of(mx, w)
        factor = 1.15 if ev.angleDelta().y() < 0 else 1 / 1.15
        span = self.s.window_span()
        new_span = min(1e8, max(5.0, span * factor))
        new_start = pivot_ns - (pivot_ns - self.s.window_start()) * (new_span / span)
        self.s.center = new_start + new_span / 2
        self.s.ns_per_div = new_span / DIVS
        self.viewChanged.emit()
        self.update()

    # ---- painting ----
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, BG_SCREEN)

        wstart, wend = self.s.window_start(), self.s.window_end()
        span = wend - wstart

        def px(t):
            return (t - wstart) / span * W

        # grid
        step = nice_step(span)
        font_small = QFont("Monospace", 8)
        p.setFont(font_small)
        fm = QFontMetrics(font_small)
        t0 = math.ceil(wstart / step) * step
        t = t0
        while t <= wend:
            x = px(t)
            strong = (round(t / step) % 5 == 0)
            p.setPen(QPen(GRID_STRONG if strong else GRID_LINE, 1))
            p.drawLine(QPointF(x, 12), QPointF(x, H - 26))
            p.setPen(TEXT_DIM)
            label = fmt_ns(t)
            lx = min(max(x - fm.horizontalAdvance(label) / 2, 2), W - fm.horizontalAdvance(label) - 2)
            p.drawText(QPointF(lx, H - 8), label)
            t += step

        # lane geometry
        if self.s.compare_mode:
            clk_top, clk_h = 26, 70
            cmp_top, cmp_h = 108, 70
            out_top, out_h = 196, 70
        else:
            clk_top, clk_h = 26, 85
            out_top, out_h = 128, 85
            cmp_top = cmp_h = None

        label_font = QFont("Sans Serif", 9)
        p.setFont(label_font)
        p.setPen(PANEL_LABEL)
        active_lbl = ("INTERNAL 100.000 MHz" if self.s.clock_source == "internal"
                      else f"EXTERNAL {self.s.ext_clk_freq_mhz:.3f} MHz")
        p.drawText(QPointF(8, clk_top - 6), f"CH1  ACTIVE CLOCK ({active_lbl})")
        p.drawText(QPointF(8, out_top - 6), "CH2  OUTPUT PULSE")

        def draw_clock_lane(period, top, h, color):
            cycle_px = period / span * W
            if cycle_px >= 8:
                self._draw_digital_trace(p, wstart, wend, W, top, h, lambda t: clock_val(t, period), color, 2.4)
            else:
                p.fillRect(QRectF(0, top, W, h), QColor(color.red(), color.green(), color.blue(), 40))
                pen = QPen(QColor(color.red(), color.green(), color.blue(), 140), 1)
                p.setPen(pen)
                x = 0.0
                while x < W:
                    p.drawLine(QPointF(x, top), QPointF(x, top + h))
                    x += 4
                p.setPen(color)
                p.setFont(font_small)
                p.drawText(QPointF(8, top + h / 2 + 4),
                           f"{1000.0/period:.2f} MHz \u2014 zoom in to resolve individual {fmt_ns(period)} cycles")

        draw_clock_lane(self.s.clk_period, clk_top, clk_h, CLK_COLOR)

        if self.s.compare_mode:
            src, freq_mhz, period = self.s.other_clock()
            p.setPen(PANEL_LABEL)
            p.setFont(label_font)
            other_lbl = f"{'INTERNAL' if src=='internal' else 'EXTERNAL'} {freq_mhz:.3f} MHz"
            p.drawText(QPointF(8, cmp_top - 6), f"CH1b  COMPARISON CLOCK ({other_lbl})")
            draw_clock_lane(period, cmp_top, cmp_h, CMP_COLOR)

        # output pulse: ideal (dashed) + realized (solid) when quantize is on
        if self.s.quantize:
            nR, nF, rQ, fQ, extra = self.s.quantized_edges()
            draw_rise, draw_fall = rQ, fQ
            pen = QPen(QColor(255, 255, 255, 110), 1.4, Qt.DashLine)
            p.setPen(pen)
            self._draw_digital_trace(p, wstart, wend, W, out_top, out_h,
                                      lambda t: output_val(t, self.s.period, self.s.rise, self.s.fall),
                                      None, 1.4, dashed=True)
        else:
            draw_rise, draw_fall = self.s.rise, self.s.fall

        self._draw_digital_trace(p, wstart, wend, W, out_top, out_h,
                                  lambda t: output_val(t, self.s.period, draw_rise, draw_fall),
                                  OUT_COLOR, 2.6)

        if self.s.quantize:
            p.setPen(QColor(255, 255, 255, 170))
            p.setFont(font_small)
            p.drawText(QPointF(8, out_top + out_h + 14),
                       "dashed = programmed (TG10)  \u00b7  solid = realized (scope)")

        # trigger / rise / fall markers per period
        n0 = math.floor(wstart / self.s.period)
        base = n0 * self.s.period
        while base <= wend:
            if wstart <= base <= wend:
                pen = QPen(QColor(255, 255, 255, 90), 1.2, Qt.DashLine)
                p.setPen(pen)
                p.drawLine(QPointF(px(base), 12), QPointF(px(base), H - 26))
                p.setPen(QColor(255, 255, 255, 160))
                p.setFont(font_small)
                p.drawText(QPointF(px(base) + 3, 24), "TRIG")
            self._draw_marker(p, px(base + draw_rise), QColor(244, 247, 242), f"RISE +{fmt_ns(draw_rise)}", H, font_small)
            self._draw_marker(p, px(base + draw_fall), QColor(255, 92, 92), f"FALL +{fmt_ns(draw_fall)}", H, font_small)
            base += self.s.period

        # pulse width bracket
        base = n0 * self.s.period
        while base <= wend:
            rx, fx = px(base + draw_rise), px(base + draw_fall)
            if -50 <= rx <= W + 50 and -50 <= fx <= W + 50 and fx > rx:
                y = out_top + out_h + 26
                p.setPen(QPen(AMBER_TEXT, 1.4))
                p.drawLine(QPointF(rx, y), QPointF(fx, y))
                p.drawLine(QPointF(rx, y - 5), QPointF(rx, y + 5))
                p.drawLine(QPointF(fx, y - 5), QPointF(fx, y + 5))
                label = f"width = {fmt_ns(draw_fall - draw_rise)}"
                fm2 = QFontMetrics(font_small)
                p.setFont(font_small)
                p.drawText(QPointF((rx + fx) / 2 - fm2.horizontalAdvance(label) / 2, y + 16), label)
            base += self.s.period

        # cursors (always on top)
        self._draw_cursor_handle(p, px(self.s.cursor1), C1_COLOR, "X1", H)
        self._draw_cursor_handle(p, px(self.s.cursor2), C2_COLOR, "X2", H)

        p.end()

    def _draw_digital_trace(self, p, wstart, wend, W, top, h, fn, color, width_px, dashed=False):
        N = 1400
        path = QPainterPath()
        prev_v = fn(wstart)

        def y(v):
            return top + (1 - v) * h

        path.moveTo(0, y(prev_v))
        for i in range(1, N + 1):
            t = wstart + (wend - wstart) * i / N
            v = fn(t)
            x = i / N * W
            if v != prev_v:
                path.lineTo(x, y(prev_v))
                path.lineTo(x, y(v))
                prev_v = v
        path.lineTo(W, y(prev_v))
        pen = QPen(color if color else QColor(255, 255, 255, 110), width_px)
        if dashed:
            pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.drawPath(path)

    def _draw_marker(self, p, x, color, label, H, font):
        if x < -80 or x > 1e6:
            return
        pen = QPen(color, 1.2, Qt.DashLine)
        p.setPen(pen)
        p.drawLine(QPointF(x, 12), QPointF(x, H - 26))
        p.setPen(color)
        p.setFont(font)
        p.drawText(QPointF(x + 4, H - 32), label)

    def _draw_cursor_handle(self, p, x, color, label, H):
        path = QPainterPath()
        path.moveTo(x - 8, 2)
        path.lineTo(x + 8, 2)
        path.lineTo(x, 16)
        path.closeSubpath()
        p.fillPath(path, color)
        pen = QPen(color, 1.6, Qt.DashLine)
        p.setPen(pen)
        p.drawLine(QPointF(x, 16), QPointF(x, H - 26))
        p.setPen(QColor(8, 17, 10))
        f = QFont("Monospace", 8, QFont.Bold)
        p.setFont(f)
        p.drawText(QPointF(x - 5, 11), label)


# ----------------------------------------------------------------------------
# Small styled helpers
# ----------------------------------------------------------------------------
def section_title(text):
    lbl = QLabel(text.upper())
    lbl.setStyleSheet("color:#93a893; font-size:10px; letter-spacing:1px; font-weight:600;")
    return lbl


def field_label(text):
    lbl = QLabel(text)
    lbl.setStyleSheet("color:#93a893; font-size:10px; letter-spacing:.5px;")
    return lbl


def panel_frame():
    f = QFrame()
    f.setStyleSheet("""
        QFrame#panel {
            background: #1c201b;
            border: 1px solid #0a0c09;
            border-radius: 8px;
        }
    """)
    f.setObjectName("panel")
    return f


SPINBOX_STYLE = """
QDoubleSpinBox, QSpinBox {
    background: #0a0d0a; border: 1px solid #303830; color: #d6ffe4;
    font-family: monospace; font-size: 12px; padding: 4px 6px; border-radius: 4px;
}
"""
BUTTON_STYLE = """
QPushButton {
    background: #141814; border: 1px solid #2c342c; color: #7c9c82;
    font-size: 10px; padding: 6px 10px; border-radius: 4px; letter-spacing: .5px;
}
QPushButton:hover { color: #d6ffe4; border-color: #2fdf8f; }
QPushButton:pressed { background: rgba(47,223,143,40); color: #2fdf8f; }
"""
CHECK_STYLE = "QCheckBox, QRadioButton { color: #93a893; font-size: 11px; } "


class ReadoutRow(QWidget):
    def __init__(self, label, value="\u2014"):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        self.l = QLabel(label)
        self.l.setStyleSheet("color:#7c9c82; font-family:monospace; font-size:11px;")
        self.v = QLabel(value)
        self.v.setStyleSheet("color:#ffcf8a; font-family:monospace; font-size:12px; font-weight:700;")
        lay.addWidget(self.l)
        lay.addStretch(1)
        lay.addWidget(self.v)

    def set(self, text):
        self.v.setText(text)


# ----------------------------------------------------------------------------
# Main window
# ----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EKSMA TG10 \u00b7 Timing Generator Simulator (PySide6)")
        self.resize(1360, 900)
        self.s = State()

        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet("background:#14160f; color:#d6ffe4; font-family:Sans Serif;")
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(14, 14, 14, 14)

        header = self._build_header()
        root_lay.addWidget(header)

        body = QHBoxLayout()
        root_lay.addLayout(body, 1)

        # ---- left controls column (scrollable) ----
        controls = QWidget()
        controls_lay = QVBoxLayout(controls)
        controls_lay.setSpacing(12)
        controls_lay.addWidget(self._build_clock_panel())
        controls_lay.addWidget(self._build_period_panel())
        controls_lay.addWidget(self._build_edges_panel())
        controls_lay.addWidget(self._build_quantize_panel())
        controls_lay.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        scroll.setFixedWidth(340)
        scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")
        body.addWidget(scroll)

        # ---- right column: scope + cursor bar + math panel ----
        right = QVBoxLayout()
        body.addLayout(right, 1)

        right.addWidget(self._build_toolbar())
        self.scope = ScopeWidget(self.s)
        self.scope.cursorsChanged.connect(self._on_cursors_changed)
        self.scope.viewChanged.connect(self._on_view_changed)
        scope_frame = panel_frame()
        sf_lay = QVBoxLayout(scope_frame)
        sf_lay.addWidget(self.scope)
        right.addWidget(scope_frame, 1)

        right.addWidget(self._build_cursor_bar())
        right.addWidget(self._build_math_panel())

        self._refresh_all()

    # ---------------- header ----------------
    def _build_header(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        title_box = QVBoxLayout()
        t1 = QLabel("TIMING GENERATOR")
        t1.setStyleSheet("font-size:18px; font-weight:800; letter-spacing:2px; color:#d6ffe4;")
        t2 = QLabel("EKSMA \u00b7 TG10 SIMULATOR (PySide6)")
        t2.setStyleSheet("font-size:11px; letter-spacing:2px; color:#2fdf8f; font-family:monospace;")
        title_box.addWidget(t1)
        title_box.addWidget(t2)
        lay.addLayout(title_box)
        lay.addStretch(1)

        self.hdr_clock = QLabel("INTERNAL CLOCK: 100.000 MHz")
        self.hdr_clock.setStyleSheet("color:#33ffb0; font-family:monospace; font-size:12px; font-weight:700;")
        self.hdr_period = QLabel("Reference period Tclk = 10.00 ns")
        self.hdr_period.setStyleSheet("color:#7c9c82; font-family:monospace; font-size:10.5px;")
        hb = QVBoxLayout()
        hb.addWidget(self.hdr_clock, 0, Qt.AlignRight)
        hb.addWidget(self.hdr_period, 0, Qt.AlignRight)
        lay.addLayout(hb)
        return w

    # ---------------- clock source panel ----------------
    def _build_clock_panel(self):
        panel = panel_frame()
        lay = QVBoxLayout(panel)
        lay.addWidget(section_title("Reference Clock Source"))

        self.rb_internal = QRadioButton("Internal (100 MHz, fixed)")
        self.rb_external = QRadioButton("External (user-set)")
        self.rb_internal.setChecked(True)
        self.rb_internal.setStyleSheet(CHECK_STYLE)
        self.rb_external.setStyleSheet(CHECK_STYLE)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_internal)
        grp.addButton(self.rb_external)
        lay.addWidget(self.rb_internal)
        lay.addWidget(self.rb_external)
        self.rb_internal.toggled.connect(self._on_clock_source_changed)

        lay.addWidget(field_label("External Clock Frequency (MHz) \u2014 10 to 100"))
        row = QHBoxLayout()
        self.ext_freq_spin = QDoubleSpinBox()
        self.ext_freq_spin.setRange(10, 100)
        self.ext_freq_spin.setDecimals(2)
        self.ext_freq_spin.setValue(20.0)
        self.ext_freq_spin.setStyleSheet(SPINBOX_STYLE)
        self.ext_freq_slider = QSlider(Qt.Horizontal)
        self.ext_freq_slider.setRange(1000, 10000)  # x100 for 2-decimal precision
        self.ext_freq_slider.setValue(2000)
        row.addWidget(self.ext_freq_spin)
        lay.addLayout(row)
        lay.addWidget(self.ext_freq_slider)
        self.ext_freq_spin.valueChanged.connect(self._on_ext_freq_spin)
        self.ext_freq_slider.valueChanged.connect(self._on_ext_freq_slider)

        self.ro_active_clk = ReadoutRow("Active clock", "INTERNAL \u00b7 100.000 MHz")
        self.ro_active_tclk = ReadoutRow("Active period Tclk", "10.00 ns")
        lay.addWidget(self.ro_active_clk)
        lay.addWidget(self.ro_active_tclk)

        self.cb_compare = QCheckBox("Compare: overlay Internal vs External on scope")
        self.cb_compare.setStyleSheet(CHECK_STYLE)
        self.cb_compare.toggled.connect(self._on_compare_toggled)
        lay.addWidget(self.cb_compare)

        self._set_external_enabled(False)
        return panel

    def _set_external_enabled(self, enabled):
        self.ext_freq_spin.setEnabled(enabled)
        self.ext_freq_slider.setEnabled(enabled)

    # ---------------- output repetition panel ----------------
    def _build_period_panel(self):
        panel = panel_frame()
        lay = QVBoxLayout(panel)
        lay.addWidget(section_title("Output Repetition"))

        lay.addWidget(field_label("Period (ns)"))
        self.period_spin = QDoubleSpinBox()
        self.period_spin.setRange(10, 1e7)
        self.period_spin.setDecimals(2)
        self.period_spin.setValue(1000)
        self.period_spin.setStyleSheet(SPINBOX_STYLE)
        lay.addWidget(self.period_spin)
        self.period_spin.valueChanged.connect(self._on_period_changed)

        lay.addWidget(field_label("Frequency"))
        row = QHBoxLayout()
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.000001, 1e9)
        self.freq_spin.setDecimals(6)
        self.freq_spin.setValue(1.0)
        self.freq_spin.setStyleSheet(SPINBOX_STYLE)
        self.freq_unit = QComboBox()
        self.freq_unit.addItems(["Hz", "kHz", "MHz"])
        self.freq_unit.setCurrentIndex(1)
        self.freq_unit.setStyleSheet(SPINBOX_STYLE)
        row.addWidget(self.freq_spin)
        row.addWidget(self.freq_unit)
        lay.addLayout(row)
        self.freq_spin.valueChanged.connect(self._on_freq_changed)
        self.freq_unit.currentIndexChanged.connect(self._on_freq_changed)

        self.cb_snap = QCheckBox("Lock period to active clock (multiple of Tclk)")
        self.cb_snap.setStyleSheet(CHECK_STYLE)
        self.cb_snap.toggled.connect(lambda: self._set_period(self.s.period))
        lay.addWidget(self.cb_snap)
        return panel

    # ---------------- output edges panel ----------------
    def _build_edges_panel(self):
        panel = panel_frame()
        lay = QVBoxLayout(panel)
        lay.addWidget(section_title("Output Edges"))

        lay.addWidget(field_label("Rise Delay \u2014 tR (ns)"))
        self.rise_spin = QDoubleSpinBox()
        self.rise_spin.setRange(0, 1e7)
        self.rise_spin.setDecimals(2)
        self.rise_spin.setValue(30)
        self.rise_spin.setStyleSheet(SPINBOX_STYLE)
        self.rise_slider = QSlider(Qt.Horizontal)
        self.rise_slider.setRange(0, 1000)
        self.rise_slider.setValue(30)
        lay.addWidget(self.rise_spin)
        lay.addWidget(self.rise_slider)
        self.rise_spin.valueChanged.connect(self._on_rise_spin)
        self.rise_slider.valueChanged.connect(self._on_rise_slider)

        lay.addWidget(field_label("Fall Delay \u2014 tF (ns)"))
        self.fall_spin = QDoubleSpinBox()
        self.fall_spin.setRange(0, 1e7)
        self.fall_spin.setDecimals(2)
        self.fall_spin.setValue(230)
        self.fall_spin.setStyleSheet(SPINBOX_STYLE)
        self.fall_slider = QSlider(Qt.Horizontal)
        self.fall_slider.setRange(0, 1000)
        self.fall_slider.setValue(230)
        lay.addWidget(self.fall_spin)
        lay.addWidget(self.fall_slider)
        self.fall_spin.valueChanged.connect(self._on_fall_spin)
        self.fall_slider.valueChanged.connect(self._on_fall_slider)

        self.ro_width = ReadoutRow("Pulse width", "200.00 ns")
        self.ro_duty = ReadoutRow("Duty cycle", "20.0 %")
        self.ro_cycles = ReadoutRow("Clock cycles / period", "100.00")
        lay.addWidget(self.ro_width)
        lay.addWidget(self.ro_duty)
        lay.addWidget(self.ro_cycles)

        self.warn_label = QLabel("")
        self.warn_label.setWordWrap(True)
        self.warn_label.setStyleSheet("color:#ffb0b0; font-size:10.5px; background:rgba(255,60,60,20); "
                                       "border:1px solid rgba(255,90,90,80); border-radius:5px; padding:6px;")
        self.warn_label.hide()
        lay.addWidget(self.warn_label)
        return panel

    # ---------------- hardware quantization panel ----------------
    def _build_quantize_panel(self):
        panel = panel_frame()
        lay = QVBoxLayout(panel)
        lay.addWidget(section_title("Hardware Realization (Clock Quantization)"))

        self.cb_quantize = QCheckBox("Show realized edges (rounded to active clock ticks)")
        self.cb_quantize.setStyleSheet(CHECK_STYLE)
        self.cb_quantize.toggled.connect(self._on_quantize_toggled)
        lay.addWidget(self.cb_quantize)

        lay.addWidget(field_label("Extra sync cycles on FALL path (N)"))
        row = QHBoxLayout()
        self.sync_spin = QSpinBox()
        self.sync_spin.setRange(0, 6)
        self.sync_spin.setValue(1)
        self.sync_spin.setStyleSheet(SPINBOX_STYLE)
        row.addWidget(self.sync_spin)
        lay.addLayout(row)
        self.sync_slider = QSlider(Qt.Horizontal)
        self.sync_slider.setRange(0, 6)
        self.sync_slider.setValue(1)
        lay.addWidget(self.sync_slider)
        self.sync_spin.valueChanged.connect(self._on_sync_spin)
        self.sync_slider.valueChanged.connect(self._on_sync_slider)

        self.ro_nr = ReadoutRow("N_R = round(tR/Tclk)", "3")
        self.ro_nf = ReadoutRow("N_F = round(tF/Tclk)", "23")
        self.ro_rise_q = ReadoutRow("Realized tR", "30.00 ns")
        self.ro_fall_q = ReadoutRow("Realized tF", "230.00 ns")
        self.ro_width_q = ReadoutRow("Realized width", "200.00 ns")
        self.ro_delta_w = ReadoutRow("\u0394 width (scope \u2212 TG10)", "+0.00 ns")
        for r in (self.ro_nr, self.ro_nf, self.ro_rise_q, self.ro_fall_q, self.ro_width_q, self.ro_delta_w):
            lay.addWidget(r)

        note = QLabel("This is the gap between the TG10-programmed pulse width and the oscilloscope "
                       "reading \u2014 see the \u201cClock Quantization\u201d row in the math panel for the relation.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#5b7a63; font-size:10px;")
        lay.addWidget(note)
        return panel

    # ---------------- scope toolbar ----------------
    def _build_toolbar(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 6)

        tb_box = QVBoxLayout()
        tb_box.addWidget(field_label("Timebase (ns/div)"))
        row = QHBoxLayout()
        self.tb_out = QPushButton("\u2212")
        self.tb_in = QPushButton("+")
        self.tb_out.setFixedWidth(28)
        self.tb_in.setFixedWidth(28)
        self.tb_out.setStyleSheet(BUTTON_STYLE)
        self.tb_in.setStyleSheet(BUTTON_STYLE)
        self.nsdiv_spin = QDoubleSpinBox()
        self.nsdiv_spin.setRange(0.5, 1e7)
        self.nsdiv_spin.setDecimals(3)
        self.nsdiv_spin.setValue(100)
        self.nsdiv_spin.setStyleSheet(SPINBOX_STYLE)
        row.addWidget(self.tb_out)
        row.addWidget(self.nsdiv_spin)
        row.addWidget(self.tb_in)
        tb_box.addLayout(row)
        self.tb_out.clicked.connect(lambda: self._step_timebase(1))
        self.tb_in.clicked.connect(lambda: self._step_timebase(-1))
        self.nsdiv_spin.valueChanged.connect(self._on_nsdiv_changed)
        lay.addLayout(tb_box)

        center_box = QVBoxLayout()
        center_box.addWidget(field_label("Center (ns)"))
        self.center_spin = QDoubleSpinBox()
        self.center_spin.setRange(-1e9, 1e9)
        self.center_spin.setDecimals(2)
        self.center_spin.setValue(500)
        self.center_spin.setStyleSheet(SPINBOX_STYLE)
        center_box.addWidget(self.center_spin)
        self.center_spin.valueChanged.connect(self._on_center_changed)
        lay.addLayout(center_box)

        lay.addStretch(1)
        btn_autoset = QPushButton("Autoset")
        btn_rise = QPushButton("Rise Edge")
        btn_fall = QPushButton("Fall Edge")
        btn_period = QPushButton("Full Period")
        for b in (btn_autoset, btn_rise, btn_fall, btn_period):
            b.setStyleSheet(BUTTON_STYLE)
        btn_autoset.clicked.connect(self._autoset_view)
        btn_rise.clicked.connect(self._zoom_rise)
        btn_fall.clicked.connect(self._zoom_fall)
        btn_period.clicked.connect(self._zoom_period)
        lay.addWidget(btn_autoset)
        lay.addWidget(btn_rise)
        lay.addWidget(btn_fall)
        lay.addWidget(btn_period)
        return w

    # ---------------- cursor bar ----------------
    def _build_cursor_bar(self):
        panel = panel_frame()
        lay = QHBoxLayout(panel)

        def chip(label, color):
            box = QVBoxLayout()
            l = QLabel(label)
            l.setStyleSheet("color:#93a893; font-size:9.5px; letter-spacing:1px;")
            v = QLabel("\u2014")
            v.setStyleSheet(f"color:{color}; font-family:monospace; font-size:14px; font-weight:700;")
            box.addWidget(l)
            box.addWidget(v)
            wrap = QWidget()
            wrap.setLayout(box)
            return wrap, v

        w1, self.cx1_val = chip("X1", "#5ad9ff")
        w2, self.cx2_val = chip("X2", "#ff5ad0")
        w3, self.cdx_val = chip("\u0394X = X2 \u2212 X1", "#d6ffe4")
        w4, self.cfx_val = chip("1 / \u0394X", "#ffcf8a")
        for w in (w1, w2, w3, w4):
            lay.addWidget(w)

        lay.addStretch(1)
        btn_mw = QPushButton("Cursors \u2192 Pulse Width")
        btn_mp = QPushButton("Cursors \u2192 Period")
        btn_mw.setStyleSheet(BUTTON_STYLE)
        btn_mp.setStyleSheet(BUTTON_STYLE)
        btn_mw.clicked.connect(self._cursors_to_width)
        btn_mp.clicked.connect(self._cursors_to_period)
        lay.addWidget(btn_mw)
        lay.addWidget(btn_mp)
        return panel

    # ---------------- math panel ----------------
    MATH_ROW_NAMES = [
        "Reference Clock (Active)",
        "Clock Comparison",
        "Period \u2194 Frequency",
        "Pulse Width",
        "Duty Cycle",
        "Clock Cycles per Period",
        "Rise Edge in Clock Cycles",
        "Fall Edge in Clock Cycles",
        "Output vs. Active Clock Rate",
        "Clock Quantization + Sync Latency (TG10 vs. scope)",
        "Cursor Measurement (X1/X2)",
    ]

    def _build_math_panel(self):
        panel = panel_frame()
        lay = QVBoxLayout(panel)
        lay.addWidget(section_title("Mathematical Relations (live)"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        lay.addLayout(grid)

        self.math_expr_labels = []
        cols = 2
        for i, name in enumerate(self.MATH_ROW_NAMES):
            box = QFrame()
            box.setStyleSheet("background:#0a0d0a; border:1px solid #262b26; border-radius:6px;")
            v = QVBoxLayout(box)
            v.setContentsMargins(10, 8, 10, 8)
            n = QLabel(name.upper())
            n.setStyleSheet("color:#93a893; font-size:9px; letter-spacing:1px;")
            e = QLabel("")
            e.setStyleSheet("color:#d6ffe4; font-family:monospace; font-size:11.5px;")
            e.setWordWrap(True)
            e.setTextFormat(Qt.RichText)
            v.addWidget(n)
            v.addWidget(e)
            grid.addWidget(box, i // cols, i % cols)
            self.math_expr_labels.append(e)
        return panel

    # ============================================================
    # Event handlers
    # ============================================================
    def _on_clock_source_changed(self):
        self.s.clock_source = "internal" if self.rb_internal.isChecked() else "external"
        self._set_external_enabled(self.s.clock_source == "external")
        self._set_period(self.s.period)  # re-applies snap against new Tclk
        self._refresh_all()

    def _on_ext_freq_spin(self, v):
        self.s.ext_clk_freq_mhz = v
        self.ext_freq_slider.blockSignals(True)
        self.ext_freq_slider.setValue(int(round(v * 100)))
        self.ext_freq_slider.blockSignals(False)
        self._set_period(self.s.period)
        self._refresh_all()

    def _on_ext_freq_slider(self, v):
        self.ext_freq_spin.setValue(v / 100.0)

    def _on_compare_toggled(self, checked):
        self.s.compare_mode = checked
        self._refresh_all()

    def _period_to_freq_fields(self, period_ns):
        hz = 1e9 / period_ns
        if hz >= 1e6:
            unit_idx, divisor = 2, 1e6
        elif hz >= 1e3:
            unit_idx, divisor = 1, 1e3
        else:
            unit_idx, divisor = 0, 1
        self.freq_unit.blockSignals(True)
        self.freq_spin.blockSignals(True)
        self.freq_unit.setCurrentIndex(unit_idx)
        self.freq_spin.setValue(hz / divisor)
        self.freq_unit.blockSignals(False)
        self.freq_spin.blockSignals(False)

    def _set_period(self, period_ns, update_freq_fields=True):
        period_ns = max(self.s.clk_period, period_ns)
        if self.cb_snap.isChecked():
            period_ns = max(self.s.clk_period, round(period_ns / self.s.clk_period) * self.s.clk_period)
        self.s.period = period_ns
        self.period_spin.blockSignals(True)
        self.period_spin.setValue(period_ns)
        self.period_spin.blockSignals(False)
        if update_freq_fields:
            self._period_to_freq_fields(period_ns)
        self.rise_slider.setMaximum(int(period_ns))
        self.fall_slider.setMaximum(int(period_ns))
        self._clamp_edges()

    def _on_period_changed(self, v):
        self._set_period(v, update_freq_fields=True)
        self._refresh_all()

    def _on_freq_changed(self, *_):
        unit = [1, 1e3, 1e6][self.freq_unit.currentIndex()]
        hz = max(1e-9, self.freq_spin.value() * unit)
        self._set_period(1e9 / hz, update_freq_fields=False)
        self._refresh_all()

    def _clamp_edges(self):
        r = min(max(self.rise_spin.value(), 0), self.s.period)
        f = min(max(self.fall_spin.value(), 0), self.s.period)
        if f <= r:
            f = min(self.s.period, r + 1)
        self.s.rise, self.s.fall = r, f
        for w, val in ((self.rise_spin, r), (self.fall_spin, f),
                       (self.rise_slider, r), (self.fall_slider, f)):
            w.blockSignals(True)
            w.setValue(val)
            w.blockSignals(False)

    def _on_rise_spin(self, v):
        self.s.rise = min(max(v, 0), self.s.period)
        if self.s.fall <= self.s.rise:
            self.s.fall = min(self.s.period, self.s.rise + 1)
            self.fall_spin.blockSignals(True); self.fall_spin.setValue(self.s.fall); self.fall_spin.blockSignals(False)
        self.rise_slider.blockSignals(True); self.rise_slider.setValue(int(self.s.rise)); self.rise_slider.blockSignals(False)
        self.fall_slider.blockSignals(True); self.fall_slider.setValue(int(self.s.fall)); self.fall_slider.blockSignals(False)
        self._refresh_all()

    def _on_rise_slider(self, v):
        self.rise_spin.setValue(v)

    def _on_fall_spin(self, v):
        self.s.fall = min(max(v, 0), self.s.period)
        if self.s.rise >= self.s.fall:
            self.s.rise = max(0, self.s.fall - 1)
            self.rise_spin.blockSignals(True); self.rise_spin.setValue(self.s.rise); self.rise_spin.blockSignals(False)
        self.rise_slider.blockSignals(True); self.rise_slider.setValue(int(self.s.rise)); self.rise_slider.blockSignals(False)
        self.fall_slider.blockSignals(True); self.fall_slider.setValue(int(self.s.fall)); self.fall_slider.blockSignals(False)
        self._refresh_all()

    def _on_fall_slider(self, v):
        self.fall_spin.setValue(v)

    def _on_quantize_toggled(self, checked):
        self.s.quantize = checked
        self._refresh_all()

    def _on_sync_spin(self, v):
        self.s.sync_cycles = v
        self.sync_slider.blockSignals(True); self.sync_slider.setValue(v); self.sync_slider.blockSignals(False)
        self._refresh_all()

    def _on_sync_slider(self, v):
        self.sync_spin.setValue(v)

    def _step_timebase(self, direction):
        cur = self.s.ns_per_div
        idx = min(range(len(STEPS_1_2_5)), key=lambda i: abs(STEPS_1_2_5[i] - cur))
        idx = min(len(STEPS_1_2_5) - 1, max(0, idx + direction))
        self._set_timebase(STEPS_1_2_5[idx])

    def _set_timebase(self, ns_per_div):
        self.s.ns_per_div = max(0.5, ns_per_div)
        self.nsdiv_spin.blockSignals(True)
        self.nsdiv_spin.setValue(self.s.ns_per_div)
        self.nsdiv_spin.blockSignals(False)
        self._refresh_scope()

    def _on_nsdiv_changed(self, v):
        self._set_timebase(v)

    def _on_center_changed(self, v):
        self.s.center = v
        self._refresh_scope()

    def _set_view(self, center, ns_per_div):
        self.s.center = center
        self.s.ns_per_div = max(0.5, ns_per_div)
        self.center_spin.blockSignals(True); self.center_spin.setValue(center); self.center_spin.blockSignals(False)
        self.nsdiv_spin.blockSignals(True); self.nsdiv_spin.setValue(self.s.ns_per_div); self.nsdiv_spin.blockSignals(False)
        self._refresh_scope()

    def _autoset_view(self):
        span = self.s.period * 2.2
        self._set_view(self.s.period * 0.5, span / DIVS)

    def _zoom_rise(self):
        self._set_view(self.s.rise, (12 * self.s.clk_period) / DIVS)

    def _zoom_fall(self):
        self._set_view(self.s.fall, (12 * self.s.clk_period) / DIVS)

    def _zoom_period(self):
        self._set_view(self.s.period / 2, (self.s.period * 1.1) / DIVS)

    def _cursors_to_width(self):
        self.s.cursor1, self.s.cursor2 = self.s.rise, self.s.fall
        self._refresh_scope()

    def _cursors_to_period(self):
        self.s.cursor1, self.s.cursor2 = 0, self.s.period
        self._refresh_scope()

    def _on_cursors_changed(self):
        self._refresh_cursor_bar()
        self._refresh_math()
        self.scope.update()

    def _on_view_changed(self):
        self.center_spin.blockSignals(True); self.center_spin.setValue(self.s.center); self.center_spin.blockSignals(False)
        self.nsdiv_spin.blockSignals(True); self.nsdiv_spin.setValue(self.s.ns_per_div); self.nsdiv_spin.blockSignals(False)
        self.scope.update()

    # ============================================================
    # Refresh / readouts
    # ============================================================
    def _refresh_all(self):
        self._refresh_header()
        self._refresh_edges_readout()
        self._refresh_quantize_readout()
        self._refresh_cursor_bar()
        self._refresh_math()
        self._refresh_scope()

    def _refresh_scope(self):
        self.scope.update()

    def _refresh_header(self):
        if self.s.clock_source == "internal":
            self.hdr_clock.setText("INTERNAL CLOCK: 100.000 MHz")
        else:
            self.hdr_clock.setText(f"EXTERNAL CLOCK: {self.s.ext_clk_freq_mhz:.3f} MHz")
        self.hdr_period.setText(f"Reference period Tclk = {fmt_ns(self.s.clk_period)}")
        label = ("INTERNAL \u00b7 100.000 MHz" if self.s.clock_source == "internal"
                 else f"EXTERNAL \u00b7 {self.s.ext_clk_freq_mhz:.3f} MHz")
        self.ro_active_clk.set(label)
        self.ro_active_tclk.set(fmt_ns(self.s.clk_period))

    def _refresh_edges_readout(self):
        msg = ""
        if self.s.fall <= self.s.rise:
            msg = "Fall delay must be greater than rise delay."
        if self.s.fall > self.s.period:
            msg = "Fall delay exceeds the output period \u2014 pulse will be clipped/wrapped."
        if msg:
            self.warn_label.setText(msg)
            self.warn_label.show()
        else:
            self.warn_label.hide()

        width = self.s.fall - self.s.rise
        self.ro_width.set(fmt_ns(width))
        self.ro_duty.set(f"{max(0,width)/self.s.period*100:.1f} %")
        self.ro_cycles.set(f"{self.s.period/self.s.clk_period:.2f}")

    def _refresh_quantize_readout(self):
        nR, nF, rQ, fQ, extra = self.s.quantized_edges()
        self.ro_nr.set(str(nR))
        self.ro_nf.set(str(nF))
        self.ro_rise_q.set(fmt_ns(rQ))
        self.ro_fall_q.set(fmt_ns(fQ))
        self.ro_width_q.set(fmt_ns(fQ - rQ))
        delta = (fQ - rQ) - (self.s.fall - self.s.rise)
        self.ro_delta_w.set(f"{'+' if delta>=0 else ''}{fmt_ns(delta)}")

    def _refresh_cursor_bar(self):
        self.cx1_val.setText(fmt_ns(self.s.cursor1))
        self.cx2_val.setText(fmt_ns(self.s.cursor2))
        dx = self.s.cursor2 - self.s.cursor1
        self.cdx_val.setText(fmt_ns(dx))
        self.cfx_val.setText(fmt_freq(abs(1e9 / dx)) if dx != 0 else "\u2014")

    def _refresh_math(self):
        T, R, F = self.s.period, self.s.rise, self.s.fall
        fclk = 1000.0 / self.s.clk_period  # MHz
        f = 1e9 / T
        tau = F - R
        duty = tau / T * 100
        N = T / self.s.clk_period
        nR_cyc = R / self.s.clk_period
        nF_cyc = F / self.s.clk_period
        src_lbl = "Internal" if self.s.clock_source == "internal" else "External"
        ext = self.s.ext_clk_freq_mhz
        dx = self.s.cursor2 - self.s.cursor1
        fdx = 1e9 / dx if dx != 0 else float("inf")
        nR, nF, rQ, fQ, extra = self.s.quantized_edges()
        wQ = fQ - rQ
        dW = wQ - tau

        exprs = [
            f"f_clk = <b>{fclk:.3f} MHz</b> ({src_lbl}) \u2192 T_clk = 1/f_clk = <b>{fmt_ns(self.s.clk_period)}</b>",
            f"Internal = <b>100.000 MHz</b> (10.00 ns) | External = <b>{ext:.3f} MHz</b> "
            f"({fmt_ns(1000/ext)}) \u2192 f_ext/f_int = <b>{ext/100:.3f}</b>",
            f"T = 1/f \u2192 T = <b>{fmt_ns(T)}</b> | f = 1/T = <b>{fmt_freq(f)}</b>",
            f"\u03c4 = tF \u2212 tR = {fmt_ns(F)} \u2212 {fmt_ns(R)} = <b>{fmt_ns(tau)}</b>",
            f"D = \u03c4/T \u00d7 100% = <b>{duty:.2f} %</b>",
            f"N = T/T_clk = {fmt_ns(T)} / {fmt_ns(self.s.clk_period)} = <b>{N:.2f} cycles</b>"
            + ("" if abs(N - round(N)) < 1e-6 else " <i>(not exact \u2014 not fully clock-locked)</i>"),
            f"nR = tR/T_clk = <b>{nR_cyc:.2f}</b> cycles after trigger",
            f"nF = tF/T_clk = <b>{nF_cyc:.2f}</b> cycles after trigger",
            f"f/f_clk = <b>{f/(fclk*1e6):.3e}</b> \u2192 output runs at 1/<b>{(fclk*1e6)/f:.1f}</b> of active clock",
            f"N_R=round(tR/Tclk)=<b>{nR}</b>, N_F=round(tF/Tclk)+N_sync=<b>{nF}</b> (N_sync={extra}) \u2192 "
            f"realized tR=<b>{fmt_ns(rQ)}</b>, tF=<b>{fmt_ns(fQ)}</b>, PW=<b>{fmt_ns(wQ)}</b> \u2192 "
            f"\u0394width = <b>{'+' if dW>=0 else ''}{fmt_ns(dW)}</b> \u2248 N_sync \u00d7 T_clk",
            f"\u0394X = X2 \u2212 X1 = {fmt_ns(self.s.cursor2)} \u2212 {fmt_ns(self.s.cursor1)} = <b>{fmt_ns(dx)}</b> "
            f"| 1/\u0394X = <b>{fmt_freq(abs(fdx))}</b>",
        ]
        for label, text in zip(self.math_expr_labels, exprs):
            label.setText(text)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()