"""
TG10 TIMING GENERATOR - C-DAC
PySide6 dashboard GUI

Run:
    python main.py

Requirement:
    pip install PySide6 pyserial
"""
import sys
import os

# ============================================================
# TG10 BACKEND PATH
# ============================================================
# TG10_Control_GUI_v1 and TG10_CAN are sibling folders:
#
# C-DAC IISc NQM Internship/
# ├── TG10_Control_GUI_v1/
# └── TG10_CAN/
#
# Add TG10_CAN to Python's module search path so the GUI can
# use the existing backend without copying backend files.
TG10_CAN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "TG10_CAN")
)

if TG10_CAN_DIR not in sys.path:
    sys.path.insert(0, TG10_CAN_DIR)


# ============================================================
# TG10 TEST01 MONITOR BACKEND PATH
# ============================================================
# monitor02.py uses the register transport from test01/main.py.
# Keep this path separate from the main GUI file (main1.py).
TEST01_DIR = os.path.join(
    TG10_CAN_DIR,
    "testtg10",
    "test01"
)

if TEST01_DIR not in sys.path:
    sys.path.insert(0, TEST01_DIR)

from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, QObject, Signal, QThread, QEvent
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

QLabel#StatusPill,
QPushButton#StatusPill {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 3px;
    color: {RED};
    font-weight: 700;
    padding: 8px 12px;
}}

QPushButton#StatusPill:hover {{
    border-color: {BLUE};
    background: #f2f7fb;
}}

QPushButton#StatusPill:disabled {{
    background: white;
    border: 1px solid {LINE};
    color: {RED};
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

QLabel#RefreshArrow {{
    color: {DEEP};
    font-size: 20px;
    font-weight: 800;
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
# MONITOR REFRESH WORKER
# ============================================================

