import json
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt

from app_paths import get_user_preferences_path
from widgets.filter_utils import normalize_text


def _sort_order_to_int(order: Any) -> int:
    if hasattr(order, "value"):
        try:
            return int(order.value)
        except Exception:
            pass

    try:
        return int(order)
    except Exception:
        return 0


def _load_all_preferences() -> Dict[str, Dict[str, dict]]:
    path = get_user_preferences_path()
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    return data if isinstance(data, dict) else {}


def _save_all_preferences(data: Dict[str, Dict[str, dict]]) -> bool:
    path = get_user_preferences_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        return False
    return True


def _get_user_key(usuario: Optional[dict]) -> Optional[str]:
    usuario = usuario or {}
    codigo = str(usuario.get("codigo") or "").strip()
    if codigo:
        return f"codigo:{codigo}"

    usuario_id = usuario.get("id")
    if usuario_id is not None:
        return f"id:{usuario_id}"

    nome = str(usuario.get("nome") or "").strip().lower()
    if nome:
        return f"nome:{nome}"

    return None


def get_widget_preferences(usuario: Optional[dict], widget_key: str) -> dict:
    user_key = _get_user_key(usuario)
    if not user_key:
        return {}

    all_preferences = _load_all_preferences()
    user_preferences = all_preferences.get(user_key, {})
    widget_preferences = user_preferences.get(widget_key, {})
    return widget_preferences if isinstance(widget_preferences, dict) else {}


def save_widget_preferences(usuario: Optional[dict], widget_key: str, preferences: dict) -> bool:
    user_key = _get_user_key(usuario)
    if not user_key:
        return False

    all_preferences = _load_all_preferences()
    user_preferences = all_preferences.setdefault(user_key, {})
    user_preferences[widget_key] = preferences or {}
    return _save_all_preferences(all_preferences)


def apply_combo_text(combo, value: Optional[str]) -> bool:
    if value is None:
        return False

    value_text = str(value)
    index = combo.findText(value_text)
    if index < 0:
        normalized_value = normalize_text(value_text)
        for combo_index in range(combo.count()):
            if normalize_text(combo.itemText(combo_index)) == normalized_value:
                index = combo_index
                break
    if index < 0:
        return False

    combo.setCurrentIndex(index)
    return True


def apply_combo_data(combo, value: Any) -> bool:
    index = combo.findData(value)
    if index < 0:
        return False

    combo.setCurrentIndex(index)
    return True


def get_table_sort_state(table) -> dict:
    header = table.horizontalHeader()
    section = header.sortIndicatorSection()
    if section is None or section < 0:
        return {}

    return {
        "column": int(section),
        "order": _sort_order_to_int(header.sortIndicatorOrder()),
    }


def apply_table_sort_state(table, state: Optional[dict]) -> bool:
    if not state:
        return False

    column = state.get("column")
    ascending_order = _sort_order_to_int(Qt.AscendingOrder)
    order_value = _sort_order_to_int(state.get("order", ascending_order))
    if not isinstance(column, int) or column < 0 or column >= table.columnCount():
        return False

    order = Qt.AscendingOrder if order_value == ascending_order else Qt.DescendingOrder
    table.horizontalHeader().setSortIndicator(column, order)
    table.sortItems(column, order)
    return True
