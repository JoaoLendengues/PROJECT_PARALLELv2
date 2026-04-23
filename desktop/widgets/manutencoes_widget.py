from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QDateEdit,
                               QTextEdit, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from api_client import api_client


class ManutencoesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.manutencoes = []
        self.manutencoes_cache = []
        self.maquinas = []
        self.empresas = []
        self._loaded = False
        self.init_ui()

    def on_show(self):
        if not self._loaded:
            self.carregar_maquinas()
            self.carregar_empresas()
            self.carregar_manutencoes()
            self._loaded = True
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)
        
        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("🔧 Manutenções")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()
        
        # Botão Nova Manutenção
        self.novo_btn = QPushButton("+ Nova Manutenção")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.nova_manutencao)
        header.addWidget(self.novo_btn)
        
        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_manutencoes)
        header.addWidget(self.atualizar_btn)
        
        layout.addLayout(header)
        
        # Barra de pesquisa e filtros
        filtros = QHBoxLayout()
        
        # Filtro Status
        filtros.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Pendente", "Em Andamento", "Concluída", "Cancelada"])
        self.status_filter.currentTextChanged.connect(self.filtrar_manutencoes)
        filtros.addWidget(self.status_filter)

        filtros.addSpacing(20)

        # Filtro Empresa
        filtros.addWidget(QLabel('Empresa:'))
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(150)
        self.empresa_filter.addItem('Todas as empresas')
        self.empresa_filter.currentTextChanged.connect(self.filtrar_manutencoes)
        filtros.addWidget(self.empresa_filter)

        filtros.addSpacing(20)

        # Filtro Máquina
        filtros.addWidget(QLabel("Máquina:"))        
        self.maquina_filter = QComboBox()
        self.maquina_filter.addItem("Todas as máquinas")
        self.maquina_filter.currentTextChanged.connect(self.filtrar_manutencoes)
        filtros.addWidget(self.maquina_filter)
        
        
        filtros.addStretch()
        
        layout.addLayout(filtros)
        
        # Tabela de manutenções com estilo melhorado
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
        
        headers = ["ID", "Máquina", "Tipo", "Descrição", "Data Início", "Data Fim", "Responsável", "Status"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()
        
        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_manutencao)
        acoes.addWidget(self.editar_btn)
        
        self.concluir_btn = QPushButton("✓ Concluir")
        self.concluir_btn.clicked.connect(self.concluir_manutencao)
        acoes.addWidget(self.concluir_btn)
        
        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_manutencao)
        acoes.addWidget(self.deletar_btn)
        
        layout.addLayout(acoes)
    
    def carregar_maquinas(self):
        """Carrega a lista de máquinas para o filtro"""
        try:
            self.maquinas = api_client.listar_maquinas_para_manutencao()
            self.maquina_filter.clear()
            self.maquina_filter.addItem("Todas as máquinas")
            for maq in self.maquinas:
                self.maquina_filter.addItem(f"{maq.get('nome', '')} - {maq.get('empresa', '')}")
            print(f'✅ Máquinas carregadas: {len(self.maquinas)}')
        except Exception as e:
            print(f"Erro ao carregar máquinas: {e}")

    def carregar_empresas(self):
        """Carrega a lista de empresas do backend para o filtro"""
        try:
            empresas = api_client.get_empresas()
            self.empresa_filter.clear()
            self.empresa_filter.addItem('Todas as empresas')
            for emp in empresas:
                if emp and emp.strip():
                    self.empresa_filter.addItem(emp)
            print(f'✅ Empresas carregadas para filtro: {len(empresas)}')
        except Exception as e:
            print(f'❌ Erro ao carregar empresas: {e}')
    
    def carregar_manutencoes(self):
        """Carrega a lista de manutenções do backend"""
        try:
            self.manutencoes = api_client.listar_manutencoes()
            self.manutencoes_cache = self.manutencoes.copy()
            self.atualizar_tabela(self.manutencoes)
            print(f"✅ Manutenções carregadas: {len(self.manutencoes)}")
        except Exception as e:
            print(f"❌ Erro ao carregar manutenções: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar manutenções: {e}")
    
    def filtrar_manutencoes(self):
        """Filtra as manutenções com base nos filtros"""
        status = self.status_filter.currentText().lower()
        empresa = self.empresa_filter.currentText()
        maquina_texto = self.maquina_filter.currentText()
        
        filtered = []
        for manut in self.manutencoes:
            # Filtro por status
            if status != "todos" and manut.get("status", "").lower() != status:
                continue

            # Filtro por empresa
            if empresa != 'Todas as empresas':
                # Buscar a empresa da máquina
                maquina_id = manut.get('maquina_id')
                if maquina_id:
                    maquina = next((m for m in self.maquinas if m.get('id') == maquina_id), None)
                    if maquina and maquina.get('empresa') != empresa:
                        continue
                else:
                    # Se não encontrar a máquina, pular
                    continue

            
            # Filtro por máquina
            if maquina_texto != "Todas as máquinas":
                maquina_nome = manut.get("maquina_nome", "")
                if maquina_texto not in maquina_nome:
                    continue
            
            filtered.append(manut)
        
        self.atualizar_tabela(filtered)
    
    def atualizar_tabela(self, manutencoes):
        """Atualiza a tabela com a lista de manutenções"""
        self.tabela.setRowCount(len(manutencoes))
        
        status_colors = {
            "pendente": QColor(244, 162, 97),
            "andamento": QColor(42, 157, 143),
            "concluida": QColor(44, 125, 160),
            "cancelada": QColor(231, 111, 81)
        }
        
        for row, manut in enumerate(manutencoes):
            self.tabela.setItem(row, 0, QTableWidgetItem(str(manut.get("id", ""))))
            self.tabela.setItem(row, 1, QTableWidgetItem(manut.get("maquina_nome", "-")))
            self.tabela.setItem(row, 2, QTableWidgetItem(manut.get("tipo", "-").upper()))
            self.tabela.setItem(row, 3, QTableWidgetItem(manut.get("descricao", "-")[:60]))
            self.tabela.setItem(row, 4, QTableWidgetItem(manut.get("data_inicio", "-")))
            self.tabela.setItem(row, 5, QTableWidgetItem(manut.get("data_fim", "-") or "-"))
            self.tabela.setItem(row, 6, QTableWidgetItem(manut.get("responsavel", "-")))
            
            status_item = QTableWidgetItem(manut.get("status", "pendente").upper())
            status_color = status_colors.get(manut.get("status", "pendente"), QColor(0, 0, 0))
            status_item.setForeground(status_color)
            self.tabela.setItem(row, 7, status_item)
    
    def nova_manutencao(self):
        dialog = ManutencaoDialog(maquinas=self.maquinas, parent=self)
        if dialog.exec():
            self.carregar_manutencoes()
            self.carregar_maquinas()
    
    def editar_manutencao(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma manutenção para editar")
            return
        
        manutencao_id = int(self.tabela.item(current_row, 0).text())
        manutencao = next((m for m in self.manutencoes if m["id"] == manutencao_id), None)
        
        if manutencao:
            dialog = ManutencaoDialog(manutencao_data=manutencao, maquinas=self.maquinas, parent=self)
            if dialog.exec():
                self.carregar_manutencoes()
                self.carregar_maquinas()
    
    def concluir_manutencao(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma manutenção para concluir")
            return
        
        manutencao_id = int(self.tabela.item(current_row, 0).text())
        manutencao = next((m for m in self.manutencoes if m["id"] == manutencao_id), None)
        
        if not manutencao:
            return
        
        if manutencao.get("status") == "concluida":
            QMessageBox.warning(self, "Atenção", "Esta manutenção já está concluída!")
            return
        
        confirm = QMessageBox.question(
            self,
            "Confirmar conclusão",
            f"Deseja concluir a manutenção da máquina '{manutencao.get('maquina_nome', '')}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if api_client.concluir_manutencao(manutencao_id):
                    QMessageBox.information(self, "Sucesso", "Manutenção concluída com sucesso!")
                    self.carregar_manutencoes()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao concluir manutenção")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao concluir: {e}")
    
    def deletar_manutencao(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma manutenção para deletar")
            return
        
        manutencao_id = int(self.tabela.item(current_row, 0).text())
        manutencao_desc = self.tabela.item(current_row, 3).text()
        
        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar a manutenção '{manutencao_desc[:50]}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if api_client.deletar_manutencao(manutencao_id):
                    QMessageBox.information(self, "Sucesso", "Manutenção deletada com sucesso!")
                    self.carregar_manutencoes()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao deletar manutenção")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


class ManutencaoDialog(QDialog):
    def __init__(self, manutencao_data=None, maquinas=None, parent=None):
        super().__init__(parent)
        self.dados_item = manutencao_data
        self.maquinas = maquinas or []
        self.maquinas_filtradas = self.maquinas.copy()
        self.setWindowTitle("Cadastro de Manutenção" if not manutencao_data else "Editar Manutenção")
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
        
        if manutencao_data:
            self.carregar_dados_edicao()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Empresa (NOVO)
        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_empresas()
        self.empresa_combo.currentIndexChanged.connect(self.filtrar_maquinas_por_empresa)
        form_layout.addRow('Empresa:', self.empresa_combo)
        
        # Máquina
        self.maquina_combo = QComboBox()
        self.maquina_combo.setEditable(False)
        self.maquina_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_maquinas_combo()
        form_layout.addRow('Máquina:', self.maquina_combo)
        
        # Tipo
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["preventiva", "corretiva", "emergencial"])
        form_layout.addRow("Tipo:", self.tipo_combo)
        
        # Descrição
        self.descricao_edit = QTextEdit()
        self.descricao_edit.setMaximumHeight(80)
        self.descricao_edit.setPlaceholderText("Descreva a manutenção a ser realizada...")
        form_layout.addRow("Descrição:", self.descricao_edit)
        
        # Data Início
        self.data_inicio = QDateEdit()
        self.data_inicio.setDate(QDate.currentDate())
        self.data_inicio.setCalendarPopup(True)
        form_layout.addRow("Data de Início:", self.data_inicio)
        
        # Data Próxima Manutenção
        self.data_proxima = QDateEdit()
        self.data_proxima.setDate(QDate.currentDate().addMonths(6))
        self.data_proxima.setCalendarPopup(True)
        form_layout.addRow("Próx. Manutenção:", self.data_proxima)
        
        # Responsável
        self.responsavel_edit = QLineEdit()
        self.responsavel_edit.setPlaceholderText("Nome do responsável")
        form_layout.addRow("Responsável:", self.responsavel_edit)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pendente", "andamento", "concluida", "cancelada"])
        form_layout.addRow("Status:", self.status_combo)
        
        # Campo Data de Término (só aparece na edição)
        self.data_fim_label = QLabel("Data de Término:")
        self.data_fim = QDateEdit()
        self.data_fim.setDate(QDate.currentDate())
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setSpecialValueText("Não definida")
        
        # Inicialmente esconder campo de edição
        self.data_fim_label.setVisible(False)
        self.data_fim.setVisible(False)
        
        # Adicionar ao layout (mas invisível)
        form_layout.addRow(self.data_fim_label, self.data_fim)
        
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

    def carregar_empresas(self):
        """Carrega as empresas do backend para o combobox"""
        try:
            empresas = api_client.get_empresas()
            self.empresa_combo.clear()
            self.empresa_combo.addItem("Todas as empresas")  # Opção para mostrar todas
            for emp in empresas:
                if emp and emp.strip():
                    self.empresa_combo.addItem(emp)
        except Exception as e:
            print(f'❌ Erro ao carregar empresas: {e}')
            self.empresa_combo.addItem("Todas as empresas")
            default_empresas = ["Matriz", "Filial 1", "Filial 2", "Filial 3"]
            for emp in default_empresas:
                self.empresa_combo.addItem(emp)
    
    def carregar_maquinas_combo(self):
        """Carrega as máquinas no combo box"""
        self.maquina_combo.clear()
        for maq in self.maquinas_filtradas:
            self.maquina_combo.addItem(
                f"{maq.get('nome', '')} - {maq.get('empresa', '')}", 
                maq.get("id")
            )

    def filtrar_maquinas_por_empresa(self):
        """Filtra as máquinas pela empresa selecionada"""
        empresa = self.empresa_combo.currentText()
        
        if empresa == "Todas as empresas" or not empresa:
            self.maquinas_filtradas = self.maquinas.copy()
        else:
            self.maquinas_filtradas = [m for m in self.maquinas if m.get("empresa") == empresa]
        
        self.carregar_maquinas_combo()
    
    def carregar_dados_edicao(self):
        """Carrega os dados da manutenção para edição (mostra campo de data fim)"""
        if self.dados_item is None:
            return
        
        # Mostrar campo de data de término
        self.data_fim_label.setVisible(True)
        self.data_fim.setVisible(True)
        
        # Buscar a máquina para saber a empresa
        maquina_id = self.dados_item.get("maquina_id")
        maquina_selecionada = None
        for maq in self.maquinas:
            if maq.get("id") == maquina_id:
                maquina_selecionada = maq
                break
        
        # Selecionar a empresa correta no filtro
        if maquina_selecionada:
            empresa = maquina_selecionada.get("empresa", "")
            idx = self.empresa_combo.findText(empresa)
            if idx >= 0:
                self.empresa_combo.setCurrentIndex(idx)
        
        # Selecionar a máquina
        for i in range(self.maquina_combo.count()):
            if self.maquina_combo.itemData(i) == maquina_id:
                self.maquina_combo.setCurrentIndex(i)
                break
        
        # Tipo
        tipo = str(self.dados_item.get("tipo", ""))
        idx = self.tipo_combo.findText(tipo)
        if idx >= 0:
            self.tipo_combo.setCurrentIndex(idx)
        
        # Descrição
        self.descricao_edit.setPlainText(str(self.dados_item.get("descricao", "")))
        
        # Datas
        data_inicio = self.dados_item.get("data_inicio")
        if data_inicio:
            self.data_inicio.setDate(QDate.fromString(data_inicio, "yyyy-MM-dd"))
        
        data_fim = self.dados_item.get("data_fim")
        if data_fim:
            self.data_fim.setDate(QDate.fromString(data_fim, "yyyy-MM-dd"))
        
        data_proxima = self.dados_item.get("data_proxima")
        if data_proxima:
            self.data_proxima.setDate(QDate.fromString(data_proxima, "yyyy-MM-dd"))
        
        # Responsável
        self.responsavel_edit.setText(str(self.dados_item.get("responsavel", "")))
        
        # Status
        status = str(self.dados_item.get("status", "pendente"))
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
    
    def salvar(self):
        # Obter ID da máquina selecionada
        maquina_id = self.maquina_combo.currentData()
        
        # Validar campos obrigatórios
        if not maquina_id:
            QMessageBox.warning(self, "Atenção", "Selecione uma máquina!")
            return
        
        descricao = self.descricao_edit.toPlainText().strip()
        if not descricao:
            QMessageBox.warning(self, "Atenção", "A descrição é obrigatória!")
            return
        
        dados = {
            "maquina_id": maquina_id,
            "tipo": self.tipo_combo.currentText(),
            "descricao": descricao,
            "data_inicio": self.data_inicio.date().toString("yyyy-MM-dd"),
            "data_proxima": self.data_proxima.date().toString("yyyy-MM-dd"),
            "responsavel": self.responsavel_edit.text().strip() or None,
            "status": self.status_combo.currentText()
        }
        
        # Se for edição, adicionar data de término (opcional)
        if self.dados_item:
            data_fim_val = self.data_fim.date().toString("yyyy-MM-dd")
            if data_fim_val != "2000-01-01":
                dados["data_fim"] = data_fim_val
        
        try:
            if self.dados_item:
                # Atualizar
                response = api_client.atualizar_manutencao(self.dados_item["id"], dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Manutenção atualizada com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao atualizar manutenção")
            else:
                # Criar
                response = api_client.criar_manutencao(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Manutenção criada com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao criar manutenção")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
            