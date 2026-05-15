from urllib.parse import urlparse

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QSpinBox,
                               QTextEdit, QMessageBox, QHeaderView, QDateEdit, QApplication, QFrame)
from PySide6.QtCore import Qt, QDate, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QColor, QCursor
from api_client import api_client
from access_control import get_action_label, has_action_access
from widgets.company_filter_utils import company_filter_ready, populate_company_filter, selected_company_value
from widgets.form_feedback import focus_invalid_field, optional_label, required_field_message, required_hint_label, required_label
from widgets.toast_notification import notification_manager
from widgets.filter_utils import contains_text, is_all_option, same_filter_value, same_text
from widgets.table_utils import configure_data_table, number_item, refresh_data_table_layout
from user_preferences import (
    apply_table_column_widths,
    apply_combo_data,
    apply_combo_text,
    apply_table_sort_state,
    get_table_column_widths,
    get_table_sort_state,
    get_widget_preferences,
    save_widget_preferences,
)


class PedidosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario = {}
        self.pedidos = []
        self.pedidos_cache = []
        self._visible_pedidos = []
        self.materiais = []
        self.departamentos = []
        self._loaded = False
        self._restoring_preferences = False
        self._saved_preferences = {}
        self._summary_labels = {}
        self.init_ui()

    def on_show(self):
        if not self._loaded:
            self.carregar_departamentos()
            self.carregar_empresas()
            self._carregar_preferencias()
            self._aplicar_preferencias_salvas()
            if self.empresa_pronta():
                empresa = self.empresa_param()
                self.carregar_materiais(empresa=empresa)
                self.carregar_pedidos()
            else:
                self._mostrar_prompt_empresa()
            self._loaded = True

    def showEvent(self, event):
        self._apply_theme_styles()
        super().showEvent(event)

    def _is_dark_theme(self):
        app = QApplication.instance()
        return str(app.property("accessibility_theme") or "Claro") == "Escuro"

    def _theme_colors(self):
        if self._is_dark_theme():
            return {
                "card_bg": "rgba(15, 23, 42, 0.34)",
                "card_border": "rgba(148, 163, 184, 0.16)",
                "title": "#f8fafc",
                "muted": "#94a3b8",
            }
        return {
            "card_bg": "rgba(248, 250, 252, 1.0)",
            "card_border": "rgba(203, 213, 225, 0.9)",
            "title": "#0f172a",
            "muted": "#64748b",
        }

    def _apply_theme_styles(self):
        colors_map = self._theme_colors()
        self.setStyleSheet(
            f"""
            QFrame#orderSummaryCard, QFrame#orderDetailCard {{
                background-color: {colors_map['card_bg']};
                border: 1px solid {colors_map['card_border']};
                border-radius: 16px;
            }}
            QLabel#orderSummaryTitle {{
                color: {colors_map['muted']};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#orderSummaryValue {{
                color: {colors_map['title']};
                font-size: 24px;
                font-weight: 700;
            }}
            QLabel#orderSummaryCaption, QLabel#orderDetailBody {{
                color: {colors_map['muted']};
                font-size: 12px;
            }}
            QLabel#orderDetailTitle {{
                color: {colors_map['title']};
                font-size: 16px;
                font-weight: 700;
            }}
            """
        )

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("📋 Pedidos")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()

        # Botão Novo Pedido
        self.novo_btn = QPushButton("+ Novo Pedido")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.novo_pedido)
        header.addWidget(self.novo_btn)

        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_pedidos)
        header.addWidget(self.atualizar_btn)

        layout.addLayout(header)

        # Barra de pesquisa e filtros
        filtros = QHBoxLayout()

        filtros.addWidget(QLabel("Busca:"))
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setPlaceholderText("Pesquisar por material, solicitante, departamento, link...")
        self.pesquisa_edit.setMaximumWidth(340)
        self.pesquisa_edit.textChanged.connect(self.filtrar_pedidos)
        filtros.addWidget(self.pesquisa_edit)

        filtros.addSpacing(20)

        # Filtro Status
        filtros.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Pendente", "Aprovado", "Concluído", "Cancelado"])
        self.status_filter.currentTextChanged.connect(self.filtrar_pedidos)
        filtros.addWidget(self.status_filter)

        filtros.setSpacing(20)

        # Filtro empresa
        filtros.addWidget(QLabel("Empresa:"))
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(150)
        self.empresa_filter.currentIndexChanged.connect(self.ao_alterar_empresa)
        filtros.addWidget(self.empresa_filter)

        filtros.addSpacing(20)

        # Filtro Departamento
        filtros.addWidget(QLabel('Departamento:'))
        self.departamento_filter = QComboBox()
        self.departamento_filter.setMinimumWidth(150)
        self.departamento_filter.addItem('Todos os departamentos')
        self.departamento_filter.currentTextChanged.connect(self.filtrar_pedidos)
        filtros.addWidget(self.departamento_filter)

        filtros.addStretch()

        layout.addLayout(filtros)

        self.empresa_prompt = QLabel('Selecione uma empresa ou "Todas as empresas" para carregar os pedidos.')
        self.empresa_prompt.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(self.empresa_prompt)

        self.summary_strip = self._create_summary_strip(
            [
                ("total", "Pedidos visiveis", "Base filtrada na grade"),
                ("pendentes", "Pendentes", "Aguardando aprovacao"),
                ("aprovados", "Aprovados", "Prontos para execucao"),
                ("com_link", "Com link", "Links de compra cadastrados"),
            ]
        )
        layout.addWidget(self.summary_strip)

        # Tabela de pedidos com estilo melhorado
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSortingEnabled(True)

        # Estilo da tabela
        self.tabela.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        headers = ["ID", "Material", "Qtd", "Solicitante", "Empresa", "Dept", "Data Solic.", "Data Conclusão", "Status", "Observação"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        headers.insert(9, "Link")
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        configure_data_table(
            self.tabela,
            stretch_columns=(1, 9, 10),
            minimum_section_size=88,
            minimum_widths={
                0: 72,
                1: 220,
                2: 90,
                3: 170,
                4: 170,
                5: 150,
                6: 135,
                7: 150,
                8: 120,
                9: 170,
                10: 240,
            },
        )
        self.tabela.horizontalHeader().sortIndicatorChanged.connect(self._ao_ordenar_tabela)
        self.tabela.horizontalHeader().sectionResized.connect(self._ao_redimensionar_coluna)
        self.tabela.itemSelectionChanged.connect(self._update_detail_from_selection)

        self.detail_card = self._create_detail_panel()
        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)
        content_layout.addWidget(self.tabela, 3)
        content_layout.addWidget(self.detail_card, 1)
        layout.addLayout(content_layout, 1)

        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()

        self.abrir_link_btn = QPushButton("Abrir Link")
        self.abrir_link_btn.clicked.connect(self.abrir_link_pedido)
        acoes.addWidget(self.abrir_link_btn)

        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_pedido)
        acoes.addWidget(self.editar_btn)

        self.aprovar_btn = QPushButton("✓ Aprovar")
        self.aprovar_btn.clicked.connect(self.aprovar_pedido)
        acoes.addWidget(self.aprovar_btn)

        self.concluir_btn = QPushButton("✅ Concluir")
        self.concluir_btn.clicked.connect(self.concluir_pedido)
        acoes.addWidget(self.concluir_btn)

        self.cancelar_btn = QPushButton("✗ Cancelar")
        self.cancelar_btn.clicked.connect(self.cancelar_pedido)
        acoes.addWidget(self.cancelar_btn)

        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_pedido)
        acoes.addWidget(self.deletar_btn)

        layout.addLayout(acoes)
        self.aplicar_permissoes()
        self._apply_theme_styles()
        self._set_detail_empty()

    def set_usuario(self, usuario):
        self.usuario = usuario or {}
        self._carregar_preferencias()
        self.aplicar_permissoes()
        if self._loaded:
            self._aplicar_preferencias_salvas()
            if self.empresa_pronta():
                empresa = self.empresa_param()
                self.carregar_materiais(empresa=empresa)
                self.carregar_pedidos()
            else:
                self._mostrar_prompt_empresa()

    def _pode(self, action_key):
        return has_action_access(self.usuario, action_key)

    def _avisar_sem_permissao(self, action_key):
        QMessageBox.warning(self, "Acesso não permitido", f"Você não tem permissão para {get_action_label(action_key)}.")

    def aplicar_permissoes(self):
        if hasattr(self, "novo_btn"):
            self.novo_btn.setVisible(self._pode("pedidos.create"))
        if hasattr(self, "editar_btn"):
            self.editar_btn.setVisible(self._pode("pedidos.edit"))
        if hasattr(self, "abrir_link_btn"):
            self.abrir_link_btn.setVisible(True)
        if hasattr(self, "aprovar_btn"):
            self.aprovar_btn.setVisible(self._pode("pedidos.approve"))
        if hasattr(self, "concluir_btn"):
            self.concluir_btn.setVisible(self._pode("pedidos.complete"))
        if hasattr(self, "cancelar_btn"):
            self.cancelar_btn.setVisible(self._pode("pedidos.cancel"))
        if hasattr(self, "deletar_btn"):
            self.deletar_btn.setVisible(self._pode("pedidos.delete"))
        if hasattr(self, "detail_open_link_btn") or hasattr(self, "detail_copy_link_btn"):
            pedido = self._pedido_selecionado()
            has_link = bool(pedido and str(pedido.get("link_compra") or "").strip())
            self._set_detail_actions_enabled(self.tabela.currentRow() >= 0, has_link)

    def empresa_pronta(self):
        return company_filter_ready(self.empresa_filter)

    def empresa_param(self):
        return selected_company_value(self.empresa_filter)

    def _carregar_preferencias(self):
        self._saved_preferences = get_widget_preferences(self.usuario, "pedidos")

    def _aplicar_preferencias_salvas(self):
        self._restoring_preferences = True
        try:
            self.pesquisa_edit.setText(str(self._saved_preferences.get("busca") or ""))
            apply_combo_text(self.status_filter, self._saved_preferences.get("status"))
            apply_combo_data(self.empresa_filter, self._saved_preferences.get("empresa"))
            apply_combo_text(self.departamento_filter, self._saved_preferences.get("departamento"))
        finally:
            self._restoring_preferences = False

    def _preferencias_atuais(self):
        return {
            "busca": self.pesquisa_edit.text().strip(),
            "status": self.status_filter.currentText(),
            "empresa": self.empresa_filter.currentData(),
            "departamento": self.departamento_filter.currentText(),
            "sort": get_table_sort_state(self.tabela),
            "widths": get_table_column_widths(self.tabela),
        }

    def _salvar_preferencias(self):
        if self._restoring_preferences:
            return
        self._saved_preferences = self._preferencias_atuais()
        save_widget_preferences(self.usuario, "pedidos", self._saved_preferences)

    def _ao_ordenar_tabela(self, *_args):
        self._salvar_preferencias()

    def _ao_redimensionar_coluna(self, *_args):
        self._salvar_preferencias()

    def _pedido_selecionado(self):
        current_row = self.tabela.currentRow()
        if current_row < 0 or self.tabela.item(current_row, 0) is None:
            return None

        pedido_id = int(self.tabela.item(current_row, 0).text())
        return next((pedido for pedido in self._visible_pedidos if pedido.get("id") == pedido_id), None)

    def _texto_link(self, link_compra):
        link = str(link_compra or "").strip()
        if not link:
            return "-"

        if "://" not in link:
            link = f"https://{link}"

        parsed = urlparse(link)
        return parsed.netloc or "Link salvo"

    def _classificar_link(self, link_compra):
        link = str(link_compra or "").strip()
        if not link:
            return ("Sem link", "-")
        if "://" not in link:
            link = f"https://{link}"
        parsed = urlparse(link)
        dominio = (parsed.netloc or "").lower()
        if not dominio:
            return ("Link invalido", "-")

        conhecidos = {
            "mercadolivre": "Marketplace",
            "amazon": "Marketplace",
            "magazineluiza": "Varejo",
            "kabum": "Tecnologia",
            "terabyteshop": "Tecnologia",
            "pichau": "Tecnologia",
        }
        categoria = next((label for key, label in conhecidos.items() if key in dominio), "Externo")
        return (categoria, dominio)

    def _create_summary_strip(self, specs):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        for key, title, caption in specs:
            card = QFrame()
            card.setObjectName("orderSummaryCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(6)

            title_label = QLabel(title)
            title_label.setObjectName("orderSummaryTitle")

            value_label = QLabel("0")
            value_label.setObjectName("orderSummaryValue")

            caption_label = QLabel(caption)
            caption_label.setObjectName("orderSummaryCaption")
            caption_label.setWordWrap(True)

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            card_layout.addWidget(caption_label)
            layout.addWidget(card, 1)
            self._summary_labels[key] = value_label

        return container

    def _create_detail_panel(self):
        card = QFrame()
        card.setObjectName("orderDetailCard")
        card.setMinimumWidth(320)
        card.setMaximumWidth(390)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel("Detalhes do pedido")
        title.setObjectName("orderDetailTitle")
        layout.addWidget(title)

        self.detail_material = QLabel("")
        self.detail_material.setWordWrap(True)
        self.detail_material.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(self.detail_material)

        self.detail_body = QLabel("")
        self.detail_body.setObjectName("orderDetailBody")
        self.detail_body.setWordWrap(True)
        self.detail_body.setTextFormat(Qt.RichText)
        self.detail_body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.detail_body, 1)

        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self.detail_open_link_btn = QPushButton("Abrir link")
        self.detail_open_link_btn.setMinimumHeight(38)
        self.detail_open_link_btn.clicked.connect(self.abrir_link_pedido)
        actions_layout.addWidget(self.detail_open_link_btn)

        self.detail_copy_link_btn = QPushButton("Copiar link")
        self.detail_copy_link_btn.setMinimumHeight(38)
        self.detail_copy_link_btn.clicked.connect(self.copiar_link_pedido)
        actions_layout.addWidget(self.detail_copy_link_btn)

        layout.addLayout(actions_layout)
        return card

    def _set_summary_value(self, key, value):
        label = self._summary_labels.get(key)
        if label is not None:
            label.setText(str(value))

    def _update_summary(self, pedidos):
        total = len(pedidos)
        pendentes = sum(1 for pedido in pedidos if str(pedido.get("status", "")).lower() == "pendente")
        aprovados = sum(1 for pedido in pedidos if str(pedido.get("status", "")).lower() == "aprovado")
        com_link = sum(1 for pedido in pedidos if str(pedido.get("link_compra") or "").strip())
        self._set_summary_value("total", total)
        self._set_summary_value("pendentes", pendentes)
        self._set_summary_value("aprovados", aprovados)
        self._set_summary_value("com_link", com_link)

    def _set_detail_empty(self):
        if hasattr(self, "detail_material"):
            self.detail_material.setText("Selecione um pedido")
        if hasattr(self, "detail_body"):
            self.detail_body.setText(
                "Escolha um item na grade para ver solicitante, empresa, dominio do link e o contexto da compra."
            )
        self._set_detail_actions_enabled(False)

    def _set_detail_actions_enabled(self, enabled, has_link=False):
        if hasattr(self, "detail_open_link_btn"):
            self.detail_open_link_btn.setEnabled(enabled and has_link)
        if hasattr(self, "detail_copy_link_btn"):
            self.detail_copy_link_btn.setEnabled(enabled and has_link)

    def _update_detail_from_selection(self):
        pedido = self._pedido_selecionado()
        if not pedido:
            self._set_detail_empty()
            return

        categoria_link, dominio = self._classificar_link(pedido.get("link_compra"))
        self.detail_material.setText(pedido.get("material_nome", "Pedido"))
        detalhe = (
            f"<b>Pedido:</b> #{pedido.get('id', '-')}<br>"
            f"<b>Quantidade:</b> {pedido.get('quantidade', '-')}<br>"
            f"<b>Solicitante:</b> {pedido.get('solicitante', '-') or '-'}<br>"
            f"<b>Empresa:</b> {pedido.get('empresa', '-') or '-'}<br>"
            f"<b>Departamento:</b> {pedido.get('departamento', '-') or '-'}<br>"
            f"<b>Status:</b> {str(pedido.get('status', '-') or '-').upper()}<br>"
            f"<b>Data de solicitacao:</b> {pedido.get('data_solicitacao', '-') or '-'}<br>"
            f"<b>Data de conclusao:</b> {pedido.get('data_conclusao', '-') or '-'}<br>"
            f"<b>Categoria do link:</b> {categoria_link}<br>"
            f"<b>Dominio:</b> {dominio}<br>"
            f"<b>Observacao:</b><br>{(pedido.get('observacao') or '-')}"
        )
        self.detail_body.setText(detalhe)
        self._set_detail_actions_enabled(True, bool(str(pedido.get("link_compra") or "").strip()))

    def _mostrar_prompt_empresa(self):
        self.pedidos = []
        self.pedidos_cache = []
        self.tabela.setRowCount(0)
        self.empresa_prompt.setVisible(True)

    def ao_alterar_empresa(self):
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            self._salvar_preferencias()
            return
        empresa = self.empresa_param()
        self.carregar_materiais(empresa=empresa)
        self.carregar_pedidos()
        self._salvar_preferencias()

    def carregar_materiais(self, empresa=None):
        """Carrega a lista de materiais"""
        try:
            self.materiais = api_client.listar_materiais_para_pedido(empresa=empresa)
        except Exception as e:
            print(f"Erro ao carregar materiais: {e}")

    def carregar_departamentos(self):
        """Carrega a lista de departamentos do backend para filtro"""
        try:
            self.departamentos = api_client.get_departamentos_lista()
            self.departamento_filter.clear()
            self.departamento_filter.addItem('Todos os departamentos')
            for dept in self.departamentos:
                if dept and dept.strip():
                    self.departamento_filter.addItem(dept)
            print(f'✅ Departamentos carregados para filtro: {len(self.departamentos)}')
        except Exception as e:
            print(f'❌ Erro ao carregar empresas: {e}')

    def carregar_empresas(self):
        """Carrega a lista de empresas do backend para filtro"""
        try:
            self.empresas = api_client.get_empresas()
            populate_company_filter(self.empresa_filter, self.empresas)
            print(f'✅ Empresas carregadas para filtro: {len(self.empresas)}')
        except Exception as e:
            print(f'❌ Erro ao carregar empresas> {e}')

    def carregar_pedidos(self):
        """Carrega a lista de pedidos do backend"""
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        try:
            self.pedidos = api_client.listar_pedidos(empresa=self.empresa_param())
            self.pedidos_cache = self.pedidos.copy()
            self.filtrar_pedidos()
            self.empresa_prompt.setVisible(False)
            print(f"✅ Pedidos carregados: {len(self.pedidos)}")
        except Exception as e:
            print(f"❌ Erro ao carregar pedidos: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar pedidos: {e}")

    def filtrar_pedidos(self):
        """Filtra os pedidos com base nos filtros"""
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        status = self.status_filter.currentText()
        empresa = self.empresa_filter.currentText()
        departamento = self.departamento_filter.currentText()
        search_text = self.pesquisa_edit.text()

        filtered = []
        for pedido in self.pedidos:
            # Filtro por status
            if not is_all_option(status) and not same_filter_value(pedido.get("status", ""), status):
                continue

            # Filtro por empresa
            if self.empresa_param() is None and not is_all_option(empresa) and not same_text(pedido.get("empresa"), empresa):
                continue

            # Filtro por departamento
            if not is_all_option(departamento) and not same_text(pedido.get('departamento'), departamento):
                continue

            if not contains_text(
                search_text,
                pedido.get("id", ""),
                pedido.get("material_nome", ""),
                pedido.get("solicitante", ""),
                pedido.get("empresa", ""),
                pedido.get("departamento", ""),
                pedido.get("status", ""),
                pedido.get("observacao", ""),
                pedido.get("link_compra", ""),
            ):
                continue

            filtered.append(pedido)

        self.atualizar_tabela(filtered)
        self._salvar_preferencias()

    def atualizar_tabela(self, pedidos):
        """Atualiza a tabela com a lista de pedidos"""
        self._visible_pedidos = list(pedidos)
        sorting_enabled = self.tabela.isSortingEnabled()
        self.tabela.setSortingEnabled(False)
        self.tabela.clearSelection()
        self.tabela.clearContents()
        self.tabela.setRowCount(len(pedidos))

        status_colors = {
            "pendente": QColor(244, 162, 97),
            "aprovado": QColor(42, 157, 143),
            "concluido": QColor(44, 125, 160),
            "cancelado": QColor(231, 111, 81)
        }

        for row, pedido in enumerate(pedidos):
            self.tabela.setItem(row, 0, number_item(pedido.get("id", "")))
            self.tabela.setItem(row, 1, QTableWidgetItem(pedido.get("material_nome", "-")))
            self.tabela.setItem(row, 2, number_item(pedido.get("quantidade", 0)))
            self.tabela.setItem(row, 3, QTableWidgetItem(pedido.get("solicitante", "-")))
            self.tabela.setItem(row, 4, QTableWidgetItem(pedido.get("empresa", "-")))
            self.tabela.setItem(row, 5, QTableWidgetItem(pedido.get("departamento", "-")))
            self.tabela.setItem(row, 6, QTableWidgetItem(pedido.get("data_solicitacao", "-")))
            self.tabela.setItem(row, 7, QTableWidgetItem(pedido.get("data_conclusao", "-") or "-"))

            status_item = QTableWidgetItem(pedido.get("status", "pendente").upper())
            status_color = status_colors.get(pedido.get("status", "pendente"), QColor(0, 0, 0))
            status_item.setForeground(status_color)
            self.tabela.setItem(row, 8, status_item)

            link_item = QTableWidgetItem(self._texto_link(pedido.get("link_compra")))
            link_item.setToolTip(pedido.get("link_compra") or "")
            self.tabela.setItem(row, 9, link_item)

            self.tabela.setItem(row, 10, QTableWidgetItem(str(pedido.get("observacao") or "-")[:50]))

        if sorting_enabled:
            self.tabela.setSortingEnabled(True)

        apply_table_sort_state(self.tabela, self._saved_preferences.get("sort"))
        refresh_data_table_layout(self.tabela)
        apply_table_column_widths(self.tabela, self._saved_preferences.get("widths"))
        self._update_summary(pedidos)
        if pedidos:
            self.tabela.selectRow(0)
            self._update_detail_from_selection()
        else:
            self._set_detail_empty()

    def novo_pedido(self):
        if not self._pode("pedidos.create"):
            self._avisar_sem_permissao("pedidos.create")
            return
        if not self.empresa_pronta():
            QMessageBox.warning(self, "Atenção", "Selecione uma empresa antes de registrar pedidos.")
            return
        dialog = PedidoDialog(materiais=self.materiais, empresa_padrao=self.empresa_param(), parent=self)
        if dialog.exec():
            self.carregar_pedidos()
            self.carregar_materiais(empresa=self.empresa_param())
    def editar_pedido(self):
        if not self._pode("pedidos.edit"):
            self._avisar_sem_permissao("pedidos.edit")
            return
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para editar")
            return

        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido = next((p for p in self.pedidos if p["id"] == pedido_id), None)

        if pedido:
            dialog = PedidoDialog(
                pedido_data=pedido,
                materiais=self.materiais,
                empresa_padrao=self.empresa_param(),
                parent=self,
            )
            if dialog.exec():
                self.carregar_pedidos()
                self.carregar_materiais(empresa=self.empresa_param())

    def abrir_link_pedido(self):
        pedido = self._pedido_selecionado()
        if not pedido:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para abrir o link.")
            return

        link_compra = str(pedido.get("link_compra") or "").strip()
        if not link_compra:
            QMessageBox.information(self, "Sem link", "Esse pedido ainda não possui link de compra cadastrado.")
            return

        url = QUrl.fromUserInput(link_compra)
        if not url.isValid():
            QMessageBox.warning(self, "Link inválido", "O link salvo para este pedido não pode ser aberto.")
            return

        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(self, "Erro", "Não foi possível abrir o link de compra.")

    def copiar_link_pedido(self):
        pedido = self._pedido_selecionado()
        if not pedido:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para copiar o link.")
            return

        link_compra = str(pedido.get("link_compra") or "").strip()
        if not link_compra:
            QMessageBox.information(self, "Sem link", "Esse pedido ainda não possui link de compra cadastrado.")
            return

        QApplication.clipboard().setText(link_compra)
        notification_manager.success("Link de compra copiado.", self.window(), 2200)

    def aprovar_pedido(self):
        if not self._pode("pedidos.approve"):
            self._avisar_sem_permissao("pedidos.approve")
            return
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para aprovar")
            return

        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido = next((p for p in self.pedidos if p["id"] == pedido_id), None)

        if not pedido:
            return

        if pedido.get("status") != "pendente":
            QMessageBox.warning(self, "Atenção", "Apenas pedidos pendentes podem ser aprovados!")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar aprovação",
            f"Deseja aprovar o pedido de {pedido.get('quantidade')} unidade(s) de '{pedido.get('material_nome')}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                if api_client.aprovar_pedido(pedido_id):
                    QMessageBox.information(self, "Sucesso", "Pedido aprovado com sucesso!")
                    self.carregar_pedidos()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao aprovar pedido")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao aprovar: {e}")

    def concluir_pedido(self):
        """Conclui o pedido selecionado"""
        if not self._pode("pedidos.complete"):
            self._avisar_sem_permissao("pedidos.complete")
            return
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para concluir")
            return

        # Buscar os dados diretamente da tabela
        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido_material = self.tabela.item(current_row, 1).text()
        pedido_qtd = self.tabela.item(current_row, 2).text()
        pedido_status = self.tabela.item(current_row, 8).text().lower()

        # Verificar se o pedido está aprovado
        if pedido_status != 'aprovado':
            QMessageBox.warning(
                self,
                "Atenção",
                f"Este pedido está com status '{pedido_status.upper()}'. Apenas pedidos APROVADOS podem ser concluídos."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar conclusão",
            f"Deseja concluir o pedido de {pedido_qtd} unidade(s) de '{pedido_material}'?\n\n"
            f"⚠️ Esta ação irá atualizar o estoque e não poderá ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                # Mostrar cursor de espera
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

                success = api_client.concluir_pedido(pedido_id)

                QApplication.restoreOverrideCursor()

                if success:
                    notification_manager.success("Pedido concluído com sucesso! Estoque atualizado.", self.window(), 3000)
                    self.carregar_pedidos()  # Recarregar a lista
                else:
                    notification_manager.error("Erro ao concluir pedido. Verifique o estoque.", self.window(), 3000)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Erro", f"Erro ao concluir pedido: {e}")

    def cancelar_pedido(self):
        if not self._pode("pedidos.cancel"):
            self._avisar_sem_permissao("pedidos.cancel")
            return
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para cancelar")
            return

        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido = next((p for p in self.pedidos if p["id"] == pedido_id), None)

        if not pedido:
            return

        if pedido.get("status") not in ["pendente", "aprovado"]:
            QMessageBox.warning(self, "Atenção", "Apenas pedidos pendentes ou aprovados podem ser cancelados!")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar cancelamento",
            f"Deseja cancelar o pedido de {pedido.get('quantidade')} unidade(s) de '{pedido.get('material_nome')}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                if api_client.cancelar_pedido(pedido_id):
                    QMessageBox.information(self, "Sucesso", "Pedido cancelado com sucesso!")
                    self.carregar_pedidos()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao cancelar pedido")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cancelar: {e}")

    def deletar_pedido(self):
        if not self._pode("pedidos.delete"):
            self._avisar_sem_permissao("pedidos.delete")
            return
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para deletar")
            return

        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido_desc = self.tabela.item(current_row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar o pedido de '{pedido_desc}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                if api_client.deletar_pedido(pedido_id):
                    QMessageBox.information(self, "Sucesso", "Pedido deletado com sucesso!")
                    self.carregar_pedidos()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao deletar pedido")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


class PedidoDialog(QDialog):
    def __init__(self, pedido_data=None, materiais=None, empresa_padrao=None, parent=None):
        super().__init__(parent)
        self.dados_item = pedido_data
        self.materiais = materiais or []
        self.empresa_padrao = empresa_padrao
        self.setWindowTitle("Novo Pedido" if not pedido_data else "Editar Pedido")
        self.setModal(True)
        self.setMinimumWidth(550)

        # Estilo do diálogo
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        self.init_ui()

        if pedido_data:
            self.carregar_dados_edicao()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        layout.addWidget(required_hint_label())

        # Material - AGORA COM CAMPO DE TEXTO LIVRE E BOTÃO PARA CADASTRAR
        material_layout = QHBoxLayout()

        self.material_edit = QLineEdit()
        self.material_edit.setPlaceholderText("Digite o nome do material ou selecione um existente")
        self.material_edit.setMinimumWidth(300)
        material_layout.addWidget(self.material_edit)

        self.material_combo = QComboBox()
        self.material_combo.setEditable(False)
        self.material_combo.setInsertPolicy(QComboBox.NoInsert)
        self.material_combo.addItem("-- Selecione um material existente --")
        for mat in self.materiais:
            self.material_combo.addItem(
                f"{mat.get('nome', '')} - Estoque: {mat.get('quantidade', 0)}",
                mat.get("id")
            )
        self.material_combo.currentIndexChanged.connect(self.on_material_selecionado)
        material_layout.addWidget(self.material_combo)

        self.novo_material_btn = QPushButton("+ Novo Material")
        self.novo_material_btn.clicked.connect(self.cadastrar_novo_material)
        material_layout.addWidget(self.novo_material_btn)

        form_layout.addRow(required_label("Material:"), material_layout)

        # ID do material (oculto, para quando for material existente)
        self.material_id_edit = QLineEdit()
        self.material_id_edit.setVisible(False)
        form_layout.addRow("", self.material_id_edit)

        # Quantidade
        self.quantidade_spin = QSpinBox()
        self.quantidade_spin.setRange(1, 99999)
        self.quantidade_spin.setValue(1)
        form_layout.addRow(required_label("Quantidade:"), self.quantidade_spin)

        # Solicitante
        self.solicitante_edit = QLineEdit()
        self.solicitante_edit.setPlaceholderText("Nome do solicitante")
        form_layout.addRow(required_label("Solicitante:"), self.solicitante_edit)

        # Empresa
        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_empresas_combo()
        form_layout.addRow(required_label("Empresa:"), self.empresa_combo)

        # Departamento
        self.departamento_combo = QComboBox()
        self.departamento_combo.setEditable(False)
        self.departamento_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_departamentos_combo()
        form_layout.addRow(required_label("Departamento:"), self.departamento_combo)

        # Status (só aparece na edição)
        self.status_label = QLabel("Status:")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pendente", "aprovado", "concluido", "cancelado"])
        self.status_label.setVisible(False)
        self.status_combo.setVisible(False)
        form_layout.addRow(self.status_label, self.status_combo)

        # Observação
        self.observacao_edit = QTextEdit()
        self.observacao_edit.setMaximumHeight(80)
        self.observacao_edit.setPlaceholderText("Observações adicionais...")
        form_layout.addRow("Observação:", self.observacao_edit)

        self.link_compra_edit = QLineEdit()
        self.link_compra_edit.setPlaceholderText("https://www.mercadolivre.com.br/... ou www.amazon.com.br/...")
        form_layout.addRow("Link de compra:", self.link_compra_edit)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.salvar_btn = QPushButton("Salvar")
        self.salvar_btn.clicked.connect(self.salvar)

        cancelar_btn = QPushButton("Cancelar")
        cancelar_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.salvar_btn)
        btn_layout.addWidget(cancelar_btn)

        layout.addLayout(btn_layout)

    def carregar_empresas_combo(self):
        """Carrega as empresas do backend para o combobox"""
        try:
            empresas = api_client.get_empresas()
            self.empresa_combo.clear()
            for emp in empresas:
                if emp and emp.strip():
                    self.empresa_combo.addItem(emp)
        except Exception as e:
            print(f'❌ Erro ao carregar empresas: {e}')
            # Fallback
            default_empresas = ["Matriz", "Filial 1", "Filial 2", "Filial 3"]
            for emp in default_empresas:
                self.empresa_combo.addItem(emp)

        if self.empresa_padrao:
            indice = self.empresa_combo.findText(str(self.empresa_padrao))
            if indice >= 0:
                self.empresa_combo.setCurrentIndex(indice)

    def carregar_departamentos_combo(self):
        """Carrega os departamentos do backend para o combobox"""
        try:
            departamentos = api_client.get_departamentos_lista()
            self.departamento_combo.clear()
            # ✅ Adiciona apenas os departamentos do backend
            for dept in departamentos:
                if dept and dept.strip():
                    self.departamento_combo.addItem(dept)

            # ✅ Se ainda estiver vazio, usa fallback
            if self.departamento_combo.count() == 0:
                default_depts = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"]
                for dept in default_depts:
                    self.departamento_combo.addItem(dept)

        except Exception as e:
            print(f"❌ Erro ao carregar departamentos: {e}")
            # Fallback em caso de erro
            default_depts = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"]
            for dept in default_depts:
                self.departamento_combo.addItem(dept)

    def on_material_selecionado(self, index):
        """Quando um material existente é selecionado no combo"""
        if index > 0:  # Primeiro item é o placeholder
            material = self.materiais[index - 1]
            self.material_edit.setText(material.get("nome", ""))
            self.material_id_edit.setText(str(material.get("id", "")))
        else:
            self.material_edit.setText("")
            self.material_id_edit.setText("")

    def cadastrar_novo_material(self):
        """Abre diálogo para cadastrar um novo material rapidamente"""
        from widgets.materiais_widget import MaterialDialog

        dialog = MaterialDialog(parent=self)
        if dialog.exec():
            # Recarregar a lista de materiais
            self.carregar_materiais_novos()
            # Selecionar o material recém-criado
            novo_material_nome = dialog.nome_edit.text() if hasattr(dialog, 'nome_edit') else ""
            self.material_edit.setText(novo_material_nome)
            self.material_id_edit.setText("")  # Será buscado pelo nome ao salvar

    def carregar_materiais_novos(self, empresa=None):
        """Recarrega a lista de materiais"""
        try:
            empresa_escolhida = empresa if empresa is not None else self.empresa_combo.currentText()
            self.materiais = api_client.listar_materiais_para_pedido(empresa=empresa_escolhida)
            self.material_combo.clear()
            self.material_combo.addItem("-- Selecione um material existente --")
            for mat in self.materiais:
                self.material_combo.addItem(
                    f"{mat.get('nome', '')} - Estoque: {mat.get('quantidade', 0)} - {mat.get('empresa', '')}",
                    mat.get("id")
                )
        except Exception as e:
            print(f"Erro ao recarregar materiais: {e}")

    def carregar_dados_edicao(self):
        """Carrega os dados do pedido para edição"""
        if self.dados_item is None:
            return

        # Mostrar campo de status na edição
        self.status_label.setVisible(True)
        self.status_combo.setVisible(True)

        # Material
        material_id = self.dados_item.get("material_id")
        material_nome = self.dados_item.get("material_nome", "")

        # Procurar o material na lista
        encontrado = False
        for i, mat in enumerate(self.materiais):
            if mat.get("id") == material_id:
                self.material_combo.setCurrentIndex(i + 1)  # +1 por causa do placeholder
                encontrado = True
                break

        if not encontrado:
            self.material_edit.setText(material_nome)
            self.material_id_edit.setText(str(material_id) if material_id else "")

        # Quantidade
        self.quantidade_spin.setValue(self.dados_item.get("quantidade", 1))

        # Solicitante
        self.solicitante_edit.setText(str(self.dados_item.get("solicitante", "")))

        # Empresa
        empresa = str(self.dados_item.get("empresa", ""))
        idx = self.empresa_combo.findText(empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)

        # Departamento
        departamento = str(self.dados_item.get("departamento", ""))
        idx = self.departamento_combo.findText(departamento)
        if idx >= 0:
            self.departamento_combo.setCurrentIndex(idx)

        # Status
        status = str(self.dados_item.get("status", "pendente"))
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        # Observação
        self.observacao_edit.setPlainText(str(self.dados_item.get("observacao", "")))
        self.link_compra_edit.setText(str(self.dados_item.get("link_compra", "") or ""))

    def normalizar_link_compra(self, link_compra):
        valor = str(link_compra or "").strip()
        if not valor:
            return None

        if "://" not in valor:
            valor = f"https://{valor}"

        parsed = urlparse(valor)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None

        return parsed.geturl()

    def salvar(self):
        # Obter o material
        material_nome = self.material_edit.text().strip()
        material_id = self.material_id_edit.text().strip()

        if not material_nome:
            focus_invalid_field(self.material_edit)
            QMessageBox.warning(self, "Atenção", "Informe o nome do material!")
            return

        quantidade = self.quantidade_spin.value()
        solicitante = self.solicitante_edit.text().strip()
        empresa = self.empresa_combo.currentText()
        departamento = self.departamento_combo.currentText()
        observacao = self.observacao_edit.toPlainText().strip()
        link_compra = self.link_compra_edit.text().strip()
        link_normalizado = self.normalizar_link_compra(link_compra)

        if link_compra and not link_normalizado:
            focus_invalid_field(self.link_compra_edit)
            QMessageBox.warning(self, "Atenção", "Informe um link de compra válido.")
            return

        if not solicitante:
            focus_invalid_field(self.solicitante_edit)
            QMessageBox.warning(self, "Atenção", "Informe o nome do solicitante!")
            return

        if not empresa:
            focus_invalid_field(self.empresa_combo)
            QMessageBox.warning(self, "Atenção", "Selecione uma empresa!")
            return

        # Verificar se o material já existe no banco
        material_existente = None
        for mat in self.materiais:
            if mat.get("nome", "").lower() == material_nome.lower():
                material_existente = mat
                break

        # Preparar dados do pedido
        dados = {
            "quantidade": quantidade,
            "solicitante": solicitante,
            "empresa": empresa,
            "departamento": departamento or None,
            "observacao": observacao or None,
            "link_compra": link_normalizado,
        }

        if material_existente:
            # Material existe, usar o ID
            dados["material_id"] = material_existente.get("id")
        else:
            # Material não existe, enviar o nome para o backend criar
            dados["material_nome"] = material_nome

        # Se for edição, incluir status
        if self.dados_item:
            dados["status"] = self.status_combo.currentText()

        try:
            if self.dados_item:
                # Atualizar
                response = api_client.atualizar_pedido(self.dados_item["id"], dados)
                if response:
                    QMessageBox.information(self, "Sucesso", f"Pedido de '{material_nome}' atualizado com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível atualizar o pedido. Revise os dados e tente novamente.")
            else:
                # Criar
                response = api_client.criar_pedido(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", f"Pedido de '{material_nome}' criado com sucesso.")
                    # Recarregar materiais para incluir o novo material
                    self.carregar_materiais_novos(empresa=empresa)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível criar o pedido. Revise os dados e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o pedido.\n\nDetalhes: {e}")
