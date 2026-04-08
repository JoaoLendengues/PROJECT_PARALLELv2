from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QSpinBox,
                               QTextEdit, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from api_client import api_client


class MateriaisWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.materiais = []
        self.categorias = []
        self.init_ui()
        self.carregar_categorias()
        self.carregar_materiais()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)
        
        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("📦 Materiais")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()
        
        # Botão Novo Material
        self.novo_btn = QPushButton("+ Novo Material")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.novo_material)
        header.addWidget(self.novo_btn)
        
        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_materiais)
        header.addWidget(self.atualizar_btn)
        
        layout.addLayout(header)
        
        # Barra de pesquisa e filtros
        filtros = QHBoxLayout()
        
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setPlaceholderText("🔍 Pesquisar por nome, descrição...")
        self.pesquisa_edit.textChanged.connect(self.filtrar_materiais)
        filtros.addWidget(self.pesquisa_edit)
        
        self.categoria_filter = QComboBox()
        self.categoria_filter.addItem("Todas as categorias")
        self.categoria_filter.currentTextChanged.connect(self.filtrar_materiais)
        filtros.addWidget(self.categoria_filter)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Ativo", "Inativo", "Descontinuado"])
        self.status_filter.currentTextChanged.connect(self.filtrar_materiais)
        filtros.addWidget(self.status_filter)
        
        layout.addLayout(filtros)
        
        # Tabela de materiais com estilo melhorado
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
        
        headers = ["ID", "Nome", "Descrição", "Qtd", "Categoria", "Empresa", "Status"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()
        
        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_material)
        acoes.addWidget(self.editar_btn)
        
        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_material)
        acoes.addWidget(self.deletar_btn)
        
        layout.addLayout(acoes)
    
    def carregar_categorias(self):
        try:
            self.categorias = api_client.listar_categorias()
            self.categoria_filter.clear()
            self.categoria_filter.addItem("Todas as categorias")
            for cat in self.categorias:
                self.categoria_filter.addItem(cat)
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")
    
    def carregar_materiais(self):
        try:
            self.materiais = api_client.listar_materiais()
            self.atualizar_tabela(self.materiais)
            print(f"✅ Materiais carregados: {len(self.materiais)}")
        except Exception as e:
            print(f"❌ Erro ao carregar materiais: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar materiais: {e}")
    
    def filtrar_materiais(self):
        search_text = self.pesquisa_edit.text().lower()
        categoria = self.categoria_filter.currentText()
        status = self.status_filter.currentText().lower()
        
        filtered = []
        for material in self.materiais:
            if status != "todos" and material.get("status", "").lower() != status:
                continue
            if categoria != "Todas as categorias" and material.get("categoria") != categoria:
                continue
            if search_text:
                if (search_text in material["nome"].lower() or
                    search_text in material.get("descricao", "").lower()):
                    filtered.append(material)
            else:
                filtered.append(material)
        
        self.atualizar_tabela(filtered)
    
    def atualizar_tabela(self, materiais):
        self.tabela.setRowCount(len(materiais))
        
        status_colors = {
            "ativo": QColor(42, 157, 143),
            "inativo": QColor(231, 111, 81),
            "descontinuado": QColor(158, 158, 158)
        }
        
        for row, material in enumerate(materiais):
            self.tabela.setItem(row, 0, QTableWidgetItem(str(material.get("id", ""))))
            self.tabela.setItem(row, 1, QTableWidgetItem(material.get("nome", "")))
            self.tabela.setItem(row, 2, QTableWidgetItem(material.get("descricao", "")[:60]))
            self.tabela.setItem(row, 3, QTableWidgetItem(str(material.get("quantidade", 0))))
            self.tabela.setItem(row, 4, QTableWidgetItem(material.get("categoria", "-")))
            self.tabela.setItem(row, 5, QTableWidgetItem(material.get("empresa", "-")))
            
            status_item = QTableWidgetItem(material.get("status", "ativo").upper())
            status_color = status_colors.get(material.get("status", "ativo"), QColor(0, 0, 0))
            status_item.setForeground(status_color)
            self.tabela.setItem(row, 6, status_item)
    
    def novo_material(self):
        dialog = MaterialDialog(item_data=None, parent=self)
        if dialog.exec():
            self.carregar_materiais()
            self.carregar_categorias()
    
    def editar_material(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um material para editar")
            return
        
        material_id = int(self.tabela.item(current_row, 0).text())
        material = next((m for m in self.materiais if m["id"] == material_id), None)
        
        if material:
            dialog = MaterialDialog(item_data=material, parent=self)
            if dialog.exec():
                self.carregar_materiais()
                self.carregar_categorias()
    
    def deletar_material(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um material para deletar")
            return
        
        material_id = int(self.tabela.item(current_row, 0).text())
        material_nome = self.tabela.item(current_row, 1).text()
        
        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar o material '{material_nome}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if api_client.deletar_material(material_id):
                    QMessageBox.information(self, "Sucesso", "Material deletado com sucesso!")
                    self.carregar_materiais()
                    self.carregar_categorias()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao deletar material")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


# CLASSE DO DIALOG - SEPARADA E CORRETA COM ESTILO MELHORADO
class MaterialDialog(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.dados_item = item_data
        self.setWindowTitle("Cadastro de Material" if not item_data else "Editar Material")
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
        
        if item_data:
            self.carregar_dados_edicao()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Ex: Mouse Logitech M90")
        form_layout.addRow("Nome do Material:", self.nome_edit)
        
        self.descricao_edit = QTextEdit()
        self.descricao_edit.setMaximumHeight(100)
        self.descricao_edit.setPlaceholderText("Descrição detalhada do material...")
        form_layout.addRow("Descrição:", self.descricao_edit)
        
        self.quantidade_spin = QSpinBox()
        self.quantidade_spin.setRange(0, 999999)
        form_layout.addRow("Quantidade:", self.quantidade_spin)
        
        self.categoria_combo = QComboBox()
        self.categoria_combo.setEditable(True)
        self.carregar_categorias()
        form_layout.addRow("Categoria:", self.categoria_combo)
        
        self.empresa_combo = QComboBox()
        self.empresa_combo.addItems(["Matriz", "Filial 1", "Filial 2", "Filial 3"])
        self.empresa_combo.setEditable(True)
        form_layout.addRow("Empresa:", self.empresa_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["ativo", "inativo", "descontinuado"])
        form_layout.addRow("Status:", self.status_combo)
        
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
    
    def carregar_categorias(self):
        try:
            categorias = api_client.listar_categorias()
            self.categoria_combo.clear()
            for cat in categorias:
                self.categoria_combo.addItem(cat)
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")
    
    def carregar_dados_edicao(self):
        """Carrega os dados do item para edição"""
        if self.dados_item is None:
            return
        
        self.nome_edit.setText(str(self.dados_item.get("nome", "")))
        self.descricao_edit.setPlainText(str(self.dados_item.get("descricao", "")))
        self.quantidade_spin.setValue(int(self.dados_item.get("quantidade", 0)))
        
        categoria = str(self.dados_item.get("categoria", ""))
        idx = self.categoria_combo.findText(categoria)
        if idx >= 0:
            self.categoria_combo.setCurrentIndex(idx)
        else:
            self.categoria_combo.setEditText(categoria)
        
        empresa = str(self.dados_item.get("empresa", ""))
        idx = self.empresa_combo.findText(empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)
        else:
            self.empresa_combo.setEditText(empresa)
        
        status = str(self.dados_item.get("status", "ativo"))
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
    
    def salvar(self):
        dados = {
            "nome": self.nome_edit.text().strip(),
            "descricao": self.descricao_edit.toPlainText().strip(),
            "quantidade": self.quantidade_spin.value(),
            "categoria": self.categoria_combo.currentText(),
            "empresa": self.empresa_combo.currentText(),
            "status": self.status_combo.currentText()
        }
    
        if not dados["nome"]:
            QMessageBox.warning(self, "Atenção", "O nome do material é obrigatório!")
            return
    
        try:
            if self.dados_item:
                # Atualizar
                response = api_client.atualizar_material(self.dados_item["id"], dados)
                if response and response.get("id"):
                    QMessageBox.information(self, "Sucesso", "Material atualizado com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao atualizar material")
            else:
                # Criar
                response = api_client.criar_material(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Material criado com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao criar material")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
            