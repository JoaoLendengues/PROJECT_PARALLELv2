from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QSpinBox,
                               QTextEdit, QMessageBox, QHeaderView, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QCursor
from datetime import datetime
from api_client import api_client
from access_control import has_action_access
from widgets.company_filter_utils import company_filter_ready, populate_company_filter, selected_company_value
from widgets.form_feedback import focus_invalid_field, optional_label, required_field_message, required_hint_label, required_label
from widgets.toast_notification import notification_manager
from widgets.filter_utils import contains_text, is_all_option, same_filter_value, same_text
from widgets.table_utils import configure_data_table, number_item, refresh_data_table_layout
from user_preferences import (
    apply_combo_data,
    apply_combo_text,
    apply_table_sort_state,
    get_table_sort_state,
    get_widget_preferences,
    save_widget_preferences,
)


class MovimentacoesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario = {}
        self.movimentacoes = []
        self.movimentacoes_cache = []
        self.materiais = []
        self.colaboradores = []
        self.colaboradores = []
        self._loaded = False
        self._restoring_preferences = False
        self._saved_preferences = {}
        self.init_ui()

    def on_show(self):
        if not self._loaded:
            self.carregar_empresas()
            self._carregar_preferencias()
            self._aplicar_preferencias_salvas()
            if self.empresa_pronta():
                empresa = self.empresa_param()
                self.carregar_colaboradores(empresa=empresa)
                self.carregar_materiais(empresa=empresa)
                self._aplicar_preferencias_dependentes()
                self.carregar_movimentacoes()
            else:
                self._mostrar_prompt_empresa()
            self._loaded = True

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("📊 Movimentações")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()

        # Botão Nova Movimentação
        self.novo_btn = QPushButton("+ Nova Movimentação")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.nova_movimentacao)
        header.addWidget(self.novo_btn)

        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_movimentacoes)
        header.addWidget(self.atualizar_btn)

        layout.addLayout(header)

        # Barra de pesquisa e filtros
        filtros = QHBoxLayout()

        filtros.addWidget(QLabel("Busca:"))
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setPlaceholderText("Pesquisar por material, colaborador, observação...")
        self.pesquisa_edit.setMaximumWidth(320)
        self.pesquisa_edit.textChanged.connect(self.filtrar_movimentacoes)
        filtros.addWidget(self.pesquisa_edit)

        filtros.addSpacing(20)

        # Filtro Tipo
        filtros.addWidget(QLabel("Tipo:"))
        self.tipo_filter = QComboBox()
        self.tipo_filter.addItems(["Todos", "Entrada", "Saída"])
        self.tipo_filter.currentTextChanged.connect(self.filtrar_movimentacoes)
        filtros.addWidget(self.tipo_filter)

        # Filtro Empresa
        filtros.addWidget(QLabel('Empresa:'))
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(150)
        self.empresa_filter.currentIndexChanged.connect(self.ao_alterar_empresa)
        filtros.addWidget(self.empresa_filter)

        filtros.addSpacing(20)

        # Filtro Material
        filtros.addWidget(QLabel("Material:"))
        self.material_filter = QComboBox()
        self.material_filter.addItem("Todos os materiais")
        self.material_filter.currentTextChanged.connect(self.filtrar_movimentacoes)
        filtros.addWidget(self.material_filter)

        filtros.addStretch()

        layout.addLayout(filtros)

        self.empresa_prompt = QLabel('Selecione uma empresa ou "Todas as empresas" para carregar as movimentações.')
        self.empresa_prompt.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(self.empresa_prompt)

        # Tabela de movimentações com estilo melhorado
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
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

        headers = ["ID", "Material", "Tipo", "Quantidade", "Empresa", "Colaborador", "Data/Hora", "Observação"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        configure_data_table(
            self.tabela,
            stretch_columns=(1, 7),
            minimum_section_size=88,
            minimum_widths={
                0: 72,
                1: 220,
                2: 110,
                3: 100,
                4: 170,
                5: 180,
                6: 155,
                7: 240,
            },
        )
        self.tabela.horizontalHeader().sortIndicatorChanged.connect(self._ao_ordenar_tabela)

        layout.addWidget(self.tabela)

        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()

        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_movimentacao)
        acoes.addWidget(self.deletar_btn)

        layout.addLayout(acoes)
        self.aplicar_permissoes()

    def set_usuario(self, usuario):
        self.usuario = usuario or {}
        self._carregar_preferencias()
        self.aplicar_permissoes()
        if self._loaded:
            self._aplicar_preferencias_salvas()
            if self.empresa_pronta():
                empresa = self.empresa_param()
                self.carregar_colaboradores(empresa=empresa)
                self.carregar_materiais(empresa=empresa)
                self._aplicar_preferencias_dependentes()
                self.carregar_movimentacoes()
            else:
                self._mostrar_prompt_empresa()

    def aplicar_permissoes(self):
        pode_deletar = has_action_access(self.usuario, "movimentacoes.deletar")
        if hasattr(self, "deletar_btn"):
            self.deletar_btn.setVisible(pode_deletar)

    def empresa_pronta(self):
        return company_filter_ready(self.empresa_filter)

    def empresa_param(self):
        return selected_company_value(self.empresa_filter)

    def _carregar_preferencias(self):
        self._saved_preferences = get_widget_preferences(self.usuario, "movimentacoes")

    def _aplicar_preferencias_salvas(self):
        self._restoring_preferences = True
        try:
            self.pesquisa_edit.setText(str(self._saved_preferences.get("busca") or ""))
            apply_combo_text(self.tipo_filter, self._saved_preferences.get("tipo"))
            apply_combo_data(self.empresa_filter, self._saved_preferences.get("empresa"))
        finally:
            self._restoring_preferences = False

    def _aplicar_preferencias_dependentes(self):
        self._restoring_preferences = True
        try:
            apply_combo_data(self.material_filter, self._saved_preferences.get("material_id"))
        finally:
            self._restoring_preferences = False

    def _preferencias_atuais(self):
        return {
            "busca": self.pesquisa_edit.text().strip(),
            "tipo": self.tipo_filter.currentText(),
            "empresa": self.empresa_filter.currentData(),
            "material_id": self.material_filter.currentData(),
            "sort": get_table_sort_state(self.tabela),
        }

    def _salvar_preferencias(self):
        if self._restoring_preferences:
            return
        self._saved_preferences = self._preferencias_atuais()
        save_widget_preferences(self.usuario, "movimentacoes", self._saved_preferences)

    def _ao_ordenar_tabela(self, *_args):
        self._salvar_preferencias()

    def _mostrar_prompt_empresa(self):
        self.movimentacoes = []
        self.movimentacoes_cache = []
        self.tabela.setRowCount(0)
        self.material_filter.blockSignals(True)
        self.material_filter.clear()
        self.material_filter.addItem("Todos os materiais")
        self.material_filter.blockSignals(False)
        self.empresa_prompt.setVisible(True)

    def ao_alterar_empresa(self):
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            self._salvar_preferencias()
            return

        empresa = self.empresa_param()
        self.carregar_colaboradores(empresa=empresa)
        self.carregar_materiais(empresa=empresa)
        self.carregar_movimentacoes()
        self._salvar_preferencias()

    def carregar_empresas(self):
        """Carrega a lista de empresas para filtro"""
        try:
            self.empresas = api_client.get_empresas()
            populate_company_filter(self.empresa_filter, self.empresas)
            print(f'✅ Empresas carregadas para filtro: {len(self.empresas)}')
        except Exception as e:
            print(f'❌ Erro ao carregar empresas: {e}')

    def carregar_materiais(self, empresa=None):
        """Carrega a lista de materiais para o filtro"""
        try:
            self.materiais = api_client.listar_materiais_para_movimentacao(empresa=empresa)
            self.material_filter.clear()
            self.material_filter.addItem("Todos os materiais")
            for mat in self.materiais:
                self.material_filter.addItem(f"{mat.get('nome', '')} - {mat.get('empresa', '')}", mat.get("id"))
            self._aplicar_preferencias_dependentes()
        except Exception as e:
            print(f"Erro ao carregar materiais: {e}")

    def carregar_colaboradores(self, empresa=None):
        """Carrega a lista de colaboradores"""
        try:
            self.colaboradores = api_client.listar_colaboradores(empresa=empresa)
        except Exception as e:
            print(f"Erro ao carregar colaboradores: {e}")

    def carregar_movimentacoes(self):
        """Carrega a lista de movimentações do backend"""
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        try:
            self.movimentacoes = api_client.listar_movimentacoes(empresa=self.empresa_param())
            self.movimentacoes_cache = self.movimentacoes.copy()
            self.filtrar_movimentacoes()
            self.empresa_prompt.setVisible(False)
            print(f"✅ Movimentações carregadas: {len(self.movimentacoes)}")
        except Exception as e:
            print(f"❌ Erro ao carregar movimentações: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar movimentações: {e}")

    def filtrar_movimentacoes(self):
        """Filtra as movimentações com base nos filtros"""
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        tipo = self.tipo_filter.currentText()
        empresa = self.empresa_filter.currentText()
        material_id = self.material_filter.currentData()
        search_text = self.pesquisa_edit.text()

        filtered = []
        for mov in self.movimentacoes_cache:
            # Filtro por tipo
            if not is_all_option(tipo) and not same_filter_value(mov.get("tipo", ""), tipo):
                continue

            # Filtro por empresa
            if self.empresa_param() is None and not is_all_option(empresa) and not same_text(mov.get('empresa'), empresa):
                continue

            # Filtro por material
            if material_id and mov.get("material_id") != material_id:
                continue

            if not contains_text(
                search_text,
                mov.get("id", ""),
                mov.get("material_nome", ""),
                mov.get("tipo", ""),
                mov.get("empresa", ""),
                mov.get("destinatario", ""),
                mov.get("observacao", ""),
            ):
                continue

            filtered.append(mov)

        self.atualizar_tabela(filtered)
        self._salvar_preferencias()

    def atualizar_tabela(self, movimentacoes):
        """Atualiza a tabela com a lista de movimentações"""
        self.tabela.setRowCount(len(movimentacoes))

        for row, mov in enumerate(movimentacoes):
            self.tabela.setItem(row, 0, number_item(mov.get("id", "")))
            self.tabela.setItem(row, 1, QTableWidgetItem(mov.get("material_nome", "-")))

            tipo_item = QTableWidgetItem(mov.get("tipo", "").upper())
            if mov.get("tipo") == "entrada":
                tipo_item.setForeground(QColor(42, 157, 143))
            else:
                tipo_item.setForeground(QColor(231, 111, 81))
            self.tabela.setItem(row, 2, tipo_item)

            self.tabela.setItem(row, 3, number_item(mov.get("quantidade", 0)))
            self.tabela.setItem(row, 4, QTableWidgetItem(mov.get("empresa", "-")))
            self.tabela.setItem(row, 5, QTableWidgetItem(mov.get("destinatario", "-")))

            data_hora = mov.get("data_hora", "")
            if data_hora:
                data_hora = data_hora[:16].replace("T", " ")
            self.tabela.setItem(row, 6, QTableWidgetItem(data_hora))

            # Tratar observação None
            obs = mov.get('observacao')
            if obs is None:
                obs = '-'
            else:
                obs = str(obs)[:50]
            self.tabela.setItem(row, 7, QTableWidgetItem(obs))

        apply_table_sort_state(self.tabela, self._saved_preferences.get("sort"))
        refresh_data_table_layout(self.tabela)


    def nova_movimentacao(self):
        if not self.empresa_pronta():
            QMessageBox.warning(self, "Atenção", "Selecione uma empresa antes de registrar movimentações.")
            return
        dialog = MovimentacaoDialog(materiais=self.materiais, colaboradores=self.colaboradores, parent=self)
        if dialog.exec():
            self.carregar_movimentacoes()
            self.carregar_materiais(empresa=self.empresa_param())
            self.carregar_colaboradores(empresa=self.empresa_param())

    def deletar_movimentacao(self):
        """Deleta a movimentação selecionada (apenas administradores)"""
        from widgets.toast_notification import notification_manager

        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma movimentação para deletar")
            return

        # Buscar os dados diretamente da tabela
        mov_id = int(self.tabela.item(current_row, 0).text())
        mov_material = self.tabela.item(current_row, 1).text()
        mov_tipo = self.tabela.item(current_row, 2).text()
        mov_qtd = self.tabela.item(current_row, 3).text()
        mov_data = self.tabela.item(current_row, 6).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar esta movimentação?\n\n"
            f"📦 Material: {mov_material}\n"
            f"📊 Tipo: {mov_tipo}\n"
            f"🔢 Quantidade: {mov_qtd}\n"
            f"📅 Data: {mov_data}\n\n"
            f"⚠️ ATENÇÃO: Esta ação NÃO reverte o estoque e só pode ser feita por administradores.\n"
            f"⚠️ Esta ação não pode ser desfeita!",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                # Mostrar cursor de espera
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

                success = api_client.deletar_movimentacao(mov_id)

                QApplication.restoreOverrideCursor()

                if success:
                    notification_manager.success("Movimentação deletada com sucesso!", self.window(), 3000)
                    self.carregar_movimentacoes()  # Recarregar a lista
                else:
                    notification_manager.error("Erro ao deletar movimentação. Verifique suas permissões.", self.window(), 3000)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Erro", f"Erro ao deletar movimentação: {e}")

