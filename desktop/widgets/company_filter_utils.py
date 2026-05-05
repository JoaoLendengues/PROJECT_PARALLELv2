COMPANY_FILTER_PLACEHOLDER = "__select_company__"
COMPANY_FILTER_ALL = "__all_companies__"


def populate_company_filter(combo, companies, selected_value=None):
    current_value = selected_value if selected_value is not None else combo.currentData()

    combo.blockSignals(True)
    combo.clear()
    combo.addItem("Selecione a empresa", COMPANY_FILTER_PLACEHOLDER)
    combo.addItem("Todas as empresas", COMPANY_FILTER_ALL)

    for company in companies:
        if company and str(company).strip():
            combo.addItem(company, company)

    restored_index = combo.findData(current_value)
    combo.setCurrentIndex(restored_index if restored_index >= 0 else 0)
    combo.blockSignals(False)


def company_filter_ready(combo):
    return combo.currentData() not in (None, COMPANY_FILTER_PLACEHOLDER)


def selected_company_value(combo):
    value = combo.currentData()
    if value in (None, COMPANY_FILTER_PLACEHOLDER, COMPANY_FILTER_ALL):
        return None
    return value
