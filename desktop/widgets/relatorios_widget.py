from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QComboBox, QDateEdit, QGroupBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QProgressBar, QFileDialog, QTabWidget,
                               QFrame, QCheckBox)
from PySide6.QtCore import Qt, QDate, QThread, Signal
from PySide6.QtGui import QFont, QColor
from api_client import api_client
from widgets.filter_utils import filter_value, is_all_option
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from datetime import datetime
import os

# Estilo para o calendário
CALENDAR_STYLE = """
    QDateEdit {
        background-color: #ffffff;
        color: #1e293b;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
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
    QCalendarWidget {
        background-color: #ffffff;
    }
    QCalendarWidget QToolButton {
        color: #1e293b;
        background-color: #f1f5f9;
        border: none;
        border-radius: 4px;
        padding: 8px;
        font-weight: bold;
        font-size: 14px;
    }
    QCalendarWidget QToolButton:hover {
        background-color: #e2e8f0;
    }
    QCalendarWidget QMenu {
        background-color: #ffffff;
        color: #1e293b;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 4px;
    }
    QCalendarWidget QMenu::item {
        padding: 6px 20px;
        border-radius: 4px;
    }
    QCalendarWidget QMenu::item:selected {
        background-color: #e6f0ff;
        color: #1e293b;
    }
    QCalendarWidget QWidget {
        alternate-background-color: #2c7da0;
    }
    QCalendarWidget QHeaderView {
        background-color: #2c7da0;
        color: #ffffff;
        font-weight: bold;
        font-size: 12px;
    }
    QCalendarWidget QHeaderView::section {
        background-color: #2c7da0;
        color: #ffffff;
        padding: 8px;
        border: none;
        font-weight: bold;
    }
    QCalendarWidget QAbstractItemView {
        background-color: #ffffff;
        color: #1e293b;
        selection-background-color: #2c7da0;
        selection-color: #ffffff;
        outline: 0;
    }
    QCalendarWidget QAbstractItemView:!enabled {
        color: #cbd5e1;
        background-color: #f8fafc;
    }
    QCalendarWidget QAbstractItemView:selected {
        background-color: #2c7da0;
        color: #ffffff;
        border-radius: 4px;
    }
    QCalendarWidget QAbstractItemView:hover {
        background-color: #e6f0ff;
        border-radius: 4px;
    }
    QCalendarWidget QAbstractItemView#qt_calendar_weekend {
        color: #e76f51;
    }
    QCalendarWidget QHeaderView::section:horizontal {
        color: #ffffff;
    }
"""


class RelatoriosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._loaded_tabs = {
            'movimentacoes': False,
            'estoque': False,
            'pedidos': False,
            'demandas': False
        }  # ✅ Controle de carregamento por aba
        self.init_ui()
        # ⚠️ NÃO carregar dados aqui - será feito no on_show() ou quando cada aba for ativada

    def on_show(self):
        """✅ Chamado quando a aba principal do relatório é selecionada"""
        # Aqui não carregamos nada automaticamente porque o relatório tem abas internas
        # Cada aba carregará seus dados quando for selecionada pela primeira vez
        pass

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Título
        titulo = QLabel("📊 Relatórios do Sistema")
        titulo.setProperty("class", "page-title")
        layout.addWidget(titulo)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("paramTabs")
        self.tabs.currentChanged.connect(self.on_tab_changed)  # ✅ Conectar evento de mudança de aba

        # Abas
        self.tab_movimentacoes = self.create_tab_movimentacoes()
        self.tabs.addTab(self.tab_movimentacoes, "📊 Movimentações")

        self.tab_estoque = self.create_tab_estoque()
        self.tabs.addTab(self.tab_estoque, "📦 Estoque")

        self.tab_pedidos = self.create_tab_pedidos()
        self.tabs.addTab(self.tab_pedidos, "📋 Pedidos")

        self.tab_demandas = self.create_tab_demandas()
        self.tabs.addTab(self.tab_demandas, "🎫 Demandas")

        layout.addWidget(self.tabs)

    def on_tab_changed(self, index):
        """✅ Carrega dados da aba quando ela é selecionada pela primeira vez"""
        tab_text = self.tabs.tabText(index)

        if tab_text == "📊 Movimentações" and not self._loaded_tabs['movimentacoes']:
            self.carregar_movimentacoes()
            self.carregar_empresas_movimentacoes()  # Carregar empresas para o filtro
            self._loaded_tabs['movimentacoes'] = True

        elif tab_text == "📦 Estoque" and not self._loaded_tabs['estoque']:
            self.carregar_categorias()
            self.carregar_estoque()
            self._loaded_tabs['estoque'] = True

        elif tab_text == "📋 Pedidos" and not self._loaded_tabs['pedidos']:
            self.carregar_pedidos()
            self.carregar_empresas_pedidos()
            self._loaded_tabs['pedidos'] = True

        elif tab_text == "🎫 Demandas" and not self._loaded_tabs['demandas']:
            self.carregar_demandas()
            self._loaded_tabs['demandas'] = True

    def create_tab_movimentacoes(self):
        """Aba de relatório de movimentações"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Filtros
        filtros = QGroupBox("Filtros")
        filtros.setObjectName("configGroup")
        filtros_layout = QHBoxLayout(filtros)
        filtros_layout.setContentsMargins(20, 15, 20, 15)

        # Período
        filtros_layout.addWidget(QLabel("Data Início:"))
        self.mov_data_inicio = QDateEdit()
        self.mov_data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.mov_data_inicio.setCalendarPopup(True)
        self.mov_data_inicio.setStyleSheet(CALENDAR_STYLE)
        filtros_layout.addWidget(self.mov_data_inicio)

        filtros_layout.addWidget(QLabel("Data Fim:"))
        self.mov_data_fim = QDateEdit()
        self.mov_data_fim.setDate(QDate.currentDate())
        self.mov_data_fim.setCalendarPopup(True)
        self.mov_data_fim.setStyleSheet(CALENDAR_STYLE)
        filtros_layout.addWidget(self.mov_data_fim)

        # Tipo
        filtros_layout.addWidget(QLabel("Tipo:"))
        self.mov_tipo = QComboBox()
        self.mov_tipo.addItems(["Todos", "Entrada", "Saída"])
        self.mov_tipo.setObjectName("configCombo")
        filtros_layout.addWidget(self.mov_tipo)

        # Empresa
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.mov_empresa = QComboBox()
        self.mov_empresa.addItems(["Todas"])
        self.mov_empresa.setObjectName("configCombo")
        filtros_layout.addWidget(self.mov_empresa)

        filtros_layout.addStretch()

        layout.addWidget(filtros)

        # Botões de ação
        btn_layout = QHBoxLayout()

        self.btn_atualizar = QPushButton("🔍 Atualizar")
        self.btn_atualizar.setObjectName("btnPrimary")
        self.btn_atualizar.clicked.connect(self.atualizar_movimentacoes)
        btn_layout.addWidget(self.btn_atualizar)

        btn_layout.addStretch()

        self.btn_exportar_excel = QPushButton("📊 Exportar Excel")
        self.btn_exportar_excel.setObjectName("btnSecondary")
        self.btn_exportar_excel.clicked.connect(lambda: self.exportar_excel("movimentacoes"))
        btn_layout.addWidget(self.btn_exportar_excel)

        self.btn_exportar_pdf = QPushButton("📄 Exportar PDF")
        self.btn_exportar_pdf.setObjectName("btnSecondary")
        self.btn_exportar_pdf.clicked.connect(lambda: self.exportar_pdf("movimentacoes"))
        btn_layout.addWidget(self.btn_exportar_pdf)

        layout.addLayout(btn_layout)

        # Tabela
        self.mov_tabela = QTableWidget()
        self.mov_tabela.setAlternatingRowColors(True)
        self.mov_tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.mov_tabela.verticalHeader().setVisible(False)
        self.mov_tabela.setSortingEnabled(True)

        self.mov_tabela.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        headers = ["ID", "Material", "Tipo", "Quantidade", "Empresa", "Destinatário", "Data/Hora", "Usuário", "Observação"]
        self.mov_tabela.setColumnCount(len(headers))
        self.mov_tabela.setHorizontalHeaderLabels(headers)
        self.mov_tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.mov_tabela)

        # Progresso
        self.mov_progress = QProgressBar()
        self.mov_progress.setVisible(False)
        layout.addWidget(self.mov_progress)

        return widget

    def carregar_empresas_movimentacoes(self):
        """Carrega empresas para o filtro de movimentações"""
        try:
            empresas = api_client.get_empresas()
            self.mov_empresa.clear()
            self.mov_empresa.addItem("Todas")
            for emp in empresas:
                if emp and emp.strip():
                    self.mov_empresa.addItem(emp)
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")

    def carregar_empresas_pedidos(self):
        """Carrega empresas para o filtro de pedidos"""
        try:
            empresas = api_client.get_empresas()
            self.ped_empresa.clear()
            self.ped_empresa.addItem("Todas")
            for emp in empresas:
                if emp and emp.strip():
                    self.ped_empresa.addItem(emp)
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")

    def create_tab_estoque(self):
        """Aba de relatório de estoque"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Filtros
        filtros = QGroupBox("Filtros")
        filtros.setObjectName("configGroup")
        filtros_layout = QHBoxLayout(filtros)
        filtros_layout.setContentsMargins(20, 15, 20, 15)

        # Categoria
        filtros_layout.addWidget(QLabel("Categoria:"))
        self.est_categoria = QComboBox()
        self.est_categoria.addItems(["Todas"])
        self.est_categoria.setObjectName("configCombo")
        filtros_layout.addWidget(self.est_categoria)

        # Empresa
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.est_empresa = QComboBox()
        self.est_empresa.addItems(["Todas"])
        self.est_empresa.setObjectName("configCombo")
        filtros_layout.addWidget(self.est_empresa)

        # Status
        filtros_layout.addWidget(QLabel("Status:"))
        self.est_status = QComboBox()
        self.est_status.addItems(["Todos", "Ativo", "Inativo", "Descontinuado"])
        self.est_status.setObjectName("configCombo")
        filtros_layout.addWidget(self.est_status)

        filtros_layout.addStretch()

        layout.addWidget(filtros)

        # Botões
        btn_layout = QHBoxLayout()

        self.btn_carregar_estoque = QPushButton("🔍 Atualizar")
        self.btn_carregar_estoque.setObjectName("btnPrimary")
        self.btn_carregar_estoque.clicked.connect(self.atualizar_estoque)
        btn_layout.addWidget(self.btn_carregar_estoque)

        btn_layout.addStretch()

        self.btn_exportar_excel_estoque = QPushButton("📊 Exportar Excel")
        self.btn_exportar_excel_estoque.setObjectName("btnSecondary")
        self.btn_exportar_excel_estoque.clicked.connect(lambda: self.exportar_excel("estoque"))
        btn_layout.addWidget(self.btn_exportar_excel_estoque)

        self.btn_exportar_pdf_estoque = QPushButton("📄 Exportar PDF")
        self.btn_exportar_pdf_estoque.setObjectName("btnSecondary")
        self.btn_exportar_pdf_estoque.clicked.connect(lambda: self.exportar_pdf("estoque"))
        btn_layout.addWidget(self.btn_exportar_pdf_estoque)

        layout.addLayout(btn_layout)

        # Tabela
        self.est_tabela = QTableWidget()
        self.est_tabela.setAlternatingRowColors(True)
        self.est_tabela.verticalHeader().setVisible(False)
        self.est_tabela.setSortingEnabled(True)

        self.est_tabela.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        headers = ["ID", "Nome", "Descrição", "Quantidade", "Categoria", "Empresa", "Status"]
        self.est_tabela.setColumnCount(len(headers))
        self.est_tabela.setHorizontalHeaderLabels(headers)
        self.est_tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.est_tabela)

        # ⚠️ NÃO carregar categorias aqui - será feito no on_tab_changed

        return widget

    def create_tab_pedidos(self):
        """Aba de relatório de pedidos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Filtros
        filtros = QGroupBox("Filtros")
        filtros.setObjectName("configGroup")
        filtros_layout = QHBoxLayout(filtros)
        filtros_layout.setContentsMargins(20, 15, 20, 15)

        # Período
        filtros_layout.addWidget(QLabel("Data Início:"))
        self.ped_data_inicio = QDateEdit()
        self.ped_data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.ped_data_inicio.setCalendarPopup(True)
        self.ped_data_inicio.setStyleSheet(CALENDAR_STYLE)
        filtros_layout.addWidget(self.ped_data_inicio)

        filtros_layout.addWidget(QLabel("Data Fim:"))
        self.ped_data_fim = QDateEdit()
        self.ped_data_fim.setDate(QDate.currentDate())
        self.ped_data_fim.setCalendarPopup(True)
        self.ped_data_fim.setStyleSheet(CALENDAR_STYLE)
        filtros_layout.addWidget(self.ped_data_fim)

        # Status
        filtros_layout.addWidget(QLabel("Status:"))
        self.ped_status = QComboBox()
        self.ped_status.addItems(["Todos", "Pendente", "Aprovado", "Concluído", "Cancelado"])
        self.ped_status.setObjectName("configCombo")
        filtros_layout.addWidget(self.ped_status)

        # Empresa
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.ped_empresa = QComboBox()
        self.ped_empresa.addItems(["Todas"])
        self.ped_empresa.setObjectName("configCombo")
        filtros_layout.addWidget(self.ped_empresa)

        filtros_layout.addStretch()

        layout.addWidget(filtros)

        # Botões
        btn_layout = QHBoxLayout()

        self.btn_carregar_pedidos = QPushButton("🔍 Atualizar")
        self.btn_carregar_pedidos.setObjectName("btnPrimary")
        self.btn_carregar_pedidos.clicked.connect(self.atualizar_pedidos)
        btn_layout.addWidget(self.btn_carregar_pedidos)

        btn_layout.addStretch()

        self.btn_exportar_excel_pedidos = QPushButton("📊 Exportar Excel")
        self.btn_exportar_excel_pedidos.setObjectName("btnSecondary")
        self.btn_exportar_excel_pedidos.clicked.connect(lambda: self.exportar_excel("pedidos"))
        btn_layout.addWidget(self.btn_exportar_excel_pedidos)

        self.btn_exportar_pdf_pedidos = QPushButton("📄 Exportar PDF")
        self.btn_exportar_pdf_pedidos.setObjectName("btnSecondary")
        self.btn_exportar_pdf_pedidos.clicked.connect(lambda: self.exportar_pdf("pedidos"))
        btn_layout.addWidget(self.btn_exportar_pdf_pedidos)

        layout.addLayout(btn_layout)

        # Tabela
        self.ped_tabela = QTableWidget()
        self.ped_tabela.setAlternatingRowColors(True)
        self.ped_tabela.verticalHeader().setVisible(False)
        self.ped_tabela.setSortingEnabled(True)

        self.ped_tabela.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        headers = ["ID", "Material", "Qtd", "Solicitante", "Empresa", "Data Solic.", "Data Conclusão", "Status"]
        self.ped_tabela.setColumnCount(len(headers))
        self.ped_tabela.setHorizontalHeaderLabels(headers)
        self.ped_tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.ped_tabela)

        return widget

    def create_tab_demandas(self):
        """Aba de relatório de demandas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Filtros
        filtros = QGroupBox("Filtros")
        filtros.setObjectName("configGroup")
        filtros_layout = QHBoxLayout(filtros)
        filtros_layout.setContentsMargins(20, 15, 20, 15)

        # Período
        filtros_layout.addWidget(QLabel("Data Início:"))
        self.dem_data_inicio = QDateEdit()
        self.dem_data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.dem_data_inicio.setCalendarPopup(True)
        self.dem_data_inicio.setStyleSheet(CALENDAR_STYLE)
        filtros_layout.addWidget(self.dem_data_inicio)

        filtros_layout.addWidget(QLabel("Data Fim:"))
        self.dem_data_fim = QDateEdit()
        self.dem_data_fim.setDate(QDate.currentDate())
        self.dem_data_fim.setCalendarPopup(True)
        self.dem_data_fim.setStyleSheet(CALENDAR_STYLE)
        filtros_layout.addWidget(self.dem_data_fim)

        # Status
        filtros_layout.addWidget(QLabel("Status:"))
        self.dem_status = QComboBox()
        self.dem_status.addItems(["Todos", "Aberto", "Em Andamento", "Concluído", "Cancelado"])
        self.dem_status.setObjectName("configCombo")
        filtros_layout.addWidget(self.dem_status)

        # Prioridade
        filtros_layout.addWidget(QLabel("Prioridade:"))
        self.dem_prioridade = QComboBox()
        self.dem_prioridade.addItems(["Todas", "Alta", "Média", "Baixa"])
        self.dem_prioridade.setObjectName("configCombo")
        filtros_layout.addWidget(self.dem_prioridade)

        filtros_layout.addStretch()

        layout.addWidget(filtros)

        # Botões
        btn_layout = QHBoxLayout()

        self.btn_carregar_demandas = QPushButton("🔍 Atualizar")
        self.btn_carregar_demandas.setObjectName("btnPrimary")
        self.btn_carregar_demandas.clicked.connect(self.atualizar_demandas)
        btn_layout.addWidget(self.btn_carregar_demandas)

        btn_layout.addStretch()

        self.btn_exportar_excel_demandas = QPushButton("📊 Exportar Excel")
        self.btn_exportar_excel_demandas.setObjectName("btnSecondary")
        self.btn_exportar_excel_demandas.clicked.connect(lambda: self.exportar_excel("demandas"))
        btn_layout.addWidget(self.btn_exportar_excel_demandas)

        self.btn_exportar_pdf_demandas = QPushButton("📄 Exportar PDF")
        self.btn_exportar_pdf_demandas.setObjectName("btnSecondary")
        self.btn_exportar_pdf_demandas.clicked.connect(lambda: self.exportar_pdf("demandas"))
        btn_layout.addWidget(self.btn_exportar_pdf_demandas)

        layout.addLayout(btn_layout)

        # Tabela
        self.dem_tabela = QTableWidget()
        self.dem_tabela.setAlternatingRowColors(True)
        self.dem_tabela.verticalHeader().setVisible(False)
        self.dem_tabela.setSortingEnabled(True)

        self.dem_tabela.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        headers = ["ID", "Título", "Solicitante", "Prioridade", "Status", "Data Abertura", "Responsável"]
        self.dem_tabela.setColumnCount(len(headers))
        self.dem_tabela.setHorizontalHeaderLabels(headers)
        self.dem_tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.dem_tabela)

        return widget

    # =====================================================
    # MÉTODOS DE CARREGAMENTO (movidos para on_tab_changed)
    # =====================================================

    def carregar_categorias(self):
        """Carrega as categorias para o filtro"""
        try:
            categorias = api_client.listar_categorias()
            self.est_categoria.clear()
            self.est_categoria.addItem("Todas")
            for cat in categorias:
                self.est_categoria.addItem(cat)

            # Carregar empresas para o filtro de estoque
            empresas = api_client.get_empresas()
            self.est_empresa.clear()
            self.est_empresa.addItem("Todas")
            for emp in empresas:
                if emp and emp.strip():
                    self.est_empresa.addItem(emp)
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")

    def carregar_movimentacoes(self):
        """Carrega movimentações para o relatório"""
        try:
            movimentacoes = api_client.listar_movimentacoes()
            movimentacoes.sort(key=lambda x: x.get("data_hora", ""), reverse=True)
            self.atualizar_tabela_movimentacoes(movimentacoes)
            print(f"✅ {len(movimentacoes)} movimentações carregadas")
        except Exception as e:
            print(f"❌ Erro ao carregar movimentações: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar movimentações: {e}")

    def atualizar_movimentacoes(self):
        """Atualiza as movimentações com os filtros atuais"""
        try:
            # Aqui você pode adicionar filtros por data, tipo, empresa
            movimentacoes = api_client.listar_movimentacoes()
            movimentacoes.sort(key=lambda x: x.get("data_hora", ""), reverse=True)
            self.atualizar_tabela_movimentacoes(movimentacoes)
        except Exception as e:
            print(f"❌ Erro ao atualizar movimentações: {e}")

    def atualizar_tabela_movimentacoes(self, movimentacoes):
        """Atualiza a tabela de movimentações"""
        self.mov_tabela.setRowCount(len(movimentacoes))

        for row, mov in enumerate(movimentacoes):
            self.mov_tabela.setItem(row, 0, QTableWidgetItem(str(mov.get("id", ""))))
            self.mov_tabela.setItem(row, 1, QTableWidgetItem(mov.get("material_nome", "-")))

            tipo = mov.get("tipo", "")
            tipo_item = QTableWidgetItem(tipo.upper())
            if tipo == "entrada":
                tipo_item.setForeground(QColor(42, 157, 143))
            else:
                tipo_item.setForeground(QColor(231, 111, 81))
            self.mov_tabela.setItem(row, 2, tipo_item)

            self.mov_tabela.setItem(row, 3, QTableWidgetItem(str(mov.get("quantidade", 0))))
            self.mov_tabela.setItem(row, 4, QTableWidgetItem(mov.get("empresa", "-")))
            self.mov_tabela.setItem(row, 5, QTableWidgetItem(mov.get("destinatario", "-")))

            data = mov.get("data_hora", "")
            if data:
                data = data[:16].replace("T", " ")
            self.mov_tabela.setItem(row, 6, QTableWidgetItem(data))
            self.mov_tabela.setItem(row, 7, QTableWidgetItem(mov.get("usuario_nome", "-")))

            obs = mov.get('observacao')
            if obs is None:
                obs = '-'
            else:
                obs = str(obs)[:50]
            self.mov_tabela.setItem(row, 8, QTableWidgetItem(obs))

    def carregar_estoque(self):
        """Carrega estoque para o relatório"""
        try:
            materiais = api_client.listar_materiais()
            materiais.sort(key=lambda x: x.get("nome", "").lower())
            self.atualizar_tabela_estoque(materiais)
            print(f"✅ {len(materiais)} materiais carregados")
        except Exception as e:
            print(f"❌ Erro ao carregar estoque: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar estoque: {e}")

    def atualizar_estoque(self):
        """Atualiza o estoque com os filtros atuais"""
        try:
            categoria = self.est_categoria.currentText()
            if is_all_option(categoria):
                categoria = None

            empresa = self.est_empresa.currentText()
            if is_all_option(empresa):
                empresa = None

            status_text = self.est_status.currentText()
            status = "" if is_all_option(status_text) else filter_value(status_text)

            materiais = api_client.listar_materiais(categoria=categoria, empresa=empresa, status=status)
            materiais.sort(key=lambda x: x.get("nome", "").lower())
            self.atualizar_tabela_estoque(materiais)
        except Exception as e:
            print(f"❌ Erro ao atualizar estoque: {e}")

    def atualizar_tabela_estoque(self, materiais):
        """Atualiza a tabela de estoque"""
        self.est_tabela.setRowCount(len(materiais))

        for row, mat in enumerate(materiais):
            self.est_tabela.setItem(row, 0, QTableWidgetItem(str(mat.get("id", ""))))
            self.est_tabela.setItem(row, 1, QTableWidgetItem(mat.get("nome", "")))
            self.est_tabela.setItem(row, 2, QTableWidgetItem(mat.get("descricao", "")[:60]))
            self.est_tabela.setItem(row, 3, QTableWidgetItem(str(mat.get("quantidade", 0))))
            self.est_tabela.setItem(row, 4, QTableWidgetItem(mat.get("categoria", "-")))
            self.est_tabela.setItem(row, 5, QTableWidgetItem(mat.get("empresa", "-")))

            status_item = QTableWidgetItem(mat.get("status", "ativo").upper())
            if mat.get("status") == "ativo":
                status_item.setForeground(QColor(42, 157, 143))
            else:
                status_item.setForeground(QColor(231, 111, 81))
            self.est_tabela.setItem(row, 6, status_item)

    def carregar_pedidos(self):
        """Carrega pedidos para o relatório"""
        try:
            pedidos = api_client.listar_pedidos()
            pedidos.sort(key=lambda x: x.get("data_solicitacao", ""), reverse=True)
            self.atualizar_tabela_pedidos(pedidos)
            print(f"✅ {len(pedidos)} pedidos carregados")
        except Exception as e:
            print(f"❌ Erro ao carregar pedidos: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar pedidos: {e}")

    def atualizar_pedidos(self):
        """Atualiza os pedidos com os filtros atuais"""
        try:
            status_text = self.ped_status.currentText()
            status = None if is_all_option(status_text) else filter_value(status_text)

            empresa = self.ped_empresa.currentText()
            if is_all_option(empresa):
                empresa = None

            pedidos = api_client.listar_pedidos(status=status, empresa=empresa)
            pedidos.sort(key=lambda x: x.get("data_solicitacao", ""), reverse=True)
            self.atualizar_tabela_pedidos(pedidos)
        except Exception as e:
            print(f"❌ Erro ao atualizar pedidos: {e}")

    def atualizar_tabela_pedidos(self, pedidos):
        """Atualiza a tabela de pedidos"""
        self.ped_tabela.setRowCount(len(pedidos))

        status_cores = {
            "pendente": QColor(244, 162, 97),
            "aprovado": QColor(42, 157, 143),
            "concluido": QColor(44, 125, 160),
            "cancelado": QColor(231, 111, 81)
        }

        for row, ped in enumerate(pedidos):
            self.ped_tabela.setItem(row, 0, QTableWidgetItem(str(ped.get("id", ""))))
            self.ped_tabela.setItem(row, 1, QTableWidgetItem(ped.get("material_nome", "-")))
            self.ped_tabela.setItem(row, 2, QTableWidgetItem(str(ped.get("quantidade", 0))))
            self.ped_tabela.setItem(row, 3, QTableWidgetItem(ped.get("solicitante", "-")))
            self.ped_tabela.setItem(row, 4, QTableWidgetItem(ped.get("empresa", "-")))
            self.ped_tabela.setItem(row, 5, QTableWidgetItem(ped.get("data_solicitacao", "-")))
            self.ped_tabela.setItem(row, 6, QTableWidgetItem(ped.get("data_conclusao", "-") or "-"))

            status_item = QTableWidgetItem(ped.get("status", "pendente").upper())
            status_item.setForeground(status_cores.get(ped.get("status", "pendente"), QColor(0, 0, 0)))
            self.ped_tabela.setItem(row, 7, status_item)

    def carregar_demandas(self):
        """Carrega demandas para o relatório"""
        try:
            demandas = api_client.listar_demandas()
            demandas.sort(key=lambda x: x.get("data_abertura", ""), reverse=True)
            self.atualizar_tabela_demandas(demandas)
            print(f"✅ {len(demandas)} demandas carregadas")
        except Exception as e:
            print(f"❌ Erro ao carregar demandas: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar demandas: {e}")

    def atualizar_demandas(self):
        """Atualiza as demandas com os filtros atuais"""
        try:
            status_text = self.dem_status.currentText()
            status = None if is_all_option(status_text) else filter_value(status_text)

            prioridade_text = self.dem_prioridade.currentText()
            prioridade = None if is_all_option(prioridade_text) else filter_value(prioridade_text)

            demandas = api_client.listar_demandas(status=status, prioridade=prioridade)
            demandas.sort(key=lambda x: x.get("data_abertura", ""), reverse=True)
            self.atualizar_tabela_demandas(demandas)
        except Exception as e:
            print(f"❌ Erro ao atualizar demandas: {e}")

    def atualizar_tabela_demandas(self, demandas):
        """Atualiza a tabela de demandas"""
        self.dem_tabela.setRowCount(len(demandas))

        prioridade_cores = {
            "alta": QColor(231, 111, 81),
            "media": QColor(244, 162, 97),
            "baixa": QColor(42, 157, 143)
        }

        for row, dem in enumerate(demandas):
            self.dem_tabela.setItem(row, 0, QTableWidgetItem(str(dem.get("id", ""))))
            self.dem_tabela.setItem(row, 1, QTableWidgetItem(dem.get("titulo", "")[:60]))
            self.dem_tabela.setItem(row, 2, QTableWidgetItem(dem.get("solicitante", "-")))

            prioridade_item = QTableWidgetItem(dem.get("prioridade", "media").upper())
            prioridade_item.setForeground(prioridade_cores.get(dem.get("prioridade", "media"), QColor(0, 0, 0)))
            self.dem_tabela.setItem(row, 3, prioridade_item)

            status_item = QTableWidgetItem(dem.get("status", "aberto").upper())
            self.dem_tabela.setItem(row, 4, status_item)

            data = dem.get("data_abertura", "")
            if data:
                data = data[:10]
            self.dem_tabela.setItem(row, 5, QTableWidgetItem(data))
            self.dem_tabela.setItem(row, 6, QTableWidgetItem(dem.get("responsavel", "-")))

    # =====================================================
    # MÉTODOS DE EXPORTAÇÃO (mantidos originais)
    # =====================================================

    def exportar_excel(self, tipo):
        """Exporta dados para Excel"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Excel", f"relatorio_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel Files (*.xlsx)"
            )

            if not file_path:
                return

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = f"Relatório {tipo.capitalize()}"

            header_font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='2C7DA0', end_color='2C7DA0', fill_type='solid')
            header_alignment = Alignment(horizontal='center', vertical='center')

            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            ws.merge_cells('A1:Z1')
            titulo_cell = ws['A1']
            titulo_cell.value = f"Relatório de {tipo.upper()}"
            titulo_cell.font = Font(name='Arial', size=16, bold=True)
            titulo_cell.alignment = Alignment(horizontal='center')

            ws['A2'] = f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            ws.merge_cells('A2:Z2')

            if tipo == "movimentacoes":
                headers = ["ID", "Material", "Tipo", "Quantidade", "Empresa", "Destinatário", "Data/Hora", "Usuário", "Observação"]
                dados = self.mov_tabela
            elif tipo == "estoque":
                headers = ["ID", "Nome", "Descrição", "Quantidade", "Categoria", "Empresa", "Status"]
                dados = self.est_tabela
            elif tipo == "pedidos":
                headers = ["ID", "Material", "Qtd", "Solicitante", "Empresa", "Data Solic.", "Data Conclusão", "Status"]
                dados = self.ped_tabela
            else:
                headers = ["ID", "Título", "Solicitante", "Prioridade", "Status", "Data Abertura", "Responsável"]
                dados = self.dem_tabela

            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=4, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = border

            for row in range(dados.rowCount()):
                for col in range(dados.columnCount()):
                    item = dados.item(row, col)
                    value = item.text() if item else ""
                    cell = ws.cell(row=row + 5, column=col + 1, value=value)
                    cell.border = border
                    cell.alignment = Alignment(horizontal='left', vertical='center')

            for col in range(1, len(headers) + 1):
                ws.column_dimensions[get_column_letter(col)].width = 20

            wb.save(file_path)
            QMessageBox.information(self, "Sucesso", f"Relatório exportado com sucesso!\n\nArquivo: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar Excel: {e}")

    def exportar_pdf(self, tipo):
        """Exporta dados para PDF"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar PDF", f"relatorio_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            elements = []

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=1,
                spaceAfter=20
            )

            elements.append(Paragraph(f"Relatório de {tipo.upper()}", title_style))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            if tipo == "movimentacoes":
                headers = ["ID", "Material", "Tipo", "Qtd", "Empresa", "Destinatário", "Data/Hora", "Usuário"]
                dados = self.mov_tabela
            elif tipo == "estoque":
                headers = ["ID", "Nome", "Descrição", "Qtd", "Categoria", "Empresa", "Status"]
                dados = self.est_tabela
            elif tipo == "pedidos":
                headers = ["ID", "Material", "Qtd", "Solicitante", "Empresa", "Data Solic.", "Status"]
                dados = self.ped_tabela
            else:
                headers = ["ID", "Título", "Solicitante", "Prioridade", "Status", "Data Abertura", "Responsável"]
                dados = self.dem_tabela

            data = [headers]

            for row in range(dados.rowCount()):
                row_data = []
                for col in range(dados.columnCount()):
                    item = dados.item(row, col)
                    value = item.text() if item else ""
                    if len(value) > 40:
                        value = value[:37] + "..."
                    row_data.append(value)
                data.append(row_data)

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C7DA0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            elements.append(table)

            doc.build(elements)
            QMessageBox.information(self, "Sucesso", f"Relatório exportado com sucesso!\n\nArquivo: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {e}")
