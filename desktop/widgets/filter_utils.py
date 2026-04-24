import unicodedata


def normalize_text(value):
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text.strip().lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.split())


def filter_value(value):
    text = normalize_text(value)
    aliases = {
        "em andamento": "andamento",
    }
    return aliases.get(text, text)


def is_all_option(value):
    text = normalize_text(value)
    return text in {"todos", "todas"} or text.startswith("todos os") or text.startswith("todas as")


def same_filter_value(left, right):
    return filter_value(left) == filter_value(right)


def same_text(left, right):
    return normalize_text(left) == normalize_text(right)


def contains_text(needle, *values):
    normalized_needle = normalize_text(needle)
    if not normalized_needle:
        return True
    return any(normalized_needle in normalize_text(value) for value in values)
