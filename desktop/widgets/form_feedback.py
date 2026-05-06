from PySide6.QtWidgets import QLabel


def required_label(text: str) -> QLabel:
    label = QLabel(f'{text} <span style="color: #ef4444;">*</span>')
    label.setTextFormat(label.textFormat())
    return label


def optional_label(text: str) -> QLabel:
    return QLabel(text)


def required_hint_label() -> QLabel:
    label = QLabel('<span style="color: #ef4444;">*</span> Campos obrigatorios.')
    label.setStyleSheet("font-size: 12px;")
    return label


def focus_invalid_field(widget) -> None:
    if widget is None:
        return
    try:
        widget.setFocus()
    except Exception:
        return

    if hasattr(widget, "selectAll"):
        try:
            widget.selectAll()
        except Exception:
            pass


def required_field_message(field_name: str) -> str:
    return f"Preencha o campo obrigatorio '{field_name}'."
