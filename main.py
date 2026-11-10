"""Wave desktop expense tracker, built with native Python and PySide6."""

from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QLocale, Qt, QDate
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter, QPainterPath, QPen, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from storage import Store


THEMES = {
    "light": {
        "ink": "#26392B", "background": "#F2F6F0", "sidebar": "#E7EEE4", "topbar": "#FBFCFA",
        "border": "#D8E2D5", "muted": "#667764", "title": "#213626", "section": "#304334",
        "hint": "#667764", "eyebrow": "#586D59", "surface": "#FFFFFF", "surface_alt": "#F5F8F3",
        "divider": "#E0E8DD", "rule": "#D6E0D3", "reminder": "#EAF3E8", "reminder_border": "#C8DCC5",
        "reminder_accent": "#4D8050", "button": "#E4ECE1", "button_text": "#405442",
        "button_hover": "#D8E5D5", "focus": "#36784A", "primary": "#2F7048", "primary_text": "#FFFFFF",
        "primary_hover": "#285E3C", "quiet": "#5F735F", "quiet_hover": "#E2EBDF",
        "nav": "#5E715E", "nav_hover": "#DEE8DA", "active_bg": "#D7E7D5", "active_text": "#285F39",
        "small": "#E4ECE1", "small_text": "#405542", "input": "#FFFFFF", "input_border": "#C9D7C6",
        "selection": "#BBD7B8", "popup": "#FFFFFF", "popup_border": "#CEDCCB",
        "progress": "#DDE7D9", "scroll": "#F2F6F0", "scroll_thumb": "#B9C9B5",
        "scroll_hover": "#96AC90", "dialog": "#F5F8F3", "menu": "#FFFFFF", "menu_border": "#D2DED0",
        "menu_selected": "#DFEBDD", "accent": "#2F7048", "positive": "#34764A", "negative": "#B84D40",
        "warning": "#896813", "wave_tile": "#2F7048", "wave_light": "#E7F2E3", "wave_mid": "#B7D6AF",
        "chart_grid": "#E0E8DD", "chart_empty": "#D8E3D5", "chart_zero": "#DDE7D9", "chart_label": "#26392B",
    },
    "dark": {
        "ink": "#E4ECE2", "background": "#121A13", "sidebar": "#18231A", "topbar": "#172119",
        "border": "#314232", "muted": "#A0AE9D", "title": "#F0F4EC", "section": "#E2EAE0",
        "hint": "#A0AE9D", "eyebrow": "#ACB9A8", "surface": "#1C281E", "surface_alt": "#19251B",
        "divider": "#304031", "rule": "#3A4A3A", "reminder": "#203326", "reminder_border": "#3E5B40",
        "reminder_accent": "#82B883", "button": "#29382A", "button_text": "#D6E0D2",
        "button_hover": "#354737", "focus": "#8FC38B", "primary": "#83B783", "primary_text": "#172418",
        "primary_hover": "#98C791", "quiet": "#A5B3A2", "quiet_hover": "#29392B",
        "nav": "#ABB8A8", "nav_hover": "#263629", "active_bg": "#2A402D", "active_text": "#B9DDB3",
        "small": "#29382A", "small_text": "#D4DED1", "input": "#172119", "input_border": "#405240",
        "selection": "#36523A", "popup": "#1C281E", "popup_border": "#405240",
        "progress": "#344535", "scroll": "#121A13", "scroll_thumb": "#536652",
        "scroll_hover": "#6D846A", "dialog": "#19241A", "menu": "#1C281E", "menu_border": "#405240",
        "menu_selected": "#2A402D", "accent": "#83B783", "positive": "#88C991", "negative": "#E38B7C",
        "warning": "#E4C66F", "wave_tile": "#2F7048", "wave_light": "#E7F2E3", "wave_mid": "#B7D6AF",
        "chart_grid": "#344536", "chart_empty": "#405240", "chart_zero": "#344536", "chart_label": "#DCE6D9",
    },
}

ACTIVE_THEME = THEMES["light"]
INK = ACTIVE_THEME["ink"]
BLUE = ACTIVE_THEME["accent"]
MINT = ACTIVE_THEME["positive"]
CORAL = ACTIVE_THEME["negative"]
MUTED = ACTIVE_THEME["muted"]
AMBER = ACTIVE_THEME["warning"]
SURFACE = ACTIVE_THEME["surface"]


STYLESHEET_TEMPLATE = """
* { font-family: 'DejaVu Sans', 'Segoe UI', Arial, sans-serif; color: @INK@; }
QMainWindow, QWidget#appRoot { background: @BACKGROUND@; }
QWidget#sidebar { background: @SIDEBAR@; border-right: 1px solid @BORDER@; }
QWidget#topbar { background: @TOPBAR@; border-bottom: 1px solid @BORDER@; }
QLabel { background: transparent; }
QLabel#muted { color: @MUTED@; }
QLabel#pageTitle { color: @TITLE@; font-size: 27px; font-weight: 650; }
QLabel#sectionTitle { color: @SECTION@; font-size: 16px; font-weight: 620; }
QLabel#metricValue { color: @TITLE@; font-size: 22px; font-weight: 650; }
QLabel#metricHint { color: @HINT@; font-size: 12px; }
QLabel#eyebrow { color: @EYEBROW@; font-size: 12px; }
QFrame#summaryBand { background: @SURFACE@; border: 1px solid @BORDER@; border-radius: 10px; }
QFrame#surfaceQuiet { background: @SURFACE@; border: 1px solid @BORDER@; border-radius: 12px; }
QFrame#sidebarSummary { background: @SURFACE_ALT@; border: 1px solid @BORDER@; border-radius: 10px; }
QFrame#divider { background: @DIVIDER@; border: none; max-height: 1px; }
QFrame#verticalRule { background: @RULE@; border: none; max-width: 1px; }
QFrame#reminderStrip { background: @REMINDER@; border: 1px solid @REMINDER_BORDER@; border-left: 3px solid @REMINDER_ACCENT@; border-radius: 8px; }
QPushButton { border: 0; border-radius: 8px; padding: 8px 11px; background: @BUTTON@; color: @BUTTON_TEXT@; }
QPushButton:hover { background: @BUTTON_HOVER@; color: @INK@; }
QPushButton:focus, QToolButton:focus { border: 1px solid @FOCUS@; }
QPushButton#primaryButton { background-color: @PRIMARY@; color: @PRIMARY_TEXT@; font-weight: 700; padding: 9px 13px; }
QPushButton#primaryButton:hover { background-color: @PRIMARY_HOVER@; }
QPushButton#quietButton { background: transparent; color: @QUIET@; padding: 7px 9px; }
QPushButton#quietButton:hover { background: @QUIET_HOVER@; color: @INK@; }
QToolButton#quietButton { background: transparent; color: @QUIET@; border-radius: 8px; font-size: 20px; }
QToolButton#quietButton:hover { background: @QUIET_HOVER@; color: @INK@; }
QToolButton#dataButton, QToolButton#themeButton { background: transparent; color: @QUIET@; border-radius: 8px; padding: 8px 10px; }
QToolButton#dataButton:hover, QToolButton#themeButton:hover { background: @QUIET_HOVER@; color: @INK@; }
QToolButton#themeButton:checked { background: @ACTIVE_BG@; color: @ACTIVE_TEXT@; }
QPushButton#navButton { text-align: left; padding: 9px 11px; color: @NAV@; background: transparent; border-left: 3px solid transparent; font-size: 14px; }
QPushButton#navButton:hover { background: @NAV_HOVER@; color: @INK@; }
QPushButton#navButton[active="true"] { background: @ACTIVE_BG@; border-left: 3px solid @PRIMARY@; color: @ACTIVE_TEXT@; font-weight: 650; }
QPushButton#smallButton { background: @SMALL@; padding: 7px 10px; color: @SMALL_TEXT@; }
QToolButton#smallButton { background: @SMALL@; border-radius: 8px; padding: 7px 10px; color: @SMALL_TEXT@; }
QToolButton#smallButton:hover { background: @BUTTON_HOVER@; color: @INK@; }
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
    background: @INPUT@; border: 1px solid @INPUT_BORDER@; border-radius: 8px;
    padding: 7px 9px; color: @INK@; selection-background-color: @SELECTION@;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus { border: 1px solid @FOCUS@; }
QComboBox::drop-down { border: 0; width: 24px; }
QComboBox QAbstractItemView { background: @POPUP@; border: 1px solid @POPUP_BORDER@; selection-background-color: @ACTIVE_BG@; }
QProgressBar { background: @PROGRESS@; border: 0; border-radius: 4px; text-align: center; max-height: 7px; }
QProgressBar::chunk { background: @ACCENT@; border-radius: 4px; }
QScrollArea { background: transparent; border: 0; }
QScrollArea QWidget#scrollContents { background: transparent; }
QScrollBar:vertical { background: @SCROLL@; width: 9px; margin: 0; border: 0; }
QScrollBar::handle:vertical { background: @SCROLL_THUMB@; min-height: 28px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: @SCROLL_HOVER@; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QDialog { background: @DIALOG@; }
QDialogButtonBox QPushButton { min-width: 80px; }
QMenu { background: @MENU@; border: 1px solid @MENU_BORDER@; padding: 5px; }
QMenu::item { padding: 8px 24px 8px 12px; border-radius: 5px; }
QMenu::item:selected { background: @MENU_SELECTED@; color: @INK@; }
"""


