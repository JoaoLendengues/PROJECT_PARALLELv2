from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QComboBox,
                               QHeaderView, QMessageBox, QWidget, QFrame, QApplication)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from api_client import api_client
from widgets.toast_notification import notification_manager


class NotificationCenter(QDialog):
    """Central de Notificações - Janela para visualizar todas as notificações"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔔 Central de Notificações")
        self.setMinimumSize(950, 650)
        self.setModal(False)
        
        # Estilo da janela
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QTableWidget::item {
                padding: 8px 6px;
            }
            QHeaderView::section {
                padding: 8px 10px;
                background-color: #f1f5f9;
                font-weight: bold;
            }
        """)
        
        self.init_ui()
        self.carregar_notificacoes()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        titulo = QLabel("🔔 Central de Notificações")
        titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #1e293b; margin-bottom: 10px;")
        layout.addWidget(titulo)
        
        # Barra de filtros
        filtros_layout = QHBoxLayout()
        
        filtros_layout.addWidget(QLabel("Filtrar por:"))
        
        self.filtro_status = QComboBox()
        self.filtro_status.addItems(["Todas", "Não lidas", "Lidas", "Ignoradas"])
        self.filtro_status.currentTextChanged.connect(self.filtrar_notificacoes)
        filtros_layout.addWidget(self.filtro_status)
        
        filtros_layout.addSpacing(20)
        
        self.filtro_prioridade = QComboBox()
        self.filtro_prioridade.addItems(["Todas", "Alta", "Média", "Baixa"])
        self.filtro_prioridade.currentTextChanged.connect(self.filtrar_notificacoes)
        filtros_layout.addWidget(self.filtro_prioridade)
        
        filtros_layout.addStretch()
        
        # Botão marcar todas como lidas
        self.btn_marcar_todas = QPushButton("✓ Marcar todas")
        self.btn_marcar_todas.setFixedHeight(30)
        self.btn_marcar_todas.clicked.connect(self.marcar_todas_lidas)
        filtros_layout.addWidget(self.btn_marcar_todas)
        
        # Botão atualizar
        self.btn_atualizar = QPushButton("🔄 Atualizar")
        self.btn_atualizar.setFixedHeight(30)
        self.btn_atualizar.clicked.connect(self.carregar_notificacoes)
        filtros_layout.addWidget(self.btn_atualizar)
        
        layout.addLayout(filtros_layout)
        
        # Tabela de notificações
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["Prioridade", "Título", "Mensagem", "Data", "Ações"])
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Configurar largura das colunas
        self.tabela.setColumnWidth(0, 80)
        self.tabela.setColumnWidth(3, 140)
        self.tabela.setColumnWidth(4, 260)
        
        layout.addWidget(self.tabela)
        
        # Rodapé com informações
        footer_layout = QHBoxLayout()
        
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("color: #64748b; font-size: 12px;")
        footer_layout.addWidget(self.lbl_info)
        
        footer_layout.addStretch()
        
        # Botão fechar
        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.setFixedSize(80, 30)
        self.btn_fechar.clicked.connect(self.close)
        footer_layout.addWidget(self.btn_fechar)
        
        layout.addLayout(footer_layout)
    
    def carregar_notificacoes(self):
        """Carrega as notificações do backend"""
        try:
            # ✅ Carregar todas as notificações (lidas e não lidas)
            notificacoes = api_client.listar_notificacoes(limit=100)
            
            # Ordenar por data (mais recentes primeiro)
            notificacoes.sort(key=lambda x: x.get("criado_em", ""), reverse=True)
            
            self.notificacoes_originais = notificacoes
            
            # Aplicar filtro atual
            self.filtrar_notificacoes()
            
            # Atualizar badge
            self.atualizar_badge()
            
            # Debug
            nao_lidas = len([n for n in notificacoes if n.get("status") == "nao_lida"])
            print(f"📊 Total: {len(notificacoes)} | Não lidas: {nao_lidas}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar notificações: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar notificações: {e}")
    
    def atualizar_badge(self):
        """Atualiza o badge de notificações na janela principal"""
        try:
            parent = self.parent()
            if parent:
                # Verificar se o parent tem o método que queremos chamar
                if hasattr(parent, 'notification_btn'):
                    btn = getattr(parent, 'notification_btn')
                    if hasattr(btn, 'atualizar_contador'):
                        btn.atualizar_contador()
                        return
        
            # Se não encontrou, tentar pela aplicação inteira
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'notification_btn'):
                    btn = getattr(widget, 'notification_btn')
                    if hasattr(btn, 'atualizar_contador'):
                        btn.atualizar_contador()
                        break

        except Exception as e:
            print(f'⚠️ Erro ao atualizar badge: {e}')
    
    def filtrar_notificacoes(self):
        """Filtra as notificações com base nos filtros selecionados"""
        status_filtro = self.filtro_status.currentText().lower()
        prioridade_filtro = self.filtro_prioridade.currentText().lower()
        
        if not hasattr(self, 'notificacoes_originais'):
            return
        
        filtradas = []
        for notif in self.notificacoes_originais:
            # Filtro por status
            if status_filtro != "todas":
                if status_filtro == "não lidas" and notif.get("status") != "nao_lida":
                    continue
                elif status_filtro == "lidas" and notif.get("status") != "lida":
                    continue
                elif status_filtro == "ignoradas" and notif.get("status") != "ignorada":
                    continue
            
            # Filtro por prioridade
            if prioridade_filtro != "todas" and notif.get("prioridade") != prioridade_filtro:
                continue
            
            filtradas.append(notif)
        
        self.atualizar_tabela(filtradas)
    
    def atualizar_tabela(self, notificacoes):
        """Atualiza a tabela com a lista de notificações"""
        self.tabela.setRowCount(len(notificacoes))
        
        prioridade_cores = {
            "alta": QColor(239, 68, 68),
            "media": QColor(245, 158, 11),
            "baixa": QColor(59, 130, 246)
        }
        
        for row, notif in enumerate(notificacoes):
            # Prioridade
            prioridade = notif.get("prioridade", "baixa")
            prioridade_item = QTableWidgetItem(prioridade.upper())
            prioridade_item.setForeground(prioridade_cores.get(prioridade, QColor(100, 100, 100)))
            prioridade_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(row, 0, prioridade_item)
            
            # Título
            titulo = notif.get("titulo", "")
            status = notif.get("status", "nao_lida")
            if status == "nao_lida":
                titulo = f"● {titulo}"
            self.tabela.setItem(row, 1, QTableWidgetItem(titulo))
            
            # Mensagem
            mensagem = notif.get("mensagem", "")[:80]
            if len(notif.get("mensagem", "")) > 80:
                mensagem += "..."
            self.tabela.setItem(row, 2, QTableWidgetItem(mensagem))
            
            # Data
            data = notif.get("criado_em", "")
            if data:
                data = data[:16].replace("T", " ")
            self.tabela.setItem(row, 3, QTableWidgetItem(data))
            
            # Botões de ação
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)
            
            if status == "nao_lida":
                btn_marcar = QPushButton("✓")
                btn_marcar.setFixedSize(30, 28)
                btn_marcar.setToolTip("Marcar como lida")
                btn_marcar.setStyleSheet("""
                    QPushButton {
                        background-color: #10b981;
                        color: white;
                        border-radius: 6px;
                        font-size: 13px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover { background-color: #059669; }
                    QPushButton:pressed { background-color: #047857; }
                """)
                btn_marcar.clicked.connect(lambda checked=False, n=notif: self.marcar_como_lida(n))
                btn_layout.addWidget(btn_marcar)
            
            btn_ver = QPushButton("👁️")
            btn_ver.setFixedSize(30, 28)
            btn_ver.setToolTip("Ver detalhes")
            btn_ver.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { background-color: #2563eb; }
                QPushButton:pressed { background-color: #1d4ed8; }
            """)
            btn_ver.clicked.connect(lambda checked=False, n=notif: self.executar_acao(n))
            btn_layout.addWidget(btn_ver)
            
            btn_excluir = QPushButton("🗑️")
            btn_excluir.setFixedSize(30, 28)
            btn_excluir.setToolTip("Excluir")
            btn_excluir.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { background-color: #dc2626; }
                QPushButton:pressed { background-color: #b91c1c; }
            """)
            btn_excluir.clicked.connect(lambda checked=False, n=notif: self.deletar_notificacao(n))
            btn_layout.addWidget(btn_excluir)
            
            btn_layout.addStretch()
            self.tabela.setCellWidget(row, 4, btn_widget)
        
        self.tabela.resizeRowsToContents()
        self.tabela.verticalHeader().setDefaultSectionSize(42)
        
        total = len(notificacoes)
        nao_lidas = len([n for n in notificacoes if n.get("status") == "nao_lida"])
        self.lbl_info.setText(f"📊 Total: {total} | Não lidas: {nao_lidas}")
    
    def marcar_como_lida(self, notificacao):
        """Marca uma notificação como lida"""
        print(f"🔍 Marcando notificação {notificacao.get('id')} como lida")
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
        print("🔍 Botão 'Marcar todas' clicado!")
        
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
    
    def deletar_notificacao(self, notificacao):
        """Deleta uma notificação"""
        confirm = QMessageBox.question(
            self, "Confirmar exclusão",
            f"Deseja excluir a notificação '{notificacao.get('titulo')}'?",
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
        """Executa a ação da notificação"""
        acao = notificacao.get("acao")
        acao_id = notificacao.get("acao_id")
        
        self.close()
        
        parent = self.parent()
        if parent and acao:
            if hasattr(parent, acao):
                getattr(parent, acao)()
                if acao_id and hasattr(parent, f"{acao}_com_id"):
                    getattr(parent, f"{acao}_com_id")(acao_id)
            
            if notificacao.get("status") == "nao_lida":
                api_client.marcar_notificacao_lida(notificacao.get("id"))
                self.atualizar_badge()
