from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QCheckBox,
                               QMessageBox, QHeaderView, QApplication, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QCursor
from api_client import api_client
from widgets.form_feedback import focus_invalid_field, optional_label, required_field_message, required_hint_label, required_label
from widgets.filter_utils import contains_text, is_all_option, same_filter_value, same_text
from widgets.table_utils import configure_data_table, number_item, refresh_data_table_layout
from user_preferences import (
    apply_combo_text,
    apply_table_column_widths,
    apply_table_sort_state,
    get_table_column_widths,
    get_table_sort_state,
    get_widget_preferences,
    save_widget_preferences,
)


class UsuariosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario = {}
        self.usuarios = []
        self.usuarios_cache = []
        self._visible_usuarios = []
        self._loaded = False
        self._restoring_preferences = False
        self._saved_preferences = {}
        self._summary_labels = {}
        self.init_ui()

    def on_show(self):
        if not self._loaded:
            self.carregar_empresas()
            self.carregar_cargos()
            self._carregar_preferencias()
            self._aplicar_preferencias_salvas()
            self.carregar_usuarios()
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
            QFrame#userSummaryCard, QFrame#userDetailCard {{
                background-color: {colors_map['card_bg']};
                border: 1px solid {colors_map['card_border']};
                border-radius: 16px;
            }}
            QLabel#userSummaryTitle {{
                color: {colors_map['muted']};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#userSummaryValue {{
                color: {colors_map['title']};
                font-size: 24px;
                font-weight: 700;
            }}
            QLabel#userSummaryCaption, QLabel#userDetailBody {{
                color: {colors_map['muted']};
                font-size: 12px;
            }}
            QLabel#userDetailTitle {{
                color: {colors_map['title']};
                font-size: 16px;
                font-weight: 700;
            }}
            QLineEdit#userSearchInput {{
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

        # CabeÃ§alho
        header = QHBoxLayout()
        titulo = QLabel("ðŸ‘¥ Usuarios do Sistema")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()







        # BotÃ£o Novo Usuario
        self.novo_btn = QPushButton("+ Novo Usuario")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.novo_usuario)
        header.addWidget(self.novo_btn)

        # BotÃ£o Atualizar
        self.atualizar_btn = QPushButton("Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_usuarios)
        header.addWidget(self.atualizar_btn)

        layout.addLayout(header)

        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setObjectName("userSearchInput")
        self.pesquisa_edit.setPlaceholderText("Pesquisar por codigo, nome, cargo ou empresa...")
        self.pesquisa_edit.setMaximumWidth(360)
        self.pesquisa_edit.textChanged.connect(self.filtrar_usuarios)
        layout.addWidget(self.pesquisa_edit)

        # Filtros
        filtros = QHBoxLayout()
        filtros.setSpacing(15)

        # Filtro Empresa
        filtros.addWidget(QLabel('Empresa:'))
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(150)
        self.empresa_filter.addItem('Todas as empresas')
        self.empresa_filter.currentTextChanged.connect(self.filtrar_usuarios)
        filtros.addWidget(self.empresa_filter)

        filtros.addSpacing(20)

        # Filtro Cargo
        filtros.addWidget(QLabel('Cargo:'))
        self.cargo_filter = QComboBox()
        self.cargo_filter.setMinimumWidth(150)
        self.cargo_filter.addItem('Todos os cargos')
        self.cargo_filter.currentIndexChanged.connect(self.filtrar_usuarios)
        filtros.addWidget(self.cargo_filter)

        filtros.addSpacing(20)

        # Filtro Status
        filtros.addWidget(QLabel("Status:"))
        self.ativo_filter = QComboBox()
        self.ativo_filter.addItems(["Todos", "Ativos", "Inativos"])
        self.ativo_filter.currentTextChanged.connect(self.filtrar_usuarios)
        filtros.addWidget(self.ativo_filter)

        filtros.addStretch()

        self.nivel_filter = QComboBox()
        self.nivel_filter.addItem("Todos os niveis")
        self.nivel_filter.addItems(["admin", "gerente", "usuario", "solicitante"])
        self.nivel_filter.currentTextChanged.connect(self.filtrar_usuarios)
        filtros.addWidget(QLabel("Nivel:"))
        filtros.addWidget(self.nivel_filter)

        filtros.addStretch()

        layout.addLayout(filtros)

        self.summary_strip = self._create_summary_strip(
            [
                ("total", "Usuarios visiveis", "Base filtrada na grade"),
                ("ativos", "Ativos", "Com acesso liberado"),
                ("inativos", "Inativos", "Registros desativados"),
                ("admins", "Admins/gerentes", "Gestao e operacao"),
            ]
        )
        layout.addWidget(self.summary_strip)

        # Tabela de usuÃ¡rios
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSortingEnabled(True)

        self.tabela.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        headers = ["ID", "Codigo", "Nome", "Cargo", "Empresa", "Nivel", "Status", "Primeiro Acesso"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        configure_data_table(
            self.tabela,
            stretch_columns=(2,),
            minimum_section_size=88,
            minimum_widths={
                0: 72,
                1: 110,
                2: 220,
                3: 160,
                4: 180,
                5: 130,
                6: 120,
                7: 150,
            },
        )

        visible_headers = ["Codigo", "Nome", "Cargo", "Empresa", "Nivel", "Status", "Primeiro Acesso"]
        self.tabela.setColumnCount(len(visible_headers))
        self.tabela.setHorizontalHeaderLabels(visible_headers)
        configure_data_table(
            self.tabela,
            stretch_columns=(1,),
            minimum_section_size=88,
            minimum_widths={
                0: 110,
                1: 220,
                2: 160,
                3: 180,
                4: 130,
                5: 120,
                6: 150,
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

        # BotÃµes de aÃ§Ã£o
        acoes = QHBoxLayout()
        acoes.addStretch()

        self.editar_btn = QPushButton("Editar")
        self.editar_btn.clicked.connect(self.editar_usuario)
        acoes.addWidget(self.editar_btn)

        self.alterar_senha_btn = QPushButton("Alterar Senha")
        self.alterar_senha_btn.clicked.connect(self.alterar_senha)
        acoes.addWidget(self.alterar_senha_btn)

        self.resetar_senha_btn = QPushButton("Resetar Senha")
        self.resetar_senha_btn.clicked.connect(self.resetar_senha)
        acoes.addWidget(self.resetar_senha_btn)

        self.deletar_btn = QPushButton("Excluir")
        self.deletar_btn.clicked.connect(self.deletar_usuario)
        acoes.addWidget(self.deletar_btn)

        layout.addLayout(acoes)
        self._apply_theme_styles()
        self._set_detail_empty()

    def set_usuario(self, usuario):
        self.usuario = usuario or {}
        self._carregar_preferencias()
        if self._loaded:
            self._aplicar_preferencias_salvas()
            self.carregar_usuarios()

    def _carregar_preferencias(self):
        self._saved_preferences = get_widget_preferences(self.usuario, "usuarios")

    def _aplicar_preferencias_salvas(self):
        self._restoring_preferences = True
        try:
            self.pesquisa_edit.setText(self._saved_preferences.get("busca", ""))
            apply_combo_text(self.empresa_filter, self._saved_preferences.get("empresa"))
            apply_combo_text(self.cargo_filter, self._saved_preferences.get("cargo"))
            apply_combo_text(self.ativo_filter, self._saved_preferences.get("status"))
            apply_combo_text(self.nivel_filter, self._saved_preferences.get("nivel"))
        finally:
            self._restoring_preferences = False

    def _preferencias_atuais(self):
        return {
            "busca": self.pesquisa_edit.text().strip(),
            "empresa": self.empresa_filter.currentText(),
            "cargo": self.cargo_filter.currentText(),
            "status": self.ativo_filter.currentText(),
            "nivel": self.nivel_filter.currentText(),
            "sort": get_table_sort_state(self.tabela),
            "widths": get_table_column_widths(self.tabela),
        }

    def _salvar_preferencias(self):
        if self._restoring_preferences:
            return
        self._saved_preferences = self._preferencias_atuais()
        save_widget_preferences(self.usuario, "usuarios", self._saved_preferences)

    def _ao_ordenar_tabela(self, *_args):
        self._salvar_preferencias()

    def _ao_redimensionar_coluna(self, *_args):
        self._salvar_preferencias()

    def _clean_display_text(self, text):
        value = "" if text is None else str(text)
        replacements = {
            "UsuÃƒÆ’Ã‚Â¡rios visÃƒÆ’Ã‚Â­veis": "Usuarios visiveis",
            "GestÃƒÆ’Ã‚Â£o e operaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o": "Gestao e operacao",
            "Selecione um usuÃƒÂ¡rio": "Selecione um usuario",
            "cÃƒÂ³digo": "codigo",
            "nÃƒÂ­vel": "nivel",
            "UsuÃƒÂ¡rio": "Usuario",
            "NÃƒÂ£o": "Nao",
        }
        for source, target in replacements.items():
            value = value.replace(source, target)
        return value

    def _role_display_name(self, level):
        normalized = str(level or "usuario").strip().lower()
        labels = {
            "admin": "Administrador",
            "gerente": "Gerencia",
            "usuario": "Usuario",
            "solicitante": "Solicitante",
        }
        return labels.get(normalized, normalized.title() or "Usuario")

    def _set_detail_actions_enabled(self, enabled):
        if hasattr(self, "detail_editar_btn"):
            self.detail_editar_btn.setEnabled(enabled)
        if hasattr(self, "detail_senha_btn"):
            self.detail_senha_btn.setEnabled(enabled)
        if hasattr(self, "detail_reset_btn"):
            self.detail_reset_btn.setEnabled(enabled)

    def _create_summary_strip(self, specs):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        for key, title, caption in specs:
            card = QFrame()
            card.setObjectName("userSummaryCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(6)

            title_label = QLabel(self._clean_display_text(title))
            title_label.setObjectName("userSummaryTitle")

            value_label = QLabel("0")
            value_label.setObjectName("userSummaryValue")

            caption_label = QLabel(self._clean_display_text(caption))
            caption_label.setWordWrap(True)
            caption_label.setObjectName("userSummaryCaption")

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            card_layout.addWidget(caption_label)
            layout.addWidget(card, 1)
            self._summary_labels[key] = value_label

        return container

    def _create_detail_panel(self):
        card = QFrame()
        card.setObjectName("userDetailCard")
        card.setMinimumWidth(320)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Detalhes")
        title.setObjectName("userDetailTitle")
        layout.addWidget(title)

        self.detail_nome = QLabel("")
        self.detail_nome.setWordWrap(True)
        self.detail_nome.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(self.detail_nome)

        self.detail_body = QLabel("")
        self.detail_body.setObjectName("userDetailBody")
        self.detail_body.setWordWrap(True)
        self.detail_body.setTextFormat(Qt.RichText)
        layout.addWidget(self.detail_body)

        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self.detail_editar_btn = QPushButton("Editar usuario")
        self.detail_editar_btn.clicked.connect(self.editar_usuario)
        self.detail_editar_btn.setMinimumHeight(38)
        actions_layout.addWidget(self.detail_editar_btn)

        self.detail_senha_btn = QPushButton("Alterar senha")
        self.detail_senha_btn.clicked.connect(self.alterar_senha)
        self.detail_senha_btn.setMinimumHeight(38)
        actions_layout.addWidget(self.detail_senha_btn)

        self.detail_reset_btn = QPushButton("Resetar senha")
        self.detail_reset_btn.clicked.connect(self.resetar_senha)
        self.detail_reset_btn.setMinimumHeight(38)
        actions_layout.addWidget(self.detail_reset_btn)

        layout.addLayout(actions_layout)
        layout.addStretch()

        return card

    def _set_summary_value(self, key, value):
        label = self._summary_labels.get(key)
        if label is not None:
            label.setText(str(value))

    def _update_summary(self, usuarios):
        self._set_summary_value("total", len(usuarios))
        self._set_summary_value("ativos", sum(1 for usuario in usuarios if usuario.get("ativo", True)))
        self._set_summary_value("inativos", sum(1 for usuario in usuarios if not usuario.get("ativo", True)))
        self._set_summary_value(
            "admins",
            sum(
                1
                for usuario in usuarios
                if str(usuario.get("nivel_acesso", "")).lower() in {"admin", "gerente"}
            ),
        )

    def _set_detail_empty(self):
        self.detail_nome.setText("Selecione um usuario")
        self.detail_body.setText(
            "Escolha um registro na grade para ver codigo, empresa, cargo, nivel, status e dados operacionais."
        )
        self._set_detail_actions_enabled(False)

    def _update_detail_from_selection(self):
        if self.tabela.rowCount() == 0:
            self._set_detail_empty()
            return

        current_row = self.tabela.currentRow()
        if current_row < 0:
            self._set_detail_empty()
            return

        usuario_id = self._selected_usuario_id()
        if usuario_id is None:
            self._set_detail_empty()
            return

        usuario = next((item for item in self._visible_usuarios if item.get("id") == usuario_id), None)
        if not usuario:
            self._set_detail_empty()
            return

        nome = usuario.get("nome", "Usuario")
        codigo = usuario.get("codigo", "-")
        cargo = usuario.get("cargo") or "-"
        empresa = usuario.get("empresa") or "-"
        nivel = self._role_display_name(usuario.get("nivel_acesso", "usuario"))
        status = "Ativo" if usuario.get("ativo", True) else "Inativo"
        primeiro_acesso = "Sim" if usuario.get("primeiro_acesso", False) else "Nao"

        self.detail_nome.setText(nome)
        self.detail_body.setText(
            f"<b>Codigo:</b> {codigo}<br>"
            f"<b>Cargo:</b> {cargo}<br>"
            f"<b>Empresa:</b> {empresa}<br>"
            f"<b>Nivel:</b> {nivel}<br>"
            f"<b>Status:</b> {status}<br>"
            f"<b>Primeiro acesso:</b> {primeiro_acesso}"
        )
        self._set_detail_actions_enabled(True)

    def carregar_usuarios(self):
        """Carrega a lista de usuÃ¡rios do backend"""
        try:
            self.usuarios = api_client.listar_usuarios()
            self.usuarios_cache = self.usuarios.copy()
            self.atualizar_tabela(self.usuarios)
            print(f"âœ… Usuarios carregados: {len(self.usuarios)}")
        except Exception as e:
            print(f"âŒ Erro ao carregar usuÃ¡rios: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar usuÃ¡rios: {e}")

    def carregar_empresas(self):
        """Carrega a lista de empresas para o filtro"""
        try:
            empresas = api_client.get_empresas()
            self.empresa_filter.clear()
            self.empresa_filter.addItem("Todas as empresas")
            for emp in empresas:
                if emp and emp.strip():
                    self.empresa_filter.addItem(emp)
        except Exception as e:
            print(f"âŒ Erro ao carregar empresas: {e}")

    def carregar_cargos(self):
        """Carrega a lista de cargos para o filtro"""
        try:
            cargos = api_client.get_cargos_lista()
            self.cargo_filter.clear()
            self.cargo_filter.addItem("Todos os cargos")
            for cargo in cargos:
                if cargo and cargo.strip():
                    self.cargo_filter.addItem(cargo)
        except Exception as e:
            print(f"âŒ Erro ao carregar cargos: {e}")

    def filtrar_usuarios(self):
        """Filtra os usuÃ¡rios com base nos filtros"""
        busca = self.pesquisa_edit.text().strip()
        empresa = self.empresa_filter.currentText()
        cargo = self.cargo_filter.currentText()
        status = self.ativo_filter.currentText().lower()
        nivel = self.nivel_filter.currentText()


        filtered = []
        for usuario in self.usuarios_cache:
            if busca and not (
                contains_text(usuario.get("codigo"), busca)
                or contains_text(usuario.get("nome"), busca)
                or contains_text(usuario.get("cargo"), busca)
                or contains_text(usuario.get("empresa"), busca)
            ):
                continue

            # Filtro por empresa
            if not is_all_option(empresa) and not same_text(usuario.get("empresa"), empresa):
                continue

            # Filtro por cargo
            if not is_all_option(cargo) and not same_text(usuario.get("cargo"), cargo):
                continue

            # Filtro por status
            if status == "ativos" and not usuario.get("ativo", True):
                continue
            if status == "inativos" and usuario.get("ativo", True):
                continue

            # Filtro por nivel
            if not is_all_option(nivel) and not same_filter_value(usuario.get("nivel_acesso"), nivel):
                continue

            filtered.append(usuario)

        self.atualizar_tabela(filtered)
        self._salvar_preferencias()

    def atualizar_tabela(self, usuarios):
        """Atualiza a tabela com a lista de usuÃ¡rios"""
        self._visible_usuarios = list(usuarios)
        sorting_enabled = self.tabela.isSortingEnabled()
        self.tabela.setSortingEnabled(False)
        self.tabela.clearSelection()
        self.tabela.clearContents()
        self.tabela.setRowCount(len(usuarios))

        for row, usuario in enumerate(usuarios):
            codigo_item = QTableWidgetItem(usuario.get("codigo", ""))
            codigo_item.setData(Qt.UserRole, usuario.get("id"))
            self.tabela.setItem(row, 0, codigo_item)
            self.tabela.setItem(row, 1, QTableWidgetItem(usuario.get("nome", "")))
            self.tabela.setItem(row, 2, QTableWidgetItem(usuario.get("cargo", "-")))
            self.tabela.setItem(row, 3, QTableWidgetItem(usuario.get("empresa", "-")))

            nivel_acesso = str(usuario.get("nivel_acesso", "usuario")).lower()
            nivel_item = QTableWidgetItem(self._role_display_name(nivel_acesso))
            if nivel_acesso == "admin":
                nivel_item.setForeground(QColor(231, 111, 81))
            elif nivel_acesso == "gerente":
                nivel_item.setForeground(QColor(244, 162, 97))
            elif nivel_acesso == "solicitante":
                nivel_item.setForeground(QColor(99, 102, 241))
            else:
                nivel_item.setForeground(QColor(42, 157, 143))
            self.tabela.setItem(row, 4, nivel_item)

            status_item = QTableWidgetItem("Ativo" if usuario.get("ativo", True) else "Inativo")
            if not usuario.get("ativo", True):
                status_item.setForeground(QColor(231, 111, 81))
            else:
                status_item.setForeground(QColor(42, 157, 143))
            self.tabela.setItem(row, 5, status_item)

            primeiro_acesso = "Sim" if usuario.get("primeiro_acesso", False) else "Nao"
            self.tabela.setItem(row, 6, QTableWidgetItem(primeiro_acesso))

        if sorting_enabled:
            self.tabela.setSortingEnabled(True)

        apply_table_sort_state(self.tabela, self._saved_preferences.get("sort"))
        refresh_data_table_layout(self.tabela)
        apply_table_column_widths(self.tabela, self._saved_preferences.get("widths"))
        self._update_summary(usuarios)
        if usuarios:
            self.tabela.selectRow(0)
            self._update_detail_from_selection()
        else:
            self._set_detail_empty()

    def _selected_usuario_id(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            return None

        codigo_item = self.tabela.item(current_row, 0)
        if codigo_item is None:
            return None

        usuario_id = codigo_item.data(Qt.UserRole)
        if usuario_id is None:
            return None

        return int(usuario_id)

    def novo_usuario(self):
        """Abre diÃ¡logo para criar novo usuÃ¡rio com cÃ³digo automÃ¡tico"""

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        try:
            response = api_client.get_proximo_codigo()
            proximo_codigo = response.get("proximo_codigo", "1")
        except Exception as e:
            print(f"âŒ Erro ao buscar prÃ³ximo cÃ³digo: {e}")
            proximo_codigo = "1"

        QApplication.restoreOverrideCursor()

        dialog = UsuarioDialog(proximo_codigo=proximo_codigo, parent=self)
        if dialog.exec():
            self.carregar_usuarios()

    def editar_usuario(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "AtenÃ§Ã£o", "Selecione um usuario para editar")
            return

        usuario_id = self._selected_usuario_id()
        if usuario_id is None:
            QMessageBox.warning(self, "Erro", "Nao foi possÃ­vel identificar o usuÃ¡rio selecionado.")
            return

        usuario = next((u for u in self.usuarios if u["id"] == usuario_id), None)

        if usuario:
            dialog = UsuarioDialog(usuario_data=usuario, parent=self)
            if dialog.exec():
                self.carregar_usuarios()

    def alterar_senha(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "AtenÃ§Ã£o", "Selecione um usuario para alterar a senha")
            return

        usuario_id = self._selected_usuario_id()
        if usuario_id is None:
            QMessageBox.warning(self, "Erro", "Nao foi possÃ­vel identificar o usuÃ¡rio selecionado.")
            return

        usuario_nome = self.tabela.item(current_row, 1).text()
        usuario_codigo = self.tabela.item(current_row, 0).text()

        senha_dialog = QDialog(self)
        senha_dialog.setWindowTitle("Alterar Senha")
        senha_dialog.setModal(True)
        senha_dialog.setMinimumWidth(400)

        senha_dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        layout = QVBoxLayout(senha_dialog)

        info_label = QLabel(f"Alterando senha do usuario: <b>{usuario_nome}</b><br>Codigo: <b>{usuario_codigo}</b>")
        info_label.setStyleSheet("margin-bottom: 15px;")
        layout.addWidget(info_label)

        form_layout = QFormLayout()

        nova_senha_edit = QLineEdit()
        nova_senha_edit.setEchoMode(QLineEdit.Password)
        nova_senha_edit.setPlaceholderText("Digite a nova senha")
        form_layout.addRow("Nova Senha:", nova_senha_edit)

        confirmar_senha_edit = QLineEdit()
        confirmar_senha_edit.setEchoMode(QLineEdit.Password)
        confirmar_senha_edit.setPlaceholderText("Confirme a nova senha")
        form_layout.addRow("Confirmar Senha:", confirmar_senha_edit)

        requisitos_label = QLabel("ðŸ”’ Requisitos:<br>â€¢ MÃ­nimo de 6 caracteres")
        requisitos_label.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 10px;")
        form_layout.addRow("", requisitos_label)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_alterar = QPushButton("Alterar Senha")
        btn_layout.addWidget(btn_alterar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(senha_dialog.reject)
        btn_layout.addWidget(btn_cancelar)

        layout.addLayout(btn_layout)

        def confirmar_alteracao():
            nova_senha = nova_senha_edit.text()
            confirmar_senha = confirmar_senha_edit.text()

            if not nova_senha:
                focus_invalid_field(nova_senha_edit)
                QMessageBox.warning(senha_dialog, "Campo obrigatorio", required_field_message("Nova senha"))
                return

            if len(nova_senha) < 6:
                focus_invalid_field(nova_senha_edit)
                QMessageBox.warning(senha_dialog, "AtenÃ§Ã£o", "A senha deve ter no mÃ­nimo 6 caracteres!")
                return

            if nova_senha != confirmar_senha:
                focus_invalid_field(confirmar_senha_edit)
                QMessageBox.warning(senha_dialog, "AtenÃ§Ã£o", "As senhas nÃ£o conferem!")
                return

            try:
                if api_client.alterar_senha_usuario(usuario_id, nova_senha):
                    QMessageBox.information(senha_dialog, "Sucesso", f"Senha do usuÃ¡rio '{usuario_nome}' alterada com sucesso.")
                    senha_dialog.accept()
                    self.carregar_usuarios()
                else:
                    QMessageBox.warning(senha_dialog, "Erro", "Nao foi possÃ­vel alterar a senha. Tente novamente.")
            except Exception as e:
                QMessageBox.critical(senha_dialog, "Erro", f"Nao foi possÃ­vel alterar a senha.\n\nDetalhes: {e}")

        btn_alterar.clicked.connect(confirmar_alteracao)
        senha_dialog.exec()

    def resetar_senha(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "AtenÃ§Ã£o", "Selecione um usuario para resetar a senha")
            return

        usuario_id = self._selected_usuario_id()
        if usuario_id is None:
            QMessageBox.warning(self, "Erro", "Nao foi possÃ­vel identificar o usuÃ¡rio selecionado.")
            return

        usuario_nome = self.tabela.item(current_row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar reset de senha",
            f"Tem certeza que deseja resetar a senha do usuÃ¡rio '{usuario_nome}'?\n\nA nova senha serÃ¡ '123456'.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                if api_client.resetar_senha_usuario(usuario_id):
                    QMessageBox.information(self, "Sucesso", f"Senha do usuÃ¡rio '{usuario_nome}' resetada para '123456'!")
                    self.carregar_usuarios()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao resetar senha")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao resetar senha: {e}")

    def deletar_usuario(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "AtenÃ§Ã£o", "Selecione um usuario para deletar")
            return

        usuario_id = self._selected_usuario_id()
        if usuario_id is None:
            QMessageBox.warning(self, "Erro", "Nao foi possÃ­vel identificar o usuÃ¡rio selecionado.")
            return

        usuario_nome = self.tabela.item(current_row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusÃ£o",
            f"Tem certeza que deseja deletar o usuÃ¡rio '{usuario_nome}'?\n\nEsta aÃ§Ã£o nÃ£o poderÃ¡ ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                if api_client.deletar_usuario(usuario_id):
                    QMessageBox.information(self, "Sucesso", "Usuario deletado com sucesso!")
                    self.carregar_usuarios()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao deletar usuÃ¡rio")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


class UsuarioDialog(QDialog):
    def __init__(self, usuario_data=None, proximo_codigo=None, parent=None):
        super().__init__(parent)
        self.dados_item = usuario_data
        self.proximo_codigo = proximo_codigo
        self.setWindowTitle("Novo Usuario" if not usuario_data else "Editar Usuario")
        self.setModal(True)
        self.setMinimumWidth(500)

        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        self.init_ui()

        if usuario_data:
            self.carregar_dados_edicao()
        elif proximo_codigo:
            self.codigo_edit.setText(proximo_codigo)
            self.codigo_edit.setReadOnly(True)

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        layout.addWidget(required_hint_label())

        self.codigo_edit = QLineEdit()
        self.codigo_edit.setPlaceholderText("Codigo numerico unico (ex: 1001)")
        form_layout.addRow(required_label("Codigo:"), self.codigo_edit)

        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Nome completo")
        form_layout.addRow(required_label("Nome:"), self.nome_edit)

        self.cargo_combo = QComboBox()
        self.cargo_combo.setEditable(False)
        self.cargo_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_cargos_combo()
        form_layout.addRow(optional_label("Cargo:"), self.cargo_combo)

        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_empresas_combo()
        form_layout.addRow(required_label("Empresa:"), self.empresa_combo)

        self.nivel_combo = QComboBox()
        self.nivel_combo.addItems(["admin", "gerente", "usuario", "solicitante"])
        self.nivel_combo.setToolTip(
            "admin: Acesso total\n"
            "gerente: Pode gerir operaÃ§Ã£o e demandas\n"
            "usuario: Acesso bÃ¡sico\n"
            "solicitante: Abre demandas e acompanha as prÃ³prias"
        )
        form_layout.addRow(required_label("Nivel de Acesso:"), self.nivel_combo)

        self.ativo_check = QCheckBox("Usuario ativo")
        self.ativo_check.setChecked(True)
        form_layout.addRow(optional_label(""), self.ativo_check)

        if not self.dados_item:
            senha_info = QLabel("âš ï¸ A senha padrÃ£o serÃ¡ '123456'.\nO usuÃ¡rio deverÃ¡ trocar no primeiro acesso.")
            senha_info.setStyleSheet("color: #64748b; font-size: 11px;")
            form_layout.addRow(optional_label(""), senha_info)

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
            self.cargo_combo.addItem('') # OpÃ§Ã£o vazia (opcional)
            for cargo in cargos:
                if cargo and cargo.strip():
                    self.cargo_combo.addItem(cargo)
            print(f'âœ… Cargos carregados: {len(cargos)}')
        except Exception as e:
            print(f'âŒ Erro ao carregar cargos: {e}')
            # Fallback em caso de erro
            default_cargos = ['Analista', 'Coordenador', 'Gerente', 'Assistente', 'TÃ©cnico']
            for cargo in default_cargos:
                self.cargo_combo.addItem(cargo)

    def carregar_empresas_combo(self):
        """Carrega as empresas do backend para o combobox"""
        try:
            empresas = api_client.get_empresas()
            self.empresa_combo.clear()
            for emp in empresas:
                if emp and emp.strip():
                    self.empresa_combo.addItem(emp)
        except Exception as e:
            print(f'âŒ Erro ao carregar empresas: {e}')
            # Fallback em caso de erro
            default_empresas = ['Matriz ', 'Filial 1', 'Filial 2', 'Filial 3']
            for emp in default_empresas:
                self.empresa_combo.addItem(emp)

    def carregar_dados_edicao(self):
        """Carrega os dados do usuÃ¡rio para ediÃ§Ã£o"""
        if self.dados_item is None:
            return

        self.codigo_edit.setText(str(self.dados_item.get("codigo", "")))
        self.codigo_edit.setReadOnly(True)
        self.nome_edit.setText(str(self.dados_item.get("nome", "")))

        cargo = str(self.dados_item.get('cargo', ''))
        idx = self.cargo_combo.findText(cargo)
        if idx >= 0:
            self.cargo_combo.setCurrentIndex(idx)

        empresa = str(self.dados_item.get("empresa", ""))
        idx = self.empresa_combo.findText(empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)

        nivel = str(self.dados_item.get("nivel_acesso", "usuario"))
        idx = self.nivel_combo.findText(nivel)
        if idx >= 0:
            self.nivel_combo.setCurrentIndex(idx)

        self.ativo_check.setChecked(self.dados_item.get("ativo", True))

    def salvar(self):
        codigo = self.codigo_edit.text().strip()
        nome = self.nome_edit.text().strip()
        cargo = self.cargo_combo.currentText().strip() or None
        empresa = self.empresa_combo.currentText()
        nivel_acesso = self.nivel_combo.currentText()
        ativo = self.ativo_check.isChecked()

        if not codigo:
            focus_invalid_field(self.codigo_edit)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Codigo"))
            return

        if not nome:
            focus_invalid_field(self.nome_edit)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Nome"))
            return

        if not empresa:
            focus_invalid_field(self.empresa_combo)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Empresa"))
            return

        dados = {
            "codigo": codigo,
            "nome": nome,
            "cargo": cargo or None,
            "empresa": empresa,
            "nivel_acesso": nivel_acesso,
            "ativo": ativo
        }

        if not self.dados_item:
            dados["senha"] = "123456"

        try:
            if self.dados_item:
                response = api_client.atualizar_usuario(self.dados_item["id"], dados)
                if response:
                    QMessageBox.information(self, "Sucesso", f"Usuario '{nome}' atualizado com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Nao foi possÃ­vel atualizar o usuÃ¡rio. Revise os dados e tente novamente.")
            else:
                response = api_client.criar_usuario(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", f"Usuario '{nome}' criado com sucesso.\n\nSenha padrao: 123456")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Nao foi possÃ­vel criar o usuÃ¡rio. Revise os dados e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Nao foi possÃ­vel salvar o usuÃ¡rio.\n\nDetalhes: {e}")


