from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QCheckBox,
                               QMessageBox, QHeaderView, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QCursor
from api_client import api_client
from widgets.filter_utils import is_all_option, same_filter_value, same_text


class UsuariosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuarios = []
        self.usuarios_cache = []
        self._loaded = False
        self.init_ui()

    def on_show(self):
        if not self._loaded:
            self.carregar_empresas()
            self.carregar_usuarios()
            self.carregar_cargos()
            self._loaded = True

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("👥 Usuários do Sistema")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()







        # Botão Novo Usuário
        self.novo_btn = QPushButton("+ Novo Usuário")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.novo_usuario)
        header.addWidget(self.novo_btn)

        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_usuarios)
        header.addWidget(self.atualizar_btn)

        layout.addLayout(header)

        # Filtros
        filtros = QHBoxLayout()

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
        self. cargo_filter.currentIndexChanged.connect(self.filtrar_usuarios)
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
        self.nivel_filter.addItem("Todos os níveis")
        self.nivel_filter.addItems(["admin", "gerente", "usuario"])
        self.nivel_filter.currentTextChanged.connect(self.filtrar_usuarios)
        filtros.addWidget(QLabel("Nível:"))
        filtros.addWidget(self.nivel_filter)

        filtros.addStretch()

        layout.addLayout(filtros)

        # Tabela de usuários
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)

        self.tabela.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        headers = ["ID", "Código", "Nome", "Cargo", "Empresa", "Nível", "Status", "Primeiro Acesso"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(self.tabela)

        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()

        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_usuario)
        acoes.addWidget(self.editar_btn)

        self.alterar_senha_btn = QPushButton("🔐 Alterar Senha")
        self.alterar_senha_btn.clicked.connect(self.alterar_senha)
        acoes.addWidget(self.alterar_senha_btn)

        self.resetar_senha_btn = QPushButton("🔑 Resetar Senha")
        self.resetar_senha_btn.clicked.connect(self.resetar_senha)
        acoes.addWidget(self.resetar_senha_btn)

        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_usuario)
        acoes.addWidget(self.deletar_btn)

        layout.addLayout(acoes)

    def carregar_usuarios(self):
        """Carrega a lista de usuários do backend"""
        try:
            self.usuarios = api_client.listar_usuarios()
            self.usuarios_cache = self.usuarios.copy()
            self.atualizar_tabela(self.usuarios)
            print(f"✅ Usuários carregados: {len(self.usuarios)}")
        except Exception as e:
            print(f"❌ Erro ao carregar usuários: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar usuários: {e}")

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
            print(f"❌ Erro ao carregar empresas: {e}")

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
            print(f"❌ Erro ao carregar cargos: {e}")

    def filtrar_usuarios(self):
        """Filtra os usuários com base nos filtros"""
        empresa = self.empresa_filter.currentText()
        cargo = self.cargo_filter.currentText()
        status = self.ativo_filter.currentText().lower()
        nivel = self.nivel_filter.currentText()


        filtered = []
        for usuario in self.usuarios_cache:
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

    def atualizar_tabela(self, usuarios):
        """Atualiza a tabela com a lista de usuários"""
        self.tabela.setRowCount(len(usuarios))

        for row, usuario in enumerate(usuarios):
            self.tabela.setItem(row, 0, QTableWidgetItem(str(usuario.get("id", ""))))
            self.tabela.setItem(row, 1, QTableWidgetItem(usuario.get("codigo", "")))
            self.tabela.setItem(row, 2, QTableWidgetItem(usuario.get("nome", "")))
            self.tabela.setItem(row, 3, QTableWidgetItem(usuario.get("cargo", "-")))
            self.tabela.setItem(row, 4, QTableWidgetItem(usuario.get("empresa", "-")))

            nivel_item = QTableWidgetItem(usuario.get("nivel_acesso", "usuario").upper())
            if usuario.get("nivel_acesso") == "admin":
                nivel_item.setForeground(QColor(231, 111, 81))
            elif usuario.get("nivel_acesso") == "gerente":
                nivel_item.setForeground(QColor(244, 162, 97))
            else:
                nivel_item.setForeground(QColor(42, 157, 143))
            self.tabela.setItem(row, 5, nivel_item)

            status_item = QTableWidgetItem("Ativo" if usuario.get("ativo", True) else "Inativo")
            if not usuario.get("ativo", True):
                status_item.setForeground(QColor(231, 111, 81))
            else:
                status_item.setForeground(QColor(42, 157, 143))
            self.tabela.setItem(row, 6, status_item)

            primeiro_acesso = "Sim" if usuario.get("primeiro_acesso", False) else "Não"
            self.tabela.setItem(row, 7, QTableWidgetItem(primeiro_acesso))

    def novo_usuario(self):
        """Abre diálogo para criar novo usuário com código automático"""

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        try:
            response = api_client.get_proximo_codigo()
            proximo_codigo = response.get("proximo_codigo", "1")
        except Exception as e:
            print(f"❌ Erro ao buscar próximo código: {e}")
            proximo_codigo = "1"

        QApplication.restoreOverrideCursor()

        dialog = UsuarioDialog(proximo_codigo=proximo_codigo, parent=self)
        if dialog.exec():
            self.carregar_usuarios()

    def editar_usuario(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um usuário para editar")
            return

        usuario_id = int(self.tabela.item(current_row, 0).text())
        usuario = next((u for u in self.usuarios if u["id"] == usuario_id), None)

        if usuario:
            dialog = UsuarioDialog(usuario_data=usuario, parent=self)
            if dialog.exec():
                self.carregar_usuarios()

    def alterar_senha(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um usuário para alterar a senha")
            return

        usuario_id = int(self.tabela.item(current_row, 0).text())
        usuario_nome = self.tabela.item(current_row, 2).text()
        usuario_codigo = self.tabela.item(current_row, 1).text()

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

        info_label = QLabel(f"Alterando senha do usuário: <b>{usuario_nome}</b><br>Código: <b>{usuario_codigo}</b>")
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

        requisitos_label = QLabel("🔒 Requisitos:<br>• Mínimo de 6 caracteres")
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
                QMessageBox.warning(senha_dialog, "Atenção", "Digite a nova senha!")
                return

            if len(nova_senha) < 6:
                QMessageBox.warning(senha_dialog, "Atenção", "A senha deve ter no mínimo 6 caracteres!")
                return

            if nova_senha != confirmar_senha:
                QMessageBox.warning(senha_dialog, "Atenção", "As senhas não conferem!")
                return

            try:
                if api_client.alterar_senha_usuario(usuario_id, nova_senha):
                    QMessageBox.information(senha_dialog, "Sucesso", f"Senha do usuário '{usuario_nome}' alterada com sucesso!")
                    senha_dialog.accept()
                    self.carregar_usuarios()
                else:
                    QMessageBox.warning(senha_dialog, "Erro", "Erro ao alterar senha")
            except Exception as e:
                QMessageBox.critical(senha_dialog, "Erro", f"Erro ao alterar senha: {e}")

        btn_alterar.clicked.connect(confirmar_alteracao)
        senha_dialog.exec()

    def resetar_senha(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um usuário para resetar a senha")
            return

        usuario_id = int(self.tabela.item(current_row, 0).text())
        usuario_nome = self.tabela.item(current_row, 2).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar reset de senha",
            f"Tem certeza que deseja resetar a senha do usuário '{usuario_nome}'?\n\nA nova senha será '123456'.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                if api_client.resetar_senha_usuario(usuario_id):
                    QMessageBox.information(self, "Sucesso", f"Senha do usuário '{usuario_nome}' resetada para '123456'!")
                    self.carregar_usuarios()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao resetar senha")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao resetar senha: {e}")

    def deletar_usuario(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um usuário para deletar")
            return

        usuario_id = int(self.tabela.item(current_row, 0).text())
        usuario_nome = self.tabela.item(current_row, 2).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar o usuário '{usuario_nome}'?\n\nEsta ação não poderá ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                if api_client.deletar_usuario(usuario_id):
                    QMessageBox.information(self, "Sucesso", "Usuário deletado com sucesso!")
                    self.carregar_usuarios()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao deletar usuário")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


class UsuarioDialog(QDialog):
    def __init__(self, usuario_data=None, proximo_codigo=None, parent=None):
        super().__init__(parent)
        self.dados_item = usuario_data
        self.proximo_codigo = proximo_codigo
        self.setWindowTitle("Novo Usuário" if not usuario_data else "Editar Usuário")
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

        self.codigo_edit = QLineEdit()
        self.codigo_edit.setPlaceholderText("Código numérico único (ex: 1001)")
        form_layout.addRow("Código:", self.codigo_edit)

        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Nome completo")
        form_layout.addRow("Nome:", self.nome_edit)

        self.cargo_combo = QComboBox()
        self.cargo_combo.setEditable(False)
        self.cargo_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_cargos_combo()
        form_layout.addRow("Cargo:", self.cargo_combo)

        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_empresas_combo()
        form_layout.addRow("Empresa:", self.empresa_combo)

        self.nivel_combo = QComboBox()
        self.nivel_combo.addItems(["admin", "gerente", "usuario"])
        self.nivel_combo.setToolTip(
            "admin: Acesso total\n"
            "gerente: Pode aprovar pedidos\n"
            "usuario: Acesso básico"
        )
        form_layout.addRow("Nível de Acesso:", self.nivel_combo)

        self.ativo_check = QCheckBox("Usuário ativo")
        self.ativo_check.setChecked(True)
        form_layout.addRow("", self.ativo_check)

        if not self.dados_item:
            senha_info = QLabel("⚠️ A senha padrão será '123456'.\nO usuário deverá trocar no primeiro acesso.")
            senha_info.setStyleSheet("color: #64748b; font-size: 11px;")
            form_layout.addRow("", senha_info)

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
            self.cargo_combo.addItem('') # Opção vazia (opcional)
            for cargo in cargos:
                if cargo and cargo.strip():
                    self.cargo_combo.addItem(cargo)
            print(f'✅ Cargos carregados: {len(cargos)}')
        except Exception as e:
            print(f'❌ Erro ao carregar cargos: {e}')
            # Fallback em caso de erro
            default_cargos = ['Analista', 'Coordenador', 'Gerente', 'Assistente', 'Técnico']
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
            print(f'❌ Erro ao carregar empresas: {e}')
            # Fallback em caso de erro
            default_empresas = ['Matriz ', 'Filial 1', 'Filial 2', 'Filial 3']
            for emp in default_empresas:
                self.empresa_combo.addItem(emp)

    def carregar_dados_edicao(self):
        """Carrega os dados do usuário para edição"""
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
            QMessageBox.warning(self, "Atenção", "O código é obrigatório!")
            return

        if not nome:
            QMessageBox.warning(self, "Atenção", "O nome é obrigatório!")
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
                    QMessageBox.information(self, "Sucesso", "Usuário atualizado com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao atualizar usuário")
            else:
                response = api_client.criar_usuario(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Usuário criado com sucesso!\n\nSenha padrão: 123456")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao criar usuário")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
