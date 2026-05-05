import json
import re
import unicodedata

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTextEdit,
    QTimeEdit,
    QWidget,
)

from app_paths import get_accessibility_config_path


THEME_OPTIONS = ("Claro", "Escuro")
FONT_SIZE_OPTIONS = ("Muito pequena", "Pequena", "Padrao", "Grande", "Muito grande")
INTERFACE_SCALE_OPTIONS = ("90%", "100%", "110%", "125%", "150%", "175%")

DEFAULT_ACCESSIBILITY_CONFIG = {
    "tema": "Claro",
    "tamanho_fonte": "Padrao",
    "escala_interface": "100%",
    "navegacao_teclado": False,
}

_FONT_SIZE_MAP = {
    "Muito pequena": 11,
    "Pequena": 12,
    "Padrao": 14,
    "Grande": 16,
    "Muito grande": 18,
}

_SCALE_FACTOR_MAP = {
    "90%": 0.9,
    "100%": 1.0,
    "110%": 1.1,
    "125%": 1.25,
    "150%": 1.5,
    "175%": 1.75,
}

_NEUTRAL_LIGHT_COLORS = {
    "#1e293b",
    "#334155",
    "#475569",
    "#5a6e85",
    "#64748b",
    "#7e95aa",
    "#94a3b8",
    "#cbd5e1",
}

_PRESERVED_ACCENT_COLORS = {
    "#2a9d8f",
    "#3b82f6",
    "#06b6d4",
    "#10b981",
    "#1d4ed8",
    "#2563eb",
    "#60a5fa",
    "#7dd3fc",
    "#8b5cf6",
    "#d97706",
    "#dc2626",
    "#e76f51",
    "#ef4444",
    "#f59e0b",
}

_app = None
_base_style = ""
_global_style = ""
_current_config = DEFAULT_ACCESSIBILITY_CONFIG.copy()
_accessibility_event_filter = None


class _AccessibilityEventFilter(QObject):
    def eventFilter(self, watched, event):
        if isinstance(watched, QWidget) and event.type() == QEvent.Show:
            _apply_accessibility_to_widget_tree(watched, _current_config)
            _repolish_widget_tree(watched)
        return False


def _normalize_key(value):
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return text.strip().lower()


def _to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "sim", "yes", "on"}


def load_local_accessibility_config():
    path = get_accessibility_config_path()
    if not path.exists():
        return DEFAULT_ACCESSIBILITY_CONFIG.copy()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_ACCESSIBILITY_CONFIG.copy()

    return normalize_accessibility_config(data)


def save_local_accessibility_config(config=None):
    normalized = normalize_accessibility_config(config)
    path = get_accessibility_config_path()

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        return False

    return True


def normalize_accessibility_config(config=None):
    source = DEFAULT_ACCESSIBILITY_CONFIG.copy()
    if config:
        source.update(config)

    tema = "Escuro" if _normalize_key(source.get("tema")) == "escuro" else "Claro"

    tamanho_key = _normalize_key(source.get("tamanho_fonte"))
    if tamanho_key in {"muito pequena", "muitopequena"}:
        tamanho_fonte = "Muito pequena"
    elif tamanho_key == "pequena":
        tamanho_fonte = "Pequena"
    elif tamanho_key in {"muito grande", "muitogrande"}:
        tamanho_fonte = "Muito grande"
    elif tamanho_key == "grande":
        tamanho_fonte = "Grande"
    else:
        tamanho_fonte = "Padrao"

    escala_interface = str(source.get("escala_interface", DEFAULT_ACCESSIBILITY_CONFIG["escala_interface"])).strip()
    if escala_interface not in _SCALE_FACTOR_MAP:
        escala_interface = DEFAULT_ACCESSIBILITY_CONFIG["escala_interface"]

    return {
        "tema": tema,
        "tamanho_fonte": tamanho_fonte,
        "escala_interface": escala_interface,
        "navegacao_teclado": _to_bool(source.get("navegacao_teclado", False)),
    }


def build_accessibility_config(tema, tamanho_fonte, escala_interface, navegacao_teclado):
    return normalize_accessibility_config(
        {
            "tema": tema,
            "tamanho_fonte": tamanho_fonte,
            "escala_interface": escala_interface,
            "navegacao_teclado": navegacao_teclado,
        }
    )


