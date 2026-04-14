from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QTextEdit,
                               QMessageBox, QHeaderView, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QCursor
from api_client import api_client
from widgets.toast_notification import notification_manager


class MaquinasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.maquinas = []
        self.departamentos = []
        self.empresas = []  # NOVO: lista de empresas
        self.init_ui()
        self.carregar_departamentos()
        self.carregar_empresas()  # NOVO
        self.carregar_maquinas()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)
        
        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("🖥️ Máquinas")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()
        
        # Botão Nova Máquina
        self.novo_btn = QPushButton("+ Nova Máquina")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.nova_maquina)
        header.addWidget(self.novo_btn)
        
        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_maquinas)
        header.addWidget(self.atualizar_btn)
        
        layout.addLayout(header)
        
        # Barra de pesquisa
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setPlaceholderText("🔍 Pesquisar por nome, modelo, MAC...")
        self.pesquisa_edit.setMaximumWidth(350)
        self.pesquisa_edit.textChanged.connect(self.filtrar_maquinas)
        layout.addWidget(self.pesquisa_edit)
        
        # Filtros (todos na mesma linha)
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(15)
        
        # Filtro Empresa (NOVO)
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(150)
        self.empresa_filter.setMaximumWidth(200)
        self.empresa_filter.addItem("Todas as empresas")
        self.empresa_filter.currentTextChanged.connect(self.filtrar_maquinas)
        filtros_layout.addWidget(self.empresa_filter)
        
        # Filtro Departamento
        filtros_layout.addWidget(QLabel("Departamento:"))
        self.departamento_filter = QComboBox()
        self.departamento_filter.setMinimumWidth(150)
        self.departamento_filter.setMaximumWidth(200)
        self.departamento_filter.addItem("Todos os departamentos")
        self.departamento_filter.currentTextChanged.connect(self.filtrar_maquinas)
        filtros_layout.addWidget(self.departamento_filter)
        
        # Filtro Status
        filtros_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(120)
        self.status_filter.setMaximumWidth(150)
        self.status_filter.addItems(["Todos", "Ativo", "Manutenção", "Inativo"])
        self.status_filter.currentTextChanged.connect(self.filtrar_maquinas)
        filtros_layout.addWidget(self.status_filter)
        
        filtros_layout.addStretch()
        
        layout.addLayout(filtros_layout)
        
        # Tabela de máquinas
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
        
        headers = ["ID", "Nome", "Modelo", "Endereço MAC", "Empresa", "Departamento", "Status", "Observações"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()
        
        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_maquina)
        acoes.addWidget(self.editar_btn)
        
        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_maquina)
        acoes.addWidget(self.deletar_btn)
        
        layout.addLayout(acoes)
    
    def carregar_departamentos(self):
        """Carrega a lista de departamentos do backend"""
        try:
            response = api_client.listar_departamentos()

            # O backend retorna {'departamentos': [...]}
            if isinstance(response, dict):
                self.departamentos = response.get('departamentos', [])
            elif isinstance(response, list):
                self.departamentos = response
            else:
                self.departamentos = []

            # Atualizar o combobox
            self.departamento_filter.clear()
            self.departamento_filter.addItem('Todos os departamentos')

            for dept in self.departamentos:
                if dept and dept.strip():
                    self.departamento_filter.addItem(dept)

            print(f'✅ Departamentos carregados: {self.departamentos}')
        
        except Exception as e:
            print(f"❌ Erro ao carregar departamentos: {e}")
            # Fallback em caso de erro
            self.departamento_filter.clear()
            self.departamento_filter.addItem('Todos os departamentos')
            default_depts = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"]

            for dept in default_depts:
                self.departamento_filter.addItem(dept)
    
    def carregar_empresas(self):
        """Carrega a lista de empresas do backend"""
        try:
            self.empresas = api_client.get_empresas()
            self.empresa_filter.clear()
            self.empresa_filter.addItem("Todas as empresas")
            for emp in self.empresas:
                self.empresa_filter.addItem(emp)
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")
    
    def carregar_maquinas(self):
        try:
            self.maquinas = api_client.listar_maquinas()
            self._dados_cache = self.maquinas.copy()
            self.atualizar_tabela(self.maquinas)
            print(f"✅ Máquinas carregadas: {len(self.maquinas)}")
        except Exception as e:
            print(f"❌ Erro ao carregar máquinas: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar máquinas: {e}")
    
    def filtrar_maquinas(self):
        search_text = self.pesquisa_edit.text().lower()
        empresa = self.empresa_filter.currentText()
        departamento = self.departamento_filter.currentText()
        status = self.status_filter.currentText().lower()
        
        filtered = []
        for maquina in self._dados_cache:
            # Filtro por status
            if status != "todos" and maquina.get("status", "").lower() != status:
                continue
            
            # Filtro por empresa
            if empresa != "Todas as empresas" and maquina.get("empresa") != empresa:
                continue
            
            # Filtro por departamento
            if departamento != "Todos os departamentos" and maquina.get("departamento") != departamento:
                continue
            
            # Filtro por pesquisa (nome, modelo, MAC)
            if search_text:
                if (search_text in maquina.get("nome", "").lower() or
                    search_text in maquina.get("modelo", "").lower() or
                    search_text in maquina.get("mac_address", "").lower()):
                    filtered.append(maquina)
            else:
                filtered.append(maquina)
        
        self.atualizar_tabela(filtered)
    
    def atualizar_tabela(self, maquinas):
        self.tabela.setRowCount(len(maquinas))
        
        status_colors = {
            "ativo": QColor(42, 157, 143),
            "manutencao": QColor(233, 196, 106),
            "inativo": QColor(231, 111, 81)
        }
        
        for row, maquina in enumerate(maquinas):
            self.tabela.setItem(row, 0, QTableWidgetItem(str(maquina.get("id", ""))))
            self.tabela.setItem(row, 1, QTableWidgetItem(maquina.get("nome", "")))
            self.tabela.setItem(row, 2, QTableWidgetItem(maquina.get("modelo", "-")))
            
            # Coluna Endereço MAC
            mac = maquina.get("mac_address", "")
            self.tabela.setItem(row, 3, QTableWidgetItem(mac if mac else "-"))
            
            self.tabela.setItem(row, 4, QTableWidgetItem(maquina.get("empresa", "-")))
            self.tabela.setItem(row, 5, QTableWidgetItem(maquina.get("departamento", "-")))
            
            status_item = QTableWidgetItem(maquina.get("status", "ativo").upper())
            status_color = status_colors.get(maquina.get("status", "ativo"), QColor(0, 0, 0))
            status_item.setForeground(status_color)
            self.tabela.setItem(row, 6, status_item)
            
            self.tabela.setItem(row, 7, QTableWidgetItem(maquina.get("observacoes", "-")[:50]))
    
    def nova_maquina(self):
        dialog = MaquinaDialog(item_data=None, parent=self)
        if dialog.exec():
            self.carregar_maquinas()
            self.carregar_departamentos()
            self.carregar_empresas()
    
    def editar_maquina(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma máquina para editar")
            return
        
        maquina_id = int(self.tabela.item(current_row, 0).text())
        maquina = next((m for m in self.maquinas if m["id"] == maquina_id), None)
        
        if maquina:
            dialog = MaquinaDialog(item_data=maquina, parent=self)
            if dialog.exec():
                self.carregar_maquinas()
                self.carregar_departamentos()
                self.carregar_empresas()
    
    def deletar_maquina(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma máquina para deletar")
            return
        
        maquina_id = int(self.tabela.item(current_row, 0).text())
        maquina_nome = self.tabela.item(current_row, 1).text()
        
        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar a máquina '{maquina_nome}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                success = api_client.deletar_maquina(maquina_id)
                QApplication.restoreOverrideCursor()
                
                if success:
                    notification_manager.success("Máquina deletada com sucesso!", self.window(), 3000)
                    self.carregar_maquinas()
                    self.carregar_departamentos()
                    self.carregar_empresas()
                else:
                    notification_manager.error("Erro ao deletar máquina", self.window(), 3000)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


# CLASSE DO DIALOG COM CAMPO MAC
class MaquinaDialog(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.dados_item = item_data
        self.setWindowTitle("Cadastro de Máquina" if not item_data else "Editar Máquina")
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
        
        if item_data:
            self.carregar_dados_edicao()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Ex: PC Administrativo 01")
        form_layout.addRow("Nome da Máquina:", self.nome_edit)
        
        self.modelo_edit = QLineEdit()
        self.modelo_edit.setPlaceholderText("Ex: Dell Optiplex 3080")
        form_layout.addRow("Modelo:", self.modelo_edit)
        
        # NOVO: Campo Endereço MAC
        self.mac_edit = QLineEdit()
        self.mac_edit.setPlaceholderText("Ex: 00:1A:2B:3C:4D:5E")
        self.mac_edit.setMaxLength(17)
        form_layout.addRow("Endereço MAC:", self.mac_edit)
        
        self.empresa_combo = QComboBox()
        self.carregar_empresas_combo()
        self.empresa_combo.setEditable(True)
        form_layout.addRow("Empresa:", self.empresa_combo)
        
        self.departamento_combo = QComboBox()
        self.carregar_departamentos_combo()
        self.departamento_combo.setEditable(True)
        form_layout.addRow("Departamento:", self.departamento_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["ativo", "manutencao", "inativo"])
        form_layout.addRow("Status:", self.status_combo)
        
        self.observacoes_edit = QTextEdit()
        self.observacoes_edit.setMaximumHeight(80)
        self.observacoes_edit.setPlaceholderText("Observações adicionais...")
        form_layout.addRow("Observações:", self.observacoes_edit)
        
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
        """Carrega empresas do backend para o combo"""
        try:
            empresas = api_client.get_empresas()
            self.empresa_combo.clear()
            for emp in empresas:
                self.empresa_combo.addItem(emp)
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")
            self.empresa_combo.addItems(["Matriz", "Filial 1", "Filial 2", "Filial 3"])
    
    def carregar_departamentos_combo(self):
        """Carrega departamentos do backend para o combo"""
        try:
            departamentos = api_client.get_departamentos()
            self.departamento_combo.clear()
            for dept in departamentos:
                self.departamento_combo.addItem(dept)
        except Exception as e:
            print(f"Erro ao carregar departamentos: {e}")
            self.departamento_combo.addItems(["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"])
    
    def carregar_dados_edicao(self):
        """Carrega os dados do item para edição"""
        if self.dados_item is None:
            return
        
        self.nome_edit.setText(str(self.dados_item.get("nome", "")))
        self.modelo_edit.setText(str(self.dados_item.get("modelo", "")))
        
        # NOVO: Carregar MAC
        mac = str(self.dados_item.get("mac_address", ""))
        self.mac_edit.setText(mac if mac != "None" else "")
        
        empresa = str(self.dados_item.get("empresa", ""))
        idx = self.empresa_combo.findText(empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)
        else:
            self.empresa_combo.setEditText(empresa)
        
        departamento = str(self.dados_item.get("departamento", ""))
        idx = self.departamento_combo.findText(departamento)
        if idx >= 0:
            self.departamento_combo.setCurrentIndex(idx)
        else:
            self.departamento_combo.setEditText(departamento)
        
        status = str(self.dados_item.get("status", "ativo"))
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        
        self.observacoes_edit.setPlainText(str(self.dados_item.get("observacoes", "")))
    
    def salvar(self):
        dados = {
            "nome": self.nome_edit.text().strip(),
            "modelo": self.modelo_edit.text().strip() or None,
            "mac_address": self.mac_edit.text().strip() or None,  # NOVO
            "empresa": self.empresa_combo.currentText(),
            "departamento": self.departamento_combo.currentText(),
            "status": self.status_combo.currentText(),
            "observacoes": self.observacoes_edit.toPlainText().strip() or None
        }
        
        if not dados["nome"]:
            QMessageBox.warning(self, "Atenção", "O nome da máquina é obrigatório!")
            return
        
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            
            if self.dados_item:
                response = api_client.atualizar_maquina(self.dados_item["id"], dados)
                if response and response.get("id"):
                    QMessageBox.information(self, "Sucesso", "Máquina atualizada com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao atualizar máquina")
            else:
                response = api_client.criar_maquina(dados)
                if response and response.get("id"):
                    QMessageBox.information(self, "Sucesso", "Máquina criada com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao criar máquina")
            
            QApplication.restoreOverrideCursor()
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
