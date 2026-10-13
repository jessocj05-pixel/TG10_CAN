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
# TG10_CAN_DIR = os.path.abspath(
#     os.path.join(os.path.dirname(__file__), "..", "TG10_CAN")
# )
TG10_CAN_DIR = os.path.dirname(os.path.abspath(__file__))

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
    QFont, QPainter, QPen, QColor, QPolygonF, QBrush, QPixmap,
    QPainterPath, QFontMetrics
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel,
    QPushButton, QComboBox, QLineEdit, QRadioButton,
    QCheckBox, QSpinBox, QDoubleSpinBox, QHBoxLayout,
    QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QButtonGroup, QSizePolicy,
    QToolButton, QDialog, QDialogButtonBox, QFormLayout,
    QGroupBox, QStackedWidget, QMessageBox, QTabWidget, QScrollArea
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

    # --------------------------------------------------------
    # Time-unit conversion
    # --------------------------------------------------------

    UNIT_TO_SECONDS = {
        "ps": 1e-12,
        "ns": 1e-9,
        "µs": 1e-6,
        "ms": 1e-3,
        "s": 1.0
    }

    def __init__(self, parent=None):

        super().__init__(parent)

        self.parent_window = parent

        self.setWindowTitle("TG10 Delay Presets")
        self.setFixedSize(700, 450)

        # ====================================================
        # ROOT
        # ====================================================

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(8)

        # ====================================================
        # TITLE
        # ====================================================

        root.addWidget(
            label(
                "Delay Presets",
                bold=True,
                size=16,
                color=DEEP
            )
        )

        # ====================================================
        # PAGE BUTTONS
        # ====================================================

        tabs = QHBoxLayout()
        tabs.setContentsMargins(0, 0, 0, 0)
        tabs.setSpacing(6)

        self.page_buttons = []

        delay_page_button = QPushButton("Delay presets")
        delay_page_button.setCheckable(True)
        delay_page_button.setChecked(True)

        post_delay_page_button = QPushButton("Post-delay")
        post_delay_page_button.setCheckable(True)

        self.page_buttons = [
            delay_page_button,
            post_delay_page_button
        ]

        delay_page_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        post_delay_page_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        delay_page_button.setFixedHeight(45)
        post_delay_page_button.setFixedHeight(45)

        tabs.addWidget(delay_page_button)
        tabs.addWidget(post_delay_page_button)

        root.addLayout(tabs)

        # ====================================================
        # STACK
        # ====================================================

        self.stack = QWidget()

        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        self.stack_layout.setSpacing(0)
        self.stack_layout.setAlignment(Qt.AlignTop)

        pages = []

        # ====================================================
        # DELAY PRESETS PAGE
        # ====================================================

        page1 = QWidget()

        page1_layout = QVBoxLayout(page1)
        page1_layout.setContentsMargins(0, 0, 0, 0)
        page1_layout.setSpacing(6)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(5)

        # ----------------------------------------------------
        # Headers
        # ----------------------------------------------------

        grid.addWidget(
            label("Preset", "FieldLabel", True),
            0, 0
        )

        grid.addWidget(
            label("Value", "FieldLabel", True),
            0, 1
        )

        grid.addWidget(
            label("Unit", "FieldLabel", True),
            0, 2
        )

        grid.addWidget(
            label("Preset", "FieldLabel", True),
            0, 3
        )

        grid.addWidget(
            label("Value", "FieldLabel", True),
            0, 4
        )

        grid.addWidget(
            label("Unit", "FieldLabel", True),
            0, 5
        )

        # ----------------------------------------------------
        # Delay widgets
        # ----------------------------------------------------

        self.delay_fields = {}
        self.delay_units = {}

        # ====================================================
        # DEL0–DEL3 = FINE
        # ====================================================

        for i in range(4):

            field = QDoubleSpinBox()

            field.setRange(
                0.025,
                150_000_000
            )

            field.setDecimals(3)

            unit = QComboBox()

            unit.addItems([
                "ps",
                "ns",
                "µs",
                "ms",
                "s"
            ])

            unit.setCurrentText("ns")

            self.delay_fields[i] = field
            self.delay_units[i] = unit

            # Label
            grid.addWidget(
                label(
                    f"DEL{i} (fine)",
                    "FieldLabel"
                ),
                i + 1,
                0
            )

            # Value
            grid.addWidget(
                field,
                i + 1,
                1
            )

            # Unit
            grid.addWidget(
                unit,
                i + 1,
                2
            )

        # ====================================================
        # DEL4–DEL7
        # ====================================================

        for i in range(4, 8):

            field = QDoubleSpinBox()

            field.setRange(
                0.025,
                150_000_000
            )

            field.setDecimals(3)

            unit = QComboBox()

            unit.addItems([
                "ps",
                "ns",
                "µs",
                "ms",
                "s"
            ])

            unit.setCurrentText("ns")

            self.delay_fields[i] = field
            self.delay_units[i] = unit

            # ------------------------------------------------
            # DEL4 = fine*
            # DEL5–DEL7 = coarse
            # ------------------------------------------------

            if i == 4:

                preset_name = "DEL4 (fine*)"

            else:

                preset_name = f"DEL{i} (coarse)"

            # Label
            grid.addWidget(
                label(
                    preset_name,
                    "FieldLabel"
                ),
                (i - 4) + 1,
                3
            )

            # Value
            grid.addWidget(
                field,
                (i - 4) + 1,
                4
            )

            # Unit
            grid.addWidget(
                unit,
                (i - 4) + 1,
                5
            )

        # ====================================================
        # RANGE
        # ====================================================

        grid.addWidget(
            label(
                "Range: 25 ps … 150 ms",
                "InfoBox"
            ),
            5,
            0,
            1,
            6
        )

        page1_layout.addLayout(grid)

        pages.append(page1)

        # ====================================================
        # POST-DELAY PAGE
        # ====================================================

        page2 = QWidget()

        page2_layout = QVBoxLayout(page2)
        page2_layout.setContentsMargins(0, 0, 0, 0)
        page2_layout.setSpacing(6)

        grid2 = QGridLayout()
        grid2.setContentsMargins(0, 0, 0, 0)
        grid2.setHorizontalSpacing(8)
        grid2.setVerticalSpacing(5)

        # ----------------------------------------------------
        # Headers
        # ----------------------------------------------------

        grid2.addWidget(
            label("Preset", "FieldLabel", True),
            0, 0
        )

        grid2.addWidget(
            label("Value", "FieldLabel", True),
            0, 1
        )

        grid2.addWidget(
            label("Unit", "FieldLabel", True),
            0, 2
        )

        # ----------------------------------------------------
        # Post-delay widgets
        # ----------------------------------------------------

        self.post_delay_fields = {}
        self.post_delay_units = {}

        # ====================================================
        # POST DEL0–DEL7
        # ====================================================

        for i in range(8):

            field = QDoubleSpinBox()

            # Keep the displayed range broad.
            # Actual hardware minimum is validated
            # after unit conversion.
            field.setRange(
                0.001,
                150_000_000
            )

            field.setDecimals(3)

            unit = QComboBox()

            unit.addItems([
                "ps",
                "ns",
                "µs",
                "ms",
                "s"
            ])

            unit.setCurrentText("ns")

            self.post_delay_fields[i] = field
            self.post_delay_units[i] = unit

            grid2.addWidget(
                label(
                    f"post DEL{i}",
                    "FieldLabel"
                ),
                i + 1,
                0
            )

            grid2.addWidget(
                field,
                i + 1,
                1
            )

            grid2.addWidget(
                unit,
                i + 1,
                2
            )

        # ====================================================
        # POST-DELAY RANGE
        # ====================================================

        grid2.addWidget(
            label(
                "Pulse width: 4 ns … 150 ms",
                "InfoBox"
            ),
            9,
            0,
            1,
            3
        )

        page2_layout.addLayout(grid2)

        pages.append(page2)

        # ====================================================
        # ADD PAGES
        # ====================================================

        for page in pages:

            self.stack_layout.addWidget(page)

        root.addWidget(
            self.stack
        )
        
        # ====================================================
        # DELAY RESOLUTION INFORMATION
        # ====================================================

        delay_info = label(
            "Fine: 25 ps resolution — DEL0–DEL3    |    "
            "Fine*: DEL4 uses a different clock frequency    |    "
            "Coarse: ~9.4 ns resolution — DEL5–DEL7",
            "InfoBox"
        )

        delay_info.setWordWrap(True)
        delay_info.setMinimumHeight(42)

        root.addWidget(delay_info)

        # ====================================================
        # SET + CLOSE BUTTONS
        # ====================================================

        self.set_button = QPushButton("Set")
        self.set_button.setObjectName("PrimaryBtn")
        self.set_button.setFixedWidth(90)

        self.close_button = QPushButton("Close")
        self.close_button.setFixedWidth(90)

        self.set_button.clicked.connect(
            self.apply_current_page
        )

        self.close_button.clicked.connect(
            self.close
        )

        action_layout = QHBoxLayout()

        action_layout.addStretch()

        action_layout.addWidget(
            self.set_button
        )

        action_layout.addWidget(
            self.close_button
        )

        root.addLayout(
            action_layout
        )

        # ====================================================
        # PAGE BUTTON CONNECTIONS
        # ====================================================

        delay_page_button.clicked.connect(
            lambda: self.show_delay_page(
                0,
                pages
            )
        )

        post_delay_page_button.clicked.connect(
            lambda: self.show_delay_page(
                1,
                pages
            )
        )

        # ====================================================
        # START WITH DELAY PAGE
        # ====================================================

        self.show_delay_page(
            0,
            pages
        )

    # ========================================================
    # PAGE SWITCHING
    # ========================================================

    def show_delay_page(self, index, pages):

        for i, page in enumerate(pages):

            page.setVisible(
                i == index
            )

        for i, button in enumerate(
            self.page_buttons
        ):

            button.setChecked(
                i == index
            )

            if i == index:

                button.setStyleSheet("""
                    QPushButton {
                        background: #087fc1;
                        color: white;
                        border: 1px solid #087fc1;
                        border-radius: 2px;
                        font-weight: 600;
                        padding: 8px 20px;
                    }

                    QPushButton:hover {
                        background: #087fc1;
                    }
                """)

            else:

                button.setStyleSheet("""
                    QPushButton {
                        background: #eef3f7;
                        color: #24445d;
                        border: 1px solid #c5d4df;
                        border-radius: 2px;
                        font-weight: 500;
                        padding: 8px 20px;
                    }

                    QPushButton:hover {
                        background: #e4edf4;
                    }
                """)

        # Remember currently selected page
        self.current_page = index

    # ========================================================
    # SYSTEM CLOCK
    # ========================================================

    def get_system_clock_hz(self, channel=None):

        """
        System clock used to convert delays / widths into counts.

        Internal sync : 100 MHz reference x Ndiv 30 = 3 GHz
        CLK IN modes  : external CLK IN x Ndiv
        SYNC IN / one-shot : internal 100 MHz reference x Ndiv
        DEL4 / post-DEL4   : always the INTERNAL clock
        """

        try:
            return self.parent_window.system_clock_hz(channel)
        except Exception:
            return 3_000_000_000.0

    # ========================================================
    # CONNECTION CHECK
    # ========================================================

    def check_connection(self):

        parent = self.parent_window

        if parent is None:

            QMessageBox.warning(
                self,
                "Connection",
                "TG10 main window is not available."
            )

            return False

        if not getattr(
            parent,
            "connection_state",
            False
        ):

            QMessageBox.warning(
                self,
                "TG10 Not Connected",
                "Please connect to the TG10 before applying presets."
            )

            return False

        if not getattr(
            parent,
            "serial_connection",
            None
        ):

            QMessageBox.warning(
                self,
                "TG10 Not Connected",
                "No active TG10 connection was found."
            )

            return False

        return True

    # ========================================================
    # APPLY CURRENT PAGE
    # ========================================================

    def _driver_review(self):

        """Summarise what is about to be sent to the DPB1 chain and stop on driver-limit violations."""

        sim = getattr(self.parent_window, "simulator_dialog", None)

        if sim is None:
            return True

        try:
            sim.load_from_main()
            return sim.setup.confirm_send(self)
        except Exception:
            return True

    def apply_current_page(self):

        if not self._driver_review():
            return

        if self.current_page == 0:

            self.apply_delay_presets()

        else:

            self.apply_post_delay_presets()

    # ========================================================
    # APPLY DELAY PRESETS
    # ========================================================

    def apply_delay_presets(self):

        if not self.check_connection():

            return

        parent = self.parent_window

        try:

            f_hz = self.get_system_clock_hz()

            # ------------------------------------------------
            # DEL0–DEL7
            # ------------------------------------------------

            for ch in range(8):

                field = self.delay_fields[ch]
                unit = self.delay_units[ch]

                value = field.value()
                selected_unit = unit.currentText()

                time_s = (
                    value
                    * self.UNIT_TO_SECONDS[
                        selected_unit
                    ]
                )

                # ------------------------------------------------
                # Hardware sequence
                # ------------------------------------------------

                sequence = (
                    parent.operations
                    .build_delay_channel(
                        ch,
                        time_s,
                        self.get_system_clock_hz(ch)
                    )
                )

                # ------------------------------------------------
                # Send to TG10
                # ------------------------------------------------

                parent.can_backend.send_sequence(
                    parent.serial_connection,
                    sequence,
                    label=(
                        f"DEL{ch} = "
                        f"{value:.3f} "
                        f"{selected_unit}"
                    )
                )
                parent.menu.update_current_config(sequence)  #for presets 

            QMessageBox.information(
                self,
                "Delay Presets",
                "All delay presets were applied successfully."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Delay Error",
                f"Failed to apply delay presets:\n\n{e}"
            )

    # ========================================================
    # APPLY POST-DELAY PRESETS
    # ========================================================

    def apply_post_delay_presets(self):

        parent = self.parent()

        if parent is None:
            return

        # ----------------------------------------------------
        # Check connection
        # ----------------------------------------------------
        if not getattr(parent, "connection_state", False):
            QMessageBox.warning(
                self,
                "Not Connected",
                "Please connect to TG10 before setting Post-delay presets."
            )
            return

        # ----------------------------------------------------
        # Get system clock
        # ----------------------------------------------------
        f_hz = self.get_system_clock_hz()

        # ----------------------------------------------------
        # Apply each Post-delay channel
        # ----------------------------------------------------
        for ch in range(8):

            field = self.post_delay_fields[ch]
            unit = self.post_delay_units[ch]

            value = field.value()
            unit_text = unit.currentText()

            # Convert GUI value to seconds
            unit_to_seconds = {
                "ps": 1e-12,
                "ns": 1e-9,
                "µs": 1e-6,
                "ms": 1e-3,
                "s": 1.0,
            }

            pulse_width_s = (
                value * unit_to_seconds[unit_text]
            )

            try:

                # ------------------------------------------------
                # Calculate the REAL TG10-supported value
                # ------------------------------------------------
                sequence, actual_width_s = (
                    parent.operations.build_post_delay_channel(
                        ch,
                        pulse_width_s,
                        self.get_system_clock_hz(ch)
                    )
                )

                # ------------------------------------------------
                # Send to TG10
                # ------------------------------------------------
                parent.can_backend.send_sequence(
                    parent.serial_connection,
                    sequence,
                    label=f"POST DEL{ch}"
                )
                parent.menu.update_current_config(sequence) #for presets
                # ------------------------------------------------
                # Convert ACTUAL programmed value back to GUI unit
                # ------------------------------------------------
                actual_value = (
                    actual_width_s /
                    unit_to_seconds[unit_text]
                )

                # ------------------------------------------------
                # Update GUI with the REAL programmed value
                # ------------------------------------------------
                field.blockSignals(True)

                field.setValue(
                    actual_value
                )

                field.blockSignals(False)

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Post-delay Error",
                    f"Failed to set post DEL{ch}:\n\n{e}"
                )

                return

        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------
        QMessageBox.information(
            self,
            "Post-delay",
            "Post-delay presets applied successfully."
        )
    
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
            "Simulator / Photonics",
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

        if name == "Simulator / Photonics":
            self.open_simulator()
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
        # Make Configuration 1/2 exactly the same height as Sync.
        sync_height = sync.sizeHint().height()
        sync.setFixedHeight(sync_height)
        config.setFixedHeight(sync_height)
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
        #config.setMinimumHeight(sync.sizeHint().height())
        middle_layout.addWidget(freq, 1)
        middle_layout.addWidget(config, 1)

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
        self.single_radio = QRadioButton("External\nSINGLE IN")
        self.dual_radio = QRadioButton("External\nDUAL IN")
        self.oneshot_radio = QRadioButton("One shot trigger")

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

        oneshot_box = QFrame()
        oneshot_box.setObjectName("ConfigModeBox")
        oneshot_box.setStyleSheet("""
            QFrame#ConfigModeBox {
                background: #ffffff;
                border: 1px solid #c5d4e2;
                border-radius: 4px;
            }
        """)

        oneshot_lay = QHBoxLayout(oneshot_box)
        oneshot_lay.setContentsMargins(10, 7, 10, 7)
        oneshot_lay.setSpacing(40)

        # Rename the existing One Shot radio for this horizontal layout
        self.oneshot_radio.setText("One shot trigger")
        self.oneshot_radio.setMinimumHeight(24)
        self.oneshot_radio.setMinimumWidth(140)

        self.software_trigger = QRadioButton("Software")
        self.software_trigger.setMinimumHeight(24)
        self.software_trigger.setMinimumWidth(100)
        self.smart_trigger = QRadioButton("Smart")
        self.smart_trigger.setMinimumHeight(24)
        self.smart_trigger.setMinimumWidth(100)

        self.software_trigger.setCursor(Qt.PointingHandCursor)
        
        self.smart_trigger.setCursor(Qt.PointingHandCursor)

        self.software_trigger.setMinimumHeight(24)
        self.smart_trigger.setMinimumHeight(24)

        self.one_shot_group = QButtonGroup(oneshot_box)
        self.one_shot_group.setExclusive(True)

        # IMPORTANT:
        # oneshot_radio already belongs to sync_mode_group.
        # Do NOT add it to this group.

        self.one_shot_group.addButton(self.software_trigger, 0)
        self.one_shot_group.addButton(self.smart_trigger, 1)
        
        self.software_trigger.setChecked(False)
        self.smart_trigger.setChecked(False)

        oneshot_lay.addWidget(self.oneshot_radio)
        oneshot_lay.addWidget(self.software_trigger)
        oneshot_lay.addWidget(self.smart_trigger)
        oneshot_lay.addStretch()


        # sync_card() uses 'body'
        body.addWidget(oneshot_box)

        # ====================================================
        # EXISTING HARDWARE INTEGRATION
        # ====================================================

        self.sync_panels = {
            "Internal": internal_box,
            "External SINGLE IN": single_box,
            "External DUAL IN": dual_box,
            "One shot trigger": oneshot_box,
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

        # ------------------------------------------------------------
        # Current main Sync mode
        # ------------------------------------------------------------

        self.sync_mode = names[index]

        # ------------------------------------------------------------
        # Keep the selected MAIN radio checked
        # ------------------------------------------------------------

        selected_radio = self.sync_mode_group.button(index)

        if selected_radio is not None:
            self.sync_mode_group.setExclusive(False)

            for radio in self.sync_mode_group.buttons():
                radio.setChecked(radio is selected_radio)

            self.sync_mode_group.setExclusive(True)

        # ------------------------------------------------------------
        # First disable all controls inside all 4 rows
        # ------------------------------------------------------------

        # INTERNAL
        self.internal_freq.setEnabled(False)

        # EXTERNAL SINGLE IN
        self.single_source_sync_radio.setEnabled(False)
        self.single_source_clk_radio.setEnabled(False)
        self.external_rate.setEnabled(False)
        self.single_rate_unit.setEnabled(False)

        # EXTERNAL DUAL IN
        self.dual_sync_input.setEnabled(False)
        self.dual_sync_unit.setEnabled(False)
        self.dual_clk_input.setEnabled(False)
        self.dual_clk_unit.setEnabled(False)

        # ONE SHOT
        self.software_trigger.setEnabled(False)
        self.smart_trigger.setEnabled(False)

        # ------------------------------------------------------------
        # Now enable ONLY the selected mode's controls
        # ------------------------------------------------------------

        if self.sync_mode == "Internal":

            self.internal_freq.setEnabled(True)

        elif self.sync_mode == "External SINGLE IN":

            # Enable SINGLE IN controls
            self.single_source_sync_radio.setEnabled(True)
            self.single_source_clk_radio.setEnabled(True)
            self.external_rate.setEnabled(True)
            self.single_rate_unit.setEnabled(True)

            # Default to SYNC IN when entering SINGLE IN
            if (
                not self.single_source_sync_radio.isChecked()
                and not self.single_source_clk_radio.isChecked()
            ):
                self.single_source_sync_radio.setChecked(True)

        elif self.sync_mode == "External DUAL IN":

            self.dual_sync_input.setEnabled(True)
            self.dual_sync_unit.setEnabled(True)
            self.dual_clk_input.setEnabled(True)
            self.dual_clk_unit.setEnabled(True)

        elif self.sync_mode == "One shot trigger":

            self.software_trigger.setEnabled(True)
            self.smart_trigger.setEnabled(True)

        # ------------------------------------------------------------
        # MAIN RADIO BUTTONS MUST ALWAYS REMAIN ENABLED
        # ------------------------------------------------------------

        self.internal_radio.setEnabled(True)
        self.single_radio.setEnabled(True)
        self.dual_radio.setEnabled(True)
        self.oneshot_radio.setEnabled(True)
        
        # ------------------------------------------------------------
        # SINGLE IN sub-options
        # ------------------------------------------------------------

        if self.sync_mode != "External SINGLE IN":
            self.single_source_group.setExclusive(False)
            self.single_source_sync_radio.setChecked(False)
            self.single_source_clk_radio.setChecked(False)
            self.single_source_group.setExclusive(True)
            
        # ------------------------------------------------------------
        # ONE SHOT sub-options
        # ------------------------------------------------------------

        if self.sync_mode != "One shot trigger":
            self.one_shot_group.setExclusive(False)
            self.software_trigger.setChecked(False)
            self.smart_trigger.setChecked(False)
            self.one_shot_group.setExclusive(True)

        # ------------------------------------------------------------
        # Update live parameter
        # ------------------------------------------------------------

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
            self.monitor_live_clk.setText(
                self._format_hz(clk)
            )

        if hasattr(self, "monitor_live_sync"):
            self.monitor_live_sync.setText(
                self._format_hz(sync)
            )

        if hasattr(self, "monitor_live_note"):
            self.monitor_live_note.setText(
                f"Hardware: {display_mode}"
                + (
                    f" | Output: {self._format_hz(out_hz)}"
                    if out_hz is not None else ""
                )
                + (
                    f" | Ratediv: {ratediv}"
                    if ratediv is not None else ""
                )
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

        operations = self.operations
        mode = self.sync_mode

        if mode == "Internal":

            sequence = operations.build_internal_100mhz_from_period(
                period_s=1.0 / 100_000_000.0,
                command_on=False
            )

        elif mode == "External SINGLE IN":

            source = self._single_source_name()

            if source == "CLK IN":
                
                period_s = self._get_sync_output_period_s()

                clk_in_hz = self._sync_value_to_hz(
                    self.external_rate.value(),
                    self.single_rate_unit.currentText()
                )
                
                sequence = operations.build_external_clkin_from_period(
                    period_s=period_s,
                    fext_hz=clk_in_hz,
                    command_on=False,
                    include_readback=False
                )

            elif source == "SYNC IN":

                period_s = self._get_sync_output_period_s()

                sync_in_hz = self._sync_value_to_hz(
                    self.external_rate.value(),
                    self.single_rate_unit.currentText()
                )

                ratediv = self.calculations.calc_rate_divider(
                    period_s,
                    1.0 / sync_in_hz
                )

                sequence = operations.build_external_syncin(
                    ratediv=ratediv,
                    command_on=False
                )

            else:
                return

        elif mode == "External DUAL IN":

            period_s = self._get_sync_output_period_s()

            clk_in_hz = self._sync_value_to_hz(
                self.dual_clk_input.value(),
                self.dual_clk_unit.currentText()
            )

            sync_in_hz = self._sync_value_to_hz(
                self.dual_sync_input.value(),
                self.dual_sync_unit.currentText()
            )

            sequence = operations.build_external_dual_in_from_period(
                period_s=period_s,
                fext_hz=clk_in_hz,
                syncin_hz=sync_in_hz,
                command_on=False
            )

        elif mode == "One shot trigger":

            if self.software_trigger.isChecked():

                sequence = operations.seq_oneshot_software(
                    command_on=False
                )

            elif self.smart_trigger.isChecked():

                sequence = operations.seq_oneshot_smart(
                    command_on=False
                )

            else:
                return

        else:
            return
        
        # Send the generated sequence to TG10
        self.can_backend.send_sequence(
            self.serial_connection,
            sequence,
            label="TG10 Sync"
        )

        # Read back the actual hardware state
        status = self._read_sync_hardware_status()
        detected = self._apply_hardware_sync_status(status)

        self._update_monitor_values()

        self.set_status(
            f"Sync applied: {mode} | TG10 readback: {detected}"
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

        if hasattr(self, "monitor_live_sync"):
            self.monitor_live_sync.setText(sync_text)

        if hasattr(self, "monitor_live_note"):
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
        ranges = (
            {
                "MHz": (20.0, 100.0),
                "kHz": (20000.0, 100000.0),
                "Hz": (2e7, 1e8),
            }
            if source == "CLK IN"
            else
            {
                "MHz": (1e-5, 20.0),
                "kHz": (0.01, 20000.0),
                "Hz": (0.01, 2e7),
            }
        )
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
    
    def _get_sync_output_period_s(self):
        if hasattr(self, "current_period_s"):
            return float(self.current_period_s)

        return self._period_to_s()
    
    def _sync_value_to_hz(self, value, unit):
        factor = {
            "Hz": 1.0,
            "kHz": 1e3,
            "MHz": 1e6,
        }[unit]

        return float(value) * factor
    
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

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(5)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 1)

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

        # ========================================================
        # Configuration modes — single vertical layout
        # ========================================================

        # --------------------------------------------------------
        # Normal
        # --------------------------------------------------------
        normal_box, normal_lay = mode_box()
        mode_radio(normal_lay, "Normal")
        grid.addWidget(normal_box, 0, 0, 1, 2)


        # --------------------------------------------------------
        # Gate
        # --------------------------------------------------------

        gate_box, gate_lay = mode_box()

        # --------------------------------------------------------
        # Main Gate mode radio
        # IMPORTANT:
        # Gate belongs ONLY to config_mode_group.
        # --------------------------------------------------------

        gate_radio = QRadioButton("Gate")
        gate_radio.setMinimumHeight(24)
        gate_radio.setMinimumWidth(65)

        self.config_mode_group.addButton(gate_radio)
        self.config_mode_buttons["Gate"] = gate_radio


        # --------------------------------------------------------
        # GATE / nGATE sub-options
        # --------------------------------------------------------

        gate_group = QButtonGroup(gate_box)
        gate_group.setExclusive(True)

        self.config_gate_group = gate_group
        self.config_gate_buttons = {}

        # GATE
        gate_option = QRadioButton("GATE")
        gate_option.setMinimumWidth(65)
        gate_group.addButton(gate_option, 0)

        self.config_gate_buttons["GATE"] = gate_option

        gate_option.toggled.connect(
            lambda checked: self._save_config_gate("GATE", checked)
        )

        # nGATE
        ngate_option = QRadioButton("nGATE")
        ngate_option.setMinimumWidth(65)
        gate_group.addButton(ngate_option, 1)

        self.config_gate_buttons["nGATE"] = ngate_option

        ngate_option.toggled.connect(
            lambda checked: self._save_config_gate("nGATE", checked)
        )


        # --------------------------------------------------------
        # Put all 3 radios on ONE horizontal line
        # --------------------------------------------------------

        gate_row = QHBoxLayout()
        gate_row.setContentsMargins(0, 0, 0, 0)
        gate_row.setSpacing(40)

        gate_row.addWidget(gate_radio)
        gate_row.addWidget(gate_option)
        gate_row.addWidget(ngate_option)
        gate_row.addStretch()

        gate_lay.addLayout(gate_row)

        grid.addWidget(gate_box, 1, 0, 1, 2)


        # --------------------------------------------------------
        # Burst
        # --------------------------------------------------------
        burst_box, burst_lay = mode_box()

        mode_radio(burst_lay, "Burst")

        # Main horizontal layout:
        #   LEFT  -> Burst trigger options
        #   RIGHT -> Burst count
        burst_content = QHBoxLayout()
        burst_content.setContentsMargins(0, 2, 0, 0)
        burst_content.setSpacing(18)

        # -------------------------
        # Left: Burst trigger
        # -------------------------
        trigger_section = QVBoxLayout()
        trigger_section.setContentsMargins(0, 0, 0, 0)
        trigger_section.setSpacing(3)

        trigger_section.addWidget(
            label("Burst trigger", "FieldLabel", bold=True)
        )

        burst_group = QButtonGroup(burst_box)
        burst_group.setExclusive(True)

        self.config_burst_group = burst_group
        self.config_burst_buttons = {}

        trigger_grid = QGridLayout()
        trigger_grid.setContentsMargins(0, 0, 0, 0)
        trigger_grid.setHorizontalSpacing(18)
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

            r.toggled.connect(
                lambda checked, value=option:
                self._save_config_burst_source(value, checked)
            )

            trigger_grid.addWidget(r, row, col)

        trigger_section.addLayout(trigger_grid)

        burst_content.addLayout(trigger_section, 2)


        # -------------------------
        # Right: Burst count
        # -------------------------
        count_section = QVBoxLayout()
        count_section.setContentsMargins(0, 0, 0, 0)
        count_section.setSpacing(3)

        count_section.addWidget(
            label("Burst count", "FieldLabel", bold=True)
        )

        self.burst_count_widget = QSpinBox()
        self.burst_count_widget.setRange(1, 65535)
        self.burst_count_widget.setValue(1)
        self.burst_count_widget.setMinimumHeight(28)
        self.burst_count_widget.valueChanged.connect(
            self._save_config_burst_count
        )

        count_section.addWidget(self.burst_count_widget)
        count_section.addStretch()

        burst_content.addLayout(count_section, 1)

        burst_lay.addLayout(burst_content)

        grid.addWidget(burst_box, 2, 0, 1, 2)


        # --------------------------------------------------------
        # Frequency divider
        # --------------------------------------------------------
        divider_box, divider_lay = mode_box()

        mode_radio(divider_lay, "Frequency divider")

        divider_lay.addWidget(
            label("Division of Freq", "FieldLabel", bold=True)
        )

        self.config_divider_widget = QSpinBox()
        self.config_divider_widget.setRange(1, 32767)
        self.config_divider_widget.setValue(1)
        self.config_divider_widget.setMinimumHeight(28)

        self.config_divider_widget.valueChanged.connect(
            self._save_config_divider
        )

        divider_lay.addWidget(self.config_divider_widget)

        grid.addWidget(divider_box, 3, 0, 1, 2)
        body.addLayout(grid, 1)

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
        """Allow Configuration 1 / 2 to fill the same vertical space as Sync."""
        if not hasattr(self, "_config_card_frame"):
            return

        self._config_card_frame.setMinimumHeight(0)
        self._config_card_frame.setMaximumHeight(16777215)
        self._config_card_frame.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
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
            import calculations02_ as calculations
            import menu02_ as menu

            self.can_backend = can_backend
            self.can_reader = can_reader
            self.monitor_backend = monitor_backend
            self.calculations = calculations
            self.operations = operations
            self.menu = menu

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
            self.calculations = None
            self.connection_state = False

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

        if not hasattr(self, "delay_dialog"):

            self.delay_dialog = DelayDialog(
                self
            )

        self.delay_dialog.exec()

    # ========================================================
    # CLOCK / SYNC CONTEXT  (used by Delay presets AND the simulator)
    # ========================================================

    # ASSUMED PLL multiplier: system clock = reference clock x Ndiv.
    # Internal: 100 MHz x 30 = 3 GHz (as documented in DelayDialog).
    # Verify against the TG10 manual; it can also be changed in the simulator window.
    system_ndiv = 30

    def sync_context(self):
        """Reference / system clocks implied by the current Sync configuration."""
        mode = getattr(self, "sync_mode", "Internal")
        f_clk, f_sync, src, kind = 100e6, None, "internal", None
        try:
            if mode == "External SINGLE IN":
                hz = self._sync_value_to_hz(self.external_rate.value(), self.single_rate_unit.currentText())
                if self._single_source_name() == "CLK IN":
                    f_clk, src = hz, "CLK IN"
                else:
                    f_sync, src = hz, "SYNC IN"
            elif mode == "External DUAL IN":
                f_clk = self._sync_value_to_hz(self.dual_clk_input.value(), self.dual_clk_unit.currentText())
                f_sync = self._sync_value_to_hz(self.dual_sync_input.value(), self.dual_sync_unit.currentText())
                src = "CLK IN + SYNC IN"
            elif mode == "One shot trigger":
                src = "one-shot"
                kind = "smart" if self.smart_trigger.isChecked() else "software"
        except Exception:
            f_clk, f_sync, src, kind = 100e6, None, "internal", None
        return sync_ctx(mode, src, f_clk, f_sync, self.system_ndiv, kind)

    def system_clock_hz(self, channel=None):
        """DEL4 (fine*) always counts from the INTERNAL clock; other outputs follow the active reference."""
        c = self.sync_context()
        return c["f_sys_int"] if channel == 4 else c["f_sys"]

    def open_simulator(self):

        if not hasattr(self, "simulator_dialog"):
            self.simulator_dialog = SimulatorDialog(self)

        self.simulator_dialog.show()
        self.simulator_dialog.raise_()
        self.simulator_dialog.activateWindow()

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
# TG10 SIMULATOR + POCKELS-CELL PLANNER  (added module)
# ============================================================
# Opens from the "Simulator / Pockels" navigation button.
#  - Reads DEL0-DEL7 and Post-delay (pulse width) values from the Delay-presets dialog
#  - Simulates what the 8 outputs do (scope view: zoom / pan / X1-X2 cursors)
#  - For every output: models driver delay, HV edges, Pockels transmission vs the laser
#    pulse train, and suggests DEL / width values before you hand them to the HV driver.
import math as _m

SIM_COLORS = ["#119447", "#d98200", "#0878c9", "#c2368f", "#6b4fd8", "#c24a1f", "#0f8f8f", "#8a8f00"]
SIM_BG = QColor(5, 10, 6)
SIM_GRID = QColor(18, 48, 22)
SIM_GRID2 = QColor(29, 74, 34)
SIM_DIM = QColor(124, 156, 130)
# Step sizes at the internal 3 GHz system clock (100 MHz x Ndiv 30). Steps scale with 1/f_sys for
# DEL0-3 and DEL5-7 (they follow CLK IN). DEL4 (fine*) always runs from the INTERNAL clock.
BASE_DELAY_STEP_NS = [0.025, 0.025, 0.025, 0.025, 0.025, 9.4, 9.4, 9.4]
MIN_WIDTH_NS = 4.0

CELL_PRESETS = {      # illustrative half-wave voltages - ALWAYS replace with your datasheet value
    "KD*P longitudinal, 1064 nm (typ.)": 6.5,
    "KD*P longitudinal, 532 nm (typ.)": 3.3,
    "BBO transverse (typ.)": 6.0,
    "RTP (typ.)": 1.8,
    "LiNbO3 (typ.)": 3.0,
    "Custom (enter datasheet Vπ)": 5.0,
}
CELL_MODES = {
    "Pulse picker / gate: crossed polarizers, HV ON = transmit": (1, False),
    "Double pass (mirror / regen): crossed polarizers, HV ON = transmit": (2, False),
    "Parallel polarizers: HV ON = BLOCK": (1, True),
}


def s_fmt_ns(v):
    a = abs(v)
    if a >= 1e9:
        return f"{v/1e9:.3f} s"
    if a >= 1e6:
        return f"{v/1e6:.3f} ms"
    if a >= 1e3:
        return f"{v/1e3:.3f} µs"
    if a >= 1:
        return f"{v:.3f} ns"
    return f"{v*1e3:.1f} ps"


def s_fmt_freq(hz):
    if not _m.isfinite(hz):
        return "—"
    a = abs(hz)
    if a >= 1e6:
        return f"{hz/1e6:.4f} MHz"
    if a >= 1e3:
        return f"{hz/1e3:.4f} kHz"
    return f"{hz:.3f} Hz"


def s_nice_step(span):
    raw = span / 10.0
    if raw <= 0:
        return 1.0
    mag = 10 ** _m.floor(_m.log10(raw))
    n = raw / mag
    return (1 if n < 1.5 else 2 if n < 3.5 else 5 if n < 7.5 else 10) * mag


# ------------------------------------------------------------
# Pockels physics model
# ------------------------------------------------------------
def sync_ctx(mode, src, f_clk, f_sync, ndiv, kind=None):
    """Clock context for one Sync-card configuration (same rules as the main window's Sync card)."""
    f_int = 100e6
    uses_clk = src in ("CLK IN", "CLK IN + SYNC IN")
    uses_sync = src in ("SYNC IN", "CLK IN + SYNC IN")
    f_ref = f_clk if uses_clk else f_int
    return dict(mode=mode, src=src, f_int=f_int, f_ref=f_ref, f_sync=(f_sync if uses_sync else None), ndiv=ndiv,
                f_sys=f_ref * ndiv, f_sys_int=f_int * ndiv, ext_clk=uses_clk, kind=kind)


SYNC_CHOICES = [   # label, mode, source, kind
    ("Internal clock (100 MHz)", "Internal", "internal", None),
    ("External SINGLE IN · CLK IN", "External SINGLE IN", "CLK IN", None),
    ("External SINGLE IN · SYNC IN", "External SINGLE IN", "SYNC IN", None),
    ("External DUAL IN · CLK IN + SYNC IN", "External DUAL IN", "CLK IN + SYNC IN", None),
    ("One shot trigger · Software", "One shot trigger", "one-shot", "software"),
    ("One shot trigger · Smart", "One shot trigger", "one-shot", "smart"),
]


def pockels_analyze(period, rE, fE, P, res_del, res_w):
    """TG10 edges -> driver delay -> HV edge shaping -> sin^2 transmission -> per-laser-pulse energy."""
    d, tr, tf, V = P["drv"], P["tr"], P["tf"], P["v"]
    vpi, k, inv, er = P["vpi"], P["k"], P["inv"], max(P["er"], 1.0)
    TL = 1000.0 / P["laser_mhz"]
    sig = max(P["fwhm"] / 2.355, 1e-4)

    def edge(t, t0, w):
        if w <= 1e-3:
            return 1.0 if t >= t0 else 0.0
        return 0.5 * (1 + _m.erf((t - t0) / (w / 2.563 * _m.sqrt(2))))

    tdec = P.get("tdec")

    def hv(t):
        v = 0.0
        for n in (-1, 0, 1):
            b = n * period
            dv = edge(t, b + rE + d, tr) - edge(t, b + fE + d, tf)
            if tdec:                                  # flat-top droop, tau = 33 MOhm x C_cell (driver manual)
                dv *= _m.exp(-max(0.0, t - (b + rE + d)) / tdec)
            v += dv
        return V * v

    def trans(v):
        sm = _m.sin(_m.pi / 2 * k * v / vpi) ** 2
        if inv:
            sm = 1 - sm
        return (1 - 1 / er) * sm + (1 / er) * (1 - sm)

    eo, ec = rE + d, fE + d
    m = max(3 * TL, 4 * max(tr, tf), 40.0)
    t0, t1 = eo - m, ec + m
    if t1 - t0 > 300 * TL:
        t1 = t0 + 300 * TL
    pulses = []
    for n in range(_m.ceil((t0 - P["arr"]) / TL), _m.floor((t1 - P["arr"]) / TL) + 1):
        tk = P["arr"] + n * TL
        acc = ws = 0.0
        for j in range(-10, 11):
            x = j * 0.35
            w = _m.exp(-x * x / 2)
            acc += w * trans(hv(tk + x * sig))
            ws += w
        pulses.append((tk, acc / ws))

    N = 1200
    ts = [t0 + (t1 - t0) * i / N for i in range(N + 1)]
    Tv = [trans(hv(t)) for t in ts]
    t_open = t_close = None
    for i in range(1, N + 1):
        up = Tv[i - 1] < 0.5 <= Tv[i]
        dn = Tv[i - 1] >= 0.5 > Tv[i]
        if (up and not inv) or (dn and inv):
            t_open = t_open if t_open is not None else ts[i]
        if (dn and not inv) or (up and inv):
            t_close = ts[i]

    sel = max(pulses, key=lambda p: p[1]) if pulses else None
    if sel and sel[1] < 0.05:
        sel = min(pulses, key=lambda p: abs(p[0] - (eo + ec) / 2))
    sug = None
    mo = 0.5 * tr + 1.5 * P["fwhm"]
    mc = 0.5 * tf + 1.5 * P["fwhm"]
    if sel and sel[0] - d - mo < 0:        # that pulse arrives too early to be gated: use the next reachable one
        cand = [p for p in pulses if p[0] - d - mo >= 0]
        if cand:
            sel = min(cand, key=lambda p: p[0])
    if sel:
        rise = round((sel[0] - d - mo) / res_del) * res_del
        width = max(MIN_WIDTH_NS, round((mo + mc) / res_w) * res_w)
        sug = dict(rise=rise, width=width, mo=mo, mc=mc, t=sel[0],
                   feasible=(mo + 3 * sig < TL) and (mc + 3 * sig < TL), neg=rise < 0)
    return dict(rE=rE, fE=fE, eo=eo, ec=ec, TL=TL, sig=sig, t0=t0, t1=t1, pulses=pulses, hv=hv, T=trans,
                t_open=t_open, t_close=t_close, sug=sug, sel=sel)


def pockels_verdict(r):
    pl = r["pulses"]
    ok = [p for p in pl if p[1] > 0.9]
    part = [p for p in pl if 0.05 < p[1] <= 0.9]
    if len(ok) == 1 and not part:
        return "Single pulse OK", "#119447"
    if not ok and not part:
        return "Misses pulse train", "#d83b3b"
    if len(ok) > 1:
        return f"{len(ok)} pulses pass (burst)", "#d98200"
    return "Pulse clipped on edge", "#d98200"


class PockelsView(QWidget):
    def __init__(self):
        super().__init__()
        self.res = None
        self.P = None
        self.period = 1000.0
        self.setMinimumHeight(400)

    def paintEvent(self, _):
        p = QPainter(self)
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, SIM_BG)
        r, P = self.res, self.P
        if not r:
            p.setPen(SIM_DIM)
            p.drawText(self.rect(), Qt.AlignCenter, "Enable a Pockels cell on this output to see the optical gate")
            p.end()
            return
        t0, t1 = r["t0"], r["t1"]
        span = max(t1 - t0, 1e-9)
        px = lambda t: (t - t0) / span * W
        sf = QFont("Consolas", 8)
        lf = QFont("Segoe UI", 9)
        step = s_nice_step(span) * 2
        p.setFont(sf)
        t = _m.ceil(t0 / step) * step
        while t <= t1:
            p.setPen(QPen(SIM_GRID, 1))
            p.drawLine(QPointF(px(t), 6), QPointF(px(t), H - 20))
            p.setPen(SIM_DIM)
            p.drawText(QPointF(px(t) + 2, H - 6), s_fmt_ns(t))
            t += step
        p.setFont(lf)
        p.setPen(QColor(147, 168, 147))
        for name, top in (("TG10 OUTPUT (realized edges)", 22), ("HV AT POCKELS CELL (driver delay + edge time)", 124),
                          ("OPTICAL TRANSMISSION + LASER PULSES (green pass / yellow clipped / red blocked)", 240)):
            p.drawText(QPointF(8, top - 6), name)

        def trace(fn, top, h, color, wpx):
            path = QPainterPath()
            n = max(200, W // 2)
            for i in range(n + 1):
                tt = t0 + span * i / n
                y = top + (1 - fn(tt)) * h
                (path.lineTo if i else path.moveTo)(i / n * W, y)
            p.setPen(QPen(color, wpx))
            p.drawPath(path)

        trace(lambda tt: 1.0 if any(r["rE"] <= tt - n * self.period < r["fE"] for n in (-1, 0, 1)) else 0.0,
              22, 60, QColor(255, 180, 84), 2.4)
        top, h = 124, 90
        vmax = max(P["v"], P["vpi"] / P["k"]) * 1.1 or 1
        trace(lambda tt: r["hv"](tt) / vmax, top, h, QColor(255, 120, 120), 2.2)
        yf = top + (1 - (P["vpi"] / P["k"]) / vmax) * h
        p.setPen(QPen(QColor(255, 255, 255, 110), 1, Qt.DashLine))
        p.drawLine(QPointF(0, yf), QPointF(W, yf))
        p.setFont(sf)
        p.drawText(QPointF(W - 200, yf - 3), f"full open V = {P['vpi']/P['k']:.2f} kV")
        p.setPen(QColor(255, 120, 120))
        p.drawText(QPointF(W - 200, top + h + 12), f"applied = {P['v']:.2f} kV")
        top, h = 240, 110
        trace(lambda tt: r["T"](r["hv"](tt)), top, h, QColor(90, 217, 255), 2.2)
        sg = r["sig"]
        for tk, fr in r["pulses"]:
            col = QColor(80, 220, 120) if fr > 0.9 else QColor(255, 210, 60) if fr > 0.05 else QColor(255, 80, 80)
            path = QPainterPath()
            path.moveTo(px(tk - 4 * sg), top + h)
            for i in range(-20, 21):
                x = i * 0.2
                path.lineTo(px(tk + x * sg), top + h - 0.85 * h * _m.exp(-x * x / 2))
            path.lineTo(px(tk + 4 * sg), top + h)
            c2 = QColor(col)
            c2.setAlpha(110)
            p.fillPath(path, c2)
            p.setPen(QPen(col, 1.2))
            p.drawLine(QPointF(px(tk), top + h), QPointF(px(tk), top + h * 0.12))
            if 10 < px(tk) < W - 30 and r["TL"] / span * W > 34:
                p.setFont(sf)
                p.drawText(QPointF(px(tk) - 12, top + h * 0.12 - 3), f"{fr*100:.0f}%")
        for key, lab in (("t_open", "OPEN 50%"), ("t_close", "CLOSE 50%")):
            tt = r[key]
            if tt is not None:
                p.setPen(QPen(QColor(255, 255, 255, 150), 1, Qt.DashLine))
                p.drawLine(QPointF(px(tt), 6), QPointF(px(tt), H - 20))
                p.setFont(sf)
                p.drawText(QPointF(px(tt) + 3, 14), lab)
        p.end()


# ------------------------------------------------------------
# Scope: TRIG + OUT0..OUT7
# ------------------------------------------------------------
class SimScope(QWidget):
    moved = Signal()

    def __init__(self, dlg):
        super().__init__()
        self.d = dlg
        self.setMinimumHeight(360)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self._drag = None

    def _win(self):
        span = self.d.ns_per_div * 10
        return self.d.center - span / 2, self.d.center + span / 2

    def ns_of(self, x):
        a, b = self._win()
        return a + x / max(self.width(), 1) * (b - a)

    def px_of(self, t):
        a, b = self._win()
        return (t - a) / (b - a) * self.width()

    def mousePressEvent(self, ev):
        mx, my = ev.position().x(), ev.position().y()
        p1, p2 = self.px_of(self.d.cursor1), self.px_of(self.d.cursor2)
        if my < 26 and abs(mx - p1) < 16 and abs(mx - p1) <= abs(mx - p2) + 0.001 or abs(mx - p1) < 7:
            self._drag = {"t": "c1"}
        elif (my < 26 and abs(mx - p2) < 16) or abs(mx - p2) < 7:
            self._drag = {"t": "c2"}
        else:
            self._drag = {"t": "pan", "x": mx, "c": self.d.center}

    def mouseMoveEvent(self, ev):
        if not self._drag:
            return
        x = ev.position().x()
        if self._drag["t"] == "pan":
            self.d.center = self._drag["c"] - (x - self._drag["x"]) / self.width() * self.d.ns_per_div * 10
        elif self._drag["t"] == "c1":
            self.d.cursor1 = self.ns_of(x)
        else:
            self.d.cursor2 = self.ns_of(x)
        self.moved.emit()
        self.update()

    def mouseReleaseEvent(self, ev):
        self._drag = None

    def wheelEvent(self, ev):
        a, b = self._win()
        span = b - a
        pivot = self.ns_of(ev.position().x())
        f = 1.15 if ev.angleDelta().y() < 0 else 1 / 1.15
        ns = min(1e10, max(0.05, span * f))
        start = pivot - (pivot - a) * (ns / span)
        self.d.center = start + ns / 2
        self.d.ns_per_div = ns / 10
        self.moved.emit()
        self.update()

    def paintEvent(self, _):
        d = self.d
        p = QPainter(self)
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, SIM_BG)
        a, b = self._win()
        span = b - a
        px = lambda t: (t - a) / span * W
        sf = QFont("Consolas", 8)
        p.setFont(sf)
        step = s_nice_step(span)
        t = _m.ceil(a / step) * step
        while t <= b:
            strong = round(t / step) % 5 == 0
            p.setPen(QPen(SIM_GRID2 if strong else SIM_GRID, 1))
            p.drawLine(QPointF(px(t), 12), QPointF(px(t), H - 26))
            p.setPen(SIM_DIM)
            lab = s_fmt_ns(t)
            fm = QFontMetrics(sf)
            p.drawText(QPointF(min(max(px(t) - fm.horizontalAdvance(lab) / 2, 2), W - fm.horizontalAdvance(lab) - 2), H - 8), lab)
            t += step
        vis = [i for i in range(8) if d.rows[i]["show"].isChecked()]
        lk = hasattr(d, "setup") and d.setup.ck_link.isChecked()
        lanes = (["sync"] if d.ctx["f_sync"] else []) + [None] + (["hv"] if lk else []) + vis
        top0, avail = 26, H - 26 - 30
        lh = min(64.0, avail / max(len(lanes), 1))
        P = d.period
        for k, ch in enumerate(lanes):
            y0 = top0 + k * lh
            hi, lo = y0 + lh * 0.16, y0 + lh * 0.82
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            if ch == "sync":
                Ts = 1e9 / d.ctx["f_sync"]
                p.setPen(QColor(150, 200, 255))
                p.drawText(QPointF(6, y0 + 11), f"SYNC IN {s_fmt_freq(d.ctx['f_sync'])}")
                nrd = max(1, round(P / Ts))
                if (b - a) / Ts > 3000:
                    p.drawText(QPointF(170, y0 + 11), "(zoom in to resolve the SYNC IN edges)")
                else:
                    n0 = _m.floor(a / Ts)
                    for n in range(n0, n0 + int((b - a) / Ts) + 2):
                        tt = n * Ts
                        if a <= tt <= b:
                            used = d.oneshot is False and (n % nrd == 0)
                            p.setPen(QPen(QColor(120, 190, 255) if used else QColor(70, 100, 140), 2.2 if used else 1.0))
                            p.drawLine(QPointF(px(tt), lo), QPointF(px(tt), hi if used else (hi + lo) / 2))
                continue
            if ch is None:
                p.setPen(QColor(230, 230, 230))
                p.drawText(QPointF(6, y0 + 11), "TRIG")
                n = _m.floor(a / P)
                cnt = 0
                while n * P <= b and cnt < 4000:
                    if n * P >= a:
                        p.setPen(QPen(QColor(255, 255, 255, 140), 1.4))
                        p.drawLine(QPointF(px(n * P), lo), QPointF(px(n * P), hi))
                    n += 1
                    cnt += 1
                continue
            if ch == "hv":
                col = QColor(255, 110, 110)
                rE, fE = d.gate_edges(d.setup.a())
                rE, fE = rE + DPB_DELAY_NS, fE + DPB_DELAY_NS
                tag = f"HV at cell (DPB1, {d.setup.mode()}-input)"
            else:
                col = QColor(SIM_COLORS[ch]).lighter(150)
                rE, fE = d.edges(ch)
                tag = f"OUT{ch}"
                if lk and ch == d.setup.a():
                    tag += " ▸ X1 (HV on" + (" / off)" if d.setup.mode() == 1 else ")")
                elif lk and ch == d.setup.b() and d.setup.mode() == 2:
                    tag += " ▸ X2 (HV off)"
            p.setPen(col)
            p.drawText(QPointF(6, y0 + 11), tag)
            n_lo, n_hi = _m.floor((a - fE) / P), _m.ceil((b - rE) / P)
            if n_hi - n_lo > 1500 or (fE - rE) / span * W < 0.5 and P / span * W < 3:
                c = QColor(col)
                c.setAlpha(60)
                p.fillRect(QRectF(0, hi, W, lo - hi), c)
                p.setPen(col)
                p.drawText(QPointF(60, y0 + 11), f"{s_fmt_freq(1e9/P)} repetition - zoom in to resolve pulses")
                continue
            path = QPainterPath()
            path.moveTo(0, lo)
            for n in range(n_lo, n_hi + 1):
                x1, x2 = px(rE + n * P), px(fE + n * P)
                path.lineTo(x1, lo)
                path.lineTo(x1, hi)
                path.lineTo(x2, hi)
                path.lineTo(x2, lo)
            path.lineTo(W, lo)
            p.setPen(QPen(col, 2.2 if ch == d.sel else 1.6))
            p.drawPath(path)
            if ch == d.sel:
                y = lo + 2
                for n in range(n_lo, n_hi + 1):
                    x1, x2 = px(rE + n * P), px(fE + n * P)
                    if x2 > x1 and -50 < x1 < W + 50:
                        p.setPen(QPen(QColor(255, 207, 138), 1.2))
                        p.drawLine(QPointF(x1, y), QPointF(x2, y))
                        p.setFont(sf)
                        lab = f"w={s_fmt_ns(fE-rE)}"
                        p.drawText(QPointF((x1 + x2) / 2 - 20, y + 10), lab)
                        break
        for cur, colr, lab in ((d.cursor1, QColor(90, 217, 255), "X1"), (d.cursor2, QColor(255, 90, 208), "X2")):
            x = px(cur)
            path = QPainterPath()
            path.moveTo(x - 8, 2)
            path.lineTo(x + 8, 2)
            path.lineTo(x, 16)
            path.closeSubpath()
            p.fillPath(path, colr)
            p.setPen(QPen(colr, 1.5, Qt.DashLine))
            p.drawLine(QPointF(x, 16), QPointF(x, H - 26))
            p.setPen(QColor(8, 17, 10))
            p.setFont(QFont("Consolas", 8, QFont.Bold))
            p.drawText(QPointF(x - 6, 11), lab)
        p.end()


# ------------------------------------------------------------
# Pockels planner tab
# ------------------------------------------------------------
class PockelsPlanner(QWidget):
    def __init__(self, dlg):
        super().__init__()
        self.d = dlg
        self.params = [dict(en=(i == 0), cell=list(CELL_PRESETS)[0], mode=0, vpi=6.5, v=6.5, drv=20.0,
                            tr=5.0, tf=5.0, er=1000.0, arr=130.0) for i in range(8)]
        self.res = [None] * 8
        self._loading = False
        root = QHBoxLayout(self)
        left = QVBoxLayout()
        root.addLayout(left, 0)
        right = QVBoxLayout()
        root.addLayout(right, 1)

        def spin(lo, hi, val, dec, suf):
            s = QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setDecimals(dec)
            s.setValue(val)
            s.setSuffix(suf)
            s.valueChanged.connect(self._store)
            return s

        g0 = QGroupBox("Laser pulse train (shared)")
        l0 = QGridLayout(g0)
        self.lrep = spin(0.0001, 2000, 5, 4, " MHz")
        self.lfw = spin(0.0005, 1e5, 10, 3, " ns")
        l0.addWidget(QLabel("Rep rate"), 0, 0)
        l0.addWidget(self.lrep, 0, 1)
        l0.addWidget(QLabel("Pulse FWHM"), 1, 0)
        l0.addWidget(self.lfw, 1, 1)
        left.addWidget(g0)

        g1 = QGroupBox("TG10 output driving this cell")
        l1 = QGridLayout(g1)
        self.cb_ch = QComboBox()
        self.cb_ch.addItems([f"OUT{i}  (DEL{i} + post-DEL{i})" for i in range(8)])
        self.cb_ch.currentIndexChanged.connect(self._channel_changed)
        self.cb_en = QCheckBox("Pockels cell attached to this output")
        self.cb_en.toggled.connect(self._store)
        l1.addWidget(self.cb_ch, 0, 0, 1, 2)
        l1.addWidget(self.cb_en, 1, 0, 1, 2)
        left.addWidget(g1)

        g2 = QGroupBox("Pockels cell && HV driver (this output)")
        l2 = QGridLayout(g2)
        self.cb_cell = QComboBox()
        self.cb_cell.addItems(CELL_PRESETS.keys())
        self.cb_cell.activated.connect(self._preset)
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(CELL_MODES.keys())
        self.cb_mode.activated.connect(lambda *_: (self._full_open(), self._store()))
        self.vpi = spin(0.05, 50, 6.5, 3, " kV")
        self.v = spin(0, 50, 6.5, 3, " kV")
        self.drv = spin(0, 1e6, 20, 3, " ns")
        self.tr = spin(0, 1e5, 5, 3, " ns")
        self.tf = spin(0, 1e5, 5, 3, " ns")
        self.er = spin(1, 1e6, 1000, 0, " :1")
        self.arr = spin(-1e9, 1e10, 130, 3, " ns")
        rows = [("Cell type", self.cb_cell), ("Mode", self.cb_mode), ("Half-wave Vπ", self.vpi),
                ("HV applied", self.v), ("Driver+cable delay", self.drv), ("HV rise 10-90 %", self.tr),
                ("HV fall 90-10 %", self.tf), ("Static extinction", self.er), ("Laser pulse #0 at cell", self.arr)]
        for i, (n, w) in enumerate(rows):
            l2.addWidget(QLabel(n), i, 0)
            l2.addWidget(w, i, 1)
        b1 = QPushButton("Set V = full open")
        b1.clicked.connect(lambda: (self._full_open(), self._store()))
        l2.addWidget(b1, len(rows), 0, 1, 2)
        left.addWidget(g2)
        b2 = QPushButton("Apply suggested DEL / width to Simulator values")
        b2.clicked.connect(self._apply_suggestion)
        left.addWidget(b2)
        left.addStretch(1)

        self.view = PockelsView()
        right.addWidget(self.view, 1)
        box = "background:#f4f8fb; border:1px solid #c5d4e2; border-radius:4px; padding:6px;"
        self.t_delay = QLabel()
        self.t_res = QLabel()
        for t in (self.t_delay, self.t_res):
            t.setTextFormat(Qt.RichText)
            t.setWordWrap(True)
            t.setStyleSheet(box)
            right.addWidget(t)
        self._load_ui()

    # --- parameter plumbing ---
    def _load_ui(self):
        P = self.params[self.d.sel]
        self._loading = True
        self.cb_ch.setCurrentIndex(self.d.sel)
        for w, v in ((self.vpi, P["vpi"]), (self.v, P["v"]), (self.drv, P["drv"]), (self.tr, P["tr"]),
                     (self.tf, P["tf"]), (self.er, P["er"]), (self.arr, P["arr"])):
            w.setValue(v)
        self.cb_en.setChecked(P["en"])
        self.cb_cell.setCurrentText(P["cell"])
        self.cb_mode.setCurrentIndex(P["mode"])
        self._loading = False
        self._lk_state = False
        self._sync_link_ui()

    def _sync_link_ui(self):
        """For the output wired to the DPB1 driver, driver/cell values come from the Setup tab."""
        lk = self.d.setup.link_params(self.d.sel)
        self._loading = True
        ws = (self.cb_cell, self.cb_mode, self.vpi, self.v, self.drv, self.tr, self.tf, self.cb_en)
        for w in ws:
            w.setEnabled(lk is None)
        if lk:
            self.cb_cell.setCurrentText(lk["cell"])
            self.cb_mode.setCurrentIndex(lk["mode"])
            for w, key in ((self.vpi, "vpi"), (self.v, "v"), (self.drv, "drv"), (self.tr, "tr"), (self.tf, "tf")):
                w.setValue(lk[key])
            self.cb_en.setChecked(True)
        elif getattr(self, "_lk_state", False):
            P = self.params[self.d.sel]
            for w, key in ((self.vpi, "vpi"), (self.v, "v"), (self.drv, "drv"), (self.tr, "tr"), (self.tf, "tf")):
                w.setValue(P[key])
            self.cb_en.setChecked(P["en"])
            self.cb_cell.setCurrentText(P["cell"])
            self.cb_mode.setCurrentIndex(P["mode"])
        self._lk_state = bool(lk)
        self._loading = False

    def _channel_changed(self, i):
        if not self._loading:
            self.d.set_sel(i)

    def _store(self, *_):
        if self._loading:
            return
        P = self.params[self.d.sel]
        P.update(en=self.cb_en.isChecked(), cell=self.cb_cell.currentText(), mode=self.cb_mode.currentIndex(),
                 vpi=self.vpi.value(), v=self.v.value(), drv=self.drv.value(), tr=self.tr.value(),
                 tf=self.tf.value(), er=self.er.value(), arr=self.arr.value())
        self.refresh()

    def _preset(self, *_):
        self.vpi.blockSignals(True)
        self.vpi.setValue(CELL_PRESETS[self.cb_cell.currentText()])
        self.vpi.blockSignals(False)
        self._full_open()
        self._store()

    def _full_open(self):
        k, _inv = CELL_MODES[self.cb_mode.currentText()]
        self.v.blockSignals(True)
        self.v.setValue(self.vpi.value() / k)
        self.v.blockSignals(False)

    def full_params(self, ch):
        P = dict(self.params[ch])
        k, inv = CELL_MODES[list(CELL_MODES)[P["mode"]]]
        P.update(k=k, inv=inv, laser_mhz=self.lrep.value(), fwhm=self.lfw.value())
        lk = self.d.setup.link_params(ch)
        if lk:
            P.update(lk)
        return P

    def analyze(self, ch):
        rE, fE = self.d.gate_edges(ch)
        return pockels_analyze(self.d.period, rE, fE, self.full_params(ch), self.d.delay_step(ch), self.d.width_res(ch))

    def _apply_suggestion(self):
        r = self.res[self.d.sel]
        if r and r["sug"]:
            self.d.apply_gate_suggestion(self.d.sel, r["sug"]["rise"], r["sug"]["width"])

    # --- recompute ---
    def refresh(self):
        d = self.d
        self._sync_link_ui()
        for ch in range(8):
            en = self.params[ch]["en"] or bool(d.setup.link_params(ch))
            self.res[ch] = self.analyze(ch) if en else None
        ch = d.sel
        r = self.res[ch]
        self.view.P = self.full_params(ch) if r else None
        self.view.res = r
        self.view.period = d.period
        self.view.update()
        if not r:
            self.t_delay.setText("<b>No Pockels cell attached to OUT%d.</b> Tick the box on the left to see how its "
                                 "DEL / post-delay values act on the cell." % ch)
            self.t_res.setText("")
        else:
            self._texts(ch, r)

    def _texts(self, ch, r):
        d, P = self.d, self.full_params(ch)
        prog_del = d.rows[ch]["del"].value()
        prog_pw = d.rows[ch]["pw"].value()
        rE, fE = r["rE"], r["fE"]
        vfull = P["vpi"] / P["k"]
        topen = _m.sin(_m.pi / 2 * P["k"] * P["v"] / P["vpi"]) ** 2
        topen = 1 - topen if P["inv"] else topen
        to, tc = r["t_open"], r["t_close"]
        gw = (tc - to) if (to is not None and tc is not None) else None
        h = f"<b style='color:#0b4778'>WHAT OUT{ch} DOES AT THE POCKELS CELL</b><br>"
        if d.setup.link_params(ch):
            h += d.setup.describe(ch, r, P)
        else:
            h += (f"<b>DEL{ch} (rise)</b>: programmed {s_fmt_ns(prog_del)} → realized {s_fmt_ns(rE)} "
                  f"(step {s_fmt_ns(d.delay_step(ch))}, error {s_fmt_ns(rE-prog_del)}) → +{s_fmt_ns(P['drv'])} driver/cable "
                  f"→ HV starts {s_fmt_ns(r['eo'])}, 90 % at {s_fmt_ns(r['eo'] + 0.5*P['tr'])} → optical gate OPENS (T=50 %) at "
                  f"<b>{s_fmt_ns(to) if to is not None else 'never'}</b>. Light arriving earlier is rejected.<br>")
            gap = d.sync_gap(ch)
            h += (f"<b>Post-DEL{ch} (width)</b>: programmed {s_fmt_ns(prog_pw)} → realized {s_fmt_ns(fE-rE-gap)}"
                  + (f" + {s_fmt_ns(gap)} fall-path sync gap" if gap else "") + f" → falling edge "
                  f"{s_fmt_ns(fE)} → HV off {s_fmt_ns(r['ec'])} → gate CLOSES (T=50 %) at "
                  f"<b>{s_fmt_ns(tc) if tc is not None else 'never'}</b>. Light arriving later is rejected.<br>")
        h += (f"<b>Optical window</b> = <b>{s_fmt_ns(gw) if gw is not None else '—'}</b> "
              f"(TG10 width {s_fmt_ns(fE-rE)}; difference comes from HV rise/fall asymmetry). "
              f"Open-state transmission at {P['v']:.2f} kV: <b>{topen*100:.1f} %</b> (full open needs {vfull:.2f} kV).")
        self.t_delay.setText(h)

        pl = r["pulses"]
        part = [p for p in pl if 0.05 < p[1] <= 0.9]
        blocked = [p[1] for p in pl if p[1] <= 0.05]
        vt, vc = pockels_verdict(r)
        m = [f"<b style='color:{vc}'>VERDICT: {vt}</b>"]
        if part:
            m.append("Clipped: " + ", ".join(f"{p[1]*100:.0f} % @ {s_fmt_ns(p[0])}" for p in part[:4]) +
                     " - move DEL or lengthen width (or accept energy loss / pulse-shape change).")
        if blocked and r["sel"]:
            leak = max(blocked)
            m.append(f"Worst leak of rejected pulses: <b>{leak*100:.3f} %</b> (static limit {100/P['er']:.3f} %), "
                     f"contrast ≈ <b>{r['sel'][1]/max(leak,1e-12):.0f}:1</b>.")
        N = d.period / r["TL"]
        m.append(f"Laser period {s_fmt_ns(r['TL'])}; TG10 period / laser period = <b>{N:.3f}</b>"
                 + (" (integer: locked divide-by-N picking)" if abs(N - round(N)) < 1e-3 else
                    " <span style='color:#d98200'>(not an integer: selected pulse walks vs the gate - lock period to the laser)</span>"))
        if d.oneshot:
            m[-1] = f"One-shot trigger: a single gate per event; laser period {s_fmt_ns(r['TL'])}."
        sg = r["sug"]
        if sg:
            if d.setup.link_params(ch):
                s_ = d.setup
                if s_.mode() == 1:
                    what = (f"DEL{ch} = <b>{s_fmt_ns(sg['rise']-s_.cab1)}</b>, OUT{ch} width = <b>{s_fmt_ns(max(100.0, sg['width']-d.sync_gap(ch)))}</b> "
                            "(1-input: width = HV pulse)")
                else:
                    wd = max(100.0, sg["width"])
                    what = (f"DEL{s_.a()} = <b>{s_fmt_ns(sg['rise']-s_.cab1)}</b>, DEL{s_.b()} = <b>{s_fmt_ns(sg['rise']+wd-s_.cab2)}</b> "
                            "(X1 opens, X2 closes)")
            else:
                what = f"DEL{ch} = <b>{s_fmt_ns(sg['rise'])}</b>, post-DEL{ch} width = <b>{s_fmt_ns(max(MIN_WIDTH_NS, sg['width']-d.sync_gap(ch)))}</b>"
            line = (f"<b style='color:#0b4778'>SUGGESTION</b> to centre the pulse at {s_fmt_ns(sg['t'])}: {what} "
                    f"(margins {s_fmt_ns(sg['mo'])} / {s_fmt_ns(sg['mc'])}, snapped to hardware steps).")
            if d.setup.link_params(ch) and sg["width"] < 100.0:
                line += (" <span style='color:#d98200'>The DPB1 needs ≥100 ns between open and close, so the gate cannot be as short as "
                         f"the optimum {s_fmt_ns(sg['width'])}: neighbouring laser pulses may also pass.</span>")
            if sg["neg"]:
                line += " <span style='color:#d83b3b'>Needs negative delay: laser arrives before the trigger can act - add optical/cable delay.</span>"
            if not sg["feasible"]:
                line += " <span style='color:#d83b3b'>Gate edges + HV rise cannot isolate one pulse at this laser rep rate.</span>"
            m.append(line)
        m.append(d.clock_note(ch))
        m.append("<span style='color:#5a7085'>Planning model only. Confirm Vπ, delays and rise times against the driver / cell datasheet.</span>")
        self.t_res.setText("<br>".join(m))


# ------------------------------------------------------------
# Signal chain from the manuals:  TG10 -> DPB1 Pockels-cell driver (+ HVS-100 supply) -> Pockels cell
# ------------------------------------------------------------
DPB_MODELS = {   # f_max kHz, V_out max kV, supply rail max ±kV, rise ns, fall ns (6 pF), P_max W, 24 V current mA
    "DPB1-250-5.2-Al": (250, 5.2, 2.6, 8.5, 8.5, 100.0, 120),
    "DPB1-300-4.6-Al": (300, 4.6, 2.3, 8.0, 8.0, 100.0, 140),
    "DPB1-350-4.0-Al": (350, 4.0, 2.0, 7.5, 7.5, 100.0, 150),
    "DPB1-1000-3.0-Al": (1000, 3.0, 1.5, 7.5, 7.5, 120.0, 300),
}
HVS_MODELS = {   # selectable maximum voltages (kV), power per unit/rail (W), power left at 24 V output (W)
    "HVS100-2X60 (bipolar, ±HV)": dict(bip=True, opts=[1.4, 2.5], p=60.0, p24=55.0),
    "HVS100-120 (unipolar)": dict(bip=False, opts=[1.8, 2.6, 3.1, 3.6], p=120.0, p24=55.0),
    "HVS100-5 (unipolar)": dict(bip=False, opts=[1.8, 2.8, 4.0, 4.4, 5.0], p=5.0, p24=190.0),
    "HVS100-40 (unipolar)": dict(bip=False, opts=[1.3, 1.8, 2.5, 3.6, 4.0], p=40.0, p24=150.0),
    "HVS100-80 (unipolar)": dict(bip=False, opts=[1.8, 2.6, 3.1, 3.6, 4.0, 4.4], p=80.0, p24=100.0),
    "HVS100-150 (unipolar, 24 V DC in)": dict(bip=False, opts=[1.8, 2.6, 3.1, 3.6, 4.0, 4.4], p=150.0, p24=None),
}
CABLE_NS_PER_M = 5.0      # coax propagation delay (assumed, typical RG-58)
DPB_DELAY_NS = 30.0       # "HV pulse delay, typical" from the DPB1 manual
SEV_COL = {"ok": "#119447", "warn": "#d98200", "err": "#d83b3b", "info": "#5a7085"}
SEV_ICON = {"ok": "✔", "warn": "⚠", "err": "✖", "info": "ℹ"}


class SetupDiagram(QWidget):
    def __init__(self, panel):
        super().__init__()
        self.pn = panel
        self.setMinimumHeight(330)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, QColor(244, 248, 251))
        S = self.pn
        colr = {k: QColor(v) for k, v in SEV_COL.items()}
        bold, small = QFont("Segoe UI", 9, QFont.Bold), QFont("Segoe UI", 8)

        def box(x, y, w, h, title, lines, sev):
            p.setPen(QPen(colr[sev], 2.5))
            p.setBrush(QColor(255, 255, 255))
            p.drawRoundedRect(QRectF(x, y, w, h), 8, 8)
            p.setFont(bold)
            p.setPen(QColor(11, 71, 120))
            p.drawText(QPointF(x + 8, y + 18), title)
            p.setFont(small)
            p.setPen(QColor(40, 50, 60))
            for i, l in enumerate(lines):
                p.drawText(QPointF(x + 8, y + 36 + i * 14), l)

        def arrow(x1, y1, x2, y2, label, c, dashed=False, lab_dy=-5):
            p.setPen(QPen(c, 2, Qt.DashLine if dashed else Qt.SolidLine))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            ang = _m.atan2(y2 - y1, x2 - x1)
            pts = [QPointF(x2, y2), QPointF(x2 - 9 * _m.cos(ang - 0.4), y2 - 9 * _m.sin(ang - 0.4)),
                   QPointF(x2 - 9 * _m.cos(ang + 0.4), y2 - 9 * _m.sin(ang + 0.4))]
            p.setBrush(c)
            p.drawPolygon(QPolygonF(pts))
            p.setFont(small)
            p.drawText(QPointF(min(x1, x2) + 4, min(y1, y2) + lab_dy), label)

        Dg = S.diag
        bw = W * 0.2
        xT, xD, xC, xL = 10, W * 0.31, W * 0.65, W * 0.86
        box(xT, 16, bw, 175, "TG10 timing generator", Dg["tg"], Dg["sev"]["tg"])
        box(xD, 16, W * 0.25, 175, Dg["dpb_title"], Dg["dpb"], Dg["sev"]["dpb"])
        box(xC, 16, W * 0.15, 175, "Pockels cell", Dg["cell"], Dg["sev"]["cell"])
        box(xL, 16, W * 0.12, 175, "Laser", Dg["laser"], "info")
        box(xD, 225, W * 0.25, 100, Dg["hvs_title"], Dg["hvs"], Dg["sev"]["hvs"])
        arrow(xT + bw, 62, xD, 62, Dg["a1"], colr[Dg["sev"]["tg"]])
        arrow(xT + bw, 112, xD, 112, Dg["a2"], colr[Dg["sev"]["tg"]] if S.mode() == 2 else QColor(160, 170, 180), S.mode() != 2)
        xm = xD + W * 0.25
        arrow(xm, 70, xC, 70, "+OUT", colr[Dg["sev"]["dpb"]])
        arrow(xm, 120, xC, 120, "−OUT", colr[Dg["sev"]["dpb"]])
        p.setFont(small)
        p.setPen(QColor(40, 50, 60))
        p.drawText(QPointF(xm + 4, 150), Dg["vcell"])
        arrow(xC + W * 0.15, 95, xL, 95, "beam", QColor(120, 120, 120))
        arrow(xD + W * 0.07, 225, xD + W * 0.07, 191, Dg["a_hv"], colr[Dg["sev"]["hvs"]], lab_dy=18)
        arrow(xD + W * 0.18, 225, xD + W * 0.18, 191, "24 V DC", colr[Dg["sev24"]], lab_dy=18)
        p.end()


