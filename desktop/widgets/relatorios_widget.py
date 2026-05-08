from datetime import date, datetime
import os

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from access_control import get_action_label, has_action_access
from api_client import api_client
from widgets.filter_utils import filter_value, is_all_option
from widgets.table_utils import configure_data_table, refresh_data_table_layout


CALENDAR_STYLE = """
    QDateEdit {
        background-color: #ffffff;
        color: #1e293b;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 8px 12px;
        min-height: 32px;
        font-size: 13px;
    }
    QDateEdit::drop-down {
        border: none;
        width: 24px;
    }
    QDateEdit::down-arrow {
        image: none;
    }
"""


class RelatoriosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario = {}
        self._loaded_tabs = {
            "movimentacoes": False,
            "estoque": False,
            "pedidos": False,
            "demandas": False,
        }
        self._summary_labels = {}
        self.init_ui()

    def set_usuario(self, usuario):
        self.usuario = usuario or {}
        self.aplicar_permissoes()

    def _pode(self, action_key):
        return has_action_access(self.usuario, action_key)

    def _avisar_sem_permissao(self, action_key):
        QMessageBox.warning(
            self,
            "Acesso nao permitido",
            f"Voce nao tem permissao para {get_action_label(action_key)}.",
        )

    def on_show(self):
        pass

    def showEvent(self, event):
        self._apply_theme_styles()
        super().showEvent(event)

    def _is_dark_theme(self):
        app = QApplication.instance()
        return str(app.property("accessibility_theme") or "Claro") == "Escuro"

    def _theme_colors(self):
        if self._is_dark_theme():
            return {
                "hero_bg": "rgba(15, 23, 42, 0.55)",
                "hero_border": "rgba(96, 165, 250, 0.18)",
                "card_bg": "rgba(15, 23, 42, 0.34)",
                "card_border": "rgba(148, 163, 184, 0.16)",
                "title": "#f8fafc",
                "muted": "#94a3b8",
            }
        return {
            "hero_bg": "rgba(255, 255, 255, 0.98)",
            "hero_border": "rgba(148, 163, 184, 0.18)",
            "card_bg": "rgba(248, 250, 252, 1.0)",
            "card_border": "rgba(203, 213, 225, 0.9)",
            "title": "#0f172a",
            "muted": "#64748b",
        }

    def _apply_theme_styles(self):
        colors_map = self._theme_colors()
        self.setStyleSheet(
            f"""
            QFrame#reportHeroCard {{
                background-color: {colors_map['hero_bg']};
                border: 1px solid {colors_map['hero_border']};
                border-radius: 20px;
            }}
            QLabel#reportHeroTitle {{
                color: {colors_map['title']};
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#reportHeroSubtitle {{
                color: {colors_map['muted']};
                font-size: 13px;
            }}
            QFrame#reportSummaryCard, QFrame#reportActionsCard {{
                background-color: {colors_map['card_bg']};
                border: 1px solid {colors_map['card_border']};
                border-radius: 16px;
            }}
            QLabel#reportSummaryTitle {{
                color: {colors_map['muted']};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#reportSummaryValue {{
                color: {colors_map['title']};
                font-size: 24px;
                font-weight: 700;
            }}
            QLabel#reportSummaryCaption {{
                color: {colors_map['muted']};
                font-size: 12px;
            }}
            """
        )

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header_card = QFrame()
        header_card.setObjectName("reportHeroCard")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(22, 20, 22, 20)
        header_layout.setSpacing(8)

        title = QLabel("Relatorios do Sistema")
        title.setObjectName("reportHeroTitle")
        header_layout.addWidget(title)

        subtitle = QLabel(
            "Acompanhe movimentacoes, estoque, pedidos e demandas com filtros, resumos visuais e exportacao."
        )
        subtitle.setObjectName("reportHeroSubtitle")
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)
        layout.addWidget(header_card)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("paramTabs")
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.tab_movimentacoes = self.create_tab_movimentacoes()
        self.tabs.addTab(self.tab_movimentacoes, "Movimentacoes")

        self.tab_estoque = self.create_tab_estoque()
        self.tabs.addTab(self.tab_estoque, "Estoque")

        self.tab_pedidos = self.create_tab_pedidos()
        self.tabs.addTab(self.tab_pedidos, "Pedidos")

        self.tab_demandas = self.create_tab_demandas()
        self.tabs.addTab(self.tab_demandas, "Demandas")

        layout.addWidget(self.tabs)
        self.aplicar_permissoes()

    def aplicar_permissoes(self):
        pode_exportar = self._pode("relatorios.export")
        for attr_name in (
            "btn_exportar_excel",
            "btn_exportar_pdf",
            "btn_exportar_excel_estoque",
            "btn_exportar_pdf_estoque",
            "btn_exportar_excel_pedidos",
            "btn_exportar_pdf_pedidos",
            "btn_exportar_excel_demandas",
            "btn_exportar_pdf_demandas",
        ):
            btn = getattr(self, attr_name, None)
            if btn is not None:
                btn.setVisible(pode_exportar)

    def on_tab_changed(self, index):
        tab_text = self.tabs.tabText(index)
        if tab_text == "Movimentacoes" and not self._loaded_tabs["movimentacoes"]:
            self.carregar_movimentacoes()
            self.carregar_empresas_movimentacoes()
            self._loaded_tabs["movimentacoes"] = True
        elif tab_text == "Estoque" and not self._loaded_tabs["estoque"]:
            self.carregar_categorias()
            self.carregar_estoque()
            self._loaded_tabs["estoque"] = True
        elif tab_text == "Pedidos" and not self._loaded_tabs["pedidos"]:
            self.carregar_pedidos()
            self.carregar_empresas_pedidos()
            self._loaded_tabs["pedidos"] = True
        elif tab_text == "Demandas" and not self._loaded_tabs["demandas"]:
            self.carregar_demandas()
            self.carregar_empresas_demandas()
            self._loaded_tabs["demandas"] = True

    def _create_summary_strip(self, key, specs):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        self._summary_labels[key] = {}

        for summary_key, title, caption in specs:
            card = QFrame()
            card.setObjectName("reportSummaryCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(4)

            title_label = QLabel(title)
            title_label.setObjectName("reportSummaryTitle")
            card_layout.addWidget(title_label)

            value_label = QLabel("--")
            value_label.setObjectName("reportSummaryValue")
            card_layout.addWidget(value_label)

            caption_label = QLabel(caption)
            caption_label.setObjectName("reportSummaryCaption")
            caption_label.setWordWrap(True)
            card_layout.addWidget(caption_label)

            layout.addWidget(card, 1)
            self._summary_labels[key][summary_key] = value_label

        return container

    def _create_actions_card(self, primary_button, export_buttons):
        card = QFrame()
        card.setObjectName("reportActionsCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        layout.addWidget(primary_button)
        layout.addStretch()
        for button in export_buttons:
            layout.addWidget(button)
        return card

    def _set_summary_value(self, group, key, value):
        label = self._summary_labels.get(group, {}).get(key)
        if label is not None:
            label.setText(str(value))

    def _build_table(self, headers, stretch_columns, minimum_widths):
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        table.setStyleSheet(
            """
            QTableWidget::item { padding: 10px 8px; }
            QHeaderView::section { padding: 10px 12px; }
            """
        )
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        configure_data_table(
            table,
            stretch_columns=stretch_columns,
            minimum_section_size=88,
            minimum_widths=minimum_widths,
        )
        return table

    def create_tab_movimentacoes(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.addWidget(
            self._create_summary_strip(
                "movimentacoes",
                (
                    ("total", "Movimentacoes", "Registros encontrados"),
                    ("entradas", "Entradas", "Fluxo de entrada"),
                    ("saidas", "Saidas", "Fluxo de saida"),
                ),
            )
        )

        filtros = QGroupBox("Filtros")
        filtros.setObjectName("configGroup")
        filtros_layout = QHBoxLayout(filtros)
        filtros_layout.setContentsMargins(20, 15, 20, 15)
        filtros_layout.addWidget(QLabel("Data Inicio:"))
        self.mov_data_inicio = self._create_date_edit(QDate.currentDate().addMonths(-1))
        filtros_layout.addWidget(self.mov_data_inicio)
        filtros_layout.addWidget(QLabel("Data Fim:"))
        self.mov_data_fim = self._create_date_edit(QDate.currentDate())
        filtros_layout.addWidget(self.mov_data_fim)
        filtros_layout.addWidget(QLabel("Tipo:"))
        self.mov_tipo = QComboBox()
        self.mov_tipo.addItems(["Todos", "Entrada", "Saida"])
        self.mov_tipo.setObjectName("configCombo")
        filtros_layout.addWidget(self.mov_tipo)
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.mov_empresa = QComboBox()
        self.mov_empresa.addItems(["Todas"])
        self.mov_empresa.setObjectName("configCombo")
        filtros_layout.addWidget(self.mov_empresa)
        filtros_layout.addStretch()
        layout.addWidget(filtros)

        self.btn_atualizar = QPushButton("Atualizar dados")
        self.btn_atualizar.setObjectName("btnPrimary")
        self.btn_atualizar.clicked.connect(self.atualizar_movimentacoes)
        self.btn_exportar_excel = QPushButton("Exportar Excel")
        self.btn_exportar_excel.setObjectName("btnSecondary")
        self.btn_exportar_excel.clicked.connect(lambda: self.exportar_excel("movimentacoes"))
        self.btn_exportar_pdf = QPushButton("Exportar PDF")
        self.btn_exportar_pdf.setObjectName("btnSecondary")
        self.btn_exportar_pdf.clicked.connect(lambda: self.exportar_pdf("movimentacoes"))
        layout.addWidget(self._create_actions_card(self.btn_atualizar, (self.btn_exportar_excel, self.btn_exportar_pdf)))

        self.mov_tabela = self._build_table(
            ["ID", "Material", "Tipo", "Quantidade", "Empresa", "Destinatario", "Data/Hora", "Usuario", "Observacao"],
            stretch_columns=(1, 8),
            minimum_widths={0: 72, 1: 220, 2: 110, 3: 100, 4: 170, 5: 180, 6: 155, 7: 160, 8: 240},
        )
        layout.addWidget(self.mov_tabela)

        self.mov_progress = QProgressBar()
        self.mov_progress.setVisible(False)
        layout.addWidget(self.mov_progress)
        return widget

    def create_tab_estoque(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.addWidget(
            self._create_summary_strip(
                "estoque",
                (
                    ("total", "Itens", "Materiais listados"),
                    ("ativos", "Ativos", "Disponiveis no estoque"),
                    ("criticos", "Criticos", "Quantidade baixa ou zerada"),
                ),
            )
        )

        filtros = QGroupBox("Filtros")
        filtros.setObjectName("configGroup")
        filtros_layout = QHBoxLayout(filtros)
        filtros_layout.setContentsMargins(20, 15, 20, 15)
        filtros_layout.addWidget(QLabel("Categoria:"))
        self.est_categoria = QComboBox()
        self.est_categoria.addItems(["Todas"])
        self.est_categoria.setObjectName("configCombo")
        filtros_layout.addWidget(self.est_categoria)
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.est_empresa = QComboBox()
        self.est_empresa.addItems(["Todas"])
        self.est_empresa.setObjectName("configCombo")
        filtros_layout.addWidget(self.est_empresa)
        filtros_layout.addWidget(QLabel("Status:"))
        self.est_status = QComboBox()
        self.est_status.addItems(["Todos", "Ativo", "Inativo", "Descontinuado"])
        self.est_status.setObjectName("configCombo")
        filtros_layout.addWidget(self.est_status)
        filtros_layout.addStretch()
        layout.addWidget(filtros)

        self.btn_carregar_estoque = QPushButton("Atualizar dados")
        self.btn_carregar_estoque.setObjectName("btnPrimary")
        self.btn_carregar_estoque.clicked.connect(self.atualizar_estoque)
        self.btn_exportar_excel_estoque = QPushButton("Exportar Excel")
        self.btn_exportar_excel_estoque.setObjectName("btnSecondary")
        self.btn_exportar_excel_estoque.clicked.connect(lambda: self.exportar_excel("estoque"))
        self.btn_exportar_pdf_estoque = QPushButton("Exportar PDF")
        self.btn_exportar_pdf_estoque.setObjectName("btnSecondary")
        self.btn_exportar_pdf_estoque.clicked.connect(lambda: self.exportar_pdf("estoque"))
        layout.addWidget(
            self._create_actions_card(
                self.btn_carregar_estoque,
                (self.btn_exportar_excel_estoque, self.btn_exportar_pdf_estoque),
            )
        )

        self.est_tabela = self._build_table(
            ["ID", "Nome", "Descricao", "Quantidade", "Categoria", "Empresa", "Status"],
            stretch_columns=(1, 2),
            minimum_widths={0: 72, 1: 220, 2: 280, 3: 100, 4: 160, 5: 180, 6: 120},
        )
        layout.addWidget(self.est_tabela)
        return widget

    def create_tab_pedidos(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.addWidget(
            self._create_summary_strip(
                "pedidos",
                (
                    ("total", "Pedidos", "Solicitacoes no periodo"),
                    ("pendentes", "Pendentes", "Aguardando tratativa"),
                    ("concluidos", "Concluidos", "Pedidos finalizados"),
                ),
            )
        )

        filtros = QGroupBox("Filtros")
        filtros.setObjectName("configGroup")
        filtros_layout = QHBoxLayout(filtros)
        filtros_layout.setContentsMargins(20, 15, 20, 15)
        filtros_layout.addWidget(QLabel("Data Inicio:"))
        self.ped_data_inicio = self._create_date_edit(QDate.currentDate().addMonths(-1))
        filtros_layout.addWidget(self.ped_data_inicio)
        filtros_layout.addWidget(QLabel("Data Fim:"))
        self.ped_data_fim = self._create_date_edit(QDate.currentDate())
        filtros_layout.addWidget(self.ped_data_fim)
        filtros_layout.addWidget(QLabel("Status:"))
        self.ped_status = QComboBox()
        self.ped_status.addItems(["Todos", "Pendente", "Aprovado", "Concluido", "Cancelado"])
        self.ped_status.setObjectName("configCombo")
        filtros_layout.addWidget(self.ped_status)
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.ped_empresa = QComboBox()
        self.ped_empresa.addItems(["Todas"])
        self.ped_empresa.setObjectName("configCombo")
        filtros_layout.addWidget(self.ped_empresa)
        filtros_layout.addStretch()
        layout.addWidget(filtros)

        self.btn_carregar_pedidos = QPushButton("Atualizar dados")
        self.btn_carregar_pedidos.setObjectName("btnPrimary")
        self.btn_carregar_pedidos.clicked.connect(self.atualizar_pedidos)
        self.btn_exportar_excel_pedidos = QPushButton("Exportar Excel")
        self.btn_exportar_excel_pedidos.setObjectName("btnSecondary")
        self.btn_exportar_excel_pedidos.clicked.connect(lambda: self.exportar_excel("pedidos"))
        self.btn_exportar_pdf_pedidos = QPushButton("Exportar PDF")
        self.btn_exportar_pdf_pedidos.setObjectName("btnSecondary")
        self.btn_exportar_pdf_pedidos.clicked.connect(lambda: self.exportar_pdf("pedidos"))
        layout.addWidget(
            self._create_actions_card(
                self.btn_carregar_pedidos,
                (self.btn_exportar_excel_pedidos, self.btn_exportar_pdf_pedidos),
            )
        )

        self.ped_tabela = self._build_table(
            ["ID", "Material", "Qtd", "Solicitante", "Empresa", "Data Solic.", "Data Conclusao", "Status"],
            stretch_columns=(1,),
            minimum_widths={0: 72, 1: 220, 2: 90, 3: 170, 4: 170, 5: 135, 6: 150, 7: 120},
        )
        layout.addWidget(self.ped_tabela)
        return widget

    def create_tab_demandas(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.addWidget(
            self._create_summary_strip(
                "demandas",
                (
                    ("total", "Demandas", "Chamados no periodo"),
                    ("abertas", "Abertas", "Aguardando tratativa"),
                    ("concluidas", "Concluidas", "Demandas resolvidas"),
                ),
            )
        )

        filtros = QGroupBox("Filtros")
        filtros.setObjectName("configGroup")
        filtros_layout = QHBoxLayout(filtros)
        filtros_layout.setContentsMargins(20, 15, 20, 15)
        filtros_layout.addWidget(QLabel("Data Inicio:"))
        self.dem_data_inicio = self._create_date_edit(QDate.currentDate().addMonths(-1))
        filtros_layout.addWidget(self.dem_data_inicio)
        filtros_layout.addWidget(QLabel("Data Fim:"))
        self.dem_data_fim = self._create_date_edit(QDate.currentDate())
        filtros_layout.addWidget(self.dem_data_fim)
        filtros_layout.addWidget(QLabel("Status:"))
        self.dem_status = QComboBox()
        self.dem_status.addItems(["Todos", "Aberto", "Em Andamento", "Concluido", "Cancelado"])
        self.dem_status.setObjectName("configCombo")
        filtros_layout.addWidget(self.dem_status)
        filtros_layout.addWidget(QLabel("Prioridade:"))
        self.dem_prioridade = QComboBox()
        self.dem_prioridade.addItems(["Todas", "Alta", "Media", "Baixa"])
        self.dem_prioridade.setObjectName("configCombo")
        filtros_layout.addWidget(self.dem_prioridade)
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.dem_empresa = QComboBox()
        self.dem_empresa.addItems(["Todas"])
        self.dem_empresa.setObjectName("configCombo")
        filtros_layout.addWidget(self.dem_empresa)
        filtros_layout.addStretch()
        layout.addWidget(filtros)

        self.btn_carregar_demandas = QPushButton("Atualizar dados")
        self.btn_carregar_demandas.setObjectName("btnPrimary")
        self.btn_carregar_demandas.clicked.connect(self.atualizar_demandas)
        self.btn_exportar_excel_demandas = QPushButton("Exportar Excel")
        self.btn_exportar_excel_demandas.setObjectName("btnSecondary")
        self.btn_exportar_excel_demandas.clicked.connect(lambda: self.exportar_excel("demandas"))
        self.btn_exportar_pdf_demandas = QPushButton("Exportar PDF")
        self.btn_exportar_pdf_demandas.setObjectName("btnSecondary")
        self.btn_exportar_pdf_demandas.clicked.connect(lambda: self.exportar_pdf("demandas"))
        layout.addWidget(
            self._create_actions_card(
                self.btn_carregar_demandas,
                (self.btn_exportar_excel_demandas, self.btn_exportar_pdf_demandas),
            )
        )

        self.dem_tabela = self._build_table(
            ["ID", "Titulo", "Solicitante", "Prioridade", "Status", "Data Abertura", "Responsavel"],
            stretch_columns=(1,),
            minimum_widths={0: 72, 1: 240, 2: 160, 3: 130, 4: 130, 5: 155, 6: 170},
        )
        layout.addWidget(self.dem_tabela)
        return widget

    def _create_date_edit(self, value):
        widget = QDateEdit()
        widget.setDate(value)
        widget.setCalendarPopup(True)
        widget.setStyleSheet(CALENDAR_STYLE)
        return widget

    def carregar_empresas_movimentacoes(self):
        self._load_empresas_combo(self.mov_empresa)

    def carregar_empresas_pedidos(self):
        self._load_empresas_combo(self.ped_empresa)

    def carregar_empresas_demandas(self):
        self._load_empresas_combo(self.dem_empresa)

    def _load_empresas_combo(self, combo):
        try:
            empresas = api_client.get_empresas()
            combo.clear()
            combo.addItem("Todas")
            for empresa in empresas:
                if empresa and str(empresa).strip():
                    combo.addItem(str(empresa))
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")

    def carregar_categorias(self):
        try:
            categorias = api_client.listar_categorias()
            self.est_categoria.clear()
            self.est_categoria.addItem("Todas")
            for categoria in categorias:
                self.est_categoria.addItem(categoria)
            self._load_empresas_combo(self.est_empresa)
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")

    def _date_edit_to_date(self, widget):
        return widget.date().toPython()

    def _parse_datetime(self, value):
        if not value:
            return None
        raw = str(value).strip()
        if not raw:
            return None
        cleaned = raw.replace("T", " ")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(cleaned[: len(fmt)], fmt)
            except Exception:
                continue
        return None

    def _passes_period(self, raw_value, start_date, end_date):
        parsed = self._parse_datetime(raw_value)
        if parsed is None:
            return True
        current = parsed.date()
        return start_date <= current <= end_date

    def carregar_movimentacoes(self):
        try:
            self.atualizar_movimentacoes()
        except Exception as e:
            print(f"Erro ao carregar movimentacoes: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar movimentacoes: {e}")

    def atualizar_movimentacoes(self):
        try:
            movimentacoes = api_client.listar_movimentacoes()
            start_date = self._date_edit_to_date(self.mov_data_inicio)
            end_date = self._date_edit_to_date(self.mov_data_fim)
            tipo = filter_value(self.mov_tipo.currentText())
            empresa = None if is_all_option(self.mov_empresa.currentText()) else self.mov_empresa.currentText()

            filtradas = []
            for item in movimentacoes:
                if not self._passes_period(item.get("data_hora"), start_date, end_date):
                    continue
                if not is_all_option(tipo) and str(item.get("tipo", "")).lower() != tipo:
                    continue
                if empresa and item.get("empresa") != empresa:
                    continue
                filtradas.append(item)

            filtradas.sort(key=lambda x: x.get("data_hora", ""), reverse=True)
            self.atualizar_tabela_movimentacoes(filtradas)
        except Exception as e:
            print(f"Erro ao atualizar movimentacoes: {e}")

    def atualizar_tabela_movimentacoes(self, movimentacoes):
        self.mov_tabela.setRowCount(len(movimentacoes))
        entradas = 0
        saidas = 0

        for row, mov in enumerate(movimentacoes):
            self.mov_tabela.setItem(row, 0, QTableWidgetItem(str(mov.get("id", ""))))
            self.mov_tabela.setItem(row, 1, QTableWidgetItem(mov.get("material_nome", "-")))

            tipo = str(mov.get("tipo", "") or "")
            tipo_item = QTableWidgetItem(tipo.upper())
            if tipo == "entrada":
                entradas += 1
                tipo_item.setForeground(QColor(42, 157, 143))
            else:
                if tipo:
                    saidas += 1
                tipo_item.setForeground(QColor(231, 111, 81))
            self.mov_tabela.setItem(row, 2, tipo_item)

            self.mov_tabela.setItem(row, 3, QTableWidgetItem(str(mov.get("quantidade", 0))))
            self.mov_tabela.setItem(row, 4, QTableWidgetItem(mov.get("empresa", "-")))
            self.mov_tabela.setItem(row, 5, QTableWidgetItem(mov.get("destinatario", "-")))

            data = str(mov.get("data_hora", "") or "")
            if data:
                data = data[:16].replace("T", " ")
            self.mov_tabela.setItem(row, 6, QTableWidgetItem(data))
            self.mov_tabela.setItem(row, 7, QTableWidgetItem(mov.get("usuario_nome", "-")))

            obs = mov.get("observacao")
            self.mov_tabela.setItem(row, 8, QTableWidgetItem("-" if obs is None else str(obs)[:50]))

        refresh_data_table_layout(self.mov_tabela)
        self._set_summary_value("movimentacoes", "total", len(movimentacoes))
        self._set_summary_value("movimentacoes", "entradas", entradas)
        self._set_summary_value("movimentacoes", "saidas", saidas)

    def carregar_estoque(self):
        try:
            self.atualizar_estoque()
        except Exception as e:
            print(f"Erro ao carregar estoque: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar estoque: {e}")

    def atualizar_estoque(self):
        try:
            categoria = None if is_all_option(self.est_categoria.currentText()) else self.est_categoria.currentText()
            empresa = None if is_all_option(self.est_empresa.currentText()) else self.est_empresa.currentText()
            status = "" if is_all_option(self.est_status.currentText()) else filter_value(self.est_status.currentText())
            materiais = api_client.listar_materiais(categoria=categoria, empresa=empresa, status=status)
            materiais.sort(key=lambda x: str(x.get("nome", "")).lower())
            self.atualizar_tabela_estoque(materiais)
        except Exception as e:
            print(f"Erro ao atualizar estoque: {e}")

    def atualizar_tabela_estoque(self, materiais):
        self.est_tabela.setRowCount(len(materiais))
        ativos = 0
        criticos = 0

        for row, mat in enumerate(materiais):
            quantidade = int(mat.get("quantidade", 0) or 0)
            status = str(mat.get("status", "ativo") or "ativo")
            if status == "ativo":
                ativos += 1
            if quantidade <= 2:
                criticos += 1

            self.est_tabela.setItem(row, 0, QTableWidgetItem(str(mat.get("id", ""))))
            self.est_tabela.setItem(row, 1, QTableWidgetItem(mat.get("nome", "")))
            self.est_tabela.setItem(row, 2, QTableWidgetItem(str(mat.get("descricao", "") or "")[:60]))
            self.est_tabela.setItem(row, 3, QTableWidgetItem(str(quantidade)))
            self.est_tabela.setItem(row, 4, QTableWidgetItem(mat.get("categoria", "-")))
            self.est_tabela.setItem(row, 5, QTableWidgetItem(mat.get("empresa", "-")))

            status_item = QTableWidgetItem(status.upper())
            status_item.setForeground(QColor(42, 157, 143) if status == "ativo" else QColor(231, 111, 81))
            self.est_tabela.setItem(row, 6, status_item)

        refresh_data_table_layout(self.est_tabela)
        self._set_summary_value("estoque", "total", len(materiais))
        self._set_summary_value("estoque", "ativos", ativos)
        self._set_summary_value("estoque", "criticos", criticos)

    def carregar_pedidos(self):
        try:
            self.atualizar_pedidos()
        except Exception as e:
            print(f"Erro ao carregar pedidos: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar pedidos: {e}")

    def atualizar_pedidos(self):
        try:
            status = None if is_all_option(self.ped_status.currentText()) else filter_value(self.ped_status.currentText())
            empresa = None if is_all_option(self.ped_empresa.currentText()) else self.ped_empresa.currentText()
            pedidos = api_client.listar_pedidos(status=status, empresa=empresa)

            start_date = self._date_edit_to_date(self.ped_data_inicio)
            end_date = self._date_edit_to_date(self.ped_data_fim)
            filtrados = [p for p in pedidos if self._passes_period(p.get("data_solicitacao"), start_date, end_date)]
            filtrados.sort(key=lambda x: x.get("data_solicitacao", ""), reverse=True)
            self.atualizar_tabela_pedidos(filtrados)
        except Exception as e:
            print(f"Erro ao atualizar pedidos: {e}")

    def atualizar_tabela_pedidos(self, pedidos):
        self.ped_tabela.setRowCount(len(pedidos))
        pendentes = 0
        concluidos = 0
        status_cores = {
            "pendente": QColor(244, 162, 97),
            "aprovado": QColor(42, 157, 143),
            "concluido": QColor(44, 125, 160),
            "cancelado": QColor(231, 111, 81),
        }

        for row, ped in enumerate(pedidos):
            status = str(ped.get("status", "pendente") or "pendente")
            if status == "pendente":
                pendentes += 1
            if status == "concluido":
                concluidos += 1

            self.ped_tabela.setItem(row, 0, QTableWidgetItem(str(ped.get("id", ""))))
            self.ped_tabela.setItem(row, 1, QTableWidgetItem(ped.get("material_nome", "-")))
            self.ped_tabela.setItem(row, 2, QTableWidgetItem(str(ped.get("quantidade", 0))))
            self.ped_tabela.setItem(row, 3, QTableWidgetItem(ped.get("solicitante", "-")))
            self.ped_tabela.setItem(row, 4, QTableWidgetItem(ped.get("empresa", "-")))
            self.ped_tabela.setItem(row, 5, QTableWidgetItem(ped.get("data_solicitacao", "-")))
            self.ped_tabela.setItem(row, 6, QTableWidgetItem(ped.get("data_conclusao", "-") or "-"))

            status_item = QTableWidgetItem(status.upper())
            status_item.setForeground(status_cores.get(status, QColor(0, 0, 0)))
            self.ped_tabela.setItem(row, 7, status_item)

        refresh_data_table_layout(self.ped_tabela)
        self._set_summary_value("pedidos", "total", len(pedidos))
        self._set_summary_value("pedidos", "pendentes", pendentes)
        self._set_summary_value("pedidos", "concluidos", concluidos)

    def carregar_demandas(self):
        try:
            self.atualizar_demandas()
        except Exception as e:
            print(f"Erro ao carregar demandas: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar demandas: {e}")

    def atualizar_demandas(self):
        try:
            status = None if is_all_option(self.dem_status.currentText()) else filter_value(self.dem_status.currentText())
            prioridade = None if is_all_option(self.dem_prioridade.currentText()) else filter_value(self.dem_prioridade.currentText())
            empresa = None if is_all_option(self.dem_empresa.currentText()) else self.dem_empresa.currentText()
            demandas = api_client.listar_demandas(status=status, prioridade=prioridade, empresa=empresa)

            start_date = self._date_edit_to_date(self.dem_data_inicio)
            end_date = self._date_edit_to_date(self.dem_data_fim)
            filtradas = [d for d in demandas if self._passes_period(d.get("data_abertura"), start_date, end_date)]
            filtradas.sort(key=lambda x: x.get("data_abertura", ""), reverse=True)
            self.atualizar_tabela_demandas(filtradas)
        except Exception as e:
            print(f"Erro ao atualizar demandas: {e}")

    def atualizar_tabela_demandas(self, demandas):
        self.dem_tabela.setRowCount(len(demandas))
        abertas = 0
        concluidas = 0
        prioridade_cores = {
            "alta": QColor(231, 111, 81),
            "media": QColor(244, 162, 97),
            "baixa": QColor(42, 157, 143),
        }

        for row, dem in enumerate(demandas):
            status = str(dem.get("status", "aberto") or "aberto")
            prioridade = str(dem.get("prioridade", "media") or "media")
            if status in {"aberto", "em_andamento"}:
                abertas += 1
            if status == "concluido":
                concluidas += 1

            self.dem_tabela.setItem(row, 0, QTableWidgetItem(str(dem.get("id", ""))))
            self.dem_tabela.setItem(row, 1, QTableWidgetItem(str(dem.get("titulo", "") or "")[:60]))
            self.dem_tabela.setItem(row, 2, QTableWidgetItem(dem.get("solicitante", "-")))

            prioridade_item = QTableWidgetItem(prioridade.upper())
            prioridade_item.setForeground(prioridade_cores.get(prioridade, QColor(0, 0, 0)))
            self.dem_tabela.setItem(row, 3, prioridade_item)

            status_item = QTableWidgetItem(status.upper())
            self.dem_tabela.setItem(row, 4, status_item)

            data = str(dem.get("data_abertura", "") or "")
            if data:
                data = data[:10]
            self.dem_tabela.setItem(row, 5, QTableWidgetItem(data))
            self.dem_tabela.setItem(row, 6, QTableWidgetItem(dem.get("responsavel", "-")))

        refresh_data_table_layout(self.dem_tabela)
        self._set_summary_value("demandas", "total", len(demandas))
        self._set_summary_value("demandas", "abertas", abertas)
        self._set_summary_value("demandas", "concluidas", concluidas)

    def _table_for_tipo(self, tipo):
        mapping = {
            "movimentacoes": self.mov_tabela,
            "estoque": self.est_tabela,
            "pedidos": self.ped_tabela,
            "demandas": self.dem_tabela,
        }
        return mapping.get(tipo)

    def _table_to_rows(self, table):
        headers = []
        for column in range(table.columnCount()):
            item = table.horizontalHeaderItem(column)
            headers.append(item.text() if item else f"Coluna {column + 1}")

        rows = []
        for row in range(table.rowCount()):
            row_values = []
            for column in range(table.columnCount()):
                cell_widget = table.cellWidget(row, column)
                if cell_widget is not None:
                    labels = cell_widget.findChildren(QLabel)
                    if labels:
                        row_values.append(labels[0].text())
                        continue
                item = table.item(row, column)
                row_values.append(item.text() if item else "")
            rows.append(row_values)
        return headers, rows

    def exportar_excel(self, tipo):
        if not self._pode("relatorios.export"):
            self._avisar_sem_permissao("relatorios.export")
            return

        table = self._table_for_tipo(tipo)
        if table is None:
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Excel",
                f"relatorio_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel Files (*.xlsx)",
            )
            if not file_path:
                return

            headers, rows = self._table_to_rows(table)
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = f"Relatorio {tipo.capitalize()}"

            sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(1, len(headers)))
            title_cell = sheet.cell(row=1, column=1)
            title_cell.value = f"Relatorio de {tipo.capitalize()}"
            title_cell.font = Font(name="Arial", size=16, bold=True)
            title_cell.alignment = Alignment(horizontal="center")

            sheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max(1, len(headers)))
            date_cell = sheet.cell(row=2, column=1)
            date_cell.value = f"Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            date_cell.alignment = Alignment(horizontal="center")

            header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
            border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))

            for column, header in enumerate(headers, start=1):
                cell = sheet.cell(row=4, column=column, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = border

            for row_index, row_values in enumerate(rows, start=5):
                for column, value in enumerate(row_values, start=1):
                    cell = sheet.cell(row=row_index, column=column, value=value)
                    cell.alignment = Alignment(vertical="center", wrap_text=True)
                    cell.border = border

            for index, header in enumerate(headers, start=1):
                max_width = max(len(str(header)), *(len(str(row[index - 1])) for row in rows), 12)
                sheet.column_dimensions[get_column_letter(index)].width = min(max_width + 2, 40)

            workbook.save(file_path)
            QMessageBox.information(self, "Sucesso", f"Relatorio exportado com sucesso.\n\nArquivo: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar Excel: {e}")

    def exportar_pdf(self, tipo):
        if not self._pode("relatorios.export"):
            self._avisar_sem_permissao("relatorios.export")
            return

        table_widget = self._table_for_tipo(tipo)
        if table_widget is None:
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar PDF",
                f"relatorio_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)",
            )
            if not file_path:
                return

            headers, rows = self._table_to_rows(table_widget)
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle("ReportTitle", parent=styles["Heading1"], fontSize=18, leading=22, spaceAfter=8)
            meta_style = ParagraphStyle("ReportMeta", parent=styles["BodyText"], fontSize=9, textColor=colors.HexColor("#475569"))
            cell_style = ParagraphStyle("ReportCell", parent=styles["BodyText"], fontSize=8, leading=10)

            elements = [
                Paragraph(f"Relatorio de {tipo.capitalize()}", title_style),
                Paragraph(f"Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", meta_style),
                Spacer(1, 10),
            ]

            data = [[Paragraph(str(header), cell_style) for header in headers]]
            for row_values in rows:
                data.append([Paragraph(str(value), cell_style) for value in row_values])

            table = Table(data, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(table)
            doc.build(elements)
            QMessageBox.information(self, "Sucesso", f"Relatorio exportado com sucesso.\n\nArquivo: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {e}")
