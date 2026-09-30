# """
# TG10 TIMING GENERATOR - C-DAC
# PySide6 dashboard GUI

# Run:
#     python main.py

# Requirement:
#     pip install PySide6 pyserial
# """

import sys
import os
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
from PySide6.QtGui import (
    QFont, QPainter, QPen, QColor, QPolygonF, QBrush, QPixmap
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel,
    QPushButton, QComboBox, QLineEdit, QRadioButton,
    QCheckBox, QSpinBox, QDoubleSpinBox, QHBoxLayout,
    QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QButtonGroup, QSizePolicy,
    QToolButton, QDialog, QDialogButtonBox, QFormLayout,
    QGroupBox, QStackedWidget, QMessageBox
)

try:
    from serial.tools import list_ports
except ImportError:
    list_ports = None


# ============================================================
# COLORS
# ============================================================

NAVY = "#082f55"
BLUE = "#0878c9"
DEEP = "#0b4778"
GREEN = "#119447"
RED = "#d83b3b"
LINE = "#c5d4e2"
PAGE = "#e9f0f6"
TEXT = "#1d344b"
GREY = "#5a7085"


# ============================================================
# STYLE
# ============================================================

STYLE = f"""
* {{
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 11px;
    color: {TEXT};
    font-weight: 500;
}}

QMainWindow {{
    background: {PAGE};
}}

QDialog {{
    background: white;
    color: #23384d;
}}

QDialog QWidget {{
    background: white;
    color: #23384d;
}}

QGroupBox {{
    background: white;
    color: #23384d;
    border: 1px solid #ccd8e3;
    border-radius: 3px;
    margin-top: 8px;
    padding-top: 8px;
}}

QGroupBox::title {{
    color: #23384d;
    background: white;
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

QDialog QLabel {{
    background: transparent;
    color: #23384d;
}}

QDialog QPushButton {{
    background: white;
    color: #23384d;
    border: 1px solid #ccd8e3;
    border-radius: 3px;
    padding: 6px 16px;
}}

QDialog QPushButton:hover {{
    background: #f2f7fb;
    border-color: #1976b9;
}}

QWidget#Root {{
    background: {PAGE};
}}

QWidget#Header {{
    background: white;
    border-bottom: 1px solid {LINE};
}}

QFrame#LogoBox {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 3px;
}}

QLabel#LogoHi {{
    color: #d32929;
    font-size: 13px;
    font-weight: 800;
}}

QLabel#LogoLo {{
    color: #d32929;
    font-size: 20px;
    font-weight: 800;
}}

QLabel#AppTitle {{
    color: {DEEP};
    font-size: 24px;
    font-weight: 800;
}}

QLabel#AppSub {{
    color: {GREY};
    font-size: 11px;
}}

QLabel#StatusPill {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 3px;
    color: {RED};
    font-weight: 700;
    padding: 8px 12px;
}}

QPushButton#HdrBtn {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 3px;
    color: #23394f;
    font-weight: 700;
    min-height: 34px;
    padding: 3px 12px;
}}

QPushButton#HdrBtn:hover {{
    border-color: {BLUE};
    background: #f2f7fb;
}}

QPushButton#HdrBtn[active="true"] {{
    background: {BLUE};
    border-color: {BLUE};
    color: white;
    font-weight: 700;
}}

QPushButton#RunBtn {{
    background: {GREEN};
    border: 1px solid {GREEN};
    border-radius: 3px;
    color: white;
    font-weight: 800;
    min-height: 34px;
    padding: 3px 14px;
}}

QPushButton#RunBtn:hover {{
    background: #117c3a;
}}

QWidget#TabBar {{
    background: #f4f7fa;
    border-bottom: 1px solid {LINE};
}}

QPushButton#Tab {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 3px;
    color: #314b62;
    min-height: 32px;
    padding: 3px 11px;
}}

QPushButton#Tab:hover {{
    background: #edf5fb;
}}

QPushButton#Tab:checked {{
    background: {BLUE};
    border-color: {BLUE};
    color: white;
    font-weight: 700;
}}

QFrame#Card {{
    background: white;
    border: 1px solid #b9ccdc;
    border-radius: 6px;
}}

QLabel#CardIcon {{
    color: {BLUE};
    font-size: 16px;
    font-weight: 700;
}}

QLabel#CardTitle {{
    color: {DEEP};
    font-size: 15px;
    font-weight: 800;
}}

QToolButton#Chevron {{
    background: transparent;
    border: none;
    color: {GREY};
    font-size: 16px;
    font-weight: 700;
}}

QFrame#SubPanel {{
    background: white;
    border: 1px solid #c4d4e2;
    border-radius: 5px;
}}

QLabel#SubHeader {{
    background: {BLUE};
    color: white;
    font-weight: 800;
    padding: 8px 10px;
}}

QLabel#FieldLabel {{
    color: #24455f;
    font-size: 11px;
    font-weight: 650;
}}

QLabel#InfoBox {{
    background: #f1f6fa;
    border: 1px solid #dbe5ed;
    border-radius: 2px;
    color: #4b6277;
    padding: 7px 9px;
}}

QLabel#SmallGrey {{
    color: {GREY};
    font-size: 10.5px;
    font-weight: 600;
}}

QComboBox,
QLineEdit,
QSpinBox,
QDoubleSpinBox {{
    background: white;
    border: 1px solid #bdcad6;
    border-radius: 2px;
    min-height: 28px;
    padding: 2px 7px;
    font-size: 11px;
    font-weight: 600;
}}

QComboBox:hover,
QLineEdit:hover,
QSpinBox:hover,
QDoubleSpinBox:hover {{
    border-color: {BLUE};
}}

QComboBox::drop-down {{
    width: 22px;
    border: none;
}}

QComboBox QAbstractItemView {{
    background: white;
    border: 1px solid {LINE};
    selection-background-color: {BLUE};
    selection-color: white;
}}

QRadioButton,
QCheckBox {{
    color: #243b50;
    spacing: 8px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel:disabled,
QRadioButton:disabled,
QCheckBox:disabled {{
    color: #9aa7b3;
}}

QComboBox:disabled,
QLineEdit:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled {{
    background: #f3f5f7;
    color: #9aa7b3;
    border-color: #d7dee5;
}}

QRadioButton::indicator,
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
}}

QRadioButton::indicator {{
    border: 1px solid #98aabd;
    border-radius: 8px;
    background: white;
}}

QRadioButton::indicator:checked {{
    border: 4px solid {BLUE};
    background: white;
}}

QCheckBox::indicator {{
    border: 1px solid #98aabd;
    border-radius: 2px;
    background: white;
}}

QCheckBox::indicator:checked {{
    background: {BLUE};
    border-color: {BLUE};
}}

QPushButton#Seg {{
    background: #eef3f7;
    border: 1px solid {LINE};
    border-radius: 2px;
    color: #334b61;
    min-height: 30px;
    padding: 2px 9px;
    font-size: 11px;
    font-weight: 650;
}}

QPushButton#Seg:checked {{
    background: {BLUE};
    border-color: {BLUE};
    color: white;
    font-weight: 600;
}}

QFrame#Tile {{
    background: #f7fafc;
    border: 1px solid #dce5ec;
    border-radius: 2px;
}}

QLabel#TileLabel {{
    color: {GREY};
    font-size: 11px;
    font-weight: 600;
}}

QLabel#TileValue {{
    color: #17324d;
    font-size: 12px;
    font-weight: 700;
}}

QTableWidget {{
    background: white;
    border: 1px solid {LINE};
    gridline-color: #d6e2ec;
    outline: none;
    font-size: 10.5px;
    font-weight: 600;
}}

QTableWidget::item {{
    padding: 4px;
}}

QHeaderView::section {{
    background: #f2f6fa;
    color: {DEEP};
    font-weight: 800;
    font-size: 10.5px;
    border: none;
    border-right: 1px solid #d5e0ea;
    border-bottom: 1px solid {LINE};
    padding: 6px 4px;
}}

QLabel#LiveHeader {{
    background: #f3f7fa;
    border: 1px solid {LINE};
    color: {DEEP};
    font-weight: 800;
    font-size: 11px;
    padding: 7px 9px;
}}

QLabel#LiveBody {{
    background: white;
    border: 1px solid {LINE};
    color: {GREY};
    font-size: 11px;
    font-weight: 600;
    padding: 8px;
}}

QPushButton#SmallBtn {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 2px;
    min-height: 28px;
    padding: 3px 10px;
    font-size: 10.5px;
    font-weight: 700;
}}

QPushButton#SmallBtn:hover {{
    border-color: {BLUE};
    background: #f2f7fb;
}}

QWidget#StatusBar {{
    background: white;
    border-top: 1px solid {LINE};
}}

QLabel#StatusText,
QLabel#StatusRight {{
    color: {DEEP};
    font-size: 10.5px;
}}

QLabel#StatusRight {{
    font-weight: 700;
}}

/* --- Instrument-grade visual polish --- */
QPushButton:hover {{
    border-color: {BLUE};
}}

QPushButton:pressed {{
    background: #dcecf8;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 2px solid {BLUE};
    padding: 1px 6px;
}}

QRadioButton:hover, QCheckBox:hover {{
    color: {DEEP};
}}

QFrame#Card:hover {{
    border-color: #9dbbd2;
}}
"""



# ============================================================
# HELPERS
# ============================================================

def label(text, name=None, bold=False, size=None, color=None):
    w = QLabel(text)

    if name:
        w.setObjectName(name)

    css = ""

    if bold:
        css += "font-weight:700;"

    if size:
        css += f"font-size:{size}px;"

    if color:
        css += f"color:{color};"

    if css:
        w.setStyleSheet(css)

    return w


def combo(items, width=None):
    c = QComboBox()
    c.addItems(items)

    if width:
        c.setFixedWidth(width)

    return c


def make_card(icon, title, collapsible=True):
    frame = QFrame()
    frame.setObjectName("Card")
    frame.setSizePolicy(
        QSizePolicy.Expanding,
        QSizePolicy.Expanding
    )

    outer = QVBoxLayout(frame)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    header = QWidget()

    hl = QHBoxLayout(header)
    hl.setContentsMargins(12, 6, 10, 5)
    hl.setSpacing(7)

    hl.addWidget(label(icon, "CardIcon"))
    hl.addWidget(label(title, "CardTitle"))
    hl.addStretch()

    if collapsible:
        button = QToolButton()
        button.setObjectName("Chevron")
        button.setText("⌃")
        button.setFixedSize(24, 24)
        hl.addWidget(button)

    outer.addWidget(header)

    body = QWidget()
    body.setSizePolicy(
        QSizePolicy.Expanding,
        QSizePolicy.Expanding
    )

    bl = QVBoxLayout(body)
    bl.setContentsMargins(12, 0, 12, 12)
    bl.setSpacing(7)

    outer.addWidget(body, 1)

    return frame, bl


def make_subpanel(title):
    frame = QFrame()
    frame.setObjectName("SubPanel")

    outer = QVBoxLayout(frame)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    header = QLabel(title)
    header.setObjectName("SubHeader")
    header.setMinimumHeight(34)

    outer.addWidget(header)

    body = QWidget()

    layout = QVBoxLayout(body)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(6)

    outer.addWidget(body, 1)

    return frame, layout


def add_card_action(frame, callback=None, text="Set"):
    """Add a compact action button to the top-right of a card header."""
    header = frame.layout().itemAt(0).widget()
    header_layout = header.layout()

    button = QPushButton(text)
    button.setObjectName("SmallBtn")
    button.setFixedSize(48, 25)
    button.setCursor(Qt.PointingHandCursor)

    if callback is not None:
        button.clicked.connect(callback)

    # Keep the chevron (when present) at the far right.
    insert_at = header_layout.count()
    if insert_at:
        last = header_layout.itemAt(insert_at - 1).widget()
        if isinstance(last, QToolButton):
            insert_at -= 1
    header_layout.insertWidget(insert_at, button)
    return button


# ============================================================
# TIMING VISUALIZATION
# ============================================================