class ModeDiagram(QWidget):
    """Manual Fig. 4, live: jumper #7 position 1 (1-input) and position 2 (2-input) side by side."""

    def __init__(self, panel):
        super().__init__()
        self.pn = panel
        self.setMinimumHeight(430)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, QColor(244, 248, 251))
        for m in (1, 2):
            self._panel(p, m, (m - 1) * W / 2 + 6, W / 2 - 12, H)
        p.end()

    def _panel(self, p, mode, x0, pw, H):
        S = self.pn
        d = S.d
        a, b = S.a(), S.b()
        pv = S.mode_preview(mode)
        active = mode == S.mode()
        p.setBrush(QColor(255, 255, 255))
        p.setPen(QPen(QColor("#119447") if active else QColor("#9aa9b8"), 3 if active else 1.5))
        p.drawRoundedRect(QRectF(x0, 4, pw, H - 8), 8, 8)
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(QColor(11, 71, 120))
        p.drawText(QPointF(x0 + 10, 24), f"JUMPER #7 → POSITION {mode}:  {'1-INPUT' if mode == 1 else '2-INPUT'} CONTROL"
                   + ("   (ACTIVE)" if active else "   (preview)"))
        tO, tC = pv["win"]
        D = max(tC - tO, 1.0)
        marg = max(0.35 * D, 50.0)
        t_lo, t_hi = tO - marg, tC + marg + 60
        X = lambda t: x0 + 16 + (t - t_lo) / (t_hi - t_lo) * (pw - 32)
        sf = QFont("Consolas", 8)
        lf = QFont("Segoe UI", 8)

        def pulse(r, f, top, h, col, label):
            path = QPainterPath()
            path.moveTo(X(t_lo), top + h)
            path.lineTo(X(r), top + h)
            path.lineTo(X(r), top)
            path.lineTo(X(f), top)
            path.lineTo(X(f), top + h)
            path.lineTo(X(t_hi), top + h)
            p.setPen(QPen(col, 2.2))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
            p.setFont(sf)
            p.setPen(col)
            p.drawText(QPointF(X(r) - 4, top - 4), s_fmt_ns(r))
            p.drawText(QPointF(X(f) + 3, top + h - 4 if f - r > 0 else top - 4), s_fmt_ns(f))
            p.setFont(lf)
            p.drawText(QPointF(x0 + 12, top - 16), label)

        c1 = QColor(SIM_COLORS[a])
        c2 = QColor(SIM_COLORS[b])
        t1, h1 = 62, 30
        t2, h2 = 118, 30
        pulse(*pv["x1"], t1, h1, c1, f"X1 (SYNC IN1) ← OUT{a}")
        if pv["x2"]:
            pulse(*pv["x2"], t2, h2, c2, f"X2 (SYNC IN2) ← OUT{b}")
        else:
            p.setPen(QPen(QColor(160, 170, 180), 1.5, Qt.DashLine))
            p.drawLine(QPointF(X(t_lo), t2 + h2), QPointF(X(t_hi), t2 + h2))
            p.setFont(lf)
            p.drawText(QPointF(x0 + 12, t2 - 16), "X2 (SYNC IN2)  - not used in this position")
        # HV pulse on the Pockels cell
        tr, tf = S.hv_edge_times()
        on, off = pv["hv"]
        base, amp = 222, 40
        poly = lambda sgn: QPolygonF([QPointF(X(on - tr / 2), base), QPointF(X(on + tr / 2), base - sgn * amp),
                                      QPointF(X(off - tf / 2), base - sgn * amp), QPointF(X(off + tf / 2), base)])
        p.setFont(lf)
        p.setPen(QColor(120, 120, 120))
        p.drawText(QPointF(x0 + 12, 168), "HV pulse on the Pockels cell:  +OUT (red) / −OUT (blue)")
        p.setPen(QPen(QColor(150, 150, 150), 1))
        p.drawLine(QPointF(X(t_lo), base), QPointF(X(t_hi), base))
        p.setBrush(QColor(255, 120, 120, 90))
        p.setPen(QPen(QColor(220, 70, 70), 2))
        p.drawPolygon(poly(1))
        p.setBrush(QColor(90, 140, 255, 90))
        p.setPen(QPen(QColor(60, 100, 220), 2))
        p.drawPolygon(poly(-1))
        # cause -> effect arrows
        def link(xt, y_from, xt2, col, txt):
            p.setPen(QPen(col, 1.4, Qt.DashLine))
            p.drawLine(QPointF(X(xt), y_from), QPointF(X(xt2), base - amp))
            p.setFont(sf)
            p.drawText(QPointF(X(xt2) + 4, base - amp - 4), txt)
        link(tO, t1 + h1, on, QColor(17, 148, 71), "HV ON")
        if mode == 1:
            link(tC, t1, off, QColor(216, 59, 59), "HV OFF")
        else:
            link(tC, t2 + h2, off, QColor(216, 59, 59), "HV OFF")
        # duration bracket
        yb = base + amp + 22
        p.setPen(QPen(QColor(11, 71, 120), 1.5))
        p.drawLine(QPointF(X(on), yb), QPointF(X(off), yb))
        p.drawLine(QPointF(X(on), yb - 5), QPointF(X(on), yb + 5))
        p.drawLine(QPointF(X(off), yb - 5), QPointF(X(off), yb + 5))
        p.setFont(lf)
        p.drawText(QPointF(max(X(on), x0 + 10) + 4, yb + 15), f"HV duration = {s_fmt_ns(D)}  (X-edge → HV edge ≈ {s_fmt_ns(DPB_DELAY_NS)})")
        # programming rules
        if mode == 1:
            txt = (f"1-input: X1 rising edge turns the HV ON, X1 falling edge turns it OFF.\n"
                   f"TG10: OUT{a} DEL = HV-on time; OUT{a} post-delay width = HV duration (100…5000 ns). Only one TG10 output is used.")
        else:
            txt = (f"2-input: X1 rising edge turns the HV ON, X2 rising edge turns it OFF.\n"
                   f"TG10: OUT{a} DEL = HV-on time; OUT{b} DEL = HV-off time (spacing 100…5000 ns); each trigger pulse > 20 ns; "
                   f"X1/X2 cables must be equal length. Allows pulse regeneration beyond 5 µs.")
        p.setPen(QColor(40, 50, 60))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(x0 + 10, yb + 24, pw - 20, H - yb - 30), Qt.TextWordWrap | Qt.AlignTop, txt)


