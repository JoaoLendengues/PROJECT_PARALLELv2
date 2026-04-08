from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QCheckBox,
                               QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from api_client import api_client


class ColaboradoresWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.colaboradores = []
        self.init_ui()
        self.carregar_colaboradores()
    
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
        self.pesquisa_edit.setPlaceholderText("🔍 Pesquisar por nome...")
        self.pesquisa_edit.textChanged.connect(self.filtrar_colaboradores)
        layout.addWidget(self.pesquisa_edit)
        
        # Tabela com estilo melhorado
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        
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
        
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
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
    
    def carregar_colaboradores(self):
        try:
            self.colaboradores = api_client.listar_colaboradores()
            self.atualizar_tabela(self.colaboradores)
            print(f"✅ Colaboradores carregados: {len(self.colaboradores)}")
        except Exception as e:
            print(f"❌ Erro ao carregar colaboradores: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar colaboradores: {e}")
    
    def filtrar_colaboradores(self):
        search = self.pesquisa_edit.text().lower()
        if not search:
            self.atualizar_tabela(self.colaboradores)
            return
        
        filtered = [c for c in self.colaboradores if search in c.get("nome", "").lower()]
        self.atualizar_tabela(filtered)
    
    def atualizar_tabela(self, colaboradores):
        self.tabela.setRowCount(len(colaboradores))
        
        for row, colab in enumerate(colaboradores):
            self.tabela.setItem(row, 0, QTableWidgetItem(str(colab.get("id", ""))))
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
    
    def novo_colaborador(self):
        dialog = ColaboradorDialog(item_data=None, parent=self)
        if dialog.exec():
            self.carregar_colaboradores()
    
    def editar_colaborador(self):
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
        
        # Nome
        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Nome completo")
        form_layout.addRow("Nome:", self.nome_edit)
        
        # Cargo
        self.cargo_edit = QLineEdit()
        self.cargo_edit.setPlaceholderText("Cargo do colaborador")
        form_layout.addRow("Cargo:", self.cargo_edit)
        
        # Departamento
        self.departamento_combo = QComboBox()
        self.departamento_combo.addItems(["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"])
        self.departamento_combo.setEditable(True)
        form_layout.addRow("Departamento:", self.departamento_combo)
        
        # Empresa
        self.empresa_combo = QComboBox()
        self.empresa_combo.addItems(["Matriz", "Filial 1", "Filial 2", "Filial 3"])
        self.empresa_combo.setEditable(True)
        form_layout.addRow("Empresa:", self.empresa_combo)
        
        # Status
        self.status_check = QCheckBox("Ativo")
        self.status_check.setChecked(True)
        form_layout.addRow("Status:", self.status_check)
        
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
        """Carrega os dados do colaborador para edição"""
        if self.dados_item is None:
            return
        
        self.nome_edit.setText(str(self.dados_item.get("nome", "")))
        self.cargo_edit.setText(str(self.dados_item.get("cargo", "")))
        
        dept = str(self.dados_item.get("departamento", ""))
        idx = self.departamento_combo.findText(dept)
        if idx >= 0:
            self.departamento_combo.setCurrentIndex(idx)
        else:
            self.departamento_combo.setEditText(dept)
        
        empresa = str(self.dados_item.get("empresa", ""))
        idx = self.empresa_combo.findText(empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)
        else:
            self.empresa_combo.setEditText(empresa)
        
        self.status_check.setChecked(self.dados_item.get("ativo", True))
    
    def salvar(self):
        dados = {
            "nome": self.nome_edit.text().strip(),
            "cargo": self.cargo_edit.text().strip() or None,
            "departamento": self.departamento_combo.currentText(),
            "empresa": self.empresa_combo.currentText(),
            "ativo": self.status_check.isChecked()
        }
        
        if not dados["nome"]:
            QMessageBox.warning(self, "Atenção", "O nome é obrigatório!")
            return
        
        try:
            if self.dados_item:
                response = api_client.atualizar_colaborador(self.dados_item["id"], dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Colaborador atualizado com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao atualizar colaborador")
            else:
                response = api_client.criar_colaborador(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Colaborador criado com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao criar colaborador")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
            