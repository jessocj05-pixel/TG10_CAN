#!/usr/bin/env python3
"""
C-DAC TG10 Timing Generator - GUI reference skeleton (PySide6)

Matches the layout of the supplied screenshot:
  Header: logo/title, status badge, COM/DELAY/PRESETS, RUN
  Tabs:   Dashboard, Sync, Freq/Period, Config 1/2, Delay presets,
          Output, Monitor, Other, Preset manager
  Dashboard: 3 columns
    col1: Synchronization (Sync) card, Output card
    col2: Frequency / Period card, Configuration 1/2 card
    col3: Monitor card (status + per-channel table + live params)
  Footer: status bar

This is UI STRUCTURE ONLY. Every place you'd plug in the simulator engine
(the State/clock-math code from tg10_simulator.py) is marked with "# TODO".
Wire those to a backend object (real serial link or the simulator State)
behind a common interface so the GUI doesn't care which one is live.
"""
import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox, QPushButton, QRadioButton,
    QButtonGroup, QCheckBox, QFrame, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QStatusBar, QSizePolicy, QScrollArea
)

# ----------------------------------------------------------------------------
# Palette (light, clinical / instrument-control look from the screenshot)
# ----------------------------------------------------------------------------
BLUE        = "#1f5fc4"
BLUE_DARK   = "#163d82"
BORDER      = "#d9dee5"
BG_PAGE     = "#f3f5f7"
BG_CARD     = "#ffffff"
TEXT_MAIN   = "#1a2430"
TEXT_DIM    = "#6b7684"
GREEN       = "#1aa34a"
RED         = "#d23b3b"

QSS = f"""
QMainWindow {{ background: {BG_PAGE}; }}
QWidget {{ color: {TEXT_MAIN}; font-family: 'Segoe UI', sans-serif; font-size: 12px; }}

/* cards */
QFrame#card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}
QLabel#cardTitle {{
    color: {BLUE_DARK};
    font-size: 13px;
    font-weight: 700;
}}

/* tabs */
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{
    background: {BG_PAGE};
    padding: 8px 16px;
    border: 1px solid {BORDER};
    border-bottom: none;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {BLUE};
    color: white;
    font-weight: 600;
}}

/* inputs */
QLineEdit, QDoubleSpinBox, QComboBox {{
    background: white; border: 1px solid {BORDER}; border-radius: 4px;
    padding: 4px 6px; min-height: 20px;
}}
QLineEdit:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
    background: #eef0f2; color: {TEXT_DIM};
}}
QPushButton {{
    background: white; border: 1px solid {BORDER}; border-radius: 4px;
    padding: 6px 14px; font-weight: 600;
}}
QPushButton:hover {{ border-color: {BLUE}; color: {BLUE}; }}

QPushButton#runBtn {{
    background: {GREEN}; color: white; border: none; font-weight: 700;
}}
QPushButton#runBtn:hover {{ background: #159142; }}

QLabel#statusBadge {{
    border: 1px solid {BORDER}; border-radius: 4px; padding: 6px 14px;
    font-weight: 700;
}}

QTableWidget {{
    background: white; border: 1px solid {BORDER}; gridline-color: {BORDER};
}}
QHeaderView::section {{
    background: {BG_PAGE}; color: {BLUE_DARK}; font-weight: 700;
    border: none; border-bottom: 1px solid {BORDER}; padding: 6px;
}}
"""


# ----------------------------------------------------------------------------
# Reusable "Card" container: icon + title + optional Set button + body
# ----------------------------------------------------------------------------
class Card(QFrame):
    setClicked = Signal()

    def __init__(self, title, icon="\u25b6", with_set_button=True, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 14)
        outer.setSpacing(10)

        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"color:{BLUE};")
        title_lbl = QLabel(title)
        title_lbl.setObjectName("cardTitle")
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch(1)
        if with_set_button:
            self.set_btn = QPushButton("Set")
            self.set_btn.clicked.connect(self.setClicked.emit)
            header.addWidget(self.set_btn)
        outer.addLayout(header)

        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        outer.addLayout(self.body)

    def add(self, widget_or_layout):
        if isinstance(widget_or_layout, QWidget):
            self.body.addWidget(widget_or_layout)
        else:
            self.body.addLayout(widget_or_layout)


