from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QStyledItemDelegate, QTableWidgetItem


class CenteredItemDelegate(QStyledItemDelegate):
    """Delegate simples para centralizar o texto de todas as celulas."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter


def configure_data_table(table, stretch_columns=(), minimum_section_size=120):
    """Aplica o comportamento padrao de grids do desktop."""
    header = table.horizontalHeader()
    header.setDefaultAlignment(Qt.AlignCenter)
    header.setSectionResizeMode(QHeaderView.ResizeToContents)
    header.setMinimumSectionSize(minimum_section_size)
    header.setSectionsClickable(True)
    header.setHighlightSections(False)
    header.setStretchLastSection(False)

    table.setWordWrap(True)
    table.setSortingEnabled(True)
    table.setItemDelegate(CenteredItemDelegate(table))

    for column in stretch_columns:
        header.setSectionResizeMode(column, QHeaderView.Stretch)


def number_item(value):
    item = QTableWidgetItem()
    try:
        item.setData(Qt.DisplayRole, int(value))
    except (TypeError, ValueError):
        item.setData(Qt.DisplayRole, str(value))
    return item