class SetupPanel(QWidget):
    """Links TG10 outputs -> DPB1 driver inputs -> Pockels cell, with HVS-100 limits. Drives the planner."""

    def __init__(self, dlg):
        super().__init__()
        self.d = dlg
        self.checks = []
        self.diag = dict(tg=[], dpb=[], hvs=[], cell=[], laser=[], sev=dict(tg="info", dpb="info", hvs="info", cell="info"),
                         dpb_title="", hvs_title="", a1="", a2="", a_hv="", vcell="", sev24="info")
        root = QHBoxLayout(self)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFixedWidth(580)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        holder = QWidget()
        left = QVBoxLayout(holder)
        sc.setWidget(holder)
        root.addWidget(sc)
        right = QVBoxLayout()
        root.addLayout(right, 1)

        def spin(lo, hi, val, dec, suf):
            s = QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setDecimals(dec)
            s.setValue(val)
            s.setSuffix(suf)
            s.valueChanged.connect(self._changed)
            return s

        def group(title, rows):
            g = QGroupBox(title)
            l = QGridLayout(g)
            for i, (n, w) in enumerate(rows):
                l.addWidget(QLabel(n), i, 0)
                l.addWidget(w, i, 1)
            left.addWidget(g)

        self.ck_link = QCheckBox("Link this setup to the Pockels planner (cell is driven by the X1 output)")
        self.ck_link.setChecked(True)
        self.ck_link.toggled.connect(self._changed)
        left.addWidget(self.ck_link)

        self.cb_dpb = QComboBox()
        self.cb_dpb.addItems(DPB_MODELS.keys())
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["1-input  (jumper #7 position 1)", "2-input  (jumper #7 position 2)"])
        self.cb_a = QComboBox()
        self.cb_b = QComboBox()
        for c in (self.cb_a, self.cb_b):
            c.addItems([f"OUT{i}" for i in range(8)])
        self.cb_b.setCurrentIndex(1)
        self.c1 = spin(0, 100, 1.5, 2, " m")
        self.c2 = spin(0, 100, 1.5, 2, " m")
        for c in (self.cb_dpb, self.cb_a, self.cb_b):
            c.currentIndexChanged.connect(self._changed)
        self.cb_mode.currentIndexChanged.connect(self._mode_changed)
        group("DPB1 driver && trigger wiring", [("Driver model", self.cb_dpb), ("Control mode", self.cb_mode),
                                                ("X1 (SYNC IN1) driven by", self.cb_a), ("X2 (SYNC IN2) driven by", self.cb_b),
                                                ("X1 cable length", self.c1), ("X2 cable length", self.c2)])

        self.cb_hvs = QComboBox()
        self.cb_hvs.addItems(HVS_MODELS.keys())
        self.cb_hvs.currentIndexChanged.connect(self._hvs_changed)
        self.cb_umax = QComboBox()
        self.cb_umax.currentIndexChanged.connect(self._changed)
        self.rail = spin(0.05, 6, 1.0, 3, " kV")
        b_auto = QPushButton("Set rails for full-open of the cell")
        b_auto.clicked.connect(self._auto_rail)
        group("HVS-100 high-voltage supply", [("Supply model", self.cb_hvs), ("Selected max voltage (Umax)", self.cb_umax),
                                              ("Rail setpoint (each of +HV / −HV)", self.rail)])
        left.addWidget(b_auto)

        self.cb_cell = QComboBox()
        self.cb_cell.addItems(CELL_PRESETS.keys())
        self.cb_cell.setCurrentText("RTP (typ.)")
        self.cb_cell.activated.connect(self._cell_preset)
        self.cb_pmode = QComboBox()
        self.cb_pmode.addItems(CELL_MODES.keys())
        self.cb_pmode.currentIndexChanged.connect(self._changed)
        self.vpi = spin(0.05, 50, 1.8, 3, " kV")
        self.cap = spin(0.5, 50, 6.0, 2, " pF")
        group("Pockels cell on the driver output", [("Cell type", self.cb_cell), ("Optical mode", self.cb_pmode),
                                                    ("Half-wave voltage Vπ", self.vpi), ("Cell capacitance (with wiring)", self.cap)])
        left.addStretch(1)

        self.inner = QTabWidget()
        right.addWidget(self.inner, 1)
        chain = QWidget()
        cl = QVBoxLayout(chain)
        self.diagram = SetupDiagram(self)
        cl.addWidget(self.diagram)
        self.txt = QLabel()
        self.txt.setTextFormat(Qt.RichText)
        self.txt.setWordWrap(True)
        self.txt.setStyleSheet("background:#f4f8fb; border:1px solid #c5d4e2; border-radius:4px; padding:6px;")
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        self.txt.setAlignment(Qt.AlignTop)
        sa.setWidget(self.txt)
        cl.addWidget(sa, 1)
        self.inner.addTab(chain, "Signal chain && limit checks")
        jm = QWidget()
        jl = QVBoxLayout(jm)
        tp = QHBoxLayout()
        self.ck_keep = QCheckBox("Keep the gate window when the jumper position is switched (re-programs OUT a / OUT b)")
        self.ck_keep.setChecked(True)
        b_prog = QPushButton("Re-program TG10 outputs for this jumper position")
        b_prog.clicked.connect(self._program_current)
        tp.addWidget(self.ck_keep, 1)
        tp.addWidget(b_prog)
        jl.addLayout(tp)
        self.mdiag = ModeDiagram(self)
        jl.addWidget(self.mdiag, 3)
        self.mtxt = QLabel()
        self.mtxt.setTextFormat(Qt.RichText)
        self.mtxt.setWordWrap(True)
        self.mtxt.setAlignment(Qt.AlignTop)
        self.mtxt.setStyleSheet("background:#ffffff; border:1px solid #c5d4e2; border-radius:4px; padding:6px;")
        sb = QScrollArea()
        sb.setWidgetResizable(True)
        sb.setWidget(self.mtxt)
        jl.addWidget(sb, 2)
        self.inner.addTab(jm, "X1 / X2 jumper modes (pulse timing)")
        sw = QWidget()
        sl = QVBoxLayout(sw)
        bl = QHBoxLayout()
        b_push = QPushButton("Send values to Delay presets")
        b_push.clicked.connect(self.d.push_to_main)
        b_open = QPushButton("Open Delay presets (apply to hardware)")
        b_open.clicked.connect(lambda: self.d.pw.open_delay())
        self.ck_guard = QCheckBox("Ask before programming the TG10 when a driver limit is violated")
        self.ck_guard.setChecked(True)
        self.ck_always = QCheckBox("Always show this review before programming")
        for wdg in (b_push, b_open):
            bl.addWidget(wdg)
        bl.addStretch(1)
        sl.addLayout(bl)
        sl.addWidget(self.ck_guard)
        sl.addWidget(self.ck_always)
        self.stxt = QLabel()
        self.stxt.setTextFormat(Qt.RichText)
        self.stxt.setWordWrap(True)
        self.stxt.setAlignment(Qt.AlignTop)
        self.stxt.setStyleSheet("background:#ffffff; border:1px solid #c5d4e2; border-radius:4px; padding:8px;")
        ss = QScrollArea()
        ss.setWidgetResizable(True)
        ss.setWidget(self.stxt)
        sl.addWidget(ss, 1)
        self.inner.insertTab(1, sw, "What you are sending && its effect")
        self.inner.currentChanged.connect(lambda *_: self._update_send())
        self._mode_prev = 1
        self._hvs_changed()

    # ---- accessors ----
    def mode(self):
        return 1 + self.cb_mode.currentIndex()

    def a(self):
        return self.cb_a.currentIndex()

    def b(self):
        return self.cb_b.currentIndex()

    @property
    def cab1(self):
        return self.c1.value() * CABLE_NS_PER_M

    @property
    def cab2(self):
        return self.c2.value() * CABLE_NS_PER_M

    def _hvs_changed(self, *_):
        h = HVS_MODELS[self.cb_hvs.currentText()]
        self.cb_umax.blockSignals(True)
        self.cb_umax.clear()
        self.cb_umax.addItems([f"{u:.1f} kV" for u in h["opts"]])
        self.cb_umax.setCurrentIndex(len(h["opts"]) - 1)
        self.cb_umax.blockSignals(False)
        self._changed()

    def umax(self):
        return float(self.cb_umax.currentText().split()[0])

    def _cell_preset(self, *_):
        self.vpi.setValue(CELL_PRESETS[self.cb_cell.currentText()])

    def _auto_rail(self):
        k, _inv = CELL_MODES[self.cb_pmode.currentText()]
        need = self.vpi.value() / k / 2.0                      # cell voltage = +rail - (-rail) = 2 x rail
        self.rail.setValue(max(need, 0.4 * self.umax()))

    def _changed(self, *_):
        self.d.refresh()

    # ---- jumper #7 handling ----
    def hv_edge_times(self):
        fmax, vout, rmax, tr0, tf0, pmax, idc = DPB_MODELS[self.cb_dpb.currentText()]
        sc = max(1.0, self.cap.value() / 6.0)
        return tr0 * sc, tf0 * sc

    def window_for(self, mode):
        """Gate window [HV-on, HV-off] seen at the driver inputs, for the given jumper position."""
        d = self.d
        a, b = self.a(), self.b()
        rA, fA = d.edges(a)
        rB, _f = d.edges(b)
        if mode == 1:
            return rA + self.cab1, fA + self.cab1
        return rA + self.cab1, rB + self.cab2

    def mode_preview(self, mode):
        d = self.d
        a, b = self.a(), self.b()
        tO, tC = self.window_for(self.mode())
        if mode == self.mode():
            rA, fA = d.edges(a)
            rB, fB = d.edges(b)
            x1 = (rA + self.cab1, fA + self.cab1)
            x2 = (rB + self.cab2, fB + self.cab2) if mode == 2 else None
        elif mode == 1:
            x1, x2 = (tO, tC), None
        else:
            x1, x2 = (tO, tO + 50.0), (tC, tC + 50.0)
        return dict(x1=x1, x2=x2, hv=(tO + DPB_DELAY_NS, tC + DPB_DELAY_NS), win=(tO, tC))

    def program(self, mode, win):
        """Program the TG10 delay/width rows so the HV gate window `win` is produced in the given jumper position."""
        d = self.d
        a, b = self.a(), self.b()
        tO, tC = win
        D = max(tC - tO, 0.0)
        d._busy = True
        try:
            d.rows[a]["del"].setValue(max(0.025, tO - self.cab1))
            if mode == 1:
                d.rows[a]["pw"].setValue(max(MIN_WIDTH_NS, max(100.0, D) - d.sync_gap(a)))
            elif a != b:
                d.rows[b]["del"].setValue(max(0.025, tO + max(D, 100.0) - self.cab2))
                for c in (a, b):
                    if d.rows[c]["pw"].value() < 20:
                        d.rows[c]["pw"].setValue(50.0)
        finally:
            d._busy = False
        d.refresh()

    def _update_send(self):
        if self.inner.currentIndex() == 1 and hasattr(self, "stxt"):
            self.stxt.setText(self.review_html())

    def _program_current(self):
        self.program(self.mode(), self.window_for(self.mode()))

    def _mode_changed(self, *_):
        new = self.mode()
        old = getattr(self, "_mode_prev", new)
        if old != new and self.ck_keep.isChecked() and getattr(self.d, "_ready", False):
            self.program(new, self.window_for(old))
        self._mode_prev = new
        self._changed()

    def mode_table_html(self):
        d = self.d
        a, b = self.a(), self.b()
        gap = d.sync_gap(a)
        ra, fa = d.edges(a)
        rb, fb = d.edges(b)
        act = self.mode()
        step2 = max(d.delay_step(a), d.delay_step(b))
        rows = [
            ("TG10 outputs used", f"OUT{a} only", f"OUT{a} (→X1) and OUT{b} (→X2)"),
            ("HV turns ON", f"X1 rising edge = DEL{a} ({s_fmt_ns(ra)})", f"X1 rising edge = DEL{a} ({s_fmt_ns(ra)})"),
            ("HV turns OFF", f"X1 <b>falling</b> edge = DEL{a} + post-delay width ({s_fmt_ns(fa)})",
             f"X2 <b>rising</b> edge = DEL{b} ({s_fmt_ns(rb)})"),
            ("HV duration set by", f"post-delay width of OUT{a}, step {s_fmt_ns(d.width_res(a))}",
             f"DEL{b} − DEL{a}, step {s_fmt_ns(step2)}"),
            ("Allowed duration", "100…5000 ns", "100…5000 ns; longer with pulse regeneration (repeat X1 about every 5 µs, "
                                                  "X2 &gt;100 ns after the last X1)"),
            ("Trigger pulse width", "= HV duration (≥100 ns)", "each &gt;20 ns, any value (only rising edges matter)"),
            ("External-clock fall-path gap", (f"HV is longer by <b>{s_fmt_ns(gap)}</b> than programmed (compensated by the planner)"
                                               if gap else "none with the internal clock"),
             "none: both HV edges come from rising edges"),
            ("Cables", "one SMB cable", "X1 and X2 cables of equal length (skew adds to the duration)"),
            ("Best for", "short gates / pulse picking up to 5 µs, saves a TG10 output",
             "long or finely tunable gates, avoids the fall-path error"),
        ]
        h = ("<table cellspacing='0' cellpadding='4' style='border-collapse:collapse'>"
             "<tr style='background:#eaf1f7'><th align='left'>&nbsp;</th>"
             f"<th align='left'>Position 1 · 1-input{' ✔ ACTIVE' if act == 1 else ''}</th>"
             f"<th align='left'>Position 2 · 2-input{' ✔ ACTIVE' if act == 2 else ''}</th></tr>")
        for n, c1, c2 in rows:
            h += (f"<tr><td style='border-top:1px solid #d5e0ea'><b>{n}</b></td>"
                  f"<td style='border-top:1px solid #d5e0ea;{'background:#effaf3' if act == 1 else ''}'>{c1}</td>"
                  f"<td style='border-top:1px solid #d5e0ea;{'background:#effaf3' if act == 2 else ''}'>{c2}</td></tr>")
        return h + "</table>"

    # ---- "what are you sending and what does it do" ----
    def impact(self, mode):
        """Consequence of the CURRENT TG10 programming if jumper #7 is in position `mode`."""
        d = self.d
        a, b = self.a(), self.b()
        rA, fA = d.edges(a)
        rB, fB = d.edges(b)
        issues = []
        if mode == 1:
            tO, tC = rA + self.cab1, fA + self.cab1
            D = tC - tO
            if D < 100:
                issues.append(("err", f"HV pulse {s_fmt_ns(D)} is below 100 ns - the driver may be damaged"))
            elif D > 5000:
                issues.append(("warn", f"HV pulse {s_fmt_ns(D)} exceeds 5000 ns - flat-top decays; use 2-input mode with regeneration"))
        else:
            tO, tC = rA + self.cab1, rB + self.cab2
            D = tC - tO
            if a == b:
                issues.append(("err", "X1 and X2 are fed by the same output - HV on and off edges coincide"))
            if D <= 0:
                issues.append(("err", f"X2 rising edge ({s_fmt_ns(tC)}) is not after X1 ({s_fmt_ns(tO)}): the HV is never switched off "
                                      "properly in this position (undefined - may stay ON)"))
            elif D < 100:
                issues.append(("err", f"X1→X2 spacing {s_fmt_ns(D)} is below 100 ns - the driver may be damaged"))
            elif D > 5000:
                issues.append(("warn", f"X1→X2 spacing {s_fmt_ns(D)} exceeds 5000 ns - use pulse regeneration"))
            for ch_, nm in ((a, "X1"), (b, "X2")):
                w = d.edges(ch_)[1] - d.edges(ch_)[0]
                if w < 20:
                    issues.append(("err", f"{nm} trigger pulse (OUT{ch_}) is {s_fmt_ns(w)}, needs > 20 ns"))
        out = dict(mode=mode, win=(tO, tC), D=D, issues=issues, res=None, verdict=None)
        if D > 0:
            res = pockels_analyze(d.period, tO, tC, d.planner.full_params(a), d.delay_step(a), d.width_res(a))
            out["res"], out["verdict"] = res, pockels_verdict(res)
        return out

    def _issue_html(self, issues):
        if not issues:
            return "<span style='color:#119447'>✔ within driver limits</span>"
        return "<br>".join(f"<span style='color:{SEV_COL[s]}'>{SEV_ICON[s]} {t}</span>" for s, t in issues)

    def review_html(self):
        d = self.d
        a, b = self.a(), self.b()
        act = self.mode()
        rA, fA = d.edges(a)
        rB, fB = d.edges(b)
        im = {1: self.impact(1), 2: self.impact(2)}
        cur = im[act]
        tO, tC = cur["win"]
        hvP = self.link_params(a) or d.planner.full_params(a)
        T = s_fmt_ns
        h = ["<div style='color:#2a3b4c'>"]
        # 1 --- what the TG10 sends
        h.append(f"<b style='color:#0b4778'>1 · WHAT THE TG10 SENDS (jumper #7 in position {act}, {act}-input mode)</b>")
        h.append("<table cellspacing='0' cellpadding='4' style='border-collapse:collapse'>"
                 "<tr style='background:#eaf1f7'><th align='left'>TG10 output → driver input</th><th align='left'>DEL programmed → realized</th>"
                 "<th align='left'>Width programmed → realized</th><th align='left'>Rising edge at driver</th>"
                 "<th align='left'>Falling edge at driver</th><th align='left'>What the driver does with it</th></tr>")

        def row(ch, tag, cab, rising_role, falling_role):
            r_, f_ = d.edges(ch)
            gap = d.sync_gap(ch)
            return (f"<tr><td style='border-top:1px solid #d5e0ea'><b>OUT{ch} → {tag}</b></td>"
                    f"<td style='border-top:1px solid #d5e0ea'>{T(d.rows[ch]['del'].value())} → {T(r_)}</td>"
                    f"<td style='border-top:1px solid #d5e0ea'>{T(d.rows[ch]['pw'].value())} → {T(f_-r_)}"
                    + (f" (incl. {T(gap)} sync gap)" if gap else "") + "</td>"
                    f"<td style='border-top:1px solid #d5e0ea'>{T(r_+cab)}<br><i>{rising_role}</i></td>"
                    f"<td style='border-top:1px solid #d5e0ea'>{T(f_+cab)}<br><i>{falling_role}</i></td>"
                    f"<td style='border-top:1px solid #d5e0ea'></td></tr>")

        if act == 1:
            h.append(row(a, "X1 (SYNC IN1)", self.cab1, "HV turns ON", "HV turns OFF"))
        else:
            h.append(row(a, "X1 (SYNC IN1)", self.cab1, "HV turns ON", "ignored"))
            h.append(row(b, "X2 (SYNC IN2)", self.cab2, "HV turns OFF", "ignored"))
        h.append("</table>")
        h.append(f"{'Single shot (one-shot trigger).' if d.oneshot else 'Repeated every ' + T(d.period) + ' (' + s_fmt_freq(1e9/d.period) + ').'} Pulse amplitude / edge speed come from the TG10 output stage "
                 "(not modelled here): the driver needs 3.5…5 V into 50 Ω with rise/fall ≤ 10 ns - check on a scope with a 50 Ω load first.")
        # 2 --- driver / HV
        tr, tf = self.hv_edge_times()
        vc = hvP["v"]
        h.append("<br><b style='color:#0b4778'>2 · WHAT THE DRIVER DOES (HV on the Pockels cell)</b>")
        h.append(f"HV ON at {T(tO + DPB_DELAY_NS)} (trigger {T(tO)} + ≈{T(DPB_DELAY_NS)} driver delay), full level after +{T(tr)} · "
                 f"HV OFF at {T(tC + DPB_DELAY_NS)}, down after +{T(tf)}.<br>"
                 f"HV duration = <b>{T(cur['D'])}</b> · cell voltage = 2 × rail ({self.rail.value():.2f} kV) = <b>{vc:.2f} kV</b> "
                 f"(full open needs {self.vpi.value()/hvP['k']:.2f} kV) · droop over the gate "
                 f"{(1-_m.exp(-max(cur['D'],0)/(33000.0*self.cap.value())))*100:.2f} %.<br>" + self._issue_html(cur["issues"]))
        # 3 --- light
        h.append("<br><b style='color:#0b4778'>3 · WHAT IT DOES TO THE LIGHT</b>")
        r = cur["res"]
        if r:
            vt, vc_ = cur["verdict"]
            seen = [p for p in r["pulses"] if p[1] > 0.05]
            lst = ", ".join(f"{s_fmt_ns(p[0])}: <b>{p[1]*100:.0f} %</b>" for p in seen[:6]) or "none"
            gw = (r["t_close"] - r["t_open"]) if (r["t_open"] is not None and r["t_close"] is not None) else None
            h.append(f"Optical gate opens (50 %) at <b>{T(r['t_open']) if r['t_open'] is not None else 'never'}</b>, closes at "
                     f"<b>{T(r['t_close']) if r['t_close'] is not None else 'never'}</b> (window {T(gw) if gw is not None else '—'}).<br>"
                     f"Laser pulses transmitted: {lst}.<br><b style='color:{vc_}'>Result: {vt}</b>")
        else:
            h.append("<span style='color:#d83b3b'>No valid gate (HV duration ≤ 0): no light is switched.</span>")
        # 4 --- mismatch matrix
        h.append("<br><b style='color:#0b4778'>4 · THE SAME TG10 VALUES IN EACH JUMPER POSITION</b> "
                 "(the jumper is set by hand on the driver - the GUI cannot see it)")
        h.append("<table cellspacing='0' cellpadding='4' style='border-collapse:collapse'>"
                 "<tr style='background:#eaf1f7'><th align='left'></th>"
                 f"<th align='left'>Position 1 · 1-input{' ✔ selected' if act == 1 else ''}</th>"
                 f"<th align='left'>Position 2 · 2-input{' ✔ selected' if act == 2 else ''}</th></tr>")
        cell = lambda m, f: f(im[m])
        rws = [
            ("HV ON at", lambda i: f"X1 rising: {T(i['win'][0])}"),
            ("HV OFF at", None),
            ("HV duration", lambda i: T(i["D"])),
            ("Driver limits", lambda i: self._issue_html(i["issues"])),
            ("Light", lambda i: (f"<span style='color:{i['verdict'][1]}'>{i['verdict'][0]}</span>" if i["verdict"] else "no valid gate")),
        ]
        for n, fn in rws:
            if n == "HV OFF at":
                c1 = f"X1 falling: {T(im[1]['win'][1])}"
                c2 = f"X2 rising: {T(im[2]['win'][1])}"
            else:
                c1, c2 = fn(im[1]), fn(im[2])
            bg = lambda m: "background:#effaf3;" if act == m else ""
            h.append(f"<tr><td style='border-top:1px solid #d5e0ea'><b>{n}</b></td>"
                     f"<td style='border-top:1px solid #d5e0ea;{bg(1)}'>{c1}</td>"
                     f"<td style='border-top:1px solid #d5e0ea;{bg(2)}'>{c2}</td></tr>")
        h.append("</table>")
        other = 3 - act
        if im[other]["issues"] and any(s == "err" for s, _t in im[other]["issues"]):
            h.append(f"<span style='color:#d83b3b'>⚠ If the jumper on the driver is actually in position {other}, these values are NOT safe.</span>")
        # 5 --- not sent
        h.append("<br><b style='color:#0b4778'>5 · NOT SENT BY THIS GUI - set by hand</b><br>"
                 f"Jumper #7 → position {act}. HVS-100: ±{self.rail.value():.2f} kV per rail ({self.cb_hvs.currentText()}, Umax {self.umax():.1f} kV). "
                 "24 V DC for the driver. Switch the TG10 outputs on only after HV and 24 V are up; switch them off before power-down.")
        h.append("</div>")
        return "<br>".join(h)

    def confirm_send(self, parent):
        """Called before the Delay dialog programs the hardware. Stops (with a choice) on driver-limit violations."""
        if not (self.ck_link.isChecked() and self.ck_guard.isChecked()):
            return True
        act = self.mode()
        cur = self.impact(act)
        ck = self.evaluate()
        errs = [t for s_, _a, t in ck if s_ == "err"]
        warns = [t for s_, _a, t in ck if s_ == "warn"]
        if not errs and not self.ck_always.isChecked():
            return True
        tO, tC = cur["win"]
        txt = (f"<b>You are about to program the TG10 for the DPB1 driver, jumper #7 in position {act} ({act}-input).</b><br><br>"
               f"X1 rising edge (HV ON) at {s_fmt_ns(tO)}; "
               + ("X1 falling edge (HV OFF)" if act == 1 else "X2 rising edge (HV OFF)") + f" at {s_fmt_ns(tC)}.<br>"
               f"HV duration {s_fmt_ns(cur['D'])} · repetition {self.d.rate_txt()} · cell voltage {self.link_params(self.a())['v']:.2f} kV.<br>"
               + (f"Light: <b>{cur['verdict'][0]}</b>.<br>" if cur["verdict"] else ""))
        if errs:
            txt += "<br><span style='color:#d83b3b'><b>Driver / supply limits violated:</b><br>" + "<br>".join("✖ " + e for e in errs[:8]) + "</span>"
        if warns:
            txt += "<br><span style='color:#d98200'>" + "<br>".join("⚠ " + w for w in warns[:6]) + "</span>"
        txt += ("<br><br>Make sure jumper #7 really is in position " f"{act} and that SYNC pulses are enabled only after the HV and 24 V are on.")
        box = QMessageBox(parent)
        box.setTextFormat(Qt.RichText)
        box.setWindowTitle("Review before sending to the TG10")
        box.setIcon(QMessageBox.Warning if errs else QMessageBox.Information)
        box.setText(txt)
        send = box.addButton("Send anyway" if errs else "Send", QMessageBox.AcceptRole)
        cancel = box.addButton("Cancel", QMessageBox.RejectRole)
        box.setDefaultButton(cancel if errs else send)
        box.exec()
        return box.clickedButton() is send

    # ---- what the planner uses ----
    def link_params(self, ch):
        if not (self.ck_link.isChecked() and ch == self.a()):
            return None
        fmax, vout, rmax, tr0, tf0, pmax, idc = DPB_MODELS[self.cb_dpb.currentText()]
        C = self.cap.value()
        sc = max(1.0, C / 6.0)                                   # spec is for 6 pF; scaled up above that (assumed linear)
        k, inv = CELL_MODES[self.cb_pmode.currentText()]
        return dict(drv=DPB_DELAY_NS, tr=tr0 * sc, tf=tf0 * sc, v=min(2 * self.rail.value(), vout),
                    tdec=33000.0 * C, vpi=self.vpi.value(), k=k, inv=inv, cell=self.cb_cell.currentText(),
                    mode=self.cb_pmode.currentIndex(), en=True)

    def describe(self, ch, r, P):
        d = self.d
        a, b = self.a(), self.b()
        rA, fA = d.edges(a)
        rB, fB = d.edges(b)
        to, tc = r["t_open"], r["t_close"]
        T = lambda v: s_fmt_ns(v) if v is not None else "never"
        h = (f"<b>OUT{a} → X1 (SYNC IN1)</b>: DEL{a} {s_fmt_ns(d.rows[a]['del'].value())} → realized rise {s_fmt_ns(rA)} "
             f"(+{s_fmt_ns(self.cab1)} cable) → X1 rising edge turns HV ON after ≈{s_fmt_ns(DPB_DELAY_NS)} (driver delay) + "
             f"{s_fmt_ns(P['tr'])} rise → optical gate OPENS (T=50 %) at <b>{T(to)}</b>.<br>")
        if self.mode() == 1:
            h += (f"1-input mode: the X1 <b>falling</b> edge turns HV OFF. OUT{a} width {s_fmt_ns(fA-rA)} = HV pulse duration → "
                  f"HV off {s_fmt_ns(r['ec'])} → gate CLOSES at <b>{T(tc)}</b>.<br>")
        else:
            h += (f"<b>OUT{b} → X2 (SYNC IN2)</b>: DEL{b} {s_fmt_ns(d.rows[b]['del'].value())} → realized {s_fmt_ns(rB)} "
                  f"(+{s_fmt_ns(self.cab2)} cable) → X2 <b>rising</b> edge turns HV OFF → gate CLOSES at <b>{T(tc)}</b>. "
                  f"X1→X2 spacing = {s_fmt_ns((rB + self.cab2) - (rA + self.cab1))} (driver limit 100–5000 ns).<br>")
        tdec = P.get("tdec")
        if tdec:
            h += (f"HV flat-top droop (τ = 33 MΩ·{self.cap.value():.1f} pF = {s_fmt_ns(tdec)}): "
                  f"{(1-_m.exp(-(r['ec']-r['eo'])/tdec))*100:.2f} % over this gate.<br>")
        return h

    # ---- limits / compatibility ----
    def evaluate(self):
        d = self.d
        ck = []
        add = lambda sev, area, text: ck.append((sev, area, text))
        name = self.cb_dpb.currentText()
        fmax, vout, rmax, tr0, tf0, pmax, idc = DPB_MODELS[name]
        hv = HVS_MODELS[self.cb_hvs.currentText()]
        mode, a, b = self.mode(), self.a(), self.b()
        P = d.period
        f = 1e9 / P if not d.oneshot else 0.0
        rA, fA = d.edges(a)
        rB, fB = d.edges(b)
        C = self.cap.value()
        # --- trigger side ---
        if f / 1e3 > fmax:
            add("err", "dpb", f"Repetition rate {s_fmt_freq(f)} exceeds the {name} limit of {fmax} kHz.")
        else:
            add("ok", "dpb", f"Repetition rate {s_fmt_freq(f)} ≤ {fmax} kHz limit.")
        if mode == 1:
            w = fA - rA
            if w < 100:
                add("err", "tg", f"1-input mode: OUT{a} pulse width {s_fmt_ns(w)} is below 100 ns - may DAMAGE the driver.")
            elif w > 5000:
                add("warn", "tg", f"HV pulse {s_fmt_ns(w)} > 5000 ns limit in 1-input mode. Use 2-input mode with pulse regeneration.")
            else:
                add("ok", "tg", f"HV pulse duration {s_fmt_ns(w)} within 100…5000 ns.")
        else:
            if a == b:
                add("err", "tg", "2-input mode needs two different TG10 outputs for X1 and X2.")
            dl = (rB + self.cab2) - (rA + self.cab1)
            if dl < 100:
                add("err", "tg", f"X1→X2 spacing {s_fmt_ns(dl)} is below 100 ns - may DAMAGE the driver.")
            elif dl > 5000:
                add("warn", "tg", f"X1→X2 spacing {s_fmt_ns(dl)} > 5000 ns: use pulse regeneration (repeat X1 pulses every ≈5 µs, "
                                  "then X2 >100 ns after the last one).")
            else:
                add("ok", "tg", f"X1→X2 spacing {s_fmt_ns(dl)} within 100…5000 ns.")
            for ch_, nm in ((a, "X1"), (b, "X2")):
                w = d.edges(ch_)[1] - d.edges(ch_)[0]
                if w < 20:
                    add("err", "tg", f"{nm} trigger pulse (OUT{ch_}) is {s_fmt_ns(w)}; the driver needs > 20 ns.")
            skew = abs(self.cab2 - self.cab1)
            if skew > 0.5:
                add("warn", "tg", f"X1/X2 cables differ by {s_fmt_ns(skew)}: use equal lengths (adds directly to the gate width).")
        if fA > P or (mode == 2 and fB > P):
            add("warn", "tg", "Gate edges extend beyond one output period.")
        add("info", "tg", "Measure the TG10 output into 50 Ω first: 3.5…5 V amplitude, rise/fall ≤ 10 ns (driver manual §6.6).")
        # --- HV side ---
        vr, um = self.rail.value(), self.umax()
        if not hv["bip"]:
            add("warn", "hvs", "This HVS-100 model is unipolar. The driver needs +HV and −HV rails: use two units (only the "
                               "HVS100-2X60 has a −HV output).")
        if vr > rmax + 1e-9:
            add("err", "hvs", f"Rail ±{vr:.2f} kV exceeds {name} maximum working voltage ±{rmax} kV.")
        if vr > um + 1e-9:
            add("err", "hvs", f"Rail ±{vr:.2f} kV is above the selected supply maximum {um:.1f} kV.")
        elif vr < 0.4 * um - 1e-9:
            add("err", "hvs", f"Rail ±{vr:.2f} kV is below the HVS-100 control limit (40 % of Umax = {0.4*um:.2f} kV).")
        else:
            add("ok", "hvs", f"Rail ±{vr:.2f} kV inside the HVS-100 control range ({0.4*um:.2f}…{um:.1f} kV) "
                             f"and ≤ driver ±{rmax} kV.")
        vc = min(2 * vr, vout)
        k, inv = CELL_MODES[self.cb_pmode.currentText()]
        need = self.vpi.value() / k
        tr_ = _m.sin(_m.pi / 2 * k * vc / self.vpi.value()) ** 2
        tr_ = 1 - tr_ if inv else tr_
        if vc < 0.98 * need:
            add("warn", "cell", f"Cell voltage {vc:.2f} kV &lt; full-open {need:.2f} kV: open transmission only {tr_*100:.1f} %.")
        elif vc > 1.02 * need:
            add("warn", "cell", f"Cell voltage {vc:.2f} kV > full-open {need:.2f} kV: over-driven, open transmission {tr_*100:.1f} %.")
        else:
            add("ok", "cell", f"Cell voltage {vc:.2f} kV ≈ full-open {need:.2f} kV (transmission {tr_*100:.1f} %).")
        if need > vout:
            add("err", "cell", f"Cell needs {need:.2f} kV but {name} only delivers {vout} kV: use a lower-Vπ cell or double-pass mode.")
        if C < 4 or C > 10:
            add("err" if C < 4 else "warn", "cell", f"Load capacitance {C:.1f} pF outside the 4…10 pF window "
                                                    f"({'driver must not run unloaded' if C < 4 else 'derate voltage or repetition rate - contact EKSMA'}).")
        else:
            add("ok", "cell", f"Load capacitance {C:.1f} pF within 4…10 pF; rise/fall ≈ {tr0*max(1,C/6):.1f} ns (spec &lt;{tr0}/{tf0} ns at 6 pF).")
        # --- power ---
        p_est = f * C * 1e-12 * (vc * 1e3) ** 2
        avail = 2 * hv["p"] * (vr / um) if um else 0
        if p_est > avail:
            add("err", "hvs", f"Estimated HV dissipation f·C·V² ≈ {p_est:.1f} W exceeds supply capability ≈ {avail:.0f} W at this setting.")
        else:
            add("ok", "hvs", f"Estimated HV dissipation f·C·V² ≈ {p_est:.1f} W (driver spec &lt; {pmax:.0f} W); supply ≈ {avail:.0f} W available.")
        need24 = 24 * idc / 1000.0
        if hv["p24"] is None:
            add("warn", "hvs", "HVS100-150 has no 24 V output: the driver needs an external 24 V ±1 V supply "
                               f"({idc} mA, ≥0.6 A peak at start).")
            self.sev24 = "warn"
        else:
            add("ok", "hvs", f"24 V for the driver: {need24:.1f} W needed (0.6 A peak at start) vs {hv['p24']:.0f} W free on the HVS-100.")
            self.sev24 = "ok"
        gate = (fB + self.cab2) - (rA + self.cab1) if mode == 2 else (fA - rA)
        if gate > 0:
            add("info", "cell", f"Gate length {s_fmt_ns(gate)}; HV droop over the gate = {(1-_m.exp(-gate/(33000.0*C)))*100:.2f} % "
                                f"(τ = 33 MΩ·C = {s_fmt_ns(33000.0*C)}).")
        return ck

    def refresh(self):
        d = self.d
        self.sev24 = "ok"
        self.checks = ck = self.evaluate()
        order = {"ok": 0, "info": 0, "warn": 1, "err": 2}
        worst = {z: "ok" for z in ("tg", "dpb", "hvs", "cell")}
        for sev, area, _t in ck:
            if order[sev] > order[worst[area]]:
                worst[area] = sev
        mode, a, b = self.mode(), self.a(), self.b()
        name = self.cb_dpb.currentText()
        fmax, vout, rmax, *_ = DPB_MODELS[name]
        ra, fa = d.edges(a)
        rb, fb = d.edges(b)
        vr = self.rail.value()
        k, _inv = CELL_MODES[self.cb_pmode.currentText()]
        g = self.diag
        g["sev"] = worst
        g["sev24"] = self.sev24
        g["tg"] = [f"OUT{a}: DEL {s_fmt_ns(d.rows[a]['del'].value())}", f"width {s_fmt_ns(fa-ra)}",
                   (f"OUT{b}: DEL {s_fmt_ns(d.rows[b]['del'].value())}" if mode == 2 else "OUT-b unused (1-input)"),
                   f"period {d.period_txt()}", f"rate {d.rate_txt()}",
                   f"clock {s_fmt_freq(d.ctx['f_ref'])}"]
        g["dpb_title"] = f"{name}"
        g["dpb"] = [f"{mode}-input mode (jumper #7 pos. {mode})", f"≤ {fmax} kHz · ≤ {vout} kV", "delay ≈ 30 ns typ.",
                    "pulse 100…5000 ns", "trigger 3.5…5 V @50 Ω", f"cable X1 {s_fmt_ns(self.cab1)}" + (f" · X2 {s_fmt_ns(self.cab2)}" if mode == 2 else "")]
        g["hvs_title"] = self.cb_hvs.currentText()
        g["hvs"] = [f"rails ±{vr:.2f} kV (Umax {self.umax():.1f} kV)", f"cell voltage = 2 × rail = {min(2*vr, vout):.2f} kV",
                    "24 V out → driver DC"]
        g["cell"] = [self.cb_cell.currentText().split(",")[0], f"Vπ {self.vpi.value():.2f} kV", f"full open {self.vpi.value()/k:.2f} kV",
                     f"C = {self.cap.value():.1f} pF"]
        g["laser"] = [f"{d.planner.lrep.value():.3g} MHz", f"{d.planner.lfw.value():.3g} ns"] if hasattr(d, "planner") else []
        g["a1"] = f"OUT{a} → X1"
        g["a2"] = f"OUT{b} → X2" if mode == 2 else "X2 unused"
        g["a_hv"] = "±HV rails"
        g["vcell"] = f"V_cell = {min(2*vr, vout):.2f} kV"
        self.diagram.update()
        self.mdiag.update()
        self.mtxt.setText(self.mode_table_html())
        self._update_send()
        rows = []
        for sev, area, t in ck:
            rows.append(f"<span style='color:{SEV_COL[sev]}'><b>{SEV_ICON[sev]}</b> {t}</span>")
        proc = ("<div style='color:#2a3b4c'><br><b style='color:#0b4778'>OPERATING ORDER (from the DPB1 / HVS-100 manuals)</b><br>"
                "1. Ground driver, HV supply and generator together (mount on the laser body); load connected (4…10 pF), wires ≤100 mm, equal length, ≥5 mm clear of conductors.<br>"
                "2. Switch on the 24 V DC supply (≥0.6 A peak) and the HV supply; confirm no overshoot while the HV rises.<br>"
                "3. <b>Only then</b> enable the SYNC pulses (TG10 outputs). Never apply SYNC IN pulses before HV and 24 V, nor keep them after power-down.<br>"
                "4. Shutdown: stop the SYNC pulses first, then HV OFF, then 24 V. Do not connect/disconnect the load while the supply is on.<br>"
                "5. Never probe the +OUT/−OUT pins; measure the pulse indirectly with an isolated 1:10 probe ≈10 mm from the output wire.<br>"
                "<span style='color:#d83b3b'>Voltages above 1000 V: qualified persons only. System safety is the assembler's responsibility.</span></div>")
        self.txt.setText("<b style='color:#0b4778'>COMPATIBILITY AND LIMIT CHECKS</b><br>" + "<br>".join(rows) + "<br>" + proc)


