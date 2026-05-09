from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QDateEdit,
                               QTextEdit, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from api_client import api_client
from access_control import get_action_label, has_action_access
from widgets.company_filter_utils import company_filter_ready, populate_company_filter, selected_company_value
from widgets.form_feedback import focus_invalid_field, optional_label, required_field_message, required_hint_label, required_label
from widgets.filter_utils import contains_text, is_all_option, same_filter_value, same_text
from widgets.table_utils import configure_data_table, number_item, refresh_data_table_layout
from user_preferences import (
    apply_combo_data,
    apply_combo_text,
    apply_table_sort_state,
    get_table_sort_state,
    get_widget_preferences,
    save_widget_preferences,
)


class ManutencoesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario = {}
        self.manutencoes = []
        self.manutencoes_cache = []
        self.maquinas = []
        self.empresas = []
        self._loaded = False
        self._restoring_preferences = False
        self._saved_preferences = {}
        self.init_ui()

    def on_show(self):
        if not self._loaded:
            self.carregar_empresas()
            self._carregar_preferencias()
            self._aplicar_preferencias_salvas()
            if self.empresa_pronta():
                empresa = self.empresa_param()
                self.carregar_maquinas(empresa=empresa)
                self.carregar_manutencoes()
            else:
                self._mostrar_prompt_empresa()
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

        filtros.addWidget(QLabel("Busca:"))
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setPlaceholderText("Pesquisar por máquina, tipo, descrição, responsável...")
        self.pesquisa_edit.setMaximumWidth(340)
        self.pesquisa_edit.textChanged.connect(self.filtrar_manutencoes)
        filtros.addWidget(self.pesquisa_edit)

        filtros.addSpacing(20)

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
        self.empresa_filter.currentIndexChanged.connect(self.ao_alterar_empresa)
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

        self.empresa_prompt = QLabel('Selecione uma empresa ou "Todas as empresas" para carregar as manutenções.')
        self.empresa_prompt.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(self.empresa_prompt)

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
        configure_data_table(
            self.tabela,
            stretch_columns=(3,),
            minimum_section_size=88,
            minimum_widths={
                0: 72,
                1: 210,
                2: 120,
                3: 280,
                4: 135,
                5: 135,
                6: 170,
                7: 120,
            },
        )
        self.tabela.horizontalHeader().sortIndicatorChanged.connect(self._ao_ordenar_tabela)

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
        self.aplicar_permissoes()

    def set_usuario(self, usuario):
        self.usuario = usuario or {}
        self._carregar_preferencias()
        self.aplicar_permissoes()
        if self._loaded:
            self._aplicar_preferencias_salvas()
            if self.empresa_pronta():
                empresa = self.empresa_param()
                self.carregar_maquinas(empresa=empresa)
                self.carregar_manutencoes()
            else:
                self._mostrar_prompt_empresa()

    def _pode(self, action_key):
        return has_action_access(self.usuario, action_key)

    def _avisar_sem_permissao(self, action_key):
        QMessageBox.warning(self, "Acesso não permitido", f"Você não tem permissão para {get_action_label(action_key)}.")

    def aplicar_permissoes(self):
        if hasattr(self, "novo_btn"):
            self.novo_btn.setVisible(self._pode("manutencoes.create"))
        if hasattr(self, "editar_btn"):
            self.editar_btn.setVisible(self._pode("manutencoes.edit"))
        if hasattr(self, "concluir_btn"):
            self.concluir_btn.setVisible(self._pode("manutencoes.complete"))
        if hasattr(self, "deletar_btn"):
            self.deletar_btn.setVisible(self._pode("manutencoes.delete"))

    def empresa_pronta(self):
        return company_filter_ready(self.empresa_filter)

    def empresa_param(self):
        return selected_company_value(self.empresa_filter)

    def _carregar_preferencias(self):
        self._saved_preferences = get_widget_preferences(self.usuario, "manutencoes")

    def _aplicar_preferencias_salvas(self):
        self._restoring_preferences = True
        try:
            self.pesquisa_edit.setText(str(self._saved_preferences.get("busca") or ""))
            apply_combo_text(self.status_filter, self._saved_preferences.get("status"))
            apply_combo_data(self.empresa_filter, self._saved_preferences.get("empresa"))
        finally:
            self._restoring_preferences = False

    def _aplicar_preferencias_dependentes(self):
        self._restoring_preferences = True
        try:
            apply_combo_data(self.maquina_filter, self._saved_preferences.get("maquina_id"))
        finally:
            self._restoring_preferences = False

    def _preferencias_atuais(self):
        return {
            "busca": self.pesquisa_edit.text().strip(),
            "status": self.status_filter.currentText(),
            "empresa": self.empresa_filter.currentData(),
            "maquina_id": self.maquina_filter.currentData(),
            "sort": get_table_sort_state(self.tabela),
        }

    def _salvar_preferencias(self):
        if self._restoring_preferences:
            return
        self._saved_preferences = self._preferencias_atuais()
        save_widget_preferences(self.usuario, "manutencoes", self._saved_preferences)

    def _ao_ordenar_tabela(self, *_args):
        self._salvar_preferencias()

    def _mostrar_prompt_empresa(self):
        self.manutencoes = []
        self.manutencoes_cache = []
        self.tabela.setRowCount(0)
        self.maquina_filter.blockSignals(True)
        self.maquina_filter.clear()
        self.maquina_filter.addItem("Todas as máquinas")
        self.maquina_filter.blockSignals(False)
        self.empresa_prompt.setVisible(True)

    def ao_alterar_empresa(self):
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            self._salvar_preferencias()
            return
        empresa = self.empresa_param()
        self.carregar_maquinas(empresa=empresa)
        self.carregar_manutencoes()
        self._salvar_preferencias()

    def carregar_maquinas(self, empresa=None):
        """Carrega a lista de máquinas para o filtro"""
        try:
            self.maquinas = api_client.listar_maquinas_para_manutencao(empresa=empresa)
            self.maquina_filter.clear()
            self.maquina_filter.addItem("Todas as máquinas")
            for maq in self.maquinas:
                self.maquina_filter.addItem(f"{maq.get('nome', '')} - {maq.get('empresa', '')}", maq.get("id"))
            self._aplicar_preferencias_dependentes()
            print(f'✅ Máquinas carregadas: {len(self.maquinas)}')
        except Exception as e:
            print(f"Erro ao carregar máquinas: {e}")

    def carregar_empresas(self):
        """Carrega a lista de empresas do backend para o filtro"""
        try:
            empresas = api_client.get_empresas()
            populate_company_filter(self.empresa_filter, empresas)
            print(f'✅ Empresas carregadas para filtro: {len(empresas)}')
        except Exception as e:
            print(f'❌ Erro ao carregar empresas: {e}')

    def carregar_manutencoes(self):
        """Carrega a lista de manutenções do backend"""
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        try:
            self.manutencoes = api_client.listar_manutencoes(empresa=self.empresa_param())
            self.manutencoes_cache = self.manutencoes.copy()
            self.filtrar_manutencoes()
            self.atualizar_dashboard_home()
            self.empresa_prompt.setVisible(False)
            print(f"✅ Manutenções carregadas: {len(self.manutencoes)}")
        except Exception as e:
            print(f"❌ Erro ao carregar manutenções: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar manutenções: {e}")

    def filtrar_manutencoes(self):
        """Filtra as manutenções com base nos filtros"""
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        status = self.status_filter.currentText()
        empresa = self.empresa_filter.currentText()
        maquina_id_selecionada = self.maquina_filter.currentData()
        search_text = self.pesquisa_edit.text()

        filtered = []
        for manut in self.manutencoes:
            # Filtro por status
            if not is_all_option(status) and not same_filter_value(manut.get("status", ""), status):
                continue

            # Filtro por empresa
            if self.empresa_param() is None and not is_all_option(empresa):
                # Buscar a empresa da máquina
                maquina_id = manut.get('maquina_id')
                if maquina_id:
                    maquina = next((m for m in self.maquinas if m.get('id') == maquina_id), None)
                    if maquina and not same_text(maquina.get('empresa'), empresa):
                        continue
                else:
                    # Se não encontrar a máquina, pular
                    continue


            # Filtro por maquina
            if maquina_id_selecionada and manut.get("maquina_id") != maquina_id_selecionada:
                continue

            if not contains_text(
                search_text,
                manut.get("id", ""),
                manut.get("maquina_nome", ""),
                manut.get("tipo", ""),
                manut.get("descricao", ""),
                manut.get("responsavel", ""),
                manut.get("status", ""),
            ):
                continue

            filtered.append(manut)

        self.atualizar_tabela(filtered)
        self._salvar_preferencias()

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
            self.tabela.setItem(row, 0, number_item(manut.get("id", "")))
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

        apply_table_sort_state(self.tabela, self._saved_preferences.get("sort"))
        refresh_data_table_layout(self.tabela)

    def nova_manutencao(self):
        if not self._pode("manutencoes.create"):
            self._avisar_sem_permissao("manutencoes.create")
            return
        if not self.empresa_pronta():
            QMessageBox.warning(self, "Atenção", "Selecione uma empresa antes de registrar manutenções.")
            return
        dialog = ManutencaoDialog(maquinas=self.maquinas, parent=self)
        if dialog.exec():
            self.carregar_manutencoes()
            self.carregar_maquinas(empresa=self.empresa_param())
            self.atualizar_dashboard_home()

    def editar_manutencao(self):
        if not self._pode("manutencoes.edit"):
            self._avisar_sem_permissao("manutencoes.edit")
            return
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
                self.carregar_maquinas(empresa=self.empresa_param())
                self.atualizar_dashboard_home()

    def concluir_manutencao(self):
        if not self._pode("manutencoes.complete"):
            self._avisar_sem_permissao("manutencoes.complete")
            return
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
        if not self._pode("manutencoes.delete"):
            self._avisar_sem_permissao("manutencoes.delete")
            return
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

    def atualizar_dashboard_home(self):
        """Sincroniza o card da home quando manutencoes mudam."""
        main_window = self.window()
        if main_window and hasattr(main_window, "refresh_home_dashboard"):
            main_window.refresh_home_dashboard()


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
        layout.addWidget(required_hint_label())

        # Empresa (NOVO)
        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_empresas()
        self.empresa_combo.currentIndexChanged.connect(self.filtrar_maquinas_por_empresa)
        form_layout.addRow(required_label('Empresa:'), self.empresa_combo)
        # Máquina
        self.maquina_combo = QComboBox()
        self.maquina_combo.setEditable(False)
        self.maquina_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_maquinas_combo()
        form_layout.addRow(required_label('Máquina:'), self.maquina_combo)
        # Tipo
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["preventiva", "corretiva", "emergencial"])
        form_layout.addRow(required_label("Tipo:"), self.tipo_combo)
        # Descrição
        self.descricao_edit = QTextEdit()
        self.descricao_edit.setMaximumHeight(80)
        self.descricao_edit.setPlaceholderText("Descreva a manutenção a ser realizada...")
        form_layout.addRow(required_label("Descrição:"), self.descricao_edit)

        # Data Início
        self.data_inicio = QDateEdit()
        self.data_inicio.setDate(QDate.currentDate())
        self.data_inicio.setCalendarPopup(True)
        form_layout.addRow(optional_label("Data de Início:"), self.data_inicio)

        # Data Próxima Manutenção
        self.data_proxima = QDateEdit()
        self.data_proxima.setDate(QDate.currentDate().addMonths(6))
        self.data_proxima.setCalendarPopup(True)
        form_layout.addRow(optional_label("Próx. Manutenção:"), self.data_proxima)

        # Responsável
        self.responsavel_edit = QLineEdit()
        self.responsavel_edit.setPlaceholderText("Nome do responsável")
        form_layout.addRow(optional_label("Responsável:"), self.responsavel_edit)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pendente", "andamento", "concluida", "cancelada"])
        form_layout.addRow(required_label("Status:"), self.status_combo)

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
            focus_invalid_field(self.maquina_combo)
            QMessageBox.warning(self, "Campo obrigatório", required_field_message("Máquina"))
            return

        descricao = self.descricao_edit.toPlainText().strip()
        if not descricao:
            focus_invalid_field(self.descricao_edit)
            QMessageBox.warning(self, "Campo obrigatório", required_field_message("Descrição"))
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
                    maquina_nome = self.maquina_combo.currentText().split(" - ")[0].strip() or "manutenção"
                    QMessageBox.information(self, "Sucesso", f"Manutencao de '{maquina_nome}' atualizada com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível atualizar a manutenção. Revise os dados e tente novamente.")
            else:
                # Criar
                response = api_client.criar_manutencao(dados)
                if response:
                    maquina_nome = self.maquina_combo.currentText().split(" - ")[0].strip() or "manutenção"
                    QMessageBox.information(self, "Sucesso", f"Manutencao de '{maquina_nome}' criada com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível criar a manutenção. Revise os dados e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar a manutenção.\n\nDetalhes: {e}")