def value_with_unit(value_text, unit_text, decimals=6, enabled=True):
    """A QDoubleSpinBox-ish numeric field + unit combo, matching the
    '100.000  MHz' style fields in the screenshot."""
    row = QHBoxLayout()
    spin = QDoubleSpinBox()
    spin.setDecimals(decimals)
    spin.setRange(0, 1e9)
    spin.setValue(float(value_text))
    spin.setEnabled(enabled)
    unit = QComboBox()
    unit.addItem(unit_text)
    unit.setEnabled(enabled)
    row.addWidget(spin, 1)
    row.addWidget(unit)
    return row, spin, unit


def labeled_field_row(label_text, value_text, unit_text, decimals=6, enabled=True):
    row = QHBoxLayout()
    lbl = QLabel(label_text)
    lbl.setMinimumWidth(90)
    row.addWidget(lbl)
    field_row, spin, unit = value_with_unit(value_text, unit_text, decimals, enabled)
    row.addLayout(field_row, 1)
    return row, spin, unit


# ----------------------------------------------------------------------------
# Dashboard: Synchronization (Sync) card
# ----------------------------------------------------------------------------
class SyncCard(Card):
    def __init__(self, parent=None):
        super().__init__("Synchronization (Sync)", icon="\u21ba", parent=parent)

        # ---- Internal Clock ----
        row = QHBoxLayout()
        self.rb_internal = QRadioButton("Internal Clock")
        self.rb_internal.setChecked(True)
        row.addWidget(self.rb_internal)
        internal_row, self.internal_freq, _ = value_with_unit("100.000", "MHz", decimals=3)
        row.addLayout(internal_row, 1)
        self.add(row)
        # TODO: self.internal_freq is fixed at 100 MHz on real hardware (read-only);
        #       in the simulator this maps to State.clock_source = 'internal'.

        divider1 = QFrame(); divider1.setFrameShape(QFrame.HLine); divider1.setStyleSheet(f"color:{BORDER};")
        self.add(divider1)

        # ---- External SINGLE IN ----
        self.rb_ext_single = QRadioButton("External\nSINGLE IN")
        self.add(self.rb_ext_single)
        sub = QHBoxLayout()
        self.rb_sync_in = QRadioButton("SYNC IN")
        self.rb_clk_in = QRadioButton("CLK IN")
        sub.addWidget(self.rb_sync_in)
        sub.addWidget(self.rb_clk_in)
        self.add(sub)
        rate_row, self.single_rate, _ = labeled_field_row("Rate", "10.000000", "MHz", enabled=False)
        self.add(rate_row)
        # TODO: maps to State.clock_source='external', State.ext_clk_freq_mhz = rate value
        #       (clamp 10-100 MHz per your simulator's validated range).

        divider2 = QFrame(); divider2.setFrameShape(QFrame.HLine); divider2.setStyleSheet(f"color:{BORDER};")
        self.add(divider2)

        # ---- External DUAL IN ----
        self.rb_ext_dual = QRadioButton("External\nDUAL IN")
        self.add(self.rb_ext_dual)
        sync_row, self.dual_sync_in, _ = labeled_field_row("SYNC IN", "1.000000", "MHz", enabled=False)
        clk_row, self.dual_clk_in, _ = labeled_field_row("CLK IN", "99.990000", "MHz", enabled=False)
        self.add(sync_row)
        self.add(clk_row)
        # TODO: dual-clock mode isn't modeled in the current simulator State
        #       (it only has one active clock). If you need it: add a second
        #       "sync" reference separate from the timing clk_period.

        divider3 = QFrame(); divider3.setFrameShape(QFrame.HLine); divider3.setStyleSheet(f"color:{BORDER};")
        self.add(divider3)

        # ---- One shot trigger ----
        oneshot_row = QHBoxLayout()
        self.rb_oneshot = QRadioButton("One shot trigger")
        self.rb_sw = QRadioButton("Software")
        self.rb_smart = QRadioButton("Smart")
        oneshot_row.addWidget(self.rb_oneshot)
        oneshot_row.addWidget(self.rb_sw)
        oneshot_row.addWidget(self.rb_smart)
        self.add(oneshot_row)
        # TODO: one-shot/trigger mode = a run-once gate around the simulator's
        #       periodic output_val(); not periodic like State.period normally is.

        # group all the top-level source radios together (exclusive choice)
        self.source_group = QButtonGroup(self)
        for rb in (self.rb_internal, self.rb_ext_single, self.rb_ext_dual, self.rb_oneshot):
            self.source_group.addButton(rb)
        self.source_group.buttonToggled.connect(self._on_source_changed)
        self._on_source_changed()

    def _on_source_changed(self, *_):
        self.single_rate.setEnabled(self.rb_ext_single.isChecked())
        self.rb_sync_in.setEnabled(self.rb_ext_single.isChecked())
        self.rb_clk_in.setEnabled(self.rb_ext_single.isChecked())
        self.dual_sync_in.setEnabled(self.rb_ext_dual.isChecked())
        self.dual_clk_in.setEnabled(self.rb_ext_dual.isChecked())
        self.rb_sw.setEnabled(self.rb_oneshot.isChecked())
        self.rb_smart.setEnabled(self.rb_oneshot.isChecked())


