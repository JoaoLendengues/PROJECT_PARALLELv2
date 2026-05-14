from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QCheckBox,
                               QMessageBox, QHeaderView, QFrame, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from api_client import api_client
from access_control import get_action_label, has_action_access
from widgets.form_feedback import focus_invalid_field, optional_label, required_field_message, required_hint_label, required_label
from widgets.filter_utils import contains_text, is_all_option, same_text
from widgets.table_utils import configure_data_table, number_item, refresh_data_table_layout
from user_preferences import apply_table_column_widths, get_table_column_widths, get_widget_preferences, save_widget_preferences


class ColaboradoresWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario = {}
        self.colaboradores = []
        self._visible_colaboradores = []
        self.colaboradores_cache = []  # Cache para filtros
        self._loaded = False
        self._summary_labels = {}
        self._saved_preferences = {}
        self.init_ui()

    def on_show(self):
        if not self._loaded:
            self.carregar_colaboradores()
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
            QFrame#collaboratorSummaryCard, QFrame#collaboratorDetailCard {{
                background-color: {colors_map['card_bg']};
                border: 1px solid {colors_map['card_border']};
                border-radius: 16px;
            }}
            QLabel#collaboratorSummaryTitle {{
                color: {colors_map['muted']};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#collaboratorSummaryValue {{
                color: {colors_map['title']};
                font-size: 24px;
                font-weight: 700;
            }}
            QLabel#collaboratorSummaryCaption, QLabel#collaboratorDetailBody {{
                color: {colors_map['muted']};
                font-size: 12px;
            }}
            QLabel#collaboratorDetailTitle {{
                color: {colors_map['title']};
                font-size: 16px;
                font-weight: 700;
            }}
            QLineEdit#collaboratorSearchInput {{
                background-color: {colors_map['card_bg']};
                color: {colors_map['title']};
                border: 1px solid {colors_map['card_border']};
                border-radius: 12px;
                padding: 10px 14px;
                min-height: 18px;
            }}
            """
        )

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("👥 Colaboradores")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()

        # Botão Novo Colaborador
        self.novo_btn = QPushButton("+ Novo Colaborador")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.novo_colaborador)
        header.addWidget(self.novo_btn)

        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_colaboradores)
        header.addWidget(self.atualizar_btn)

        layout.addLayout(header)

        # Barra de pesquisa
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setObjectName("collaboratorSearchInput")
        self.pesquisa_edit.setPlaceholderText("🔍 Pesquisar por nome...")
        self.pesquisa_edit.setMaximumWidth(300)
        self.pesquisa_edit.textChanged.connect(self.filtrar_colaboradores)
        layout.addWidget(self.pesquisa_edit)

        # Filtros
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(15)

        # Filtro Status
        filtros_layout.addWidget(QLabel('Status:'))
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(100)
        self.status_filter.addItems(['Todos', 'Ativo', 'Inativo'])
        self.status_filter.currentTextChanged.connect(self.filtrar_colaboradores)
        filtros_layout.addWidget(self.status_filter)

        # Filtro Empresa
        filtros_layout.addWidget(QLabel('Empresa:'))
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(150)
        self.empresa_filter.addItem('Todas as empresas')
        self.empresa_filter.currentTextChanged.connect(self.filtrar_colaboradores)
        filtros_layout.addWidget(self.empresa_filter)

        # Filtro Departamento
        filtros_layout.addWidget(QLabel('Departamento:'))
        self.departamento_filter = QComboBox()
        self.departamento_filter.setMinimumWidth(150)
        self.departamento_filter.addItem('Todos os departamentos')
        self.departamento_filter.currentTextChanged.connect(self.filtrar_colaboradores)
        filtros_layout.addWidget(self.departamento_filter)

        filtros_layout.addStretch()
        layout.addLayout(filtros_layout)

        self.summary_strip = self._create_summary_strip(
            [
                ("total", "Colaboradores visíveis", "Base filtrada na grade"),
                ("ativos", "Ativos", "Disponíveis no sistema"),
                ("inativos", "Inativos", "Registros desativados"),
                ("empresas", "Empresas", "Distribuição visível"),
            ]
        )
        layout.addWidget(self.summary_strip)

        # Tabela com estilo melhorado
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSortingEnabled(True)
        self.tabela.verticalHeader().setVisible(False)

        # Estilo da tabela
        self.tabela.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        headers = ["ID", "Nome", "Cargo", "Departamento", "Empresa", "Status"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        configure_data_table(
            self.tabela,
            stretch_columns=(1,),
            minimum_section_size=88,
            minimum_widths={
                0: 72,
                1: 220,
                2: 160,
                3: 180,
                4: 180,
                5: 120,
            },
        )

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

        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_colaborador)
        acoes.addWidget(self.editar_btn)

        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_colaborador)
        acoes.addWidget(self.deletar_btn)

        layout.addLayout(acoes)

        # Carregar listas para os filtros (DEPOIS de criar os comboboxes)
        self.carregar_empresas()
        self.carregar_departamentos()
        self.aplicar_permissoes()
        self._set_detail_empty()

    def set_usuario(self, usuario):
        self.usuario = usuario or {}
        self._carregar_preferencias()
        self.aplicar_permissoes()

    def _carregar_preferencias(self):
        self._saved_preferences = get_widget_preferences(self.usuario, "colaboradores")

    def _salvar_preferencias(self):
        self._saved_preferences = {
            "widths": get_table_column_widths(self.tabela),
        }
        save_widget_preferences(self.usuario, "colaboradores", self._saved_preferences)

    def _ao_redimensionar_coluna(self, *_args):
        self._salvar_preferencias()

    def _pode(self, action_key):
        return has_action_access(self.usuario, action_key)

    def _avisar_sem_permissao(self, action_key):
        QMessageBox.warning(self, "Acesso não permitido", f"Você não tem permissão para {get_action_label(action_key)}.")

    def aplicar_permissoes(self):
        if hasattr(self, "novo_btn"):
            self.novo_btn.setVisible(self._pode("colaboradores.create"))
        if hasattr(self, "editar_btn"):
            self.editar_btn.setVisible(self._pode("colaboradores.edit"))
        if hasattr(self, "deletar_btn"):
            self.deletar_btn.setVisible(self._pode("colaboradores.delete"))

    def _create_summary_strip(self, specs):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        self._summary_labels = {}

        for key, title, caption in specs:
            card = QFrame()
            card.setObjectName("collaboratorSummaryCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(4)

            title_label = QLabel(title)
            title_label.setObjectName("collaboratorSummaryTitle")
            card_layout.addWidget(title_label)

            value_label = QLabel("--")
            value_label.setObjectName("collaboratorSummaryValue")
            card_layout.addWidget(value_label)

            caption_label = QLabel(caption)
            caption_label.setObjectName("collaboratorSummaryCaption")
            caption_label.setWordWrap(True)
            card_layout.addWidget(caption_label)

            layout.addWidget(card, 1)
            self._summary_labels[key] = value_label

        return container

    def _create_detail_panel(self):
        card = QFrame()
        card.setObjectName("collaboratorDetailCard")
        card.setMinimumWidth(320)
        card.setMaximumWidth(380)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel("Detalhes do colaborador")
        title.setObjectName("collaboratorDetailTitle")
        layout.addWidget(title)

        self.detail_body = QLabel("")
        self.detail_body.setObjectName("collaboratorDetailBody")
        self.detail_body.setWordWrap(True)
        self.detail_body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.detail_body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.detail_body, 1)

        return card

    def _set_summary_value(self, key, value):
        label = self._summary_labels.get(key)
        if label is not None:
            label.setText(str(value))

    def _set_detail_empty(self):
        if hasattr(self, "detail_body"):
            self.detail_body.setText(
                "Selecione um colaborador para ver cargo, departamento, empresa e status."
            )

    def _build_detail_text(self, colaborador):
        return (
            f"Nome: {colaborador.get('nome', '-')}\n"
            f"Cargo: {colaborador.get('cargo') or '-'}\n"
            f"Departamento: {colaborador.get('departamento') or '-'}\n"
            f"Empresa: {colaborador.get('empresa') or '-'}\n"
            f"Status: {'Ativo' if colaborador.get('ativo', True) else 'Inativo'}"
        )

    def _atualizar_resumo(self, colaboradores):
        total = len(colaboradores)
        ativos = sum(1 for colab in colaboradores if colab.get("ativo", True))
        inativos = max(0, total - ativos)
        empresas = {
            str(colab.get("empresa") or "").strip()
            for colab in colaboradores
            if str(colab.get("empresa") or "").strip()
        }

        self._set_summary_value("total", total)
        self._set_summary_value("ativos", ativos)
        self._set_summary_value("inativos", inativos)
        self._set_summary_value("empresas", len(empresas))

    def _update_detail_from_selection(self):
        if self.tabela.rowCount() == 0:
            self._set_detail_empty()
            return

        current_row = self.tabela.currentRow()
        if current_row < 0:
            self._set_detail_empty()
            return

        id_item = self.tabela.item(current_row, 0)
        if id_item is None:
            self._set_detail_empty()
            return

        try:
            colaborador_id = int(id_item.text())
        except Exception:
            self._set_detail_empty()
            return

        colaborador = next((item for item in self._visible_colaboradores if item.get("id") == colaborador_id), None)
        if not colaborador:
            self._set_detail_empty()
            return

        self.detail_body.setText(self._build_detail_text(colaborador))

    def carregar_colaboradores(self):
        """Carrega a lista de colaboradores do backend"""
        try:
            self.colaboradores = api_client.listar_colaboradores()
            self._visible_colaboradores = list(self.colaboradores)
            self.colaboradores_cache = self.colaboradores.copy()
            self.atualizar_tabela(self.colaboradores)
            print(f"✅ Colaboradores carregados: {len(self.colaboradores)}")
        except Exception as e:
            print(f"❌ Erro ao carregar colaboradores: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar colaboradores: {e}")

    def filtrar_colaboradores(self):
        """Filtra os colaboradores com base nos filtros"""
        search_text = self.pesquisa_edit.text()
        status = self.status_filter.currentText().lower()
        empresa = self.empresa_filter.currentText()
        departamento = self.departamento_filter.currentText()

        filtered = []
        for colab in self.colaboradores_cache:
            # Filtro por status
            if status == 'ativo' and not colab.get('ativo', True):
                continue
            if status == 'inativo' and colab.get('ativo', True):
                continue

            # Filtro por empresa
            if not is_all_option(empresa) and not same_text(colab.get('empresa'), empresa):
                continue

            # Filtro por departamento
            if not is_all_option(departamento) and not same_text(colab.get('departamento'), departamento):
                continue

            # Filtro por pesquisa
            if contains_text(search_text, colab.get('nome', '')):
                filtered.append(colab)

        self.atualizar_tabela(filtered)

    def atualizar_tabela(self, colaboradores):
        self._visible_colaboradores = list(colaboradores)
        sorting_enabled = self.tabela.isSortingEnabled()
        self.tabela.setSortingEnabled(False)
        self.tabela.clearContents()
        self.tabela.setRowCount(len(colaboradores))

        for row, colab in enumerate(colaboradores):
            self.tabela.setItem(row, 0, number_item(colab.get("id", "")))
            self.tabela.setItem(row, 1, QTableWidgetItem(colab.get("nome", "")))
            self.tabela.setItem(row, 2, QTableWidgetItem(colab.get("cargo", "-")))
            self.tabela.setItem(row, 3, QTableWidgetItem(colab.get("departamento", "-")))
            self.tabela.setItem(row, 4, QTableWidgetItem(colab.get("empresa", "-")))

            status_item = QTableWidgetItem("Ativo" if colab.get("ativo", True) else "Inativo")
            if not colab.get("ativo", True):
                status_item.setForeground(QColor(231, 111, 81))
            else:
                status_item.setForeground(QColor(42, 157, 143))
            self.tabela.setItem(row, 5, status_item)

        if sorting_enabled:
            self.tabela.setSortingEnabled(True)

        refresh_data_table_layout(self.tabela)
        apply_table_column_widths(self.tabela, self._saved_preferences.get("widths"))
        self._atualizar_resumo(colaboradores)
        if colaboradores:
            self.tabela.setCurrentCell(0, 0)
        else:
            self._set_detail_empty()

    def novo_colaborador(self):
        if not self._pode("colaboradores.create"):
            self._avisar_sem_permissao("colaboradores.create")
            return
        dialog = ColaboradorDialog(item_data=None, parent=self)
        if dialog.exec():
            self.pesquisa_edit.clear()
            self.status_filter.setCurrentIndex(0)
            self.empresa_filter.setCurrentIndex(0)
            self.departamento_filter.setCurrentIndex(0)
            self.carregar_colaboradores()

    def editar_colaborador(self):
        if not self._pode("colaboradores.edit"):
            self._avisar_sem_permissao("colaboradores.edit")
            return
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um colaborador para editar")
            return

        colab_id = int(self.tabela.item(row, 0).text())
        colab = next((c for c in self.colaboradores if c["id"] == colab_id), None)

        if colab:
            dialog = ColaboradorDialog(item_data=colab, parent=self)
            if dialog.exec():
                self.carregar_colaboradores()

    def deletar_colaborador(self):
        if not self._pode("colaboradores.delete"):
            self._avisar_sem_permissao("colaboradores.delete")
            return
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um colaborador para deletar")
            return

        colab_id = int(self.tabela.item(row, 0).text())
        colab_nome = self.tabela.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar o colaborador '{colab_nome}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                if api_client.deletar_colaborador(colab_id):
                    QMessageBox.information(self, "Sucesso", "Colaborador deletado com sucesso!")
                    self.carregar_colaboradores()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao deletar colaborador")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")

    def carregar_departamentos(self):
        """Carrega a lista de departamentos do backend para o filtro"""
        try:
            departamentos = api_client.get_departamentos_lista()
            self.departamento_filter.clear()
            self.departamento_filter.addItem('Todos os departamentos')
            for dept in departamentos:
                if dept and dept.strip():
                    self.departamento_filter.addItem(dept)
            print(f"✅ Departamentos carregados para filtro: {len(departamentos)}")
        except Exception as e:
            print(f'❌ Erro ao carregar departamentos: {e}')

    def carregar_empresas(self):
        """Carrega a lista de empresas do backend para o filtro"""
        try:
            empresas = api_client.get_empresas()
            self.empresa_filter.clear()
            self.empresa_filter.addItem('Todas as empresas')
            for emp in empresas:
                if emp and emp.strip():
                    self.empresa_filter.addItem(emp)
            print(f"✅ Empresas carregadas para filtro: {len(empresas)}")
        except Exception as e:
            print(f'❌ Erro ao carregar empresas: {e}')


class ColaboradorDialog(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.dados_item = item_data
        self.setWindowTitle("Cadastro de Colaborador" if not item_data else "Editar Colaborador")
        self.setModal(True)
        self.setMinimumWidth(450)

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

        if item_data:
            self.carregar_dados_edicao()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        layout.addWidget(required_hint_label())

        # Nome
        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Nome completo")
        form_layout.addRow(required_label("Nome:"), self.nome_edit)

        # Cargo
        self.cargo_combo = QComboBox()
        self.cargo_combo.setEditable(False)
        self.cargo_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_cargos_combo()
        form_layout.addRow(optional_label('Cargo:'), self.cargo_combo)

        # Departamento
        self.departamento_combo = QComboBox()
        self.departamento_combo.setEditable(False)
        self.departamento_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_departamentos_combo()
        form_layout.addRow(optional_label("Departamento:"), self.departamento_combo)

        # Empresa
        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_empresas_combo()
        form_layout.addRow(required_label("Empresa:"), self.empresa_combo)

        # Status
        self.status_check = QCheckBox("Ativo")
        self.status_check.setChecked(True)
        form_layout.addRow(optional_label("Status:"), self.status_check)

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

    def carregar_cargos_combo(self):
        """Carrega os cargos do backend para o combobox"""
        try:
            cargos = api_client.get_cargos_lista()
            self.cargo_combo.clear()
            self.cargo_combo.addItem('')
            for cargo in cargos:
                if cargo and cargo.strip():
                    self.cargo_combo.addItem(cargo)
            print(f'✅ Cargos carregados: {len(cargos)}')
        except Exception as e:
            print(f'❌ Erro ao carregar cargos: {e}')
            # Fallback em caso de erro
            default_cargos = ['', 'Analista', 'Coordenador', 'Gerente', 'Assistente', 'Técnico']
            for cargo in default_cargos:
                self.cargo_combo.addItem(cargo)

    def carregar_departamentos_combo(self):
        """Carrega os departamentos do backend para o combobox"""
        try:
            departamentos = api_client.get_departamentos_lista()
            self.departamento_combo.clear()
            for dept in departamentos:
                if dept and dept.strip():
                    self.departamento_combo.addItem(dept)
        except Exception as e:
            print(f'❌ Erro ao carregar departamentos: {e}')
            # Fallback em caso de erro
            default_depts = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"]
            for dept in default_depts:
                self.departamento_combo.addItem(dept)

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
            # Fallback em caso de erro
            default_empresas = ["Matriz", "Filial 1", "Filial 2", "Filial 3"]
            for emp in default_empresas:
                self.empresa_combo.addItem(emp)

    def carregar_dados_edicao(self):
        """Carrega os dados do colaborador para edição"""
        if self.dados_item is None:
            return

        self.nome_edit.setText(str(self.dados_item.get("nome", "")))

        cargo = str(self.dados_item.get('cargo', ''))
        idx = self.cargo_combo.findText(cargo)
        if idx >= 0:
            self.cargo_combo.setCurrentIndex(idx)

        dept = str(self.dados_item.get("departamento", ""))
        idx = self.departamento_combo.findText(dept)
        if idx >= 0:
            self.departamento_combo.setCurrentIndex(idx)

        empresa = str(self.dados_item.get("empresa", ""))
        idx = self.empresa_combo.findText(empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)

        self.status_check.setChecked(self.dados_item.get("ativo", True))

    def salvar(self):
        dados = {
            "nome": self.nome_edit.text().strip(),
            "cargo": self.cargo_combo.currentText().strip() or None,
            "departamento": self.departamento_combo.currentText(),
            "empresa": self.empresa_combo.currentText(),
            "ativo": self.status_check.isChecked()
        }

        if not dados["nome"]:
            focus_invalid_field(self.nome_edit)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Nome"))
            return

        if not dados['empresa']:
            focus_invalid_field(self.empresa_combo)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Empresa"))
            return

        try:
            if self.dados_item:
                response = api_client.atualizar_colaborador(self.dados_item["id"], dados)
                if response:
                    QMessageBox.information(self, "Sucesso", f"Colaborador '{dados['nome']}' atualizado com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível atualizar o colaborador. Revise os dados e tente novamente.")
            else:
                response = api_client.criar_colaborador(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", f"Colaborador '{dados['nome']}' criado com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível criar o colaborador. Revise os dados e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o colaborador.\n\nDetalhes: {e}")