def get_accessibility_options():
    return {
        "tema": list(THEME_OPTIONS),
        "tamanho_fonte": list(FONT_SIZE_OPTIONS),
        "escala_interface": list(INTERFACE_SCALE_OPTIONS),
    }


def initialize_accessibility(app, base_style="", global_style=""):
    global _app, _base_style, _global_style, _accessibility_event_filter, _current_config
    _app = app
    _base_style = base_style or ""
    _global_style = global_style or ""
    _current_config = load_local_accessibility_config()
    if _accessibility_event_filter is None:
        _accessibility_event_filter = _AccessibilityEventFilter(app)
        _app.installEventFilter(_accessibility_event_filter)
    apply_accessibility_config(_current_config)


def get_current_accessibility_config():
    return _current_config.copy()


def apply_accessibility_config(config=None):
    global _current_config

    normalized = normalize_accessibility_config(config)
    _current_config = normalized

    if _app is None:
        return normalized

    font = QFont(_app.font())
    font.setPixelSize(_FONT_SIZE_MAP[normalized["tamanho_fonte"]])
    _app.setFont(font)
    _apply_palette(normalized["tema"])

    stylesheet = _build_stylesheet(normalized)
    _app.setStyleSheet("")
    _app.setStyleSheet(stylesheet)
    _app.setProperty("accessibility_theme", normalized["tema"])
    _app.setProperty("accessibility_font_size", normalized["tamanho_fonte"])
    _app.setProperty("accessibility_scale", normalized["escala_interface"])
    _app.setProperty("keyboard_navigation_enabled", normalized["navegacao_teclado"])

    _apply_widget_overrides(normalized)
    _repolish_widgets()
    return normalized


def _apply_palette(theme):
    if _app is None:
        return

    palette = QPalette()
    if theme == "Escuro":
        palette.setColor(QPalette.Window, QColor("#0f172a"))
        palette.setColor(QPalette.WindowText, QColor("#e2e8f0"))
        palette.setColor(QPalette.Base, QColor("#0f172a"))
        palette.setColor(QPalette.AlternateBase, QColor("#172033"))
        palette.setColor(QPalette.Text, QColor("#e2e8f0"))
        palette.setColor(QPalette.Button, QColor("#1e293b"))
        palette.setColor(QPalette.ButtonText, QColor("#f8fafc"))
        palette.setColor(QPalette.Highlight, QColor("#2563eb"))
        palette.setColor(QPalette.HighlightedText, QColor("#f8fafc"))
    else:
        palette = QApplication.style().standardPalette()
    _app.setPalette(palette)


def _apply_widget_overrides(config):
    if _app is None:
        return

    scale = _get_font_zoom(config)
    for widget in _app.allWidgets():
        _cache_widget_defaults(widget)
        _apply_scaled_widget_font(widget, scale)
        _apply_keyboard_navigation_preferences(widget, config)
        _apply_widget_stylesheet(widget, config)


def _apply_accessibility_to_widget_tree(root_widget, config):
    widgets = [root_widget, *root_widget.findChildren(QWidget)]
    scale = _get_font_zoom(config)
    for widget in widgets:
        _cache_widget_defaults(widget)
        _apply_scaled_widget_font(widget, scale)
        _apply_keyboard_navigation_preferences(widget, config)
        _apply_widget_stylesheet(widget, config)


def _cache_widget_defaults(widget):
    if widget.property("_accessibility_base_stylesheet") is None:
        widget.setProperty("_accessibility_base_stylesheet", widget.styleSheet() or "")

    font = widget.font()
    if widget.property("_accessibility_base_font_pixel") is None:
        widget.setProperty("_accessibility_base_font_pixel", font.pixelSize())
    if widget.property("_accessibility_base_font_point") is None:
        widget.setProperty("_accessibility_base_font_point", font.pointSize())


def _apply_keyboard_navigation_preferences(widget, config):
    if not widget.property("keyboardNavigationTarget"):
        return

    focus_policy = Qt.StrongFocus if config["navegacao_teclado"] else Qt.NoFocus
    if widget.focusPolicy() != focus_policy:
        widget.setFocusPolicy(focus_policy)