class MonitorRefreshWorker(QObject):
    """Run the existing TG10 Monitor backend reads off the GUI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, read_function):
        super().__init__()
        self.read_function = read_function

    def run(self):
        try:
            self.finished.emit(self.read_function())
        except Exception as exc:
            self.failed.emit(str(exc))


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
        self.com_bps = self._fixed_field("2000000")
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
        self.setFixedSize(700, 450)

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
        self.stack_layout.setSpacing(0)
        self.stack_layout.setAlignment(Qt.AlignTop)

        pages = []

        # ----------------------------------------------------
        # DELAY PRESETS
        # ----------------------------------------------------

        page1 = QWidget()

        page1_layout = QVBoxLayout(page1)
        page1_layout.setContentsMargins(0, 0, 0, 0)
        page1_layout.setSpacing(0)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(5)

        grid.addWidget(
            label("Preset", "FieldLabel", True),
            0, 0
        )

        grid.addWidget(
            label("Value", "FieldLabel", True),
            0, 1
        )

        grid.addWidget(
            label("Preset", "FieldLabel", True),
            0, 3
        )

        grid.addWidget(
            label("Value", "FieldLabel", True),
            0, 4
        )

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

            grid.addWidget(
                a,
                i + 1, 1, 1, 2
            )

            grid.addWidget(
                label(f"DEL{i + 4}", "FieldLabel"),
                i + 1, 3
            )

            grid.addWidget(
                b,
                i + 1, 4, 1, 2
            )

        grid.addWidget(
            label("Range: 0 … 150 ms", "InfoBox"),
            5, 0, 1, 6
        )

        # Keep the Delay Presets content at the top of the page.
        # Any unused vertical space stays below the content.
        page1_layout.addLayout(grid)

        page1.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Maximum
        )

        pages.append(page1)

        # ----------------------------------------------------
        # POST DELAY
        # ----------------------------------------------------

        page2 = QWidget()

        page2_layout = QVBoxLayout(page2)
        page2_layout.setContentsMargins(0, 0, 0, 0)
        page2_layout.setSpacing(0)

        grid2 = QGridLayout()
        grid2.setContentsMargins(4, 8, 4, 4)
        grid2.setHorizontalSpacing(10)
        grid2.setVerticalSpacing(6)

        for i in range(8):

            value = QDoubleSpinBox()
            value.setRange(0, 150_000_000)
            value.setDecimals(3)
            value.setSuffix(" ns")

            grid2.addWidget(
                label(f"post DEL{i}", "FieldLabel"),
                i, 0
            )

            grid2.addWidget(
                value,
                i, 1
            )

        # Keep the Post-delay content at the top of the page.
        # Any unused vertical space stays below the content.
        page2_layout.addLayout(grid2)

        page2.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Maximum
        )

        pages.append(page2)

        # ----------------------------------------------------
        # PAGE BUTTONS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # STACKED PAGES
        # ----------------------------------------------------

        for page in pages:
            page.setVisible(False)
            self.stack_layout.addWidget(page)

        pages[0].setVisible(True)

        root.addWidget(self.stack, 1)

        # ----------------------------------------------------
        # CLOSE BUTTON
        # ----------------------------------------------------

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

            if i < len(self.page_buttons):
                self.page_buttons[i].setChecked(i == index)


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
        self.monitor_backend = None
        self.connection_state = False

        # Monitor refresh worker state. The existing hardware backend is
        # still used; only the blocking read is moved off the GUI thread.
        self.monitor_refresh_thread = None
        self.monitor_refresh_worker = None
        self.monitor_refresh_timer = None
        self.monitor_refresh_frames = ["⟳", "↻", "⟲", "↺"]
        self.monitor_refresh_frame_index = 0

        # Built-in Monitor refresh after 10 seconds of user inactivity.
        # There is intentionally NO visible Auto option or indicator.
        self.monitor_inactivity_timer = QTimer(self)
        self.monitor_inactivity_timer.setSingleShot(True)
        self.monitor_inactivity_timer.setInterval(10_000)
        self.monitor_inactivity_timer.timeout.connect(
            self._automatic_inactivity_refresh
        )
        self._monitor_inactivity_refresh_enabled = False

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

        # Watch real user interaction across the whole GUI so that any
        # meaningful interaction restarts the invisible 10-second timer.
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

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

        # Connection status is also the disconnect control.
        # There is intentionally no separate DISCONNECT button.
        self.connection = QPushButton(
            "●  DISCONNECTED"
        )

        self.connection.setObjectName(
            "StatusPill"
        )

        self.connection.setCursor(Qt.PointingHandCursor)
        self.connection.setFixedWidth(190)
        self.connection.setToolTip(
            "Click here to disconnect when TG10 is connected"
        )
        self.connection.clicked.connect(
            self._request_disconnect
        )
        self.connection.setEnabled(False)

        h.addWidget(self.connection)

        # COM
        com = QPushButton("COM")
        com.setObjectName("HdrBtn")
        com.setFixedWidth(90)
        com.clicked.connect(self.open_com)

        h.addWidget(com)

        # Delay
        self.delay_header_btn = QPushButton("DELAY")
        self.delay_header_btn.setObjectName("HdrBtn")
        self.delay_header_btn.setFixedWidth(95)
        self.delay_header_btn.clicked.connect(self.open_delay)

        h.addWidget(self.delay_header_btn)

        # Presets
        self.presets_header_btn = QPushButton("PRESETS")
        self.presets_header_btn.setObjectName("HdrBtn")
        self.presets_header_btn.setFixedWidth(100)
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
            "Preset manager",
        ]

        for i, name in enumerate(names):
            b = QPushButton(name)
            b.setObjectName("Tab")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked, name=name: self._navigation_clicked(name))
            if i == 0:
                b.setChecked(True)
            group.addButton(b, i)
            h.addWidget(b)

        h.addStretch()
        return w

    def _navigation_clicked(self, name):
        """Handle dashboard navigation, including the Other popup."""
        self.highlight_header_buttons(name)

        if name == "Other":
            self.open_other()
            return

        self.highlight_section(name)

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
        """Main TG10 dashboard.

        Layout:
            LEFT   : Sync / Output
            MIDDLE : Configuration 1/2 / Frequency-Period
            RIGHT  : Monitor

        Delay and Live Parameter dashboard panels are intentionally omitted.
        The Other section is opened as a compact dialog from the Other
        navigation button.
        """
        page = QWidget()

        grid = QGridLayout(page)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        sync = self.sync_card()
        config = self.config_card()
        freq = self.frequency_card()
        output = self.output_card()
        monitor = self.monitor_card()

        self.section_cards = {
            "Sync": sync,
            "Freq / Period": freq,
            "Config 1/2": config,
            "Output": output,
            "Monitor": monitor,
        }

        for card in (sync, config, freq, output, monitor):
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # LEFT: Sync above Output.
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(sync, 1)
        left_layout.addWidget(output, 1)

        # MIDDLE: Configuration above Frequency / Period.
        middle_column = QWidget()
        middle_layout = QVBoxLayout(middle_column)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(8)
        middle_layout.addWidget(config, 1)
        middle_layout.addWidget(freq, 1)

        grid.addWidget(left_column, 0, 0, 2, 1)
        grid.addWidget(middle_column, 0, 1, 2, 1)
        grid.addWidget(monitor, 0, 2, 2, 1)

        # Keep Sync/Config horizontally compact while giving Monitor enough
        # width for all eight output rows and the two live-parameter tiles.
        grid.setColumnStretch(0, 38)
        grid.setColumnStretch(1, 27)
        grid.setColumnStretch(2, 35)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)

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

        self._update_other_live_parameter()
        return frame

    # ========================================================
    # SYNC
    # ========================================================

    def sync_card(self):

        frame, body = make_card(
            "∿",
            "Synchronization (Sync)",
            collapsible=False
        )
        # ====================================================
        # SET BUTTON
        # ====================================================
        
        add_card_action(
            frame,
            callback=self._set_sync_hardware,
            text="Set"
        )

        # ====================================================
        # MAIN SYNC MODE GROUP
        # ====================================================

        mode_group = QButtonGroup(self)
        mode_group.setExclusive(True)
        self.sync_mode_group = mode_group

        self.internal_radio = QRadioButton("Internal Clock")
        self.single_radio = QRadioButton("External Source\nSINGLE IN")
        self.dual_radio = QRadioButton("External\nDUAL IN")
        self.oneshot_radio = QRadioButton("One shot\ntrigger")

        radios = [
            self.internal_radio,
            self.single_radio,
            self.dual_radio,
            self.oneshot_radio,
        ]

        for i, radio in enumerate(radios):
            radio.setCursor(Qt.PointingHandCursor)
            radio.setMinimumHeight(30)
            mode_group.addButton(radio, i)

        self.internal_radio.setChecked(True)
        mode_group.idClicked.connect(self._sync_mode_selected)

        # ====================================================
        # 1. INTERNAL BOX
        # ====================================================

        internal_box = QGroupBox()
        internal_box.setObjectName("SyncBox")
        internal_box.setMinimumHeight(58)

        internal_layout = QHBoxLayout(internal_box)
        internal_layout.setContentsMargins(10, 7, 10, 7)
        internal_layout.setSpacing(10)

        internal_layout.addWidget(self.internal_radio)

        self.internal_freq = QLineEdit("100.000")
        self.internal_freq.setReadOnly(True)
        self.internal_freq.setAlignment(Qt.AlignCenter)
        self.internal_freq.setFixedHeight(28)
        internal_layout.addWidget(self.internal_freq, 1)

        internal_layout.addWidget(
            label("MHz", "FieldLabel", True)
        )

        body.addWidget(internal_box)

        # ====================================================
        # 2. EXTERNAL SINGLE IN BOX
        # ====================================================

        single_box = QGroupBox()
        single_box.setObjectName("SyncBox")
        single_box.setMinimumHeight(78)

        single_layout = QGridLayout(single_box)
        single_layout.setContentsMargins(10, 7, 10, 7)
        single_layout.setHorizontalSpacing(8)
        single_layout.setVerticalSpacing(5)

        single_layout.addWidget(
            self.single_radio,
            0, 0, 2, 1,
            Qt.AlignVCenter
        )

        self.single_source_group = QButtonGroup(self)
        self.single_source_group.setExclusive(True)

        self.single_source_sync_radio = QRadioButton("SYNC IN")
        self.single_source_clk_radio = QRadioButton("CLK IN")
        self.single_source_sync_radio.setChecked(True)

        self.single_source_group.addButton(
            self.single_source_sync_radio, 0
        )
        self.single_source_group.addButton(
            self.single_source_clk_radio, 1
        )

        single_layout.addWidget(
            self.single_source_sync_radio, 0, 1
        )
        single_layout.addWidget(
            self.single_source_clk_radio, 0, 2
        )

        single_layout.addWidget(
            label("Rate", "FieldLabel", True),
            1, 1
        )

        self.external_rate = QDoubleSpinBox()
        self.external_rate.setDecimals(6)
        self.external_rate.setValue(10.0)
        self.external_rate.setFixedHeight(28)
        single_layout.addWidget(self.external_rate, 1, 2)

        self.single_rate_unit = combo(
            ["MHz", "kHz", "Hz"],
            62
        )
        single_layout.addWidget(self.single_rate_unit, 1, 3)

        body.addWidget(single_box)

        # ====================================================
        # 3. EXTERNAL DUAL IN BOX
        # ====================================================

        dual_box = QGroupBox()
        dual_box.setObjectName("SyncBox")
        dual_box.setMinimumHeight(78)

        dual_layout = QGridLayout(dual_box)
        dual_layout.setContentsMargins(10, 7, 10, 7)
        dual_layout.setHorizontalSpacing(8)
        dual_layout.setVerticalSpacing(5)

        dual_layout.addWidget(
            self.dual_radio,
            0, 0, 2, 1,
            Qt.AlignVCenter
        )

        dual_layout.addWidget(
            label("SYNC IN", "FieldLabel", True),
            0, 1
        )

        self.dual_sync_input = QDoubleSpinBox()
        self.dual_sync_input.setDecimals(6)
        self.dual_sync_input.setValue(1.0)
        self.dual_sync_input.setFixedHeight(28)
        dual_layout.addWidget(self.dual_sync_input, 0, 2)

        self.dual_sync_unit = combo(
            ["MHz", "kHz", "Hz"],
            62
        )
        dual_layout.addWidget(self.dual_sync_unit, 0, 3)

        dual_layout.addWidget(
            label("CLK IN", "FieldLabel", True),
            1, 1
        )

        self.dual_clk_input = QDoubleSpinBox()
        self.dual_clk_input.setDecimals(6)
        self.dual_clk_input.setValue(99.99)
        self.dual_clk_input.setFixedHeight(28)
        dual_layout.addWidget(self.dual_clk_input, 1, 2)

        self.dual_clk_unit = combo(
            ["MHz", "kHz", "Hz"],
            62
        )
        dual_layout.addWidget(self.dual_clk_unit, 1, 3)

        body.addWidget(dual_box)

        # ====================================================
        # 4. ONE SHOT / SOFTWARE / SMART BOX
        # ====================================================

        trigger_box = QGroupBox()
        trigger_box.setObjectName("SyncBox")
        trigger_box.setMinimumHeight(58)

        trigger_layout = QHBoxLayout(trigger_box)
        trigger_layout.setContentsMargins(10, 7, 10, 7)
        trigger_layout.setSpacing(16)

        trigger_layout.addWidget(self.oneshot_radio)

        self.software_trigger = QRadioButton("Software")
        self.smart_trigger = QRadioButton("Smart")

        self.one_shot_group = QButtonGroup(self)
        self.one_shot_group.setExclusive(True)
        self.one_shot_group.addButton(self.software_trigger, 0)
        self.one_shot_group.addButton(self.smart_trigger, 1)

        trigger_layout.addWidget(self.software_trigger)
        trigger_layout.addWidget(self.smart_trigger)
        trigger_layout.addStretch()

        body.addWidget(trigger_box)

        # ====================================================
        # EXISTING HARDWARE INTEGRATION
        # ====================================================

        self.sync_panels = {
            "Internal": self.internal_freq,
            "External SINGLE IN": self.external_rate,
            "External DUAL IN": self.dual_sync_input,
            "One shot trigger": self.software_trigger,
        }

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
        """Compact Configuration 1/2 layout matching the approved sketch."""
        frame, body = make_card("⚙", "Configuration 1 / 2", collapsible=False)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._config_card_frame = frame

        body.setContentsMargins(8, 0, 8, 8)
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

        content_grid = QGridLayout()
        content_grid.setContentsMargins(0, 0, 0, 0)
        content_grid.setHorizontalSpacing(7)
        content_grid.setVerticalSpacing(5)
        content_grid.setColumnStretch(0, 1)
        content_grid.setColumnStretch(1, 1)
        content_grid.setRowStretch(0, 1)
        content_grid.setRowStretch(1, 1)
        content_grid.setRowStretch(2, 1)

        self.config_mode_group = QButtonGroup(self)
        self.config_mode_group.setExclusive(True)
        self.config_mode_buttons = {}

        def mode_box():
            box = QFrame()
            box.setObjectName("ConfigModeBox")
            box.setStyleSheet("""
                QFrame#ConfigModeBox {
                    background:#ffffff;
                    border:1px solid #c5d4e2;
                    border-radius:4px;
                }
            """)
            lay = QVBoxLayout(box)
            lay.setContentsMargins(8, 6, 8, 6)
            lay.setSpacing(3)
            return box, lay

        def mode_radio(lay, name):
            r = QRadioButton(name)
            r.setMinimumHeight(24)
            self.config_mode_group.addButton(r)
            self.config_mode_buttons[name] = r
            lay.addWidget(r)
            return r

        # Normal
        normal_box, normal_lay = mode_box()
        mode_radio(normal_lay, "Normal")
        normal_lay.addStretch()
        content_grid.addWidget(normal_box, 0, 0)

        # Gate: NO extra Burst radio. Gate and nGate are horizontal.
        gate_box, gate_lay = mode_box()
        mode_radio(gate_lay, "Gate")
        gate_group = QButtonGroup(gate_box)
        gate_group.setExclusive(True)
        self.config_gate_group = gate_group
        self.config_gate_buttons = {}
        gate_row = QHBoxLayout()
        gate_row.setContentsMargins(0, 0, 0, 0)
        gate_row.setSpacing(5)
        for option in ("GATE", "nGATE"):
            r = QRadioButton(option)
            r.setMinimumHeight(24)
            gate_group.addButton(r)
            self.config_gate_buttons[option] = r
            r.toggled.connect(lambda checked, value=option: self._save_config_gate(value, checked))
            gate_row.addWidget(r)
        gate_row.addStretch()
        gate_lay.addLayout(gate_row)
        gate_lay.addStretch()
        content_grid.addWidget(gate_box, 1, 0)

        # Frequency divider: radio stays directly beside its label.
        divider_box, divider_lay = mode_box()
        mode_radio(divider_lay, "Frequency divider")
        divider_lay.addWidget(label("Division of Freq", "FieldLabel", bold=True))
        self.config_divider_widget = QSpinBox()
        self.config_divider_widget.setRange(1, 32767)
        self.config_divider_widget.setValue(1)
        self.config_divider_widget.setMinimumHeight(28)
        self.config_divider_widget.valueChanged.connect(self._save_config_divider)
        divider_lay.addWidget(self.config_divider_widget)
        content_grid.addWidget(divider_box, 2, 0)

        # Burst — full right column.
        burst_box, burst_lay = mode_box()
        mode_radio(burst_lay, "Burst")
        burst_lay.addWidget(label("Burst trigger", "FieldLabel", bold=True))

        burst_group = QButtonGroup(burst_box)
        burst_group.setExclusive(True)
        self.config_burst_group = burst_group
        self.config_burst_buttons = {}

        trigger_grid = QGridLayout()
        trigger_grid.setContentsMargins(0, 0, 0, 0)
        trigger_grid.setHorizontalSpacing(12)
        trigger_grid.setVerticalSpacing(2)
        for option, row, col in [
            ("SYNC IN", 0, 0),
            ("GATE", 0, 1),
            ("nGATE", 1, 0),
            ("Software", 1, 1),
        ]:
            r = QRadioButton(option)
            r.setMinimumHeight(24)
            burst_group.addButton(r)
            self.config_burst_buttons[option] = r
            r.toggled.connect(lambda checked, value=option: self._save_config_burst_source(value, checked))
            trigger_grid.addWidget(r, row, col)
        burst_lay.addLayout(trigger_grid)
        burst_lay.addSpacing(4)
        burst_lay.addWidget(label("Burst count", "FieldLabel", bold=True))
        self.burst_count_widget = QSpinBox()
        self.burst_count_widget.setRange(1, 65535)
        self.burst_count_widget.setValue(1)
        self.burst_count_widget.setMinimumHeight(28)
        self.burst_count_widget.valueChanged.connect(self._save_config_burst_count)
        burst_lay.addWidget(self.burst_count_widget)
        burst_lay.addStretch()
        content_grid.addWidget(burst_box, 0, 1, 3, 1)

        body.addLayout(content_grid, 1)

        add_card_action(
            frame,
            lambda: (
                self._commit_config_to_monitor(),
                self.set_status(f'Config 1/2 set: {self.config_settings["Config 1"]["mode"]}')
            ),
            "Set",
        )

        self.config_mode_group.buttonClicked.connect(self._configuration_mode_radio_clicked)
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

        c1_grid.addWidget(label("Pulse width", "FieldLabel"), 2, 0)
        self.output_c1_pulse = QDoubleSpinBox()
        self.output_c1_pulse.setRange(0.001, 150000000.0)
        self.output_c1_pulse.setDecimals(2)
        self.output_c1_pulse.setValue(25.64)
        self.output_c1_pulse.setFixedHeight(28)
        self.output_c1_pulse_unit = combo(["ps", "ns", "us"], 58)
        pulse1_row = QHBoxLayout()
        pulse1_row.setContentsMargins(0, 0, 0, 0)
        pulse1_row.setSpacing(4)
        pulse1_row.addWidget(self.output_c1_pulse)
        pulse1_row.addWidget(self.output_c1_pulse_unit)
        pulse1_container = QWidget()
        pulse1_container.setLayout(pulse1_row)
        c1_grid.addWidget(pulse1_container, 2, 1)
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

        c2_grid.addWidget(label("Pulse width", "FieldLabel"), 2, 0)
        self.output_c2_pulse = QDoubleSpinBox()
        self.output_c2_pulse.setRange(0.001, 150000000.0)
        self.output_c2_pulse.setDecimals(2)
        self.output_c2_pulse.setValue(25.64)
        self.output_c2_pulse.setFixedHeight(28)
        self.output_c2_pulse_unit = combo(["ps", "ns", "us"], 58)
        pulse2_row = QHBoxLayout()
        pulse2_row.setContentsMargins(0, 0, 0, 0)
        pulse2_row.setSpacing(4)
        pulse2_row.addWidget(self.output_c2_pulse)
        pulse2_row.addWidget(self.output_c2_pulse_unit)
        pulse2_container = QWidget()
        pulse2_container.setLayout(pulse2_row)
        c2_grid.addWidget(pulse2_container, 2, 1)
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

        self.monitor_refresh_button = QPushButton("Refresh")
        self.monitor_refresh_button.setObjectName("HdrBtn")
        self.monitor_refresh_button.setFocusPolicy(Qt.NoFocus)
        self.monitor_refresh_button.setFixedWidth(88)
        
        self.monitor_refresh_button.clicked.connect(
            self._refresh_monitor_hardware
        )
        header.addWidget(self.monitor_refresh_button)

        self.monitor_refresh_spinner = QLabel("↻")
        self.monitor_refresh_spinner.setObjectName("RefreshArrow")
        self.monitor_refresh_spinner.setAlignment(Qt.AlignCenter)
        self.monitor_refresh_spinner.setFixedSize(30, 34)
        self.monitor_refresh_spinner.setToolTip(
            "↻ Idle • rotating while Monitor is being refreshed"
        )
        header.addWidget(self.monitor_refresh_spinner)

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

        body.addWidget(live)

        self._update_monitor_values()

        return frame

    @staticmethod
    def _monitor_frequency_text(monitor, value):
        """Use the existing TG10 monitor backend formatter."""
        try:
            return monitor.fmt_freq(value)
        except Exception:
            if value is None:
                return "--"
            value = float(value)
            if value >= 1e6:
                return f"{value / 1e6:.6f} MHz"
            if value >= 1e3:
                return f"{value / 1e3:.3f} kHz"
            return f"{value:.3f} Hz"

    @staticmethod
    def _monitor_period_text(monitor, value):
        """Use the existing TG10 monitor backend formatter."""
        try:
            # The backend uses "us"; the GUI uses the TG10-style micro symbol.
            result = monitor.fmt_period(value)
            return result.replace(" us", " µs")
        except Exception:
            if value is None:
                return "--"
            value = float(value)
            if value < 1e-6:
                return f"{value * 1e9:.3f} ns"
            if value < 1e-3:
                return f"{value * 1e6:.3f} µs"
            if value < 1:
                return f"{value * 1e3:.3f} ms"
            return f"{value:.6f} s"

    @staticmethod
    def _monitor_mode_text(mode):
        names = {
            "internal": "Internal",
            "ext_clk": "External SINGLE IN",
            "ext_sync": "External SINGLE IN",
            "ext_dual": "External DUAL IN",
            "oneshot": "One shot trigger",
            "smart": "Smart trigger",
        }
        return names.get(mode, str(mode) if mode is not None else "--")

    def _update_monitor_output_table(self, output_data):
        """
        Update the existing eight-row Monitor table from TG10 hardware.

        Columns:
            0 = Output
            1 = Config1 Rise delay
            2 = Config1 Fall delay
            3 = Config2 Rise delay
            4 = Config2 Fall delay
            5 = Logic out
        """
        if not hasattr(self, "monitor_table_widget"):
            return

        table = self.monitor_table_widget

        for block in range(8):
            row = block
            data = output_data.get(block, {}) if isinstance(output_data, dict) else {}

            values = [
                f"OUT{block}",
                data.get("conf1", {}).get("rise", "NC"),
                data.get("conf1", {}).get("fall", "NC"),
                data.get("conf2", {}).get("rise", "NC"),
                data.get("conf2", {}).get("fall", "NC"),
            ]

            logic = data.get("logic_out")
            values.append(
                logic.get("text", "-") if isinstance(logic, dict) else "-"
            )

            for column, value in enumerate(values):
                item = table.item(row, column)

                if item is None:
                    item = QTableWidgetItem()

                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

                    table.setItem(
                        row,
                        column,
                        item
                    )

                item.setText(str(value))

    def _set_refresh_button_active(self, active):
        if not hasattr(self, "monitor_refresh_button"):
            return
        self.monitor_refresh_button.setProperty("active", bool(active))
        self.monitor_refresh_button.style().unpolish(self.monitor_refresh_button)
        self.monitor_refresh_button.style().polish(self.monitor_refresh_button)
        self.monitor_refresh_button.update()

    def _toggle_refresh_visual(self, loading):
        """Show the refresh state while the real hardware read is running."""
        if hasattr(self, "monitor_refresh_button"):
            self.monitor_refresh_button.setEnabled(not loading)
            self._set_refresh_button_active(loading)

        if not hasattr(self, "monitor_refresh_spinner"):
            return

        if loading:
            self.monitor_refresh_frame_index = 0
            self.monitor_refresh_spinner.setText(
                self.monitor_refresh_frames[0]
            )
            self.monitor_refresh_spinner.show()

            if self.monitor_refresh_timer is None:
                self.monitor_refresh_timer = QTimer(self)
                self.monitor_refresh_timer.setInterval(160)
                self.monitor_refresh_timer.timeout.connect(
                    self._animate_monitor_refresh
                )

            self.monitor_refresh_timer.start()
        else:
            if self.monitor_refresh_timer is not None:
                self.monitor_refresh_timer.stop()

            self.monitor_refresh_spinner.setText("↻")
            self.monitor_refresh_spinner.show()

    def _animate_monitor_refresh(self):
        self.monitor_refresh_frame_index = (
            self.monitor_refresh_frame_index + 1
        ) % len(self.monitor_refresh_frames)

        self.monitor_refresh_spinner.setText(
            self.monitor_refresh_frames[
                self.monitor_refresh_frame_index
            ]
        )

    def _read_monitor_hardware_data(self):
        """
        Perform the existing Monitor backend reads and return only data.

        No Qt widgets are touched here. This function runs in the worker
        thread so the GUI remains responsive until the actual hardware
        read completes.
        """
        monitor = self.monitor_backend
        ser = self.serial_connection

        if monitor is None:
            raise RuntimeError("Monitor backend not loaded.")

        result = {
            "status": None,
            "run_status": None,
            "live": None,
            "config": None,
            "output_data": None,
            "run_status_error": None,
            "live_error": None,
            "config_error": None,
            "output_error": None,
        }

        # Existing backend read: status / sync / output frequency / period.
        result["status"] = monitor.read_status(
            ser,
            show=False
        )

        # Existing backend read: device run status.
        try:
            result["run_status"] = monitor.read_run_status(ser)
        except Exception as exc:
            result["run_status_error"] = str(exc)

        # Existing backend read: live CLK IN / SYNC IN.
        try:
            result["live"] = monitor.read_live(
                ser,
                show=False
            )
        except Exception as exc:
            result["live_error"] = str(exc)

        # Existing backend read: configuration.
        try:
            result["config"] = monitor.read_config(
                ser,
                show=False
            )
        except Exception as exc:
            result["config_error"] = str(exc)

        # Existing backend read: OUT0 ... OUT7 monitor information.
        try:
            result["output_data"] = monitor.read_mux_delay(
                ser,
                blocks=range(8),
                show=False,
                fast=False
            )
        except Exception as exc:
            result["output_error"] = str(exc)

        return result

    def _apply_monitor_hardware_data(self, data):
        """Apply completed hardware readback to Qt widgets on the GUI thread."""
        monitor = self.monitor_backend

        status = data["status"]
        mode = status.get("mode")

        self.monitor_sync_value.setText(
            self._monitor_mode_text(mode)
        )

        out_hz = status.get("out_hz")
        out_period_s = status.get("out_period_s")

        if out_hz is not None and out_hz > 0:
            self.monitor_freq_value.setText(
                self._monitor_frequency_text(
                    monitor,
                    out_hz
                )
            )

            if out_period_s is None:
                out_period_s = 1.0 / out_hz

            self.monitor_period_value.setText(
                self._monitor_period_text(
                    monitor,
                    out_period_s
                )
            )
        else:
            self.monitor_freq_value.setText("--")
            self.monitor_period_value.setText("--")

        # Device status.
        if data["run_status_error"] is None:
            self.monitor_device_value.setText(
                str(data["run_status"])
            )
        else:
            print(
                f"[MONITOR] Run status read failed: "
                f"{data['run_status_error']}"
            )
            self.monitor_device_value.setText("UNKNOWN")

        # Live parameters.
        if data["live_error"] is None and data["live"] is not None:
            live = data["live"]
            clk_hz = live.get("clk_in_hz")
            sync_hz = live.get("sync_in_hz")

            if clk_hz is not None:
                self.monitor_live_clk.setText(
                    self._monitor_frequency_text(
                        monitor,
                        clk_hz
                    )
                )
            else:
                self.monitor_live_clk.setText("--")

            if sync_hz is not None and sync_hz > 0:
                self.monitor_live_sync.setText(
                    self._monitor_frequency_text(
                        monitor,
                        sync_hz
                    )
                )
            else:
                self.monitor_live_sync.setText("--")
        else:
            print(
                f"[MONITOR] Live parameter read failed: "
                f"{data['live_error']}"
            )
            self.monitor_live_clk.setText("--")
            self.monitor_live_sync.setText("--")

        # Configuration.
        if data["config_error"] is None and data["config"] is not None:
            config = data["config"]
            config_text = config.get(
                "text",
                config.get(
                    "mode",
                    "--"
                )
            )
            self.monitor_config_value.setText(
                str(config_text)
            )
        else:
            print(
                f"[MONITOR] Config read failed: "
                f"{data['config_error']}"
            )
            self.monitor_config_value.setText("--")

        # Output table.
        if data["output_error"] is None:
            self._update_monitor_output_table(
                data["output_data"]
            )
        else:
            print(
                f"[MONITOR] Output table read failed: "
                f"{data['output_error']}"
            )

        errors = []
        for key, title in (
            ("run_status_error", "run status"),
            ("live_error", "live parameters"),
            ("config_error", "config"),
            ("output_error", "output table"),
        ):
            if data[key]:
                errors.append(title)

        if errors:
            return "Monitor refreshed; partial read: " + ", ".join(errors)

        return "Monitor refreshed from TG10 hardware"

    # ========================================================
    # BUILT-IN 10-SECOND INACTIVITY MONITOR REFRESH
    # ========================================================

    def _reset_monitor_inactivity_timer(self):
        """Restart the invisible 10-second user-inactivity countdown."""
        if not self.connection_state or self.serial_connection is None:
            self.monitor_inactivity_timer.stop()
            self._monitor_inactivity_refresh_enabled = False
            return

        self._monitor_inactivity_refresh_enabled = True
        self.monitor_inactivity_timer.start()

    def _start_monitor_inactivity_refresh(self):
        """Start the invisible inactivity refresh countdown after connection."""
        if not self.connection_state or self.serial_connection is None:
            self.monitor_inactivity_timer.stop()
            self._monitor_inactivity_refresh_enabled = False
            return

        self._monitor_inactivity_refresh_enabled = True
        self.monitor_inactivity_timer.start()

    def _stop_monitor_inactivity_refresh(self):
        """Stop automatic inactivity refresh when TG10 is disconnected."""
        self.monitor_inactivity_timer.stop()
        self._monitor_inactivity_refresh_enabled = False

    def _automatic_inactivity_refresh(self):
        """
        Refresh Monitor when the GUI has been unused for 10 seconds.

        This is completely invisible to the user. The existing Monitor
        worker performs the real hardware read; no fake delay or duplicate
        hardware-read path is created.

        The inactivity countdown is stopped while the refresh is running and
        is started again only after the real worker finishes. Therefore the
        next automatic refresh is another full 10 seconds after the last
        user activity / completed refresh cycle.
        """
        if not self.connection_state or self.serial_connection is None:
            self._stop_monitor_inactivity_refresh()
            return

        # Do not keep a second countdown running while the real hardware
        # worker is active.
        self.monitor_inactivity_timer.stop()

        # _refresh_monitor_hardware() already prevents overlapping reads.
        self._refresh_monitor_hardware()

    def eventFilter(self, watched, event):
        """
        Reset the invisible 10-second inactivity countdown whenever the user
        actually interacts with this GUI.

        This covers normal GUI activity such as:
        - mouse movement/clicks
        - keyboard input
        - mouse-wheel interaction

        Programmatic updates from the Monitor worker do not generate these
        user-input events, so they do not keep postponing the refresh.
        """
        if self.connection_state and self.serial_connection is not None:
            user_events = {
                QEvent.MouseMove,
                QEvent.MouseButtonPress,
                QEvent.KeyPress,
                QEvent.Wheel,
            }

            if event.type() in user_events:
                self._reset_monitor_inactivity_timer()

        return super().eventFilter(watched, event)

    def _refresh_monitor_hardware(self):
        """
        Start the existing Monitor hardware read in a worker thread.

        The loading indicator remains visible until the actual backend
        hardware reads return. There is no fixed artificial delay.
        """
        if (
            not self.connection_state
            or self.serial_connection is None
        ):
            self._set_refresh_button_active(True)
            QTimer.singleShot(180, lambda: self._set_refresh_button_active(False))
            self.set_status(
                "Not connected — connect to TG10 first"
            )
            return

        if self.monitor_backend is None:
            self._set_refresh_button_active(True)
            QTimer.singleShot(180, lambda: self._set_refresh_button_active(False))
            self.set_status(
                "Monitor backend not loaded"
            )
            return

        if (
            self.monitor_refresh_thread is not None
            and self.monitor_refresh_thread.isRunning()
        ):
            return

        self.set_status(
            "Refreshing TG10 Monitor..."
        )
        self._toggle_refresh_visual(True)

        self.monitor_refresh_thread = QThread(self)
        self.monitor_refresh_worker = MonitorRefreshWorker(
            self._read_monitor_hardware_data
        )

        self.monitor_refresh_worker.moveToThread(
            self.monitor_refresh_thread
        )

        self.monitor_refresh_thread.started.connect(
            self.monitor_refresh_worker.run
        )
        self.monitor_refresh_worker.finished.connect(
            self._monitor_refresh_finished
        )
        self.monitor_refresh_worker.failed.connect(
            self._monitor_refresh_failed
        )
        self.monitor_refresh_worker.finished.connect(
            self.monitor_refresh_thread.quit
        )
        self.monitor_refresh_worker.failed.connect(
            self.monitor_refresh_thread.quit
        )
        self.monitor_refresh_worker.finished.connect(
            self.monitor_refresh_worker.deleteLater
        )
        self.monitor_refresh_worker.failed.connect(
            self.monitor_refresh_worker.deleteLater
        )
        self.monitor_refresh_thread.finished.connect(
            self._monitor_refresh_thread_finished
        )

        self.monitor_refresh_thread.start()

    def _monitor_refresh_finished(self, data):
        try:
            message = self._apply_monitor_hardware_data(data)
            self.set_status(message)
        except Exception as exc:
            self._monitor_refresh_failed(
                f"Could not apply Monitor data: {exc}"
            )

    def _monitor_refresh_failed(self, error_text):
        print(
            f"[MONITOR] Hardware refresh failed: {error_text}"
        )
        self.set_status(
            f"Monitor refresh failed: {error_text}"
        )

        QMessageBox.warning(
            self,
            "TG10 Monitor Refresh",
            "Could not refresh the TG10 values.\n\n"
            f"{error_text}"
        )

    def _monitor_refresh_thread_finished(self):
        self._toggle_refresh_visual(False)

        thread = self.monitor_refresh_thread
        self.monitor_refresh_worker = None
        self.monitor_refresh_thread = None

        if thread is not None:
            thread.deleteLater()

        # Start a fresh 10-second inactivity window only after the real
        # hardware read has completed. If the user interacted while the
        # worker was running, eventFilter will already have restarted the
        # timer, so do not overwrite that newer countdown.
        if (
            self.connection_state
            and self.serial_connection is not None
            and self.monitor_inactivity_timer is not None
            and not self.monitor_inactivity_timer.isActive()
        ):
            self.monitor_inactivity_timer.start()

    def _update_monitor_values(self):
        """
        Keep the existing Monitor update entry point.

        When connected, perform a real hardware read.
        When disconnected, show the neutral Monitor state.
        """
        if not hasattr(
            self,
            "monitor_sync_value"
        ):
            return

        if (
            not self.connection_state
            or self.serial_connection is None
            or self.monitor_backend is None
        ):
            self.monitor_sync_value.setText("--")
            self.monitor_config_value.setText("--")
            self.monitor_freq_value.setText("--")
            self.monitor_period_value.setText("--")
            self.monitor_device_value.setText("OFF")

            if hasattr(
                self,
                "monitor_live_clk"
            ):
                self.monitor_live_clk.setText("--")

            if hasattr(
                self,
                "monitor_live_sync"
            ):
                self.monitor_live_sync.setText("--")

            return

        self._refresh_monitor_hardware()

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

        # Initial values shown before the first hardware refresh.
        # They are deliberately neutral; Refresh replaces them with
        # actual TG10 register readback.
        lcd_rows = [
            ["OUT0", "--", "--", "--", "--", "-"],
            ["OUT1", "--", "--", "--", "--", "-"],
            ["OUT2", "--", "--", "--", "--", "-"],
            ["OUT3", "--", "--", "--", "--", "-"],
            ["OUT4", "--", "--", "--", "--", "-"],
            ["OUT5", "--", "--", "--", "--", "-"],
            ["OUT6", "--", "--", "--", "--", "-"],
            ["OUT7", "--", "--", "--", "--", "-"],
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

    def open_other(self):
        """Open the Other controls as a compact popup from the navigation bar.

        The dashboard has no permanent Other card.  The popup contains only
        Push trigger and Frequency limit, with the frequency-limit controls
        below the trigger controls as in the approved TG10 layout.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("TG10 — Other")
        dialog.setModal(False)
        dialog.resize(520, 390)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.addWidget(label("⚒", "CardIcon"))
        title_row.addWidget(label("Other", "CardTitle"))
        title_row.addStretch()
        root.addLayout(title_row)

        selector = QHBoxLayout()
        selector.setContentsMargins(0, 0, 0, 0)
        selector.setSpacing(28)
        push_radio = QRadioButton("Push trigger")
        limit_radio = QRadioButton("Frequency limit")
        push_radio.setChecked(True)
        selector.addWidget(push_radio)
        selector.addWidget(limit_radio)
        selector.addStretch()
        root.addLayout(selector)

        # ------------------------------------------------------------
        # Push trigger
        # ------------------------------------------------------------
        push_box = QGroupBox("Push trigger")
        push_grid = QGridLayout(push_box)
        push_grid.setContentsMargins(8, 8, 8, 8)
        push_grid.setHorizontalSpacing(7)
        push_grid.setVerticalSpacing(6)

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
            btn.setMinimumHeight(31)

        push_grid.addWidget(self.push_one_shot, 0, 0)
        push_grid.addWidget(self.push_burst, 0, 1)
        push_grid.addWidget(self.push_latch_set, 1, 0)
        push_grid.addWidget(self.push_latch_reset, 1, 1)

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

        root.addWidget(push_box)

        # ------------------------------------------------------------
        # Frequency limit
        # ------------------------------------------------------------
        limit_box = QGroupBox("Frequency limit")
        limit_grid = QGridLayout(limit_box)
        limit_grid.setContentsMargins(8, 8, 8, 8)
        limit_grid.setHorizontalSpacing(7)
        limit_grid.setVerticalSpacing(5)

        limit_grid.addWidget(
            label("Maximum frequency", "FieldLabel", True),
            0, 0
        )

        self.frequency_limit_value = QDoubleSpinBox()
        self.frequency_limit_value.setRange(0.00000001, 20.0)
        self.frequency_limit_value.setDecimals(6)
        self.frequency_limit_value.setValue(20.0)
        self.frequency_limit_value.setMinimumHeight(30)
        limit_grid.addWidget(self.frequency_limit_value, 0, 1)

        limit_unit = combo(["MHz", "kHz", "Hz"], 62)
        limit_grid.addWidget(limit_unit, 0, 2)

        apply_limit = QPushButton("Apply")
        apply_limit.setObjectName("SmallBtn")
        apply_limit.clicked.connect(
            lambda: self.set_status("Frequency limit updated")
        )
        limit_grid.addWidget(apply_limit, 0, 3)
        limit_grid.setColumnStretch(1, 1)

        root.addWidget(limit_box)

        bottom = QHBoxLayout()
        bottom.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("SmallBtn")
        close_btn.clicked.connect(dialog.accept)
        bottom.addWidget(close_btn)
        root.addLayout(bottom)

        dialog.exec()

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

    def _request_disconnect(self):
        """Ask for confirmation before intentionally disconnecting TG10."""
        if not self.connection_state:
            return

        answer = QMessageBox.question(
            self,
            "Disconnect TG10",
            "Are you sure you want to disconnect?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if answer == QMessageBox.Yes:
            self._close_can_connection()
            self.set_status("Disconnected from TG10")

    def _close_can_connection(self):
        """Close the current USB-CAN serial connection, if one exists."""

        # Stop the invisible inactivity refresh immediately when disconnected.
        self._stop_monitor_inactivity_refresh()

        if self.serial_connection is not None:
            try:
                if self.serial_connection.is_open:
                    self.serial_connection.close()
            except Exception:
                pass

        self.serial_connection = None
        self.connection_state = False
        self.monitor_backend = None
        self.connection.setText("●  DISCONNECTED")
        self.connection.setToolTip("Connect or select a COM port using COM")
        if hasattr(self, "connection"):
            self.connection.setEnabled(False)

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
            import main as can_backend
            import monitor02 as can_reader
            import monitor02 as monitor_backend
            import operations02 as operations

            self.can_backend = can_backend
            self.can_reader = can_reader
            self.monitor_backend = monitor_backend
            self.operations = operations

            # Use the backend's existing serial settings. The COM number
            # comes ONLY from the GUI selection.
            self.serial_connection = can_backend.serial.Serial(
                port,
                baudrate=can_backend.BAUDRATE,
                timeout=can_backend.TIMEOUT
            )

            # READ-ONLY hardware test using the SAME transport used by
            # monitor02.py. This avoids mixing the old readv1 transport
            # with the test01 Monitor backend.
            config_value = monitor_backend._rd(
                self.serial_connection,
                0x52,
                wait=0.5
            )

            self.connection_state = True
            self.connection.setText(
                f"●  CONNECTED — {port}"
            )
            self.connection.setToolTip(
                "Click here to disconnect from the TG10 USB-CAN device"
            )
            if hasattr(self, "connection"):
                self.connection.setEnabled(True)
            self.set_status(
                f"Connected to TG10 on {port} | Read 0x52 = 0x{config_value:02X}"
            )

            # Start the invisible 10-second inactivity countdown.
            # No immediate automatic read is performed here; the first
            # automatic read occurs only after 10 seconds without user input.
            self._start_monitor_inactivity_refresh()

            return True

        except Exception as exc:
            self._close_can_connection()
            self.can_backend = None
            self.can_reader = None
            self.monitor_backend = None

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
        try:
            if not self.connection_state or self.serial_connection is None:
                QMessageBox.warning(
                    self,
                    "TG10 RUN / STOP",
                    "TG10 is not connected. Open COM and connect first."
                )
                return

            if not self.running:
                # RUN
                sequence = self.operations.seq_run_on()
                label = "RUN_ON"
            else:
                # STOP
                sequence = self.operations.seq_run_off()
                label = "RUN_OFF"

            # Use the existing CAN backend function.
            self.can_backend.send_sequence(
                self.serial_connection,
                sequence,
                label=label
            )

            # Change GUI state only after hardware command succeeds.
            self.running = not self.running

            if self.running:
                # TG10 is RUNNING → show STOP in RED
                self.run_button.setText("■  STOP")
                self.run_button.setStyleSheet(
                    """
                    QPushButton#RunBtn {
                        background:#d32f2f;
                        border:1px solid #d32f2f;
                        color:white;
                        font-weight:700;
                        min-height:40px;
                        padding:5px 22px;
                        border-radius:3px;
                    }
                    """
                )
                self.set_status("RUN active")

            else:
                # TG10 is STOPPED → show RUN in GREEN
                self.run_button.setText("▶  RUN")
                self.run_button.setStyleSheet(
                    """
                    QPushButton#RunBtn {
                        background:#159447;
                        border:1px solid #159447;
                        color:white;
                        font-weight:700;
                        min-height:40px;
                        padding:5px 22px;
                        border-radius:3px;
                    }
                    """
                )
                self.set_status("RUN stopped")

            self._update_monitor_values()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "TG10 RUN / STOP Failed",
                f"Could not change RUN/STOP state:\n{exc}"
            )
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
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)

        self._stop_monitor_inactivity_refresh()

        if (
            self.monitor_refresh_thread is not None
            and self.monitor_refresh_thread.isRunning()
        ):
            self.monitor_refresh_thread.quit()
            self.monitor_refresh_thread.wait(1500)

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