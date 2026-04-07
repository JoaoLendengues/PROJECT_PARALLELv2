from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QTextEdit,
                               QDateEdit, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from api_client import api_client


class DemandasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.demandas = []
        self.init_ui()
        self.carregar_demandas()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)
        
        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("🎫 Demandas / Chamados TI")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()
        
        # Botão Nova Demanda
        self.novo_btn = QPushButton("+ Nova Demanda")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.nova_demanda)
        header.addWidget(self.novo_btn)
        
        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_demandas)
        header.addWidget(self.atualizar_btn)
        
        layout.addLayout(header)
        
        # Filtros
        filtros = QHBoxLayout()
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Aberto", "Em Andamento", "Concluído", "Cancelado"])
        self.status_filter.currentTextChanged.connect(self.filtrar_demandas)
        filtros.addWidget(QLabel("Status:"))
        filtros.addWidget(self.status_filter)
        
        self.prioridade_filter = QComboBox()
        self.prioridade_filter.addItems(["Todas", "Alta", "Média", "Baixa"])
        self.prioridade_filter.currentTextChanged.connect(self.filtrar_demandas)
        filtros.addWidget(QLabel("Prioridade:"))
        filtros.addWidget(self.prioridade_filter)
        
        filtros.addStretch()
        
        layout.addLayout(filtros)
        
        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        
        headers = ["ID", "Título", "Solicitante", "Prioridade", "Urgência", "Status", "Data Abertura", "Responsável"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()
        
        self.ver_btn = QPushButton("👁️ Ver Detalhes")
        self.ver_btn.clicked.connect(self.ver_demanda)
        acoes.addWidget(self.ver_btn)
        
        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_demanda)
        acoes.addWidget(self.editar_btn)
        
        self.concluir_btn = QPushButton("✅ Concluir")
        self.concluir_btn.clicked.connect(self.concluir_demanda)
        acoes.addWidget(self.concluir_btn)
        
        self.cancelar_btn = QPushButton("❌ Cancelar")
        self.cancelar_btn.clicked.connect(self.cancelar_demanda)
        acoes.addWidget(self.cancelar_btn)
        
        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_demanda)
        acoes.addWidget(self.deletar_btn)
        
        layout.addLayout(acoes)
    
    def carregar_demandas(self):
        try:
            self.demandas = api_client.listar_demandas()
            self.atualizar_tabela(self.demandas)
            print(f"✅ Demandas carregadas: {len(self.demandas)}")
        except Exception as e:
            print(f"❌ Erro ao carregar demandas: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar demandas: {e}")
    
    def filtrar_demandas(self):
        status = self.status_filter.currentText().lower()
        prioridade = self.prioridade_filter.currentText().lower()
        
        filtered = []
        for d in self.demandas:
            if status != "todos" and d.get("status", "").lower() != status:
                continue
            if prioridade != "todas" and d.get("prioridade", "").lower() != prioridade:
                continue
            filtered.append(d)
        
        self.atualizar_tabela(filtered)
    
    def atualizar_tabela(self, demandas):
        self.tabela.setRowCount(len(demandas))
        
        prioridade_cores = {
            "alta": QColor(231, 111, 81),
            "media": QColor(244, 162, 97),
            "baixa": QColor(42, 157, 143)
        }
        
        status_cores = {
            "aberto": QColor(244, 162, 97),
            "andamento": QColor(42, 157, 143),
            "concluido": QColor(44, 125, 160),
            "cancelado": QColor(231, 111, 81)
        }
        
        for row, d in enumerate(demandas):
            self.tabela.setItem(row, 0, QTableWidgetItem(str(d.get("id", ""))))
            self.tabela.setItem(row, 1, QTableWidgetItem(d.get("titulo", "")[:60]))
            self.tabela.setItem(row, 2, QTableWidgetItem(d.get("solicitante", "-")))
            
            prioridade_item = QTableWidgetItem(d.get("prioridade", "media").upper())
            prioridade_item.setForeground(prioridade_cores.get(d.get("prioridade", "media"), QColor(0, 0, 0)))
            self.tabela.setItem(row, 3, prioridade_item)
            
            urgencia_item = QTableWidgetItem(d.get("urgencia", "media").upper())
            self.tabela.setItem(row, 4, urgencia_item)
            
            status_item = QTableWidgetItem(d.get("status", "aberto").upper())
            status_item.setForeground(status_cores.get(d.get("status", "aberto"), QColor(0, 0, 0)))
            self.tabela.setItem(row, 5, status_item)
            
            data = d.get("data_abertura", "")
            if data:
                data = data[:10]
            self.tabela.setItem(row, 6, QTableWidgetItem(data))
            
            self.tabela.setItem(row, 7, QTableWidgetItem(d.get("responsavel", "-")))
    
    def nova_demanda(self):
        dialog = DemandaDialog(parent=self)
        if dialog.exec():
            self.carregar_demandas()
    
    def ver_demanda(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para visualizar")
            return
        
        demanda_id = int(self.tabela.item(row, 0).text())
        demanda = next((d for d in self.demandas if d["id"] == demanda_id), None)
        
        if demanda:
            dialog = DemandaDialog(demanda_data=demanda, readonly=True, parent=self)
            dialog.exec()
    
    def editar_demanda(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para editar")
            return
        
        demanda_id = int(self.tabela.item(row, 0).text())
        demanda = next((d for d in self.demandas if d["id"] == demanda_id), None)
        
        if demanda:
            dialog = DemandaDialog(demanda_data=demanda, parent=self)
            if dialog.exec():
                self.carregar_demandas()
    
    def concluir_demanda(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para concluir")
            return
        
        demanda_id = int(self.tabela.item(row, 0).text())
        demanda_titulo = self.tabela.item(row, 1).text()
        
        confirm = QMessageBox.question(
            self,
            "Confirmar conclusão",
            f"Deseja concluir a demanda '{demanda_titulo}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if api_client.concluir_demanda(demanda_id):
                    QMessageBox.information(self, "Sucesso", "Demanda concluída com sucesso!")
                    self.carregar_demandas()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao concluir demanda")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao concluir: {e}")
    
    def cancelar_demanda(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para cancelar")
            return
        
        demanda_id = int(self.tabela.item(row, 0).text())
        demanda_titulo = self.tabela.item(row, 1).text()
        
        confirm = QMessageBox.question(
            self,
            "Confirmar cancelamento",
            f"Deseja cancelar a demanda '{demanda_titulo}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if api_client.cancelar_demanda(demanda_id):
                    QMessageBox.information(self, "Sucesso", "Demanda cancelada com sucesso!")
                    self.carregar_demandas()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao cancelar demanda")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cancelar: {e}")
    
    def deletar_demanda(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma demanda para deletar")
            return
        
        demanda_id = int(self.tabela.item(row, 0).text())
        demanda_titulo = self.tabela.item(row, 1).text()
        
        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar a demanda '{demanda_titulo}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if api_client.deletar_demanda(demanda_id):
                    QMessageBox.information(self, "Sucesso", "Demanda deletada com sucesso!")
                    self.carregar_demandas()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao deletar demanda")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


class DemandaDialog(QDialog):
    def __init__(self, demanda_data=None, readonly=False, parent=None):
        super().__init__(parent)
        self.dados_item = demanda_data
        self.readonly = readonly
        self.setWindowTitle("Detalhes da Demanda" if readonly else ("Editar Demanda" if demanda_data else "Nova Demanda"))
        self.setModal(True)
        self.setMinimumWidth(600)
        self.init_ui()
        
        if demanda_data and not readonly:
            self.carregar_dados_edicao()
        elif demanda_data and readonly:
            self.carregar_dados_visualizacao()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Título
        self.titulo_edit = QLineEdit()
        self.titulo_edit.setPlaceholderText("Título da demanda")
        form_layout.addRow("Título:", self.titulo_edit)
        
        # Descrição
        self.descricao_edit = QTextEdit()
        self.descricao_edit.setMaximumHeight(100)
        self.descricao_edit.setPlaceholderText("Descreva a demanda detalhadamente...")
        form_layout.addRow("Descrição:", self.descricao_edit)
        
        # Solicitante
        self.solicitante_edit = QLineEdit()
        self.solicitante_edit.setPlaceholderText("Nome de quem solicitou")
        form_layout.addRow("Solicitante:", self.solicitante_edit)
        
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
        
        # Prioridade
        self.prioridade_combo = QComboBox()
        self.prioridade_combo.addItems(["alta", "media", "baixa"])
        form_layout.addRow("Prioridade:", self.prioridade_combo)
        
        # Urgência
        self.urgencia_combo = QComboBox()
        self.urgencia_combo.addItems(["alta", "media", "baixa"])
        form_layout.addRow("Urgência:", self.urgencia_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["aberto", "andamento", "concluido", "cancelado"])
        form_layout.addRow("Status:", self.status_combo)
        
        # Data Prevista
        self.data_prevista = QDateEdit()
        self.data_prevista.setDate(QDate.currentDate().addDays(7))
        self.data_prevista.setCalendarPopup(True)
        form_layout.addRow("Data Prevista:", self.data_prevista)
        
        # Responsável
        self.responsavel_edit = QLineEdit()
        self.responsavel_edit.setPlaceholderText("Responsável pela demanda")
        form_layout.addRow("Responsável:", self.responsavel_edit)
        
        # Observação
        self.observacao_edit = QTextEdit()
        self.observacao_edit.setMaximumHeight(80)
        self.observacao_edit.setPlaceholderText("Observações adicionais...")
        form_layout.addRow("Observação:", self.observacao_edit)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        if not self.readonly:
            self.salvar_btn = QPushButton("Salvar")
            self.salvar_btn.clicked.connect(self.salvar)
            btn_layout.addWidget(self.salvar_btn)
        
        self.cancelar_btn = QPushButton("Fechar" if self.readonly else "Cancelar")
        self.cancelar_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancelar_btn)
        
        layout.addLayout(btn_layout)
        
        if self.readonly:
            self.set_readonly()
    
    def set_readonly(self):
        self.titulo_edit.setReadOnly(True)
        self.descricao_edit.setReadOnly(True)
        self.solicitante_edit.setReadOnly(True)
        self.departamento_combo.setEnabled(False)
        self.empresa_combo.setEnabled(False)
        self.prioridade_combo.setEnabled(False)
        self.urgencia_combo.setEnabled(False)
        self.status_combo.setEnabled(False)
        self.data_prevista.setEnabled(False)
        self.responsavel_edit.setReadOnly(True)
        self.observacao_edit.setReadOnly(True)
    
    def carregar_dados_edicao(self):
        if self.dados_item is None:
            return
        
        self.titulo_edit.setText(str(self.dados_item.get("titulo", "")))
        self.descricao_edit.setPlainText(str(self.dados_item.get("descricao", "")))
        self.solicitante_edit.setText(str(self.dados_item.get("solicitante", "")))
        
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
        
        prioridade = str(self.dados_item.get("prioridade", "media"))
        idx = self.prioridade_combo.findText(prioridade)
        if idx >= 0:
            self.prioridade_combo.setCurrentIndex(idx)
        
        urgencia = str(self.dados_item.get("urgencia", "media"))
        idx = self.urgencia_combo.findText(urgencia)
        if idx >= 0:
            self.urgencia_combo.setCurrentIndex(idx)
        
        status = str(self.dados_item.get("status", "aberto"))
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        
        data_prevista = self.dados_item.get("data_prevista")
        if data_prevista:
            self.data_prevista.setDate(QDate.fromString(data_prevista, "yyyy-MM-dd"))
        
        self.responsavel_edit.setText(str(self.dados_item.get("responsavel", "")))
        self.observacao_edit.setPlainText(str(self.dados_item.get("observacao", "")))
    
    def carregar_dados_visualizacao(self):
        self.carregar_dados_edicao()
    
    def salvar(self):
        dados = {
            "titulo": self.titulo_edit.text().strip(),
            "descricao": self.descricao_edit.toPlainText().strip(),
            "solicitante": self.solicitante_edit.text().strip(),
            "departamento": self.departamento_combo.currentText(),
            "empresa": self.empresa_combo.currentText(),
            "prioridade": self.prioridade_combo.currentText(),
            "urgencia": self.urgencia_combo.currentText(),
            "status": self.status_combo.currentText(),
            "data_prevista": self.data_prevista.date().toString("yyyy-MM-dd"),
            "responsavel": self.responsavel_edit.text().strip() or None,
            "observacao": self.observacao_edit.toPlainText().strip() or None
        }
        
        if not dados["titulo"]:
            QMessageBox.warning(self, "Atenção", "O título é obrigatório!")
            return
        
        if not dados["descricao"]:
            QMessageBox.warning(self, "Atenção", "A descrição é obrigatória!")
            return
        
        if not dados["solicitante"]:
            QMessageBox.warning(self, "Atenção", "O solicitante é obrigatório!")
            return
        
        try:
            if self.dados_item:
                response = api_client.atualizar_demanda(self.dados_item["id"], dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Demanda atualizada com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao atualizar demanda")
            else:
                response = api_client.criar_demanda(dados)
                if response:
                    QMessageBox.information(self, "Sucesso", "Demanda criada com sucesso!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Erro ao criar demanda")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
            