class ConfirmacaoSenhaDialog(QDialog):
    def __init__(self, resumo, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirmar senha")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        mensagem = QLabel(
            "Para registrar esta movimentacao, confirme a sua senha.\n\n"
            f"{resumo}"
        )
        mensagem.setWordWrap(True)
        layout.addWidget(mensagem)

        form_layout = QFormLayout()
        self.senha_edit = QLineEdit()
        self.senha_edit.setEchoMode(QLineEdit.Password)
        self.senha_edit.returnPressed.connect(self.accept)
        form_layout.addRow("Senha:", self.senha_edit)
        layout.addLayout(form_layout)

        botoes = QHBoxLayout()
        botoes.addStretch()

        confirmar_btn = QPushButton("Confirmar")
        confirmar_btn.clicked.connect(self.accept)
        cancelar_btn = QPushButton("Cancelar")
        cancelar_btn.clicked.connect(self.reject)

        botoes.addWidget(confirmar_btn)
        botoes.addWidget(cancelar_btn)
        layout.addLayout(botoes)

    def senha(self):
        return self.senha_edit.text().strip()


class MovimentacaoDialog(QDialog):
    def __init__(self, materiais=None, colaboradores=None, parent=None):
        super().__init__(parent)
        self.materiais = materiais or []
        self.colaboradores = colaboradores or []
        self.setWindowTitle("Nova Movimentação")
        self.setModal(True)
        self.setMinimumWidth(500)

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
        self.carregar_empresas() # Buscar empresas do backend

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        layout.addWidget(required_hint_label())

        # Material
        self.material_combo = QComboBox()
        self.material_combo.setEditable(False)
        self.material_combo.setInsertPolicy(QComboBox.NoInsert)
        for mat in self.materiais:
            self.material_combo.addItem(
                f"{mat.get('nome', '')} - Estoque: {mat.get('quantidade', 0)} - {mat.get('empresa', '')}",
                mat.get("id")
            )
        form_layout.addRow(required_label("Material:"), self.material_combo)
        # Tipo (Entrada/Saída)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["entrada", "saida"])
        self.tipo_combo.currentTextChanged.connect(self.on_tipo_changed)
        form_layout.addRow(required_label("Tipo:"), self.tipo_combo)
        # Quantidade
        self.quantidade_spin = QSpinBox()
        self.quantidade_spin.setRange(1, 999999)
        self.quantidade_spin.setValue(1)
        form_layout.addRow(required_label("Quantidade:"), self.quantidade_spin)
        # Empresa
        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        form_layout.addRow(required_label('Empresa:'), self.empresa_combo)
        # Destinatário (com colaboradores)
        self.destinatario_label = required_label("Colaborador:")
        self.destinatario_combo = QComboBox()
        self.destinatario_combo.setEditable(False)
        self.destinatario_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_colaboradores_no_combo()
        form_layout.addRow(self.destinatario_label, self.destinatario_combo)

        # Observação
        self.observacao_edit = QTextEdit()
        self.observacao_edit.setMaximumHeight(80)
        self.observacao_edit.setPlaceholderText("Observação sobre a movimentação...")
        form_layout.addRow(optional_label("Observação:"), self.observacao_edit)

        layout.addLayout(form_layout)

        # Status do estoque (para informação)
        self.estoque_label = QLabel("")
        self.estoque_label.setStyleSheet("color: #64748b; font-size: 12px; margin-top: 10px;")
        layout.addWidget(self.estoque_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.salvar_btn = QPushButton("Registrar")
        self.salvar_btn.clicked.connect(self.salvar)

        cancelar_btn = QPushButton("Cancelar")
        cancelar_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.salvar_btn)
        btn_layout.addWidget(cancelar_btn)

        layout.addLayout(btn_layout)

        # Atualizar informação de estoque ao mudar material
        self.material_combo.currentIndexChanged.connect(self.atualizar_info_estoque)
        self.atualizar_info_estoque()

    def carregar_empresas(self):
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
            default_empresas = ['Matriz', 'Filial 1', 'Filial 2', 'Filial 3']
            for emp in default_empresas:
                self.empresa_combo.addItem(emp)

    def carregar_colaboradores_no_combo(self):
        """Carrega os colaboradores no combo box"""
        try:
            self.destinatario_combo.clear()
            # Adicionar opção de digitar manualmente
            for colab in self.colaboradores:
                if colab.get("ativo", True):
                    self.destinatario_combo.addItem(colab.get("nome", ""))
        except Exception as e:
            print(f"Erro ao carregar colaboradores: {e}")

    def on_tipo_changed(self):
        """Altera o texto do destinatário conforme o tipo"""
        tipo = self.tipo_combo.currentText()
        if tipo == "entrada":
            self.destinatario_label.setText('Fornecedor/Origem: <span style="color: #ef4444;">*</span>')
            # ✅ Para entrada, permitir digitar (fornecedor pode não estar cadastrado)
            self.destinatario_combo.setEditable(True)
            self.destinatario_combo.clear()
            self.destinatario_combo.addItem("")
            self.destinatario_combo.setPlaceholderText("Digite o nome do fornecedor")
        else:
            self.destinatario_label.setText('Colaborador: <span style="color: #ef4444;">*</span>')
            # ✅ Para saída, apenas seleção (colaboradores cadastrados)
            self.destinatario_combo.setEditable(False)
            self.destinatario_combo.setInsertPolicy(QComboBox.NoInsert)
            self.carregar_colaboradores_no_combo()

    def atualizar_info_estoque(self):
        """Atualiza a label com a informação do estoque atual"""
        idx = self.material_combo.currentIndex()
        if idx >= 0 and idx < len(self.materiais):
            material = self.materiais[idx]
            quantidade = material.get("quantidade", 0)
            self.estoque_label.setText(f"📦 Estoque atual: {quantidade} unidades")
        else:
            self.estoque_label.setText("")

    def confirmar_registro_senha(self, material_nome, tipo, quantidade):
        resumo = (
            f"Material: {material_nome}\n"
            f"Tipo: {tipo.upper()}\n"
            f"Quantidade: {quantidade}"
        )

        dialog = ConfirmacaoSenhaDialog(resumo, self)
        if dialog.exec() != QDialog.Accepted:
            return False

        senha = dialog.senha()
        if not senha:
            focus_invalid_field(dialog.senha_edit)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Senha"))
            return False

        if not api_client.confirmar_senha_atual(senha):
            QMessageBox.warning(self, "Senha incorreta", "Não foi possível confirmar a senha informada.")
            return False

        return True

    def salvar(self):
        # Obter ID do material selecionado
        idx = self.material_combo.currentIndex()
        if idx < 0 or idx >= len(self.materiais):
            focus_invalid_field(self.material_combo)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Material"))
            return

        material_id = self.materiais[idx].get("id")
        tipo = self.tipo_combo.currentText()
        quantidade = self.quantidade_spin.value()
        empresa = self.empresa_combo.currentText()
        destinatario = self.destinatario_combo.currentText().strip()
        observacao = self.observacao_edit.toPlainText().strip()

        # Verificar destinatário
        if not destinatario:
            if tipo == "entrada":
                focus_invalid_field(self.destinatario_combo)
                QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Fornecedor/Origem"))
            else:
                focus_invalid_field(self.destinatario_combo)
                QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Colaborador"))
            return

        # Verificar estoque para saída
        if tipo == "saida":
            material = self.materiais[idx]
            if material.get("quantidade", 0) < quantidade:
                QMessageBox.warning(
                    self,
                    "Atenção",
                    f"Estoque insuficiente!\nDisponível: {material.get('quantidade', 0)}"
                )
                return

        material_nome = self.materiais[idx].get("nome", "")
        if not self.confirmar_registro_senha(material_nome, tipo, quantidade):
            return

        dados = {
            "material_id": material_id,
            "tipo": tipo,
            "quantidade": quantidade,
            "empresa": empresa,
            "destinatario": destinatario,
            "observacao": observacao or None
        }

        try:
            response = api_client.criar_movimentacao(dados)
            if response:
                QMessageBox.information(self, "Sucesso", f"Movimentacao de {tipo} para '{material_nome}' registrada com sucesso.")
                self.accept()
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível registrar a movimentação. Revise os dados e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar a movimentação.\n\nDetalhes: {e}")