# ------------------------------------------------------------
# Quantum-photonics planner: excitation -> emitter lifetime -> gated single-photon detection
# ------------------------------------------------------------
EMITTERS = {                      # illustrative lifetimes; use your own sample's value
    "Quantum dot (InAs, ~1 ns)": 1.0,
    "NV centre in diamond (~12 ns)": 12.0,
    "Trapped ion / alkali atom (~25 ns)": 26.0,
    "Heralded SPDC photon (ps-scale)": 0.01,
    "Custom lifetime": 10.0,
}
DETECTORS = {                     # (efficiency %, jitter FWHM ps, dark cps, gate turn-on ns) - typical, verify datasheet
    "Si SPAD, gated (typ.)": (60.0, 350.0, 100.0, 1.0),
    "InGaAs gated APD, telecom (typ.)": (25.0, 200.0, 2000.0, 1.0),
    "SNSPD, counter window (typ.)": (85.0, 40.0, 100.0, 0.5),
    "Custom detector": (50.0, 300.0, 200.0, 1.0),
}


def _log_erfc(z):
    if z < 18.0:
        return _m.log(max(_m.erfc(z), 1e-300))
    return -z * z - _m.log(z * _m.sqrt(_m.pi))


def exg_pdf(t, mu, sig, tau):
    """Exponential decay (lifetime tau) convolved with Gaussian IRF (sigma): photon arrival density."""
    if tau < 1e-4:
        s = max(sig, 1e-6)
        return _m.exp(-0.5 * ((t - mu) / s) ** 2) / (s * _m.sqrt(2 * _m.pi))
    if sig < 1e-5:
        return _m.exp(-(t - mu) / tau) / tau if t >= mu else 0.0
    z = (sig * sig / tau - (t - mu)) / (sig * _m.sqrt(2))
    lg = -_m.log(2 * tau) + sig * sig / (2 * tau * tau) - (t - mu) / tau + _log_erfc(z)
    return _m.exp(min(lg, 700.0))


