from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QSpinBox,
                               QTextEdit, QMessageBox, QHeaderView, QDateEdit, QApplication)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor, QCursor
from api_client import api_client
from widgets.toast_notification import notification_manager


class PedidosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.pedidos = []
        self.pedidos_cache = []
        self.materiais = []
        self.departamentos = []
        self._loaded = False
        self.init_ui()
    
    def on_show(self):
        if not self._loaded:
            self.carregar_materiais()
            self.carregar_departamentos()
            self.carregar_empresas()
            self.carregar_pedidos()
            self._loaded = True
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)
        
        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("📋 Pedidos")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()
        
        # Botão Novo Pedido
        self.novo_btn = QPushButton("+ Novo Pedido")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.novo_pedido)
        header.addWidget(self.novo_btn)
        
        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_pedidos)
        header.addWidget(self.atualizar_btn)
        
        layout.addLayout(header)
        
        # Barra de pesquisa e filtros
        filtros = QHBoxLayout()
        
        # Filtro Status
        filtros.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Pendente", "Aprovado", "Concluído", "Cancelado"])
        self.status_filter.currentTextChanged.connect(self.filtrar_pedidos)
        filtros.addWidget(self.status_filter)
        
        filtros.setSpacing(20)
        
        # Filtro empresa
        filtros.addWidget(QLabel("Empresa:"))
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(150)
        self.empresa_filter.addItem("Todas as empresas")
        self.empresa_filter.currentTextChanged.connect(self.filtrar_pedidos)
        filtros.addWidget(self.empresa_filter)
        
        filtros.addSpacing(20)

        # Filtro Departamento
        filtros.addWidget(QLabel('Departamento:'))
        self.departamento_filter = QComboBox()
        self.departamento_filter.setMinimumWidth(150)
        self.departamento_filter.addItem('Todos os departamentos')
        self.departamento_filter.currentTextChanged.connect(self.filtrar_pedidos)
        filtros.addWidget(self.departamento_filter)
        
        filtros.addStretch()
        
        layout.addLayout(filtros)
        
        # Tabela de pedidos com estilo melhorado
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
        
        headers = ["ID", "Material", "Qtd", "Solicitante", "Empresa", "Dept", "Data Solic.", "Data Conclusão", "Status", "Observação"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(9, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()
        
        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_pedido)
        acoes.addWidget(self.editar_btn)
        
        self.aprovar_btn = QPushButton("✓ Aprovar")
        self.aprovar_btn.clicked.connect(self.aprovar_pedido)
        acoes.addWidget(self.aprovar_btn)
        
        self.concluir_btn = QPushButton("✅ Concluir")
        self.concluir_btn.clicked.connect(self.concluir_pedido)
        acoes.addWidget(self.concluir_btn)
        
        self.cancelar_btn = QPushButton("✗ Cancelar")
        self.cancelar_btn.clicked.connect(self.cancelar_pedido)
        acoes.addWidget(self.cancelar_btn)
        
        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_pedido)
        acoes.addWidget(self.deletar_btn)
        
        layout.addLayout(acoes)
    
    def carregar_materiais(self):
        """Carrega a lista de materiais"""
        try:
            self.materiais = api_client.listar_materiais_para_pedido()
        except Exception as e:
            print(f"Erro ao carregar materiais: {e}")

    def carregar_departamentos(self):
        """Carrega a lista de departamentos do backend para filtro"""
        try:
            self.departamentos = api_client.get_departamentos_lista()
            self.departamento_filter.clear()
            self.departamento_filter.addItem('Todos os departamentos')
            for dept in self.departamentos:
                if dept and dept.strip():
                    self.departamento_filter.addItem(dept)
            print(f'✅ Departamentos carregados para filtro: {len(self.departamentos)}')
        except Exception as e:
            print(f'❌ Erro ao carregar empresas: {e}')

    def carregar_empresas(self):
        """Carrega a lista de empresas do backend para filtro"""
        try:
            self.empresas = api_client.get_empresas()
            self.empresa_filter.clear()
            self.empresa_filter.addItem('Todas as empresas')
            for emp in self.empresas:
                if emp and emp.strip():
                    self.empresa_filter.addItem(emp)
            print(f'✅ Empresas carregadas para filtro: {len(self.empresas)}')
        except Exception as e:
            print(f'❌ Erro ao carregar empresas> {e}')          

    def carregar_pedidos(self):
        """Carrega a lista de pedidos do backend"""
        try:
            self.pedidos = api_client.listar_pedidos()
            self.pedidos_cache = self.pedidos.copy()
            self.atualizar_tabela(self.pedidos)
            print(f"✅ Pedidos carregados: {len(self.pedidos)}")
        except Exception as e:
            print(f"❌ Erro ao carregar pedidos: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar pedidos: {e}")
    
    def filtrar_pedidos(self):
        """Filtra os pedidos com base nos filtros"""
        status = self.status_filter.currentText().lower()
        empresa = self.empresa_filter.currentText()
        departamento = self.departamento_filter.currentText()
        
        filtered = []
        for pedido in self.pedidos:
            # Filtro por status
            if status != "todos" and pedido.get("status", "").lower() != status:
                continue
            
            # Filtro por empresa
            if empresa != "Todas as empresas" and pedido.get("empresa") != empresa:
                continue

            # Filtro por departamento
            if departamento != 'Todos os departamentos' and pedido.get('departamento') != departamento:
                continue
            
            filtered.append(pedido)
        
        self.atualizar_tabela(filtered)
    
    def atualizar_tabela(self, pedidos):
        """Atualiza a tabela com a lista de pedidos"""
        self.tabela.setRowCount(len(pedidos))
        
        status_colors = {
            "pendente": QColor(244, 162, 97),
            "aprovado": QColor(42, 157, 143),
            "concluido": QColor(44, 125, 160),
            "cancelado": QColor(231, 111, 81)
        }
        
        for row, pedido in enumerate(pedidos):
            self.tabela.setItem(row, 0, QTableWidgetItem(str(pedido.get("id", ""))))
            self.tabela.setItem(row, 1, QTableWidgetItem(pedido.get("material_nome", "-")))
            self.tabela.setItem(row, 2, QTableWidgetItem(str(pedido.get("quantidade", 0))))
            self.tabela.setItem(row, 3, QTableWidgetItem(pedido.get("solicitante", "-")))
            self.tabela.setItem(row, 4, QTableWidgetItem(pedido.get("empresa", "-")))
            self.tabela.setItem(row, 5, QTableWidgetItem(pedido.get("departamento", "-")))
            self.tabela.setItem(row, 6, QTableWidgetItem(pedido.get("data_solicitacao", "-")))
            self.tabela.setItem(row, 7, QTableWidgetItem(pedido.get("data_conclusao", "-") or "-"))
            
            status_item = QTableWidgetItem(pedido.get("status", "pendente").upper())
            status_color = status_colors.get(pedido.get("status", "pendente"), QColor(0, 0, 0))
            status_item.setForeground(status_color)
            self.tabela.setItem(row, 8, status_item)
            
            self.tabela.setItem(row, 9, QTableWidgetItem(pedido.get("observacao", "-")[:50]))
    
    def novo_pedido(self):
        dialog = PedidoDialog(materiais=self.materiais, parent=self)
        if dialog.exec():
            self.carregar_pedidos()
            self.carregar_materiais()
    
    def editar_pedido(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para editar")
            return
        
        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido = next((p for p in self.pedidos if p["id"] == pedido_id), None)
        
        if pedido:
            dialog = PedidoDialog(pedido_data=pedido, materiais=self.materiais, parent=self)
            if dialog.exec():
                self.carregar_pedidos()
                self.carregar_materiais()
    
    def aprovar_pedido(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para aprovar")
            return
        
        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido = next((p for p in self.pedidos if p["id"] == pedido_id), None)
        
        if not pedido:
            return
        
        if pedido.get("status") != "pendente":
            QMessageBox.warning(self, "Atenção", "Apenas pedidos pendentes podem ser aprovados!")
            return
        
        confirm = QMessageBox.question(
            self,
            "Confirmar aprovação",
            f"Deseja aprovar o pedido de {pedido.get('quantidade')} unidade(s) de '{pedido.get('material_nome')}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if api_client.aprovar_pedido(pedido_id):
                    QMessageBox.information(self, "Sucesso", "Pedido aprovado com sucesso!")
                    self.carregar_pedidos()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao aprovar pedido")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao aprovar: {e}")
    
    def concluir_pedido(self):
        """Conclui o pedido selecionado"""
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para concluir")
            return
        
        # Buscar os dados diretamente da tabela
        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido_material = self.tabela.item(current_row, 1).text()
        pedido_qtd = self.tabela.item(current_row, 2).text()
        pedido_status = self.tabela.item(current_row, 8).text().lower()
        
        # Verificar se o pedido está aprovado
        if pedido_status != 'aprovado':
            QMessageBox.warning(
                self, 
                "Atenção", 
                f"Este pedido está com status '{pedido_status.upper()}'. Apenas pedidos APROVADOS podem ser concluídos."
            )
            return
        
        confirm = QMessageBox.question(
            self,
            "Confirmar conclusão",
            f"Deseja concluir o pedido de {pedido_qtd} unidade(s) de '{pedido_material}'?\n\n"
            f"⚠️ Esta ação irá atualizar o estoque e não poderá ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                # Mostrar cursor de espera
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                
                success = api_client.concluir_pedido(pedido_id)
                
                QApplication.restoreOverrideCursor()
                
                if success:
                    notification_manager.success("Pedido concluído com sucesso! Estoque atualizado.", self.window(), 3000)
                    self.carregar_pedidos()  # Recarregar a lista
                else:
                    notification_manager.error("Erro ao concluir pedido. Verifique o estoque.", self.window(), 3000)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Erro", f"Erro ao concluir pedido: {e}")

    def cancelar_pedido(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para cancelar")
            return
        
        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido = next((p for p in self.pedidos if p["id"] == pedido_id), None)
        
        if not pedido:
            return
        
        if pedido.get("status") not in ["pendente", "aprovado"]:
            QMessageBox.warning(self, "Atenção", "Apenas pedidos pendentes ou aprovados podem ser cancelados!")
            return
        
        confirm = QMessageBox.question(
            self,
            "Confirmar cancelamento",
            f"Deseja cancelar o pedido de {pedido.get('quantidade')} unidade(s) de '{pedido.get('material_nome')}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if api_client.cancelar_pedido(pedido_id):
                    QMessageBox.information(self, "Sucesso", "Pedido cancelado com sucesso!")
                    self.carregar_pedidos()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao cancelar pedido")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cancelar: {e}")
    
    def deletar_pedido(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido para deletar")
            return
        
        pedido_id = int(self.tabela.item(current_row, 0).text())
        pedido_desc = self.tabela.item(current_row, 1).text()
        
        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar o pedido de '{pedido_desc}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if api_client.deletar_pedido(pedido_id):
                    QMessageBox.information(self, "Sucesso", "Pedido deletado com sucesso!")
                    self.carregar_pedidos()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao deletar pedido")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


class PedidoDialog(QDialog):
    def __init__(self, pedido_data=None, materiais=None, parent=None):
        super().__init__(parent)
        self.dados_item = pedido_data
        self.materiais = materiais or []
        self.setWindowTitle("Novo Pedido" if not pedido_data else "Editar Pedido")
        self.setModal(True)
        self.setMinimumWidth(550)
        
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
        
        if pedido_data:
            self.carregar_dados_edicao()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Material - AGORA COM CAMPO DE TEXTO LIVRE E BOTÃO PARA CADASTRAR
        material_layout = QHBoxLayout()
        
        self.material_edit = QLineEdit()
        self.material_edit.setPlaceholderText("Digite o nome do material ou selecione um existente")
        self.material_edit.setMinimumWidth(300)
        material_layout.addWidget(self.material_edit)
        
        self.material_combo = QComboBox()
        self.material_combo.setEditable(False)
        self.material_combo.setInsertPolicy(QComboBox.NoInsert)
        self.material_combo.addItem("-- Selecione um material existente --")
        for mat in self.materiais:
            self.material_combo.addItem(
                f"{mat.get('nome', '')} - Estoque: {mat.get('quantidade', 0)}", 
                mat.get("id")
            )
        self.material_combo.currentIndexChanged.connect(self.on_material_selecionado)
        material_layout.addWidget(self.material_combo)
        
        self.novo_material_btn = QPushButton("+ Novo Material")
        self.novo_material_btn.clicked.connect(self.cadastrar_novo_material)
        material_layout.addWidget(self.novo_material_btn)
        
        form_layout.addRow("Material:", material_layout)
        
        # ID do material (oculto, para quando for material existente)
        self.material_id_edit = QLineEdit()
        self.material_id_edit.setVisible(False)
        form_layout.addRow("", self.material_id_edit)
        
        # Quantidade
        self.quantidade_spin = QSpinBox()
        self.quantidade_spin.setRange(1, 99999)
        self.quantidade_spin.setValue(1)
        form_layout.addRow("Quantidade:", self.quantidade_spin)
        
        # Solicitante
        self.solicitante_edit = QLineEdit()
        self.solicitante_edit.setPlaceholderText("Nome do solicitante")
        form_layout.addRow("Solicitante:", self.solicitante_edit)
        
        # Empresa
        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_empresas_combo()
        form_layout.addRow("Empresa:", self.empresa_combo)
        
        # Departamento
        self.departamento_combo = QComboBox()
        self.departamento_combo.setEditable(False)
        self.departamento_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_departamentos_combo()
        form_layout.addRow("Departamento:", self.departamento_combo)
        
        # Status (só aparece na edição)
        self.status_label = QLabel("Status:")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pendente", "aprovado", "concluido", "cancelado"])
        self.status_label.setVisible(False)
        self.status_combo.setVisible(False)
        form_layout.addRow(self.status_label, self.status_combo)
        
        # Observação
        self.observacao_edit = QTextEdit()
        self.observacao_edit.setMaximumHeight(80)
        self.observacao_edit.setPlaceholderText("Observações adicionais...")
        form_layout.addRow("Observação:", self.observacao_edit)
        
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
            default_empresas = ["Matriz", "Filial 1", "Filial 2", "Filial 3"]
            for emp in default_empresas:
                self.empresa_combo.addItem(emp)

    def carregar_departamentos_combo(self):
        """Carrega os departamentos do backend para o combobox"""
        try:
            departamentos = api_client.get_departamentos_lista()
            self.departamento_combo.clear()
            # ✅ Adiciona apenas os departamentos do backend
            for dept in departamentos:
                if dept and dept.strip():
                    self.departamento_combo.addItem(dept)
            
            # ✅ Se ainda estiver vazio, usa fallback
            if self.departamento_combo.count() == 0:
                default_depts = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"]
                for dept in default_depts:
                    self.departamento_combo.addItem(dept)
                    
        except Exception as e:
            print(f"❌ Erro ao carregar departamentos: {e}")
            # Fallback em caso de erro
            default_depts = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"]
            for dept in default_depts:
                self.departamento_combo.addItem(dept)
    
    def on_material_selecionado(self, index):
        """Quando um material existente é selecionado no combo"""
        if index > 0:  # Primeiro item é o placeholder
            material = self.materiais[index - 1]
            self.material_edit.setText(material.get("nome", ""))
            self.material_id_edit.setText(str(material.get("id", "")))
        else:
            self.material_edit.setText("")
            self.material_id_edit.setText("")
    
    def cadastrar_novo_material(self):
        """Abre diálogo para cadastrar um novo material rapidamente"""
        from widgets.materiais_widget import MaterialDialog
        
        dialog = MaterialDialog(parent=self)
        if dialog.exec():
            # Recarregar a lista de materiais
            self.carregar_materiais_novos()
            # Selecionar o material recém-criado
            novo_material_nome = dialog.nome_edit.text() if hasattr(dialog, 'nome_edit') else ""
            self.material_edit.setText(novo_material_nome)
            self.material_id_edit.setText("")  # Será buscado pelo nome ao salvar
    
    def carregar_materiais_novos(self):
        """Recarrega a lista de materiais"""
        try:
            self.materiais = api_client.listar_materiais_para_pedido()
            self.material_combo.clear()
            self.material_combo.addItem("-- Selecione um material existente --")
            for mat in self.materiais:
                self.material_combo.addItem(
                    f"{mat.get('nome', '')} - Estoque: {mat.get('quantidade', 0)} - {mat.get('empresa', '')}", 
                    mat.get("id")
                )
        except Exception as e:
            print(f"Erro ao recarregar materiais: {e}")
    
    def carregar_dados_edicao(self):
        """Carrega os dados do pedido para edição"""
        if self.dados_item is None:
            return
        
        # Mostrar campo de status na edição
        self.status_label.setVisible(True)
        self.status_combo.setVisible(True)
        
        # Material
        material_id = self.dados_item.get("material_id")
        material_nome = self.dados_item.get("material_nome", "")
        
        # Procurar o material na lista
        encontrado = False
        for i, mat in enumerate(self.materiais):
            if mat.get("id") == material_id:
                self.material_combo.setCurrentIndex(i + 1)  # +1 por causa do placeholder
                encontrado = True
                break
        
        if not encontrado:
            self.material_edit.setText(material_nome)
            self.material_id_edit.setText(str(material_id) if material_id else "")
        
        # Quantidade
        self.quantidade_spin.setValue(self.dados_item.get("quantidade", 1))
        
        # Solicitante
        self.solicitante_edit.setText(str(self.dados_item.get("solicitante", "")))
        
        # Empresa
        empresa = str(self.dados_item.get("empresa", ""))
        idx = self.empresa_combo.findText(empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)
        
        # Departamento
        departamento = str(self.dados_item.get("departamento", ""))
        idx = self.departamento_combo.findText(departamento)
        if idx >= 0:
            self.departamento_combo.setCurrentIndex(idx)
        
        # Status
        status = str(self.dados_item.get("status", "pendente"))
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        
        # Observação
        self.observacao_edit.setPlainText(str(self.dados_item.get("observacao", "")))
    
    def salvar(self):
        # Obter o material
        material_nome = self.material_edit.text().strip()
        material_id = self.material_id_edit.text().strip()
        
        if not material_nome:
            QMessageBox.warning(self, "Atenção", "Informe o nome do material!")
            return
        
        quantidade = self.quantidade_spin.value()
        solicitante = self.solicitante_edit.text().strip()
        empresa = self.empresa_combo.currentText()
        departamento = self.departamento_combo.currentText()
        observacao = self.observacao_edit.toPlainText().strip()
        
        if not solicitante:
            QMessageBox.warning(self, "Atenção", "Informe o nome do solicitante!")
            return
        
        if not empresa:
            QMessageBox.warning(self, "Atenção", "Selecione uma empresa!")
            return
        
        # Verificar se o material já existe no banco
        material_existente = None
        for mat in self.materiais:
            if mat.get("nome", "").lower() == material_nome.lower():
                material_existente = mat
                break
        
        # Preparar dados do pedido
        dados = {
            "quantidade": quantidade,
            "solicitante": solicitante,
            "empresa": empresa,
            "departamento": departamento or None,
            "observacao": observacao or None
        }
        
        if material_existente:
            # Material existe, usar o ID
            dados["material_id"] = material_existente.get("id")
        else:
            # Material não existe, enviar o nome para o backend criar
            dados["material_nome"] = material_nome
        
        # Se for edição, incluir status
        if self.dados_item:
            dados["status"] = self.status_combo.currentText()
        
        try:
            if self.dados_item:
                # Atualizar
                response = api_client.atualizar_pedido(self.dados_item["id"], dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Pedido atualizado com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao atualizar pedido")
            else:
                # Criar
                response = api_client.criar_pedido(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Pedido criado com sucesso!")
                    # Recarregar materiais para incluir o novo material
                    self.carregar_materiais_novos()
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao criar pedido")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

            