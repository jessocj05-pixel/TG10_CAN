#!/usr/bin/env python3
"""
EKSMA TG10 Timing Generator - PySide6 CONTROL PANEL

Drives a real TG10 (via serial) or a built-in Mock device.
Uses the same clock / quantization model as the simulator (main1.py).

NOTE: The command strings below are PLACEHOLDERS. Edit them in the
"Command templates" box (or in DEFAULT_COMMANDS) to match the TG10 manual.
Available fields: {period_ns} {rise_ns} {fall_ns} {clock} {ext_mhz}
                  {period_ticks} {rise_ticks} {fall_ticks}

    pip install PySide6 pyserial
    python3 tg10_control.py
"""
import sys
import math
import time
from dataclasses import dataclass

from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QDoubleSpinBox, QComboBox, QPushButton, QRadioButton, QButtonGroup,
    QCheckBox, QLineEdit, QPlainTextEdit, QGroupBox, QSpinBox, QMessageBox
)

try:
    import serial
    import serial.tools.list_ports
    HAVE_SERIAL = True
except ImportError:
    HAVE_SERIAL = False

# ---------------------------------------------------------------------------
# Placeholder command set - EDIT TO MATCH THE TG10 MANUAL
# ---------------------------------------------------------------------------
DEFAULT_COMMANDS = {
    "clock":  "CLK:SRC {clock}\n",
    "extclk": "CLK:EXT:FREQ {ext_mhz}\n",
    "period": "OUT:PER {period_ns}\n",
    "rise":   "OUT:RISE {rise_ns}\n",
    "fall":   "OUT:FALL {fall_ns}\n",
    "query":  "*IDN?\n",
}

OUT_COLOR = QColor(255, 180, 84)
CLK_COLOR = QColor(51, 255, 176)
BG = QColor(5, 10, 6)


def fmt_ns(v):
    a = abs(v)
    if a >= 1e6:
        return f"{v/1e6:.3f} ms"
    if a >= 1e3:
        return f"{v/1e3:.3f} \u00b5s"
    return f"{v:.2f} ns"


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
@dataclass
class Settings:
    clock_source: str = "internal"
    ext_mhz: float = 20.0
    period: float = 1000.0
    rise: float = 30.0
    fall: float = 230.0
    sync_cycles: int = 1

    @property
    def tclk(self):
        return 10.0 if self.clock_source == "internal" else 1000.0 / max(self.ext_mhz, 1e-6)

    def quantized(self):
        T = self.tclk
        nR = round(self.rise / T)
        nF = round(self.fall / T) + (self.sync_cycles if self.clock_source == "external" else 0)
        nP = max(1, round(self.period / T))
        if nF <= nR:
            nF = nR + 1
        return nP, nR, nF, nP * T, nR * T, nF * T


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------
class MockDevice:
    name = "Mock"

    def __init__(self):
        self.is_open = False

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def send(self, text):
        if text.strip().upper().startswith("*IDN?"):
            return "EKSMA,TG10-MOCK,0,1.0"
        return "OK"


class SerialDevice:
    name = "Serial"

    def __init__(self, port, baud):
        self.port, self.baud, self.ser = port, baud, None

    @property
    def is_open(self):
        return self.ser is not None and self.ser.is_open

    def open(self):
        self.ser = serial.Serial(self.port, self.baud, timeout=0.3, write_timeout=1.0)

    def close(self):
        if self.ser:
            self.ser.close()
        self.ser = None

    def send(self, text):
        self.ser.reset_input_buffer()
        self.ser.write(text.encode("ascii", "replace"))
        time.sleep(0.05)
        return self.ser.read(self.ser.in_waiting or 1).decode("ascii", "replace").strip()