def exg_cdf(t, mu, sig, tau):
    phi = lambda x: 0.5 * _m.erfc(-x / _m.sqrt(2))
    if tau < 1e-4:
        return phi((t - mu) / max(sig, 1e-6))
    if sig < 1e-5:
        return 1 - _m.exp(-(t - mu) / tau) if t >= mu else 0.0
    x = (t - mu) / sig
    a = sig * sig / (2 * tau * tau) - (t - mu) / tau
    lg = a + _log_erfc(-(x - sig / tau) / _m.sqrt(2)) + _m.log(0.5)
    return min(1.0, max(0.0, phi(x) - _m.exp(min(lg, 700.0))))


def _cycles(T, tau):
    return 0 if T <= 1e-6 else min(20, int(12 * tau / T) + 1)


def in_gate_sharp(op, cl, mu, sig, tau, T, k0=0):
    return sum(exg_cdf(cl, mu - k * T, sig, tau) - exg_cdf(op, mu - k * T, sig, tau)
               for k in range(k0, _cycles(T, tau) + 1))


def quantum_calc(Q):
    tau, sig, mu, T = Q["tau"], Q["sig"], Q["mu"], Q["T"]
    op, cl, ton, toff = Q["open"], Q["close"], max(Q["ton"], 1e-3), max(Q["toff"], 1e-3)
    W = cl - op
    edge = lambda t, t0, w: 0.5 * (1 + _m.erf((t - t0) / (w / 2.563 * _m.sqrt(2))))
    G = lambda t: edge(t, op, ton) - edge(t, cl, toff)
    lo, hi = op - 4 * ton - 1, min(cl + 4 * toff + 1, mu + 14 * tau + 8 * sig + 1)
    p0 = 0.0
    if hi > lo:
        cand = [x for x in (sig, tau, ton, toff) if x > 1e-4]
        h = 0.2 * (min(cand) if cand else 1.0)
        N = int(min(8000, max(400, (hi - lo) / max(h, 1e-6))))
        dt = (hi - lo) / N
        for i in range(N):
            t = lo + (i + 0.5) * dt
            g = G(t)
            if g > 1e-6:
                p0 += exg_pdf(t, mu, sig, tau) * g * dt
    cross = in_gate_sharp(op, cl, mu, sig, tau, T, 1)
    Pg = p0 + cross
    S = Q["eta"] * Pg
    noise = (Q["dcr"] + Q["bg"]) * 1e-9 * max(W, 0)
    # SNR-optimal gate width (ideal edges, gate opened at the suggested time)
    sug_open = mu - 3 * sig - 0.5 * ton
    wmin = max(0.05, 0.3 * max(2.355 * sig, ton))
    wmax = max(wmin * 2, min(T * 0.95, 25 * tau + 10 * sig + 5))
    sweep = []
    for i in range(48):
        w = wmin * (wmax / wmin) ** (i / 47)
        s_ = Q["eta"] * in_gate_sharp(sug_open, sug_open + w, mu, sig, tau, T)
        n_ = (Q["dcr"] + Q["bg"]) * 1e-9 * w
        sweep.append((w, s_ / _m.sqrt(s_ + n_ + 1e-30)))
    wopt = max(sweep, key=lambda p: p[1])[0]
    return dict(W=W, early=exg_cdf(op, mu, sig, tau), late=1 - exg_cdf(cl, mu, sig, tau), p0=p0, cross=cross,
                Pg=Pg, S=S, noise=noise, sbr=S / noise if noise > 0 else float("inf"),
                supp=T / W if W > 0 else float("inf"), rate=S / T * 1e9 if T > 0 else 0.0,
                sweep=sweep, wopt=wopt, sug_open=sug_open, G=G)