# ----------------------------------------------------------------------------
# Dashboard: Output card (per-channel rise/fall condition + pulse width)
# ----------------------------------------------------------------------------
class OutputCard(Card):
    def __init__(self, parent=None):
        super().__init__("Output", icon="\u25a3", parent=parent)

        top = QHBoxLayout()
        top.addWidget(QLabel("Channel:"))
        self.channel = QComboBox()
        self.channel.addItems([f"OUT{i}" for i in range(8)])
        top.addWidget(self.channel)
        top.addSpacing(16)
        top.addWidget(QLabel("Logic:"))
        self.logic = QLineEdit("NA")
        self.logic.setEnabled(False)
        self.logic.setMaximumWidth(60)
        top.addWidget(self.logic)
        top.addStretch(1)
        self.add(top)
        # TODO: self.channel.currentText() selects which output's Config1/2
        #       rise/fall/pulse-width fields below are being edited. In the
        #       simulator this is State.rise / State.fall per channel.

        cfg_row = QHBoxLayout()
        cfg_row.addWidget(self._build_config_box("Config 1", "DEL0", "DEL1", "25.64"))
        cfg_row.addWidget(self._build_config_box("Config 2", "DEL2", "DEL3", "25.64"))
        self.add(cfg_row)

    def _build_config_box(self, title, rise_default, fall_default, pw_default):
        box = QFrame()
        v = QVBoxLayout(box)
        t = QLabel(title)
        t.setStyleSheet("font-weight:700;")
        v.addWidget(t)

        rise_row = QHBoxLayout()
        rise_row.addWidget(QLabel("Rise condition"))
        rise_field = QLineEdit(rise_default)
        rise_row.addWidget(rise_field)
        v.addLayout(rise_row)

        fall_row = QHBoxLayout()
        fall_row.addWidget(QLabel("Fall condition"))
        fall_field = QLineEdit(fall_default)
        fall_row.addWidget(fall_field)
        v.addLayout(fall_row)

        pw_row = QHBoxLayout()
        pw_row.addWidget(QLabel("Pulse width"))
        pw_spin = QDoubleSpinBox()
        pw_spin.setDecimals(2)
        pw_spin.setRange(0, 1e9)
        pw_spin.setValue(float(pw_default))
        pw_unit = QComboBox()
        pw_unit.addItems(["ps", "ns", "\u00b5s"])
        pw_row.addWidget(pw_spin, 1)
        pw_row.addWidget(pw_unit)
        v.addLayout(pw_row)
        # TODO: "Rise condition"/"Fall condition" (DEL0..DEL3) are named delay-line
        #       sources on real hardware, not raw ns values -- on the simulator
        #       side the nearest equivalent is State.rise / State.fall (ns),
        #       and pulse width is State.fall - State.rise. You'll likely want
        #       a lookup table mapping DELn -> an actual ns offset.

        return box