# ---------------------------------------------------------------------------
# Preview widget (one programmed period vs realized)
# ---------------------------------------------------------------------------
class Preview(QWidget):
    def __init__(self, s: Settings):
        super().__init__()
        self.s = s
        self.setMinimumHeight(170)

    def paintEvent(self, _):
        p = QPainter(self)
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, BG)
        P = max(self.s.period, 1e-9)
        span = P * 1.2
        x0 = W * 0.04

        def px(t):
            return x0 + t / span * (W - 2 * x0)

        def pulse(r, f, y_top, h, pen):
            path = QPainterPath()
            lo, hi = y_top + h, y_top
            path.moveTo(px(0), lo)
            for n in range(2):
                b = n * P
                if b + r > span:
                    break
                path.lineTo(px(b + r), lo)
                path.lineTo(px(b + r), hi)
                path.lineTo(px(min(b + f, span)), hi)
                path.lineTo(px(min(b + f, span)), lo)
            path.lineTo(px(span), lo)
            p.setPen(pen)
            p.drawPath(path)

        p.setFont(QFont("Sans Serif", 8))
        p.setPen(QColor(147, 168, 147))
        p.drawText(QPointF(8, 14), "Programmed (dashed) vs realized on clock grid (solid)")
        pulse(self.s.rise, self.s.fall, 30, 40, QPen(QColor(255, 255, 255, 140), 1.3, Qt.DashLine))
        _, _, _, _, rQ, fQ = self.s.quantized()
        pulse(rQ, fQ, 90, 40, QPen(OUT_COLOR, 2.2))
        p.end()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EKSMA TG10 \u00b7 Control Panel (PySide6)")
        self.resize(1100, 780)
        self.s = Settings()
        self.dev = None
        self.cmd_edits = {}

        root = QWidget()
        self.setCentralWidget(root)
        main = QHBoxLayout(root)
        left, right = QVBoxLayout(), QVBoxLayout()
        main.addLayout(left, 0)
        main.addLayout(right, 1)

        left.addWidget(self._conn_group())
        left.addWidget(self._clock_group())
        left.addWidget(self._timing_group())
        left.addWidget(self._apply_group())
        left.addStretch(1)

        self.preview = Preview(self.s)
        right.addWidget(self.preview)
        right.addWidget(self._readout_group())
        right.addWidget(self._cmd_group())
        right.addWidget(self._log_group(), 1)

        self.auto_timer = QTimer(self, singleShot=True, interval=400)
        self.auto_timer.timeout.connect(self.apply_all)
        self._refresh()

    # ---- UI builders ----
    def _conn_group(self):
        g = QGroupBox("Connection")
        lay = QGridLayout(g)
        self.cb_backend = QComboBox()
        self.cb_backend.addItem("Mock device")
        if HAVE_SERIAL:
            self.cb_backend.addItem("Serial (COM/tty)")
        self.cb_port = QComboBox()
        self.cb_port.setEditable(True)
        self.sp_baud = QSpinBox()
        self.sp_baud.setRange(300, 3000000)
        self.sp_baud.setValue(115200)
        btn_scan = QPushButton("Scan")
        self.btn_conn = QPushButton("Connect")
        self.lbl_status = QLabel("Disconnected")
        lay.addWidget(QLabel("Backend"), 0, 0)
        lay.addWidget(self.cb_backend, 0, 1, 1, 2)
        lay.addWidget(QLabel("Port"), 1, 0)
        lay.addWidget(self.cb_port, 1, 1)
        lay.addWidget(btn_scan, 1, 2)
        lay.addWidget(QLabel("Baud"), 2, 0)
        lay.addWidget(self.sp_baud, 2, 1, 1, 2)
        lay.addWidget(self.btn_conn, 3, 0, 1, 3)
        lay.addWidget(self.lbl_status, 4, 0, 1, 3)
        btn_scan.clicked.connect(self.scan_ports)
        self.btn_conn.clicked.connect(self.toggle_connection)
        self.scan_ports()
        return g

    def _clock_group(self):
        g = QGroupBox("Reference clock")
        lay = QVBoxLayout(g)
        self.rb_int = QRadioButton("Internal (100 MHz)")
        self.rb_ext = QRadioButton("External")
        self.rb_int.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_int)
        grp.addButton(self.rb_ext)
        self.sp_ext = QDoubleSpinBox()
        self.sp_ext.setRange(10, 100)
        self.sp_ext.setDecimals(3)
        self.sp_ext.setSuffix(" MHz")
        self.sp_ext.setValue(20)
        self.sp_ext.setEnabled(False)
        self.sp_sync = QSpinBox()
        self.sp_sync.setRange(0, 6)
        self.sp_sync.setValue(1)
        lay.addWidget(self.rb_int)
        lay.addWidget(self.rb_ext)
        lay.addWidget(self.sp_ext)
        lay.addWidget(QLabel("Extra fall-path sync cycles (model only)"))
        lay.addWidget(self.sp_sync)
        self.rb_int.toggled.connect(self._on_change)
        self.sp_ext.valueChanged.connect(self._on_change)
        self.sp_sync.valueChanged.connect(self._on_change)
        return g

    def _timing_group(self):
        g = QGroupBox("Output timing")
        lay = QGridLayout(g)

        def spin(val):
            sb = QDoubleSpinBox()
            sb.setRange(0, 1e7)
            sb.setDecimals(2)
            sb.setSuffix(" ns")
            sb.setValue(val)
            sb.valueChanged.connect(self._on_change)
            return sb

        self.sp_period = spin(1000)
        self.sp_period.setMinimum(10)
        self.sp_rise = spin(30)
        self.sp_fall = spin(230)
        self.lbl_freq = QLabel("")
        lay.addWidget(QLabel("Period"), 0, 0)
        lay.addWidget(self.sp_period, 0, 1)
        lay.addWidget(QLabel("Frequency"), 1, 0)
        lay.addWidget(self.lbl_freq, 1, 1)
        lay.addWidget(QLabel("Rise delay"), 2, 0)
        lay.addWidget(self.sp_rise, 2, 1)
        lay.addWidget(QLabel("Fall delay"), 3, 0)
        lay.addWidget(self.sp_fall, 3, 1)
        self.cb_snap = QCheckBox("Snap values to clock ticks before sending")
        self.cb_snap.setChecked(True)
        lay.addWidget(self.cb_snap, 4, 0, 1, 2)
        return g

    def _apply_group(self):
        g = QGroupBox("Apply")
        lay = QVBoxLayout(g)
        self.cb_auto = QCheckBox("Auto-apply on change")
        btn = QPushButton("Apply to device")
        btn_q = QPushButton("Query device (*IDN?)")
        lay.addWidget(self.cb_auto)
        lay.addWidget(btn)
        lay.addWidget(btn_q)
        btn.clicked.connect(self.apply_all)
        btn_q.clicked.connect(lambda: self.send_raw(self.cmd_edits["query"].text()))
        return g

    def _readout_group(self):
        g = QGroupBox("Computed / realized")
        lay = QGridLayout(g)
        self.readouts = {}
        names = ["Tclk", "Pulse width (programmed)", "Duty cycle", "Ticks P / R / F",
                 "Realized tR", "Realized tF", "Realized width", "\u0394 width"]
        for i, n in enumerate(names):
            lay.addWidget(QLabel(n), i // 2, (i % 2) * 2)
            v = QLabel("\u2014")
            v.setStyleSheet("font-family:monospace; font-weight:bold; color:#b36b00;")
            lay.addWidget(v, i // 2, (i % 2) * 2 + 1)
            self.readouts[n] = v
        return g

    def _cmd_group(self):
        g = QGroupBox("Command templates (placeholders \u2014 edit to match TG10 manual)")
        lay = QGridLayout(g)
        for i, (k, v) in enumerate(DEFAULT_COMMANDS.items()):
            lay.addWidget(QLabel(k), i, 0)
            e = QLineEdit(v.replace("\n", "\\n"))
            lay.addWidget(e, i, 1)
            self.cmd_edits[k] = e
        self.raw_edit = QLineEdit()
        self.raw_edit.setPlaceholderText("Raw command, Enter to send")
        self.raw_edit.returnPressed.connect(
            lambda: (self.send_raw(self.raw_edit.text() + "\\n"), self.raw_edit.clear()))
        lay.addWidget(QLabel("raw"), len(DEFAULT_COMMANDS), 0)
        lay.addWidget(self.raw_edit, len(DEFAULT_COMMANDS), 1)
        return g

    def _log_group(self):
        g = QGroupBox("Log")
        lay = QVBoxLayout(g)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(1000)
        lay.addWidget(self.log)
        return g

    # ---- logic ----
    def scan_ports(self):
        self.cb_port.clear()
        if HAVE_SERIAL:
            for p in serial.tools.list_ports.comports():
                self.cb_port.addItem(p.device)

    def _on_change(self, *_):
        self.s.clock_source = "internal" if self.rb_int.isChecked() else "external"
        self.sp_ext.setEnabled(self.s.clock_source == "external")
        self.s.ext_mhz = self.sp_ext.value()
        self.s.sync_cycles = self.sp_sync.value()
        self.s.period = self.sp_period.value()
        self.s.rise = self.sp_rise.value()
        self.s.fall = self.sp_fall.value()
        self._refresh()
        if self.cb_auto.isChecked() and self.dev and self.dev.is_open:
            self.auto_timer.start()

    def _refresh(self):
        s = self.s
        nP, nR, nF, pQ, rQ, fQ = s.quantized()
        w = s.fall - s.rise
        self.lbl_freq.setText(f"{1e9 / s.period / 1e3:.4f} kHz")
        r = self.readouts
        r["Tclk"].setText(fmt_ns(s.tclk))
        r["Pulse width (programmed)"].setText(fmt_ns(w))
        r["Duty cycle"].setText(f"{w / s.period * 100:.2f} %")
        r["Ticks P / R / F"].setText(f"{nP} / {nR} / {nF}")
        r["Realized tR"].setText(fmt_ns(rQ))
        r["Realized tF"].setText(fmt_ns(fQ))
        r["Realized width"].setText(fmt_ns(fQ - rQ))
        r["\u0394 width"].setText(fmt_ns((fQ - rQ) - w))
        if s.fall <= s.rise or s.fall > s.period:
            self.lbl_status.setStyleSheet("color:#c00;")
        self.preview.update()

    def _log(self, msg):
        self.log.appendPlainText(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def toggle_connection(self):
        if self.dev and self.dev.is_open:
            self.dev.close()
            self.dev = None
            self.btn_conn.setText("Connect")
            self.lbl_status.setText("Disconnected")
            self._log("Disconnected")
            return
        try:
            if self.cb_backend.currentIndex() == 0:
                self.dev = MockDevice()
            else:
                self.dev = SerialDevice(self.cb_port.currentText(), self.sp_baud.value())
            self.dev.open()
        except Exception as e:
            self.dev = None
            QMessageBox.critical(self, "Connection failed", str(e))
            return
        self.btn_conn.setText("Disconnect")
        self.lbl_status.setText(f"Connected ({self.dev.name})")
        self._log(f"Connected via {self.dev.name}")

    def _template(self, key, **fields):
        raw = self.cmd_edits[key].text().replace("\\n", "\n").replace("\\r", "\r")
        try:
            return raw.format(**fields)
        except (KeyError, IndexError) as e:
            raise ValueError(f"Bad template '{key}': {e}")

    def send_raw(self, text):
        if not (self.dev and self.dev.is_open):
            self._log("Not connected")
            return False
        text = text.replace("\\n", "\n").replace("\\r", "\r")
        try:
            self._log(f"TX {text.strip()!r}")
            self._log(f"RX {self.dev.send(text)!r}")
            return True
        except Exception as e:
            self._log(f"ERROR {e}")
            return False

    def apply_all(self):
        s = self.s
        if s.fall <= s.rise or s.fall > s.period:
            QMessageBox.warning(self, "Invalid timing", "Need rise < fall \u2264 period.")
            return
        nP, nR, nF, pQ, rQ, fQ = s.quantized()
        # when snapping, send tick-aligned values (without the model-only sync offset)
        if self.cb_snap.isChecked():
            period, rise, fall = nP * s.tclk, round(s.rise / s.tclk) * s.tclk, round(s.fall / s.tclk) * s.tclk
        else:
            period, rise, fall = s.period, s.rise, s.fall
        fields = dict(
            clock=s.clock_source.upper(), ext_mhz=f"{s.ext_mhz:.3f}",
            period_ns=f"{period:.2f}", rise_ns=f"{rise:.2f}", fall_ns=f"{fall:.2f}",
            period_ticks=nP, rise_ticks=nR, fall_ticks=round(s.fall / s.tclk),
        )
        try:
            seq = ["clock"] + (["extclk"] if s.clock_source == "external" else []) + ["period", "rise", "fall"]
            for key in seq:
                if not self.send_raw(self._template(key, **fields)):
                    self._log("Apply aborted")
                    return
        except ValueError as e:
            self._log(str(e))
            return
        self._log("Apply complete")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()