class QuantumView(QWidget):
    def __init__(self):
        super().__init__()
        self.R = None
        self.setMinimumHeight(480)

    def paintEvent(self, _):
        p = QPainter(self)
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, SIM_BG)
        R = self.R
        if not R:
            p.end()
            return
        Q, C = R["Q"], R["C"]
        t0, t1 = R["view"]
        span = max(t1 - t0, 1e-9)
        px = lambda t: (t - t0) / span * W
        sf, lf = QFont("Consolas", 8), QFont("Segoe UI", 9)
        step = s_nice_step(span) * 2
        p.setFont(sf)
        t = _m.ceil(t0 / step) * step
        while t <= t1:
            p.setPen(QPen(SIM_GRID, 1))
            p.drawLine(QPointF(px(t), 6), QPointF(px(t), 300))
            p.setPen(SIM_DIM)
            p.drawText(QPointF(px(t) + 2, 312), s_fmt_ns(t))
            t += step
        p.setFont(lf)
        p.setPen(QColor(147, 168, 147))
        p.drawText(QPointF(8, 16), "TG10 OUTPUTS (excitation / detector gate)")
        p.drawText(QPointF(8, 112), "PHOTON ARRIVAL (cyan) · DETECTED (green) · GATE WINDOW (amber)")
        p.drawText(QPointF(8, 336), "SIGNAL / √(SIGNAL+NOISE) vs GATE WIDTH (ideal edges)")

        def digital(rE, fE, y_hi, y_lo, col):
            P = Q["T"]
            path = QPainterPath()
            path.moveTo(0, y_lo)
            nlo, nhi = _m.floor((t0 - fE) / P), _m.ceil((t1 - rE) / P)
            if nhi - nlo > 400:
                return
            for n in range(nlo, nhi + 1):
                x1, x2 = px(rE + n * P), px(fE + n * P)
                path.lineTo(x1, y_lo)
                path.lineTo(x1, y_hi)
                path.lineTo(x2, y_hi)
                path.lineTo(x2, y_lo)
            path.lineTo(W, y_lo)
            p.setPen(QPen(col, 2.0))
            p.drawPath(path)

        if R["exc_edges"]:
            digital(*R["exc_edges"], 24, 52, QColor(SIM_COLORS[R["exc_ch"]]).lighter(150))
        digital(*R["gate_edges"], 62, 92, QColor(SIM_COLORS[R["gate_ch"]]).lighter(150))
        # photon pdf
        top, h = 120, 170
        n = max(200, W // 2)
        mu, sig, tau, T = Q["mu"], Q["sig"], Q["tau"], Q["T"]
        K = _cycles(T, tau)
        pdf = lambda tt: sum(exg_pdf(tt, mu - k * T, sig, tau) for k in range(K + 1))
        ts = [t0 + span * i / n for i in range(n + 1)]
        vals = [pdf(tt) for tt in ts]
        vmax = max(vals) or 1.0
        Gf = C["G"]
        for col, fn in ((QColor(90, 217, 255, 90), lambda i: vals[i]), (QColor(80, 220, 120, 150), lambda i: vals[i] * Gf(ts[i]))):
            path = QPainterPath()
            path.moveTo(0, top + h)
            for i in range(n + 1):
                path.lineTo(i / n * W, top + h - 0.9 * h * fn(i) / vmax)
            path.lineTo(W, top + h)
            p.fillPath(path, col)
        path = QPainterPath()
        for i in range(n + 1):
            (path.lineTo if i else path.moveTo)(i / n * W, top + h - 0.95 * h * Gf(ts[i]))
        p.setPen(QPen(QColor(255, 190, 70), 2.0))
        p.drawPath(path)
        p.setFont(sf)
        for k, (tt, lab, col) in enumerate(((Q["t_exc"], "EXCITE", QColor(255, 235, 120)), (mu, "PHOTON PEAK", QColor(90, 217, 255)),
                                            (Q["open"], "GATE OPEN 50%", QColor(255, 190, 70)), (Q["close"], "GATE CLOSE 50%", QColor(255, 190, 70)))):
            if t0 <= tt <= t1:
                p.setPen(QPen(col, 1, Qt.DashLine))
                p.drawLine(QPointF(px(tt), 120), QPointF(px(tt), 300))
                p.setPen(col)
                p.drawText(QPointF(min(px(tt) + 3, W - 110), 134 + 12 * k), lab)
        # sweep plot
        top2, h2 = 345, H - 345 - 28
        sw = C["sweep"]
        wmin, wmax = sw[0][0], sw[-1][0]
        fmax = max(v for _, v in sw) or 1.0
        lx = lambda w: (_m.log(w / wmin) / _m.log(wmax / wmin)) * (W - 20) + 10
        path = QPainterPath()
        for i, (w, v) in enumerate(sw):
            (path.lineTo if i else path.moveTo)(lx(w), top2 + h2 - 0.9 * h2 * v / fmax)
        p.setPen(QPen(QColor(90, 217, 255), 2))
        p.drawPath(path)
        for w, col, lab in ((C["wopt"], QColor(80, 220, 120), f"optimum {s_fmt_ns(C['wopt'])}"),
                            (C["W"], QColor(255, 120, 120), f"current {s_fmt_ns(C['W'])}")):
            if wmin <= w <= wmax:
                p.setPen(QPen(col, 1.5, Qt.DashLine))
                p.drawLine(QPointF(lx(w), top2), QPointF(lx(w), top2 + h2))
                p.setPen(col)
                p.drawText(QPointF(min(lx(w) + 4, W - 120), top2 + 12 + (12 if lab.startswith("cur") else 0)), lab)
        p.setPen(SIM_DIM)
        p.drawText(QPointF(10, H - 8), s_fmt_ns(wmin))
        p.drawText(QPointF(W - 70, H - 8), s_fmt_ns(wmax))
        p.end()


class QuantumPlanner(QWidget):
    def __init__(self, dlg):
        super().__init__()
        self.d = dlg
        self.R = None
        self._lock = True
        root = QHBoxLayout(self)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFixedWidth(470)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        holder = QWidget()
        left = QVBoxLayout(holder)
        sc.setWidget(holder)
        root.addWidget(sc)
        right = QVBoxLayout()
        root.addLayout(right, 1)

        def spin(lo, hi, val, dec, suf):
            s = QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setDecimals(dec)
            s.setValue(val)
            s.setSuffix(suf)
            s.valueChanged.connect(self.refresh)
            return s

        def group(title, rows):
            g = QGroupBox(title)
            l = QGridLayout(g)
            for i, (n, w) in enumerate(rows):
                l.addWidget(QLabel(n), i, 0)
                l.addWidget(w, i, 1)
            left.addWidget(g)

        self.cb_exc = QComboBox()
        self.cb_gate = QComboBox()
        for c in (self.cb_exc, self.cb_gate):
            c.addItems([f"OUT{i}" for i in range(8)])
            c.currentIndexChanged.connect(self.refresh)
        self.cb_gate.setCurrentIndex(1)
        self.ck_ext = QCheckBox("Excitation laser is external (not fired by a TG10 output)")
        self.ck_ext.toggled.connect(self.refresh)
        self.arr = spin(-1e9, 1e10, 100, 3, " ns")
        self.exlat = spin(-1e6, 1e6, 50, 3, " ns")
        group("Which TG10 outputs", [("Excitation / laser trigger", self.cb_exc), ("Detector gate", self.cb_gate),
                                     ("", self.ck_ext), ("Ext. laser pulse at emitter", self.arr),
                                     ("Trigger → pulse latency", self.exlat)])

        self.cb_em = QComboBox()
        self.cb_em.addItems(EMITTERS.keys())
        self.cb_em.activated.connect(self._emitter)
        self.tau = spin(0.0001, 1e6, 10, 4, " ns")
        self.lfw = spin(0.0001, 1e4, 0.1, 4, " ns")
        self.path = spin(0, 1e6, 25, 3, " ns")
        self.coll = spin(0.001, 100, 10, 3, " %")
        group("Emitter / photon source", [("Emitter", self.cb_em), ("Lifetime τ", self.tau),
                                          ("Excitation pulse FWHM", self.lfw), ("Emitter → detector delay", self.path),
                                          ("Collection efficiency", self.coll)])

        self.cb_det = QComboBox()
        self.cb_det.addItems(DETECTORS.keys())
        self.cb_det.activated.connect(self._detector)
        self.eff = spin(0.1, 100, 60, 2, " %")
        self.jit = spin(0, 1e5, 350, 1, " ps")
        self.dcr = spin(0, 1e9, 100, 1, " cps")
        self.bg = spin(0, 1e9, 50, 1, " cps")
        self.glat = spin(-1e6, 1e6, 10, 3, " ns")
        self.ton = spin(0.001, 1e5, 1.0, 3, " ns")
        self.toff = spin(0.001, 1e5, 1.0, 3, " ns")
        self.tgj = spin(0, 1e6, 0, 1, " ps")
        group("Detector && gate driver", [("Detector", self.cb_det), ("Efficiency", self.eff), ("Jitter FWHM", self.jit),
                                         ("Dark counts", self.dcr), ("Background", self.bg),
                                         ("Gate driver latency", self.glat), ("Gate turn-on 10-90 %", self.ton),
                                         ("Gate turn-off", self.toff), ("TG10 extra jitter rms", self.tgj)])
        self.cb_view = QComboBox()
        self.cb_view.addItems(["View: whole sequence", "View: photon pulse", "View: gate opening edge"])
        self.cb_view.currentIndexChanged.connect(self.refresh)
        left.addWidget(self.cb_view)
        b = QPushButton("Apply suggested DEL / width to the gate output")
        b.clicked.connect(self._apply)
        left.addWidget(b)
        left.addStretch(1)

        self.view = QuantumView()
        right.addWidget(self.view, 1)
        self.txt = QLabel()
        self.txt.setTextFormat(Qt.RichText)
        self.txt.setWordWrap(True)
        self.txt.setStyleSheet("background:#f4f8fb; border:1px solid #c5d4e2; border-radius:4px; padding:6px;")
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(self.txt)
        sa.setMinimumHeight(250)
        right.addWidget(sa)
        self._lock = False

    def _emitter(self, *_):
        self.tau.setValue(EMITTERS[self.cb_em.currentText()])

    def _detector(self, *_):
        e, j, dc, ton = DETECTORS[self.cb_det.currentText()]
        self._lock = True
        for w, v in ((self.eff, e), (self.jit, j), (self.dcr, dc), (self.ton, ton), (self.toff, ton)):
            w.setValue(v)
        self._lock = False
        self.refresh()

    def _apply(self):
        R = self.R
        if R and R["sug"]:
            row = self.d.rows[R["gate_ch"]]
            row["del"].setValue(max(0.025, R["sug"]["del"]))
            row["pw"].setValue(R["sug"]["pw"])

    def refresh(self, *_):
        if self._lock:
            return
        d, c = self.d, self.d.ctx
        ge, gg = self.cb_exc.currentIndex(), self.cb_gate.currentIndex()
        ext = self.ck_ext.isChecked()
        T = d.period
        gR, gF = d.edges(gg)
        eR, eF = d.edges(ge)
        t_exc = self.arr.value() if ext else eR + self.exlat.value()
        lat = self.glat.value()
        sig_l = self.lfw.value() / 2.355
        sig_d = self.jit.value() * 1e-3 / 2.355
        sig_u = self.tgj.value() * 1e-3
        dom = c["ext_clk"] and ((gg == 4) if ext else ((ge == 4) != (gg == 4)))
        sig_dom = d.t_ref_ch(4) / _m.sqrt(12) if dom else 0.0
        sig_s = d.t_ref_ch(gg) / _m.sqrt(12) if (ext and c["f_sync"]) else 0.0
        sig = _m.sqrt(sig_l ** 2 + sig_d ** 2 + sig_u ** 2 + sig_dom ** 2 + sig_s ** 2)
        Q = dict(tau=self.tau.value(), sig=sig, mu=t_exc + self.path.value(), T=T, t_exc=t_exc,
                 open=gR + lat, close=gF + lat, ton=self.ton.value(), toff=self.toff.value(),
                 eta=self.coll.value() / 100 * self.eff.value() / 100, dcr=self.dcr.value(), bg=self.bg.value())
        C = quantum_calc(Q)
        # suggestion
        stepd, resw, gap = d.delay_step(gg), d.width_res(gg), d.sync_gap(gg)
        s_del = round((C["sug_open"] - lat) / stepd) * stepd
        s_pw = max(MIN_WIDTH_NS, round((C["wopt"] - gap) / resw) * resw)
        sug = dict(**{"del": s_del, "pw": s_pw})
        span_lo = min(Q["open"] - 3 * Q["ton"], Q["mu"] - 5 * sig, (eR if not ext else Q["t_exc"]))
        span_hi = max(Q["close"] + 3 * Q["toff"], Q["mu"] + 8 * Q["tau"] + 5 * sig)
        pad = 0.04 * (span_hi - span_lo + 1e-9)
        vm = self.cb_view.currentIndex()
        if vm == 1:
            view = (Q["mu"] - 6 * sig - 0.5, Q["mu"] + 8 * Q["tau"] + 6 * sig + 0.5)
        elif vm == 2:
            view = (Q["open"] - 6 * Q["ton"] - 1, Q["open"] + 6 * Q["ton"] + 1)
        else:
            view = (span_lo - pad, span_hi + pad)
        R = dict(Q=Q, C=C, sug=sug, view=view, exc_ch=ge, gate_ch=gg, ext=ext,
                 exc_edges=None if ext else (eR, eF), gate_edges=(gR + lat, gF + lat), sigs=(sig_l, sig_d, sig_u, sig_dom, sig_s, sig))
        self.R = R
        self.view.R = R
        self.view.update()
        self._text(R, ge, gg, T, c, lat, gap)

    def _text(self, R, ge, gg, T, c, lat, gap):
        Q, C, d = R["Q"], R["C"], self.d
        sl, sd, su, sdom, ss, st = R["sigs"]
        h = ["<b style='color:#0b4778'>WHAT THE TG10 TIMING DOES TO YOUR PHOTONS</b>"]
        if R["ext"]:
            h.append(f"Excitation: external laser, pulse at emitter at {s_fmt_ns(Q['t_exc'])} after TRIG.")
        else:
            eR, eF = d.edges(ge)
            h.append(f"<b>OUT{ge} (excitation)</b>: DEL → realized rise {s_fmt_ns(eR)} → laser pulse at emitter {s_fmt_ns(Q['t_exc'])}.")
        h.append(f"Photons: lifetime τ = {s_fmt_ns(Q['tau'])} → arrival peak at detector <b>{s_fmt_ns(Q['mu'])}</b>, "
                 f"earliest ≈ {s_fmt_ns(Q['mu'] - 3*st)}.")
        gR, gF = d.edges(gg)
        margin = Q["mu"] - 3 * st - Q["open"]
        h.append(f"<b>OUT{gg} (detector gate)</b>: rise {s_fmt_ns(gR)} + driver {s_fmt_ns(lat)} → gate OPENS (50 %) at "
                 f"<b>{s_fmt_ns(Q['open'])}</b>; fall {s_fmt_ns(gF)} → CLOSES at <b>{s_fmt_ns(Q['close'])}</b>; window {s_fmt_ns(C['W'])}"
                 + (f" (incl. {s_fmt_ns(gap)} sync gap)" if gap else "") + ".")
        if margin < 0:
            h.append(f"<span style='color:#d83b3b'>Gate opens {s_fmt_ns(-margin)} too LATE: early photons are cut.</span>")
        else:
            h.append(f"Gate opens {s_fmt_ns(margin)} before the earliest photons (turn-on {s_fmt_ns(self.ton.value())}).")
        h.append(f"<b>Photon budget</b>: lost before gate {C['early']*100:.2f} % · lost after gate {C['late']*100:.2f} % · "
                 f"in gate {C['p0']*100:.2f} %" + (f" (+{C['cross']*100:.2f} % tails of earlier excitation cycles)" if C["cross"] > 1e-4 else "") + ".")
        h.append(f"<b>Detection probability per excitation</b> = {C['S']:.3e} "
                 f"(collection × detector × gate) · count rate ≈ <b>{s_fmt_freq(C['rate'])}</b> at {s_fmt_freq(1e9/T)} repetition.")
        h.append(f"<b>Noise</b>: dark + background per gate = {C['noise']:.3e} counts → signal/noise = "
                 f"<b>{C['sbr']:.2f}</b>; gating suppresses noise by <b>{C['supp']:.1f}×</b> versus a free-running detector.")
        h.append(f"<b>Timing budget (rms)</b>: laser {s_fmt_ns(sl)} · detector {s_fmt_ns(sd)} · TG10 extra {s_fmt_ns(su)}"
                 + (f" · clock-domain walk {s_fmt_ns(sdom)}" if sdom else "") + (f" · SYNC IN sampling {s_fmt_ns(ss)}" if ss else "")
                 + f" → total σ = <b>{s_fmt_ns(st)}</b> (FWHM {s_fmt_ns(2.355*st)}); suggested coincidence / time-tag window ≈ ±3σ = <b>±{s_fmt_ns(3*st)}</b>.")
        if C["W"] < 2.355 * st:
            h.append("<span style='color:#d98200'>Gate is narrower than the timing resolution: photons will be clipped by jitter.</span>")
        if Q["T"] < 5 * Q["tau"]:
            h.append(f"<span style='color:#d98200'>Repetition period {s_fmt_ns(Q['T'])} &lt; 5τ: the emitter has not decayed before the next excitation (pile-up / re-excitation).</span>")
        if C["W"] > Q["T"]:
            h.append("<span style='color:#d83b3b'>Gate is wider than the repetition period.</span>")
        sg = R["sug"]
        line = (f"<b style='color:#0b4778'>SUGGESTION</b> (maximises S/√(S+N)): gate DEL{gg} = <b>{s_fmt_ns(sg['del'])}</b>, "
                f"post-DEL{gg} width = <b>{s_fmt_ns(sg['pw'])}</b> (optical window {s_fmt_ns(C['wopt'])}, snapped to hardware steps).")
        if sg["del"] < 0:
            line += " <span style='color:#d83b3b'>Needs negative delay: delay the photons (longer path) or trigger the gate earlier.</span>"
        h.append(line)
        h.append(d.clock_note(gg))
        if not R["ext"] and ge != gg:
            h.append(d.clock_note(ge))
        h.append("<span style='color:#5a7085'>Planning model (single exponential emitter, Gaussian response, ideal erf gate edges). "
                 "Confirm detector and driver numbers with their datasheets.</span>")
        self.txt.setText("<br>".join(h))


# ------------------------------------------------------------
# Main simulator window
# ------------------------------------------------------------
class SimulatorDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.pw = parent
        self.setWindowTitle("TG10 Simulator & Photonics Planner (Pockels cells · quantum detection)")
        self.resize(1320, 860)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.period = 1000.0
        self.f_sys = 3e9
        self.center, self.ns_per_div = 500.0, 100.0
        self.cursor1, self.cursor2 = 30.0, 230.0
        self.sel = 0
        self.rows = []
        self._width_cache = {}
        self._busy = False
        self.prog_period = 1000.0
        self._sig = None
        self._ready = False
        self._read_ctx()

        root = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Output period"))
        self.sp_period = QDoubleSpinBox()
        self.sp_period.setRange(1, 1e12)
        self.sp_period.setDecimals(3)
        self.sp_period.setSuffix(" ns")
        self.sp_period.setValue(1000)
        self.sp_period.valueChanged.connect(self._period_changed)
        top.addWidget(self.sp_period)
        self.lbl_info = QLabel("")
        top.addWidget(self.lbl_info, 1)
        b_load = QPushButton("Load from Delay presets / main window")
        b_push = QPushButton("Send values to Delay presets")
        b_open = QPushButton("Open Delay presets (apply to hardware)")
        b_load.clicked.connect(self.load_from_main)
        b_push.clicked.connect(self.push_to_main)
        b_open.clicked.connect(self.pw.open_delay)
        for b in (b_load, b_push, b_open):
            top.addWidget(b)
        root.addLayout(top)

        top2 = QHBoxLayout()
        self.sp_ndiv = QSpinBox()
        self.sp_ndiv.setRange(1, 200)
        self.sp_ndiv.setValue(getattr(self.pw, "system_ndiv", 30))
        self.sp_ndiv.setToolTip("ASSUMED PLL multiplier: f_sys = f_ref x Ndiv (internal: 100 MHz x 30 = 3 GHz)")
        self.sp_ndiv.valueChanged.connect(self._ndiv_changed)
        self.sp_sync = QSpinBox()
        self.sp_sync.setRange(0, 6)
        self.sp_sync.setValue(1)
        self.sp_sync.setToolTip("Extra reference-clock cycles on the FALL path with an external CLK IN "
                                "(models the measured TG10-vs-scope pulse-width gap)")
        self.sp_sync.valueChanged.connect(self.refresh)
        self.cb_qper = QCheckBox("Lock output period to reference clock")
        self.cb_qper.setChecked(True)
        self.cb_qper.toggled.connect(self.refresh)
        for wdg in (QLabel("PLL Ndiv (assumed)"), self.sp_ndiv, QLabel("Fall-path sync cycles (ext. CLK IN)"),
                    self.sp_sync, self.cb_qper):
            top2.addWidget(wdg)
        top2.addStretch(1)
        root.addLayout(top2)

        top3 = QHBoxLayout()
        self.ck_follow = QCheckBox("Follow main-window Sync card")
        self.ck_follow.setChecked(True)
        self.cb_sync = QComboBox()
        self.cb_sync.addItems([c[0] for c in SYNC_CHOICES])
        self.sp_clk = QDoubleSpinBox()
        self.sp_clk.setDecimals(6)
        self.sp_clk.setSuffix(" MHz")
        self.sp_clk.setRange(10.0, 100.0)
        self.sp_clk.setValue(100.0)
        self.sp_syn = QDoubleSpinBox()
        self.sp_syn.setDecimals(8)
        self.sp_syn.setSuffix(" MHz")
        self.sp_syn.setRange(1e-8, 20.0)
        self.sp_syn.setValue(1.0)
        self.b_copy = QPushButton("Copy to main Sync card")
        self.b_copy.clicked.connect(self._push_sync_to_main)
        self.ck_follow.toggled.connect(self._follow_toggled)
        self.cb_sync.currentIndexChanged.connect(self._sync_ui)
        self.sp_clk.valueChanged.connect(self._sync_ui)
        self.sp_syn.valueChanged.connect(self._sync_ui)
        self.sp_clk.setToolTip("CLK IN: 20-100 MHz (SINGLE IN) or 10-100 MHz (DUAL IN)")
        self.sp_syn.setToolTip("SYNC IN: 0.01 Hz ... 20 MHz")
        for wdg in (self.ck_follow, QLabel("Sync mode"), self.cb_sync, QLabel("CLK IN"), self.sp_clk,
                    QLabel("SYNC IN"), self.sp_syn, self.b_copy):
            top3.addWidget(wdg)
        top3.addStretch(1)
        root.addLayout(top3)
        self._update_sync_enabled()

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self.tabs.addTab(self._build_sim_tab(), "Timing Simulator")
        self.setup = SetupPanel(self)
        self.tabs.addTab(self.setup, "Setup: TG10 → DPB1 driver → Pockels cell")
        self.planner = PockelsPlanner(self)
        self.tabs.addTab(self.planner, "Pockels Cell (optical switching)")
        self.quantum = QuantumPlanner(self)
        self.tabs.addTab(self.quantum, "Quantum Photonics (gated detection)")
        self.ov = self._build_overview_tab()
        self.tabs.addTab(self.ov, "All Outputs Overview")
        self.tabs.currentChanged.connect(lambda *_: self.refresh())
        self._ready = True
        self.load_from_main()
        self._poll = QTimer(self)
        self._poll.timeout.connect(self._poll_main)
        self._poll.start(700)

    # --- tab 1 ---
    def _build_sim_tab(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        left = QGroupBox("Outputs (DEL = rise delay after trigger, width = post-delay)")
        gl = QGridLayout(left)
        for c, t in enumerate(["Show", "Out", "DEL (ns)", "Width (ns)", "Realized rise", "Realized fall"]):
            gl.addWidget(QLabel(f"<b>{t}</b>"), 0, c)
        for i in range(8):
            row = {}
            row["show"] = QCheckBox()
            row["show"].setChecked(i < 4)
            row["show"].toggled.connect(self.refresh)
            row["name"] = QPushButton(f"OUT{i}")
            row["name"].setStyleSheet(f"font-weight:700; color:{SIM_COLORS[i]};")
            row["name"].clicked.connect(lambda _=False, k=i: self.set_sel(k))
            row["del"] = QDoubleSpinBox()
            row["del"].setRange(0.025, 150e6)
            row["del"].setDecimals(3)
            row["del"].setValue(30 + 40 * i)
            row["pw"] = QDoubleSpinBox()
            row["pw"].setRange(MIN_WIDTH_NS, 150e6)
            row["pw"].setDecimals(3)
            row["pw"].setValue(200)
            row["rr"] = QLabel("-")
            row["rf"] = QLabel("-")
            for wdg in (row["del"], row["pw"]):
                wdg.valueChanged.connect(self.refresh)
            for c, wdg in enumerate([row["show"], row["name"], row["del"], row["pw"], row["rr"], row["rf"]]):
                gl.addWidget(wdg, i + 1, c)
            self.rows.append(row)
        gl.setRowStretch(9, 1)
        left.setFixedWidth(560)
        lay.addWidget(left)

        right = QVBoxLayout()
        lay.addLayout(right, 1)
        tb = QHBoxLayout()
        self.sp_div = QDoubleSpinBox()
        self.sp_div.setRange(0.05, 1e10)
        self.sp_div.setDecimals(3)
        self.sp_div.setSuffix(" ns/div")
        self.sp_div.setValue(100)
        self.sp_div.valueChanged.connect(self._view_edit)
        self.sp_center = QDoubleSpinBox()
        self.sp_center.setRange(-1e12, 1e12)
        self.sp_center.setDecimals(3)
        self.sp_center.setSuffix(" ns centre")
        self.sp_center.setValue(500)
        self.sp_center.valueChanged.connect(self._view_edit)
        tb.addWidget(self.sp_div)
        tb.addWidget(self.sp_center)
        tb.addStretch(1)
        for text, fn in (("Autoset", self._autoset), ("Full period", self._autoset), ("Rise edge", self._zoom_rise),
                         ("Fall edge", self._zoom_fall)):
            b = QPushButton(text)
            b.clicked.connect(fn)
            tb.addWidget(b)
        right.addLayout(tb)
        self.scope = SimScope(self)
        self.scope.moved.connect(self._scope_moved)
        right.addWidget(self.scope, 1)
        cb = QHBoxLayout()
        self.lbl_cur = QLabel("")
        self.lbl_cur.setTextFormat(Qt.RichText)
        cb.addWidget(self.lbl_cur, 1)
        for text, fn in (("Cursors → width of selected", self._cur_width), ("Cursors → period", self._cur_period)):
            b = QPushButton(text)
            b.clicked.connect(fn)
            cb.addWidget(b)
        right.addLayout(cb)
        self.lbl_math = QLabel("")
        self.lbl_math.setTextFormat(Qt.RichText)
        self.lbl_math.setWordWrap(True)
        self.lbl_math.setStyleSheet("background:#f4f8fb; border:1px solid #c5d4e2; border-radius:4px; padding:6px;")
        right.addWidget(self.lbl_math)
        self.lbl_sync = QLabel("")
        self.lbl_sync.setTextFormat(Qt.RichText)
        self.lbl_sync.setWordWrap(True)
        self.lbl_sync.setStyleSheet("background:#fff8e8; border:1px solid #e6cf9a; border-radius:4px; padding:6px;")
        right.addWidget(self.lbl_sync)
        return w

    # --- tab 3 ---
    def _build_overview_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(QLabel("Every output at a glance. Enable a Pockels cell per output in the Planner tab."))
        self.tbl = QTableWidget(8, 9)
        self.tbl.setHorizontalHeaderLabels(["Output", "DEL realized", "Fall realized", "Width", "Cell",
                                             "Gate opens", "Gate closes", "Pulses passed", "Verdict"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)
        lay.addWidget(self.tbl, 1)
        return w

    # --- clock / sync model ---
    def _read_ctx(self):
        try:
            base = self.pw.sync_context()
        except Exception:
            base = sync_ctx("Internal", "internal", 100e6, None, 30)
        cf = getattr(self, "ck_follow", None)
        if cf is None or cf.isChecked():
            self.ctx = base
            if cf is not None:
                self._show_sync_controls(base)
        else:
            self.ctx = self._ctx_from_controls()
        self.f_sys = self.ctx["f_sys"]

    def _ctx_from_controls(self):
        _lbl, mode, src, kind = SYNC_CHOICES[self.cb_sync.currentIndex()]
        return sync_ctx(mode, src, self.sp_clk.value() * 1e6, self.sp_syn.value() * 1e6,
                        getattr(self.pw, "system_ndiv", 30), kind)

    def _show_sync_controls(self, c):
        """Mirror the main window's Sync card in the selector (read-only while following)."""
        if c["mode"] == "Internal":
            i = 0
        elif c["mode"] == "External SINGLE IN":
            i = 1 if c["src"] == "CLK IN" else 2
        elif c["mode"] == "External DUAL IN":
            i = 3
        else:
            i = 5 if c.get("kind") == "smart" else 4
        for w in (self.cb_sync, self.sp_clk, self.sp_syn):
            w.blockSignals(True)
        self.cb_sync.setCurrentIndex(i)
        self._update_sync_enabled()
        if c["ext_clk"]:
            self.sp_clk.setValue(c["f_ref"] / 1e6)
        if c["f_sync"]:
            self.sp_syn.setValue(c["f_sync"] / 1e6)
        for w in (self.cb_sync, self.sp_clk, self.sp_syn):
            w.blockSignals(False)

    def _update_sync_enabled(self):
        follow = self.ck_follow.isChecked()
        i = self.cb_sync.currentIndex()
        self.sp_clk.setRange(20.0 if i == 1 else 10.0, 100.0)      # SINGLE IN CLK IN: 20-100 MHz, DUAL IN CLK IN: 10-100 MHz
        self.cb_sync.setEnabled(not follow)
        self.sp_clk.setEnabled((not follow) and i in (1, 3))
        self.sp_syn.setEnabled((not follow) and i in (2, 3))
        self.b_copy.setEnabled(not follow)

    def _sync_ui(self, *_):
        if not getattr(self, "_ready", False):
            return
        self._update_sync_enabled()
        if not self.ck_follow.isChecked():
            self._read_ctx()
            self.refresh()

    def _follow_toggled(self, *_):
        if not getattr(self, "_ready", False):
            return
        self._read_ctx()
        self._update_sync_enabled()
        self.refresh()

    def _push_sync_to_main(self):
        """Copy the what-if Sync selection into the main window's Sync card (hardware is only programmed by its Set button)."""
        pw = self.pw
        i = self.cb_sync.currentIndex()
        try:
            pw._sync_mode_selected({0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 3}[i])
            if i in (1, 2):
                (pw.single_source_clk_radio if i == 1 else pw.single_source_sync_radio).setChecked(True)
                pw.single_rate_unit.setCurrentText("MHz")
                pw._update_single_rate_range()
                pw.external_rate.setValue(self.sp_clk.value() if i == 1 else self.sp_syn.value())
            elif i == 3:
                pw.dual_clk_unit.setCurrentText("MHz")
                pw.dual_sync_unit.setCurrentText("MHz")
                pw._update_dual_rate_ranges()
                pw.dual_clk_input.setValue(self.sp_clk.value())
                pw.dual_sync_input.setValue(self.sp_syn.value())
            elif i in (4, 5):
                (pw.software_trigger if i == 4 else pw.smart_trigger).setChecked(True)
            QMessageBox.information(self, "Sync card", "The main window's Sync card now shows this selection.\n"
                                    "Press its Set button to program the TG10.")
        except Exception as e:
            QMessageBox.warning(self, "Sync card", f"Could not update the Sync card: {e}")

    def _ndiv_changed(self, v):
        self.pw.system_ndiv = v
        self._read_ctx()
        self.refresh()

    def f_sys_ch(self, ch):
        """DEL4 always counts from the INTERNAL clock; every other output follows the active reference."""
        return self.ctx["f_sys_int"] if ch == 4 else self.ctx["f_sys"]

    def t_ref_ch(self, ch):
        return 1e9 / (self.ctx["f_int"] if ch == 4 else self.ctx["f_ref"])

    def delay_step(self, ch):
        return BASE_DELAY_STEP_NS[ch] * 3e9 / self.f_sys_ch(ch)

    def width_res(self, ch):
        return 1e9 / self.f_sys_ch(ch)

    def sync_gap(self, ch):
        return self.sp_sync.value() * self.t_ref_ch(ch) if self.ctx["ext_clk"] else 0.0

    def trig_uncertainty(self, ch):
        """SYNC IN edges are sampled by the reference clock -> up to one reference period of placement uncertainty."""
        return self.t_ref_ch(ch) if self.ctx["f_sync"] else 0.0

    @property
    def oneshot(self):
        return self.ctx["mode"] == "One shot trigger"

    def period_txt(self):
        return "single shot" if self.oneshot else s_fmt_ns(self.period)

    def rate_txt(self):
        return "single shot" if self.oneshot else s_fmt_freq(1e9 / self.period)

    def realize_period(self):
        c, P = self.ctx, self.prog_period
        if c["mode"] == "One shot trigger":
            return 1e15                      # single event: no repetition
        if c["f_sync"]:
            Ts = 1e9 / c["f_sync"]
            return max(1, round(P / Ts)) * Ts
        if self.cb_qper.isChecked():
            Tr = 1e9 / c["f_ref"]
            return max(1, round(P / Tr)) * Tr
        return P

    def clock_note(self, ch):
        c = self.ctx
        lines = []
        dom = ("INTERNAL clock (100 MHz x Ndiv)" if ch == 4 else
               f"{'external CLK IN' if c['ext_clk'] else 'internal reference'} {s_fmt_freq(c['f_ref'])}")
        lines.append(f"<b>Clock domain of OUT{ch}</b>: {dom} → f_sys {s_fmt_freq(self.f_sys_ch(ch))}, "
                     f"DEL step {s_fmt_ns(self.delay_step(ch))}, width step {s_fmt_ns(self.width_res(ch))}.")
        if ch == 4 and c["ext_clk"]:
            lines.append("<span style='color:#d98200'>OUT4 is NOT locked to the external CLK IN: its gate can drift against a laser "
                         f"that is locked to that clock by up to ≈ one internal period ({s_fmt_ns(self.t_ref_ch(4))}). "
                         "Prefer OUT0-3 / 5-7 for a clock-locked laser.</span>")
        unc = self.delay_step(ch) / 2 + self.trig_uncertainty(ch)
        lines.append(f"Edge-placement uncertainty ≈ ±{s_fmt_ns(unc)}"
                     + (f" (incl. SYNC IN sampling by the {s_fmt_ns(self.t_ref_ch(ch))} reference clock)" if c["f_sync"] else "")
                     + f" vs laser pulse FWHM {s_fmt_ns(self.lfw_value())}.")
        if c["mode"] == "One shot trigger":
            lines.append("One-shot trigger: only the first gate is physical; software trigger timing is asynchronous to the laser.")
        return "<br>".join(lines)

    def lfw_value(self):
        return self.planner.lfw.value() if hasattr(self, "planner") else 10.0

    def realized_width(self, ch, pw):
        f = self.f_sys_ch(ch)
        key = (ch, round(pw, 6), f)
        if key in self._width_cache:
            return self._width_cache[key]
        val = None
        ops = getattr(self.pw, "operations", None)
        if ops is not None and getattr(self.pw, "connection_state", False):
            try:
                _seq, actual = ops.build_post_delay_channel(ch, pw * 1e-9, f)
                val = actual * 1e9
            except Exception:
                val = None
        if val is None:
            tick = 1e9 / f
            val = max(MIN_WIDTH_NS, round(pw / tick) * tick)
        self._width_cache[key] = val
        return val

    def gate_edges(self, ch):
        """Edges as the Pockels driver sees them (TG10 edges + trigger-cable delay; 2-input: X2 rising closes)."""
        s = self.setup
        if s.ck_link.isChecked() and ch == s.a():
            rA, fA = self.edges(s.a())
            if s.mode() == 1:
                return rA + s.cab1, fA + s.cab1
            rB, _f = self.edges(s.b())
            return rA + s.cab1, rB + s.cab2
        return self.edges(ch)

    def apply_gate_suggestion(self, ch, rise, width):
        s = self.setup
        if s.ck_link.isChecked() and ch == s.a():
            self.rows[s.a()]["del"].setValue(max(0.025, rise - s.cab1))
            if s.mode() == 1:
                self.rows[s.a()]["pw"].setValue(max(100.0, width - self.sync_gap(s.a())))
            else:
                self.rows[s.b()]["del"].setValue(max(0.025, rise + max(100.0, width) - s.cab2))
                for c in (s.a(), s.b()):
                    if self.rows[c]["pw"].value() < 20:
                        self.rows[c]["pw"].setValue(50.0)
        else:
            self.rows[ch]["del"].setValue(max(0.025, rise))
            self.rows[ch]["pw"].setValue(max(MIN_WIDTH_NS, width - self.sync_gap(ch)))

    def edges(self, ch):
        step = self.delay_step(ch)
        r = round(self.rows[ch]["del"].value() / step) * step
        return r, r + self.realized_width(ch, self.rows[ch]["pw"].value()) + self.sync_gap(ch)

    # --- sync with main window ---
    def load_from_main(self):
        try:
            dd = getattr(self.pw, "delay_dialog", None)
            if dd is None:
                dd = DelayDialog(self.pw)
                self.pw.delay_dialog = dd
            self._read_ctx()
            u = DelayDialog.UNIT_TO_SECONDS
            self._busy = True
            for i in range(8):
                self.rows[i]["del"].setValue(dd.delay_fields[i].value() * u[dd.delay_units[i].currentText()] * 1e9)
                self.rows[i]["pw"].setValue(max(MIN_WIDTH_NS, dd.post_delay_fields[i].value() * u[dd.post_delay_units[i].currentText()] * 1e9))
            self._busy = False
            per = getattr(self.pw, "current_period_s", None)
            if per:
                self.sp_period.setValue(per * 1e9)
        except Exception as e:
            self._busy = False
            QMessageBox.warning(self, "Load", f"Could not read Delay presets: {e}")
        self.refresh()

    def push_to_main(self):
        try:
            dd = getattr(self.pw, "delay_dialog", None)
            if dd is None:
                dd = DelayDialog(self.pw)
                self.pw.delay_dialog = dd
            for i in range(8):
                for fld, unit, val in ((dd.delay_fields[i], dd.delay_units[i], self.rows[i]["del"].value()),
                                       (dd.post_delay_fields[i], dd.post_delay_units[i], self.rows[i]["pw"].value())):
                    unit.setCurrentText("ns")
                    fld.setValue(val)
            QMessageBox.information(self, "Delay presets", "Values copied into the Delay-presets dialog.\n"
                                    "Open it and press Apply to program the TG10.")
        except Exception as e:
            QMessageBox.warning(self, "Send", f"Could not write Delay presets: {e}")

    # --- interaction ---
    def set_sel(self, i):
        self.sel = i
        self.planner._load_ui()
        self.refresh()

    def _period_changed(self, v):
        self.prog_period = v
        self.refresh()

    def _main_signature(self):
        dd = getattr(self.pw, "delay_dialog", None)
        vals = ()
        if dd is not None:
            vals = tuple((dd.delay_fields[i].value(), dd.delay_units[i].currentText(),
                          dd.post_delay_fields[i].value(), dd.post_delay_units[i].currentText()) for i in range(8))
        c = self.pw.sync_context() if self.ck_follow.isChecked() else {}
        return (tuple(sorted((k, v) for k, v in c.items())), getattr(self.pw, "current_period_s", None), vals)

    def _poll_main(self):
        if not self.isVisible():
            return
        try:
            sig = self._main_signature()
        except Exception:
            return
        if self._sig is None:
            self._sig = sig
        elif sig != self._sig:
            self._sig = sig
            self.load_from_main()

    def _view_edit(self, *_):
        if self._busy:
            return
        self.ns_per_div, self.center = self.sp_div.value(), self.sp_center.value()
        self.scope.update()

    def _scope_moved(self):
        self._busy = True
        self.sp_div.setValue(self.ns_per_div)
        self.sp_center.setValue(self.center)
        self._busy = False
        self._refresh_cursors()

    def _set_view(self, c, npd):
        self.center, self.ns_per_div = c, max(0.05, npd)
        self._scope_moved()
        self.scope.update()

    def _autoset(self):
        if self.oneshot:
            ext = max([self.edges(i)[1] for i in range(8) if self.rows[i]["show"].isChecked()] + [100.0])
            self._set_view(ext * 0.5, ext * 1.3 / 10)
        else:
            self._set_view(self.period * 0.5, self.period * 1.1 / 10)

    def _zoom_rise(self):
        rE, fE = self.edges(self.sel)
        self._set_view(rE, max(fE - rE, 1) * 0.4 / 10 * 2)

    def _zoom_fall(self):
        rE, fE = self.edges(self.sel)
        self._set_view(fE, max(fE - rE, 1) * 0.4 / 10 * 2)

    def _cur_width(self):
        self.cursor1, self.cursor2 = self.edges(self.sel)
        self._refresh_cursors()
        self.scope.update()

    def _cur_period(self):
        self.cursor1, self.cursor2 = 0.0, (self.edges(self.sel)[1] if self.oneshot else self.period)
        self._refresh_cursors()
        self.scope.update()

    def showEvent(self, e):
        super().showEvent(e)
        self.load_from_main()

    # --- refresh ---
    def _refresh_cursors(self):
        dx = self.cursor2 - self.cursor1
        self.lbl_cur.setText(f"<span style='color:#1b9ad1'><b>X1</b> {s_fmt_ns(self.cursor1)}</span> &nbsp; "
                             f"<span style='color:#c2368f'><b>X2</b> {s_fmt_ns(self.cursor2)}</span> &nbsp; "
                             f"<b>ΔX</b> {s_fmt_ns(dx)} &nbsp; <b>1/ΔX</b> {s_fmt_freq(abs(1e9/dx)) if dx else '—'}")

    def refresh(self, *_):
        if self._busy or not self._ready:
            return
        self.period = self.realize_period()
        for i in range(8):
            rE, fE = self.edges(i)
            self.rows[i]["rr"].setText(s_fmt_ns(rE))
            self.rows[i]["rf"].setText(s_fmt_ns(fE))
            self.rows[i]["name"].setStyleSheet(f"font-weight:700; color:{SIM_COLORS[i]};" +
                                               ("border:2px solid #0878c9;" if i == self.sel else ""))
        c = self.ctx
        mode_txt = c["mode"] + (f" ({c['src']})" if c["src"] not in ("internal", "one-shot") else "")
        if c["f_sync"]:
            mode_txt += f" · SYNC IN {s_fmt_freq(c['f_sync'])} (rate div {round(self.period*c['f_sync']*1e-9)})"
        if not self.ck_follow.isChecked():
            mode_txt = "WHAT-IF (not the main window) · " + mode_txt
        backend = "TG10 backend" if (getattr(self.pw, "operations", None) is not None and getattr(self.pw, "connection_state", False)) else "model (1/f_sys)"
        self.lbl_info.setText(f"<b>{mode_txt}</b> · f_ref {s_fmt_freq(c['f_ref'])} → f_sys {s_fmt_freq(self.f_sys)} · "
                              f"DEL4 on internal {s_fmt_freq(c['f_sys_int'])} · output {self.rate_txt()} "
                              f"(T = {self.period_txt()}) · widths: {backend}")
        self._refresh_cursors()
        self._refresh_math()
        self.scope.update()
        cur = self.tabs.currentWidget()
        if hasattr(self, "setup"):
            self.setup.refresh()
        if cur is self.planner:
            self.planner.refresh()
        elif cur is self.quantum:
            self.quantum.refresh()
        elif cur is getattr(self, "ov", None):
            self.planner.refresh()
            self._refresh_overview()

    def sync_effects_html(self):
        c = self.ctx
        Tr = 1e9 / c["f_ref"]
        steps = (f"DEL step: OUT0-3 {s_fmt_ns(self.delay_step(0))}, OUT5-7 {s_fmt_ns(self.delay_step(5))}, "
                 f"OUT4 (internal clock) {s_fmt_ns(self.delay_step(4))}; width step {s_fmt_ns(self.width_res(0))}.")
        h = [f"<b style='color:#0b4778'>SYNC MODE: {c['mode']}" + (f" · {c['src']}" if c['src'] not in ('internal', 'one-shot') else "") + "</b>"]
        if c["mode"] == "Internal":
            h.append(f"The TG10 runs from its internal 100 MHz reference (×{c['ndiv']} → f_sys {s_fmt_freq(c['f_sys'])}). "
                     f"Output period = N × {s_fmt_ns(Tr)}: programmed {s_fmt_ns(self.prog_period)} → realized <b>{s_fmt_ns(self.period)}</b>. "
                     "Triggers are generated internally, so there is no external edge to sample.")
        elif c["mode"] == "External SINGLE IN" and c["src"] == "CLK IN":
            h.append(f"CLK IN {s_fmt_freq(c['f_ref'])} replaces the internal reference (valid 20-100 MHz) → f_sys {s_fmt_freq(c['f_sys'])}. "
                     f"Output period is a whole number of CLK IN cycles of {s_fmt_ns(Tr)}: programmed {s_fmt_ns(self.prog_period)} → "
                     f"realized <b>{s_fmt_ns(self.period)}</b>. Fall edges carry the fall-path sync gap "
                     f"({self.sp_sync.value()} × {s_fmt_ns(Tr)}). OUT4 stays on the internal clock and is not locked to CLK IN.")
        elif c["mode"] == "External SINGLE IN":
            Ts = 1e9 / c["f_sync"]
            nd = max(1, round(self.prog_period / Ts))
            dP = self.period - self.prog_period
            h.append(f"SYNC IN {s_fmt_freq(c['f_sync'])} (valid 0.01 Hz-20 MHz, period {s_fmt_ns(Ts)}) is the trigger source; the clock stays "
                     f"internal 100 MHz (f_sys {s_fmt_freq(c['f_sys'])}). Rate divider = <b>{nd}</b>: {'every SYNC IN edge' if nd == 1 else 'every ' + str(nd) + 'th SYNC IN edge'} triggers the outputs → "
                     f"realized period <b>{s_fmt_ns(self.period)}</b> ({s_fmt_freq(1e9/self.period)}).")
            if abs(dP) > 1e-6:
                h.append(f"<span style='color:#d98200'>Programmed period {s_fmt_ns(self.prog_period)} is not a multiple of the SYNC IN period"
                         + (" (it is shorter than one SYNC IN period; the rate divider cannot go below 1)" if self.prog_period < Ts else "")
                         + f": realized differs by {s_fmt_ns(dP)}.</span>")
            h.append(f"Each SYNC IN edge is sampled by the {s_fmt_ns(Tr)} reference clock → trigger placement uncertainty up to ±{s_fmt_ns(Tr)} "
                     "(relative to the SYNC IN edge).")
        elif c["mode"] == "External DUAL IN":
            Ts = 1e9 / c["f_sync"]
            nd = max(1, round(self.prog_period / Ts))
            dP = self.period - self.prog_period
            h.append(f"DUAL IN: CLK IN {s_fmt_freq(c['f_ref'])} is the reference (valid 10-100 MHz → f_sys {s_fmt_freq(c['f_sys'])}) and "
                     f"SYNC IN {s_fmt_freq(c['f_sync'])} is the trigger. Rate divider = <b>{nd}</b> → realized period "
                     f"<b>{s_fmt_ns(self.period)}</b> ({s_fmt_freq(1e9/self.period)}).")
            if abs(dP) > 1e-6:
                h.append(f"<span style='color:#d98200'>Programmed period {s_fmt_ns(self.prog_period)} is not a multiple of the SYNC IN period: "
                         f"realized differs by {s_fmt_ns(dP)}.</span>")
            h.append(f"SYNC IN is sampled by the {s_fmt_ns(Tr)} CLK IN cycle → placement uncertainty up to ±{s_fmt_ns(Tr)}; both inputs together "
                     "keep the outputs locked to your laser clock and its pulse-selection trigger. Fall edges carry the sync gap "
                     f"({self.sp_sync.value()} × {s_fmt_ns(Tr)}).")
        else:
            kind = "Software" if c.get("kind") != "smart" else "Smart"
            h.append(f"{kind} one-shot: each trigger event produces one set of output pulses (no repetition, only the first gate is drawn). "
                     "The event is asynchronous to your laser unless the laser itself is fired from a TG10 output. "
                     + ("Smart trigger arming/behaviour: see the TG10 manual." if kind == "Smart" else ""))
        h.append(steps)
        return "<br>".join(h)

    def _refresh_math(self):
        ch = self.sel
        rE, fE = self.edges(ch)
        P, tau = self.period, fE - rE
        pd, pw = self.rows[ch]["del"].value(), self.rows[ch]["pw"].value()
        res = self.delay_step(ch)
        txt = f"<b style='color:#0b4778'>RELATIONS FOR OUT{ch}</b><br>"
        if self.oneshot:
            txt += "One-shot trigger: one gate per trigger event (no repetition).<br>"
        else:
            nloop = P * 1e-9 * self.f_sys_ch(ch)
            txt += (f"f = 1/T = 1/{s_fmt_ns(P)} = <b>{s_fmt_freq(1e9/P)}</b> &nbsp;|&nbsp; T = {nloop:.0f} system-clock cycles<br>")
        txt += (f"Rise: DEL{ch} = {s_fmt_ns(pd)} → realized <b>{s_fmt_ns(rE)}</b> (step {s_fmt_ns(res)}, error {s_fmt_ns(rE-pd)})<br>"
                f"Width τ: programmed {s_fmt_ns(pw)} → realized <b>{s_fmt_ns(tau)}</b>"
                + (f" (incl. {s_fmt_ns(self.sync_gap(ch))} sync gap)" if self.sync_gap(ch) else "")
                + f" &nbsp;|&nbsp; Fall = DEL + τ = <b>{s_fmt_ns(fE)}</b>")
        if not self.oneshot:
            txt += (f"<br>Duty D = τ/T × 100 % = <b>{tau/P*100:.4f} %</b> &nbsp;|&nbsp; "
                    + ("<span style='color:#d83b3b'>Fall exceeds period: pulse overlaps the next trigger</span>" if fE > P else "pulse fits inside one period"))
        self.lbl_math.setText(txt)
        self.lbl_sync.setText(self.sync_effects_html())

    def _refresh_overview(self):
        pl = self.planner
        for ch in range(8):
            rE, fE = self.edges(ch)
            en = pl.params[ch]["en"] or bool(self.setup.link_params(ch))
            r = pl.res[ch] if en else None
            if r is None and en:
                r = pl.analyze(ch)
                pl.res[ch] = r
            vals = [f"OUT{ch}", s_fmt_ns(rE), s_fmt_ns(fE), s_fmt_ns(fE - rE),
                    (self.setup.cb_cell.currentText().split(",")[0] + " via DPB1" if self.setup.link_params(ch)
                     else pl.params[ch]["cell"].split(",")[0]) if r else "—",
                    s_fmt_ns(r["t_open"]) if r and r["t_open"] is not None else "—",
                    s_fmt_ns(r["t_close"]) if r and r["t_close"] is not None else "—",
                    str(sum(1 for p in r["pulses"] if p[1] > 0.5)) if r else "—",
                    pockels_verdict(r)[0] if r else "no cell attached"]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c == 8 and r:
                    it.setForeground(QColor(pockels_verdict(r)[1]))
                self.tbl.setItem(ch, c, it)


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