def _apply_scaled_widget_font(widget, scale):
    base_pixel = widget.property("_accessibility_base_font_pixel")
    base_point = widget.property("_accessibility_base_font_point")

    font = QFont(widget.font())
    if isinstance(base_pixel, int) and base_pixel > 0:
        font.setPixelSize(max(1, round(base_pixel * scale)))
        widget.setFont(font)
        return

    if isinstance(base_point, int) and base_point > 0:
        font.setPointSize(max(1, round(base_point * scale)))
        widget.setFont(font)


def _get_font_zoom(config):
    interface_scale = _SCALE_FACTOR_MAP[config["escala_interface"]]
    font_scale = _FONT_SIZE_MAP[config["tamanho_fonte"]] / _FONT_SIZE_MAP["Padrao"]
    return interface_scale * font_scale


def _apply_widget_stylesheet(widget, config):
    base_stylesheet = widget.property("_accessibility_base_stylesheet")
    if base_stylesheet is None:
        base_stylesheet = widget.styleSheet() or ""

    override = _build_widget_override(widget, config, base_stylesheet)
    final_stylesheet = base_stylesheet or ""
    if override:
        final_stylesheet = f"{final_stylesheet}\n{override}".strip()

    if widget.styleSheet() != final_stylesheet:
        widget.setStyleSheet(final_stylesheet)


def _build_widget_override(widget, config, base_stylesheet):
    if not base_stylesheet:
        return ""

    theme = config["tema"]
    font_px = _get_scaled_widget_font_px(widget, base_stylesheet, config)
    button_height = max(36, round(36 * _SCALE_FACTOR_MAP[config["escala_interface"]]))
    input_height = max(38, round(38 * _SCALE_FACTOR_MAP[config["escala_interface"]]))

    if isinstance(widget, QLabel):
        return _build_label_override(widget, theme, font_px, base_stylesheet)

    if isinstance(widget, QPushButton):
        return _build_button_override(widget, theme, font_px, button_height)

    if isinstance(widget, (QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit)):
        return _build_input_override(widget, theme, font_px, input_height)

    if isinstance(widget, QTableWidget):
        return _build_table_override(theme, font_px)

    if isinstance(widget, QListWidget):
        return _build_list_override(theme, font_px)

    if isinstance(widget, QCheckBox):
        return _build_checkbox_override(theme, font_px)

    if isinstance(widget, QGroupBox):
        return _build_groupbox_override(theme, font_px)

    if isinstance(widget, QFrame):
        return _build_frame_override(theme)

    if isinstance(widget, QDialog):
        return _build_dialog_override(theme)

    if isinstance(widget, QWidget):
        return _build_container_override(theme)

    return ""


def _font_to_pixels(font, fallback):
    if font.pixelSize() > 0:
        return font.pixelSize()
    if font.pointSizeF() > 0:
        return max(1, round(font.pointSizeF() * 96 / 72))
    return fallback


def _get_scaled_widget_font_px(widget, base_stylesheet, config):
    css_match = re.search(r"font-size\s*:\s*(\d+)px", base_stylesheet or "", re.IGNORECASE)
    if css_match:
        base_px = int(css_match.group(1))
    else:
        base_pixel = widget.property("_accessibility_base_font_pixel")
        base_point = widget.property("_accessibility_base_font_point")
        if isinstance(base_pixel, int) and base_pixel > 0:
            base_px = base_pixel
        elif isinstance(base_point, int) and base_point > 0:
            base_px = max(1, round(base_point * 96 / 72))
        else:
            base_px = _FONT_SIZE_MAP["Padrao"]

    return max(10, round(base_px * _get_font_zoom(config)))


def _build_label_override(widget, theme, font_px, base_stylesheet):
    color_rule = ""
    if theme == "Escuro":
        color_rule = f"color: {_resolve_dark_label_color(widget, base_stylesheet)};"

    extra_rules = ""
    if widget.property("class") == "page-title":
        extra_rules = "border-bottom: 2px solid #60a5fa;" if theme == "Escuro" else ""

    return f"""
        QLabel {{
            font-size: {font_px}px;
            {color_rule}
            {extra_rules}
        }}
    """


