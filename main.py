"""
TG10 TIMING GENERATOR - C-DAC
PySide6 dashboard GUI

Run:
    python main.py

Requirement:
    pip install PySide6
"""

import sys
import os
from PySide6.QtCore import Qt, QPointF, QRectF
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


# ============================================================
# COLORS
# ============================================================

NAVY = "#0b3b66"
BLUE = "#1976b9"
DEEP = "#124a7c"
GREEN = "#159447"
RED = "#d83232"
LINE = "#ccd8e3"
PAGE = "#edf2f7"
TEXT = "#23384d"
GREY = "#60758a"


# ============================================================
# STYLE
# ============================================================

STYLE = f"""
* {{
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
    color: {TEXT};
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
    font-size: 12px;
    font-weight: 700;
}}

QLabel#LogoLo {{
    color: #d32929;
    font-size: 20px;
    font-weight: 800;
}}

QLabel#AppTitle {{
    color: {DEEP};
    font-size: 25px;
    font-weight: 700;
}}

QLabel#AppSub {{
    color: {GREY};
    font-size: 12px;
}}

QLabel#StatusPill {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 3px;
    color: {RED};
    font-weight: 600;
    padding: 8px 12px;
}}

QPushButton#HdrBtn {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 3px;
    color: #23394f;
    font-weight: 600;
    min-height: 40px;
    padding: 5px 20px;
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
    font-weight: 700;
    min-height: 40px;
    padding: 5px 22px;
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
    min-height: 34px;
    padding: 4px 14px;
}}

QPushButton#Tab:hover {{
    background: #edf5fb;
}}

QPushButton#Tab:checked {{
    background: {BLUE};
    border-color: {BLUE};
    color: white;
    font-weight: 600;
}}

QFrame#Card {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 4px;
}}

QLabel#CardIcon {{
    color: {BLUE};
    font-size: 16px;
}}

QLabel#CardTitle {{
    color: {DEEP};
    font-size: 15px;
    font-weight: 700;
}}

QToolButton#Chevron {{
    background: transparent;
    border: none;
    color: {GREY};
    font-size: 14px;
}}

QFrame#SubPanel {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 3px;
}}

QLabel#SubHeader {{
    background: {BLUE};
    color: white;
    font-weight: 600;
    padding: 7px 10px;
}}

QLabel#FieldLabel {{
    color: #334b61;
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
}}

QComboBox,
QLineEdit,
QSpinBox,
QDoubleSpinBox {{
    background: white;
    border: 1px solid #bdcad6;
    border-radius: 2px;
    min-height: 27px;
    padding: 2px 6px;
}}

QComboBox:hover,
QLineEdit:hover,
QSpinBox:hover,
QDoubleSpinBox:hover {{
    border-color: {BLUE};
}}

QComboBox::drop-down {{
    width: 20px;
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
    spacing: 6px;
}}

QRadioButton::indicator,
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
}}

QRadioButton::indicator {{
    border: 1px solid #98aabd;
    border-radius: 7px;
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
    min-height: 33px;
    padding: 4px 8px;
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
    font-size: 10px;
}}

QLabel#TileValue {{
    color: #17324d;
    font-size: 12px;
    font-weight: 700;
}}

QTableWidget {{
    background: white;
    border: 1px solid {LINE};
    gridline-color: #dfe7ee;
    outline: none;
}}

QTableWidget::item {{
    padding: 3px;
}}

QHeaderView::section {{
    background: #f2f6fa;
    color: {DEEP};
    font-weight: 700;
    border: none;
    border-right: 1px solid #dfe7ee;
    border-bottom: 1px solid {LINE};
    padding: 5px 3px;
}}

QLabel#LiveHeader {{
    background: #f3f7fa;
    border: 1px solid {LINE};
    color: {DEEP};
    font-weight: 700;
    padding: 6px 8px;
}}

QLabel#LiveBody {{
    background: white;
    border: 1px solid {LINE};
    color: {GREY};
    padding: 8px;
}}

QPushButton#SmallBtn {{
    background: white;
    border: 1px solid {LINE};
    border-radius: 2px;
    min-height: 29px;
    padding: 4px 12px;
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
    color: {BLUE};
}}

QLabel#StatusRight {{
    font-weight: 600;
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

        form.addRow(
            "COM Port:",
            combo(
                ["COM1", "COM2", "COM3", "COM4",
                 "COM5", "COM6", "COM7"]
            )
        )

        form.addRow(
            "COM BPS:",
            combo(["9600", "115200", "1 Mbps", "2 Mbps"])
        )

        form.addRow(
            "CAN Mode:",
            combo(["Normal", "Loopback"])
        )

        form.addRow(
            "Frame:",
            combo(["Standard Frame", "Extended Frame"])
        )

        form.addRow(
            "CAN BPS:",
            combo(["125 kbps", "250 kbps",
                   "500 kbps", "1 Mbps"])
        )

        layout.addWidget(group)

        layout.addWidget(
            label(
                "PC → USB-CAN → CAN → TG10",
                "InfoBox"
            )
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Close
        )

        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)


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
            a.setRange(0, 150000)
            a.setDecimals(3)
            a.setSuffix(" ns")

            b = QDoubleSpinBox()
            b.setRange(0, 150000)
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

        pages.append(page1)

        # ----------------------------------------------------
        # POST DELAY
        # ----------------------------------------------------

        page2 = QWidget()

        grid2 = QGridLayout(page2)

        for i in range(8):

            value = QDoubleSpinBox()
            value.setRange(0, 150000)
            value.setDecimals(3)
            value.setSuffix(" ns")

            grid2.addWidget(
                label(f"post DEL{i}", "FieldLabel"),
                i, 0
            )
            grid2.addWidget(value, i, 1)

        pages.append(page2)

        # ----------------------------------------------------
        # RELATIONS
        # ----------------------------------------------------

        page3 = QWidget()

        grid3 = QGridLayout(page3)

        headers = [
            "Output",
            "C1 Rise",
            "C1 Fall",
            "C2 Rise",
            "C2 Fall"
        ]

        for c, text in enumerate(headers):
            grid3.addWidget(
                label(text, "FieldLabel", True),
                0, c
            )

        for r in range(8):

            grid3.addWidget(
                label(f"OUT{r}", "FieldLabel"),
                r + 1, 0
            )

            for c in range(1, 5):
                grid3.addWidget(
                    combo(
                        [f"DEL{i}" for i in range(8)],
                        82
                    ),
                    r + 1,
                    c
                )

        pages.append(page3)

        names = [
            "Delay presets",
            "Post-delay",
            "Delay relations"
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

        self.setMinimumSize(1280, 760)
        self.resize(1600, 920)

        self.running = False

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

        w.setMinimumHeight(76)
        w.setMaximumHeight(76)

        h = QHBoxLayout(w)
        h.setContentsMargins(12, 6, 12, 6)
        h.setSpacing(12)

        # Logo
        # C-DAC Logo
        logo = QLabel()
        logo.setFixedSize(120, 58)
        logo.setAlignment(Qt.AlignCenter)

        logo_path = os.path.join(
            os.path.dirname(__file__),
            "cdac_logo.png"
        )

        pixmap = QPixmap(logo_path)

        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    120,
                    58,
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

        self.connection.setFixedWidth(145)

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

        w.setMinimumHeight(45)
        w.setMaximumHeight(45)

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

        grid.setContentsMargins(
            12, 9, 12, 8
        )

        grid.setHorizontalSpacing(9)
        grid.setVerticalSpacing(9)

        sync = self.sync_card()
        config = self.config_card()
        monitor = self.monitor_card()

        freq = self.frequency_card()
        output = self.output_card()

        other = self.other_card()

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
        # TOP
        # ----------------------------------------------------

        grid.addWidget(
            sync,
            0, 0, 1, 2
        )

        grid.addWidget(
            config,
            0, 2
        )

        grid.addWidget(
            monitor,
            0, 3, 2, 1
        )

        # ----------------------------------------------------
        # MIDDLE
        # ----------------------------------------------------

        grid.addWidget(
            freq,
            1, 0
        )

        grid.addWidget(
            output,
            1, 1, 1, 2
        )

        # ----------------------------------------------------
        # BOTTOM
        # ----------------------------------------------------

        grid.addWidget(
            other,
            2, 0, 1, 4
        )

        # Column proportions
        grid.setColumnStretch(0, 29)
        grid.setColumnStretch(1, 17)
        grid.setColumnStretch(2, 22)
        grid.setColumnStretch(3, 32)

        # Important:
        # minimum heights prevent controls from overlapping.
        grid.setRowMinimumHeight(0, 365)
        grid.setRowMinimumHeight(1, 185)
        grid.setRowMinimumHeight(2, 100)

        grid.setRowStretch(0, 38)
        grid.setRowStretch(1, 22)
        grid.setRowStretch(2, 10)

        return page

    # ========================================================
    # SYNC
    # ========================================================

    def sync_card(self):

        frame, body = make_card(
            "∿",
            "Synchronization (Sync)"
        )

        # ============================================================
        # MAIN SYNC AREA
        # LEFT = Internal + One Shot
        # RIGHT = External (Single / Dual)
        # ============================================================

        main_row = QHBoxLayout()
        main_row.setSpacing(10)
        main_row.setContentsMargins(0, 0, 0, 0)

        # ============================================================
        # LEFT COLUMN
        # Internal
        # One Shot
        # ============================================================

        left_column = QVBoxLayout()
        left_column.setSpacing(10)
        left_column.setContentsMargins(0, 0, 0, 0)

        # ------------------------------------------------------------
        # INTERNAL
        # ------------------------------------------------------------

        internal, il = make_subpanel("Internal")

        self.internal_radio = QRadioButton(
            "Internal clock"
        )
        self.internal_radio.setChecked(True)

        il.addWidget(
            self.internal_radio
        )

        '''il.addWidget(
            label(
                "Reference frequency",
                "FieldLabel"
            )
        )'''

        freq_row = QHBoxLayout()
        freq_row.setSpacing(5)

        self.internal_freq = QDoubleSpinBox()
        self.internal_freq.setRange(
            0.001,
            1000
        )
        self.internal_freq.setDecimals(3)
        self.internal_freq.setValue(
            100.000
        )

        freq_row.addWidget(
            self.internal_freq,
            1
        )

        freq_row.addWidget(
            combo(
                ["MHz", "kHz", "Hz"],
                68
            )
        )

        il.addLayout(
            freq_row
        )

        left_column.addWidget(
            internal,
            1
        )

        # ------------------------------------------------------------
        # ONE SHOT TRIGGER
        # ------------------------------------------------------------

        one_shot, osl = make_subpanel(
            "One shot trigger"
        )

        trigger_row = QHBoxLayout()
        trigger_row.setSpacing(15)

        self.one_shot_group = QButtonGroup(
            one_shot
        )

        self.software_trigger = QRadioButton(
            "Software trigger"
        )

        self.smart_trigger = QRadioButton(
            "Smart trigger"
        )

        self.software_trigger.setChecked(
            True
        )

        self.one_shot_group.addButton(
            self.software_trigger
        )

        self.one_shot_group.addButton(
            self.smart_trigger
        )

        trigger_row.addWidget(
            self.software_trigger
        )

        trigger_row.addWidget(
            self.smart_trigger
        )

        trigger_row.addStretch()

        osl.addLayout(
            trigger_row
        )

        left_column.addWidget(
            one_shot,
            1
        )

        # ============================================================
        # RIGHT COLUMN
        # External Single / Dual
        # ============================================================

        external, el = make_subpanel(
            "External (Single / Dual)"
        )

        external_row = QHBoxLayout()
        external_row.setSpacing(12)
        external_row.setContentsMargins(
            0, 0, 0, 0
        )

        # ------------------------------------------------------------
        # SINGLE
        # ------------------------------------------------------------

        single = QVBoxLayout()
        single.setSpacing(5)

        self.single_radio = QRadioButton(
            "External SINGLE IN"
        )

        single.addWidget(
            self.single_radio
        )

        single.addWidget(
            label(
                "Input source",
                "FieldLabel"
            )
        )

        self.single_source = combo(
            [
                "CLK IN",
                "SYNC IN"
            ]
        )

        single.addWidget(
            self.single_source
        )

        single.addWidget(
            label(
                "Input frequency / rate",
                "FieldLabel"
            )
        )

        rate_row = QHBoxLayout()
        rate_row.setSpacing(5)

        self.external_rate = QDoubleSpinBox()
        self.external_rate.setRange(
            0.01,
            20000
        )
        self.external_rate.setDecimals(3)
        self.external_rate.setValue(
            100.000
        )

        rate_row.addWidget(
            self.external_rate,
            1
        )

        rate_row.addWidget(
            combo(
                ["MHz", "kHz", "Hz"],
                65
            )
        )

        single.addLayout(
            rate_row
        )

        external_row.addLayout(
            single,
            1
        )

        # ------------------------------------------------------------
        # DUAL
        # ------------------------------------------------------------

        dual = QVBoxLayout()
        dual.setSpacing(5)

        self.dual_radio = QRadioButton(
            "External DUAL IN"
        )

        dual.addWidget(
            self.dual_radio
        )

        dual.addWidget(
            label(
                "SYNC input",
                "FieldLabel"
            )
        )

        self.dual_sync_input = combo(
            [
                "SYNC IN",
                "CLK IN"
            ]
        )

        dual.addWidget(
            self.dual_sync_input
        )

        dual.addWidget(
            label(
                "CLK input",
                "FieldLabel"
            )
        )

        self.dual_clk_input = combo(
            [
                "CLK IN",
                "SYNC IN"
            ]
        )

        dual.addWidget(
            self.dual_clk_input
        )

        external_row.addLayout(
            dual,
            1
        )

        el.addLayout(
            external_row
        )

        # ============================================================
        # PUT LEFT + RIGHT TOGETHER
        # ============================================================

        main_row.addLayout(
            left_column,
            1
        )

        main_row.addWidget(
            external,
            2
        )

        body.addLayout(
            main_row
        )

        return frame

    # ========================================================
    # FREQUENCY
    # ========================================================

    def frequency_card(self):

        frame, body = make_card(
            "∿",
            "Frequency / Period (Freq)"
        )

        selector = QHBoxLayout()
        selector.setSpacing(18)

        frequency = QRadioButton(
            "Frequency"
        )

        frequency.setChecked(True)

        period = QRadioButton(
            "Period"
        )

        selector.addWidget(
            frequency
        )

        selector.addWidget(
            period
        )

        selector.addStretch()

        body.addLayout(selector)

        grid = QGridLayout()

        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(6)

        grid.addWidget(
            label(
                "Frequency:",
                "FieldLabel"
            ),
            0, 0
        )

        grid.addWidget(
            QLineEdit("1.000000"),
            0, 1
        )

        grid.addWidget(
            combo(
                ["MHz", "kHz", "Hz"],
                78
            ),
            0, 2
        )

        grid.addWidget(
            label(
                "Period:",
                "FieldLabel"
            ),
            1, 0
        )

        grid.addWidget(
            QLineEdit("1.000000"),
            1, 1
        )

        grid.addWidget(
            combo(
                ["µs", "ns", "ms", "s"],
                78
            ),
            1, 2
        )

        grid.setColumnStretch(1, 1)

        body.addLayout(grid)

        body.addWidget(
            label(
                "Range: 0.01 Hz – 20 MHz   |   "
                "Period: 50 ns – 100 s",
                "InfoBox"
            )
        )

        return frame

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def config_card(self):

        frame, body = make_card(
            "⚙",
            "Configuration 1 / 2"
        )

        tabs = QHBoxLayout()
        tabs.setSpacing(6)

        group = QButtonGroup(frame)
        group.setExclusive(True)

        c1 = QPushButton(
            "Config 1"
        )

        c2 = QPushButton(
            "Config 2"
        )

        for i, button in enumerate(
            [c1, c2]
        ):

            button.setObjectName(
                "Seg"
            )

            button.setCheckable(
                True
            )

            button.setChecked(
                i == 0
            )

            group.addButton(
                button,
                i
            )

            tabs.addWidget(
                button,
                1
            )

        body.addLayout(tabs)

        grid = QGridLayout()

        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        # Mode
        grid.addWidget(
            label(
                "Mode",
                "FieldLabel"
            ),
            0, 0
        )

        mode = combo(
            [
                "Normal",
                "Gate",
                "Burst",
                "Frequency divider"
            ]
        )

        grid.addWidget(
            mode,
            0, 1
        )

        # Gate
        grid.addWidget(
            label(
                "Gate",
                "FieldLabel"
            ),
            1, 0
        )

        gate = combo(
            ["GATE", "nGATE"]
        )

        grid.addWidget(
            gate,
            1, 1
        )

        # Burst
        grid.addWidget(
            label(
                "Burst",
                "FieldLabel"
            ),
            2, 0
        )

        burst = combo(
            [
                "SYNC IN",
                "GATE",
                "nGATE",
                "Software"
            ]
        )

        grid.addWidget(
            burst,
            2, 1
        )

        # Burst count
        grid.addWidget(
            label(
                "Burst count",
                "FieldLabel"
            ),
            3, 0
        )

        burst_count = QSpinBox()

        burst_count.setRange(
            1,
            65535
        )

        burst_count.setValue(
            1
        )

        grid.addWidget(
            burst_count,
            3, 1
        )

        # Divider
        grid.addWidget(
            label(
                "Frequency divider",
                "FieldLabel"
            ),
            4, 0
        )

        divider = QSpinBox()

        divider.setRange(
            1,
            32767
        )

        divider.setValue(
            1
        )

        grid.addWidget(
            divider,
            4, 1
        )

        grid.setColumnStretch(
            1,
            1
        )

        body.addLayout(grid)

        return frame

    # ========================================================
    # OUTPUT
    # ========================================================

    def output_card(self):

        frame, body = make_card(
            "▣",
            "Output"
        )

        grid = QGridLayout()

        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(5)

        # Row 1
        grid.addWidget(
            label(
                "Channel:",
                "FieldLabel"
            ),
            0, 0
        )

        grid.addWidget(
            combo(
                [f"OUT{i}" for i in range(8)],
                82
            ),
            0, 1
        )

        enable = QCheckBox(
            "Enable"
        )

        enable.setChecked(True)

        grid.addWidget(
            enable,
            0, 2
        )

        grid.addWidget(
            label(
                "C1 Rise:",
                "FieldLabel"
            ),
            0, 3
        )

        grid.addWidget(
            combo(
                [f"DEL{i}" for i in range(8)],
                76
            ),
            0, 4
        )

        grid.addWidget(
            label(
                "C2 Rise:",
                "FieldLabel"
            ),
            0, 5
        )

        c2rise = combo(
            [f"DEL{i}" for i in range(8)],
            76
        )

        c2rise.setCurrentText(
            "DEL1"
        )

        grid.addWidget(
            c2rise,
            0, 6
        )

        # Row 2
        grid.addWidget(
            label(
                "Logic:",
                "FieldLabel"
            ),
            1, 0
        )

        grid.addWidget(
            combo(
                ["OR", "AND", "NOT"],
                82
            ),
            1, 1
        )

        grid.addWidget(
            label(
                "C1 Fall:",
                "FieldLabel"
            ),
            1, 3
        )

        c1fall = combo(
            [f"DEL{i}" for i in range(8)],
            76
        )

        c1fall.setCurrentText(
            "DEL2"
        )

        grid.addWidget(
            c1fall,
            1, 4
        )

        grid.addWidget(
            label(
                "C2 Fall:",
                "FieldLabel"
            ),
            1, 5
        )

        c2fall = combo(
            [f"DEL{i}" for i in range(8)],
            76
        )

        c2fall.setCurrentText(
            "DEL3"
        )

        grid.addWidget(
            c2fall,
            1, 6
        )

        grid.setColumnStretch(
            2,
            1
        )

        body.addLayout(grid)

        title = QHBoxLayout()

        title.addWidget(
            label(
                "OUT0",
                None,
                bold=True,
                color=DEEP
            )
        )

        title.addWidget(
            label(
                "•  GUI Timing Visualization",
                None,
                bold=True,
                color=DEEP
            )
        )

        title.addStretch()

        body.addLayout(title)

        body.addWidget(
            TimingViz(),
            1
        )

        return frame

    # ========================================================
    # MONITOR
    # ========================================================

    def monitor_card(self):

        frame, body = make_card(
            "▮▮",
            "Monitor",
            collapsible=False
        )

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
                "SmallGrey"
            )
        )

        header.addWidget(
            combo(
                ["100 ms", "250 ms",
                 "500 ms", "1 s"],
                88
            )
        )

        refresh = QToolButton()
        refresh.setObjectName(
            "Chevron"
        )
        refresh.setText("↻")
        refresh.setFixedSize(
            25, 25
        )

        header.addWidget(
            refresh
        )

        # ----------------------------------------------------
        # MONITOR TILES
        # ----------------------------------------------------

        tiles = QGridLayout()

        tiles.setHorizontalSpacing(5)
        tiles.setVerticalSpacing(5)

        values = [
            ("Sync", "Internal", 0, 0, 1),
            ("Freq", "100.000000 MHz", 0, 1, 1),
            ("Period", "10.000 ns", 0, 2, 1),
            ("Config", "1 (Normal)", 0, 3, 1),

            ("Execution", "STOPPED", 1, 0, 1),
            ("Outputs active", "1 / 8", 1, 1, 1),
            ("Device status", "READY", 1, 2, 2)
        ]

        for name, value, r, c, span in values:

            tile = QFrame()
            tile.setObjectName(
                "Tile"
            )

            tv = QVBoxLayout(tile)

            tv.setContentsMargins(
                7, 4, 7, 4
            )

            tv.setSpacing(1)

            tv.addWidget(
                label(
                    name,
                    "TileLabel"
                )
            )

            tv.addWidget(
                label(
                    value,
                    "TileValue"
                )
            )

            tiles.addWidget(
                tile,
                r,
                c,
                1,
                span
            )

        for c in range(4):
            tiles.setColumnStretch(
                c,
                1
            )

        body.addLayout(
            tiles
        )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        body.addWidget(
            self.monitor_table(),
            1
        )

        # ----------------------------------------------------
        # LIVE PARAMETER
        # ----------------------------------------------------

        bottom = QHBoxLayout()

        live = QVBoxLayout()
        live.setSpacing(0)

        live.addWidget(
            label(
                "Live parameter",
                "LiveHeader"
            )
        )

        live.addWidget(
            label(
                "No live data. Connect to device "
                "to view live parameters.",
                "LiveBody"
            ),
            1
        )

        bottom.addLayout(
            live,
            1
        )

        menu = QPushButton(
            "Menu"
        )

        menu.setObjectName(
            "SmallBtn"
        )

        menu.setFixedWidth(
            70
        )

        menu.clicked.connect(
            self.monitor_menu
        )

        bottom.addWidget(
            menu
        )

        body.addLayout(
            bottom
        )

        return frame

    def monitor_table(self):

        headers = [
            "#",
            "Output",
            "C1 Rise",
            "C1 Fall",
            "C2 Rise",
            "C2 Fall",
            "Logic",
            "Status"
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

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.Fixed
        )

        table.setColumnWidth(
            0,
            28
        )

        table.verticalHeader().setDefaultSectionSize(
            24
        )

        for r in range(8):

            data = [
                str(r + 1),
                f"OUT{r}",
                "DEL0",
                "DEL1",
                "DEL2",
                "DEL3",
                "OR"
            ]

            for c, value in enumerate(data):

                item = QTableWidgetItem(
                    value
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                table.setItem(
                    r,
                    c,
                    item
                )

            active = r == 0

            status = QTableWidgetItem(
                "●  ACTIVE"
                if active
                else
                "●  OFF"
            )

            status.setTextAlignment(
                Qt.AlignCenter
            )

            status.setForeground(
                QColor(
                    GREEN
                    if active
                    else RED
                )
            )

            font = status.font()
            font.setBold(True)

            status.setFont(font)

            table.setItem(
                r,
                7,
                status
            )

        return table

    def monitor_menu(self):

        msg = QMessageBox(self)

        msg.setWindowTitle("Monitor")
        msg.setIcon(QMessageBox.Information)

        msg.setStyleSheet("""
            QMessageBox {
                background: white;
                color: #23384d;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QMessageBox QLabel {
                color: #23384d;
                background: white;
            }

            QMessageBox QPushButton {
                background: white;
                color: #23384f;
                border: 1px solid #ccd8e3;
                border-radius: 3px;
                padding: 6px 20px;
                min-width: 55px;
            }

            QMessageBox QPushButton:hover {
                background: #f2f7fb;
                border-color: #1976b9;
            }
        """)

        msg.setText(
            "<b style='color:#124a7c; font-size:14px;'>TG10 Monitor</b>"
        )

        msg.setInformativeText(
            "<span style='color:#334b61; font-size:13px;'>"
            "• Sync<br>"
            "• Frequency<br>"
            "• Output<br>"
            "• Config<br>"
            "• Live parameter"
            "</span>"
        )

        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec()

    # ========================================================
    # OTHER
    # ========================================================

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

            button = QPushButton(name)
            button.setObjectName("Seg")
            button.setCheckable(True)

            if i == 0:
                button.setChecked(True)

            self.other_group.addButton(button, i)
            self.other_buttons.append(button)

            tabs.addWidget(
                button,
                1
            )

        body.addLayout(tabs)

        # ============================================================
        # STACKED CONTENT AREA
        # ============================================================

        self.other_stack = QStackedWidget()

        # ============================================================
        # PAGE 1 — PUSH TRIGGER
        # ============================================================

        push_page = QWidget()

        push_layout = QHBoxLayout(push_page)
        push_layout.setContentsMargins(
            10, 6, 10, 6
        )
        push_layout.setSpacing(12)

        push_layout.addWidget(
            label(
                "Push trigger",
                None,
                bold=True,
                color=DEEP
            )
        )

        self.push_one_shot = QRadioButton(
            "One shot trigger"
        )

        self.push_burst = QRadioButton(
            "Burst trigger"
        )

        self.push_latch_set = QRadioButton(
            "Latch SET"
        )

        self.push_latch_reset = QRadioButton(
            "Latch RESET"
        )

        self.push_one_shot.setChecked(
            True
        )

        push_layout.addWidget(
            self.push_one_shot
        )

        push_layout.addWidget(
            self.push_burst
        )

        push_layout.addWidget(
            self.push_latch_set
        )

        push_layout.addWidget(
            self.push_latch_reset
        )

        push_layout.addStretch()

        separator = QFrame()
        separator.setFrameShape(
            QFrame.VLine
        )

        push_layout.addWidget(
            separator
        )

        push_layout.addWidget(
            label(
                "Trigger",
                None,
                bold=True,
                color=DEEP
            )
        )

        send_button = QPushButton(
            "Send Trigger"
        )

        send_button.setObjectName(
            "SmallBtn"
        )

        send_button.setFixedWidth(
            135
        )

        send_button.clicked.connect(
            lambda:
            self.set_status(
                "Software trigger requested"
            )
        )

        push_layout.addWidget(
            send_button
        )

        self.other_stack.addWidget(
            push_page
        )

        # ============================================================
        # PAGE 2 — FREQUENCY LIMIT
        # ============================================================

        frequency_page = QWidget()

        frequency_layout = QHBoxLayout(
            frequency_page
        )

        frequency_layout.setContentsMargins(
            10, 6, 10, 6
        )

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

        self.frequency_limit_value.setRange(
            0.01,
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

        device_layout = QHBoxLayout(
            device_page
        )

        device_layout.setContentsMargins(
            10, 6, 10, 6
        )

        device_layout.setSpacing(
            9
        )

        device_layout.addWidget(
            label(
                "Device presets",
                None,
                bold=True,
                color=DEEP
            )
        )

        device_layout.addWidget(
            label(
                "Preset:",
                "FieldLabel"
            )
        )

        self.device_preset_combo = combo(
            [
                "Default",
                "Pockels_100ns",
                "External_Sync",
                "Experiment_01"
            ],
            160
        )

        device_layout.addWidget(
            self.device_preset_combo
        )

        load_preset = QPushButton(
            "Load"
        )

        load_preset.setObjectName(
            "SmallBtn"
        )

        load_preset.clicked.connect(
            lambda:
            self.set_status(
                "Device preset loaded"
            )
        )

        device_layout.addWidget(
            load_preset
        )

        save_preset = QPushButton(
            "Save"
        )

        save_preset.setObjectName(
            "SmallBtn"
        )

        save_preset.clicked.connect(
            lambda:
            self.set_status(
                "Device preset saved"
            )
        )

        device_layout.addWidget(
            save_preset
        )

        device_layout.addStretch()

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

        sound_layout.setContentsMargins(
            10, 6, 10, 6
        )

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

        info_layout.setContentsMargins(
            10, 5, 10, 5
        )

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
    # ACTIONS
    # ========================================================

    def open_com(self):

        dialog = COMDialog(
            self
        )

        dialog.exec()

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

            self.set_status(
                "RUN active"
            )

        else:

            self.run_button.setText(
                "▶  RUN"
            )

            self.run_button.setStyleSheet(
                ""
            )

            self.set_status(
                "RUN stopped"
            )

    def set_status(self, text):

        self.status.setText(
            text +
            "   |   Not connected"
        )


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
            9
        )
    )

    window = TG10Window()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()