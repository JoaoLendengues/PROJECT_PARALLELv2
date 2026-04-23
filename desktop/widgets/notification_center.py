from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QComboBox,
                               QHeaderView, QMessageBox, QWidget, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from api_client import api_client
from widgets.toast_notification import notification_manager


class NotificationCenter(QDialog):
    """Central de Notificações - Design Moderno"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Central de Notificações")
        self.setMinimumSize(1100, 700)
        self.setModal(False)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QLabel {
                color: #1e293b;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 120px;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #94a3b8;
            }
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 12px;
                outline: none;
                gridline-color: transparent;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #f1f5f9;
            }
            QTableWidget::item:selected {
                background-color: #e6f0ff;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #64748b;
                padding: 12px 8px;
                border: none;
                font-weight: 600;
                font-size: 12px;
            }
            QScrollBar:vertical {
                background-color: #f1f5f9;
                border-radius: 10px;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #cbd5e1;
                border-radius: 10px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #94a3b8;
            }
            /* ✅ Estilo para botões do QMessageBox */
            QMessageBox QPushButton {
                min-width: 80px;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 500;
            }
        """)
        
        self.init_ui()
        self.carregar_notificacoes()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # ========== CABEÇALHO ==========
        header_layout = QHBoxLayout()
        
        titulo = QLabel("🔔 Central de Notificações")
        titulo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #0f172a;")
        header_layout.addWidget(titulo)
        
        header_layout.addStretch()
        
        self.badge_label = QLabel("0 não lidas")
        self.badge_label.setStyleSheet("""
            background-color: #e2e8f0;
            color: #475569;
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 12px;
            font-weight: 500;
        """)
        header_layout.addWidget(self.badge_label)
        
        layout.addLayout(header_layout)
        
        # ========== BARRA DE FILTROS ==========
        filtros_card = QFrame()
        filtros_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
                padding: 8px;
            }
        """)
        filtros_layout = QHBoxLayout(filtros_card)
        filtros_layout.setContentsMargins(16, 12, 16, 12)
        filtros_layout.setSpacing(16)
        
        filtros_layout.addWidget(QLabel("📋 Status:"))
        self.filtro_status = QComboBox()
        self.filtro_status.addItems(["Todas", "Não lidas", "Lidas", "Ignoradas"])
        self.filtro_status.currentTextChanged.connect(self.filtrar_notificacoes)
        filtros_layout.addWidget(self.filtro_status)
        
        filtros_layout.addWidget(QLabel("🎯 Prioridade:"))
        self.filtro_prioridade = QComboBox()
        self.filtro_prioridade.addItems(["Todas", "Alta", "Média", "Baixa"])
        self.filtro_prioridade.currentTextChanged.connect(self.filtrar_notificacoes)
        filtros_layout.addWidget(self.filtro_prioridade)
        
        filtros_layout.addStretch()
        
        layout.addWidget(filtros_card)
        
        # ========== TABELA ==========
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Prioridade", "Título", "Mensagem", "Data"])
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setShowGrid(False)
        self.tabela.setWordWrap(True)
        self.tabela.setSelectionMode(QTableWidget.ExtendedSelection)
        
        self.tabela.setColumnWidth(0, 110)
        self.tabela.setColumnWidth(1, 300)
        self.tabela.setColumnWidth(2, 450)
        self.tabela.setColumnWidth(3, 150)
        
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
        # ========== RODAPÉ COM BOTÕES DE AÇÃO ==========
        footer_card = QFrame()
        footer_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
                padding: 8px;
            }
        """)
        footer_layout = QHBoxLayout(footer_card)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(16)
        
        # Informações
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("color: #64748b; font-size: 13px;")
        footer_layout.addWidget(self.lbl_info)
        
        footer_layout.addStretch()
        
        # ✅ Botão Marcar como Lida
        self.btn_marcar = QPushButton("✓ Marcar como lida")
        self.btn_marcar.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_marcar.clicked.connect(self.marcar_selecionada_como_lida)
        footer_layout.addWidget(self.btn_marcar)
        
        # ✅ Botão Marcar Todas
        self.btn_marcar_todas = QPushButton("✓ Marcar todas como lidas")
        self.btn_marcar_todas.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_marcar_todas.clicked.connect(self.marcar_todas_lidas)
        footer_layout.addWidget(self.btn_marcar_todas)
        
        # ✅ Botão Excluir
        self.btn_excluir = QPushButton("🗑️ Excluir")
        self.btn_excluir.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.btn_excluir.clicked.connect(self.excluir_selecionada)
        footer_layout.addWidget(self.btn_excluir)
        
        # ✅ Botão Atualizar (com cor azul)
        self.btn_atualizar = QPushButton("🔄 Atualizar")
        self.btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_atualizar.clicked.connect(self.carregar_notificacoes)
        footer_layout.addWidget(self.btn_atualizar)
        
        # ✅ Botão Fechar
        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        self.btn_fechar.clicked.connect(self.close)
        footer_layout.addWidget(self.btn_fechar)
        
        layout.addWidget(footer_card)
    
    def carregar_notificacoes(self):
        """Carrega as notificações do backend"""
        try:
            notificacoes = api_client.listar_notificacoes(limit=100)
            notificacoes.sort(key=lambda x: x.get("criado_em", ""), reverse=True)
            
            self.notificacoes_originais = notificacoes
            self.filtrar_notificacoes()
            self.atualizar_badge()
            
            nao_lidas = len([n for n in notificacoes if n.get("status") == "nao_lida"])
            print(f"📊 Total: {len(notificacoes)} | Não lidas: {nao_lidas}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar notificações: {e}")
    
    def atualizar_badge(self):
        """Atualiza o badge de notificações"""
        try:
            if hasattr(self, 'notificacoes_originais'):
                nao_lidas = len([n for n in self.notificacoes_originais if n.get("status") == "nao_lida"])
                self.badge_label.setText(f"{nao_lidas} não lidas")
                
                if nao_lidas > 0:
                    self.badge_label.setStyleSheet("""
                        background-color: #ef4444;
                        color: white;
                        border-radius: 20px;
                        padding: 6px 16px;
                        font-size: 12px;
                        font-weight: 500;
                    """)
                else:
                    self.badge_label.setStyleSheet("""
                        background-color: #e2e8f0;
                        color: #475569;
                        border-radius: 20px;
                        padding: 6px 16px;
                        font-size: 12px;
                        font-weight: 500;
                    """)
            
            parent = self.parent()
            if parent and hasattr(parent, 'notification_btn'):
                parent.notification_btn.atualizar_contador()
        except:
            pass
    
    def filtrar_notificacoes(self):
        """Filtra as notificações"""
        status_filtro = self.filtro_status.currentText().lower()
        prioridade_filtro = self.filtro_prioridade.currentText().lower()
        
        if not hasattr(self, 'notificacoes_originais'):
            return
        
        filtradas = []
        for notif in self.notificacoes_originais:
            if status_filtro != "todas":
                if status_filtro == "não lidas" and notif.get("status") != "nao_lida":
                    continue
                elif status_filtro == "lidas" and notif.get("status") != "lida":
                    continue
                elif status_filtro == "ignoradas" and notif.get("status") != "ignorada":
                    continue
            
            if prioridade_filtro != "todas" and notif.get("prioridade") != prioridade_filtro:
                continue
            
            filtradas.append(notif)
        
        self.atualizar_tabela(filtradas)
    
    def atualizar_tabela(self, notificacoes):
        """Atualiza a tabela com design moderno"""
        self.tabela.setRowCount(len(notificacoes))
        
        prioridade_cores = {
            "alta": {"color": "#DC2626", "bg": "#FEE2E2", "label": "🔴 ALTA"},
            "media": {"color": "#D97706", "bg": "#FEF3C7", "label": "🟠 MÉDIA"},
            "baixa": {"color": "#2563EB", "bg": "#DBEAFE", "label": "🔵 BAIXA"}
        }
        
        for row, notif in enumerate(notificacoes):
            prioridade = notif.get("prioridade", "baixa")
            status = notif.get("status", "nao_lida")
            cor = prioridade_cores.get(prioridade, prioridade_cores["baixa"])
            
            # Prioridade
            prioridade_widget = QFrame()
            prioridade_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {cor['bg']};
                    border-radius: 20px;
                }}
                QLabel {{
                    color: {cor['color']};
                    font-weight: bold;
                    font-size: 11px;
                }}
            """)
            prioridade_layout = QHBoxLayout(prioridade_widget)
            prioridade_layout.setContentsMargins(8, 6, 8, 6)
            prioridade_layout.setAlignment(Qt.AlignCenter)
            prioridade_label = QLabel(cor['label'])
            prioridade_label.setAlignment(Qt.AlignCenter)
            prioridade_layout.addWidget(prioridade_label)
            self.tabela.setCellWidget(row, 0, prioridade_widget)
            
            # Título
            titulo = notif.get("titulo", "")
            if status == "nao_lida":
                titulo = f"● {titulo}"
            titulo_item = QTableWidgetItem(titulo)
            if status == "nao_lida":
                titulo_item.setForeground(QColor("#1e293b"))
                font = QFont()
                font.setBold(True)
                titulo_item.setFont(font)
            else:
                titulo_item.setForeground(QColor("#64748b"))
            self.tabela.setItem(row, 1, titulo_item)
            
            # Mensagem
            mensagem = notif.get("mensagem", "")
            mensagem_item = QTableWidgetItem(mensagem)
            mensagem_item.setToolTip(mensagem)
            self.tabela.setItem(row, 2, mensagem_item)
            
            # Data
            data = notif.get("criado_em", "")
            if data:
                data = data[:16].replace("T", " ")
            data_item = QTableWidgetItem(data)
            data_item.setForeground(QColor("#94a3b8"))
            self.tabela.setItem(row, 3, data_item)
        
        self.tabela.resizeRowsToContents()
        
        self.notificacoes_atuais = notificacoes
        
        total = len(notificacoes)
        nao_lidas = len([n for n in notificacoes if n.get("status") == "nao_lida"])
        self.lbl_info.setText(f"📊 {total} notificações • {nao_lidas} não lidas")
    
    def obter_notificacao_selecionada(self):
        """Retorna a notificação selecionada na tabela"""
        current_row = self.tabela.currentRow()
        if current_row < 0 or not hasattr(self, 'notificacoes_atuais'):
            return None
        
        if current_row < len(self.notificacoes_atuais):
            return self.notificacoes_atuais[current_row]
        return None
    
    def marcar_selecionada_como_lida(self):
        """Marca a notificação selecionada como lida"""
        notificacao = self.obter_notificacao_selecionada()
        if not notificacao:
            notification_manager.warning("Selecione uma notificação!", self, 2000)
            return
        
        if notificacao.get("status") == "lida":
            notification_manager.info("Esta notificação já está lida!", self, 2000)
            return
        
        try:
            success = api_client.marcar_notificacao_lida(notificacao.get("id"))
            if success:
                notification_manager.success("Notificação marcada como lida!", self, 2000)
                self.carregar_notificacoes()
            else:
                notification_manager.error("Erro ao marcar notificação", self, 3000)
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def marcar_todas_lidas(self):
        """Marca todas as notificações como lidas"""
        if not hasattr(self, 'notificacoes_originais'):
            return
        
        nao_lidas = [n for n in self.notificacoes_originais if n.get("status") == "nao_lida"]
        if not nao_lidas:
            notification_manager.info("Não há notificações não lidas!", self, 2000)
            return
        
        confirm = QMessageBox.question(
            self, "Confirmar",
            f"Deseja marcar {len(nao_lidas)} notificação(ões) como lida(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                success = api_client.marcar_todas_notificacoes_lidas()
                if success:
                    notification_manager.success("Todas as notificações foram marcadas como lidas!", self, 3000)
                    self.carregar_notificacoes()
                else:
                    notification_manager.error("Erro ao marcar notificações", self, 3000)
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def excluir_selecionada(self):
        """Exclui a notificação selecionada"""
        notificacao = self.obter_notificacao_selecionada()
        if not notificacao:
            notification_manager.warning("Selecione uma notificação!", self, 2000)
            return
        
        confirm = QMessageBox.question(
            self, "Confirmar exclusão",
            f"Deseja excluir esta notificação?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                success = api_client.deletar_notificacao(notificacao.get("id"))
                if success:
                    notification_manager.success("Notificação excluída!", self, 2000)
                    self.carregar_notificacoes()
                else:
                    notification_manager.error("Erro ao excluir notificação", self, 3000)
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def executar_acao(self, notificacao):
        """Executa a ação da notificação ao clicar duas vezes"""
        acao = notificacao.get("acao")
        
        self.close()
        
        parent = self.parent()
        if parent and acao and hasattr(parent, acao):
            getattr(parent, acao)()
            
            if notificacao.get("status") == "nao_lida":
                api_client.marcar_notificacao_lida(notificacao.get("id"))
    
    def mouseDoubleClickEvent(self, event):
        """Ao clicar duas vezes na tabela, executar ação"""
        current_row = self.tabela.currentRow()
        if current_row >= 0 and hasattr(self, 'notificacoes_atuais'):
            if current_row < len(self.notificacoes_atuais):
                self.executar_acao(self.notificacoes_atuais[current_row])
        super().mouseDoubleClickEvent(event)
        