def _resolve_dark_label_color(widget, base_stylesheet):
    widget_class = str(widget.property("class") or "")
    if widget_class == "page-title":
        return "#f8fafc"
    if widget_class == "footer":
        return "#cbd5e1"

    lowered = (base_stylesheet or "").lower()
    if "white" in lowered:
        return "#f8fafc"

    colors = re.findall(r"#[0-9a-fA-F]{6}", lowered)
    for color in colors:
        if color in _PRESERVED_ACCENT_COLORS:
            return color

    return "#e2e8f0"


def _build_button_override(widget, theme, font_px, button_height):
    return f"""
        QPushButton {{
            font-size: {font_px}px;
            min-height: {button_height}px;
        }}
    """


def _build_input_override(widget, theme, font_px, input_height):
    selector = widget.metaObject().className()
    if selector == "QComboBox":
        if theme == "Escuro":
            return f"""
                QComboBox {{
                    font-size: {font_px}px;
                    min-height: {input_height}px;
                    background-color: #0f172a;
                    color: #e2e8f0;
                    border: 1px solid #475569;
                }}

                QComboBox QAbstractItemView {{
                    font-size: {font_px}px;
                    background-color: #111827;
                    color: #e2e8f0;
                    border: 1px solid #334155;
                }}

                QComboBox QAbstractItemView::item:selected {{
                    background-color: #1d4ed8;
                    color: #f8fafc;
                }}
            """

        return f"""
            QComboBox {{
                font-size: {font_px}px;
                min-height: {input_height}px;
            }}

            QComboBox QAbstractItemView {{
                font-size: {font_px}px;
            }}
        """

    if theme == "Escuro":
        return f"""
            {selector} {{
                font-size: {font_px}px;
                min-height: {input_height}px;
                background-color: #0f172a;
                color: #e2e8f0;
                border: 1px solid #475569;
            }}
        """

    return f"""
        {selector} {{
            font-size: {font_px}px;
            min-height: {input_height}px;
        }}
    """


def _build_table_override(theme, font_px):
    if theme == "Escuro":
        return f"""
            QTableWidget {{
                font-size: {font_px}px;
                background-color: #111827;
                color: #e2e8f0;
                alternate-background-color: #172033;
                gridline-color: #334155;
                selection-background-color: #1d4ed8;
                selection-color: #f8fafc;
            }}

            QHeaderView::section {{
                font-size: {font_px}px;
                background-color: #1e293b;
                color: #e2e8f0;
                border-color: #334155;
            }}
        """

    return f"""
        QTableWidget {{
            font-size: {font_px}px;
        }}

        QHeaderView::section {{
            font-size: {font_px}px;
        }}
    """


def _build_list_override(theme, font_px):
    if theme == "Escuro":
        return f"""
            QListWidget {{
                font-size: {font_px}px;
                background-color: #111827;
                color: #e2e8f0;
                border: 1px solid #334155;
            }}

            QListWidget::item:selected {{
                background-color: #1d4ed8;
                color: #f8fafc;
            }}
        """

    return f"""
        QListWidget {{
            font-size: {font_px}px;
        }}
    """


def _build_checkbox_override(theme, font_px):
    if theme == "Escuro":
        return f"""
            QCheckBox {{
                font-size: {font_px}px;
                color: #e2e8f0;
            }}

            QCheckBox::indicator {{
                border: 1px solid #475569;
                background-color: #0f172a;
            }}

            QCheckBox::indicator:checked {{
                background-color: #2563eb;
                border-color: #3b82f6;
            }}
        """

    return f"""
        QCheckBox {{
            font-size: {font_px}px;
        }}
    """


def _build_groupbox_override(theme, font_px):
    if theme == "Escuro":
        return f"""
            QGroupBox {{
                font-size: {font_px}px;
                background-color: #111827;
                color: #e2e8f0;
                border: 1px solid #334155;
            }}

            QGroupBox::title {{
                color: #7dd3fc;
                background-color: #111827;
            }}
        """

    return f"""
        QGroupBox {{
            font-size: {font_px}px;
        }}

        QGroupBox::title {{
            font-size: {font_px}px;
        }}
    """


def _build_frame_override(theme):
    if theme != "Escuro":
        return ""

    return """
        QFrame {
            background-color: #111827;
            border-color: #334155;
        }
    """


def _build_dialog_override(theme):
    if theme != "Escuro":
        return ""

    return """
        QDialog {
            background-color: #0f172a;
            color: #e2e8f0;
        }
    """