# ----------------------------------------------------------------------------
# Dashboard: Frequency / Period card
# ----------------------------------------------------------------------------
class FreqPeriodCard(Card):
    def __init__(self, parent=None):
        super().__init__("Frequency / Period (Freq)", icon="\u21ba", parent=parent)

        mode_row = QHBoxLayout()
        self.rb_freq = QRadioButton("Frequency")
        self.rb_period = QRadioButton("Period")
        self.rb_freq.setChecked(True)
        mode_row.addWidget(self.rb_freq)
        mode_row.addWidget(self.rb_period)
        mode_row.addStretch(1)
        self.add(mode_row)

        freq_row, self.freq_spin, self.freq_unit = labeled_field_row("Frequency", "1.00000000", "MHz")
        self.add(freq_row)

        period_row, self.period_spin, self.period_unit = labeled_field_row("Period", "1.00000000", "\u00b5s", enabled=False)
        self.add(period_row)

        self.rb_freq.toggled.connect(self._on_mode_changed)
        self._on_mode_changed()
        # TODO: this is exactly State.period / State._on_freq_changed /
        #       State._period_to_freq_fields from tg10_simulator.py -- same
        #       bidirectional T=1/f link, just reskinned to this field layout.

    def _on_mode_changed(self):
        self.freq_spin.setEnabled(self.rb_freq.isChecked())
        self.freq_unit.setEnabled(self.rb_freq.isChecked())
        self.period_spin.setEnabled(self.rb_period.isChecked())
        self.period_unit.setEnabled(self.rb_period.isChecked())


# ----------------------------------------------------------------------------
# Dashboard: Configuration 1/2 card (mode select: Normal / Gate / Burst / Divider)
# ----------------------------------------------------------------------------
class ConfigCard(Card):
    def __init__(self, parent=None):
        super().__init__("Configuration 1 / 2", icon="\u2699", parent=parent)

        self.rb_normal = QCheckBox("Normal")
        self.rb_normal.setChecked(True)
        self.add(self.rb_normal)

        divider1 = QFrame(); divider1.setFrameShape(QFrame.HLine); divider1.setStyleSheet(f"color:{BORDER};")
        self.add(divider1)

        gate_row = QHBoxLayout()
        self.rb_gate_mode = QRadioButton("Gate")
        self.rb_gate = QRadioButton("GATE")
        self.rb_ngate = QRadioButton("nGATE")
        gate_row.addWidget(self.rb_gate_mode)
        gate_row.addWidget(self.rb_gate)
        gate_row.addWidget(self.rb_ngate)
        self.add(gate_row)

        divider2 = QFrame(); divider2.setFrameShape(QFrame.HLine); divider2.setStyleSheet(f"color:{BORDER};")
        self.add(divider2)

        self.rb_burst = QRadioButton("Burst")
        self.add(self.rb_burst)
        burst_row = QHBoxLayout()
        burst_trig_box = QVBoxLayout()
        burst_trig_box.addWidget(QLabel("Burst trigger"))
        bt_row1 = QHBoxLayout()
        self.rb_bt_sync = QRadioButton("SYNC IN")
        self.rb_bt_gate = QRadioButton("GATE")
        bt_row1.addWidget(self.rb_bt_sync)
        bt_row1.addWidget(self.rb_bt_gate)
        burst_trig_box.addLayout(bt_row1)
        bt_row2 = QHBoxLayout()
        self.rb_bt_ngate = QRadioButton("nGATE")
        self.rb_bt_sw = QRadioButton("Software")
        bt_row2.addWidget(self.rb_bt_ngate)
        bt_row2.addWidget(self.rb_bt_sw)
        burst_trig_box.addLayout(bt_row2)
        burst_row.addLayout(burst_trig_box, 1)

        count_box = QVBoxLayout()
        count_box.addWidget(QLabel("Burst count"))
        self.burst_count = QDoubleSpinBox()
        self.burst_count.setDecimals(0)
        self.burst_count.setRange(1, 1e6)
        self.burst_count.setValue(1)
        count_box.addWidget(self.burst_count)
        burst_row.addLayout(count_box)
        self.add(burst_row)

        divider3 = QFrame(); divider3.setFrameShape(QFrame.HLine); divider3.setStyleSheet(f"color:{BORDER};")
        self.add(divider3)

        self.rb_divider = QRadioButton("Frequency divider")
        self.add(self.rb_divider)
        div_row = QHBoxLayout()
        div_row.addWidget(QLabel("Division of Freq"))
        self.div_value = QDoubleSpinBox()
        self.div_value.setDecimals(0)
        self.div_value.setRange(1, 1e6)
        self.div_value.setValue(1)
        div_row.addWidget(self.div_value)
        self.add(div_row)
        # TODO: none of Gate/Burst/Divider modes exist in the current
        #       simulator engine (it's free-running periodic only). To model:
        #       Gate -> output_val() gated by an extra enable signal
        #       Burst -> only emit N periods after trigger, then hold low
        #       Divider -> output State.period = N * (1/active_clk_freq)

        mode_group = QButtonGroup(self)
        for rb in (self.rb_gate_mode, self.rb_burst, self.rb_divider):
            mode_group.addButton(rb)