class TimingViz(QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumHeight(90)
        self.setObjectName("Viz")

    def paintEvent(self, event):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        p.fillRect(self.rect(), QColor("white"))

        left = 42
        right = w - 12
        top = 28
        bottom = h - 17

        high = top + 9
        low = bottom - 7

        # Grid
        p.setPen(QPen(QColor("#e4ebf2"), 1))

        for i in range(9):
            x = left + (right - left) * i / 8
            p.drawLine(int(x), top, int(x), bottom)

        for i in range(5):
            y = top + (bottom - top) * i / 4
            p.drawLine(left, int(y), right, int(y))

        # Axis
        p.setPen(QPen(QColor("#9fb0c0"), 1))
        p.drawLine(left, top, left, bottom)
        p.drawLine(left, bottom, right, bottom)

        p.setPen(QColor("#33475c"))
        p.setFont(QFont("Segoe UI", 8))

        p.drawText(7, high + 4, "High")
        p.drawText(9, low + 4, "Low")
        p.drawText(left - 3, bottom + 13, "t0")
        p.drawText(right - 5, bottom + 13, "t")

        span = right - left

        x1 = left + span * 0.17
        x2 = left + span * 0.35
        x3 = left + span * 0.58
        x4 = left + span * 0.78

        points = [
            QPointF(left, low),
            QPointF(x1, low),
            QPointF(x1, high),
            QPointF(x2, high),
            QPointF(x2, low),
            QPointF(x3, low),
            QPointF(x3, high),
            QPointF(x4, high),
            QPointF(x4, low),
            QPointF(right, low)
        ]

        p.setPen(QPen(QColor(BLUE), 2))

        for a, b in zip(points, points[1:]):
            p.drawLine(a, b)

        self.draw_arrow(p, x1, x2, top - 5, "Pulse Width")
        self.draw_arrow(p, x1, x3, top + 7, "Period")

        p.end()

    def draw_arrow(self, p, x1, x2, y, text):

        if x2 - x1 < 50:
            return

        p.setPen(QPen(QColor("#17324d"), 1))

        p.drawLine(
            QPointF(x1, y),
            QPointF(x2, y)
        )

        for x, direction in ((x1, 1), (x2, -1)):

            poly = QPolygonF([
                QPointF(x, y),
                QPointF(x + 5 * direction, y - 3),
                QPointF(x + 5 * direction, y + 3)
            ])

            p.setBrush(QBrush(QColor("#17324d")))
            p.drawPolygon(poly)

        p.setBrush(Qt.NoBrush)
        p.setFont(QFont("Segoe UI", 8))

        width = p.fontMetrics().horizontalAdvance(text)
        center = (x1 + x2) / 2

        p.fillRect(
            QRectF(
                center - width / 2 - 3,
                y - 13,
                width + 6,
                12
            ),
            QColor("white")
        )

        p.drawText(
            QPointF(center - width / 2, y - 4),
            text
        )


# ============================================================
# COM DIALOG
# ============================================================

class COMDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("COM / CAN Configuration")
        self.resize(460, 320)

        self.selected_port = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(
            label(
                "Communication Configuration",
                bold=True,
                size=16,
                color=DEEP
            )
        )

        group = QGroupBox("USB-CAN / CAN")
        form = QFormLayout(group)
        form.setSpacing(8)

        # COM port list is populated from the ports currently detected
        # by the operating system. The list is refreshed periodically so
        # newly plugged-in / removed USB-CAN adapters are reflected.
        self.com_port = QComboBox()
        self.com_port.setMinimumWidth(250)
        self.com_port.currentIndexChanged.connect(self._port_changed)
        form.addRow("COM Port:", self.com_port)

        # These communication parameters are fixed for this TG10 setup.
        self.com_bps = self._fixed_field("9600")
        form.addRow("COM BPS:", self.com_bps)

        self.can_mode = self._fixed_field("Normal")
        form.addRow("CAN Mode:", self.can_mode)

        self.frame = self._fixed_field("Extended Frame")
        form.addRow("Frame:", self.frame)

        self.can_bps = self._fixed_field("1 Mbps")
        form.addRow("CAN BPS:", self.can_bps)

        layout.addWidget(group)

        layout.addWidget(
            label(
                "PC → USB-CAN → CAN → TG10",
                "InfoBox"
            )
        )

        # Apply & Close replaces the old Close-only button.
        buttons = QHBoxLayout()
        buttons.addStretch()

        apply_close = QPushButton("Apply && Close")
        apply_close.setObjectName("SmallBtn")
        apply_close.setMinimumWidth(110)
        apply_close.clicked.connect(self.apply_and_close)
        buttons.addWidget(apply_close)

        layout.addLayout(buttons)

        # Poll for hot-plug changes while this dialog is open.
        self.port_timer = QTimer(self)
        self.port_timer.setInterval(1000)
        self.port_timer.timeout.connect(self.refresh_ports)
        self.refresh_ports()
        self.port_timer.start()

    def _fixed_field(self, value):
        field = QLineEdit(value)
        field.setReadOnly(True)
        return field

    def refresh_ports(self):
        """Refresh the COM dropdown from the ports detected by Windows."""
        current_port = self.selected_port
        if self.com_port.currentIndex() >= 0:
            current_data = self.com_port.currentData()
            if current_data:
                current_port = current_data

        ports = []
        if list_ports is not None:
            try:
                ports = sorted(
                    list(list_ports.comports()),
                    key=lambda p: p.device
                )
            except Exception:
                ports = []

        self.com_port.blockSignals(True)
        self.com_port.clear()

        if ports:
            for port in ports:
                description = (port.description or "").strip()
                if description and description.lower() != "n/a":
                    display = f"{port.device} — {description}"
                else:
                    display = port.device
                self.com_port.addItem(display, port.device)

            # Keep the previously selected port if it is still connected;
            # otherwise select the first detected port.
            index = self.com_port.findData(current_port)
            if index < 0:
                index = 0
            self.com_port.setCurrentIndex(index)
            self.selected_port = self.com_port.currentData()
        else:
            self.com_port.addItem("No COM ports detected", None)
            self.selected_port = None

        self.com_port.blockSignals(False)

    def _port_changed(self, index):
        self.selected_port = self.com_port.itemData(index)

    def apply_and_close(self):
        """Save the selected COM port and close the dialog."""
        self.selected_port = self.com_port.currentData()
        if self.port_timer.isActive():
            self.port_timer.stop()
        self.accept()

    def reject(self):
        if hasattr(self, "port_timer") and self.port_timer.isActive():
            self.port_timer.stop()
        super().reject()


# ============================================================
# DELAY DIALOG
# ============================================================

class DelayDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("TG10 Delay Presets")
        self.resize(700, 450)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(8)

        root.addWidget(
            label(
                "Delay Presets",
                bold=True,
                size=16,
                color=DEEP
            )
        )

        tabs = QHBoxLayout()
        tabs.setSpacing(5)

        self.stack = QWidget()
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)

        pages = []

        # ----------------------------------------------------
        # DELAY PRESETS
        # ----------------------------------------------------

        page1 = QWidget()

        grid = QGridLayout(page1)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(5)

        grid.addWidget(label("Preset", "FieldLabel", True), 0, 0)
        grid.addWidget(label("Value", "FieldLabel", True), 0, 1)
        grid.addWidget(label("Preset", "FieldLabel", True), 0, 3)
        grid.addWidget(label("Value", "FieldLabel", True), 0, 4)

        for i in range(4):

            a = QDoubleSpinBox()
            a.setRange(0, 150_000_000)
            a.setDecimals(3)
            a.setSuffix(" ns")

            b = QDoubleSpinBox()
            b.setRange(0, 150_000_000)
            b.setDecimals(3)
            b.setSuffix(" ns")

            grid.addWidget(
                label(f"DEL{i}", "FieldLabel"),
                i + 1, 0
            )
            grid.addWidget(a, i + 1, 1, 1, 2)

            grid.addWidget(
                label(f"DEL{i + 4}", "FieldLabel"),
                i + 1, 3
            )
            grid.addWidget(b, i + 1, 4, 1, 2)

        grid.addWidget(
            label("Range: 0 … 150 ms", "InfoBox"),
            5, 0, 1, 6
        )

        pages.append(page1)

        # ----------------------------------------------------
        # POST DELAY
        # ----------------------------------------------------

        page2 = QWidget()

        grid2 = QGridLayout(page2)

        for i in range(8):

            value = QDoubleSpinBox()
            value.setRange(0, 150_000_000)
            value.setDecimals(3)
            value.setSuffix(" ns")

            grid2.addWidget(
                label(f"post DEL{i}", "FieldLabel"),
                i, 0
            )
            grid2.addWidget(value, i, 1)

        pages.append(page2)

        names = [
            "Delay presets",
            "Post-delay"
        ]

        self.page_buttons = []

        for i, name in enumerate(names):

            b = QPushButton(name)
            b.setObjectName("Seg")
            b.setCheckable(True)
            b.setChecked(i == 0)

            self.page_buttons.append(b)

            tabs.addWidget(b, 1)

            b.clicked.connect(
                lambda checked, index=i:
                self.show_delay_page(index, pages)
            )

        root.addLayout(tabs)

        for page in pages:
            page.setVisible(False)
            self.stack_layout.addWidget(page)

        pages[0].setVisible(True)

        root.addWidget(self.stack, 1)

        close_button = QPushButton("Close")
        close_button.setObjectName("SmallBtn")
        close_button.clicked.connect(self.accept)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close_button)

        root.addLayout(bottom)

    def show_delay_page(self, index, pages):

        for i, page in enumerate(pages):
            page.setVisible(i == index)


# ============================================================
# PRESET DIALOG
# ============================================================

class PresetDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("TG10 Preset Manager")
        self.resize(650, 400)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)

        root.addWidget(
            label(
                "Preset Manager",
                bold=True,
                size=16,
                color=DEEP
            )
        )

        table = QTableWidget(4, 5)

        table.setHorizontalHeaderLabels([
            "Preset",
            "Frequency",
            "Sync",
            "Config",
            "Status"
        ])

        table.verticalHeader().setVisible(False)

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        data = [
            ["Default", "1.000000 MHz",
             "Internal", "Config 1", "Ready"],

            ["Pockels_100ns", "1.000000 MHz",
             "Internal", "Config 1", "Ready"],

            ["External_Sync", "10.000000 MHz",
             "External", "Config 2", "Ready"],

            ["Experiment_01", "5.000000 MHz",
             "Internal", "Config 2", "Ready"]
        ]

        for r, row in enumerate(data):

            for c, value in enumerate(row):

                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)

                table.setItem(r, c, item)

        root.addWidget(table, 1)

        buttons = QHBoxLayout()

        for text in [
            "LOAD",
            "SAVE",
            "ADD",
            "EDIT",
            "DELETE"
        ]:

            b = QPushButton(text)
            b.setObjectName("SmallBtn")

            buttons.addWidget(b)

        buttons.addStretch()

        close = QPushButton("Close")
        close.setObjectName("SmallBtn")
        close.clicked.connect(self.accept)

        buttons.addWidget(close)

        root.addLayout(buttons)


# ============================================================
# MAIN WINDOW
# ============================================================