def _build_container_override(theme):
    if theme != "Escuro":
        return ""

    return """
        background-color: #0f172a;
        color: #e2e8f0;

        QWidget {
            background-color: #0f172a;
            color: #e2e8f0;
        }
    """


def _repolish_widgets():
    if _app is None:
        return

    for widget in _app.allWidgets():
        style = widget.style()
        if style is None:
            continue
        style.unpolish(widget)
        style.polish(widget)
        widget.update()


def _repolish_widget_tree(root_widget):
    for widget in [root_widget, *root_widget.findChildren(QWidget)]:
        style = widget.style()
        if style is None:
            continue
        style.unpolish(widget)
        style.polish(widget)
        widget.update()


def _build_stylesheet(config):
    scale = _SCALE_FACTOR_MAP[config["escala_interface"]]
    base_font = _FONT_SIZE_MAP[config["tamanho_fonte"]]
    title_font = max(22, round(24 * scale))
    body_font = max(12, round(base_font * scale))
    small_font = max(11, round((base_font - 1) * scale))
    button_height = max(36, round(36 * scale))
    input_height = max(38, round(38 * scale))
    tab_padding_y = max(10, round(12 * scale))
    tab_padding_x = max(20, round(28 * scale))
    input_padding_y = max(8, round(10 * scale))
    input_padding_x = max(12, round(14 * scale))
    button_padding_y = max(8, round(10 * scale))
    button_padding_x = max(16, round(20 * scale))
    header_padding_y = max(10, round(14 * scale))
    header_padding_x = max(12, round(16 * scale))
    logo_font = max(18, round(20 * scale))
    menu_font = max(14, round(15 * scale))

    focus_override = _build_focus_override(config["tema"], config["navegacao_teclado"])
    if config["tema"] == "Escuro":
        dark_stylesheet = _build_dark_stylesheet(
            body_font=body_font,
            title_font=title_font,
            small_font=small_font,
            button_height=button_height,
            input_height=input_height,
            tab_padding_y=tab_padding_y,
            tab_padding_x=tab_padding_x,
            input_padding_y=input_padding_y,
            input_padding_x=input_padding_x,
            button_padding_y=button_padding_y,
            button_padding_x=button_padding_x,
            header_padding_y=header_padding_y,
            header_padding_x=header_padding_x,
            logo_font=logo_font,
            menu_font=menu_font,
            menu_height=max(44, round(48 * scale)),
        )
        return f"{dark_stylesheet}\n{focus_override}"

    size_override = f"""
        QWidget {{
            font-size: {body_font}px;
        }}

        QLabel,
        QFormLayout QLabel,
        QCheckBox {{
            font-size: {body_font}px;
        }}

        QLabel[class="page-title"] {{
            font-size: {title_font}px;
        }}

        .logo {{
            font-size: {logo_font}px;
        }}

        .menu-button,
        .menu-button-bottom,
        .footer,
        QPushButton,
        QPushButton#btnPrimary,
        QPushButton#btnSecondary,
        QMessageBox QPushButton,
        QDialog QPushButton,
        QTableWidget,
        QHeaderView::section,
        QLineEdit,
        QDateEdit,
        QTimeEdit,
        QSpinBox,
        QTextEdit,
        QComboBox,
        QComboBox QAbstractItemView,
        QListWidget,
        QCheckBox,
        QGroupBox,
        QGroupBox#configGroup,
        QDateEdit QCalendarWidget,
        QDateEdit QCalendarWidget QToolButton,
        QDateEdit QCalendarWidget QToolButton#qt_calendar_monthbutton,
        QDateEdit QCalendarWidget QSpinBox,
        QStatusBar,
        QMenu,
        QToolTip {{
            font-size: {body_font}px;
        }}

        .menu-button,
        .menu-button-bottom {{
            font-size: {menu_font}px;
            height: {max(44, round(48 * scale))}px;
        }}

        .footer {{
            font-size: {small_font}px;
        }}

        QPushButton,
        QPushButton#btnPrimary,
        QPushButton#btnSecondary,
        QMessageBox QPushButton,
        QDialog QPushButton {{
            min-height: {button_height}px;
            padding: {button_padding_y}px {button_padding_x}px;
        }}

        QLineEdit,
        QDateEdit,
        QTimeEdit,
        QSpinBox,
        QTextEdit,
        QComboBox,
        QLineEdit#configInput,
        QLineEdit#configInputOnly,
        QLineEdit#configInputReadonly,
        QSpinBox#configSpin,
        QComboBox#configCombo,
        QDialog QComboBox,
        QDialog QLineEdit,
        QDialog QSpinBox,
        QDialog QDateEdit,
        QDialog QTextEdit {{
            min-height: {input_height}px;
            padding: {input_padding_y}px {input_padding_x}px;
        }}

        QComboBox QAbstractItemView::item,
        QTableWidget::item,
        QHeaderView::section {{
            padding: {header_padding_y}px {header_padding_x}px;
        }}

        QTabBar::tab {{
            min-height: {max(34, round(36 * scale))}px;
            padding: {tab_padding_y}px {tab_padding_x}px;
            font-size: {body_font}px;
        }}
    """

    return f"{_base_style}\n{_global_style}\n{size_override}\n{focus_override}"


