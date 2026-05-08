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
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from api_client import api_client
from widgets.filter_utils import filter_value, is_all_option
from widgets.table_utils import configure_data_table
from widgets.toast_notification import notification_manager


class NotificationCenter(QDialog):
    """Central de notificacoes com lista, busca e painel de detalhe."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notificacoes_originais = []
        self.notificacoes_atuais = []
        self.mapa_tipos = {
            "demanda": "Demandas",
            "pedido": "Pedidos",
            "manutencao": "Manutencoes",
            "conexao": "Rede",
            "backup": "Backup",
            "atualizacao": "Atualizacoes",
            "estoque_critico": "Estoque",
            "estoque_baixo": "Estoque",
            "sistema": "Sistema",
        }

        self.setObjectName("notificationCenterDialog")
        self.setWindowTitle("Central de Notificacoes")
        self.setMinimumSize(1220, 760)
        self.setModal(False)

        self.init_ui()
        self._apply_theme_styles()
        self.carregar_notificacoes()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(20)
        root_layout.setContentsMargins(24, 24, 24, 24)

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
        root_layout.addLayout(header_layout)

        self.subtitulo = QLabel("Acompanhe, filtre, pesquise e trate avisos do sistema em um unico lugar.")
        self.subtitulo.setObjectName("notificationSubtitle")
        self.subtitulo.setWordWrap(True)
        root_layout.addWidget(self.subtitulo)

        self.filtros_card = QFrame()
        self.filtros_card.setObjectName("filterCard")
        filtros_layout = QHBoxLayout(self.filtros_card)
        filtros_layout.setContentsMargins(16, 12, 16, 12)
        filtros_layout.setSpacing(14)

        self.lbl_busca = QLabel("Busca:")
        filtros_layout.addWidget(self.lbl_busca)

        self.campo_busca = QLineEdit()
        self.campo_busca.setObjectName("notificationSearch")
        self.campo_busca.setPlaceholderText("Pesquisar por titulo, mensagem, origem ou acao...")
        self.campo_busca.setClearButtonEnabled(True)
        self.campo_busca.setMinimumWidth(320)
        self.campo_busca.textChanged.connect(self.filtrar_notificacoes)
        filtros_layout.addWidget(self.campo_busca)

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

        self.lbl_tipo = QLabel("Origem:")
        filtros_layout.addWidget(self.lbl_tipo)

        self.filtro_tipo = QComboBox()
        self.filtro_tipo.addItems(["Todas"])
        self.filtro_tipo.currentTextChanged.connect(self.filtrar_notificacoes)
        filtros_layout.addWidget(self.filtro_tipo)

        filtros_layout.addStretch()
        root_layout.addWidget(self.filtros_card)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        self.list_container = QWidget()
        self.list_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        list_layout = QVBoxLayout(self.list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        self.tabela = QTableWidget()
        self.tabela.setObjectName("notificationTable")
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["Prioridade", "Origem", "Titulo", "Mensagem", "Data"])
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tabela.setShowGrid(False)
        self.tabela.setWordWrap(True)
        self.tabela.setFocusPolicy(Qt.ClickFocus)
        self.tabela.itemDoubleClicked.connect(self._ao_duplo_clique_na_tabela)
        self.tabela.itemSelectionChanged.connect(self._atualizar_estado_selecao)
        configure_data_table(self.tabela, stretch_columns=(3,))
        list_layout.addWidget(self.tabela)
        content_layout.addWidget(self.list_container, 3)

        self.detail_card = QFrame()
        self.detail_card.setObjectName("detailCard")
        self.detail_card.setMinimumWidth(330)
        self.detail_card.setMaximumWidth(390)
        self.detail_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        detail_layout = QVBoxLayout(self.detail_card)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(14)

        self.detail_heading = QLabel("Detalhes")
        self.detail_heading.setObjectName("detailHeading")
        self.detail_heading.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        detail_layout.addWidget(self.detail_heading)

        chip_layout = QHBoxLayout()
        chip_layout.setSpacing(8)
        self.detail_status_chip = QLabel("Sem selecao")
        self.detail_status_chip.setObjectName("detailStatusChip")
        chip_layout.addWidget(self.detail_status_chip)
        self.detail_type_chip = QLabel("Sistema")
        self.detail_type_chip.setObjectName("detailTypeChip")
        chip_layout.addWidget(self.detail_type_chip)
        chip_layout.addStretch()
        detail_layout.addLayout(chip_layout)

        self.detail_title = QLabel("Selecione uma notificacao")
        self.detail_title.setObjectName("detailTitle")
        self.detail_title.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        self.detail_title.setWordWrap(True)
        detail_layout.addWidget(self.detail_title)

        self.detail_message = QLabel(
            "Escolha um item da lista para ver o conteudo completo, a origem e as acoes disponiveis."
        )
        self.detail_message.setObjectName("detailMessage")
        self.detail_message.setWordWrap(True)
        self.detail_message.setTextInteractionFlags(Qt.TextSelectableByMouse)
        detail_layout.addWidget(self.detail_message)

        self.detail_info = QLabel("Nenhuma notificacao selecionada.")
        self.detail_info.setObjectName("detailInfo")
        self.detail_info.setWordWrap(True)
        detail_layout.addWidget(self.detail_info)
        detail_layout.addStretch()

        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        self.btn_abrir_acao = QPushButton("Abrir")
        self.btn_abrir_acao.setObjectName("primaryButton")
        self.btn_abrir_acao.setMinimumWidth(92)
        self.btn_abrir_acao.clicked.connect(self.abrir_notificacao_atual)
        action_layout.addWidget(self.btn_abrir_acao)

        self.btn_marcar_item = QPushButton("Marcar como lida")
        self.btn_marcar_item.setObjectName("successButton")
        self.btn_marcar_item.setMinimumWidth(132)
        self.btn_marcar_item.clicked.connect(self.marcar_notificacao_atual)
        action_layout.addWidget(self.btn_marcar_item)

        self.btn_excluir_item = QPushButton("Excluir")
        self.btn_excluir_item.setObjectName("dangerButton")
        self.btn_excluir_item.setMinimumWidth(92)
        self.btn_excluir_item.clicked.connect(self.excluir_notificacao_atual)
        action_layout.addWidget(self.btn_excluir_item)
        detail_layout.addLayout(action_layout)
        content_layout.addWidget(self.detail_card, 1)

        root_layout.addLayout(content_layout)

        self.footer_card = QFrame()
        self.footer_card.setObjectName("footerCard")
        footer_layout = QHBoxLayout(self.footer_card)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(14)

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

        self.btn_selecionar_todas = QPushButton("Selecionar tudo")
        self.btn_selecionar_todas.setObjectName("secondaryButton")
        self.btn_selecionar_todas.clicked.connect(self.selecionar_todas)
        footer_layout.addWidget(self.btn_selecionar_todas)

        self.btn_limpar_lidas = QPushButton("Limpar lidas")
        self.btn_limpar_lidas.setObjectName("secondaryButton")
        self.btn_limpar_lidas.clicked.connect(self.limpar_lidas)
        footer_layout.addWidget(self.btn_limpar_lidas)

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
        root_layout.addWidget(self.footer_card)

        self._resetar_detalhes()

    def showEvent(self, event):
        self._apply_theme_styles()
        super().showEvent(event)

    def _is_dark_theme(self):
        app = QApplication.instance()
        return str(app.property("accessibility_theme") or "Claro") == "Escuro"

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
            QLabel#notificationTitle,
            QLabel#detailHeading,
            QLabel#detailTitle {{
                color: {colors['title']};
            }}
            QLabel#notificationSubtitle,
            QLabel#notificationInfo,
            QLabel#detailInfo {{
                color: {colors['muted']};
                font-size: 13px;
            }}
            QLabel#detailMessage {{
                color: {colors['text']};
                font-size: 13px;
                line-height: 1.3;
            }}
            QFrame#filterCard,
            QFrame#footerCard,
            QFrame#detailCard {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['card_border']};
                border-radius: 16px;
            }}
            QLineEdit#notificationSearch {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['input_border']};
                border-radius: 10px;
                padding: 10px 12px;
                min-width: 260px;
                color: {colors['text']};
                font-size: 13px;
            }}
            QLineEdit#notificationSearch:hover,
            QLineEdit#notificationSearch:focus {{
                border-color: {colors['input_border_hover']};
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
        self._apply_detail_chip_styles()

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

    def _apply_detail_chip_styles(self):
        dark = self._is_dark_theme()
        status = (self.detail_status_chip.text() or "").lower()
        status_bg = "#1e293b"
        status_fg = "#e2e8f0"
        if "nao lida" in status:
            status_bg = "#7f1d1d" if dark else "#fee2e2"
            status_fg = "#fecaca" if dark else "#b91c1c"
        elif "lida" in status:
            status_bg = "#172033" if dark else "#e2e8f0"
            status_fg = "#cbd5e1" if dark else "#475569"
        elif "ignorada" in status:
            status_bg = "#3f2b11" if dark else "#fef3c7"
            status_fg = "#fde68a" if dark else "#b45309"

        type_bg = "#10243f" if dark else "#dbeafe"
        type_fg = "#93c5fd" if dark else "#1d4ed8"
        for label, bg, fg in (
            (self.detail_status_chip, status_bg, status_fg),
            (self.detail_type_chip, type_bg, type_fg),
        ):
            label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {bg};
                    color: {fg};
                    border-radius: 14px;
                    padding: 6px 12px;
                    font-size: 11px;
                    font-weight: 700;
                }}
                """
            )

    def _label_tipo(self, tipo):
        base = (tipo or "sistema").lower()
        return self.mapa_tipos.get(base, base.replace("_", " ").title())

    def _popular_filtro_tipo(self):
        atual = self.filtro_tipo.currentText() if hasattr(self, "filtro_tipo") else "Todas"
        tipos = sorted({self._label_tipo(n.get("tipo")) for n in self.notificacoes_originais if n.get("tipo")})
        self.filtro_tipo.blockSignals(True)
        self.filtro_tipo.clear()
        self.filtro_tipo.addItem("Todas")
        self.filtro_tipo.addItems(tipos)
        index = self.filtro_tipo.findText(atual)
        self.filtro_tipo.setCurrentIndex(index if index >= 0 else 0)
        self.filtro_tipo.blockSignals(False)

    def _resetar_detalhes(self):
        self.detail_status_chip.setText("Sem selecao")
        self.detail_type_chip.setText("Sistema")
        self.detail_title.setText("Selecione uma notificacao")
        self.detail_message.setText(
            "Escolha um item da lista para ver o conteudo completo, a origem e as acoes disponiveis."
        )
        self.detail_info.setText("Nenhuma notificacao selecionada.")
        self.btn_abrir_acao.setEnabled(False)
        self.btn_marcar_item.setEnabled(False)
        self.btn_excluir_item.setEnabled(False)
        self._apply_detail_chip_styles()

    def _atualizar_detalhes(self, notificacao):
        if not notificacao:
            self._resetar_detalhes()
            return

        status = str(notificacao.get("status", "nao_lida")).replace("_", " ").title()
        tipo = self._label_tipo(notificacao.get("tipo"))
        criado_em = str(notificacao.get("criado_em", "") or "")
        if criado_em:
            criado_em = criado_em[:19].replace("T", " ")
        prioridade = str(notificacao.get("prioridade", "baixa") or "baixa").upper()
        acao = notificacao.get("acao") or "Sem acao direta"

        self.detail_status_chip.setText(status)
        self.detail_type_chip.setText(tipo)
        self.detail_title.setText(notificacao.get("titulo") or "Notificacao sem titulo")
        self.detail_message.setText(notificacao.get("mensagem") or "Sem mensagem.")
        self.detail_info.setText(
            f"Prioridade: {prioridade}\n"
            f"Criada em: {criado_em or 'Sem data'}"
        )
        self.btn_abrir_acao.setEnabled(bool(notificacao.get("acao")))
        self.btn_marcar_item.setEnabled(notificacao.get("status") != "lida")
        self.btn_excluir_item.setEnabled(True)
        self._apply_detail_chip_styles()

    def carregar_notificacoes(self):
        try:
            notificacoes = api_client.listar_notificacoes(limit=100)
            notificacoes.sort(key=lambda x: x.get("criado_em", ""), reverse=True)
            self.notificacoes_originais = notificacoes
            self._popular_filtro_tipo()
            self.filtrar_notificacoes()
            self.atualizar_badge()
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
        tipo_filtro = filter_value(self.filtro_tipo.currentText())
        busca = (self.campo_busca.text() or "").strip().lower()

        filtradas = []
        for notif in self.notificacoes_originais:
            status = notif.get("status", "")
            prioridade = notif.get("prioridade", "")
            tipo_label = self._label_tipo(notif.get("tipo"))

            if not is_all_option(status_filtro):
                if status_filtro == "nao lidas" and status != "nao_lida":
                    continue
                if status_filtro == "lidas" and status != "lida":
                    continue
                if status_filtro == "ignoradas" and status != "ignorada":
                    continue

            if not is_all_option(prioridade_filtro) and prioridade != prioridade_filtro:
                continue

            if not is_all_option(tipo_filtro) and tipo_label.lower() != tipo_filtro:
                continue

            if busca:
                alvo_busca = " ".join(
                    [
                        str(notif.get("titulo", "") or ""),
                        str(notif.get("mensagem", "") or ""),
                        str(notif.get("tipo", "") or ""),
                        str(tipo_label or ""),
                        str(notif.get("acao", "") or ""),
                    ]
                ).lower()
                if busca not in alvo_busca:
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
        texto_padrao = QColor("#e2e8f0" if dark else "#1e293b")

        for row, notif in enumerate(notificacoes):
            prioridade = notif.get("prioridade", "baixa")
            status = notif.get("status", "nao_lida")
            cor = prioridade_cores.get(prioridade, prioridade_cores["baixa"])

            prioridade_widget = QFrame()
            prioridade_widget.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {cor['bg']};
                    border-radius: 18px;
                }}
                QLabel {{
                    color: {cor['color']};
                    font-weight: 700;
                    font-size: 11px;
                    background: transparent;
                }}
                """
            )
            prioridade_layout = QHBoxLayout(prioridade_widget)
            prioridade_layout.setContentsMargins(8, 6, 8, 6)
            prioridade_layout.setAlignment(Qt.AlignCenter)
            prioridade_label = QLabel(cor["label"])
            prioridade_layout.addWidget(prioridade_label)
            self.tabela.setCellWidget(row, 0, prioridade_widget)

            tipo_widget = QFrame()
            tipo_widget.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {'#10243f' if dark else '#dbeafe'};
                    border-radius: 18px;
                }}
                QLabel {{
                    color: {'#93c5fd' if dark else '#1d4ed8'};
                    font-weight: 700;
                    font-size: 11px;
                    background: transparent;
                }}
                """
            )
            tipo_layout = QHBoxLayout(tipo_widget)
            tipo_layout.setContentsMargins(8, 6, 8, 6)
            tipo_layout.setAlignment(Qt.AlignCenter)
            tipo_label = QLabel(self._label_tipo(notif.get("tipo")))
            tipo_layout.addWidget(tipo_label)
            self.tabela.setCellWidget(row, 1, tipo_widget)

            titulo = notif.get("titulo", "")
            if status == "nao_lida":
                titulo = f"* {titulo}"
            titulo_item = QTableWidgetItem(titulo)
            titulo_item.setForeground(titulo_nao_lido if status == "nao_lida" else titulo_lido)
            if status == "nao_lida":
                font = QFont()
                font.setBold(True)
                titulo_item.setFont(font)
            self.tabela.setItem(row, 2, titulo_item)

            mensagem = notif.get("mensagem", "")
            mensagem_item = QTableWidgetItem(mensagem)
            mensagem_item.setToolTip(mensagem)
            mensagem_item.setForeground(texto_padrao)
            self.tabela.setItem(row, 3, mensagem_item)

            data = str(notif.get("criado_em", "") or "")
            if data:
                data = data[:16].replace("T", " ")
            data_item = QTableWidgetItem(data)
            data_item.setForeground(data_color)
            self.tabela.setItem(row, 4, data_item)

        self.tabela.resizeRowsToContents()
        self.tabela.clearSelection()
        self.tabela.setCurrentCell(-1, -1)
        self.tabela.clearFocus()
        self.notificacoes_atuais = notificacoes
        self._resetar_detalhes()
        self._atualizar_estado_selecao()

    def obter_notificacao_selecionada(self):
        indices = sorted({index.row() for index in self.tabela.selectionModel().selectedRows()})
        if indices:
            row = indices[0]
            if 0 <= row < len(self.notificacoes_atuais):
                return self.notificacoes_atuais[row]

        current_row = self.tabela.currentRow()
        if 0 <= current_row < len(self.notificacoes_atuais):
            return self.notificacoes_atuais[current_row]
        return None

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
            self._atualizar_detalhes(self.obter_notificacao_selecionada())
            return

        sufixo = "notificacao" if quantidade == 1 else "notificacoes"
        self.btn_marcar.setText(f"Marcar {quantidade} {sufixo}")
        self.btn_excluir.setText(f"Excluir {quantidade} {sufixo}")
        self.lbl_info.setText(f"{quantidade} selecionada(s) | {total} exibidas | {nao_lidas} nao lidas")
        self._atualizar_detalhes(self.obter_notificacao_selecionada())

    def selecionar_todas(self):
        if self.tabela.rowCount() <= 0:
            notification_manager.info("Nao ha notificacoes para selecionar.", self, 2000)
            return
        self.tabela.selectAll()
        self._atualizar_estado_selecao()

    def limpar_lidas(self):
        lidas = [n for n in self.notificacoes_atuais if n.get("status") == "lida"]
        if not lidas:
            notification_manager.info("Nao ha notificacoes lidas para limpar.", self, 2200)
            return

        confirm = QMessageBox.question(
            self,
            "Limpar lidas",
            f"Deseja excluir {len(lidas)} notificacao(oes) lida(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            sucesso = True
            for notificacao in lidas:
                if not api_client.deletar_notificacao(notificacao.get("id")):
                    sucesso = False
            if sucesso:
                notification_manager.success("Notificacoes lidas removidas!", self, 2200)
                self.carregar_notificacoes()
            else:
                notification_manager.error("Nem todas as notificacoes lidas puderam ser removidas.", self, 3000)
        except Exception as e:
            print(f"Erro ao limpar notificacoes lidas: {e}")

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
        if confirm != QMessageBox.Yes:
            return

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
        if confirm != QMessageBox.Yes:
            return

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

    def abrir_notificacao_atual(self):
        notificacao = self.obter_notificacao_selecionada()
        if not notificacao:
            notification_manager.warning("Selecione uma notificacao.", self, 2000)
            return
        self.executar_acao(notificacao)

    def marcar_notificacao_atual(self):
        notificacao = self.obter_notificacao_selecionada()
        if not notificacao:
            notification_manager.warning("Selecione uma notificacao.", self, 2000)
            return

        row = self.notificacoes_atuais.index(notificacao)
        self.tabela.clearSelection()
        self.tabela.selectRow(row)
        self.marcar_selecionadas_como_lidas()

    def excluir_notificacao_atual(self):
        notificacao = self.obter_notificacao_selecionada()
        if not notificacao:
            notification_manager.warning("Selecione uma notificacao.", self, 2000)
            return

        row = self.notificacoes_atuais.index(notificacao)
        self.tabela.clearSelection()
        self.tabela.selectRow(row)
        self.excluir_selecionadas()

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
