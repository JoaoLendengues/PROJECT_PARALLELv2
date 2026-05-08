from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from api_client import api_client
from widgets.filter_utils import filter_value, is_all_option
from widgets.table_utils import configure_data_table
from widgets.toast_notification import notification_manager


class NotificationCenter(QDialog):
    """Central de notificacoes do desktop."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notificacoes_originais = []
        self.notificacoes_atuais = []

        self.setObjectName("notificationCenterDialog")
        self.setWindowTitle("Central de Notificacoes")
        self.setMinimumSize(1100, 700)
        self.setModal(False)

        self.init_ui()
        self._apply_theme_styles()
        self.carregar_notificacoes()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)

        self.titulo = QLabel("Central de Notificacoes")
        self.titulo.setObjectName("notificationTitle")
        self.titulo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header_layout.addWidget(self.titulo)

        header_layout.addStretch()

        self.badge_label = QLabel("0 nao lidas")
        self.badge_label.setObjectName("notificationBadge")
        header_layout.addWidget(self.badge_label)

        layout.addLayout(header_layout)

        self.subtitulo = QLabel("Acompanhe, filtre e trate avisos do sistema em um unico lugar.")
        self.subtitulo.setObjectName("notificationSubtitle")
        self.subtitulo.setWordWrap(True)
        layout.addWidget(self.subtitulo)

        self.filtros_card = QFrame()
        self.filtros_card.setObjectName("filterCard")
        filtros_layout = QHBoxLayout(self.filtros_card)
        filtros_layout.setContentsMargins(16, 12, 16, 12)
        filtros_layout.setSpacing(16)

        self.lbl_status = QLabel("Status:")
        filtros_layout.addWidget(self.lbl_status)

        self.filtro_status = QComboBox()
        self.filtro_status.addItems(["Todas", "Nao lidas", "Lidas", "Ignoradas"])
        self.filtro_status.currentTextChanged.connect(self.filtrar_notificacoes)
        filtros_layout.addWidget(self.filtro_status)

        self.lbl_prioridade = QLabel("Prioridade:")
        filtros_layout.addWidget(self.lbl_prioridade)

        self.filtro_prioridade = QComboBox()
        self.filtro_prioridade.addItems(["Todas", "Alta", "Media", "Baixa"])
        self.filtro_prioridade.currentTextChanged.connect(self.filtrar_notificacoes)
        filtros_layout.addWidget(self.filtro_prioridade)

        filtros_layout.addStretch()
        layout.addWidget(self.filtros_card)

        self.tabela = QTableWidget()
        self.tabela.setObjectName("notificationTable")
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Prioridade", "Titulo", "Mensagem", "Data"])
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tabela.setShowGrid(False)
        self.tabela.setWordWrap(True)
        self.tabela.setFocusPolicy(Qt.ClickFocus)
        self.tabela.itemDoubleClicked.connect(self._ao_duplo_clique_na_tabela)
        self.tabela.itemSelectionChanged.connect(self._atualizar_estado_selecao)
        configure_data_table(self.tabela, stretch_columns=(2,))
        layout.addWidget(self.tabela)

        self.footer_card = QFrame()
        self.footer_card.setObjectName("footerCard")
        footer_layout = QHBoxLayout(self.footer_card)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(16)

        self.lbl_info = QLabel("")
        self.lbl_info.setObjectName("notificationInfo")
        footer_layout.addWidget(self.lbl_info)
        footer_layout.addStretch()

        self.btn_marcar = QPushButton("Marcar selecionadas")
        self.btn_marcar.setObjectName("successButton")
        self.btn_marcar.clicked.connect(self.marcar_selecionadas_como_lidas)
        footer_layout.addWidget(self.btn_marcar)

        self.btn_marcar_todas = QPushButton("Marcar todas como lidas")
        self.btn_marcar_todas.setObjectName("successButton")
        self.btn_marcar_todas.clicked.connect(self.marcar_todas_lidas)
        footer_layout.addWidget(self.btn_marcar_todas)

        self.btn_excluir = QPushButton("Excluir selecionadas")
        self.btn_excluir.setObjectName("dangerButton")
        self.btn_excluir.clicked.connect(self.excluir_selecionadas)
        footer_layout.addWidget(self.btn_excluir)

        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.setObjectName("primaryButton")
        self.btn_atualizar.clicked.connect(self.carregar_notificacoes)
        footer_layout.addWidget(self.btn_atualizar)

        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.setObjectName("secondaryButton")
        self.btn_fechar.clicked.connect(self.close)
        footer_layout.addWidget(self.btn_fechar)

        layout.addWidget(self.footer_card)

    def showEvent(self, event):
        self._apply_theme_styles()
        super().showEvent(event)

    def _is_dark_theme(self):
        app = QApplication.instance()
        return str(app.property("accessibility_theme") or "Claro") == "Escuro"

    def _apply_theme_styles(self):
        dark = self._is_dark_theme()
        colors = self._theme_colors(dark)

        self.setStyleSheet(
            f"""
            QDialog#notificationCenterDialog {{
                background-color: {colors['dialog_bg']};
                color: {colors['text']};
            }}

            QLabel {{
                color: {colors['text']};
                background: transparent;
            }}

            QLabel#notificationTitle {{
                color: {colors['title']};
            }}

            QLabel#notificationSubtitle {{
                color: {colors['muted']};
                font-size: 13px;
                padding: 0 0 2px 0;
            }}

            QLabel#notificationInfo {{
                color: {colors['muted']};
                font-size: 13px;
            }}

            QFrame#filterCard,
            QFrame#footerCard {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['card_border']};
                border-radius: 16px;
            }}

            QComboBox {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['input_border']};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 120px;
                color: {colors['text']};
                font-size: 13px;
            }}

            QComboBox:hover {{
                border-color: {colors['input_border_hover']};
            }}

            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['card_border']};
                padding: 4px;
            }}

            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                color: {colors['text']};
            }}

            QComboBox QAbstractItemView::item:selected {{
                background-color: {colors['selection_bg']};
                color: {colors['selection_text']};
            }}

            QTableWidget#notificationTable {{
                background-color: {colors['table_bg']};
                color: {colors['text']};
                border: 1px solid {colors['card_border']};
                border-radius: 12px;
                outline: none;
                gridline-color: transparent;
                selection-background-color: {colors['selection_bg']};
                selection-color: {colors['selection_text']};
            }}

            QTableWidget#notificationTable::item {{
                padding: 12px 8px;
                border-bottom: 1px solid {colors['row_border']};
                color: {colors['text']};
            }}

            QTableWidget#notificationTable::item:selected {{
                background-color: {colors['selection_bg']};
                color: {colors['selection_text']};
            }}

            QHeaderView::section {{
                background-color: {colors['header_bg']};
                color: {colors['muted']};
                padding: 12px 8px;
                border: none;
                font-weight: 600;
                font-size: 12px;
            }}

            QScrollBar:vertical {{
                background-color: {colors['scroll_bg']};
                border-radius: 10px;
                width: 8px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {colors['scroll_handle']};
                border-radius: 10px;
                min-height: 20px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {colors['scroll_handle_hover']};
            }}

            QPushButton#successButton {{
                background-color: #10b981;
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 600;
                border: none;
            }}

            QPushButton#successButton:hover {{
                background-color: #059669;
            }}

            QPushButton#dangerButton {{
                background-color: #ef4444;
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 600;
                border: none;
            }}

            QPushButton#dangerButton:hover {{
                background-color: #dc2626;
            }}

            QPushButton#primaryButton {{
                background-color: #2563eb;
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 600;
                border: none;
            }}

            QPushButton#primaryButton:hover {{
                background-color: #1d4ed8;
            }}

            QPushButton#secondaryButton {{
                background-color: {colors['secondary_btn_bg']};
                color: {colors['secondary_btn_text']};
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 600;
                border: 1px solid {colors['secondary_btn_border']};
            }}

            QPushButton#secondaryButton:hover {{
                background-color: {colors['secondary_btn_hover']};
            }}

            QMessageBox QPushButton {{
                min-width: 80px;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 500;
            }}
            """
        )
        self._apply_badge_style()

    def _theme_colors(self, dark):
        if dark:
            return {
                "dialog_bg": "#0f172a",
                "card_bg": "#111827",
                "card_border": "#334155",
                "table_bg": "#111827",
                "header_bg": "#1e293b",
                "row_border": "#1e293b",
                "text": "#e2e8f0",
                "title": "#f8fafc",
                "muted": "#94a3b8",
                "input_bg": "#0f172a",
                "input_border": "#475569",
                "input_border_hover": "#60a5fa",
                "selection_bg": "#1d4ed8",
                "selection_text": "#f8fafc",
                "scroll_bg": "#1e293b",
                "scroll_handle": "#475569",
                "scroll_handle_hover": "#64748b",
                "secondary_btn_bg": "#172033",
                "secondary_btn_text": "#e2e8f0",
                "secondary_btn_border": "#475569",
                "secondary_btn_hover": "#1e293b",
                "badge_bg": "#1e293b",
                "badge_text": "#e2e8f0",
            }

        return {
            "dialog_bg": "#f8fafc",
            "card_bg": "#ffffff",
            "card_border": "#e2e8f0",
            "table_bg": "#ffffff",
            "header_bg": "#f8fafc",
            "row_border": "#f1f5f9",
            "text": "#1e293b",
            "title": "#0f172a",
            "muted": "#64748b",
            "input_bg": "#ffffff",
            "input_border": "#e2e8f0",
            "input_border_hover": "#94a3b8",
            "selection_bg": "#dbeafe",
            "selection_text": "#1e293b",
            "scroll_bg": "#f1f5f9",
            "scroll_handle": "#cbd5e1",
            "scroll_handle_hover": "#94a3b8",
            "secondary_btn_bg": "#64748b",
            "secondary_btn_text": "#ffffff",
            "secondary_btn_border": "#64748b",
            "secondary_btn_hover": "#475569",
            "badge_bg": "#e2e8f0",
            "badge_text": "#475569",
        }

    def _apply_badge_style(self):
        colors = self._theme_colors(self._is_dark_theme())
        nao_lidas = len([n for n in self.notificacoes_originais if n.get("status") == "nao_lida"])

        if nao_lidas > 0:
            self.badge_label.setStyleSheet(
                """
                QLabel#notificationBadge {
                    background-color: #ef4444;
                    color: #ffffff;
                    border-radius: 20px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }
                """
            )
            return

        self.badge_label.setStyleSheet(
            f"""
            QLabel#notificationBadge {{
                background-color: {colors['badge_bg']};
                color: {colors['badge_text']};
                border-radius: 20px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            """
        )

    def carregar_notificacoes(self):
        """Carrega as notificacoes do backend."""
        try:
            notificacoes = api_client.listar_notificacoes(limit=100)
            notificacoes.sort(key=lambda x: x.get("criado_em", ""), reverse=True)
            self.notificacoes_originais = notificacoes
            self.filtrar_notificacoes()
            self.atualizar_badge()
            nao_lidas = len([n for n in notificacoes if n.get("status") == "nao_lida"])
            print(f"Notificacoes carregadas: total={len(notificacoes)} nao_lidas={nao_lidas}")
        except Exception as e:
            print(f"Erro ao carregar notificacoes: {e}")

    def atualizar_badge(self):
        try:
            nao_lidas = len([n for n in self.notificacoes_originais if n.get("status") == "nao_lida"])
            self.badge_label.setText(f"{nao_lidas} nao lidas")
            self._apply_badge_style()

            parent = self.parent()
            if parent and hasattr(parent, "notification_btn"):
                parent.notification_btn.atualizar_contador()
        except Exception:
            pass

    def filtrar_notificacoes(self):
        status_filtro = filter_value(self.filtro_status.currentText())
        prioridade_filtro = filter_value(self.filtro_prioridade.currentText())

        filtradas = []
        for notif in self.notificacoes_originais:
            if not is_all_option(status_filtro):
                if status_filtro == "nao lidas" and notif.get("status") != "nao_lida":
                    continue
                if status_filtro == "lidas" and notif.get("status") != "lida":
                    continue
                if status_filtro == "ignoradas" and notif.get("status") != "ignorada":
                    continue

            if not is_all_option(prioridade_filtro) and notif.get("prioridade") != prioridade_filtro:
                continue

            filtradas.append(notif)

        self.atualizar_tabela(filtradas)

    def atualizar_tabela(self, notificacoes):
        self.tabela.setRowCount(len(notificacoes))
        dark = self._is_dark_theme()

        prioridade_cores = {
            "alta": {"color": "#fecaca" if dark else "#b91c1c", "bg": "#7f1d1d" if dark else "#fee2e2", "label": "ALTA"},
            "media": {"color": "#fde68a" if dark else "#b45309", "bg": "#78350f" if dark else "#fef3c7", "label": "MEDIA"},
            "baixa": {"color": "#bfdbfe" if dark else "#1d4ed8", "bg": "#1e3a8a" if dark else "#dbeafe", "label": "BAIXA"},
        }

        titulo_nao_lido = QColor("#f8fafc" if dark else "#1e293b")
        titulo_lido = QColor("#94a3b8" if dark else "#64748b")
        data_color = QColor("#94a3b8")

        for row, notif in enumerate(notificacoes):
            prioridade = notif.get("prioridade", "baixa")
            status = notif.get("status", "nao_lida")
            cor = prioridade_cores.get(prioridade, prioridade_cores["baixa"])

            prioridade_widget = QFrame()
            prioridade_widget.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {cor['bg']};
                    border-radius: 20px;
                }}
                QLabel {{
                    color: {cor['color']};
                    font-weight: bold;
                    font-size: 11px;
                    background: transparent;
                }}
                """
            )
            prioridade_layout = QHBoxLayout(prioridade_widget)
            prioridade_layout.setContentsMargins(8, 6, 8, 6)
            prioridade_layout.setAlignment(Qt.AlignCenter)
            prioridade_label = QLabel(cor["label"])
            prioridade_label.setAlignment(Qt.AlignCenter)
            prioridade_layout.addWidget(prioridade_label)
            self.tabela.setCellWidget(row, 0, prioridade_widget)

            titulo = notif.get("titulo", "")
            if status == "nao_lida":
                titulo = f"* {titulo}"
            titulo_item = QTableWidgetItem(titulo)
            titulo_item.setForeground(titulo_nao_lido if status == "nao_lida" else titulo_lido)
            if status == "nao_lida":
                font = QFont()
                font.setBold(True)
                titulo_item.setFont(font)
            self.tabela.setItem(row, 1, titulo_item)

            mensagem = notif.get("mensagem", "")
            mensagem_item = QTableWidgetItem(mensagem)
            mensagem_item.setToolTip(mensagem)
            mensagem_item.setForeground(QColor("#e2e8f0" if dark else "#1e293b"))
            self.tabela.setItem(row, 2, mensagem_item)

            data = notif.get("criado_em", "")
            if data:
                data = data[:16].replace("T", " ")
            data_item = QTableWidgetItem(data)
            data_item.setForeground(data_color)
            self.tabela.setItem(row, 3, data_item)

        self.tabela.resizeRowsToContents()
        self.tabela.clearSelection()
        self.tabela.setCurrentCell(-1, -1)
        self.tabela.clearFocus()

        self.notificacoes_atuais = notificacoes
        self._atualizar_estado_selecao()

    def obter_notificacao_selecionada(self):
        current_row = self.tabela.currentRow()
        if current_row < 0 or current_row >= len(self.notificacoes_atuais):
            return None
        return self.notificacoes_atuais[current_row]

    def obter_notificacoes_selecionadas(self):
        indices = sorted({index.row() for index in self.tabela.selectionModel().selectedRows()})
        return [self.notificacoes_atuais[index] for index in indices if 0 <= index < len(self.notificacoes_atuais)]

    def _atualizar_estado_selecao(self):
        selecionadas = self.obter_notificacoes_selecionadas()
        quantidade = len(selecionadas)
        total = len(self.notificacoes_atuais)
        nao_lidas = len([n for n in self.notificacoes_atuais if n.get("status") == "nao_lida"])

        if quantidade <= 0:
            self.btn_marcar.setText("Marcar selecionadas")
            self.btn_excluir.setText("Excluir selecionadas")
            self.lbl_info.setText(f"{total} notificacoes | {nao_lidas} nao lidas")
            return

        sufixo = "notificacao" if quantidade == 1 else "notificacoes"
        self.btn_marcar.setText(f"Marcar {quantidade} {sufixo}")
        self.btn_excluir.setText(f"Excluir {quantidade} {sufixo}")
        self.lbl_info.setText(f"{quantidade} selecionada(s) | {total} exibidas | {nao_lidas} nao lidas")

    def marcar_selecionadas_como_lidas(self):
        notificacoes = self.obter_notificacoes_selecionadas()
        if not notificacoes:
            notification_manager.warning("Selecione ao menos uma notificacao.", self, 2000)
            return

        pendentes = [n for n in notificacoes if n.get("status") != "lida"]
        if not pendentes:
            notification_manager.info("As notificacoes selecionadas ja estao lidas.", self, 2000)
            return

        if len(pendentes) > 1:
            confirm = QMessageBox.question(
                self,
                "Confirmar",
                f"Deseja marcar {len(pendentes)} notificacoes como lidas?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm != QMessageBox.Yes:
                return

        try:
            sucesso = True
            for notificacao in pendentes:
                if not api_client.marcar_notificacao_lida(notificacao.get("id")):
                    sucesso = False

            if sucesso:
                mensagem = "Notificacao marcada como lida!" if len(pendentes) == 1 else "Notificacoes marcadas como lidas!"
                notification_manager.success(mensagem, self, 2200)
                self.carregar_notificacoes()
            else:
                notification_manager.error("Nem todas as notificacoes puderam ser marcadas como lidas.", self, 3000)
        except Exception as e:
            print(f"Erro ao marcar notificacao: {e}")

    def marcar_todas_lidas(self):
        nao_lidas = [n for n in self.notificacoes_originais if n.get("status") == "nao_lida"]
        if not nao_lidas:
            notification_manager.info("Nao ha notificacoes nao lidas!", self, 2000)
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            f"Deseja marcar {len(nao_lidas)} notificacao(oes) como lida(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            try:
                if api_client.marcar_todas_notificacoes_lidas():
                    notification_manager.success("Todas as notificacoes foram marcadas como lidas!", self, 3000)
                    self.carregar_notificacoes()
                else:
                    notification_manager.error("Erro ao marcar notificacoes", self, 3000)
            except Exception as e:
                print(f"Erro ao marcar todas as notificacoes: {e}")

    def excluir_selecionadas(self):
        notificacoes = self.obter_notificacoes_selecionadas()
        if not notificacoes:
            notification_manager.warning("Selecione ao menos uma notificacao.", self, 2000)
            return

        quantidade = len(notificacoes)
        confirm = QMessageBox.question(
            self,
            "Confirmar exclusao",
            "Deseja excluir esta notificacao?"
            if quantidade == 1
            else f"Deseja excluir {quantidade} notificacoes selecionadas?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            try:
                sucesso = True
                for notificacao in notificacoes:
                    if not api_client.deletar_notificacao(notificacao.get("id")):
                        sucesso = False

                if sucesso:
                    mensagem = "Notificacao excluida!" if quantidade == 1 else "Notificacoes excluidas!"
                    notification_manager.success(mensagem, self, 2200)
                    self.carregar_notificacoes()
                else:
                    notification_manager.error("Nem todas as notificacoes puderam ser excluidas.", self, 3000)
            except Exception as e:
                print(f"Erro ao excluir notificacao: {e}")

    def executar_acao(self, notificacao):
        acao = notificacao.get("acao")
        self.close()

        parent = self.parent()
        if parent and acao and hasattr(parent, acao):
            getattr(parent, acao)()
            if notificacao.get("status") == "nao_lida":
                api_client.marcar_notificacao_lida(notificacao.get("id"))

    def _ao_duplo_clique_na_tabela(self, item):
        row = item.row()
        if 0 <= row < len(self.notificacoes_atuais):
            self.executar_acao(self.notificacoes_atuais[row])