def _build_dark_stylesheet(
    *,
    body_font,
    title_font,
    small_font,
    button_height,
    input_height,
    tab_padding_y,
    tab_padding_x,
    input_padding_y,
    input_padding_x,
    button_padding_y,
    button_padding_x,
    header_padding_y,
    header_padding_x,
    logo_font,
    menu_font,
    menu_height,
):
    return f"""
        QMainWindow {{
            background-color: #0f172a;
        }}

        QWidget {{
            background-color: #0f172a;
            color: #e2e8f0;
            font-family: 'Segoe UI', 'Inter', 'Arial', sans-serif;
            font-size: {body_font}px;
        }}

        QLabel[class="page-title"] {{
            font-size: {title_font}px;
            font-weight: bold;
            color: #f8fafc;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #60a5fa;
        }}

        .sidebar {{
            background-color: #0b1623;
            border-right: none;
        }}

        .logo {{
            color: #f8fafc;
            font-size: {logo_font}px;
            font-weight: bold;
            padding: 24px 20px;
            border-bottom: 1px solid #1e293b;
            margin-bottom: 20px;
            background-color: #09111b;
        }}

        .menu-button,
        .menu-button-bottom {{
            text-align: left;
            padding-left: 20px;
            background-color: transparent;
            color: #cbd5e1;
            border: none;
            font-size: {menu_font}px;
            font-weight: 500;
            border-radius: 8px;
            margin: 0;
            height: {menu_height}px;
        }}

        .menu-button:hover,
        .menu-button-bottom:hover {{
            background-color: #1e293b;
            color: #f8fafc;
        }}

        .menu-button:pressed,
        .menu-button-bottom:pressed {{
            background-color: #09111b;
        }}

        .menu-button[active="true"] {{
            background-color: #1d4ed8;
            color: #f8fafc;
            border-left: 3px solid #93c5fd;
        }}

        .footer {{
            color: #94a3b8;
            font-size: {small_font}px;
            padding: 16px;
            border-top: 1px solid #1e293b;
        }}

        .dashboard-card {{
            background-color: #111827;
            border-radius: 16px;
            border: 1px solid #334155;
            padding: 16px;
        }}

        .dashboard-card:hover {{
            border-color: #60a5fa;
            background-color: #172033;
        }}

        QTableWidget {{
            background-color: #111827;
            alternate-background-color: #172033;
            gridline-color: #334155;
            selection-background-color: #1d4ed8;
            selection-color: #f8fafc;
            border: none;
            border-radius: 12px;
            padding: 4px;
            font-size: {body_font}px;
            color: #e2e8f0;
        }}

        QTableWidget::item {{
            padding: {header_padding_y}px {header_padding_x}px;
            border-bottom: 1px solid #1e293b;
        }}

        QHeaderView::section {{
            background-color: #1e293b;
            color: #e2e8f0;
            padding: {header_padding_y}px {header_padding_x}px;
            border: none;
            font-weight: 600;
            font-size: {body_font}px;
        }}

        QTableCornerButton::section {{
            background-color: #1e293b;
            border: none;
            width: 0px;
        }}

        QPushButton {{
            background-color: #2563eb;
            color: #f8fafc;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: {button_padding_y}px {button_padding_x}px;
            font-weight: 600;
            font-size: {body_font}px;
            min-height: {button_height}px;
        }}

        QPushButton:hover {{
            background-color: #1d4ed8;
        }}

        QPushButton:pressed {{
            background-color: #1e40af;
        }}

        QPushButton#btnPrimary {{
            background-color: #2563eb;
            color: #f8fafc;
            border-radius: 8px;
            padding: {button_padding_y}px {button_padding_x}px;
            font-weight: 600;
            font-size: {body_font}px;
        }}

        QPushButton#btnPrimary:hover {{
            background-color: #1d4ed8;
        }}

        QPushButton#btnSecondary {{
            background-color: #172033;
            color: #e2e8f0;
            border: 1px solid #475569;
            border-radius: 8px;
            padding: {button_padding_y}px {button_padding_x}px;
            font-weight: 500;
            font-size: {body_font}px;
        }}

        QPushButton#btnSecondary:hover {{
            background-color: #1e293b;
            color: #f8fafc;
        }}

        QLineEdit,
        QDateEdit,
        QTimeEdit,
        QSpinBox,
        QTextEdit,
        QComboBox,
        QLineEdit#configInput,
        QLineEdit#configInputOnly,
        QLineEdit#configInputReadonly,
        QSpinBox#configSpin,
        QComboBox#configCombo,
        QDialog QComboBox,
        QDialog QLineEdit,
        QDialog QSpinBox,
        QDialog QDateEdit,
        QDialog QTextEdit {{
            background-color: #0f172a;
            border: 1px solid #475569;
            border-radius: 8px;
            padding: {input_padding_y}px {input_padding_x}px;
            color: #e2e8f0;
            font-size: {body_font}px;
            min-height: {input_height}px;
            selection-background-color: #1d4ed8;
            selection-color: #f8fafc;
        }}

        QLineEdit:focus,
        QDateEdit:focus,
        QTimeEdit:focus,
        QSpinBox:focus,
        QTextEdit:focus,
        QComboBox:focus {{
            border-color: #60a5fa;
        }}

        QComboBox::drop-down,
        QDateEdit::drop-down {{
            border: none;
            width: 25px;
            background: transparent;
        }}

        QComboBox::down-arrow,
        QDateEdit::down-arrow {{
            image: none;
            border: none;
            background: transparent;
        }}

        QComboBox QAbstractItemView {{
            background-color: #111827;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 6px;
            outline: none;
            font-size: {body_font}px;
            color: #e2e8f0;
        }}

        QComboBox QAbstractItemView::item {{
            padding: {input_padding_y}px {input_padding_x}px;
            border: none;
            color: #e2e8f0;
            outline: none;
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: #1d4ed8;
            color: #f8fafc;
            border: none;
        }}

        QComboBox QAbstractItemView::item:hover {{
            background-color: #1e293b;
            border: none;
        }}

        QDateEdit QCalendarWidget {{
            background-color: #111827;
            color: #e2e8f0;
            font-size: {body_font}px;
        }}

        QDateEdit QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: #1e293b;
        }}

        QDateEdit QCalendarWidget QToolButton {{
            background-color: #2563eb;
            color: #f8fafc;
            border-radius: 4px;
            border: none;
            min-width: 35px;
            min-height: 30px;
            font-size: {body_font}px;
        }}

        QDateEdit QCalendarWidget QToolButton:hover {{
            background-color: #1d4ed8;
        }}

        QDateEdit QCalendarWidget QToolButton#qt_calendar_monthbutton,
        QDateEdit QCalendarWidget QToolButton#qt_calendar_yearbutton {{
            background-color: #2563eb;
            color: #f8fafc;
            font-weight: bold;
        }}

        QDateEdit QCalendarWidget QSpinBox {{
            background-color: #0f172a;
            color: #e2e8f0;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 6px;
            min-width: 80px;
            font-size: {body_font}px;
        }}

        QDateEdit QCalendarWidget QMenu::item,
        QCalendarWidget QMenu::item {{
            padding: 10px 24px;
            color: #e2e8f0;
            font-size: {body_font}px;
        }}

        QDateEdit QCalendarWidget QMenu::item:selected,
        QCalendarWidget QMenu::item:selected {{
            background-color: #1d4ed8;
            color: #f8fafc;
        }}

        QDateEdit QCalendarWidget QAbstractItemView,
        QCalendarWidget QAbstractItemView {{
            background-color: #111827;
            color: #e2e8f0;
            selection-background-color: #1d4ed8;
            selection-color: #f8fafc;
            font-size: {body_font}px;
        }}

        QCalendarWidget QHeaderView::section {{
            background-color: #1e293b;
            color: #f8fafc;
            padding: 10px;
            font-weight: bold;
            font-size: {body_font}px;
            border: none;
        }}

        QTabWidget::pane {{
            border: 1px solid #334155;
            border-radius: 12px;
            background-color: #111827;
            padding: 20px;
        }}

        QTabBar::tab {{
            background-color: #1e293b;
            color: #cbd5e1;
            padding: {tab_padding_y}px {tab_padding_x}px;
            margin-right: 4px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            font-weight: 500;
            font-size: {body_font}px;
            min-height: 36px;
        }}

        QTabBar::tab:selected {{
            background-color: #111827;
            color: #60a5fa;
            border-bottom: 2px solid #60a5fa;
        }}

        QTabBar::tab:hover:!selected {{
            background-color: #172033;
            color: #f8fafc;
        }}

        QGroupBox,
        QGroupBox#configGroup {{
            border: 1px solid #334155;
            border-radius: 12px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: 600;
            font-size: {body_font}px;
            background-color: #111827;
            color: #e2e8f0;
        }}

        QGroupBox::title,
        QGroupBox#configGroup::title {{
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: #7dd3fc;
            background-color: #111827;
            font-size: {body_font}px;
        }}

        QCheckBox#configCheckbox {{
            spacing: 10px;
            font-size: {body_font}px;
            color: #e2e8f0;
        }}

        QCheckBox#configCheckbox::indicator {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid #475569;
            background-color: #0f172a;
        }}

        QCheckBox#configCheckbox::indicator:checked {{
            background-color: #2563eb;
            border-color: #3b82f6;
        }}

        QScrollBar:vertical {{
            border: none;
            background-color: #1e293b;
            width: 10px;
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical {{
            background-color: #475569;
            border-radius: 5px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: #64748b;
        }}

        QScrollBar:horizontal {{
            border: none;
            background-color: #1e293b;
            height: 10px;
            border-radius: 5px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: #475569;
            border-radius: 5px;
            min-width: 30px;
        }}

        QMessageBox,
        QDialog,
        QFrame#infoCard {{
            background-color: #111827;
            color: #e2e8f0;
        }}

        QMessageBox QLabel {{
            font-size: {body_font}px;
            color: #e2e8f0;
        }}

        QMessageBox QPushButton,
        QDialog QPushButton {{
            min-width: 90px;
            font-size: {body_font}px;
            padding: {button_padding_y}px {button_padding_x}px;
        }}

        QStatusBar {{
            background-color: #111827;
            color: #cbd5e1;
            border-top: 1px solid #334155;
            font-size: {small_font}px;
        }}

        QToolTip {{
            background-color: #111827;
            color: #f8fafc;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: {small_font}px;
        }}

        QMenu {{
            background-color: #111827;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 6px;
            font-size: {body_font}px;
            color: #e2e8f0;
        }}

        QMenu::item {{
            padding: 10px 24px;
            border-radius: 6px;
        }}

        QMenu::item:selected {{
            background-color: #1e293b;
            color: #f8fafc;
        }}
    """


def _build_focus_override(theme, keyboard_navigation_enabled):
    if not keyboard_navigation_enabled:
        return ""

    focus_color = "#7dd3fc" if theme == "Escuro" else "#2563eb"
    return f"""
        QPushButton:focus,
        QPushButton#btnPrimary:focus,
        QPushButton#btnSecondary:focus,
        QLineEdit:focus,
        QLineEdit#configInput:focus,
        QLineEdit#configInputOnly:focus,
        QLineEdit#configInputReadonly:focus,
        QComboBox:focus,
        QComboBox#configCombo:focus,
        QSpinBox:focus,
        QSpinBox#configSpin:focus,
        QDateEdit:focus,
        QTimeEdit:focus,
        QTextEdit:focus,
        QCheckBox:focus,
        QCheckBox#configCheckbox:focus,
        QTableWidget:focus,
        QListWidget:focus,
        QTabBar::tab:focus {{
            border: 3px solid {focus_color};
            outline: none;
        }}
    """