# ----------------------------------------------------------------------------
# Dashboard: Monitor card (status + per-channel delay table + live params)
# ----------------------------------------------------------------------------
class MonitorCard(Card):
    def __init__(self, parent=None):
        super().__init__("Monitor", icon="\u23f8", parent=parent)
        self.set_btn.setText("Refresh")

        stat_grid = QGridLayout()
        self.lbl_sync = self._stat_pair(stat_grid, 0, 0, "Sync")
        self.lbl_config = self._stat_pair(stat_grid, 0, 1, "Config")
        self.lbl_freq = self._stat_pair(stat_grid, 1, 0, "Frequency")
        self.lbl_period = self._stat_pair(stat_grid, 1, 1, "Period")
        self.add(stat_grid)

        dev_row = QHBoxLayout()
        dev_row.addWidget(QLabel("Device Status"))
        self.device_status = QLabel("OFF")
        self.device_status.setStyleSheet(f"color:{RED}; font-weight:700;")
        dev_row.addWidget(self.device_status)
        dev_row.addStretch(1)
        self.add(dev_row)

        self.table = QTableWidget(8, 6)
        self.table.setHorizontalHeaderLabels(
            ["Output", "Config1\nRise delay", "Fall delay", "Config2\nRise delay", "Fall delay", "Logic out"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        for i in range(8):
            self.table.setItem(i, 0, QTableWidgetItem(f"OUT{i}"))
            for c in range(1, 6):
                self.table.setItem(i, c, QTableWidgetItem("--"))
        self.add(self.table)
        # TODO: populate this table from your State per output channel each
        #       time the simulator recomputes (mirrors ScopeWidget's readouts:
        #       fmt_ns(rise), fmt_ns(fall), etc. -- one simulator State per
        #       OUT0..OUT7 if you want independent channels).

        live_row = QHBoxLayout()
        live_row.addWidget(QLabel("\u25cf Live parameter"))
        live_row.addStretch(1)
        live_row.addWidget(QLabel("CLK IN"))
        self.live_clk = QLabel("--")
        live_row.addWidget(self.live_clk)
        live_row.addSpacing(16)
        live_row.addWidget(QLabel("SYNC IN"))
        self.live_sync = QLabel("--")
        live_row.addWidget(self.live_sync)
        self.add(live_row)

    def _stat_pair(self, grid, row, col, label):
        box = QVBoxLayout()
        l = QLabel(label)
        l.setStyleSheet(f"color:{TEXT_DIM};")
        v = QLabel("--")
        v.setStyleSheet("font-weight:700; font-size:13px;")
        box.addWidget(l)
        box.addWidget(v)
        w = QWidget()
        w.setLayout(box)
        grid.addWidget(w, row, col)
        return v


# ----------------------------------------------------------------------------
# Dashboard tab: assembles the three columns
# ----------------------------------------------------------------------------
class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # column 1
        col1 = QVBoxLayout()
        self.sync_card = SyncCard()
        self.output_card = OutputCard()
        col1.addWidget(self.sync_card)
        col1.addWidget(self.output_card)
        col1.addStretch(1)

        # column 2
        col2 = QVBoxLayout()
        self.freq_card = FreqPeriodCard()
        self.config_card = ConfigCard()
        col2.addWidget(self.freq_card)
        col2.addWidget(self.config_card)
        col2.addStretch(1)

        # column 3
        col3 = QVBoxLayout()
        self.monitor_card = MonitorCard()
        col3.addWidget(self.monitor_card)
        col3.addStretch(1)

        for col, stretch in ((col1, 3), (col2, 3), (col3, 4)):
            wrap = QWidget()
            wrap.setLayout(col)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(wrap)
            scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")
            root.addWidget(scroll, stretch)


# ----------------------------------------------------------------------------
# Placeholder tab (Sync / Freq-Period / Config 1/2 / Delay presets / Output /
# Monitor / Other / Preset manager full pages) -- stub out for now.
# ----------------------------------------------------------------------------
class PlaceholderTab(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lbl = QLabel(f"{name} \u2014 full page goes here")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color:{TEXT_DIM}; font-size:14px;")
        lay.addWidget(lbl)
        # TODO: each of these tabs is presumably a full-size version of the
        #       matching dashboard card (e.g. "Sync" tab = SyncCard's controls
        #       at full width, maybe with more detail / advanced options).
        #       Reuse the Card subclasses above rather than duplicating.


# ----------------------------------------------------------------------------
# Header bar
# ----------------------------------------------------------------------------
class HeaderBar(QWidget):
    runClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)

        logo = QLabel("\U0001F53A")  # stand-in for the C-DAC logo image
        logo.setStyleSheet(f"font-size:26px; color:{BLUE};")
        lay.addWidget(logo)

        title_box = QVBoxLayout()
        title = QLabel("TG10 TIMING GENERATOR")
        title.setStyleSheet(f"font-size:19px; font-weight:800; color:{TEXT_MAIN};")
        subtitle = QLabel("Precision Timing  \u2022  Synchronization  \u2022  Pockels Cell Control")
        subtitle.setStyleSheet(f"font-size:10.5px; color:{BLUE};")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        lay.addLayout(title_box)

        lay.addStretch(1)

        self.status_badge = QLabel("\u25cf DISCONNECTED")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setStyleSheet(f"color:{RED}; border:1px solid {BORDER};")
        lay.addWidget(self.status_badge)

        for text in ("COM", "DELAY", "PRESETS"):
            b = QPushButton(text)
            lay.addWidget(b)
            # TODO: COM -> serial port picker dialog (real hardware) or a
            #       no-op when running against the simulator engine.
            #       DELAY / PRESETS -> open the matching tab / a presets dialog.

        run_btn = QPushButton("\u25b6 RUN")
        run_btn.setObjectName("runBtn")
        run_btn.clicked.connect(self.runClicked.emit)
        lay.addWidget(run_btn)
        # TODO: RUN should start/stop the simulator's live update loop
        #       (e.g. a QTimer ticking State forward) or send the hardware
        #       "start" command when a real COM link is connected.

    def set_connected(self, connected: bool):
        if connected:
            self.status_badge.setText("\u25cf CONNECTED")
            self.status_badge.setStyleSheet(f"color:{GREEN}; border:1px solid {BORDER};")
        else:
            self.status_badge.setText("\u25cf DISCONNECTED")
            self.status_badge.setStyleSheet(f"color:{RED}; border:1px solid {BORDER};")


# ----------------------------------------------------------------------------
# Main window
# ----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("C-DAC | TG10 Timing Generator")
        self.resize(1920, 1040)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = HeaderBar()
        self.header.runClicked.connect(self._on_run)
        root.addWidget(self.header)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet(f"color:{BORDER};")
        root.addWidget(sep)

        self.tabs = QTabWidget()
        self.dashboard = DashboardTab()
        self.tabs.addTab(self.dashboard, "Dashboard")
        for name in ("Sync", "Freq / Period", "Config 1/2", "Delay presets",
                     "Output", "Monitor", "Other", "Preset manager"):
            self.tabs.addTab(PlaceholderTab(name), name)
        root.addWidget(self.tabs, 1)

        self.status = QStatusBar()
        self.status.showMessage("Ready  |  Not connected")
        version_lbl = QLabel("C-DAC     TG10 GUI v1.0")
        version_lbl.setStyleSheet(f"color:{TEXT_DIM};")
        self.status.addPermanentWidget(version_lbl)
        self.setStatusBar(self.status)

        # TODO: wire everything above to a backend. Suggested shape:
        #
        #   class Backend(QObject):
        #       stateChanged = Signal()
        #       def set_clock_source(self, source, ext_freq_mhz=None): ...
        #       def set_period(self, ns): ...
        #       def set_edges(self, channel, rise_ns, fall_ns): ...
        #       def poll(self) -> dict: ...   # for Monitor table / live params
        #
        #   Give it two implementations:
        #     - SimulatorBackend (wraps tg10_simulator.State + a QTimer)
        #     - SerialBackend (talks to real TG10 over COM/CAN)
        #   The Dashboard/cards only ever call Backend methods, so swapping
        #   HeaderBar's status badge between the two is the only visible change.

    def _on_run(self):
        # TODO: start backend / simulator tick loop here.
        pass


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()