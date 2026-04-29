from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QSpinBox,
                               QTextEdit, QMessageBox, QHeaderView, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QCursor
from datetime import datetime
from api_client import api_client
from widgets.toast_notification import notification_manager
from widgets.filter_utils import is_all_option, same_filter_value, same_text
from widgets.table_utils import configure_data_table, number_item


class MovimentacoesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.movimentacoes = []
        self.movimentacoes_cache = []
        self.materiais = []
        self.colaboradores = []
        self.colaboradores = []
        self._loaded = False
        self.init_ui()

    def on_show(self):
        if not self._loaded:
            self.carregar_colaboradores()
            self.carregar_empresas()
            self.carregar_materiais()
            self.carregar_movimentacoes()
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
        self.empresa_filter.addItem('Todas as empresas')
        self.empresa_filter.currentIndexChanged.connect(self.filtrar_movimentacoes)
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
        configure_data_table(self.tabela, stretch_columns=(1, 7))

        layout.addWidget(self.tabela)

        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()

        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_movimentacao)
        acoes.addWidget(self.deletar_btn)

        layout.addLayout(acoes)

    def carregar_empresas(self):
        """Carrega a lista de empresas para filtro"""
        try:
            self.empresas = api_client.get_empresas()
            self.empresa_filter.clear()
            self.empresa_filter.addItem('Todas as empresas')
            for emp in self.empresas:
                if emp and emp.strip():
                    self.empresa_filter.addItem(emp)
            print(f'✅ Empresas carregadas para filtro: {len(self.empresas)}')
        except Exception as e:
            print(f'❌ Erro ao carregar empresas: {e}')

    def carregar_materiais(self):
        """Carrega a lista de materiais para o filtro"""
        try:
            self.materiais = api_client.listar_materiais_para_movimentacao()
            self.material_filter.clear()
            self.material_filter.addItem("Todos os materiais")
            for mat in self.materiais:
                self.material_filter.addItem(f"{mat.get('nome', '')} - {mat.get('empresa', '')}", mat.get("id"))
        except Exception as e:
            print(f"Erro ao carregar materiais: {e}")

    def carregar_colaboradores(self):
        """Carrega a lista de colaboradores"""
        try:
            self.colaboradores = api_client.listar_colaboradores()
        except Exception as e:
            print(f"Erro ao carregar colaboradores: {e}")

    def carregar_movimentacoes(self):
        """Carrega a lista de movimentações do backend"""
        try:
            self.movimentacoes = api_client.listar_movimentacoes()
            self.movimentacoes_cache = self.movimentacoes.copy()
            self.atualizar_tabela(self.movimentacoes)
            print(f"✅ Movimentações carregadas: {len(self.movimentacoes)}")
        except Exception as e:
            print(f"❌ Erro ao carregar movimentações: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar movimentações: {e}")

    def filtrar_movimentacoes(self):
        """Filtra as movimentações com base nos filtros"""
        tipo = self.tipo_filter.currentText()
        empresa = self.empresa_filter.currentText()
        material_id = self.material_filter.currentData()

        filtered = []
        for mov in self.movimentacoes_cache:
            # Filtro por tipo
            if not is_all_option(tipo) and not same_filter_value(mov.get("tipo", ""), tipo):
                continue

            # Filtro por empresa
            if not is_all_option(empresa) and not same_text(mov.get('empresa'), empresa):
                continue

            # Filtro por material
            if material_id and mov.get("material_id") != material_id:
                continue

            filtered.append(mov)

        self.atualizar_tabela(filtered)

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


    def nova_movimentacao(self):
        dialog = MovimentacaoDialog(materiais=self.materiais, colaboradores=self.colaboradores, parent=self)
        if dialog.exec():
            self.carregar_movimentacoes()
            self.carregar_materiais()
            self.carregar_colaboradores()

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

        # Material
        self.material_combo = QComboBox()
        self.material_combo.setEditable(False)
        self.material_combo.setInsertPolicy(QComboBox.NoInsert)
        for mat in self.materiais:
            self.material_combo.addItem(
                f"{mat.get('nome', '')} - Estoque: {mat.get('quantidade', 0)} - {mat.get('empresa', '')}",
                mat.get("id")
            )
        form_layout.addRow("Material:", self.material_combo)

        # Tipo (Entrada/Saída)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["entrada", "saida"])
        self.tipo_combo.currentTextChanged.connect(self.on_tipo_changed)
        form_layout.addRow("Tipo:", self.tipo_combo)

        # Quantidade
        self.quantidade_spin = QSpinBox()
        self.quantidade_spin.setRange(1, 999999)
        self.quantidade_spin.setValue(1)
        form_layout.addRow("Quantidade:", self.quantidade_spin)

        # Empresa
        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        form_layout.addRow('Empresa:', self.empresa_combo)

        # Destinatário (com colaboradores)
        self.destinatario_label = QLabel("Colaborador:")
        self.destinatario_combo = QComboBox()
        self.destinatario_combo.setEditable(False)
        self.destinatario_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_colaboradores_no_combo()
        form_layout.addRow(self.destinatario_label, self.destinatario_combo)

        # Observação
        self.observacao_edit = QTextEdit()
        self.observacao_edit.setMaximumHeight(80)
        self.observacao_edit.setPlaceholderText("Observação sobre a movimentação...")
        form_layout.addRow("Observação:", self.observacao_edit)

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
            self.destinatario_label.setText("Fornecedor/Origem:")
            # ✅ Para entrada, permitir digitar (fornecedor pode não estar cadastrado)
            self.destinatario_combo.setEditable(True)
            self.destinatario_combo.clear()
            self.destinatario_combo.addItem("")
            self.destinatario_combo.setPlaceholderText("Digite o nome do fornecedor")
        else:
            self.destinatario_label.setText("Colaborador:")
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
            QMessageBox.warning(self, "AtenÃ§Ã£o", "Digite a sua senha para confirmar o registro.")
            return False

        if not api_client.confirmar_senha_atual(senha):
            QMessageBox.warning(self, "Senha incorreta", "Nao foi possivel confirmar a senha informada.")
            return False

        return True

    def salvar(self):
        # Obter ID do material selecionado
        idx = self.material_combo.currentIndex()
        if idx < 0 or idx >= len(self.materiais):
            QMessageBox.warning(self, "Atenção", "Selecione um material válido!")
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
                QMessageBox.warning(self, "Atenção", "Informe o fornecedor/origem!")
            else:
                QMessageBox.warning(self, "Atenção", "Selecione um colaborador!")
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
                QMessageBox.information(self, "Sucesso", f"Movimentação de {tipo} registrada com sucesso!")
                self.accept()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao registrar movimentação")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