def stylesheet_for(theme: dict[str, str]) -> str:
    stylesheet = STYLESHEET_TEMPLATE
    for name, value in theme.items():
        stylesheet = stylesheet.replace(f"@{name.upper()}@", value)
    return stylesheet


def activate_theme(mode: str) -> None:
    global ACTIVE_THEME, INK, BLUE, MINT, CORAL, MUTED, AMBER, SURFACE
    ACTIVE_THEME = THEMES[mode]
    INK = ACTIVE_THEME["ink"]
    BLUE = ACTIVE_THEME["accent"]
    MINT = ACTIVE_THEME["positive"]
    CORAL = ACTIVE_THEME["negative"]
    MUTED = ACTIVE_THEME["muted"]
    AMBER = ACTIVE_THEME["warning"]
    SURFACE = ACTIVE_THEME["surface"]


STYLESHEET = stylesheet_for(THEMES["light"])


def money(cents: int) -> str:
    rupees, paise = divmod(abs(cents), 100)
    digits = str(rupees)
    if len(digits) > 3:
        trailing = digits[-3:]
        leading = digits[:-3]
        groups = []
        while leading:
            groups.append(leading[-2:])
            leading = leading[:-2]
        digits = ",".join(reversed(groups)) + "," + trailing
    return f"₹{digits}.{paise:02d}"


def short_money(cents: int) -> str:
    rupees = abs(cents) / 100
    if rupees >= 10_000_000:
        return f"₹{rupees / 10_000_000:.1f}Cr"
    if rupees >= 100_000:
        return f"₹{rupees / 100_000:.1f}L"
    if rupees >= 1_000:
        return f"₹{rupees / 1_000:.1f}k"
    return f"₹{round(rupees):,}"


def set_indian_currency(spin: QDoubleSpinBox) -> None:
    spin.setLocale(QLocale("en_IN"))
    spin.setGroupSeparatorShown(True)


def readable_category_color(value: str) -> str:
    color = QColor(value)

    def luminance(component: float) -> float:
        return component / 12.92 if component <= 0.04045 else ((component + 0.055) / 1.055) ** 2.4

    background = QColor(SURFACE)

    def relative_luminance(sample: QColor) -> float:
        red, green, blue, _ = sample.getRgbF()
        return 0.2126 * luminance(red) + 0.7152 * luminance(green) + 0.0722 * luminance(blue)

    background_lightness = relative_luminance(background)
    for _ in range(8):
        color_lightness = relative_luminance(color)
        lighter = max(background_lightness, color_lightness)
        darker = min(background_lightness, color_lightness)
        if (lighter + 0.05) / (darker + 0.05) >= 4.5:
            break
        color = color.darker(115) if background_lightness > 0.5 else color.lighter(115)
    return color.name()


def month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def month_label(value: date) -> str:
    return value.strftime("%B %Y")


def shift_month(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    year, month = divmod(month_index, 12)
    return date(year, month + 1, 1)


def pretty_date(raw: str) -> str:
    value = date.fromisoformat(raw)
    today = date.today()
    if value == today:
        return "Today"
    if value == today - timedelta(days=1):
        return "Yesterday"
    return value.strftime("%b %d").replace(" 0", " ")


def divider() -> QFrame:
    frame = QFrame()
    frame.setObjectName("divider")
    frame.setFixedHeight(1)
    return frame


def make_label(text: str, object_name: str | None = None) -> QLabel:
    result = QLabel(text)
    if object_name:
        result.setObjectName(object_name)
    return result


class WaveMark(QWidget):
    """Small painted brand mark: two moving-water strokes in a deep teal tile."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(38, 38)
        self.setAccessibleName("Wave")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(ACTIVE_THEME["wave_tile"]))
        painter.drawRoundedRect(self.rect(), 12, 12)

        for y, color in ((14, ACTIVE_THEME["wave_light"]), (23, ACTIVE_THEME["wave_mid"])):
            wave = QPainterPath(QPointF(7, y))
            wave.cubicTo(QPointF(12, y - 5), QPointF(17, y + 5), QPointF(22, y))
            wave.cubicTo(QPointF(26, y - 4), QPointF(29, y - 3), QPointF(32, y - 1))
            painter.setPen(QPen(QColor(color), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawPath(wave)
        painter.end()


class SpendingPieChart(QWidget):
    """A native-painted donut chart for the selected month's expense mix."""

    def __init__(self, segments: list[dict], total_cents: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.segments = segments
        self.total_cents = total_cents
        self.setMinimumSize(142, 142)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        diameter = min(self.width(), self.height()) - 10
        chart = QRectF(
            (self.width() - diameter) / 2,
            (self.height() - diameter) / 2,
            diameter,
            diameter,
        )
        if self.total_cents > 0:
            start = 90 * 16
            for segment in self.segments:
                span = round(segment["amount_cents"] * 360 * 16 / self.total_cents)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(segment["color"]))
                painter.drawPie(chart, start, -span)
                start -= span
        else:
            painter.setPen(QPen(QColor(ACTIVE_THEME["chart_empty"]), 12))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(chart.adjusted(7, 7, -7, -7))

        hole = chart.adjusted(diameter * 0.27, diameter * 0.27, -diameter * 0.27, -diameter * 0.27)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(SURFACE))
        painter.drawEllipse(hole)
        painter.setPen(QColor(INK if self.total_cents else MUTED))
        font = QFont(self.font())
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(hole.adjusted(-6, 0, 6, 0), Qt.AlignmentFlag.AlignCenter, short_money(self.total_cents))
        painter.end()


class WeeklySpendingChart(QWidget):
    """A compact native bar chart of weekly expenses in the selected month."""

    def __init__(self, values: list[int], labels: list[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.values = values
        self.labels = labels
        self.setMinimumHeight(142)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        plot = QRectF(34, 12, max(1, self.width() - 44), max(1, self.height() - 38))
        peak = max(self.values, default=0)
        chart_max = max(peak * 1.15, 100)

        for part in range(4):
            y = plot.top() + plot.height() * part / 3
            painter.setPen(QPen(QColor(ACTIVE_THEME["chart_grid"]), 1, Qt.PenStyle.DotLine))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))

        if peak <= 0:
            painter.setPen(QColor(MUTED))
            painter.drawText(plot, Qt.AlignmentFlag.AlignCenter, "No expenses recorded")
            painter.end()
            return

        group_width = plot.width() / max(1, len(self.values))
        bar_width = min(34.0, group_width * 0.56)
        for index, value in enumerate(self.values):
            x_center = plot.left() + group_width * (index + 0.5)
            bar_height = max(2.0, value / chart_max * plot.height()) if value else 0
            bar = QRectF(x_center - bar_width / 2, plot.bottom() - bar_height, bar_width, bar_height)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(BLUE if value else ACTIVE_THEME["chart_zero"]))
            painter.drawRoundedRect(bar, 4, 4)

            painter.setPen(QColor(ACTIVE_THEME["chart_label"]))
            painter.drawText(
                QRectF(x_center - group_width / 2, max(0, bar.top() - 17), group_width, 16),
                Qt.AlignmentFlag.AlignCenter,
                short_money(value),
            )
            painter.setPen(QColor(MUTED))
            painter.drawText(
                QRectF(x_center - group_width / 2, plot.bottom() + 5, group_width, 18),
                Qt.AlignmentFlag.AlignCenter,
                self.labels[index],
            )
        painter.end()


