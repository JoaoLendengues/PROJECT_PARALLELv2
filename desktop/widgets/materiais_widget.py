from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QSpinBox,
                               QTextEdit, QMessageBox, QHeaderView, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QCursor
from api_client import api_client
from widgets.toast_notification import notification_manager
from widgets.filter_utils import contains_text, is_all_option, same_filter_value, same_text


class MateriaisWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.materiais = []
        self.dados_cache = []
        self.categorias = []
        self.empresas = []
        self._loaded = False  # ✅ Flag para controle de carregamento
        self.init_ui()
        # ⚠️ NÃO carregar dados aqui - será feito no on_show()

    def on_show(self):
        """✅ Chamado quando a aba é selecionada - carrega dados sob demanda"""
        if not self._loaded:
            self.carregar_categorias()
            self.carregar_empresas()
            self.carregar_materiais()
            self._loaded = True

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

        # Barra de pesquisa
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setPlaceholderText("🔍 Pesquisar por nome, descrição...")
        self.pesquisa_edit.setMaximumWidth(350)
        self.pesquisa_edit.textChanged.connect(self.filtrar_materiais)
        layout.addWidget(self.pesquisa_edit)

        # Filtros (todos na mesma linha)
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(15)

        # Filtro Empresa
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(150)
        self.empresa_filter.setMaximumWidth(200)
        self.empresa_filter.addItem("Todas as empresas")
        self.empresa_filter.currentTextChanged.connect(self.filtrar_materiais)
        filtros_layout.addWidget(self.empresa_filter)

        # Filtro Categoria
        filtros_layout.addWidget(QLabel("Categoria:"))
        self.categoria_filter = QComboBox()
        self.categoria_filter.setMinimumWidth(150)
        self.categoria_filter.setMaximumWidth(200)
        self.categoria_filter.addItem("Todas as categorias")
        self.categoria_filter.currentTextChanged.connect(self.filtrar_materiais)
        filtros_layout.addWidget(self.categoria_filter)

        # Filtro Status
        filtros_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(120)
        self.status_filter.setMaximumWidth(150)
        self.status_filter.addItems(["Todos", "Ativo", "Inativo", "Descontinuado"])
        self.status_filter.currentTextChanged.connect(self.filtrar_materiais)
        filtros_layout.addWidget(self.status_filter)

        filtros_layout.addStretch()

        layout.addLayout(filtros_layout)

        # Tabela de materiais
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSortingEnabled(True)

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

    def carregar_empresas(self):
        """Carrega a lista de empresas do backend"""
        try:
            self.empresas = api_client.get_empresas()
            self.empresa_filter.clear()
            self.empresa_filter.addItem('Todas as empresas')
            for emp in self.empresas:
                self.empresa_filter.addItem(emp)
        except Exception as e:
            print(f'Erro ao carregar empresas: {e}')

    def carregar_materiais(self):
        """Carrega a lista de materiais do backend"""
        try:
            self.materiais = api_client.listar_materiais()
            self.dados_cache = self.materiais.copy() # Cache para filtros
            self.atualizar_tabela(self.materiais)
            print(f"✅ Materiais carregados: {len(self.materiais)}")
        except Exception as e:
            print(f"❌ Erro ao carregar materiais: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar materiais: {e}")

    def filtrar_materiais(self):
        search_text = self.pesquisa_edit.text()
        empresa = self.empresa_filter.currentText()
        categoria = self.categoria_filter.currentText()
        status = self.status_filter.currentText()

        filtered = []
        for material in self.dados_cache:
            # Filtro por status
            if not is_all_option(status) and not same_filter_value(material.get("status", ""), status):
                continue

            # Filtro por empresa
            if not is_all_option(empresa) and not same_text(material.get('empresa'), empresa):
                continue

            # Filtro por categoria
            if not is_all_option(categoria) and not same_text(material.get("categoria"), categoria):
                continue

            # Filtro de pesquisa
            if contains_text(search_text, material.get("nome", ""), material.get("descricao", "")):
                filtered.append(material)

        self.atualizar_tabela(filtered)

    def atualizar_tabela(self, materiais):
        """Atualiza a tabela com a lista de materiais"""
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
            self.carregar_empresas()

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
                self.carregar_empresas()

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
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                success = api_client.deletar_material(material_id)
                QApplication.restoreOverrideCursor()

                if success:
                    notification_manager.success('Material deletado com sucesso!', self.window(), 3000)

                    self.carregar_materiais()
                    self.carregar_categorias()
                    self.carregar_empresas()
                else:
                    notification_manager.error('Erro ao deletar material', self.window(), 3000)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, 'Erro', f'Erro ao deletar: {e}')


# CLASSE DO DIALOG (mantida igual, sem alterações)
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
        self.categoria_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                color: #1e293b;
                min-height: 34px;
                outline: none;
            }
            QComboBox:focus {
                outline: none;
                border: 1px solid #cbd5e1;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e6f0ff;
                border: none;
            }
        """)
        self.categoria_combo.setEditable(False)
        self.categoria_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_categorias()
        form_layout.addRow("Categoria:", self.categoria_combo)

        self.empresa_combo = QComboBox()
        self.empresa_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                color: #1e293b;
                min-height: 34px;
                outline: none;
            }
            QComboBox:focus {
                outline: none;
                border: 1px solid #cbd5e1;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e6f0ff;
                border: none;
            }
        """)
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_empresas()
        form_layout.addRow("Empresa:", self.empresa_combo)

        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                color: #1e293b;
                min-height: 34px;
                outline: none;
            }
            QComboBox:focus {
                outline: none;
                border: 1px solid #cbd5e1;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e6f0ff;
                border: none;
            }
        """)
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

    def carregar_empresas(self):
        try:
            empresas = api_client.get_empresas()
            self.empresa_combo.clear()
            for emp in empresas:
                self.empresa_combo.addItem(emp)
        except Exception as e:
            print(f'Erro ao carregar empresas: {e}')

    def carregar_dados_edicao(self):
        if self.dados_item is None:
            return

        self.nome_edit.setText(str(self.dados_item.get("nome", "")))
        self.descricao_edit.setPlainText(str(self.dados_item.get("descricao", "")))
        self.quantidade_spin.setValue(int(self.dados_item.get("quantidade", 0)))

        categoria = str(self.dados_item.get("categoria", ""))
        idx = self.categoria_combo.findText(categoria)
        if idx >= 0:
            self.categoria_combo.setCurrentIndex(idx)

        empresa = str(self.dados_item.get("empresa", ""))
        idx = self.empresa_combo.findText(empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)

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
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

            if self.dados_item:
                response = api_client.atualizar_material(self.dados_item['id'], dados)
                if response:
                    QMessageBox.information(self, 'Sucesso', 'Material atualizado com sucesso')
                    self.accept()
                else:
                    QMessageBox.warning(self, 'Erro', 'Erro ao atualizar material')
            else:
                response = api_client.criar_material(dados)
                if response:
                    QMessageBox.information(self, 'Sucesso', 'Material criado com sucesso')
                    self.accept()
                else:
                    QMessageBox.warning(self, 'Erro', 'Erro ao criar material')

            QApplication.restoreOverrideCursor()

        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, 'Erro', f'Erro ao salvar: {e}')