class TG10Window(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "C-DAC | TG10 Timing Generator"
        )

        # Keep the dashboard usable in a normal window; maximize still gives
        # the full instrument view on larger displays.
        self.setMinimumSize(1180, 680)
        self.resize(1450, 820)

        self.running = False

        # USB-CAN connection state. The COM port is selected dynamically
        # from Windows; no COM number is hard-coded in the GUI.
        self.selected_com_port = None
        self.serial_connection = None
        self.can_backend = None
        self.can_reader = None
        self.connection_state = False

        self.sync_mode = "Internal"
        self.frequency_mode = "Frequency"
        self.current_frequency_hz = 1_000_000.0
        self.current_period_s = 1e-6

        # Values shown in Monitor are committed only when the corresponding
        # section's Set button is pressed.
        self.committed_sync_mode = "Internal"
        self.committed_config_name = "Config 1"
        self.committed_frequency_hz = 1_000_000.0
        self.committed_period_s = 1e-6
        self.committed_freq_unit = "MHz"
        self.committed_period_unit = "µs"

        # Navigation -> dashboard section mapping used for highlighting
        self.section_cards = {}

        root = QWidget()
        root.setObjectName("Root")

        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self.header())
        main.addWidget(self.navigation())
        main.addWidget(self.dashboard(), 1)
        main.addWidget(self.status_bar())

    # ========================================================
    # HEADER
    # ========================================================

    def header(self):

        w = QWidget()
        w.setObjectName("Header")

        w.setMinimumHeight(66)
        w.setMaximumHeight(66)

        h = QHBoxLayout(w)
        h.setContentsMargins(12, 6, 12, 6)
        h.setSpacing(12)

        # Logo
        # C-DAC Logo
        logo = QLabel()
        logo.setFixedSize(104, 52)
        logo.setAlignment(Qt.AlignCenter)

        logo_path = os.path.join(
            os.path.dirname(__file__),
            "cdac_logo.png"
        )

        pixmap = QPixmap(logo_path)

        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    104,
                    52,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

        h.addWidget(logo)

        # Blue vertical line
        line = QFrame()
        line.setFixedWidth(3)
        line.setStyleSheet(
            f"background:{BLUE};"
        )

        h.addWidget(line)

        title = QVBoxLayout()
        title.setSpacing(1)

        title.addWidget(
            label(
                "TG10 TIMING GENERATOR",
                "AppTitle"
            )
        )

        title.addWidget(
            label(
                "Precision Timing  •  Synchronization  •  "
                "Pockels Cell Control",
                "AppSub"
            )
        )

        h.addLayout(title)

        h.addStretch()

        self.connection = QLabel(
            "●  DISCONNECTED"
        )

        self.connection.setObjectName(
            "StatusPill"
        )

        self.connection.setAlignment(
            Qt.AlignCenter
        )

        self.connection.setFixedWidth(220)

        h.addWidget(self.connection)

        # COM
        com = QPushButton("COM")
        com.setObjectName("HdrBtn")
        com.setFixedWidth(100)
        com.clicked.connect(self.open_com)

        h.addWidget(com)

        # Delay
        self.delay_header_btn = QPushButton("DELAY")
        self.delay_header_btn.setObjectName("HdrBtn")
        self.delay_header_btn.setFixedWidth(100)
        self.delay_header_btn.clicked.connect(self.open_delay)

        h.addWidget(self.delay_header_btn)

        # Presets
        self.presets_header_btn = QPushButton("PRESETS")
        self.presets_header_btn.setObjectName("HdrBtn")
        self.presets_header_btn.setFixedWidth(105)
        self.presets_header_btn.clicked.connect(self.open_presets)

        h.addWidget(self.presets_header_btn)

        # Run
        self.run_button = QPushButton("▶  RUN")
        self.run_button.setObjectName("RunBtn")
        self.run_button.setFixedWidth(115)
        self.run_button.clicked.connect(
            self.toggle_run
        )

        h.addWidget(self.run_button)

        return w

    # ========================================================
    # NAVIGATION
    # ========================================================

    def navigation(self):

        w = QWidget()
        w.setObjectName("TabBar")

        w.setMinimumHeight(38)
        w.setMaximumHeight(38)

        h = QHBoxLayout(w)
        h.setContentsMargins(12, 5, 12, 5)
        h.setSpacing(6)

        group = QButtonGroup(w)
        group.setExclusive(True)

        names = [
            "Dashboard",
            "Sync",
            "Freq / Period",
            "Config 1/2",
            "Delay presets",
            "Output",
            "Monitor",
            "Other",
            "Preset manager"
        ]

        for i, name in enumerate(names):

            b = QPushButton(name)
            b.setObjectName("Tab")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)

            b.clicked.connect(
                lambda checked, name=name: (
                    self.highlight_section(name),
                    self.highlight_header_buttons(name)
                )
            )

            if i == 0:
                b.setChecked(True)

            group.addButton(b, i)

            h.addWidget(b)

        h.addStretch()

        return w

    def highlight_header_buttons(self, name):
        """Highlight DELAY/PRESETS buttons in the header near COM."""
        delay = getattr(self, "delay_header_btn", None)
        presets = getattr(self, "presets_header_btn", None)

        if delay is not None:
            delay.setProperty("active", name == "Delay presets")
            delay.style().unpolish(delay)
            delay.style().polish(delay)
            delay.update()

        if presets is not None:
            presets.setProperty("active", name == "Preset manager")
            presets.style().unpolish(presets)
            presets.style().polish(presets)
            presets.update()

    def highlight_section(self, name):
        """Highlight the dashboard card associated with a top navigation button."""

        # Dashboard clears any card highlight.
        if name == "Dashboard":
            for widget in self.section_cards.values():
                widget.setStyleSheet("")
            return

        # Clear previous highlight.
        for widget in self.section_cards.values():
            widget.setStyleSheet("")

        # Highlight the selected dashboard section, if it exists.
        if name in self.section_cards:
            self.section_cards[name].setStyleSheet("""
                QFrame#Card {
                    background: white;
                    border: 2px solid #1976b9;
                    border-radius: 4px;
                }
            """)

    # ========================================================
    # DASHBOARD
    # ========================================================

    def dashboard(self):

        page = QWidget()

        grid = QGridLayout(page)

        grid.setContentsMargins(8, 6, 8, 6)

        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        sync = self.sync_card()
        config = self.config_card()
        freq = self.frequency_card()
        output = self.output_card()
        monitor = self.monitor_card()
        other = self.other_card()

        # Defensive validation: every dashboard section must return its QFrame.
        dashboard_cards = {
            "Sync": sync,
            "Config 1/2": config,
            "Freq / Period": freq,
            "Output": output,
            "Monitor": monitor,
            "Other": other,
        }
        missing_cards = [name for name, widget in dashboard_cards.items() if widget is None]
        if missing_cards:
            raise RuntimeError(
                "Dashboard card returned None: " + ", ".join(missing_cards)
            )

        # Store dashboard sections for navigation highlighting
        self.section_cards = {
            "Sync": sync,
            "Freq / Period": freq,
            "Config 1/2": config,
            "Output": output,
            "Monitor": monitor,
            "Other": other,
        }

        # ----------------------------------------------------
        # MAIN DASHBOARD
        # ----------------------------------------------------
        # The dashboard Live parameter strip is intentionally not placed
        # between Sync/Config and Output/Frequency. Live parameters now
        # belong below the Monitor output table.
        grid.addWidget(sync, 0, 0)
        grid.addWidget(config, 0, 1)
        grid.addWidget(monitor, 0, 2, 3, 1)
        grid.addWidget(output, 1, 0)
        grid.addWidget(freq, 1, 1)
        grid.addWidget(other, 2, 0, 1, 2)

        grid.setColumnStretch(0, 43)
        grid.setColumnStretch(1, 17)
        grid.setColumnStretch(2, 40)

        grid.setRowMinimumHeight(0, 390)
        grid.setRowMinimumHeight(1, 170)
        grid.setRowMinimumHeight(2, 80)

        grid.setRowStretch(0, 34)
        grid.setRowStretch(1, 18)
        grid.setRowStretch(2, 7)

        return page

    def live_parameter_card(self):
        """Compact dashboard Live parameter strip."""
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setMinimumHeight(48)
        frame.setMaximumHeight(62)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(8)

        layout.addWidget(label("◉", "CardIcon"))
        layout.addWidget(label("Live parameter", "CardTitle"))
        layout.addSpacing(10)

        clk_tile = QFrame()
        clk_tile.setObjectName("Tile")
        clk_layout = QHBoxLayout(clk_tile)
        clk_layout.setContentsMargins(9, 3, 9, 3)
        clk_layout.setSpacing(7)
        clk_layout.addWidget(label("CLK IN", "TileLabel"))
        self.dashboard_live_clk = label("100.000 MHz", "TileValue")
        clk_layout.addWidget(self.dashboard_live_clk)
        layout.addWidget(clk_tile, 1)

        sync_tile = QFrame()
        sync_tile.setObjectName("Tile")
        sync_layout = QHBoxLayout(sync_tile)
        sync_layout.setContentsMargins(9, 3, 9, 3)
        sync_layout.setSpacing(7)
        sync_layout.addWidget(label("SYNC IN", "TileLabel"))
        self.dashboard_live_sync = label("--", "TileValue")
        sync_layout.addWidget(self.dashboard_live_sync)
        layout.addWidget(sync_tile, 1)

        self.dashboard_live_note = label("Internal timing reference", "SmallGrey")
        layout.addWidget(self.dashboard_live_note)

        self._update_other_live_parameter()
        return frame

    # ========================================================
    # SYNC
    # ========================================================

    def sync_card(self):
        """TG10-style Synchronization section with the exact 3-column geometry.

        Geometry:

            Internal + One shot trigger | External SINGLE IN | External DUAL IN

        The External SINGLE IN and External DUAL IN panels occupy the full
        vertical height.  Their height is equal to the combined height of
        the Internal and One shot trigger panels on the left.
        """
        frame, body = make_card("∿", "Synchronization (Sync)")

        # ------------------------------------------------------------
        # TOP ROW — four synchronization mode selectors
        # ------------------------------------------------------------
        mode_group = QButtonGroup(self)
        mode_group.setExclusive(True)
        self.sync_mode_group = mode_group

        mode_names = [
            "Internal",
            "External SINGLE IN",
            "External DUAL IN",
            "One shot trigger",
        ]

        # Keep ALL FOUR synchronization modes on ONE horizontal row.
        # Fixed widths prevent Qt from wrapping the long labels into a
        # second row when the Sync card is resized.
        mode_row = QHBoxLayout()
        mode_row.setContentsMargins(2, 0, 2, 4)
        mode_row.setSpacing(8)

        mode_buttons = []
        mode_widths = [
            92,   # Internal
            165,  # External SINGLE IN
            165,  # External DUAL IN
            145,  # One shot trigger
        ]

        for idx, (name, width) in enumerate(zip(mode_names, mode_widths)):
            radio = QRadioButton(name)
            radio.setObjectName("SyncModeRadio")
            radio.setChecked(idx == 0)
            radio.setCursor(Qt.PointingHandCursor)
            radio.setFixedWidth(width)
            radio.setMinimumHeight(30)
            radio.setMaximumHeight(30)
            radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            mode_group.addButton(radio, idx)
            mode_buttons.append(radio)
            mode_row.addWidget(radio, 0)

        # Consume any remaining horizontal space without moving the
        # synchronization options onto another row.
        mode_row.addStretch(1)

        self.internal_radio, self.single_radio, self.dual_radio, self.oneshot_radio = mode_buttons
        mode_group.idClicked.connect(self._sync_mode_selected)
        body.addLayout(mode_row)

        # ------------------------------------------------------------
        # CONTENT — 3 columns
        #
        #   Column 0: Internal + One shot trigger
        #   Column 1: External SINGLE IN (full height)
        #   Column 2: External DUAL IN (full height)
        #
        # The two right-hand panels are deliberately the same total
        # height as the two stacked panels on the left.
        # ------------------------------------------------------------
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(10)

        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(8)

        def style_sync_panel(panel, title_text, icon_text="◈"):
            outer = panel.layout()
            old_header = outer.itemAt(0).widget()
            old_header.deleteLater()

            new_header = QWidget()
            new_header_layout = QHBoxLayout(new_header)
            new_header_layout.setContentsMargins(10, 5, 8, 3)
            new_header_layout.setSpacing(5)

            icon = QLabel(icon_text)
            icon.setObjectName("SyncPanelIcon")
            icon.setStyleSheet(
                "color:#1976b9; font-size:12px; font-weight:800; background:transparent;"
            )
            title = QLabel(title_text)
            title.setObjectName("SyncPanelTitle")
            title.setStyleSheet(
                "color:#124a7c; font-size:12px; font-weight:800; background:transparent;"
            )
            new_header_layout.addWidget(icon)
            new_header_layout.addWidget(title)
            new_header_layout.addStretch()
            outer.insertWidget(0, new_header)

        # ------------------------------------------------------------
        # INTERNAL — left column, upper half
        # ------------------------------------------------------------
        internal, il = make_subpanel("")
        style_sync_panel(internal, "Internal", "◈")

        # The TG10 internal clock is a fixed 100 MHz timing reference.
        # It is displayed as a read-only value, not a spin box, because
        # there is no user-adjustable increase/decrease control here.
        self.internal_freq = QLineEdit("100.000 MHz")
        self.internal_freq.setReadOnly(True)
        self.internal_freq.setAlignment(Qt.AlignCenter)
        self.internal_freq.setFixedHeight(27)
        self.internal_freq.setMinimumWidth(105)

        il.addWidget(label("Clock", "FieldLabel"))
        il.addWidget(self.internal_freq)
        # The internal panel intentionally shows only the fixed 100 MHz clock.
        # Do not add a separate "Timing reference" line here.
        il.addStretch()

        # ------------------------------------------------------------
        # ONE SHOT TRIGGER — left column, lower half
        # ------------------------------------------------------------
        oneshot, ol = make_subpanel("")
        style_sync_panel(oneshot, "One shot trigger", "◈")

        self.software_trigger = QRadioButton("Software")
        self.smart_trigger = QRadioButton("Smart")
        self.software_trigger.setChecked(False)

        self.one_shot_group = QButtonGroup(oneshot)
        self.one_shot_group.setExclusive(True)
        self.one_shot_group.addButton(self.software_trigger)
        self.one_shot_group.addButton(self.smart_trigger)

        # Place Software and Smart vertically, centered in the One shot
        # trigger panel, matching the user's sketch.
        trigger_column = QVBoxLayout()
        trigger_column.setContentsMargins(0, 2, 0, 2)
        trigger_column.setSpacing(4)
        trigger_column.setAlignment(Qt.AlignCenter)

        # Keep both radio buttons on one straight vertical axis while the
        # whole group remains centered inside the One shot trigger panel.
        trigger_stack = QWidget()
        trigger_stack.setFixedWidth(105)
        trigger_stack_layout = QVBoxLayout(trigger_stack)
        trigger_stack_layout.setContentsMargins(0, 0, 0, 0)
        trigger_stack_layout.setSpacing(4)
        trigger_stack_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        trigger_stack_layout.addWidget(self.software_trigger)
        trigger_stack_layout.addWidget(self.smart_trigger)

        trigger_column.addWidget(trigger_stack, 0, Qt.AlignCenter)

        ol.setContentsMargins(8, 2, 8, 2)
        ol.setSpacing(2)
        ol.addStretch(1)
        ol.addLayout(trigger_column)
        ol.addStretch(1)

        # ------------------------------------------------------------
        # EXTERNAL SINGLE IN — full-height middle column
        # ------------------------------------------------------------
        single, sl = make_subpanel("")
        style_sync_panel(single, "External SINGLE IN", "◈")

        sl.setSpacing(9)

        sl.addWidget(label("Source", "FieldLabel"))

        source_row = QHBoxLayout()
        source_row.setContentsMargins(0, 0, 0, 0)
        source_row.setSpacing(14)

        self.single_source_group = QButtonGroup(single)
        self.single_source_group.setExclusive(True)

        self.single_source_sync_radio = QRadioButton("SYNC IN")
        self.single_source_clk_radio = QRadioButton("CLK IN")
        self.single_source_clk_radio.setChecked(False)

        self.single_source_group.addButton(self.single_source_sync_radio, 0)
        self.single_source_group.addButton(self.single_source_clk_radio, 1)
        source_row.addWidget(self.single_source_sync_radio)
        source_row.addWidget(self.single_source_clk_radio)
        source_row.addStretch()
        sl.addLayout(source_row)

        rate_label_row = QHBoxLayout()
        rate_label_row.setContentsMargins(0, 4, 0, 0)
        rate_label_row.addWidget(label("Rate", "FieldLabel"))
        rate_label_row.addStretch()
        sl.addLayout(rate_label_row)

        # Numeric rate with the unit directly underneath, so MHz is clearly
        # visible below the value instead of beside it.
        rate_block = QVBoxLayout()
        rate_block.setContentsMargins(0, 0, 0, 0)
        rate_block.setSpacing(2)

        self.external_rate = QDoubleSpinBox()
        self.external_rate.setDecimals(6)
        self.external_rate.setValue(99.99)
        self.external_rate.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.single_rate_unit = combo(["MHz", "kHz", "Hz"], 70)
        self.single_rate_unit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        rate_block.addWidget(self.external_rate)
        unit_row = QHBoxLayout()
        unit_row.setContentsMargins(0, 0, 0, 0)
        unit_row.setSpacing(0)
        # Keep MHz directly below the numeric field, aligned to its left edge.
        unit_row.addWidget(self.single_rate_unit, 0, Qt.AlignLeft)
        unit_row.addStretch(1)
        rate_block.addLayout(unit_row)

        sl.addLayout(rate_block)
        sl.addStretch()

        # ------------------------------------------------------------
        # EXTERNAL DUAL IN — full-height right column
        # ------------------------------------------------------------
        dual, dl = make_subpanel("")
        style_sync_panel(dual, "External DUAL IN", "◈")

        # Each Dual-IN value gets its unit directly UNDER the numeric field,
        # matching the requested TG10 sketch:
        #
        #   SYNC IN   [1.000000]
        #                [MHz]
        #
        #   CLK IN    [99.990000]
        #                [MHz]
        def dual_value_block(spin, unit_combo):
            block = QVBoxLayout()
            block.setContentsMargins(0, 0, 0, 0)
            block.setSpacing(2)
            block.addWidget(spin)
            block.addWidget(unit_combo, 0, Qt.AlignLeft)
            return block

        r3 = QHBoxLayout()
        r3.setContentsMargins(0, 0, 0, 0)
        r3.setSpacing(4)
        r3.addWidget(label("SYNC IN", "FieldLabel"))
        self.dual_sync_input = QDoubleSpinBox()
        self.dual_sync_input.setDecimals(6)
        self.dual_sync_input.setValue(1.0)
        self.dual_sync_unit = combo(["MHz", "kHz", "Hz"], 70)
        r3.addLayout(dual_value_block(
            self.dual_sync_input,
            self.dual_sync_unit
        ), 1)
        dl.addLayout(r3)

        r4 = QHBoxLayout()
        r4.setContentsMargins(0, 0, 0, 0)
        r4.setSpacing(4)
        r4.addWidget(label("CLK IN", "FieldLabel"))
        self.dual_clk_input = QDoubleSpinBox()
        self.dual_clk_input.setDecimals(6)
        self.dual_clk_input.setValue(99.99)
        self.dual_clk_unit = combo(["MHz", "kHz", "Hz"], 70)
        r4.addLayout(dual_value_block(
            self.dual_clk_input,
            self.dual_clk_unit
        ), 1)
        dl.addLayout(r4)
        dl.addStretch()

        # ------------------------------------------------------------
        # Assemble the exact geometry.
        # ------------------------------------------------------------
        left_column.addWidget(internal, 1)
        left_column.addWidget(oneshot, 1)

        content.addLayout(left_column, 1)
        content.addWidget(single, 1.8)
        content.addWidget(dual, 2.0)

        body.addLayout(content, 1)

        self.sync_panels = {
            "Internal": internal,
            "External SINGLE IN": single,
            "External DUAL IN": dual,
            "One shot trigger": oneshot,
        }

        # ------------------------------------------------------------
        # Signal connections
        # ------------------------------------------------------------
        self.single_source_group.idClicked.connect(
            self._single_source_selected
        )
        self.single_rate_unit.currentTextChanged.connect(
            self._update_single_rate_range
        )
        self.external_rate.valueChanged.connect(
            self._update_other_live_parameter
        )
        self.dual_sync_unit.currentTextChanged.connect(
            self._update_dual_rate_ranges
        )
        self.dual_clk_unit.currentTextChanged.connect(
            self._update_dual_rate_ranges
        )
        self.dual_sync_input.valueChanged.connect(
            self._update_other_live_parameter
        )
        self.dual_clk_input.valueChanged.connect(
            self._update_other_live_parameter
        )

        self._update_single_rate_range()
        self._update_dual_rate_ranges()
        self._sync_mode_selected(0)
        self._update_other_live_parameter()

        add_card_action(
            frame,
            lambda: (
                self._commit_sync_to_monitor(),
                self.set_status(f"Sync set: {self.sync_mode}")
            )
        )
        return frame

    def _single_source_selected(self, index):
        """Update the selected External SINGLE IN source."""
        self._update_single_rate_range()
        self._update_other_live_parameter()

    def _single_source_name(self):
        if hasattr(self, "single_source_clk_radio") and self.single_source_clk_radio.isChecked():
            return "CLK IN"
        if hasattr(self, "single_source_sync_radio") and self.single_source_sync_radio.isChecked():
            return "SYNC IN"
        return None

    def _sync_mode_selected(self, index):
        names = [
            "Internal",
            "External SINGLE IN",
            "External DUAL IN",
            "One shot trigger",
        ]

        if index < 0 or index >= len(names):
            return

        self.sync_mode = names[index]

        # A sub-option belongs to its synchronization mode. When that mode
        # is not selected, do not leave an old/default radio selection visible.
        if hasattr(self, "software_trigger") and self.sync_mode != "One shot trigger":
            self.software_trigger.setChecked(False)
            self.smart_trigger.setChecked(False)

        if hasattr(self, "single_source_sync_radio") and self.sync_mode != "External SINGLE IN":
            self.single_source_sync_radio.setChecked(False)
            self.single_source_clk_radio.setChecked(False)

        # Only the selected mode can be operated. The other three panels
        # remain visible but all of their controls are disabled.
        for name, panel in self.sync_panels.items():
            active = name == self.sync_mode
            panel.setEnabled(active)

            if active:
                panel.setStyleSheet("")
            else:
                panel.setStyleSheet(
                    "QFrame#SubPanel { "
                    "background:#f6f8fa; "
                    "border:1px solid #dfe5ea; "
                    "}"
                )

            for child in panel.findChildren(QLabel):
                if child.objectName() == "SyncPanelIcon":
                    child.setStyleSheet(
                        "color:#1976b9; font-size:12px; font-weight:800; background:transparent;"
                        if active else
                        "color:#a8b5c1; font-size:12px; font-weight:800; background:transparent;"
                    )
                elif child.objectName() == "SyncPanelTitle":
                    child.setStyleSheet(
                        "color:#124a7c; font-size:12px; font-weight:800; background:transparent;"
                        if active else
                        "color:#9aa7b3; font-size:12px; font-weight:800; background:transparent;"
                    )

        self._update_other_live_parameter()

    def _run_existing_sync_sequence(self, sequence_name):
        """Run one of the existing TG10 Sync sequences from the backend.

        No CAN ID, register address, payload, or sequence is invented here.
        The GUI only selects a sequence that already exists in
        Sy4000_can_control_org.py.
        """
        if not self.connection_state or self.serial_connection is None:
            raise RuntimeError("TG10 is not connected. Open COM and connect first.")

        backend = self.can_backend
        if backend is None:
            raise RuntimeError("TG10 CAN backend is not loaded.")

        sequence = getattr(backend, sequence_name, None)
        if sequence is None:
            raise AttributeError(
                f"Existing backend sequence '{sequence_name}' was not found."
            )

        run_sequence = getattr(backend, "run_sequence", None)
        if not callable(run_sequence):
            raise AttributeError(
                "Sy4000_can_control_org.run_sequence() is not available."
            )

        run_sequence(self.serial_connection, sequence)

    def _read_sync_hardware_status(self):
        """Read the existing readv1 status dictionary after a Sync write."""
        if not self.connection_state or self.serial_connection is None:
            raise RuntimeError("TG10 is not connected.")

        reader = self.can_reader
        if reader is None:
            raise RuntimeError("readv1 backend is not loaded.")

        read_status = getattr(reader, "read_status", None)
        if not callable(read_status):
            raise AttributeError("readv1.read_status() is not available.")

        return read_status(self.serial_connection, show=False)

    @staticmethod
    def _format_hz(value):
        if value is None:
            return "--"
        try:
            value = float(value)
        except (TypeError, ValueError):
            return str(value)

        if value >= 1e6:
            return f"{value / 1e6:.6f} MHz"
        if value >= 1e3:
            return f"{value / 1e3:.6f} kHz"
        return f"{value:.3f} Hz"

    def _apply_hardware_sync_status(self, status):
        """Reflect the readv1 hardware dictionary in the Sync live displays."""
        if not isinstance(status, dict):
            raise RuntimeError("readv1.read_status() did not return a dictionary.")

        mode = status.get("mode")
        clk = status.get("clk_in_hz")
        sync = status.get("sync_in_hz")
        out_hz = status.get("freq_hz")
        ratediv = status.get("ratediv")

        mode_names = {
            "internal": "Internal",
            "ext_clk": "External SINGLE IN",
            "ext_sync": "External SINGLE IN",
            "ext_dual": "External DUAL IN",
            "oneshot": "One shot trigger",
            "smart": "One shot trigger",
        }
        display_mode = mode_names.get(mode, str(mode) if mode else "Unknown")

        # Hardware values, rather than the currently edited GUI spin boxes,
        # are shown after a successful Set/readback cycle.
        if hasattr(self, "other_live_clk"):
            self.other_live_clk.setText(
                "CLK IN: " + self._format_hz(clk)
            )
            self.other_live_sync.setText(
                "SYNC IN: " + self._format_hz(sync)
            )

        if hasattr(self, "monitor_live_clk"):
            self.monitor_live_clk.setText(self._format_hz(clk))
            self.monitor_live_sync.setText(self._format_hz(sync))
            self.monitor_live_note.setText(
                f"Hardware: {display_mode}"
                + (f" | Output: {self._format_hz(out_hz)}" if out_hz else "")
                + (f" | Ratediv: {ratediv}" if ratediv is not None else "")
            )

        if hasattr(self, "dashboard_live_clk"):
            self.dashboard_live_clk.setText(self._format_hz(clk))
            self.dashboard_live_sync.setText(self._format_hz(sync))
            self.dashboard_live_note.setText(
                f"Hardware: {display_mode}"
            )

        # Keep the monitor's committed Sync label aligned with the actual
        # hardware mode. Do not silently change the user's editable controls.
        self.committed_sync_mode = display_mode
        self.hardware_sync_status = status

        return display_mode

    def _set_sync_hardware(self):
        """Apply the currently selected Sync mode using existing backend data."""
        if not self.connection_state:
            QMessageBox.warning(
                self,
                "TG10 Sync",
                "Connect to TG10 before pressing Sync → Set."
            )
            return

        mode = getattr(self, "sync_mode", "Internal")
        sequence_name = None
        detail = mode

        if mode == "Internal":
            sequence_name = "INTERNAL_100MHz_SEQUENCE"

        elif mode == "External SINGLE IN":
            source = self._single_source_name()

            if source == "CLK IN":
                sequence_name = "EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE"
                detail = "External SINGLE IN → CLK IN"
            elif source == "SYNC IN":
                sequence_name = "EXTERNALSINGLEIN_SYNCIN_10MHZ_SEQUENCE"
                detail = "External SINGLE IN → SYNC IN"
            else:
                QMessageBox.warning(
                    self,
                    "TG10 Sync",
                    "Select CLK IN or SYNC IN for External SINGLE IN."
                )
                return

        elif mode == "External DUAL IN":
            sequence_name = "EXTERNALDUALIN_CLKIN_100MHZ_SYNCIN_20MHZ_SEQUENCE"
            detail = "External DUAL IN"

        elif mode == "One shot trigger":
            if hasattr(self, "software_trigger") and self.software_trigger.isChecked():
                sequence_name = "ONESHOT_TRIGGER_SOFTWARETRIG"
                detail = "One shot trigger → Software"
            elif hasattr(self, "smart_trigger") and self.smart_trigger.isChecked():
                sequence_name = "ONESHOT_TRIGGER_SMARTTRIG"
                detail = "One shot trigger → Smart"
            else:
                QMessageBox.warning(
                    self,
                    "TG10 Sync",
                    "Select Software or Smart trigger for One shot trigger."
                )
                return

        if sequence_name is None:
            QMessageBox.warning(
                self,
                "TG10 Sync",
                f"No existing backend sequence is mapped for '{mode}'."
            )
            return

        try:
            self.set_status(f"Applying Sync: {detail} …")
            QApplication.processEvents()

            self._run_existing_sync_sequence(sequence_name)

            # Read the actual TG10 state after the write. This is the
            # verification step required before trusting GUI state.
            status = self._read_sync_hardware_status()
            detected = self._apply_hardware_sync_status(status)

            self._update_monitor_values()
            self.set_status(
                f"Sync applied: {detail} | TG10 readback: {detected}"
            )

        except Exception as exc:
            self.set_status("Sync apply failed")
            QMessageBox.critical(
                self,
                "TG10 Sync Error",
                f"Could not apply the existing TG10 Sync sequence.\n\n"
                f"Sequence: {sequence_name}\n"
                f"Error: {exc}"
            )

    def _commit_sync_to_monitor(self):
        self.committed_sync_mode = self.sync_mode
        self._update_monitor_values()

    def _update_other_live_parameter(self):
        """Update Other -> Live parameter and the dashboard Live strip."""
        mode = getattr(self, "sync_mode", "Internal")

        if mode == "External SINGLE IN":
            source = self._single_source_name()
            rate = f"{self.external_rate.value():.6f} {self.single_rate_unit.currentText()}"
            if source == "CLK IN":
                clk_text = rate
                sync_text = "--"
            elif source == "SYNC IN":
                clk_text = "--"
                sync_text = rate
            else:
                clk_text = "--"
                sync_text = "--"
            note = "External SINGLE IN"

        elif mode == "External DUAL IN":
            clk_text = f"{self.dual_clk_input.value():.6f} {self.dual_clk_unit.currentText()}"
            sync_text = f"{self.dual_sync_input.value():.6f} {self.dual_sync_unit.currentText()}"
            note = "External DUAL IN"

        elif mode == "Internal":
            clk_text = "100.000 MHz"
            sync_text = "--"
            note = "Internal timing reference"

        else:
            clk_text = "--"
            sync_text = "--"
            note = "One shot trigger"

        # Existing Other -> Live parameter page.
        if hasattr(self, "other_live_clk"):
            self.other_live_clk.setText(
                "CLK IN: " + clk_text if clk_text != "--" else "CLK IN: --"
            )
            self.other_live_sync.setText(
                "SYNC IN: " + sync_text if sync_text != "--" else "SYNC IN: --"
            )

        # Live parameter display below the Monitor output table.
        if hasattr(self, "monitor_live_clk"):
            self.monitor_live_clk.setText(clk_text)
            self.monitor_live_sync.setText(sync_text)
            self.monitor_live_note.setText(note)

        # Retain compatibility with the older dashboard live widgets if
        # another page creates them.
        if hasattr(self, "dashboard_live_clk"):
            self.dashboard_live_clk.setText(clk_text)
            self.dashboard_live_sync.setText(sync_text)
            self.dashboard_live_note.setText(note)

    def _update_single_rate_range(self):
        if not hasattr(self, "external_rate"):
            return
        source = self._single_source_name()
        unit = self.single_rate_unit.currentText()
        ranges = ({"MHz": (10.0,100.0), "kHz": (10000.0,100000.0), "Hz": (1e7,1e8)}
                   if source == "CLK IN" else
                   {"MHz": (1e-5,20.0), "kHz": (0.01,20000.0), "Hz": (0.01,2e7)})
        lo, hi = ranges[unit]
        self.external_rate.setRange(lo, hi)
        self.external_rate.setValue(min(max(self.external_rate.value(), lo), hi))
        self._update_other_live_parameter()

    def _update_dual_rate_ranges(self):
        if not hasattr(self, "dual_sync_input"):
            return
        sync = {"MHz":(1e-5,20.0),"kHz":(0.01,20000.0),"Hz":(0.01,2e7)}
        clk = {"MHz":(10.0,100.0),"kHz":(10000.0,100000.0),"Hz":(1e7,1e8)}
        for widget, unit, ranges in ((self.dual_sync_input,self.dual_sync_unit,sync),(self.dual_clk_input,self.dual_clk_unit,clk)):
            lo,hi=ranges[unit.currentText()]; widget.setRange(lo,hi); widget.setValue(min(max(widget.value(),lo),hi))
        self._update_other_live_parameter()


    # ========================================================
    # FREQUENCY
    # ========================================================

    def frequency_card(self):

        frame, body = make_card("∿", "Frequency / Period (Freq)")

        selector = QHBoxLayout(); selector.setSpacing(12)
        self.frequency_group = QButtonGroup(self); self.frequency_group.setExclusive(True)
        frequency = QRadioButton("Frequency")
        period = QRadioButton("Period")
        self.frequency_group.addButton(frequency, 0); self.frequency_group.addButton(period, 1)
        frequency.setChecked(True)
        selector.addWidget(frequency); selector.addWidget(period); selector.addStretch()
        self.frequency_mode = "Frequency"
        self.frequency_group.idClicked.connect(lambda i: self._frequency_mode_selected(i))
        body.addLayout(selector)

        grid = QGridLayout(); grid.setContentsMargins(0, 2, 0, 0); grid.setHorizontalSpacing(5); grid.setVerticalSpacing(4)
        grid.addWidget(label("Frequency", "FieldLabel", bold=True), 0, 0)
        self.freq_value = QDoubleSpinBox(); self.freq_value.setDecimals(8); self.freq_value.setRange(1e-8,20.0); self.freq_value.setValue(1.0)
        self.freq_unit = combo(["MHz","kHz","Hz"], 72)
        self.freq_unit.setMinimumWidth(72)
        self.freq_unit.setStyleSheet("""QComboBox { font-size: 10px; font-weight: 600; padding: 3px 8px; } QComboBox::drop-down { width: 18px; }""")
        grid.addWidget(self.freq_value,0,1); grid.addWidget(self.freq_unit,0,2)
        grid.addWidget(label("Period", "FieldLabel", bold=True),1,0)
        self.period_value = QDoubleSpinBox(); self.period_value.setDecimals(8); self.period_value.setRange(0.05,1e8); self.period_value.setValue(1.0)
        self.period_unit = combo(["µs","ns","ms","s"], 58)
        grid.addWidget(self.period_value,1,1); grid.addWidget(self.period_unit,1,2)
        grid.setColumnStretch(1,1)
        body.addLayout(grid)

        self.freq_value.valueChanged.connect(self._frequency_changed)
        self.freq_unit.currentTextChanged.connect(self._frequency_unit_changed)
        self.period_value.valueChanged.connect(self._period_changed)
        self.period_unit.currentTextChanged.connect(self._period_unit_changed)
        self._updating_frequency = False
        self._updating_period = False
        self._set_frequency_hz(1_000_000.0)

        # The mathematical relation is used internally by the GUI; the
        # formula is intentionally not shown on the instrument face.
        add_card_action(
            frame,
            lambda: (
                self._commit_frequency_to_monitor(),
                self.set_status(
                    f"Frequency set: {self.freq_value.text()} {self.freq_unit.currentText()}"
                )
            )
        )
        return frame

    def _frequency_mode_selected(self, index):
        self.frequency_mode = "Frequency" if index == 0 else "Period"

    def _frequency_unit_changed(self, new_unit):
        if getattr(self, "_updating_frequency", False):
            return
        hz = getattr(self, "current_frequency_hz", self._freq_to_hz())
        factor = {"Hz":1.0, "kHz":1e3, "MHz":1e6}[new_unit]
        self._updating_frequency = True
        self.freq_value.setValue(hz / factor)
        self._updating_frequency = False
        self._update_frequency_range()

    def _period_unit_changed(self, new_unit):
        if getattr(self, "_updating_period", False):
            return
        sec = getattr(self, "current_period_s", self._period_to_s())
        factor = {"s":1.0, "ms":1e-3, "µs":1e-6, "ns":1e-9}[new_unit]
        self._updating_period = True
        self.period_value.setValue(sec / factor)
        self._updating_period = False
        self._update_period_range()

    def _freq_to_hz(self):
        factor = {"Hz":1.0,"kHz":1e3,"MHz":1e6}[self.freq_unit.currentText()]
        return self.freq_value.value()*factor

    def _period_to_s(self):
        factor = {"s":1.0,"ms":1e-3,"µs":1e-6,"ns":1e-9}[self.period_unit.currentText()]
        return self.period_value.value()*factor

    def _set_frequency_hz(self, hz):
        hz=max(0.01,min(20e6,float(hz)))
        self.current_frequency_hz=hz; self.current_period_s=1.0/hz
        unit=self.freq_unit.currentText(); factor={"Hz":1,"kHz":1e3,"MHz":1e6}[unit]
        self._updating_frequency=True; self.freq_value.setValue(hz/factor); self._updating_frequency=False
        self._set_period_seconds(1.0/hz)

    def _set_period_seconds(self, sec):
        sec=max(50e-9,min(100.0,float(sec)))
        self.current_period_s=sec
        unit=self.period_unit.currentText(); factor={"s":1,"ms":1e-3,"µs":1e-6,"ns":1e-9}[unit]
        self._updating_period=True; self.period_value.setValue(sec/factor); self._updating_period=False

    def _frequency_changed(self, *_):
        if getattr(self,"_updating_frequency",False): return
        self._update_frequency_range()
        self._set_frequency_hz(self._freq_to_hz())

    def _period_changed(self, *_):
        if getattr(self,"_updating_period",False): return
        self._update_period_range()
        sec=self._period_to_s(); self.current_period_s=sec; self._set_frequency_from_period(sec)

    def _set_frequency_from_period(self, sec):
        sec=max(50e-9,min(100.0,float(sec))); hz=1.0/sec
        hz=max(0.01,min(20e6,hz)); self.current_frequency_hz=hz
        unit=self.freq_unit.currentText(); factor={"Hz":1,"kHz":1e3,"MHz":1e6}[unit]
        self._updating_frequency=True; self.freq_value.setValue(hz/factor); self._updating_frequency=False

    def _commit_frequency_to_monitor(self):
        self.committed_frequency_hz = self._freq_to_hz()
        self.committed_period_s = self._period_to_s()
        self.committed_freq_unit = self.freq_unit.currentText()
        self.committed_period_unit = self.period_unit.currentText()
        self._update_monitor_values()

    def _update_frequency_range(self):
        if not hasattr(self,"freq_value"): return
        ranges={"MHz":(1e-8,20.0),"kHz":(1e-5,20000.0),"Hz":(0.01,2e7)}
        lo,hi=ranges[self.freq_unit.currentText()]; self.freq_value.setRange(lo,hi)

    def _update_period_range(self):
        if not hasattr(self,"period_value"): return
        ranges={"s":(50e-9,100.0),"ms":(50e-6,100000.0),"µs":(0.05,1e8),"ns":(50.0,1e11)}
        lo,hi=ranges[self.period_unit.currentText()]; self.period_value.setRange(lo,hi)

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def config_card(self):
        """Configuration 1/2 card arranged like the user's sketch.

        Layout:
            LEFT COLUMN  : Normal / Gate / Frequency divider
            RIGHT COLUMN : Burst (full height)

        Keeping all four mode boxes visible removes the large empty area that
        appeared when the selected mode had few/no dynamic controls.
        """
        frame, body = make_card("⚙", "Configuration 1 / 2")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setFixedHeight(300)
        self._config_card_frame = frame

        body.setContentsMargins(12, 0, 12, 8)
        body.setSpacing(4)

        self.config_settings = {
            "Config 1": {
                "mode": "Normal",
                "gate": "GATE",
                "burst_source": "SYNC IN",
                "burst_count": 1,
                "divider": 1,
            }
        }
        self.active_config_name = "Config 1"
        self.committed_config_name = "Config 1"

        # ------------------------------------------------------------
        # MODE label above all four mutually-exclusive mode boxes.
        # ------------------------------------------------------------
        body.addWidget(label("Mode", "FieldLabel", bold=True))

        # ------------------------------------------------------------
        # Four mode boxes, arranged exactly as the sketch:
        #
        #   ┌──────────────┐   ┌─────────────────────────────┐
        #   │ ○ Normal     │   │ ○ Burst                    │
        #   └──────────────┘   │ Burst trigger               │
        #   ┌──────────────┐   │ ○ SYNC IN  ○ GATE           │
        #   │ ○ Gate       │   │ ○ nGATE   ○ Software        │
        #   │ ○ GATE       │   │ Burst count                 │
        #   │ ○ nGATE      │   │ [                       ]   │
        #   └──────────────┘   └─────────────────────────────┘
        #   ┌──────────────┐
        #   │ Frequency    │
        #   │ divider      │
        #   │ Division ... │
        #   │ [          ] │
        #   └──────────────┘
        # ------------------------------------------------------------
        content_grid = QGridLayout()
        content_grid.setContentsMargins(0, 0, 0, 0)
        content_grid.setHorizontalSpacing(8)
        content_grid.setVerticalSpacing(6)
        content_grid.setColumnStretch(0, 1)
        content_grid.setColumnStretch(1, 2)
        content_grid.setRowStretch(0, 1)
        content_grid.setRowStretch(1, 1)
        content_grid.setRowStretch(2, 1)

        self.config_mode_group = QButtonGroup(self)
        self.config_mode_group.setExclusive(True)
        self.config_mode_buttons = {}

        def mode_box(mode_name, parent=None):
            box = QFrame(parent)
            box.setObjectName("ConfigModeBox")
            box.setStyleSheet("""
                QFrame#ConfigModeBox {
                    background: #ffffff;
                    border: 1px solid #c5d4e2;
                    border-radius: 4px;
                }
            """)
            layout = QVBoxLayout(box)
            layout.setContentsMargins(10, 7, 10, 7)
            layout.setSpacing(4)
            return box, layout

        def add_mode_radio(layout, mode_name):
            radio = QRadioButton(mode_name)
            radio.setObjectName("ConfigModeRadio")
            radio.setCursor(Qt.PointingHandCursor)
            radio.setMinimumHeight(25)
            self.config_mode_group.addButton(radio)
            self.config_mode_buttons[mode_name] = radio
            layout.addWidget(radio)
            return radio

        # ---------------- NORMAL ----------------
        normal_box, normal_layout = mode_box("Normal")
        add_mode_radio(normal_layout, "Normal")
        normal_layout.addStretch()
        content_grid.addWidget(normal_box, 0, 0)

        # ---------------- GATE ----------------
        gate_box, gate_layout = mode_box("Gate")
        add_mode_radio(gate_layout, "Gate")

        gate_group = QButtonGroup(gate_box)
        gate_group.setExclusive(True)
        gate_row = QHBoxLayout()
        gate_row.setContentsMargins(2, 0, 0, 0)
        gate_row.setSpacing(4)

        self.config_gate_buttons = {}
        self.config_gate_group = gate_group
        for option in ("GATE", "nGATE"):
            radio = QRadioButton(option)
            radio.setMinimumHeight(24)
            radio.setFixedWidth(82 if option == "GATE" else 88)
            # Do not pre-select a Gate sub-option while Normal is selected.
            # The sub-option is selected only when Gate mode is activated.
            radio.setChecked(False)
            gate_group.addButton(radio)
            self.config_gate_buttons[option] = radio
            radio.toggled.connect(
                lambda checked, value=option:
                self._save_config_gate(value, checked)
            )
            gate_row.addWidget(radio)
        gate_row.addStretch()
        gate_layout.addLayout(gate_row)
        gate_layout.addStretch()
        content_grid.addWidget(gate_box, 1, 0)

        # ---------------- FREQUENCY DIVIDER ----------------
        divider_box, divider_layout = mode_box("Frequency divider")
        add_mode_radio(divider_layout, "Frequency divider")

        divider_layout.addWidget(
            label("Division of output frequency", "FieldLabel", bold=True)
        )

        divider_row = QHBoxLayout()
        divider_row.setContentsMargins(4, 0, 0, 0)
        divider_row.setSpacing(7)

        self.config_divider_widget = QSpinBox()
        self.config_divider_widget.setRange(1, 32767)
        self.config_divider_widget.setValue(
            self.config_settings["Config 1"]["divider"]
        )
        self.config_divider_widget.setFixedWidth(150)
        self.config_divider_widget.valueChanged.connect(
            self._save_config_divider
        )
        divider_row.addWidget(self.config_divider_widget)
        divider_row.addStretch()
        divider_layout.addLayout(divider_row)
        divider_layout.addStretch()
        content_grid.addWidget(divider_box, 2, 0)

        # ---------------- BURST (FULL RIGHT COLUMN) ----------------
        burst_box, burst_layout = mode_box("Burst")
        add_mode_radio(burst_layout, "Burst")

        burst_layout.addSpacing(5)
        burst_layout.addWidget(
            label("Burst trigger", "FieldLabel", bold=True)
        )

        burst_group = QButtonGroup(burst_box)
        burst_group.setExclusive(True)
        self.config_burst_buttons = {}
        self.config_burst_group = burst_group

        # Two rows, as in the sketch.
        trigger_grid = QGridLayout()
        trigger_grid.setContentsMargins(4, 0, 4, 0)
        trigger_grid.setHorizontalSpacing(18)
        trigger_grid.setVerticalSpacing(4)

        options = [
            ("SYNC IN", 0, 0),
            ("GATE", 0, 1),
            ("nGATE", 1, 0),
            ("Software", 1, 1),
        ]
        for option, row, col in options:
            radio = QRadioButton(option)
            radio.setMinimumHeight(26)
            radio.setMinimumWidth(82 if option in ("GATE", "nGATE") else 92)
            # Do not pre-select a Burst trigger while Normal is selected.
            # The trigger is selected only when Burst mode is activated.
            radio.setChecked(False)
            burst_group.addButton(radio)
            self.config_burst_buttons[option] = radio
            radio.toggled.connect(
                lambda checked, value=option:
                self._save_config_burst_source(value, checked)
            )
            trigger_grid.addWidget(radio, row, col)

        burst_layout.addLayout(trigger_grid)
        burst_layout.addSpacing(8)
        burst_layout.addWidget(
            label("Burst count", "FieldLabel", bold=True)
        )

        count_row = QHBoxLayout()
        count_row.setContentsMargins(4, 0, 4, 0)
        count_row.setSpacing(8)

        self.burst_count_widget = QSpinBox()
        self.burst_count_widget.setRange(1, 65535)
        self.burst_count_widget.setValue(
            self.config_settings["Config 1"]["burst_count"]
        )
        self.burst_count_widget.setFixedWidth(180)
        self.burst_count_widget.valueChanged.connect(
            self._save_config_burst_count
        )
        self.config_burst_count_row = count_row
        count_row.addWidget(self.burst_count_widget)
        count_row.addStretch()
        burst_layout.addLayout(count_row)
        burst_layout.addStretch()
        content_grid.addWidget(burst_box, 0, 1, 3, 1)

        body.addLayout(content_grid, 1)

        add_card_action(
            frame,
            lambda: (
                self._commit_config_to_monitor(),
                self.set_status(
                    f'Config 1/2 set: {self.config_settings["Config 1"]["mode"]}'
                )
            )
        )

        self.config_mode_group.buttonClicked.connect(
            self._configuration_mode_radio_clicked
        )

        self.config_mode_buttons["Normal"].setChecked(True)
        self._configuration_mode_changed("Normal")
        return frame

    def _set_config_card_height(self, mode):
        """Keep the Configuration card compact instead of filling dashboard row 0."""
        if not hasattr(self, "_config_card_frame"):
            return

        # Content-sized heights: Normal is shortest; Burst needs extra room.
        heights = {
            "Normal": 205,
            "Gate": 255,
            "Burst": 285,
            "Frequency divider": 255,
        }
        self._config_card_frame.setFixedHeight(heights.get(mode, 255))
        self._config_card_frame.updateGeometry()

    def _configuration_mode_radio_clicked(self, button):
        """Handle configuration modes exactly like the Sync mode selector.

        Only one top-level mode may remain checked.  Gate/Burst sub-options
        are cleared whenever their parent mode is not selected.
        """
        if button is None:
            return

        mode = button.text()

        # QButtonGroup should enforce exclusivity, but explicitly clear every
        # other top-level radio as well so the visual state can never show two
        # modes checked at once.
        for radio in self.config_mode_group.buttons():
            if radio is not button:
                radio.blockSignals(True)
                radio.setAutoExclusive(False)
                radio.setChecked(False)
                radio.setAutoExclusive(True)
                radio.blockSignals(False)

        button.blockSignals(True)
        button.setAutoExclusive(False)
        button.setChecked(True)
        button.setAutoExclusive(True)
        button.blockSignals(False)

        self._configuration_mode_changed(mode)

    def _clear_config_dynamic(self):
        while self.config_dynamic_layout.count():
            item = self.config_dynamic_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_config_layout(item.layout())

    def _clear_config_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_config_layout(item.layout())

    def _configuration_mode_changed(self, mode):
        """Enable only the controls belonging to the selected TG10 mode.

        The mode radio buttons are independent of the Gate/Burst option
        radios.  Therefore changing Mode must explicitly clear every
        sub-option from the modes that are not selected, just like the Sync
        section enables only the currently selected Sync mode.
        """
        settings = self.config_settings[self.active_config_name]
        settings["mode"] = mode

        # Keep the four Mode radios mutually exclusive.
        selected_mode = self.config_mode_buttons.get(mode)
        if selected_mode is not None:
            # Force a single visible selection, even if a previous signal or
            # programmatic update left another mode checked.
            for radio in self.config_mode_group.buttons():
                radio.blockSignals(True)
                radio.setAutoExclusive(False)
                radio.setChecked(radio is selected_mode)
                radio.setAutoExclusive(True)
                radio.blockSignals(False)

        def clear_group(group):
            # Force the whole sub-group off before changing enabled state.
            # QButtonGroup exclusivity is disabled temporarily so a stale
            # checked indicator can never be restored by another button.
            if group is None:
                return
            group.setExclusive(False)
            for radio in group.buttons():
                radio.blockSignals(True)
                radio.setChecked(False)
                radio.blockSignals(False)
                radio.setEnabled(False)
                radio.update()
            group.setExclusive(True)

        def select_group(group, desired):
            if group is None:
                return
            group.setExclusive(False)
            for radio in group.buttons():
                radio.blockSignals(True)
                radio.setEnabled(True)
                radio.setChecked(radio is desired)
                radio.blockSignals(False)
                radio.update()
            group.setExclusive(True)

        def clear_radio(radio):
            if radio is None:
                return
            radio.blockSignals(True)
            radio.setAutoExclusive(False)
            radio.setChecked(False)
            radio.setAutoExclusive(True)
            radio.blockSignals(False)
            radio.update()

        def select_radio(radio):
            if radio is None:
                return
            radio.blockSignals(True)
            radio.setAutoExclusive(False)
            radio.setChecked(True)
            radio.setAutoExclusive(True)
            radio.blockSignals(False)
            radio.update()

        # ------------------------------------------------------------
        # GATE options
        # ------------------------------------------------------------
        gate_enabled = mode == "Gate"
        if hasattr(self, "config_gate_group"):
            if not gate_enabled:
                clear_group(self.config_gate_group)
            else:
                desired = self.config_gate_buttons.get(
                    settings.get("gate", "GATE")
                )
                select_group(self.config_gate_group, desired)

        # ------------------------------------------------------------
        # BURST trigger options
        # ------------------------------------------------------------
        burst_enabled = mode == "Burst"
        if hasattr(self, "config_burst_group"):
            if not burst_enabled:
                clear_group(self.config_burst_group)
            else:
                desired = self.config_burst_buttons.get(
                    settings.get("burst_source", "SYNC IN")
                )
                select_group(self.config_burst_group, desired)

        # ------------------------------------------------------------
        # Burst count and Frequency divider controls
        # ------------------------------------------------------------
        if hasattr(self, "burst_count_widget"):
            self.burst_count_widget.setEnabled(burst_enabled)

        divider_enabled = mode == "Frequency divider"
        if hasattr(self, "config_divider_widget"):
            self.config_divider_widget.setEnabled(divider_enabled)

    def _commit_config_to_monitor(self):
        self.committed_config_name = self.active_config_name
        self._update_monitor_values()

    def _save_config_gate(self, value, checked):
        if checked:
            self.config_settings[
                self.active_config_name
]["gate"] = value

    def _save_config_burst_source(self, value, checked):
        if checked:
            self.config_settings[
                self.active_config_name
]["burst_source"] = value

    def _save_config_burst_count(self, value):
        self.config_settings[
            self.active_config_name
        ]["burst_count"] = value

    def _save_config_burst_infinite(self, checked):
        self.config_settings[
            self.active_config_name
        ]["burst_infinite"] = checked

        if hasattr(self, "burst_count_widget"):
            self.burst_count_widget.setEnabled(not checked)

    def _save_config_divider(self, value):
        self.config_settings[
            self.active_config_name
        ]["divider"] = value

    # ========================================================
    # OUTPUT
    # ========================================================

    def output_card(self):

        frame, body = make_card("▣", "Output")
        body.setContentsMargins(12, 0, 12, 8)
        body.setSpacing(5)

        # ------------------------------------------------------------
        # OUTPUT SELECTION / LOGIC
        # ------------------------------------------------------------
        top = QGridLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setHorizontalSpacing(7)
        top.setVerticalSpacing(3)

        top.addWidget(label("Channel:", "FieldLabel", True), 0, 0)
        self.output_channel = combo(
            [
                *[f"OUT{i}" for i in range(8)],
                "AN OUT", "COM TRIG", "PRE TRIG"
            ],
            88
        )
        self.output_channel.currentTextChanged.connect(self._output_channel_changed)
        top.addWidget(self.output_channel, 0, 1)

        top.addWidget(label("Logic:", "FieldLabel", True), 0, 2)
        self.output_logic = combo(["NA", "OR", "AND", "NOT"], 78)
        self.output_logic.currentTextChanged.connect(self._output_logic_changed)
        top.addWidget(self.output_logic, 0, 3)
        top.setColumnStretch(4, 1)

        body.addLayout(top)

        # ------------------------------------------------------------
        # CONFIG 1 / CONFIG 2 CONDITION GROUPS
        # ------------------------------------------------------------
        condition_row = QHBoxLayout()
        condition_row.setContentsMargins(0, 0, 0, 0)
        condition_row.setSpacing(7)

        config1 = QGroupBox("Config 1")
        c1_grid = QGridLayout(config1)
        c1_grid.setContentsMargins(8, 5, 8, 5)
        c1_grid.setHorizontalSpacing(5)
        c1_grid.setVerticalSpacing(3)

        c1_grid.addWidget(label("Rise condition", "FieldLabel"), 0, 0)
        self.output_c1_rise = combo(self._output_condition_options("OUT0"), 108)
        self.output_c1_rise.setCurrentText("DEL0")
        self.output_c1_rise.currentTextChanged.connect(self._output_condition_changed)
        c1_grid.addWidget(self.output_c1_rise, 0, 1)

        c1_grid.addWidget(label("Fall condition", "FieldLabel"), 1, 0)
        self.output_c1_fall = combo(self._output_condition_options("OUT0"), 108)
        self.output_c1_fall.setCurrentText("DEL1")
        self.output_c1_fall.currentTextChanged.connect(self._output_condition_changed)
        c1_grid.addWidget(self.output_c1_fall, 1, 1)
        condition_row.addWidget(config1, 1)

        config2 = QGroupBox("Config 2")
        c2_grid = QGridLayout(config2)
        c2_grid.setContentsMargins(8, 5, 8, 5)
        c2_grid.setHorizontalSpacing(5)
        c2_grid.setVerticalSpacing(3)

        c2_grid.addWidget(label("Rise condition", "FieldLabel"), 0, 0)
        self.output_c2_rise = combo(self._output_condition_options("OUT0"), 108)
        self.output_c2_rise.setCurrentText("DEL2")
        self.output_c2_rise.currentTextChanged.connect(self._output_condition_changed)
        c2_grid.addWidget(self.output_c2_rise, 0, 1)

        c2_grid.addWidget(label("Fall condition", "FieldLabel"), 1, 0)
        self.output_c2_fall = combo(self._output_condition_options("OUT0"), 108)
        self.output_c2_fall.setCurrentText("DEL3")
        self.output_c2_fall.currentTextChanged.connect(self._output_condition_changed)
        c2_grid.addWidget(self.output_c2_fall, 1, 1)
        condition_row.addWidget(config2, 1)

        body.addLayout(condition_row)

        # Small explanatory line using only documented TG10 terminology.
        
        self._update_output_logic_options()
        self._update_output_condition_controls()

        add_card_action(
            frame,
            lambda: (
                self._commit_output_to_monitor(),
                self.set_status(f"{self.output_channel.currentText()} output set")
            )
        )
        return frame

    @staticmethod
    def _output_condition_options(channel=None):
        """Return TG10 output condition choices.

        EKSMA's TG10 manual states that a post DELx condition is tied to
        the matching output number: if a post counter is used, the delay
        and output numbers should match. Therefore:
            OUT0 -> post DEL0 only
            OUT1 -> post DEL1 only
            ...
            OUT7 -> post DEL7 only

        The ordinary DEL0..DEL7 choices remain available independently.
        """
        options = [f"DEL{i}" for i in range(8)]

        if channel and channel.startswith("OUT"):
            try:
                index = int(channel[3:])
                if 0 <= index <= 7:
                    options.append(f"post DEL{index}")
            except ValueError:
                pass
        else:
            options.extend(f"post DEL{i}" for i in range(8))

        options += [
            "No change", "Force set", "Force reset", "Trigger",
            "Latch set", "Latch reset", "GATE", "nGATE",
            "Delayed set", "Delayed reset",
        ]
        return options

    def _refresh_output_condition_options(self, channel):
        """Refresh all four condition selectors for the selected OUTx.

        For OUTx, only post DELx is offered from the post-delay family.
        """
        if not channel.startswith("OUT"):
            return

        try:
            index = int(channel[3:])
        except ValueError:
            return

        if not 0 <= index <= 7:
            return

        new_items = self._output_condition_options(channel)

        for widget in (
            self.output_c1_rise,
            self.output_c1_fall,
            self.output_c2_rise,
            self.output_c2_fall,
        ):
            current = widget.currentText()
            widget.blockSignals(True)
            widget.clear()
            widget.addItems(new_items)

            # Preserve the current selection when it is still valid.
            if current in new_items:
                widget.setCurrentText(current)
            else:
                # If the old value was a post DELx from another channel,
                # move it to the matching post DELx.
                if current.startswith("post DEL"):
                    widget.setCurrentText(f"post DEL{index}")
                elif widget.count():
                    widget.setCurrentIndex(0)

            widget.blockSignals(False)

    def _output_channel_changed(self, *_):
        channel = self.output_channel.currentText()
        self._refresh_output_condition_options(channel)
        self._update_output_logic_options()
        self._update_output_condition_controls()

    def _update_output_condition_controls(self):
        if not hasattr(self, "output_channel"):
            return
        digital = self.output_channel.currentText().startswith("OUT")
        for widget in (
            self.output_c1_rise, self.output_c1_fall,
            self.output_c2_rise, self.output_c2_fall
        ):
            widget.setEnabled(digital)

    def _output_logic_changed(self, *_):
        self._update_output_logic_options()

    def _update_output_logic_options(self):
        if not hasattr(self, "output_channel"):
            return
        channel = self.output_channel.currentText()
        logic_available = channel in {"OUT2", "OUT3", "OUT4", "OUT5"}
        self.output_logic.setEnabled(logic_available)
        self.output_logic.blockSignals(True)
        if not logic_available:
            self.output_logic.setCurrentText("NA")
        elif self.output_logic.currentText() == "NA":
            self.output_logic.setCurrentText("OR")
        self.output_logic.blockSignals(False)

    def _output_condition_changed(self, *_):
        pass

    def _update_output_monitor(self, *_):
        self._update_output_logic_options()
        self._update_output_condition_controls()
        if hasattr(self, "monitor_table_widget"):
            self._update_monitor_values()

    def _commit_output_to_monitor(self):
        if not hasattr(self, "monitor_table_widget"):
            return
        channel = self.output_channel.currentText()
        if not channel.startswith("OUT"):
            return
        try:
            row = int(channel[3:])
        except ValueError:
            return

        values = [
            self.output_c1_rise.currentText(),
            self.output_c1_fall.currentText(),
            self.output_c2_rise.currentText(),
            self.output_c2_fall.currentText(),
            self.output_logic.currentText()
        ]
        # Monitor table columns after removing the serial (#) and Status columns:
        # Output, Config1 Rise, Config1 Fall, Config2 Rise, Config2 Fall, Logic out
        for col, value in zip((1, 2, 3, 4, 5), values):
            item = self.monitor_table_widget.item(row, col)
            if item is not None:
                item.setText(value)

        self._update_monitor_values()

    # ========================================================
    # MONITOR
    # ========================================================

    def monitor_card(self):
        """
        Monitor section only.

        Layout:
            Row 1 : Sync | Config
            Row 2 : Frequency | Period
            Row 3 : Device Status (full width)
            Row 4 : Output table (fills remaining space)

        No Live Parameter panel is placed below the output table so that
        the output monitor can use the complete remaining height.
        """
        frame, body = make_card(
            "▮▮",
            "Monitor",
            collapsible=False
        )

        # ----------------------------------------------------
        # Monitor header controls
        # ----------------------------------------------------
        header = (
            frame
            .layout()
            .itemAt(0)
            .widget()
            .layout()
        )

        header.addStretch()

        header.addWidget(
            label(
                "Update:",
                "FieldLabel"
            )
        )

        update_rate = combo(
            ["100 ms", "250 ms", "500 ms", "1 s"],
            92
        )
        update_rate.setMinimumWidth(92)
        update_rate.setObjectName("MonitorUpdateCombo")
        update_rate.setToolTip("Monitor refresh interval")
        header.addWidget(update_rate)

        refresh = QToolButton()
        refresh.setObjectName("Chevron")
        refresh.setText("↻")
        refresh.setFixedSize(22, 22)
        refresh.clicked.connect(
            self._update_monitor_values
        )
        header.addWidget(refresh)

        # ----------------------------------------------------
        # 1st + 2nd + 3rd monitor layers
        # ----------------------------------------------------
        tiles = QGridLayout()
        tiles.setContentsMargins(0, 0, 0, 0)
        tiles.setHorizontalSpacing(5)
        tiles.setVerticalSpacing(5)

        def make_monitor_tile(title, value_widget):
            tile = QFrame()
            tile.setObjectName("Tile")

            layout = QVBoxLayout(tile)
            layout.setContentsMargins(7, 4, 7, 4)
            layout.setSpacing(1)

            layout.addWidget(
                label(
                    title,
                    "TileLabel"
                )
            )

            layout.addWidget(
                value_widget
            )

            return tile

        # ----------------------------------------------------
        # 1st layer: Sync | Config
        # ----------------------------------------------------
        self.monitor_sync_value = label(
            "Internal",
            "TileValue"
        )

        self.monitor_config_value = label(
            "1 (Normal)",
            "TileValue"
        )

        tiles.addWidget(
            make_monitor_tile(
                "Sync",
                self.monitor_sync_value
            ),
            0,
            0
        )

        tiles.addWidget(
            make_monitor_tile(
                "Config",
                self.monitor_config_value
            ),
            0,
            1
        )

        # ----------------------------------------------------
        # 2nd layer: Frequency | Period
        # ----------------------------------------------------
        self.monitor_freq_value = label(
            "1.000000 MHz",
            "TileValue"
        )

        self.monitor_period_value = label(
            "1.000000 µs",
            "TileValue"
        )

        tiles.addWidget(
            make_monitor_tile(
                "Frequency",
                self.monitor_freq_value
            ),
            1,
            0
        )

        tiles.addWidget(
            make_monitor_tile(
                "Period",
                self.monitor_period_value
            ),
            1,
            1
        )

        # ----------------------------------------------------
        # 3rd layer: Device Status — full width
        # ----------------------------------------------------
        device_tile = QFrame()
        device_tile.setObjectName("Tile")

        device_layout = QHBoxLayout(device_tile)
        device_layout.setContentsMargins(
            7, 4, 7, 4
        )
        device_layout.setSpacing(8)

        device_layout.addWidget(
            label(
                "Device Status",
                "TileLabel"
            )
        )

        self.monitor_device_value = label(
            "OFF",
            "TileValue"
        )

        device_layout.addWidget(
            self.monitor_device_value
        )

        device_layout.addStretch()

        tiles.addWidget(
            device_tile,
            2,
            0,
            1,
            2
        )

        tiles.setColumnStretch(0, 1)
        tiles.setColumnStretch(1, 1)

        body.addLayout(
            tiles
        )

        # ----------------------------------------------------
        # 4th layer: Output table — fills remaining space
        # ----------------------------------------------------
        self.monitor_table_widget = self.monitor_table()

        body.addWidget(
            self.monitor_table_widget,
            1
        )

        # ----------------------------------------------------
        # Live parameter — directly below the Monitor table
        # ----------------------------------------------------
        live = QFrame()
        live.setObjectName("Card")
        live.setMinimumHeight(58)
        live.setMaximumHeight(66)

        live_layout = QHBoxLayout(live)
        live_layout.setContentsMargins(8, 4, 8, 4)
        live_layout.setSpacing(7)

        live_layout.addWidget(
            label("◉", "CardIcon")
        )
        live_layout.addWidget(
            label("Live parameter", "CardTitle")
        )
        live_layout.addSpacing(6)

        clk_tile = QFrame()
        clk_tile.setObjectName("Tile")
        clk_layout = QHBoxLayout(clk_tile)
        clk_layout.setContentsMargins(8, 3, 8, 3)
        clk_layout.setSpacing(6)
        clk_layout.addWidget(label("CLK IN", "TileLabel"))
        self.monitor_live_clk = label("100.000 MHz", "TileValue")
        clk_layout.addWidget(self.monitor_live_clk)
        live_layout.addWidget(clk_tile, 1)

        sync_tile = QFrame()
        sync_tile.setObjectName("Tile")
        sync_layout = QHBoxLayout(sync_tile)
        sync_layout.setContentsMargins(8, 3, 8, 3)
        sync_layout.setSpacing(6)
        sync_layout.addWidget(label("SYNC IN", "TileLabel"))
        self.monitor_live_sync = label("--", "TileValue")
        sync_layout.addWidget(self.monitor_live_sync)
        live_layout.addWidget(sync_tile, 1)

        self.monitor_live_note = label(
            "Internal timing reference",
            "SmallGrey"
        )
        live_layout.addWidget(self.monitor_live_note)

        body.addWidget(live)

        self._update_monitor_values()

        return frame

    def _update_monitor_values(self):
        """
        Update only the values displayed by the Monitor section.
        Other dashboard sections are not modified here.
        """
        if not hasattr(
            self,
            "monitor_sync_value"
        ):
            return

        # 1st layer
        self.monitor_sync_value.setText(
            self.committed_sync_mode
        )

        # 2nd layer
        if hasattr(self, "committed_frequency_hz"):
            freq_factor = {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6}
            freq_display = (
                self.committed_frequency_hz /
                freq_factor[self.committed_freq_unit]
            )
            self.monitor_freq_value.setText(
                f"{freq_display:.8f} {self.committed_freq_unit}"
            )

        if hasattr(self, "committed_period_s"):
            period_factor = {"s": 1.0, "ms": 1e-3, "µs": 1e-6, "ns": 1e-9}
            period_display = (
                self.committed_period_s /
                period_factor[self.committed_period_unit]
            )
            self.monitor_period_value.setText(
                f"{period_display:.8f} {self.committed_period_unit}"
            )

        # Config monitor
        if hasattr(
            self,
            "config_settings"
        ):
            cfg_name = self.committed_config_name
            cfg = self.config_settings[cfg_name]

            extra = ""

            if cfg["mode"] == "Burst":
                burst_count_text = (
                    "∞"
                    if cfg.get("burst_infinite", False)
                    else str(cfg.get("burst_count", 1))
                )
                extra = (
                    f" / {cfg['burst_source']}"
                    f" / {burst_count_text}"
                )

            elif cfg["mode"] == "Gate":
                extra = (
                    f" / {cfg['gate']}"
                )

            elif cfg["mode"] == "Frequency divider":
                extra = (
                    f" / ÷{cfg['divider']}"
                )

            self.monitor_config_value.setText(
                f"{cfg_name[-1]} "
                f"({cfg['mode']})"
                f"{extra}"
            )

        # 3rd layer
        self.monitor_device_value.setText(
            "RUN"
            if self.running
            else "OFF"
        )

    def monitor_table(self):
        """
        TG10 LCD-style Output monitor table.

        The table occupies all remaining Monitor space.
        All eight outputs are visible simultaneously and
        no scrolling is used.
        """
        headers = [
            "Output",
            "Config1\nRise delay",
            "Fall delay",
            "Config2\nRise delay",
            "Fall delay",
            "Logic out"
        ]

        table = QTableWidget(
            8,
            len(headers)
        )

        table.setHorizontalHeaderLabels(
            headers
        )

        table.verticalHeader().setVisible(
            False
        )

        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        table.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        table.setFocusPolicy(
            Qt.NoFocus
        )

        table.setShowGrid(
            False
        )

        table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        # Let the table expand vertically with the Monitor card.
        table.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # Stretch all columns so the table uses the complete
        # width of the third dashboard column.
        for column in range(
            len(headers)
        ):
            table.horizontalHeader().setSectionResizeMode(
                column,
                QHeaderView.Stretch
            )

        # Eight rows must always remain visible.
        table.verticalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        lcd_rows = [
            [
                "OUT0",
                "25.64 ps",
                "65.36 ns",
                "25.64 ps",
                "25.64 ps",
                "-",
            ],
            [
                "OUT1",
                "NC",
                "reset",
                "25.64 ps",
                "25.64 ps",
                "-",
            ],
            [
                "OUT2",
                "25.64 ps",
                "196.00 ns",
                "25.64 ps",
                "*196.00 ns",
                "OUT2",
            ],
            [
                "OUT3",
                "25.64 ps",
                "298.67 ns",
                "25.64 ps",
                "*298.67 ns",
                "OUT3",
            ],
            [
                "OUT4",
                "25.64 ps",
                "400.00 ns",
                "109.89 ps",
                "*400.00 ns",
                "And OUT3",
            ],
            [
                "OUT5",
                "NC",
                "NC",
                "NC",
                "NC",
                "OUT5",
            ],
            [
                "OUT6",
                "set",
                "NC",
                "25.64 ps",
                "reset",
                "-",
            ],
            [
                "OUT7",
                "NC",
                "NC",
                "25.64 ps",
                "*0.70 us",
                "-",
            ],
        ]

        for row_index, row_data in enumerate(
            lcd_rows
        ):
            for column_index, value in enumerate(
                row_data
            ):
                item = QTableWidgetItem(
                    value
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                table.setItem(
                    row_index,
                    column_index,
                    item
                )

        return table


    # ========================================================
    # OTHER
    # ========================================================

    def monitor_menu(self):
        """Show the TG10 Monitor information available in the GUI."""
        QMessageBox.information(
            self,
            "Monitor",
            "TG10 Monitor\n\n"
            "• Sync\n"
            "• Frequency\n"
            "• Output\n"
            "• Config\n"
            "• Live parameter"
        )

    def other_card(self):

        frame, body = make_card(
            "⚒",
            "Other"
        )

        # ============================================================
        # TOP BUTTONS
        # ============================================================

        tabs = QHBoxLayout()
        tabs.setSpacing(5)

        self.other_group = QButtonGroup(frame)
        self.other_group.setExclusive(True)

        self.other_buttons = []

        names = [
            "Push trigger",
            "Frequency limit",
            "Device presets",
            "Sound",
            "Info"
        ]

        for i, name in enumerate(names):
            button = QRadioButton(name)
            button.setObjectName("OtherRadio")
            button.setMinimumHeight(24)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            if i == 0:
                button.setChecked(True)

            self.other_group.addButton(button, i)
            self.other_buttons.append(button)
            tabs.addWidget(button, 1)

        body.addLayout(tabs)

        # ============================================================
        # STACKED CONTENT AREA
        # ============================================================

        self.other_stack = QStackedWidget()

        # ============================================================
        # PAGE 1 — PUSH TRIGGER
        # ============================================================

        push_page = QWidget()
        push_layout = QVBoxLayout(push_page)
        push_layout.setContentsMargins(6, 3, 6, 3)
        push_layout.setSpacing(3)
        push_layout.addWidget(label("Push trigger", None, bold=True, color=DEEP))

        # LCD Display Screens page 63 shows four force-trigger buttons:
        # One shot trigger, Burst trigger, Latch SET trigger, Latch RESET trigger.
        trigger_row = QHBoxLayout()
        trigger_row.setContentsMargins(0, 0, 0, 0)
        trigger_row.setSpacing(6)

        self.push_one_shot = QPushButton("One shot trigger")
        self.push_burst = QPushButton("Burst trigger")
        self.push_latch_set = QPushButton("Latch SET trigger")
        self.push_latch_reset = QPushButton("Latch RESET trigger")
        self.push_trigger_buttons = [
            self.push_one_shot,
            self.push_burst,
            self.push_latch_set,
            self.push_latch_reset,
        ]

        for btn in self.push_trigger_buttons:
            btn.setObjectName("Seg")
            btn.setMinimumHeight(28)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            trigger_row.addWidget(btn, 1)

        self.push_one_shot.clicked.connect(
            lambda: self._force_push_trigger("One shot trigger")
        )
        self.push_burst.clicked.connect(
            lambda: self._force_push_trigger("Burst trigger")
        )
        self.push_latch_set.clicked.connect(
            lambda: self._force_push_trigger("Latch SET trigger")
        )
        self.push_latch_reset.clicked.connect(
            lambda: self._force_push_trigger("Latch RESET trigger")
        )

        push_layout.addLayout(trigger_row)
        push_layout.addWidget(label("Push button to force trigger", "SmallGrey"))
        self.other_stack.addWidget(push_page)


        # PAGE 6 — LIVE PARAMETER
        # TG10 manual: live parameters display frequencies at input channels.
        live_page = QWidget()
        live_layout = QGridLayout(live_page)
        live_layout.setContentsMargins(6, 4, 6, 4)
        live_layout.setHorizontalSpacing(10)
        live_layout.setVerticalSpacing(5)

        live_layout.addWidget(label("Live parameter", "FieldLabel", True), 0, 0, 1, 2)

        self.other_live_clk = label("CLK IN: --", "TileValue")
        self.other_live_sync = label("SYNC IN: --", "TileValue")

        live_layout.addWidget(label("CLK IN", "FieldLabel"), 1, 0)
        live_layout.addWidget(self.other_live_clk, 1, 1)
        live_layout.addWidget(label("SYNC IN", "FieldLabel"), 2, 0)
        live_layout.addWidget(self.other_live_sync, 2, 1)
        live_layout.setColumnStretch(1, 1)

        # Live parameter is intentionally not exposed as an Other radio option.
        # Its values are still used internally by the Monitor live strip.

        # PAGE 2 — FREQUENCY LIMIT
        # ============================================================

        frequency_page = QWidget()

        frequency_layout = QHBoxLayout(
            frequency_page
        )

        frequency_layout.setContentsMargins(6, 3, 6, 3)

        frequency_layout.setSpacing(
            10
        )

        frequency_layout.addWidget(
            label(
                "Frequency limit",
                None,
                bold=True,
                color=DEEP
            )
        )

        frequency_layout.addWidget(
            label(
                "Limit:",
                "FieldLabel"
            )
        )

        self.frequency_limit_value = QDoubleSpinBox()

        # Frequency limit is expressed in MHz and cannot exceed
        # the TG10 output-frequency maximum of 20 MHz.
        self.frequency_limit_value.setRange(
            0.00000001,
            20.0
        )

        self.frequency_limit_value.setDecimals(
            3
        )

        self.frequency_limit_value.setValue(
            20.000
        )

        frequency_layout.addWidget(
            self.frequency_limit_value
        )

        frequency_layout.addWidget(
            label(
                "MHz",
                "FieldLabel"
            )
        )

        self.frequency_limit_enable = QCheckBox(
            "Enable frequency limit"
        )

        frequency_layout.addWidget(
            self.frequency_limit_enable
        )

        frequency_layout.addStretch()

        frequency_apply = QPushButton(
            "Apply"
        )

        frequency_apply.setObjectName(
            "SmallBtn"
        )

        frequency_apply.clicked.connect(
            lambda:
            self.set_status(
                "Frequency limit updated"
            )
        )

        frequency_layout.addWidget(
            frequency_apply
        )

        self.other_stack.addWidget(
            frequency_page
        )

        # ============================================================
        # PAGE 3 — DEVICE PRESETS
        # ============================================================

        device_page = QWidget()

        # Keep the exact height/space allocated to the Other section.
        # Only the contents inside Device presets are made compact,
        # matching the small hardcoded preset labels shown on the TG10 LCD.
        device_layout = QHBoxLayout(
            device_page
        )

        device_layout.setContentsMargins(
            10, 6, 10, 6
        )

        device_layout.setSpacing(
            6
        )

        device_layout.addWidget(
            label(
                "Device presets",
                None,
                bold=True,
                color=DEEP,
                size=11
            )
        )

        # Hardcoded TG10 external-device presets.
        # These are display selections only; no undocumented CAN command
        # is generated or assumed here.
        preset_texts = [
            "1 channel - Pockels cell driver - OUT0-X1",
            "2 channel - Pockels cell driver - OUT0-X1  OUT2-X2",
            "4 channel - Pockels cell driver - OUT0-X1  OUT2-X2 - OUT3-X3  OUT4-X4"
        ]

        for text_value in preset_texts:
            preset_label = QLabel(text_value)
            preset_label.setAlignment(
                Qt.AlignCenter
            )
            preset_label.setWordWrap(True)
            preset_label.setMinimumHeight(42)
            preset_label.setStyleSheet("""
                QLabel {
                    background: #f7fafc;
                    border: 1px solid #b9cddd;
                    border-radius: 4px;
                    color: #173f67;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 6px 8px;
                }
            """)
            preset_label.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Expanding
            )
            device_layout.addWidget(
                preset_label,
                1
            )

        set_preset = QPushButton(
            "Set"
        )
        set_preset.setObjectName(
            "SmallBtn"
        )
        set_preset.setFixedWidth(
            45
        )
        set_preset.setFixedHeight(
            27
        )
        set_preset.setStyleSheet("""
            QPushButton#SmallBtn {
                font-size: 10px;
                padding: 2px 5px;
                min-height: 23px;
            }
        """)
        set_preset.clicked.connect(
            lambda:
            self.set_status(
                "Device preset selected"
            )
        )

        device_layout.addWidget(
            set_preset
        )

        self.other_stack.addWidget(
            device_page
        )

        # ============================================================
        # PAGE 4 — SOUND
        # ============================================================

        sound_page = QWidget()

        sound_layout = QHBoxLayout(
            sound_page
        )

        sound_layout.setContentsMargins(6, 3, 6, 3)

        sound_layout.setSpacing(
            12
        )

        sound_layout.addWidget(
            label(
                "Sound",
                None,
                bold=True,
                color=DEEP
            )
        )

        self.sound_enable = QCheckBox(
            "Enable sound"
        )

        self.sound_enable.setChecked(
            True
        )

        sound_layout.addWidget(
            self.sound_enable
        )

        sound_layout.addWidget(
            label(
                "Volume:",
                "FieldLabel"
            )
        )

        self.sound_volume = QSpinBox()

        self.sound_volume.setRange(
            0,
            100
        )

        self.sound_volume.setValue(
            70
        )

        self.sound_volume.setSuffix(
            " %"
        )

        sound_layout.addWidget(
            self.sound_volume
        )

        sound_layout.addStretch()

        self.other_stack.addWidget(
            sound_page
        )

        # ============================================================
        # PAGE 5 — INFO
        # ============================================================

        info_page = QWidget()

        info_layout = QHBoxLayout(
            info_page
        )

        info_layout.setContentsMargins(6, 3, 6, 3)

        info_layout.setSpacing(
            25
        )

        info_layout.addWidget(
            label(
                "TG10 Timing Generator",
                None,
                bold=True,
                color=DEEP
            )
        )

        info_layout.addWidget(
            label(
                "C-DAC TG10 Control GUI"
            )
        )

        info_layout.addWidget(
            label(
                "GUI Version: 1.0"
            )
        )

        info_layout.addWidget(
            label(
                "Hardware: EKSMA Optics TG10"
            )
        )

        info_layout.addStretch()

        self.other_stack.addWidget(
            info_page
        )

        # ============================================================
        # ADD STACK
        # ============================================================

        body.addWidget(
            self.other_stack,
            1
        )

        # ============================================================
        # BUTTON → PAGE CONNECTION
        # ============================================================

        self.other_group.idClicked.connect(
            self.other_stack.setCurrentIndex
        )

        return frame


    def _force_push_trigger(self, trigger_name):
        # GUI/front-end action only. TG10 CAN protocol is proprietary and no
        # undocumented CAN ID/payload is generated by this application.
        self.last_push_trigger = trigger_name
        self.set_status(f"{trigger_name} requested (GUI state only)")

    # ========================================================
    # STATUS BAR
    # ========================================================

    def status_bar(self):

        w = QWidget()

        w.setObjectName(
            "StatusBar"
        )

        w.setMinimumHeight(
            26
        )

        w.setMaximumHeight(
            26
        )

        h = QHBoxLayout(w)

        h.setContentsMargins(
            12, 0, 12, 0
        )

        self.status = label(
            "Ready   |   Not connected",
            "StatusText"
        )

        h.addWidget(
            self.status
        )

        h.addStretch()

        h.addWidget(
            label(
                "C-DAC",
                "StatusRight"
            )
        )

        h.addSpacing(
            12
        )

        h.addWidget(
            label(
                "TG10 GUI v1.0",
                "StatusRight"
            )
        )

        return w

    # ========================================================
    # USB-CAN / BACKEND CONNECTION
    # ========================================================

    def _close_can_connection(self):
        """Close the current USB-CAN serial connection, if one exists."""
        if self.serial_connection is not None:
            try:
                if self.serial_connection.is_open:
                    self.serial_connection.close()
            except Exception:
                pass

        self.serial_connection = None
        self.connection_state = False
        self.connection.setText("●  DISCONNECTED")

    def _connect_can_backend(self):
        """
        Open the dynamically selected COM port and perform one READ-ONLY
        TG10 register test. No GUI Set operation is sent to the hardware.

        Existing project modules are used for the actual CAN framing and
        register-read implementation; this method only supplies the COM
        port selected by the GUI.
        """
        port = self.selected_com_port

        if not port:
            QMessageBox.warning(
                self,
                "USB-CAN",
                "No COM port is selected."
            )
            return False

        self._close_can_connection()

        try:
            # Lazy imports keep the GUI start-up independent of the hardware
            # backend. These are the existing project backend modules.
            import Sy4000_can_control_org as can_backend
            import readv1 as can_reader

            self.can_backend = can_backend
            self.can_reader = can_reader

            # Use the backend's existing serial settings. The COM number
            # comes ONLY from the GUI selection.
            self.serial_connection = can_backend.serial.Serial(
                port,
                baudrate=can_backend.BAUDRATE,
                timeout=can_backend.TIMEOUT
            )

            # READ-ONLY hardware test: register 0x52 is already used by the
            # existing TG10 backend for MuxConfSw / Config mode.
            config_value = can_reader._rd(
                self.serial_connection,
                0x52,
                wait=0.5
            )

            self.connection_state = True
            self.connection.setText(
                f"●  CONNECTED — {port}"
            )
            self.set_status(
                f"Connected to TG10 on {port} | Read 0x52 = 0x{config_value:02X}"
            )

            return True

        except Exception as exc:
            self._close_can_connection()
            self.can_backend = None
            self.can_reader = None

            self.set_status(
                f"Connection failed on {port}"
            )

            QMessageBox.critical(
                self,
                "TG10 Connection Failed",
                f"Could not connect to {port} or read TG10 register 0x52.\n\n"
                f"Error: {exc}"
            )
            return False

    def open_com(self):

        dialog = COMDialog(
            self
        )

        # Restore the previously selected port if it is still connected.
        if self.selected_com_port:
            index = dialog.com_port.findData(self.selected_com_port)
            if index >= 0:
                dialog.com_port.setCurrentIndex(index)

        if dialog.exec() == QDialog.Accepted:
            self.selected_com_port = dialog.selected_port

            if self.selected_com_port:
                self._connect_can_backend()
            else:
                self._close_can_connection()
                self.set_status("No COM port selected")

    def open_delay(self):

        dialog = DelayDialog(
            self
        )

        dialog.exec()

    def open_presets(self):

        dialog = PresetDialog(
            self
        )

        dialog.exec()

    def toggle_run(self):

        self.running = not self.running

        if self.running:

            self.run_button.setText(
                "■  STOP"
            )

            self.run_button.setStyleSheet(
                f"""
                QPushButton#RunBtn {{
                    background:{RED};
                    border:1px solid {RED};
                    color:white;
                    font-weight:700;
                    min-height:40px;
                    padding:5px 22px;
                    border-radius:3px;
                }}
                """
            )

            self.set_status("RUN active")
            self._update_monitor_values()

        else:

            self.run_button.setText(
                "▶  RUN"
            )

            self.run_button.setStyleSheet(
                ""
            )

            self.set_status("RUN stopped")
            self._update_monitor_values()

    def set_status(self, text):

        if self.connection_state and self.selected_com_port:
            self.status.setText(
                text +
                f"   |   Connected: {self.selected_com_port}"
            )
        else:
            self.status.setText(
                text +
                "   |   Not connected"
            )

    def closeEvent(self, event):
        """Close the serial port cleanly when the GUI exits."""
        self._close_can_connection()
        event.accept()


# ============================================================
# MAIN
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setStyle(
        "Fusion"
    )

    app.setStyleSheet(
        STYLE
    )

    app.setFont(
        QFont(
            "Segoe UI",
            10
        )
    )

    window = TG10Window()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()