class TransactionDialog(QDialog):
    def __init__(
        self,
        store: Store,
        default_date: date,
        parent: QWidget | None = None,
        transaction: dict | None = None,
    ):
        super().__init__(parent)
        self.store = store
        self.transaction = transaction
        self.setWindowTitle("Edit an entry" if transaction else "Add an entry")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(make_label("Edit an entry" if transaction else "Add an entry", "sectionTitle"))
        layout.addWidget(make_label("Keep it simple. You can edit your categories any time.", "muted"))

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("What was this for?")
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setRange(0.01, 10000000)
        self.amount_edit.setDecimals(2)
        self.amount_edit.setPrefix("₹ ")
        set_indian_currency(self.amount_edit)
        self.kind_combo = QComboBox()
        self.kind_combo.addItem("Expense", "expense")
        self.kind_combo.addItem("Income", "income")
        self.category_combo = QComboBox()
        self.date_edit = QDateEdit(QDate(default_date.year, default_date.month, default_date.day))
        self.date_edit.setCalendarPopup(True)
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Optional note")
        if transaction:
            self.title_edit.setText(transaction["title"])
            self.amount_edit.setValue(transaction["amount_cents"] / 100)
            self.kind_combo.setCurrentIndex(1 if transaction["kind"] == "income" else 0)
            self.date_edit.setDate(QDate(default_date.year, default_date.month, default_date.day))
            self.note_edit.setText(transaction.get("note", ""))
        form.addRow("Name", self.title_edit)
        form.addRow("Amount", self.amount_edit)
        form.addRow("Type", self.kind_combo)
        form.addRow("Category", self.category_combo)
        form.addRow("Date", self.date_edit)
        form.addRow("Note", self.note_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        save_button.setObjectName("primaryButton")
        if transaction:
            save_button.setText("Save changes")
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.kind_combo.currentIndexChanged.connect(self.refresh_categories)
        self.refresh_categories()
        if transaction:
            for index in range(self.category_combo.count()):
                if self.category_combo.itemData(index) == transaction["category_id"]:
                    self.category_combo.setCurrentIndex(index)
                    break

    def refresh_categories(self) -> None:
        kind = self.kind_combo.currentData()
        self.category_combo.clear()
        for category in self.store.categories(kind):
            self.category_combo.addItem(f"{category['mark']}   {category['name']}", category["id"])
        if not self.transaction and self.category_combo.count():
            last_id = self.store.preference(f"last_category_{kind}")
            for index in range(self.category_combo.count()):
                if str(self.category_combo.itemData(index)) == last_id:
                    self.category_combo.setCurrentIndex(index)
                    break

    def validate_and_accept(self) -> None:
        if not self.title_edit.text().strip():
            QMessageBox.information(self, "Add a name", "Give this entry a short name first.")
            self.title_edit.setFocus()
            return
        if self.category_combo.count() == 0:
            QMessageBox.information(self, "No categories", "Add a category before creating this entry.")
            return
        self.accept()

    def entry(self) -> dict:
        qdate = self.date_edit.date()
        return {
            "title": self.title_edit.text().strip(),
            "amount_cents": round(self.amount_edit.value() * 100),
            "kind": self.kind_combo.currentData(),
            "category_id": int(self.category_combo.currentData()),
            "happened_on": date(qdate.year(), qdate.month(), qdate.day()).isoformat(),
            "note": self.note_edit.text().strip(),
        }


class BudgetDialog(QDialog):
    def __init__(self, categories: list[dict], selected_id: int | None = None, limit: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monthly budget")
        self.setMinimumWidth(390)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(make_label("Set a monthly limit", "sectionTitle"))
        layout.addWidget(make_label("Give a category a little structure, not a hard stop.", "muted"))
        form = QFormLayout()
        self.category_combo = QComboBox()
        for item in categories:
            self.category_combo.addItem(f"{item['mark']}   {item['name']}", item["id"])
            if item["id"] == selected_id:
                self.category_combo.setCurrentIndex(self.category_combo.count() - 1)
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setRange(1, 10000000)
        self.amount_edit.setDecimals(2)
        self.amount_edit.setPrefix("₹ ")
        set_indian_currency(self.amount_edit)
        if limit:
            self.amount_edit.setValue(limit / 100)
        form.addRow("Category", self.category_combo)
        form.addRow("Monthly limit", self.amount_edit)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("primaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[int, int]:
        return int(self.category_combo.currentData()), round(self.amount_edit.value() * 100)


class CategoryDialog(QDialog):
    PALETTE = ["#28786F", "#267596", "#586EA8", "#7759A4", "#B54F37", "#896813", "#A24F76", "#4E7B42"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create a category")
        self.setMinimumWidth(390)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(make_label("Create a category", "sectionTitle"))
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Name your category")
        self.kind_combo = QComboBox()
        self.kind_combo.addItem("Expense", "expense")
        self.kind_combo.addItem("Income", "income")
        self.color_combo = QComboBox()
        for color in self.PALETTE:
            self.color_combo.addItem("●", color)
            self.color_combo.setItemData(
                self.color_combo.count() - 1,
                readable_category_color(color),
                Qt.ItemDataRole.ForegroundRole,
            )
        form.addRow("Name", self.name_edit)
        form.addRow("Type", self.kind_combo)
        form.addRow("Color", self.color_combo)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("primaryButton")
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.information(self, "Name your category", "Enter a name to continue.")
            return
        self.accept()

    def values(self) -> tuple[str, str, str, str]:
        name = self.name_edit.text().strip()
        return name, self.color_combo.currentData(), name[:1].upper(), self.kind_combo.currentData()


class RecurringDialog(QDialog):
    def __init__(self, store: Store, parent=None, recurring: dict | None = None):
        super().__init__(parent)
        self.store = store
        self.recurring = recurring
        self.setWindowTitle("Edit reminder" if recurring else "New reminder")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(make_label("Recurring reminder", "sectionTitle"))
        layout.addWidget(make_label("Wave never posts these automatically. You confirm each entry.", "muted"))

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Name this reminder")
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setRange(0.01, 10000000)
        self.amount_edit.setDecimals(2)
        self.amount_edit.setPrefix("₹ ")
        set_indian_currency(self.amount_edit)
        self.kind_combo = QComboBox()
        self.kind_combo.addItem("Expense", "expense")
        self.kind_combo.addItem("Income", "income")
        self.category_combo = QComboBox()
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItem("Monthly", "monthly")
        self.frequency_combo.addItem("Weekly", "weekly")
        self.frequency_combo.addItem("Yearly", "yearly")
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd MMM yyyy")
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Optional note")

        if recurring:
            self.title_edit.setText(recurring["title"])
            self.amount_edit.setValue(recurring["amount_cents"] / 100)
            self.kind_combo.setCurrentIndex(1 if recurring["kind"] == "income" else 0)
            self.frequency_combo.setCurrentIndex(self.frequency_combo.findData(recurring["frequency"]))
            due = date.fromisoformat(recurring["next_due"])
            self.date_edit.setDate(QDate(due.year, due.month, due.day))
            self.note_edit.setText(recurring.get("note", ""))

        form.addRow("Name", self.title_edit)
        form.addRow("Amount", self.amount_edit)
        form.addRow("Type", self.kind_combo)
        form.addRow("Category", self.category_combo)
        form.addRow("Repeats", self.frequency_combo)
        form.addRow("Next reminder", self.date_edit)
        form.addRow("Note", self.note_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        save_button.setObjectName("primaryButton")
        if recurring:
            save_button.setText("Save changes")
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.kind_combo.currentIndexChanged.connect(self.refresh_categories)
        self.refresh_categories()
        if recurring:
            for index in range(self.category_combo.count()):
                if self.category_combo.itemData(index) == recurring["category_id"]:
                    self.category_combo.setCurrentIndex(index)
                    break

    def refresh_categories(self) -> None:
        self.category_combo.clear()
        kind = self.kind_combo.currentData()
        for category in self.store.categories(kind):
            self.category_combo.addItem(f"{category['mark']}   {category['name']}", category["id"])
        if not self.recurring and self.category_combo.count():
            last_id = self.store.preference(f"last_category_{kind}")
            for index in range(self.category_combo.count()):
                if str(self.category_combo.itemData(index)) == last_id:
                    self.category_combo.setCurrentIndex(index)
                    break

    def validate(self) -> None:
        if not self.title_edit.text().strip():
            QMessageBox.information(self, "Name this reminder", "Enter a name to continue.")
            return
        if self.category_combo.count() == 0:
            QMessageBox.information(self, "No categories", "Create a matching category before adding a reminder.")
            return
        self.accept()

    def values(self) -> dict:
        due = self.date_edit.date()
        return {
            "title": self.title_edit.text().strip(),
            "amount_cents": round(self.amount_edit.value() * 100),
            "kind": self.kind_combo.currentData(),
            "category_id": int(self.category_combo.currentData()),
            "frequency": self.frequency_combo.currentData(),
            "next_due": date(due.year(), due.month(), due.day()).isoformat(),
            "note": self.note_edit.text().strip(),
        }


class MainWindow(QMainWindow):
    NAV_ITEMS = ["Overview", "Activity", "Budgets", "Recurring", "Categories"]
    NAV_GLYPHS = {
        "Overview": "⌂",
        "Activity": "≋",
        "Budgets": "▤",
        "Recurring": "↻",
        "Categories": "◇",
    }

    def __init__(self, store: Store):
        super().__init__()
        self.store = store
        self.dark_mode = store.preference("theme_mode") == "dark"
        activate_theme("dark" if self.dark_mode else "light")
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet_for(ACTIVE_THEME))
        self.current_month = date.today().replace(day=1)
        self.current_page = "Overview"
        self.setWindowTitle("Wave: money in motion")
        self.setMinimumSize(1020, 700)
        self.resize(1400, 920)
        self.new_entry_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.new_entry_shortcut.activated.connect(self.add_entry)

        root = QWidget()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self.build_sidebar())

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.build_topbar())
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.page_host = QWidget()
        self.page_host.setObjectName("scrollContents")
        self.page_layout = QVBoxLayout(self.page_host)
        self.page_layout.setContentsMargins(24, 20, 24, 24)
        self.page_layout.setSpacing(14)
        self.scroll.setWidget(self.page_host)
        right_layout.addWidget(self.scroll, 1)
        root_layout.addWidget(right, 1)
        self.render_page()

    def build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(226)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(18, 20, 18, 16)
        layout.setSpacing(7)
        brand = QHBoxLayout()
        self.wave_mark = WaveMark()
        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        self.brand_title = QLabel("wave")
        self.brand_subtitle = make_label("money in motion", "muted")
        name_col.addWidget(self.brand_title)
        name_col.addWidget(self.brand_subtitle)
        self.brand_title.setStyleSheet(f"font-size:23px; font-weight:700; color:{INK};")
        self.brand_subtitle.setStyleSheet(f"font-size:10px; color:{MUTED};")
        brand.addWidget(self.wave_mark)
        brand.addSpacing(10)
        brand.addLayout(name_col)
        brand.addStretch(1)
        layout.addLayout(brand)
        layout.addSpacing(22)
        layout.addWidget(make_label("Workspace", "muted"))
        layout.addSpacing(5)
        self.nav_buttons: dict[str, QPushButton] = {}
        for item in self.NAV_ITEMS:
            button = QPushButton(f"{self.NAV_GLYPHS[item]}   {item}")
            button.setObjectName("navButton")
            button.setProperty("active", item == self.current_page)
            button.setAccessibleName(item)
            button.setToolTip(item)
            button.clicked.connect(lambda checked=False, page=item: self.navigate(page))
            layout.addWidget(button)
            self.nav_buttons[item] = button
        layout.addStretch(1)

        summary_card = QFrame()
        summary_card.setObjectName("sidebarSummary")
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(11, 9, 11, 9)
        summary_layout.setSpacing(4)
        summary_layout.addWidget(make_label("This month", "muted"))
        self.sidebar_spent = make_label("₹0.00", "metricValue")
        self.sidebar_spent.setStyleSheet("font-size:18px; font-weight:650;")
        summary_layout.addWidget(self.sidebar_spent)
        self.sidebar_plan = make_label("No category limits", "metricHint")
        summary_layout.addWidget(self.sidebar_plan)
        self.sidebar_progress = QProgressBar()
        self.sidebar_progress.setRange(0, 100)
        self.sidebar_progress.setTextVisible(False)
        self.sidebar_progress.setFixedHeight(5)
        summary_layout.addWidget(self.sidebar_progress)
        layout.addWidget(summary_card)

        local_card = QFrame()
        local_card.setObjectName("surfaceQuiet")
        local_layout = QVBoxLayout(local_card)
        local_layout.setContentsMargins(12, 12, 12, 12)
        local_layout.setSpacing(7)
        status = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{MINT}; font-size:10px;")
        self.sidebar_privacy_dot = dot
        status.addWidget(dot)
        private_label = make_label("Private by default", "sectionTitle")
        private_label.setStyleSheet("font-size:14px; font-weight:600;")
        status.addWidget(private_label)
        status.addStretch(1)
        local_layout.addLayout(status)
        privacy_note = make_label("Your entries stay on this device. No accounts, no connection.", "muted")
        privacy_note.setWordWrap(True)
        local_layout.addWidget(privacy_note)
        layout.addWidget(local_card)
        return side

    def build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(64)
        bar.setObjectName("topbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setSpacing(8)
        self.month_prev = QToolButton()
        self.month_prev.setObjectName("quietButton")
        self.month_prev.setText("‹")
        self.month_prev.setFixedSize(30, 32)
        self.month_prev.clicked.connect(lambda: self.change_month(-1))
        self.month_next = QToolButton()
        self.month_next.setObjectName("quietButton")
        self.month_next.setText("›")
        self.month_next.setFixedSize(30, 32)
        self.month_next.clicked.connect(lambda: self.change_month(1))
        self.month_text = make_label(month_label(self.current_month), "sectionTitle")
        self.month_text.setMinimumWidth(126)
        layout.addWidget(self.month_prev)
        layout.addWidget(self.month_text)
        layout.addWidget(self.month_next)
        layout.addStretch(1)
        self.local_status = make_label("●   Local only", "muted")
        self.local_status.setStyleSheet(f"color:{MUTED}; font-size:12px; padding-right:14px;")
        layout.addWidget(self.local_status)
        self.theme_toggle = QToolButton()
        self.theme_toggle.setObjectName("themeButton")
        self.theme_toggle.setText("Dark mode")
        self.theme_toggle.setCheckable(True)
        self.theme_toggle.setChecked(self.dark_mode)
        self.theme_toggle.setAccessibleName("Dark mode")
        self.theme_toggle.setToolTip("Switch between light and dark forest themes")
        self.theme_toggle.toggled.connect(self.set_dark_mode)
        layout.addWidget(self.theme_toggle)
        data_button = QToolButton()
        data_button.setObjectName("dataButton")
        data_button.setText("Data")
        data_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        data_menu = QMenu(data_button)
        backup_action = data_menu.addAction("Create a backup…")
        restore_action = data_menu.addAction("Restore a backup…")
        backup_action.triggered.connect(lambda: self.export_backup())
        restore_action.triggered.connect(lambda: self.restore_backup())
        data_button.setMenu(data_menu)
        layout.addWidget(data_button)
        add_button = QPushButton("+  New entry")
        add_button.setObjectName("primaryButton")
        add_button.setToolTip("Add an entry (Ctrl+N)")
        add_button.clicked.connect(self.add_entry)
        layout.addWidget(add_button)
        return bar

    @property
    def selected_month(self) -> str:
        return month_key(self.current_month)

    def change_month(self, delta: int) -> None:
        self.current_month = shift_month(self.current_month, delta)
        self.month_text.setText(month_label(self.current_month))
        self.render_page()

    def set_dark_mode(self, enabled: bool) -> None:
        self.dark_mode = enabled
        mode = "dark" if enabled else "light"
        self.store.set_preference("theme_mode", mode)
        activate_theme(mode)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet_for(ACTIVE_THEME))
        self.brand_title.setStyleSheet(f"font-size:23px; font-weight:700; color:{INK};")
        self.brand_subtitle.setStyleSheet(f"font-size:10px; color:{MUTED};")
        self.sidebar_privacy_dot.setStyleSheet(f"color:{MINT}; font-size:10px;")
        self.local_status.setStyleSheet(f"color:{MUTED}; font-size:12px; padding-right:14px;")
        self.wave_mark.update()
        self.refresh_sidebar_summary()
        self.render_page()

    def refresh_sidebar_summary(self) -> None:
        totals = self.store.month_totals(self.selected_month)
        budget_rows = self.store.budget_rows(self.selected_month)
        planned = sum(row["limit_cents"] for row in budget_rows)
        spent = totals["expense"]
        self.sidebar_spent.setText(short_money(spent))
        self.sidebar_spent.setToolTip(money(spent))
        if planned:
            percent = round(spent * 100 / planned)
            self.sidebar_plan.setText(f"of {short_money(planned)} planned")
            self.sidebar_progress.setValue(min(100, percent))
            color = CORAL if percent >= 100 else BLUE
            self.sidebar_progress.setStyleSheet(f"QProgressBar::chunk{{background:{color}; border-radius:3px;}}")
            self.sidebar_progress.show()
        else:
            self.sidebar_plan.setText("No category limits")
            self.sidebar_progress.hide()

    def navigate(self, page: str) -> None:
        self.current_page = page
        for item, button in self.nav_buttons.items():
            button.setProperty("active", item == page)
            button.style().unpolish(button)
            button.style().polish(button)
        self.render_page()

    def clear_page(self) -> None:
        self.clear_layout(self.page_layout)

    def clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            if child_layout:
                self.clear_layout(child_layout)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def render_page(self) -> None:
        self.refresh_sidebar_summary()
        self.clear_page()
        if self.current_page == "Overview":
            self.render_overview()
        elif self.current_page == "Activity":
            self.render_activity()
        elif self.current_page == "Budgets":
            self.render_budgets()
        elif self.current_page == "Recurring":
            self.render_recurring()
        else:
            self.render_categories()
        if self.current_page != "Overview":
            self.page_layout.addStretch(1)

    def page_heading(self, title: str, subtitle: str) -> None:
        heading = QVBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(3)
        heading.addWidget(make_label(title, "pageTitle"))
        heading.addWidget(make_label(subtitle, "muted"))
        self.page_layout.addLayout(heading)

    def inline_stat(self, title: str, value: str, hint: str = "", color: str | None = None) -> QWidget:
        stat = QWidget()
        layout = QVBoxLayout(stat)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(make_label(title, "eyebrow"))
        number = make_label(value, "metricValue")
        number.setStyleSheet(f"color:{color or INK}; font-size:21px; font-weight:650;")
        layout.addWidget(number)
        if hint:
            layout.addWidget(make_label(hint, "metricHint"))
        return stat

    @staticmethod
    def vertical_rule() -> QFrame:
        rule = QFrame()
        rule.setObjectName("verticalRule")
        rule.setFixedWidth(1)
        return rule

    def budget_pace(self, row: dict) -> tuple[str, str, int | None]:
        limit = row["limit_cents"]
        spent = row["spent_cents"]
        if limit <= 0:
            return "No limit", MUTED, None
        today = date.today()
        current_month = self.selected_month == month_key(today)
        projection = None
        if current_month:
            days = (shift_month(today.replace(day=1), 1) - timedelta(days=1)).day
            projection = round(spent * days / max(1, today.day))
        if spent > limit:
            return f"Over by {money(spent - limit)}", CORAL, projection
        if spent == limit:
            return "At your limit", CORAL, projection
        if not current_month:
            if self.current_month > today.replace(day=1):
                return "Starts this month", MUTED, None
            return "Within limit", MINT, None
        if spent == 0:
            return "No spend yet", MUTED, None
        expected = limit * today.day / days
        if today.day >= 3 and projection is not None and projection > limit * 1.05:
            return "Trending over", CORAL, projection
        if spent > expected * 1.18 and spent > 0:
            return "A little ahead of pace", AMBER, projection
        return "On pace", MINT, projection

    def section_header(self, title: str, trailing: QWidget | None = None) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(make_label(title, "sectionTitle"))
        row.addStretch(1)
        if trailing:
            row.addWidget(trailing)
        return row

    def render_overview(self) -> None:
        totals = self.store.month_totals(self.selected_month)
        expenses, income = totals["expense"], totals["income"]
        budget_rows = self.store.budget_rows(self.selected_month)
        month_entries = self.store.transactions(month=self.selected_month)
        category_spend: dict[int, dict] = {}
        for entry in month_entries:
            if entry["kind"] != "expense":
                continue
            bucket = category_spend.setdefault(
                entry["category_id"],
                {
                    "name": entry["category_name"],
                    "color": readable_category_color(entry["category_color"]),
                    "amount_cents": 0,
                },
            )
            bucket["amount_cents"] += entry["amount_cents"]
        pie_segments = sorted(category_spend.values(), key=lambda row: row["amount_cents"], reverse=True)
        if len(pie_segments) > 5:
            remainder = pie_segments[4:]
            pie_segments = pie_segments[:4] + [
                {
                    "name": "Other",
                    "color": readable_category_color(MUTED),
                    "amount_cents": sum(row["amount_cents"] for row in remainder),
                }
            ]
        planned = sum(row["limit_cents"] for row in budget_rows)
        net = income - expenses
        net_label = money(net) if net >= 0 else f"−{money(net)}"
        self.page_heading("Overview", "Your month at a glance.")

        summary = QFrame()
        summary.setObjectName("summaryBand")
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(16, 12, 16, 12)
        summary_layout.setSpacing(8)
        summary_stats = QHBoxLayout()
        summary_stats.setSpacing(12)
        spend_hint = f"of {money(planned)} planned" if planned else "No monthly limits set"
        summary_stats.addWidget(self.inline_stat("Spent this month", money(expenses), spend_hint), 1)
        summary_stats.addWidget(self.vertical_rule())
        summary_stats.addWidget(self.inline_stat("Income", money(income), "Money recorded", MINT), 1)
        summary_stats.addWidget(self.vertical_rule())
        summary_stats.addWidget(
            self.inline_stat("Net this month", net_label, "Income minus spending", CORAL if net < 0 else BLUE),
            1,
        )
        summary_layout.addLayout(summary_stats)
        if planned:
            total_progress = QProgressBar()
            total_progress.setRange(0, 100)
            total_progress.setValue(min(100, round(expenses * 100 / planned)))
            total_progress.setTextVisible(False)
            total_progress.setFixedHeight(7)
            color = CORAL if expenses >= planned else BLUE
            total_progress.setStyleSheet(f"QProgressBar::chunk{{background:{color}; border-radius:4px;}}")
            progress_caption = QHBoxLayout()
            progress_caption.addWidget(make_label("Spending against category plans", "metricHint"))
            progress_caption.addStretch(1)
            progress_caption.addWidget(make_label(f"{min(999, round(expenses * 100 / planned))}% used", "metricHint"))
            summary_layout.addLayout(progress_caption)
            summary_layout.addWidget(total_progress)
        self.page_layout.addWidget(summary)

        due_reminders = self.store.due_recurring()
        if due_reminders:
            reminder = QFrame()
            reminder.setObjectName("reminderStrip")
            reminder_layout = QHBoxLayout(reminder)
            reminder_layout.setContentsMargins(14, 10, 14, 10)
            count = len(due_reminders)
            reminder_layout.addWidget(make_label(f"{count} recurring reminder{'s' if count != 1 else ''} due for review", "sectionTitle"))
            reminder_layout.addWidget(make_label("Nothing is added until you confirm it.", "muted"), 1)
            review = QPushButton("Review")
            review.setObjectName("smallButton")
            review.clicked.connect(lambda: self.navigate("Recurring"))
            reminder_layout.addWidget(review)
            self.page_layout.addWidget(reminder)

        days = (shift_month(self.current_month, 1) - timedelta(days=1)).day
        day_values = self.store.daily_spend(self.selected_month, days)
        if self.selected_month == month_key(date.today()):
            day_values = day_values[: date.today().day]
        elif self.current_month > date.today().replace(day=1):
            day_values = [0] * days
        weekly_spend = [sum(day_values[start : start + 7]) for start in range(0, len(day_values), 7)]
        week_labels = [
            f"{start + 1}-{min(start + 7, len(day_values))}"
            for start in range(0, len(day_values), 7)
        ]

        charts = QHBoxLayout()
        charts.setSpacing(12)
        pie_panel = QFrame()
        pie_panel.setObjectName("surfaceQuiet")
        pie_layout = QVBoxLayout(pie_panel)
        pie_layout.setContentsMargins(12, 10, 12, 10)
        pie_layout.setSpacing(7)
        pie_layout.addWidget(make_label("Spending by category", "sectionTitle"))
        pie_content = QHBoxLayout()
        pie_content.setSpacing(10)
        pie_content.addWidget(SpendingPieChart(pie_segments, expenses), 1)
        legend = QVBoxLayout()
        legend.setContentsMargins(0, 0, 0, 0)
        legend.setSpacing(5)
        legend.addStretch(1)
        if pie_segments:
            for segment in pie_segments:
                legend_row = QHBoxLayout()
                legend_row.setSpacing(5)
                swatch = QLabel("●")
                swatch.setStyleSheet(f"color:{segment['color']}; font-size:10px;")
                legend_row.addWidget(swatch)
                name = make_label(segment["name"], "muted")
                legend_row.addWidget(name, 1)
                amount = make_label(money(segment["amount_cents"]), "muted")
                amount.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                legend_row.addWidget(amount)
                legend.addLayout(legend_row)
        else:
            legend.addWidget(make_label("Add an expense to see the split.", "muted"))
        legend.addStretch(1)
        pie_content.addLayout(legend, 1)
        pie_layout.addLayout(pie_content, 1)
        charts.addWidget(pie_panel, 1)

        bar_panel = QFrame()
        bar_panel.setObjectName("surfaceQuiet")
        bar_layout = QVBoxLayout(bar_panel)
        bar_layout.setContentsMargins(12, 10, 12, 8)
        bar_layout.setSpacing(4)
        bar_layout.addWidget(make_label("Weekly spending", "sectionTitle"))
        bar_layout.addWidget(make_label("Seven-day totals", "muted"))
        bar_layout.addWidget(WeeklySpendingChart(weekly_spend, week_labels), 1)
        charts.addWidget(bar_panel, 1)
        self.page_layout.addLayout(charts, 2)

        details = QHBoxLayout()
        details.setSpacing(16)
        ledger = QWidget()
        ledger_layout = QVBoxLayout(ledger)
        ledger_layout.setContentsMargins(0, 0, 0, 0)
        ledger_layout.setSpacing(5)
        activity_button = QPushButton("All activity  ›")
        activity_button.setObjectName("quietButton")
        activity_button.clicked.connect(lambda: self.navigate("Activity"))
        ledger_layout.addLayout(self.section_header("Latest entries", activity_button))
        entries = month_entries[:5]
        if entries:
            for index, entry in enumerate(entries):
                ledger_layout.addWidget(self.transaction_row(entry, deletable=False))
                if index < len(entries) - 1:
                    ledger_layout.addWidget(divider())
        else:
            ledger_layout.addSpacing(8)
            ledger_layout.addWidget(make_label("Nothing recorded for this month.", "sectionTitle"))
            ledger_layout.addWidget(make_label("Start with one expense or income. You can change it later.", "muted"))
            add_first = QPushButton("+  Add an entry")
            add_first.setObjectName("smallButton")
            add_first.clicked.connect(self.add_entry)
            ledger_layout.addWidget(add_first, 0, Qt.AlignmentFlag.AlignLeft)
        details.addWidget(ledger, 1)
        details.addWidget(self.vertical_rule())

        budget_column = QWidget()
        budget_layout = QVBoxLayout(budget_column)
        budget_layout.setContentsMargins(0, 0, 0, 0)
        budget_layout.setSpacing(5)
        budget_button = QPushButton("Manage  ›")
        budget_button.setObjectName("quietButton")
        budget_button.clicked.connect(lambda: self.navigate("Budgets"))
        budget_layout.addLayout(self.section_header("Budget pace", budget_button))
        active = sorted(
            (row for row in budget_rows if row["limit_cents"] > 0),
            key=lambda row: row["spent_cents"] / max(1, row["limit_cents"]),
            reverse=True,
        )
        unplanned_spending = sorted(
            (row for row in budget_rows if row["limit_cents"] == 0 and row["spent_cents"] > 0),
            key=lambda row: row["spent_cents"],
            reverse=True,
        )
        overview_budgets = (active + unplanned_spending)[:4]
        if overview_budgets:
            for row in overview_budgets:
                budget_layout.addWidget(self.compact_budget(row))
        else:
            budget_layout.addWidget(make_label("No monthly limits yet.", "muted"))
            set_budget = QPushButton("Set a limit")
            set_budget.setObjectName("quietButton")
            set_budget.clicked.connect(self.edit_budget)
            budget_layout.addWidget(set_budget, 0, Qt.AlignmentFlag.AlignLeft)
        details.addWidget(budget_column, 1, Qt.AlignmentFlag.AlignTop)
        self.page_layout.addLayout(details)

    def compact_budget(self, row: dict) -> QWidget:
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        top = QHBoxLayout()
        mark = QLabel(row["mark"])
        mark.setStyleSheet(f"color:{readable_category_color(row['color'])}; font-weight:700;")
        top.addWidget(mark)
        top.addWidget(make_label(row["name"]))
        top.addStretch(1)
        if row["limit_cents"]:
            top.addWidget(make_label(f"{money(row['spent_cents'])} / {money(row['limit_cents'])}", "muted"))
        elif row["spent_cents"]:
            top.addWidget(make_label(money(row["spent_cents"]), "muted"))
        else:
            top.addWidget(make_label("No spend", "muted"))
        layout.addLayout(top)
        if row["limit_cents"]:
            percent = min(999, round(row["spent_cents"] * 100 / row["limit_cents"]))
            progress = QProgressBar()
            progress.setTextVisible(False)
            progress.setRange(0, 100)
            progress.setValue(min(100, percent))
            tint = CORAL if percent >= 100 else readable_category_color(row["color"])
            progress.setStyleSheet(f"QProgressBar::chunk{{background:{tint}; border-radius:4px;}}")
            layout.addWidget(progress)
            status_text, status_color, projection = self.budget_pace(row)
            if projection is not None:
                status_text = f"{status_text} · projected {money(projection)}"
        else:
            status_text, status_color = "No limit set", MUTED
        status = make_label(status_text, "metricHint")
        status.setStyleSheet(f"color:{status_color}; font-size:11px;")
        layout.addWidget(status)
        return wrapper

    def transaction_row(self, entry: dict, deletable: bool = False) -> QWidget:
        row = QWidget()
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row.setFixedHeight(44)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(11)
        badge = QLabel(entry["category_mark"])
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(25, 25)
        badge.setStyleSheet(f"color:{readable_category_color(entry['category_color'])}; font-weight:700; font-size:13px;")
        layout.addWidget(badge)
        details = QVBoxLayout()
        details.setSpacing(3)
        details.addWidget(make_label(entry["title"], "sectionTitle"))
        secondary = f"{entry['category_name']}  ·  {pretty_date(entry['happened_on'])}"
        if entry.get("note"):
            secondary += f"  ·  {entry['note']}"
        details.addWidget(make_label(secondary, "muted"))
        layout.addLayout(details, 1)
        amount = make_label(("+" if entry["kind"] == "income" else "−") + money(entry["amount_cents"]))
        amount.setStyleSheet(f"color:{MINT if entry['kind'] == 'income' else INK}; font-weight:650;")
        layout.addWidget(amount)
        if deletable:
            edit_button = QPushButton("Edit")
            edit_button.setObjectName("quietButton")
            edit_button.clicked.connect(lambda checked=False, item=entry: self.edit_transaction(item))
            layout.addWidget(edit_button)
            remove_button = QPushButton("×")
            remove_button.setObjectName("quietButton")
            remove_button.setFixedSize(28, 28)
            remove_button.setToolTip("Remove this entry")
            remove_button.clicked.connect(lambda checked=False, txid=entry["id"]: self.remove_transaction(txid))
            layout.addWidget(remove_button)
        return row

    def remove_transaction(self, transaction_id: int) -> None:
        confirm = QMessageBox.question(self, "Remove this entry?", "This entry will be removed from your local history.")
        if confirm == QMessageBox.StandardButton.Yes:
            self.store.delete_transaction(transaction_id)
            self.render_page()

    def edit_transaction(self, entry: dict) -> None:
        default_date = date.fromisoformat(entry["happened_on"])
        dialog = TransactionDialog(self.store, default_date, self, transaction=entry)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.entry()
            try:
                self.store.update_transaction(entry["id"], **values)
                self.current_month = date.fromisoformat(values["happened_on"]).replace(day=1)
                self.month_text.setText(month_label(self.current_month))
                self.render_page()
            except Exception as exc:
                QMessageBox.critical(self, "Entry not updated", str(exc))

    def render_activity(self) -> None:
        self.page_heading("Activity", "Every entry, in one place. Search by name, note, or category.")
        controls = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search this month’s entries…")
        self.search_edit.setMinimumWidth(240)
        self.category_filter = QComboBox()
        self.category_filter.addItem("All categories", None)
        for item in self.store.categories():
            self.category_filter.addItem(item["name"], item["id"])
        self.type_filter = QComboBox()
        self.type_filter.addItem("All types", None)
        self.type_filter.addItem("Expenses", "expense")
        self.type_filter.addItem("Income", "income")
        self.export_button = QPushButton("Export month")
        self.export_button.setObjectName("smallButton")
        self.export_button.clicked.connect(self.export_csv)
        controls.addWidget(self.search_edit, 1)
        controls.addWidget(self.category_filter)
        controls.addWidget(self.type_filter)
        controls.addWidget(self.export_button)
        self.page_layout.addLayout(controls)

        self.activity_panel = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_panel)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(6)
        self.activity_count = make_label("", "muted")
        self.activity_layout.addWidget(self.activity_count)
        self.activity_list_layout = QVBoxLayout()
        self.activity_list_layout.setSpacing(6)
        self.activity_layout.addLayout(self.activity_list_layout)
        self.page_layout.addWidget(self.activity_panel)
        self.search_edit.textChanged.connect(self.refresh_activity_list)
        self.category_filter.currentIndexChanged.connect(self.refresh_activity_list)
        self.type_filter.currentIndexChanged.connect(self.refresh_activity_list)
        self.refresh_activity_list()

    def refresh_activity_list(self) -> None:
        if not hasattr(self, "activity_list_layout"):
            return
        while self.activity_list_layout.count():
            item = self.activity_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        rows = self.store.transactions(
            month=self.selected_month,
            search=self.search_edit.text(),
            category_id=self.category_filter.currentData(),
            kind=self.type_filter.currentData(),
        )
        self.activity_count.setText(f"{len(rows)} entr{'y' if len(rows) == 1 else 'ies'} in {month_label(self.current_month)}")
        for index, entry in enumerate(rows):
            self.activity_list_layout.addWidget(self.transaction_row(entry, deletable=True))
            if index < len(rows) - 1:
                self.activity_list_layout.addWidget(divider())
        if not rows:
            has_filter = bool(
                self.search_edit.text().strip()
                or self.category_filter.currentData() is not None
                or self.type_filter.currentData() is not None
            )
            message = (
                "No entries match those filters. Clear them to see the full month."
                if has_filter
                else "No entries this month yet. Add an expense or income to start your history."
            )
            empty = make_label(message, "muted")
            empty.setContentsMargins(0, 10, 0, 10)
            self.activity_list_layout.addWidget(empty)
            if has_filter:
                clear_button = QPushButton("Clear filters")
                clear_button.setObjectName("smallButton")
                clear_button.clicked.connect(self.clear_activity_filters)
                self.activity_list_layout.addWidget(clear_button, 0, Qt.AlignmentFlag.AlignLeft)
            else:
                add_button = QPushButton("+  Add your first entry")
                add_button.setObjectName("smallButton")
                add_button.clicked.connect(self.add_entry)
                self.activity_list_layout.addWidget(add_button, 0, Qt.AlignmentFlag.AlignLeft)

    def clear_activity_filters(self) -> None:
        self.search_edit.clear()
        self.category_filter.setCurrentIndex(0)
        self.type_filter.setCurrentIndex(0)

    def export_csv(self) -> None:
        suggested = f"wave-{self.selected_month}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export activity", str(Path.home() / suggested), "CSV files (*.csv)")
        if not path:
            return
        rows = self.store.transactions(month=self.selected_month)
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Type", "Name", "Category", "Amount (INR)", "Note"])
                for entry in rows:
                    writer.writerow([
                        entry["happened_on"], entry["kind"], entry["title"], entry["category_name"],
                        f"{entry['amount_cents'] / 100:.2f}", entry["note"],
                    ])
            QMessageBox.information(self, "Export complete", f"Saved {len(rows)} entries to:\n{path}")
        except OSError as exc:
            QMessageBox.critical(self, "Could not export", str(exc))

    def export_backup(self) -> None:
        suggested = Path.home() / f"wave-backup-{date.today().isoformat()}.wavebackup"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Create a Wave backup",
            str(suggested),
            "Wave backup (*.wavebackup)",
        )
        if not path:
            return
        target = Path(path)
        if not target.suffix:
            target = target.with_suffix(".wavebackup")
        try:
            self.store.export_backup(target)
            QMessageBox.information(self, "Backup created", f"Your local Wave backup is ready:\n{target}")
        except Exception as exc:
            QMessageBox.critical(self, "Backup failed", str(exc))

    def restore_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore a Wave backup",
            str(Path.home()),
            "Wave backup (*.wavebackup *.db);;All files (*)",
        )
        if not path:
            return
        confirm = QMessageBox(self)
        confirm.setIcon(QMessageBox.Icon.Warning)
        confirm.setWindowTitle("Replace Wave data?")
        confirm.setText("Restoring replaces all current categories, entries, budgets, and reminders with the backup. This cannot be undone.")
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        confirm.button(QMessageBox.StandardButton.Yes).setText("Restore backup")
        confirm.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if confirm.exec() != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.restore_backup(path)
            self.render_page()
            QMessageBox.information(self, "Backup restored", "Wave has been restored from the selected backup.")
        except Exception as exc:
            QMessageBox.critical(self, "Restore failed", str(exc))

    def budget_row(self, entry: dict) -> QWidget:
        card = QWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(3, 6, 3, 6)
        layout.setSpacing(4)
        top = QHBoxLayout()
        mark = QLabel(entry["mark"])
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedWidth(25)
        mark.setStyleSheet(f"color:{readable_category_color(entry['color'])}; font-weight:700; font-size:13px;")
        name_group = QVBoxLayout()
        name_group.setSpacing(2)
        name_group.addWidget(make_label(entry["name"], "sectionTitle"))
        if entry["limit_cents"]:
            remaining = entry["limit_cents"] - entry["spent_cents"]
            detail_text = f"{money(max(0, remaining))} left" if remaining >= 0 else f"{money(abs(remaining))} over plan"
            detail = make_label(detail_text, "muted")
        else:
            detail = make_label("No monthly limit yet", "muted")
        name_group.addWidget(detail)
        top.addWidget(mark)
        top.addLayout(name_group, 1)
        if entry["limit_cents"]:
            top.addWidget(make_label(f"{money(entry['spent_cents'])} / {money(entry['limit_cents'])}", "sectionTitle"))
        elif entry["spent_cents"]:
            top.addWidget(make_label(f"{money(entry['spent_cents'])} spent", "sectionTitle"))
        else:
            top.addWidget(make_label("No activity", "muted"))
        edit = QPushButton("Edit limit" if entry["limit_cents"] else "Set limit")
        edit.setObjectName("smallButton")
        edit.clicked.connect(lambda checked=False, row=entry: self.edit_budget(row))
        top.addWidget(edit)
        layout.addLayout(top)
        if entry["limit_cents"]:
            percent = round(entry["spent_cents"] * 100 / entry["limit_cents"])
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(min(100, percent))
            bar.setTextVisible(False)
            color = CORAL if percent >= 100 else readable_category_color(entry["color"])
            bar.setStyleSheet(f"QProgressBar::chunk{{background:{color}; border-radius:4px;}}")
            layout.addWidget(bar)
            pace, pace_color, projection = self.budget_pace(entry)
            if projection is not None:
                pace = f"{pace} · projected {money(projection)}"
            pace_label = make_label(pace, "muted")
            pace_label.setStyleSheet(f"color:{pace_color}; font-size:11px;")
            layout.addWidget(pace_label)
        return card

    def render_budgets(self) -> None:
        self.page_heading("Budgets", "Set a soft limit for the categories that matter to you.")
        rows = self.store.budget_rows(self.selected_month)
        total_limit = sum(row["limit_cents"] for row in rows)
        total_spent = sum(row["spent_cents"] for row in rows if row["limit_cents"] > 0)
        has_budgets = total_limit > 0
        summary = QFrame()
        summary.setObjectName("summaryBand")
        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(16, 12, 16, 12)
        summary_layout.setSpacing(14)
        if has_budgets:
            projection = None
            today = date.today()
            is_current_month = self.selected_month == month_key(today)
            is_future_month = self.current_month > today.replace(day=1)
            if is_current_month:
                days = (shift_month(date.today().replace(day=1), 1) - timedelta(days=1)).day
                projection = sum(round(row["spent_cents"] * days / date.today().day) for row in rows if row["limit_cents"] > 0)
            summary_layout.addWidget(self.inline_stat("Monthly limits", money(total_limit)), 1)
            summary_layout.addWidget(self.vertical_rule())
            summary_layout.addWidget(self.inline_stat("Spent", money(total_spent), "In planned categories", MINT), 1)
            summary_layout.addWidget(self.vertical_rule())
            summary_layout.addWidget(
                self.inline_stat(
                    "Month-end projection",
                    money(projection) if projection is not None else ("Not started" if is_future_month else "Month ended"),
                    "Based on current daily average" if projection is not None else ("Selected future month" if is_future_month else "Actual for selected month"),
                    CORAL if projection is not None and projection > total_limit else INK,
                ),
                1,
            )
        else:
            actual_spend = self.store.month_totals(self.selected_month)["expense"]
            summary_layout.addWidget(self.inline_stat("Monthly plan", "Not set", "Choose category limits below", BLUE), 1)
            summary_layout.addWidget(self.vertical_rule())
            summary_layout.addWidget(self.inline_stat("Spent this month", money(actual_spend), "Across all categories", MINT), 1)
            summary_layout.addWidget(self.vertical_rule())
            summary_layout.addWidget(self.inline_stat("Categories", str(len(rows)), "Ready for a limit", BLUE), 1)
        self.page_layout.addWidget(summary)

        button = QPushButton("+  Add budget")
        button.setObjectName("primaryButton")
        button.clicked.connect(lambda: self.edit_budget())
        self.page_layout.addLayout(self.section_header("Category plans", button))
        if not rows:
            empty = QWidget()
            empty_layout = QVBoxLayout(empty)
            empty_layout.setContentsMargins(0, 10, 0, 0)
            empty_layout.addWidget(make_label("No expense categories yet.", "sectionTitle"))
            empty_layout.addWidget(make_label("Create a category first, then set a monthly limit.", "muted"))
            self.page_layout.addWidget(empty)
        for index, row in enumerate(rows):
            self.page_layout.addWidget(self.budget_row(row))
            if index < len(rows) - 1:
                self.page_layout.addWidget(divider())

    @staticmethod
    def frequency_label(frequency: str) -> str:
        return {"weekly": "Weekly", "monthly": "Monthly", "yearly": "Yearly"}.get(frequency, frequency.title())

    def recurring_row(self, entry: dict, due: bool = False) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(3, 5, 3, 5)
        layout.setSpacing(9)
        mark = QLabel(entry["category_mark"])
        mark.setFixedWidth(25)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setStyleSheet(f"color:{readable_category_color(entry['category_color'])}; font-size:13px; font-weight:700;")
        layout.addWidget(mark)
        details = QVBoxLayout()
        details.setSpacing(3)
        details.addWidget(make_label(entry["title"], "sectionTitle"))
        scheduled = date.fromisoformat(entry["next_due"]).strftime("%d %b %Y")
        details.addWidget(make_label(f"{entry['category_name']} · {self.frequency_label(entry['frequency'])} · {scheduled}", "muted"))
        layout.addLayout(details, 1)
        amount = make_label(("+" if entry["kind"] == "income" else "−") + money(entry["amount_cents"]))
        amount.setStyleSheet(f"color:{MINT if entry['kind'] == 'income' else INK}; font-weight:650;")
        layout.addWidget(amount)

        if due:
            post = QPushButton("Add entry")
            post.setObjectName("primaryButton")
            post.setToolTip("Add this scheduled occurrence to your activity")
            post.clicked.connect(lambda checked=False, item_id=entry["id"]: self.post_recurring(item_id))
            skip = QPushButton("Skip")
            skip.setObjectName("quietButton")
            skip.clicked.connect(lambda checked=False, item_id=entry["id"]: self.skip_recurring(item_id))
            layout.addWidget(post)
            layout.addWidget(skip)
            manage = QToolButton()
            manage.setObjectName("smallButton")
            manage.setText("More")
            menu = QMenu(manage)
            edit_action = menu.addAction("Edit reminder")
            remove_action = menu.addAction("Remove reminder")
            edit_action.triggered.connect(lambda checked=False, item=entry: self.edit_recurring(item))
            remove_action.triggered.connect(lambda checked=False, item_id=entry["id"]: self.remove_recurring(item_id))
            manage.setMenu(menu)
            manage.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            layout.addWidget(manage)
        else:
            edit = QPushButton("Edit")
            edit.setObjectName("quietButton")
            edit.clicked.connect(lambda checked=False, item=entry: self.edit_recurring(item))
            remove = QPushButton("×")
            remove.setObjectName("quietButton")
            remove.setFixedSize(28, 28)
            remove.setToolTip("Remove reminder")
            remove.clicked.connect(lambda checked=False, item_id=entry["id"]: self.remove_recurring(item_id))
            layout.addWidget(edit)
            layout.addWidget(remove)
        return row

    def render_recurring(self) -> None:
        heading = QVBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(3)
        title_row = QHBoxLayout()
        title_row.addWidget(make_label("Recurring", "pageTitle"))
        title_row.addStretch(1)
        add_button = QPushButton("+  New reminder")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_recurring)
        title_row.addWidget(add_button)
        heading.addLayout(title_row)
        heading.addWidget(make_label("A reminder only. Wave adds an entry when you confirm it.", "muted"))
        self.page_layout.addLayout(heading)

        due = self.store.due_recurring()
        if due:
            self.page_layout.addWidget(make_label("Due for review", "sectionTitle"))
            for index, entry in enumerate(due):
                self.page_layout.addWidget(self.recurring_row(entry, due=True))
                if index < len(due) - 1:
                    self.page_layout.addWidget(divider())
            self.page_layout.addSpacing(6)

        all_entries = self.store.recurring_entries()
        due_ids = {entry["id"] for entry in due}
        upcoming = [entry for entry in all_entries if entry["id"] not in due_ids]
        self.page_layout.addWidget(make_label("Scheduled reminders", "sectionTitle"))
        if upcoming:
            for index, entry in enumerate(upcoming):
                self.page_layout.addWidget(self.recurring_row(entry))
                if index < len(upcoming) - 1:
                    self.page_layout.addWidget(divider())
        elif due:
            self.page_layout.addWidget(make_label("No other reminders scheduled.", "muted"))
        else:
            empty = QWidget()
            empty_layout = QVBoxLayout(empty)
            empty_layout.setContentsMargins(0, 10, 0, 0)
            empty_layout.addWidget(make_label("No reminders set.", "sectionTitle"))
            empty_layout.addWidget(make_label("Add one for a regular bill or income. Nothing will be recorded until you approve it.", "muted"))
            create = QPushButton("Create a reminder")
            create.setObjectName("smallButton")
            create.clicked.connect(self.add_recurring)
            empty_layout.addWidget(create, 0, Qt.AlignmentFlag.AlignLeft)
            self.page_layout.addWidget(empty)

    def add_recurring(self) -> None:
        dialog = RecurringDialog(self.store, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.store.add_recurring(**dialog.values())
                self.render_page()
            except Exception as exc:
                QMessageBox.critical(self, "Reminder not saved", str(exc))

    def edit_recurring(self, entry: dict) -> None:
        dialog = RecurringDialog(self.store, self, recurring=entry)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.store.update_recurring(entry["id"], **dialog.values())
                self.render_page()
            except Exception as exc:
                QMessageBox.critical(self, "Reminder not updated", str(exc))

    def post_recurring(self, recurring_id: int) -> None:
        try:
            self.store.post_recurring(recurring_id)
            self.render_page()
        except Exception as exc:
            QMessageBox.critical(self, "Entry not added", str(exc))

    def skip_recurring(self, recurring_id: int) -> None:
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Skip this occurrence?")
        confirm.setText("This advances the reminder without adding anything to your activity.")
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        confirm.button(QMessageBox.StandardButton.Yes).setText("Skip occurrence")
        confirm.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if confirm.exec() == QMessageBox.StandardButton.Yes:
            self.store.skip_recurring(recurring_id)
            self.render_page()

    def remove_recurring(self, recurring_id: int) -> None:
        answer = QMessageBox.question(
            self,
            "Remove reminder?",
            "This removes the schedule. Any entries already added remain in your activity.",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.store.delete_recurring(recurring_id)
            self.render_page()

    def edit_budget(self, row: dict | None = None) -> None:
        categories = self.store.categories("expense")
        if not categories:
            QMessageBox.information(self, "Add a category first", "Create an expense category before setting a budget.")
            return
        dialog = BudgetDialog(
            categories,
            row["id"] if row else None,
            row["limit_cents"] if row else 0,
            self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            category_id, cents = dialog.values()
            self.store.save_budget(category_id, cents)
            self.render_page()

    def render_categories(self) -> None:
        heading = QVBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(3)
        title_row = QHBoxLayout()
        title_row.addWidget(make_label("Categories", "pageTitle"))
        title_row.addStretch(1)
        create = QPushButton("+  New category")
        create.setObjectName("primaryButton")
        create.clicked.connect(self.add_category)
        title_row.addWidget(create)
        heading.addLayout(title_row)
        heading.addWidget(make_label("Make the labels yours. Categories can be renamed as your life changes.", "muted"))
        self.page_layout.addLayout(heading)

        for kind, title, subtitle in [
            ("expense", "Spending categories", "Used to organize your expenses and budgets"),
            ("income", "Income categories", "Keep track of where money comes from"),
        ]:
            section_heading = QVBoxLayout()
            section_heading.setContentsMargins(0, 0, 0, 0)
            section_heading.setSpacing(2)
            section_heading.addWidget(make_label(title, "sectionTitle"))
            section_heading.addWidget(make_label(subtitle, "muted"))
            self.page_layout.addLayout(section_heading)
            categories = self.store.categories(kind)
            category_list = QWidget()
            list_layout = QVBoxLayout(category_list)
            list_layout.setContentsMargins(0, 0, 0, 0)
            list_layout.setSpacing(0)
            for index, item in enumerate(categories):
                list_layout.addWidget(self.category_card(item))
                if index < len(categories) - 1:
                    list_layout.addWidget(divider())
            if not categories:
                list_layout.addWidget(make_label("No categories yet.", "muted"))
            self.page_layout.addWidget(category_list)

    def category_card(self, category: dict) -> QWidget:
        card = QWidget()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(9)
        mark = QLabel(category["mark"])
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedWidth(25)
        mark.setStyleSheet(f"color:{readable_category_color(category['color'])}; font-weight:700; font-size:13px;")
        layout.addWidget(mark)
        layout.addWidget(make_label(category["name"], "sectionTitle"), 1)
        rename = QPushButton("Rename")
        rename.setObjectName("quietButton")
        rename.clicked.connect(lambda checked=False, item=category: self.rename_category(item))
        delete = QPushButton("×")
        delete.setObjectName("quietButton")
        delete.setFixedWidth(28)
        delete.setToolTip("Remove category")
        delete.clicked.connect(lambda checked=False, item=category: self.remove_category(item))
        layout.addWidget(rename)
        layout.addWidget(delete)
        return card

    def add_category(self) -> None:
        dialog = CategoryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, color, mark, kind = dialog.values()
            try:
                self.store.add_category(name, color, mark, kind)
            except Exception as exc:
                QMessageBox.warning(self, "Category not added", f"That name may already be in use.\n\n{exc}")
            self.render_page()

    def rename_category(self, category: dict) -> None:
        name, accepted = QInputDialog.getText(self, "Rename category", "Category name:", text=category["name"])
        if accepted and name.strip():
            try:
                self.store.rename_category(category["id"], name)
                self.render_page()
            except Exception as exc:
                QMessageBox.warning(self, "Category not renamed", f"That name may already be in use.\n\n{exc}")

    def remove_category(self, category: dict) -> None:
        confirm = QMessageBox.question(
            self,
            "Remove category?",
            f"Remove “{category['name']}”? Categories with saved entries can’t be removed.",
        )
        if confirm == QMessageBox.StandardButton.Yes:
            if not self.store.delete_category(category["id"]):
                QMessageBox.information(self, "Category is in use", "Move or remove its entries before deleting this category.")
            self.render_page()

    def add_entry(self) -> None:
        target_month = self.current_month
        today = date.today()
        default_date = today if month_key(target_month) == month_key(today) else target_month
        dialog = TransactionDialog(self.store, default_date, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.entry()
            try:
                self.store.add_transaction(**values)
                self.current_month = date.fromisoformat(values["happened_on"]).replace(day=1)
                self.month_text.setText(month_label(self.current_month))
                self.render_page()
            except Exception as exc:
                QMessageBox.critical(self, "Entry not saved", str(exc))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Wave")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    store = Store()
    window = MainWindow(store)
    window.show()
    result = app.exec()
    store.close()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
