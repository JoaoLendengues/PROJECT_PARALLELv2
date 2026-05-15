from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from access_control import (
    ROLE_REQUESTER,
    get_action_label,
    has_action_access,
    normalize_access_level,
)
from api_client import api_client
from widgets.company_filter_utils import (
    company_filter_ready,
    populate_company_filter,
    selected_company_value,
)
from widgets.form_feedback import focus_invalid_field, optional_label, required_field_message, required_hint_label, required_label
from widgets.filter_utils import is_all_option, same_filter_value
from widgets.filter_utils import contains_text
from widgets.table_utils import configure_data_table, number_item, refresh_data_table_layout
from user_preferences import (
    apply_combo_data,
    apply_combo_text,
    apply_table_column_widths,
    apply_table_sort_state,
    get_table_column_widths,
    get_table_sort_state,
    get_widget_preferences,
    save_widget_preferences,
)


class DemandasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario = {}
        self.demandas = []
        self.empresas = []
        self._visible_demandas = []
        self._loaded = False
        self._modo_solicitante = False
        self._restoring_preferences = False
        self._saved_preferences = {}
        self._summary_labels = {}
        self.init_ui()

    def on_show(self):
        if not self._loaded:
            self.carregar_empresas()
            self._carregar_preferencias()
            self._aplicar_preferencias_salvas()
            self._loaded = True

        if self._modo_solicitante:
            self.carregar_demandas()
        elif self.empresa_pronta():
            self.carregar_demandas()
        else:
            self._mostrar_prompt_empresa()

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
            QFrame#demandSummaryCard, QFrame#demandDetailCard {{
                background-color: {colors_map['card_bg']};
                border: 1px solid {colors_map['card_border']};
                border-radius: 16px;
            }}
            QLabel#demandSummaryTitle {{
                color: {colors_map['muted']};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#demandSummaryValue {{
                color: {colors_map['title']};
                font-size: 24px;
                font-weight: 700;
            }}
            QLabel#demandSummaryCaption, QLabel#demandDetailBody {{
                color: {colors_map['muted']};
                font-size: 12px;
            }}
            QLabel#demandDetailTitle {{
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

        header = QHBoxLayout()
        self.titulo_label = QLabel("Demandas / Chamados TI")
        self.titulo_label.setProperty("class", "page-title")
        header.addWidget(self.titulo_label)
        header.addStretch()

        self.novo_btn = QPushButton("+ Nova Demanda")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.nova_demanda)
        header.addWidget(self.novo_btn)

        self.atualizar_btn = QPushButton("Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_demandas)
        header.addWidget(self.atualizar_btn)

        layout.addLayout(header)

        filtros = QHBoxLayout()

        self.busca_label = QLabel("Busca:")
        filtros.addWidget(self.busca_label)
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setPlaceholderText("Pesquisar por título, descrição, status ou responsável...")
        self.pesquisa_edit.setMaximumWidth(340)
        self.pesquisa_edit.textChanged.connect(self.filtrar_demandas)
        filtros.addWidget(self.pesquisa_edit)

        filtros.addSpacing(20)

        self.status_label = QLabel("Status:")
        filtros.addWidget(self.status_label)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Aberto", "Em Andamento", "Concluído", "Cancelado"])
        self.status_filter.currentTextChanged.connect(self.filtrar_demandas)
        filtros.addWidget(self.status_filter)

        self.empresa_label = QLabel("Empresa:")
        filtros.addWidget(self.empresa_label)
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(170)
        self.empresa_filter.currentIndexChanged.connect(self.ao_alterar_empresa)
        filtros.addWidget(self.empresa_filter)

        self.prioridade_label = QLabel("Prioridade:")
        filtros.addWidget(self.prioridade_label)
        self.prioridade_filter = QComboBox()
        self.prioridade_filter.addItems(["Todas", "Alta", "Media", "Baixa"])
        self.prioridade_filter.currentTextChanged.connect(self.filtrar_demandas)
        filtros.addWidget(self.prioridade_filter)

        filtros.addStretch()
        layout.addLayout(filtros)

        self.empresa_prompt = QLabel("Selecione uma empresa ou 'Todas as empresas' para carregar as demandas.")
        self.empresa_prompt.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(self.empresa_prompt)

        self.summary_strip = self._create_summary_strip(
            [
                ("total", "Demandas visiveis", "Base filtrada na grade"),
                ("abertas", "Abertas", "Aguardando andamento"),
                ("andamento", "Em andamento", "Ja assumidas"),
                ("criticas", "Criticas", "Alta prioridade ou urgencia"),
            ]
        )
        layout.addWidget(self.summary_strip)

        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setStyleSheet(
            """
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
            """
        )
        self.detail_card = self._create_detail_panel()
        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)
        content_layout.addWidget(self.tabela, 3)
        content_layout.addWidget(self.detail_card, 1)
        layout.addLayout(content_layout, 1)

        acoes = QHBoxLayout()
        acoes.addStretch()

        self.ver_btn = QPushButton("Ver Detalhes")
        self.ver_btn.clicked.connect(self.ver_demanda)
        acoes.addWidget(self.ver_btn)

        self.assumir_btn = QPushButton("Assumir para mim")
        self.assumir_btn.clicked.connect(self.assumir_demanda)
        acoes.addWidget(self.assumir_btn)

        self.editar_btn = QPushButton("Editar")
        self.editar_btn.clicked.connect(self.editar_demanda)
        acoes.addWidget(self.editar_btn)

        self.concluir_btn = QPushButton("Concluir")
        self.concluir_btn.clicked.connect(self.concluir_demanda)
        acoes.addWidget(self.concluir_btn)

        self.cancelar_btn = QPushButton("Cancelar")
        self.cancelar_btn.clicked.connect(self.cancelar_demanda)
        acoes.addWidget(self.cancelar_btn)

        self.deletar_btn = QPushButton("Deletar")
        self.deletar_btn.clicked.connect(self.deletar_demanda)
        acoes.addWidget(self.deletar_btn)

        layout.addLayout(acoes)

        self._configurar_colunas_tabela()
        self.tabela.horizontalHeader().sortIndicatorChanged.connect(self._ao_ordenar_tabela)
        self.tabela.horizontalHeader().sectionResized.connect(self._ao_redimensionar_coluna)
        self.tabela.itemSelectionChanged.connect(self._update_detail_from_selection)
        self.aplicar_permissoes()
        self.aplicar_modo_usuario()
        self._apply_theme_styles()
        self._set_detail_empty()

    def set_usuario(self, usuario):
        self.usuario = usuario or {}
        self._modo_solicitante = normalize_access_level(self.usuario.get("nivel_acesso")) == ROLE_REQUESTER
        self._carregar_preferencias()
        self.aplicar_modo_usuario()
        self.aplicar_permissoes()
        if self._loaded:
            self._aplicar_preferencias_salvas()
            if self._modo_solicitante or self.empresa_pronta():
                self.carregar_demandas()
            else:
                self._mostrar_prompt_empresa()

    def _pode(self, action_key):
        return has_action_access(self.usuario, action_key)

    def _avisar_sem_permissao(self, action_key):
        QMessageBox.warning(
            self,
            "Acesso não permitido",
            f"Você não tem permissão para {get_action_label(action_key)}.",
        )

    def _empresa_contexto_solicitante(self):
        return str(self.usuario.get("empresa") or "").strip() or None

    def _demandas_visiveis_para_usuario(self, demandas):
        if not self._modo_solicitante:
            return list(demandas or [])

        usuario_id = self.usuario.get("id")
        visiveis = []
        for demanda in demandas or []:
            if usuario_id is not None and demanda.get("criado_por") == usuario_id:
                visiveis.append(demanda)
        return visiveis

    def _configurar_colunas_tabela(self):
        if self._modo_solicitante:
            headers = ["ID", "Título", "Prioridade", "Urgência", "Status", "Data Abertura"]
        else:
            headers = [
                "ID",
                "Título",
                "Solicitante",
                "Prioridade",
                "Urgencia",
                "Status",
                "Data Abertura",
                "Responsavel",
            ]

        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        configure_data_table(
            self.tabela,
            stretch_columns=(1,),
            minimum_section_size=88,
            minimum_widths={
                0: 72,
                1: 240,
                2: 160,
                3: 130,
                4: 130,
                5: 140,
                6: 155,
                7: 170,
            },
        )

    def _create_summary_strip(self, specs):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        for key, title, caption in specs:
            card = QFrame()
            card.setObjectName("demandSummaryCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(6)

            title_label = QLabel(title)
            title_label.setObjectName("demandSummaryTitle")

            value_label = QLabel("0")
            value_label.setObjectName("demandSummaryValue")

            caption_label = QLabel(caption)
            caption_label.setObjectName("demandSummaryCaption")
            caption_label.setWordWrap(True)

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            card_layout.addWidget(caption_label)
            layout.addWidget(card, 1)
            self._summary_labels[key] = value_label

        return container

    def _create_detail_panel(self):
        card = QFrame()
        card.setObjectName("demandDetailCard")
        card.setMinimumWidth(320)
        card.setMaximumWidth(390)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel("Detalhes da demanda")
        title.setObjectName("demandDetailTitle")
        layout.addWidget(title)

        self.detail_titulo = QLabel("")
        self.detail_titulo.setWordWrap(True)
        self.detail_titulo.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(self.detail_titulo)

        self.detail_body = QLabel("")
        self.detail_body.setObjectName("demandDetailBody")
        self.detail_body.setWordWrap(True)
        self.detail_body.setTextFormat(Qt.RichText)
        self.detail_body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.detail_body, 1)

        return card

    def _set_summary_value(self, key, value):
        label = self._summary_labels.get(key)
        if label is not None:
            label.setText(str(value))

    def _display_status(self, value):
        labels = {
            "aberto": "Aberto",
            "andamento": "Em andamento",
            "concluido": "Concluido",
            "cancelado": "Cancelado",
        }
        return labels.get(str(value or "").strip().lower(), str(value or "-"))

    def _display_level(self, value):
        labels = {
            "alta": "Alta",
            "media": "Media",
            "baixa": "Baixa",
        }
        return labels.get(str(value or "").strip().lower(), str(value or "-"))

    def _update_summary(self, demandas):
        total = len(demandas)
        abertas = sum(1 for demanda in demandas if str(demanda.get("status", "")).lower() == "aberto")
        andamento = sum(1 for demanda in demandas if str(demanda.get("status", "")).lower() == "andamento")
        criticas = sum(
            1
            for demanda in demandas
            if str(demanda.get("prioridade", "")).lower() == "alta"
            or str(demanda.get("urgencia", "")).lower() == "alta"
        )
        self._set_summary_value("total", total)
        self._set_summary_value("abertas", abertas)
        self._set_summary_value("andamento", andamento)
        self._set_summary_value("criticas", criticas)

    def _set_detail_empty(self):
        if hasattr(self, "detail_titulo"):
            self.detail_titulo.setText("Selecione uma demanda")
        if hasattr(self, "detail_body"):
            self.detail_body.setText(
                "Escolha um item na grade para ver solicitante, empresa, prioridade, urgencia e o contexto completo."
            )

    def _update_detail_from_selection(self):
        demanda = self._demanda_selecionada()
        if not demanda:
            self._set_detail_empty()
            return

        self.detail_titulo.setText(demanda.get("titulo", "Demanda"))
        detalhe = (
            f"<b>ID:</b> {demanda.get('id', '-')}<br>"
            f"<b>Solicitante:</b> {demanda.get('solicitante', '-') or '-'}<br>"
            f"<b>Empresa:</b> {demanda.get('empresa', '-') or '-'}<br>"
            f"<b>Departamento:</b> {demanda.get('departamento', '-') or '-'}<br>"
            f"<b>Prioridade:</b> {self._display_level(demanda.get('prioridade'))}<br>"
            f"<b>Urgencia:</b> {self._display_level(demanda.get('urgencia'))}<br>"
            f"<b>Status:</b> {self._display_status(demanda.get('status'))}<br>"
            f"<b>Responsavel:</b> {demanda.get('responsavel', '-') or '-'}<br>"
            f"<b>Data de abertura:</b> {(demanda.get('data_abertura') or '')[:10] or '-'}<br>"
            f"<b>Descricao:</b><br>{(demanda.get('descricao') or '-')}<br>"
            f"<b>Observacao:</b><br>{(demanda.get('observacao') or '-')}"
        )
        self.detail_body.setText(detalhe)
    def aplicar_modo_usuario(self):
        if not hasattr(self, "titulo_label"):
            return

        self._configurar_colunas_tabela()

        if self._modo_solicitante:
            self.titulo_label.setText("Minhas Demandas")
            self.empresa_label.setVisible(False)
            self.empresa_filter.setVisible(False)
            self.empresa_prompt.setText("Abra uma nova demanda e acompanhe abaixo apenas os chamados enviados por você.")
        else:
            self.titulo_label.setText("Demandas / Chamados TI")
            self.empresa_label.setVisible(True)
            self.empresa_filter.setVisible(True)
            self.empresa_prompt.setText("Selecione uma empresa ou 'Todas as empresas' para carregar as demandas.")

        self.ver_btn.setVisible(True)

    def aplicar_permissoes(self):
        if hasattr(self, "novo_btn"):
            self.novo_btn.setVisible(self._pode("demandas.create"))
        if hasattr(self, "assumir_btn"):
            self.assumir_btn.setVisible(self._pode("demandas.assign") and not self._modo_solicitante)
        if hasattr(self, "editar_btn"):
            self.editar_btn.setVisible(self._pode("demandas.edit") and not self._modo_solicitante)
        if hasattr(self, "concluir_btn"):
            self.concluir_btn.setVisible(self._pode("demandas.complete") and not self._modo_solicitante)
        if hasattr(self, "cancelar_btn"):
            self.cancelar_btn.setVisible(self._pode("demandas.cancel") and not self._modo_solicitante)
        if hasattr(self, "deletar_btn"):
            self.deletar_btn.setVisible(self._pode("demandas.delete") and not self._modo_solicitante)

    def empresa_pronta(self):
        if self._modo_solicitante:
            return True
        return company_filter_ready(self.empresa_filter)

    def empresa_param(self):
        if self._modo_solicitante:
            return self._empresa_contexto_solicitante()
        return selected_company_value(self.empresa_filter)

    def _carregar_preferencias(self):
        self._saved_preferences = get_widget_preferences(self.usuario, "demandas")

    def _sort_pref_key(self):
        return "sort_solicitante" if self._modo_solicitante else "sort_admin"

    def _widths_pref_key(self):
        return "widths_solicitante" if self._modo_solicitante else "widths_admin"

    def _aplicar_preferencias_salvas(self):
        self._restoring_preferences = True
        try:
            self.pesquisa_edit.setText(str(self._saved_preferences.get("busca") or ""))
            apply_combo_text(self.status_filter, self._saved_preferences.get("status"))
            apply_combo_text(self.prioridade_filter, self._saved_preferences.get("prioridade"))
            if not self._modo_solicitante:
                apply_combo_data(self.empresa_filter, self._saved_preferences.get("empresa"))
        finally:
            self._restoring_preferences = False

    def _preferencias_atuais(self):
        return {
            "busca": self.pesquisa_edit.text().strip(),
            "status": self.status_filter.currentText(),
            "prioridade": self.prioridade_filter.currentText(),
            "empresa": self.empresa_filter.currentData(),
            self._sort_pref_key(): get_table_sort_state(self.tabela),
            self._widths_pref_key(): get_table_column_widths(self.tabela),
        }

    def _salvar_preferencias(self):
        if self._restoring_preferences:
            return
        merged = dict(self._saved_preferences or {})
        merged.update(self._preferencias_atuais())
        self._saved_preferences = merged
        save_widget_preferences(self.usuario, "demandas", self._saved_preferences)

    def _ao_ordenar_tabela(self, *_args):
        self._salvar_preferencias()

    def _ao_redimensionar_coluna(self, *_args):
        self._salvar_preferencias()

    def carregar_empresas(self):
        try:
            self.empresas = api_client.get_empresas()
            populate_company_filter(self.empresa_filter, self.empresas)
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")

    def _mostrar_prompt_empresa(self):
        self.demandas = []
        self.tabela.setRowCount(0)
        self.empresa_prompt.setVisible(True)

    def _atualizar_prompt_apos_carga(self, quantidade):
        if self._modo_solicitante:
            if quantidade:
                self.empresa_prompt.setVisible(False)
            else:
                if self.demandas:
                    self.empresa_prompt.setText("Nenhuma demanda encontrada com os filtros atuais.")
                else:
                    self.empresa_prompt.setText("Você ainda não abriu nenhuma demanda.")
                self.empresa_prompt.setVisible(True)
            return

        if quantidade:
            self.empresa_prompt.setVisible(False)
        elif not self.empresa_pronta():
            self.empresa_prompt.setText("Selecione uma empresa ou 'Todas as empresas' para carregar as demandas.")
            self.empresa_prompt.setVisible(True)
        else:
            self.empresa_prompt.setText("Nenhuma demanda encontrada para os filtros atuais.")
            self.empresa_prompt.setVisible(True)

    def ao_alterar_empresa(self):
        if self._modo_solicitante:
            return
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            self._salvar_preferencias()
            return
        self.carregar_demandas()
        self._salvar_preferencias()

    def carregar_demandas(self):
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        try:
            demandas = api_client.listar_demandas(empresa=self.empresa_param())
            self.demandas = self._demandas_visiveis_para_usuario(demandas)
            self.filtrar_demandas()
        except Exception as e:
            print(f"Erro ao carregar demandas: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar demandas: {e}")

    def filtrar_demandas(self):
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        status = self.status_filter.currentText()
        prioridade = self.prioridade_filter.currentText()
        search_text = self.pesquisa_edit.text()

        filtradas = []
        for demanda in self.demandas:
            if not is_all_option(status) and not same_filter_value(demanda.get("status", ""), status):
                continue
            if not is_all_option(prioridade) and not same_filter_value(demanda.get("prioridade", ""), prioridade):
                continue
            if not contains_text(
                search_text,
                demanda.get("id", ""),
                demanda.get("titulo", ""),
                demanda.get("descricao", ""),
                demanda.get("solicitante", ""),
                demanda.get("responsavel", ""),
                demanda.get("status", ""),
                demanda.get("empresa", ""),
            ):
                continue
            filtradas.append(demanda)

        self.atualizar_tabela(filtradas)
        self._atualizar_prompt_apos_carga(len(filtradas))
        self._salvar_preferencias()

    def atualizar_tabela(self, demandas):
        self._visible_demandas = list(demandas)
        sorting_enabled = self.tabela.isSortingEnabled()
        self.tabela.setSortingEnabled(False)
        self.tabela.clearSelection()
        self.tabela.clearContents()
        self.tabela.setRowCount(len(demandas))

        prioridade_cores = {
            "alta": QColor(231, 111, 81),
            "media": QColor(244, 162, 97),
            "baixa": QColor(42, 157, 143),
        }

        status_cores = {
            "aberto": QColor(244, 162, 97),
            "andamento": QColor(42, 157, 143),
            "concluido": QColor(44, 125, 160),
            "cancelado": QColor(231, 111, 81),
        }

        for row, demanda in enumerate(demandas):
            data = (demanda.get("data_abertura") or "")[:10]
            self.tabela.setItem(row, 0, number_item(demanda.get("id", "")))
            self.tabela.setItem(row, 1, QTableWidgetItem((demanda.get("titulo") or "")[:80]))

            prioridade_item = QTableWidgetItem((demanda.get("prioridade", "media") or "media").upper())
            prioridade_item.setForeground(prioridade_cores.get(demanda.get("prioridade", "media"), QColor(0, 0, 0)))

            urgencia_item = QTableWidgetItem((demanda.get("urgencia", "media") or "media").upper())

            status_item = QTableWidgetItem((demanda.get("status", "aberto") or "aberto").upper())
            status_item.setForeground(status_cores.get(demanda.get("status", "aberto"), QColor(0, 0, 0)))

            if self._modo_solicitante:
                self.tabela.setItem(row, 2, prioridade_item)
                self.tabela.setItem(row, 3, urgencia_item)
                self.tabela.setItem(row, 4, status_item)
                self.tabela.setItem(row, 5, QTableWidgetItem(data))
            else:
                self.tabela.setItem(row, 2, QTableWidgetItem(demanda.get("solicitante", "-")))
                self.tabela.setItem(row, 3, prioridade_item)
                self.tabela.setItem(row, 4, urgencia_item)
                self.tabela.setItem(row, 5, status_item)
                self.tabela.setItem(row, 6, QTableWidgetItem(data))
                self.tabela.setItem(row, 7, QTableWidgetItem(demanda.get("responsavel", "-") or "-"))

        if sorting_enabled:
            self.tabela.setSortingEnabled(True)

        apply_table_sort_state(self.tabela, self._saved_preferences.get(self._sort_pref_key()))
        refresh_data_table_layout(self.tabela)
        apply_table_column_widths(self.tabela, self._saved_preferences.get(self._widths_pref_key()))
        self._update_summary(demandas)
        if demandas:
            self.tabela.selectRow(0)
            self._update_detail_from_selection()
        else:
            self._set_detail_empty()

    def _demanda_selecionada(self):
        row = self.tabela.currentRow()
        if row < 0:
            return None

        item_id = self.tabela.item(row, 0)
        if item_id is None:
            return None

        demanda_id = int(item_id.text())
        return next((demanda for demanda in self._visible_demandas if demanda.get("id") == demanda_id), None)

    def nova_demanda(self):
        if not self._pode("demandas.create"):
            self._avisar_sem_permissao("demandas.create")
            return

        dialog = DemandaDialog(
            requester_mode=self._modo_solicitante,
            usuario_context=self.usuario,
            empresa_padrao=self.empresa_param(),
            parent=self,
        )
        if dialog.exec():
            self.carregar_demandas()

    def ver_demanda(self):
        demanda = self._demanda_selecionada()
        if not demanda:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para visualizar.")
            return

        dialog = DemandaDialog(
            demanda_data=demanda,
            readonly=True,
            requester_mode=self._modo_solicitante,
            usuario_context=self.usuario,
            empresa_padrao=self.empresa_param(),
            parent=self,
        )
        dialog.exec()

    def assumir_demanda(self):
        if not self._pode("demandas.assign"):
            self._avisar_sem_permissao("demandas.assign")
            return

        demanda = self._demanda_selecionada()
        if not demanda:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para assumir.")
            return

        titulo = demanda.get("titulo", "")
        confirm = QMessageBox.question(
            self,
            "Assumir demanda",
            f"Deseja assumir a demanda '{titulo}' para você?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            if api_client.assumir_demanda(demanda["id"]):
                QMessageBox.information(self, "Sucesso", "Demanda assumida com sucesso!")
                self.carregar_demandas()
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível assumir a demanda.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao assumir demanda: {e}")

    def editar_demanda(self):
        if not self._pode("demandas.edit"):
            self._avisar_sem_permissao("demandas.edit")
            return

        demanda = self._demanda_selecionada()
        if not demanda:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para editar.")
            return

        dialog = DemandaDialog(
            demanda_data=demanda,
            requester_mode=False,
            usuario_context=self.usuario,
            empresa_padrao=self.empresa_param(),
            parent=self,
        )
        if dialog.exec():
            self.carregar_demandas()

    def concluir_demanda(self):
        if not self._pode("demandas.complete"):
            self._avisar_sem_permissao("demandas.complete")
            return

        demanda = self._demanda_selecionada()
        if not demanda:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para concluir.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar conclusão",
            f"Deseja concluir a demanda '{demanda.get('titulo', '')}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            if api_client.concluir_demanda(demanda["id"]):
                QMessageBox.information(self, "Sucesso", "Demanda concluída com sucesso!")
                self.carregar_demandas()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao concluir demanda.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao concluir: {e}")

    def cancelar_demanda(self):
        if not self._pode("demandas.cancel"):
            self._avisar_sem_permissao("demandas.cancel")
            return

        demanda = self._demanda_selecionada()
        if not demanda:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para cancelar.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar cancelamento",
            f"Deseja cancelar a demanda '{demanda.get('titulo', '')}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            if api_client.cancelar_demanda(demanda["id"]):
                QMessageBox.information(self, "Sucesso", "Demanda cancelada com sucesso!")
                self.carregar_demandas()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao cancelar demanda.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao cancelar: {e}")

    def deletar_demanda(self):
        if not self._pode("demandas.delete"):
            self._avisar_sem_permissao("demandas.delete")
            return

        demanda = self._demanda_selecionada()
        if not demanda:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para deletar.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar a demanda '{demanda.get('titulo', '')}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            if api_client.deletar_demanda(demanda["id"]):
                QMessageBox.information(self, "Sucesso", "Demanda deletada com sucesso!")
                self.carregar_demandas()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao deletar demanda.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


class DemandaDialog(QDialog):
    def __init__(
        self,
        demanda_data=None,
        readonly=False,
        requester_mode=False,
        usuario_context=None,
        empresa_padrao=None,
        parent=None,
    ):
        super().__init__(parent)
        self.dados_item = demanda_data
        self.readonly = readonly
        self.requester_mode = requester_mode
        self.usuario_context = usuario_context or {}
        self.empresa_padrao = empresa_padrao
        self._rows = {}
        self._required_rows = {"titulo", "descricao", "solicitante", "empresa", "prioridade", "urgencia"}

        if readonly:
            titulo = "Detalhes da Demanda"
        elif demanda_data:
            titulo = "Editar Demanda"
        else:
            titulo = "Nova Demanda"

        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(620)
        self.init_ui()
        self._prefill_contexto_usuario()

        if demanda_data:
            self.carregar_dados_edicao()

        self._aplicar_modo_solicitante()

        if self.readonly:
            self.set_readonly()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setSpacing(14)
        self.form_layout = form_layout
        layout.addWidget(required_hint_label())

        self.titulo_edit = QLineEdit()
        self.titulo_edit.setPlaceholderText("Título da demanda")
        self._add_row("titulo", "Título:", self.titulo_edit)

        self.descricao_edit = QTextEdit()
        self.descricao_edit.setMaximumHeight(110)
        self.descricao_edit.setPlaceholderText("Descreva o problema com clareza.")
        self._add_row("descricao", "Descrição:", self.descricao_edit)

        self.solicitante_edit = QLineEdit()
        self.solicitante_edit.setPlaceholderText("Nome de quem solicitou")
        self._add_row("solicitante", "Solicitante:", self.solicitante_edit)

        self.departamento_combo = QComboBox()
        self.carregar_departamentos_combo()
        self._add_row("departamento", "Departamento:", self.departamento_combo)

        self.empresa_combo = QComboBox()
        self.carregar_empresas_combo()
        self._add_row("empresa", "Empresa:", self.empresa_combo)

        self.prioridade_combo = QComboBox()
        self.prioridade_combo.addItems(["alta", "media", "baixa"])
        self._add_row("prioridade", "Prioridade:", self.prioridade_combo)

        self.urgencia_combo = QComboBox()
        self.urgencia_combo.addItems(["alta", "media", "baixa"])
        self._add_row("urgencia", "Urgencia:", self.urgencia_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["aberto", "andamento", "concluido", "cancelado"])
        self._add_row("status", "Status:", self.status_combo)

        self.data_prevista = QDateEdit()
        self.data_prevista.setCalendarPopup(True)
        self.data_prevista.setDate(QDate.currentDate().addDays(7))
        self._add_row("data_prevista", "Data Prevista:", self.data_prevista)

        self.responsavel_edit = QLineEdit()
        self.responsavel_edit.setPlaceholderText("Responsavel pela demanda")
        self._add_row("responsavel", "Responsavel:", self.responsavel_edit)

        self.observacao_edit = QTextEdit()
        self.observacao_edit.setMaximumHeight(80)
        self.observacao_edit.setPlaceholderText("Observacoes adicionais")
        self._add_row("observacao", "Observacao:", self.observacao_edit)

        layout.addLayout(form_layout)

        botoes = QHBoxLayout()
        botoes.addStretch()

        if not self.readonly:
            self.salvar_btn = QPushButton("Salvar")
            self.salvar_btn.clicked.connect(self.salvar)
            botoes.addWidget(self.salvar_btn)

        self.cancelar_btn = QPushButton("Fechar" if self.readonly else "Cancelar")
        self.cancelar_btn.clicked.connect(self.reject)
        botoes.addWidget(self.cancelar_btn)

        layout.addLayout(botoes)

    def _add_row(self, key, label_text, widget):
        label = required_label(label_text) if key in self._required_rows else optional_label(label_text)
        self.form_layout.addRow(label, widget)
        self._rows[key] = (label, widget)

    def _set_row_visible(self, key, visible):
        label, widget = self._rows[key]
        label.setVisible(visible)
        widget.setVisible(visible)

    def _set_combo_value(self, combo, value, append_if_missing=False):
        texto = "" if value is None else str(value)
        index = combo.findText(texto)
        if index < 0 and texto and append_if_missing:
            combo.addItem(texto)
            index = combo.findText(texto)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _prefill_contexto_usuario(self):
        if self.usuario_context.get("nome"):
            self.solicitante_edit.setText(str(self.usuario_context.get("nome")))
        empresa = self.usuario_context.get("empresa") or self.empresa_padrao
        if empresa:
            self._set_combo_value(self.empresa_combo, empresa, append_if_missing=True)
        if self.requester_mode:
            self.status_combo.setCurrentText("aberto")

    def _aplicar_modo_solicitante(self):
        if not self.requester_mode:
            return

        self._set_row_visible("solicitante", False)
        self._set_row_visible("responsavel", False)
        self._set_row_visible("observacao", False)
        self._set_row_visible("status", self.readonly)
        self._set_row_visible("data_prevista", self.readonly)
        self.empresa_combo.setEnabled(False)

    def carregar_departamentos_combo(self):
        try:
            departamentos = api_client.get_departamentos_lista()
            self.departamento_combo.clear()
            for departamento in departamentos:
                if departamento and str(departamento).strip():
                    self.departamento_combo.addItem(departamento)
            if self.departamento_combo.count() == 0:
                for item in ["TI", "Administrativo", "Financeiro", "Comercial"]:
                    self.departamento_combo.addItem(item)
        except Exception as e:
            print(f"Erro ao carregar departamentos: {e}")
            for item in ["TI", "Administrativo", "Financeiro", "Comercial"]:
                self.departamento_combo.addItem(item)

    def carregar_empresas_combo(self):
        try:
            empresas = api_client.get_empresas()
            self.empresa_combo.clear()
            for empresa in empresas:
                if empresa and str(empresa).strip():
                    self.empresa_combo.addItem(empresa)
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")
            for item in ["Matriz", "Filial 1", "Filial 2"]:
                self.empresa_combo.addItem(item)

    def set_readonly(self):
        self.titulo_edit.setReadOnly(True)
        self.descricao_edit.setReadOnly(True)
        self.solicitante_edit.setReadOnly(True)
        self.departamento_combo.setEnabled(False)
        self.empresa_combo.setEnabled(False)
        self.prioridade_combo.setEnabled(False)
        self.urgencia_combo.setEnabled(False)
        self.status_combo.setEnabled(False)
        self.data_prevista.setEnabled(False)
        self.responsavel_edit.setReadOnly(True)
        self.observacao_edit.setReadOnly(True)

    def carregar_dados_edicao(self):
        if self.dados_item is None:
            return

        self.titulo_edit.setText(str(self.dados_item.get("titulo", "")))
        self.descricao_edit.setPlainText(str(self.dados_item.get("descricao", "")))
        self.solicitante_edit.setText(str(self.dados_item.get("solicitante", "")))
        self._set_combo_value(self.departamento_combo, self.dados_item.get("departamento", ""), append_if_missing=True)
        self._set_combo_value(self.empresa_combo, self.dados_item.get("empresa", ""), append_if_missing=True)
        self._set_combo_value(self.prioridade_combo, self.dados_item.get("prioridade", "media"))
        self._set_combo_value(self.urgencia_combo, self.dados_item.get("urgencia", "media"))
        self._set_combo_value(self.status_combo, self.dados_item.get("status", "aberto"))

        data_prevista = self.dados_item.get("data_prevista")
        if data_prevista:
            parsed = QDate.fromString(str(data_prevista)[:10], "yyyy-MM-dd")
            if parsed.isValid():
                self.data_prevista.setDate(parsed)
        elif self.readonly:
            self._set_row_visible("data_prevista", False)

        self.responsavel_edit.setText(str(self.dados_item.get("responsavel", "") or ""))
        self.observacao_edit.setPlainText(str(self.dados_item.get("observacao", "") or ""))

    def salvar(self):
        dados = {
            "titulo": self.titulo_edit.text().strip(),
            "descricao": self.descricao_edit.toPlainText().strip(),
            "solicitante": self.solicitante_edit.text().strip(),
            "departamento": self.departamento_combo.currentText() or None,
            "empresa": self.empresa_combo.currentText().strip(),
            "prioridade": self.prioridade_combo.currentText(),
            "urgencia": self.urgencia_combo.currentText(),
            "status": self.status_combo.currentText(),
            "data_prevista": self.data_prevista.date().toString("yyyy-MM-dd"),
            "responsavel": self.responsavel_edit.text().strip() or None,
            "observacao": self.observacao_edit.toPlainText().strip() or None,
        }

        if self.requester_mode:
            dados["solicitante"] = str(self.usuario_context.get("nome") or dados["solicitante"]).strip()
            dados["empresa"] = str(self.usuario_context.get("empresa") or dados["empresa"]).strip()
            if not self.dados_item:
                dados["status"] = "aberto"
                dados["responsavel"] = None
                dados["observacao"] = None
                dados["data_prevista"] = None

        if not dados["titulo"]:
            focus_invalid_field(self.titulo_edit)
            QMessageBox.warning(self, "Campo obrigatório", required_field_message("Título"))
            return

        if not dados["descricao"]:
            focus_invalid_field(self.descricao_edit)
            QMessageBox.warning(self, "Campo obrigatório", required_field_message("Descrição"))
            return

        if not dados["solicitante"]:
            focus_invalid_field(self.solicitante_edit)
            QMessageBox.warning(self, "Campo obrigatório", required_field_message("Solicitante"))
            return

        if not dados["empresa"]:
            focus_invalid_field(self.empresa_combo)
            QMessageBox.warning(self, "Campo obrigatório", required_field_message("Empresa"))
            return

        try:
            if self.dados_item:
                response = api_client.atualizar_demanda(self.dados_item["id"], dados)
                if response:
                    QMessageBox.information(self, "Sucesso", f"Demanda '{dados['titulo']}' atualizada com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível atualizar a demanda. Revise os dados e tente novamente.")
            else:
                response = api_client.criar_demanda(dados)
                if response:
                    protocolo = response.get("id")
                    if self.requester_mode and protocolo:
                        mensagem = f"Demanda #{protocolo} enviada com sucesso!"
                    else:
                        mensagem = f"Demanda '{dados['titulo']}' criada com sucesso!"
                    QMessageBox.information(self, "Sucesso", mensagem)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível criar a demanda. Revise os dados e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar a demanda.\n\nDetalhes: {e}")
