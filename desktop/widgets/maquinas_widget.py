from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QTextEdit,
                               QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from api_client import api_client


class MaquinasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.maquinas = []
        self.departamentos = []
        self.init_ui()
        self.carregar_departamentos()
        self.carregar_maquinas()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)
        
        header = QHBoxLayout()
        titulo = QLabel("🖥️ Máquinas")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()
        
        self.novo_btn = QPushButton("+ Nova Máquina")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.nova_maquina)
        header.addWidget(self.novo_btn)
        
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_maquinas)
        header.addWidget(self.atualizar_btn)
        
        layout.addLayout(header)
        
        filtros = QHBoxLayout()
        
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setPlaceholderText("🔍 Pesquisar por nome, modelo...")
        self.pesquisa_edit.textChanged.connect(self.filtrar_maquinas)
        filtros.addWidget(self.pesquisa_edit)
        
        self.departamento_filter = QComboBox()
        self.departamento_filter.addItem("Todos os departamentos")
        self.departamento_filter.currentTextChanged.connect(self.filtrar_maquinas)
        filtros.addWidget(self.departamento_filter)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Ativo", "Manutenção", "Inativo"])
        self.status_filter.currentTextChanged.connect(self.filtrar_maquinas)
        filtros.addWidget(self.status_filter)
        
        layout.addLayout(filtros)
        
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        
        headers = ["ID", "Nome", "Modelo", "Empresa", "Departamento", "Status", "Observações"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
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
        try:
            self.departamentos = api_client.listar_departamentos()
            self.departamento_filter.clear()
            self.departamento_filter.addItem("Todos os departamentos")
            for dept in self.departamentos:
                self.departamento_filter.addItem(dept)
        except Exception as e:
            print(f"Erro ao carregar departamentos: {e}")
    
    def carregar_maquinas(self):
        try:
            self.maquinas = api_client.listar_maquinas()
            self.atualizar_tabela(self.maquinas)
            print(f"✅ Máquinas carregadas: {len(self.maquinas)}")
        except Exception as e:
            print(f"❌ Erro ao carregar máquinas: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar máquinas: {e}")
    
    def filtrar_maquinas(self):
        search_text = self.pesquisa_edit.text().lower()
        departamento = self.departamento_filter.currentText()
        status = self.status_filter.currentText().lower()
        
        filtered = []
        for maquina in self.maquinas:
            if status != "todos" and maquina.get("status", "").lower() != status:
                continue
            if departamento != "Todos os departamentos" and maquina.get("departamento") != departamento:
                continue
            if search_text:
                if (search_text in maquina.get("nome", "").lower() or
                    search_text in maquina.get("modelo", "").lower()):
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
            self.tabela.setItem(row, 3, QTableWidgetItem(maquina.get("empresa", "-")))
            self.tabela.setItem(row, 4, QTableWidgetItem(maquina.get("departamento", "-")))
            
            status_item = QTableWidgetItem(maquina.get("status", "ativo").upper())
            status_color = status_colors.get(maquina.get("status", "ativo"), QColor(0, 0, 0))
            status_item.setForeground(status_color)
            self.tabela.setItem(row, 5, status_item)
            
            self.tabela.setItem(row, 6, QTableWidgetItem(maquina.get("observacoes", "-")[:50]))
    
    def nova_maquina(self):
        dialog = MaquinaDialog(item_data=None, parent=self)
        if dialog.exec():
            self.carregar_maquinas()
            self.carregar_departamentos()
    
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
                if api_client.deletar_maquina(maquina_id):
                    QMessageBox.information(self, "Sucesso", "Máquina deletada com sucesso!")
                    self.carregar_maquinas()
                    self.carregar_departamentos()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao deletar máquina")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


# CLASSE DO DIALOG - SEPARADA E CORRETA
class MaquinaDialog(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.dados_item = item_data  # Nome diferente para evitar conflito
        self.setWindowTitle("Cadastro de Máquina" if not item_data else "Editar Máquina")
        self.setModal(True)
        self.setMinimumWidth(500)
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
        
        self.empresa_combo = QComboBox()
        self.empresa_combo.addItems(["Matriz", "Filial 1", "Filial 2", "Filial 3"])
        self.empresa_combo.setEditable(True)
        form_layout.addRow("Empresa:", self.empresa_combo)
        
        self.departamento_combo = QComboBox()
        self.departamento_combo.addItems(["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"])
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
    
    def carregar_dados_edicao(self):
        """Carrega os dados do item para edição"""
        if self.dados_item is None:
            return
        
        self.nome_edit.setText(str(self.dados_item.get("nome", "")))
        self.modelo_edit.setText(str(self.dados_item.get("modelo", "")))
        
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
            "empresa": self.empresa_combo.currentText(),
            "departamento": self.departamento_combo.currentText(),
            "status": self.status_combo.currentText(),
            "observacoes": self.observacoes_edit.toPlainText().strip() or None
        }
        
        if not dados["nome"]:
            QMessageBox.warning(self, "Atenção", "O nome da máquina é obrigatório!")
            return
        
        try:
            if self.dados_item:
                response = api_client.atualizar_maquina(self.dados_item["id"], dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Máquina atualizada com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao atualizar máquina")
            else:
                response = api_client.criar_maquina(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Máquina criada com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao criar máquina")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
            