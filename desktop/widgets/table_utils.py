from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QStyledItemDelegate, QTableWidgetItem


class CenteredItemDelegate(QStyledItemDelegate):
    """Delegate simples para centralizar o texto de todas as celulas."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter


def configure_data_table(table, stretch_columns=(), minimum_section_size=120, minimum_widths=None):
    """Aplica o comportamento padrao de grids do desktop."""
    header = table.horizontalHeader()
    header.setDefaultAlignment(Qt.AlignCenter)
    header.setMinimumSectionSize(minimum_section_size)
    header.setSectionsClickable(True)
    header.setHighlightSections(False)
    header.setStretchLastSection(False)
    header.setSectionResizeMode(QHeaderView.Interactive)

    table.setWordWrap(False)
    table.setSortingEnabled(True)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setTextElideMode(Qt.ElideRight)
    table.setItemDelegate(CenteredItemDelegate(table))

    table._pp_stretch_columns = tuple(stretch_columns)
    table._pp_minimum_section_size = int(minimum_section_size)
    table._pp_minimum_widths = {int(column): int(width) for column, width in (minimum_widths or {}).items()}

    refresh_data_table_layout(table)


def refresh_data_table_layout(table):
    """Recalcula larguras das colunas preservando minimos e colunas expansivas."""
    header = table.horizontalHeader()
    stretch_columns = getattr(table, "_pp_stretch_columns", ())
    minimum_section_size = int(getattr(table, "_pp_minimum_section_size", 120))
    minimum_widths = getattr(table, "_pp_minimum_widths", {})

    table.setUpdatesEnabled(False)
    try:
        for column in range(table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)

        table.resizeColumnsToContents()

        for column in range(table.columnCount()):
            target_width = max(header.sectionSize(column), int(minimum_widths.get(column, minimum_section_size)))
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, target_width)

        for column in stretch_columns:
            if 0 <= column < table.columnCount():
                header.setSectionResizeMode(column, QHeaderView.Stretch)
    finally:
        table.setUpdatesEnabled(True)


def number_item(value):
    item = QTableWidgetItem()
    try:
        item.setData(Qt.DisplayRole, int(value))
    except (TypeError, ValueError):
        item.setData(Qt.DisplayRole, str(value))
    return item
