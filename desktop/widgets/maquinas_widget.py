from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QDialog, QFormLayout, QTextEdit,
                               QMessageBox, QHeaderView, QApplication, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QCursor
from api_client import api_client
from access_control import get_action_label, has_action_access
from widgets.company_filter_utils import company_filter_ready, populate_company_filter, selected_company_value
from widgets.form_feedback import focus_invalid_field, optional_label, required_field_message, required_hint_label, required_label
from widgets.toast_notification import notification_manager
from widgets.filter_utils import contains_text, is_all_option, same_filter_value, same_text
from widgets.table_utils import configure_data_table, number_item, refresh_data_table_layout
from user_preferences import (
    apply_table_column_widths,
    apply_combo_data,
    apply_combo_text,
    apply_table_sort_state,
    get_table_column_widths,
    get_table_sort_state,
    get_widget_preferences,
    save_widget_preferences,
)


class MaquinasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario = {}
        self.maquinas = []
        self._visible_maquinas = []
        self.dados_cache = []
        self.departamentos = []
        self.empresas = []  # NOVO: lista de empresas
        self.monitoramento_status = {}
        self.lan_status = {"links": [], "resumo": {}}
        self._loaded = False
        self._restoring_preferences = False
        self._saved_preferences = {}
        self._summary_labels = {}
        self.init_ui()
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.atualizar_monitoramento_rede)
        self.monitor_timer.start(30000)

    def on_show(self):
        if not self._loaded:
            self.carregar_departamentos()
            self.carregar_empresas()
            self._carregar_preferencias()
            self._aplicar_preferencias_salvas()
            if self.empresa_pronta():
                self.carregar_maquinas()
            else:
                self._mostrar_prompt_empresa()
            self._loaded = True

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
            QFrame#machineHeroCard {{
                background-color: {colors_map['hero_bg']};
                border: 1px solid {colors_map['hero_border']};
                border-radius: 20px;
            }}
            QLabel#machineHeroTitle {{
                color: {colors_map['title']};
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#machineHeroSubtitle {{
                color: {colors_map['muted']};
                font-size: 13px;
            }}
            QFrame#machineSummaryCard, QFrame#machineDetailCard {{
                background-color: {colors_map['card_bg']};
                border: 1px solid {colors_map['card_border']};
                border-radius: 16px;
            }}
            QLabel#machineSummaryTitle {{
                color: {colors_map['muted']};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#machineSummaryValue {{
                color: {colors_map['title']};
                font-size: 24px;
                font-weight: 700;
            }}
            QLabel#machineSummaryCaption, QLabel#machineDetailBody {{
                color: {colors_map['muted']};
                font-size: 12px;
            }}
            QLabel#machineDetailTitle {{
                color: {colors_map['title']};
                font-size: 16px;
                font-weight: 700;
            }}
            QLineEdit#machineSearchInput {{
                background-color: {colors_map['card_bg']};
                color: {colors_map['title']};
                border: 1px solid {colors_map['card_border']};
                border-radius: 12px;
                padding: 10px 14px;
                min-height: 18px;
            }}
            """
        )

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Cabeçalho
        header = QHBoxLayout()
        titulo = QLabel("🖥️ Máquinas")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        header.addStretch()

        # Botão Nova Máquina
        self.novo_btn = QPushButton("+ Nova Máquina")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.nova_maquina)
        header.addWidget(self.novo_btn)

        # Botão Atualizar
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_maquinas)
        header.addWidget(self.atualizar_btn)

        self.monitorar_btn = QPushButton("📡 Atualizar Rede")
        self.monitorar_btn.setFixedHeight(40)
        self.monitorar_btn.clicked.connect(lambda: self.atualizar_monitoramento_rede(show_feedback=True))
        header.addWidget(self.monitorar_btn)

        layout.addLayout(header)

        # Barra de pesquisa
        self.pesquisa_edit = QLineEdit()
        self.pesquisa_edit.setObjectName("machineSearchInput")
        self.pesquisa_edit.setPlaceholderText("🔍 Pesquisar por nome, modelo, MAC...")
        self.pesquisa_edit.setMaximumWidth(350)
        self.pesquisa_edit.textChanged.connect(self.filtrar_maquinas)
        layout.addWidget(self.pesquisa_edit)

        # Filtros (todos na mesma linha)
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(15)

        # Filtro Empresa (NOVO)
        filtros_layout.addWidget(QLabel("Empresa:"))
        self.empresa_filter = QComboBox()
        self.empresa_filter.setMinimumWidth(150)
        self.empresa_filter.setMaximumWidth(200)
        self.empresa_filter.currentIndexChanged.connect(self.ao_alterar_empresa)
        filtros_layout.addWidget(self.empresa_filter)

        # Filtro Departamento
        filtros_layout.addWidget(QLabel("Departamento:"))
        self.departamento_filter = QComboBox()
        self.departamento_filter.setMinimumWidth(150)
        self.departamento_filter.setMaximumWidth(200)
        self.departamento_filter.addItem("Todos os departamentos")
        self.departamento_filter.currentTextChanged.connect(self.filtrar_maquinas)
        filtros_layout.addWidget(self.departamento_filter)

        # Filtro Status
        filtros_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(120)
        self.status_filter.setMaximumWidth(150)
        self.status_filter.addItems(["Todos", "Ativo", "Manutenção", "Inativo"])
        self.status_filter.currentTextChanged.connect(self.filtrar_maquinas)
        filtros_layout.addWidget(self.status_filter)

        filtros_layout.addWidget(QLabel("Rede:"))
        self.rede_filter = QComboBox()
        self.rede_filter.setMinimumWidth(140)
        self.rede_filter.setMaximumWidth(170)
        self.rede_filter.addItems(
            [
                "Todas",
                "Online",
                "Sem resposta",
                "Sem rota",
                "Rota com erro",
                "Sem alvo",
                "Com erro",
            ]
        )
        self.rede_filter.currentTextChanged.connect(self.filtrar_maquinas)
        filtros_layout.addWidget(self.rede_filter)

        filtros_layout.addStretch()

        layout.addLayout(filtros_layout)

        self.empresa_prompt = QLabel('Selecione uma empresa ou "Todas as empresas" para carregar as máquinas.')
        self.empresa_prompt.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(self.empresa_prompt)

        self.monitoramento_label = QLabel("Monitoramento de rede local aguardando a primeira leitura.")
        self.monitoramento_label.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(self.monitoramento_label)

        self.summary_strip = self._create_summary_strip(
            [
                ("total", "Máquinas visíveis", "Base filtrada na grade"),
                ("online", "Online", "Conectividade confirmada"),
                ("atencao", "Atenção", "Sem resposta, rota ou alvo"),
                ("manutencao", "Em manutenção", "Estado operacional interno"),
            ]
        )
        layout.addWidget(self.summary_strip)

        # Tabela de máquinas
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSortingEnabled(True)

        self.tabela.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        headers = ["ID", "Nome", "Modelo", "IP/Host", "Endereço MAC", "Empresa", "Departamento", "Rede", "Status", "Observações"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        configure_data_table(
            self.tabela,
            stretch_columns=(1, 9),
            minimum_section_size=88,
            minimum_widths={
                0: 72,
                1: 210,
                2: 170,
                3: 170,
                4: 170,
                5: 170,
                6: 180,
                7: 145,
                8: 120,
                9: 240,
            },
        )
        self.tabela.horizontalHeader().sortIndicatorChanged.connect(self._ao_ordenar_tabela)
        self.tabela.horizontalHeader().sectionResized.connect(self._ao_redimensionar_coluna)
        self.tabela.itemSelectionChanged.connect(self._update_detail_from_selection)

        self.detail_card = self._create_detail_panel()
        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)
        content_layout.addWidget(self.tabela, 3)
        content_layout.addWidget(self.detail_card, 1)
        layout.addLayout(content_layout, 1)

        # Botões de ação
        acoes = QHBoxLayout()
        acoes.addStretch()

        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_maquina)
        acoes.addWidget(self.editar_btn)

        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_maquina)
        acoes.addWidget(self.deletar_btn)

        layout.addLayout(acoes)
        self.aplicar_permissoes()
        self._set_detail_empty()

    def set_usuario(self, usuario):
        self.usuario = usuario or {}
        self._carregar_preferencias()
        self.aplicar_permissoes()
        if self._loaded:
            self._aplicar_preferencias_salvas()
            if self.empresa_pronta():
                self.carregar_maquinas()
            else:
                self._mostrar_prompt_empresa()

    def _pode(self, action_key):
        return has_action_access(self.usuario, action_key)

    def _avisar_sem_permissao(self, action_key):
        QMessageBox.warning(self, "Acesso não permitido", f"Você não tem permissão para {get_action_label(action_key)}.")

    def aplicar_permissoes(self):
        if hasattr(self, "novo_btn"):
            self.novo_btn.setVisible(self._pode("maquinas.create"))
        if hasattr(self, "editar_btn"):
            self.editar_btn.setVisible(self._pode("maquinas.edit"))
        if hasattr(self, "deletar_btn"):
            self.deletar_btn.setVisible(self._pode("maquinas.delete"))

    def _create_summary_strip(self, specs):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        self._summary_labels = {}

        for key, title, caption in specs:
            card = QFrame()
            card.setObjectName("machineSummaryCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(4)

            title_label = QLabel(title)
            title_label.setObjectName("machineSummaryTitle")
            card_layout.addWidget(title_label)

            value_label = QLabel("--")
            value_label.setObjectName("machineSummaryValue")
            card_layout.addWidget(value_label)

            caption_label = QLabel(caption)
            caption_label.setObjectName("machineSummaryCaption")
            caption_label.setWordWrap(True)
            card_layout.addWidget(caption_label)

            layout.addWidget(card, 1)
            self._summary_labels[key] = value_label

        return container

    def _create_detail_panel(self):
        card = QFrame()
        card.setObjectName("machineDetailCard")
        card.setMinimumWidth(320)
        card.setMaximumWidth(380)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel("Detalhes da máquina")
        title.setObjectName("machineDetailTitle")
        layout.addWidget(title)

        self.detail_body = QLabel("")
        self.detail_body.setObjectName("machineDetailBody")
        self.detail_body.setWordWrap(True)
        self.detail_body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.detail_body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.detail_body, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.detail_copy_btn = QPushButton("Copiar IP/Host")
        self.detail_copy_btn.clicked.connect(self._copiar_ip_ou_host_selecionado)
        actions.addWidget(self.detail_copy_btn)

        self.detail_edit_btn = QPushButton("Editar")
        self.detail_edit_btn.clicked.connect(self.editar_maquina)
        actions.addWidget(self.detail_edit_btn)

        layout.addLayout(actions)

        return card

    def _set_summary_value(self, key, value):
        label = self._summary_labels.get(key)
        if label is not None:
            label.setText(str(value))

    def _set_detail_empty(self):
        if hasattr(self, "detail_body"):
            self.detail_body.setText(
                "Selecione uma máquina para ver IP/Host, rota de rede, status operacional, MAC e observações."
            )
        if hasattr(self, "detail_copy_btn"):
            self.detail_copy_btn.setEnabled(False)
        if hasattr(self, "detail_edit_btn"):
            self.detail_edit_btn.setEnabled(False)

    def _build_detail_text(self, maquina, monitor_label, monitor_tooltip, ip_ou_host):
        observacoes = maquina.get("observacoes") or "-"
        return (
            f"Nome: {maquina.get('nome', '-')}\n"
            f"Modelo: {maquina.get('modelo') or '-'}\n"
            f"IP/Host: {ip_ou_host}\n"
            f"MAC: {maquina.get('mac_address') or '-'}\n"
            f"Empresa: {maquina.get('empresa') or '-'}\n"
            f"Departamento: {maquina.get('departamento') or '-'}\n"
            f"Rede: {monitor_label}\n"
            f"Detalhe da rede: {monitor_tooltip}\n"
            f"Status operacional: {str(maquina.get('status', '-')).upper()}\n"
            f"Observações: {observacoes}"
        )

    def _copiar_ip_ou_host_selecionado(self):
        current_row = self.tabela.currentRow()
        if current_row < 0:
            return

        id_item = self.tabela.item(current_row, 0)
        if id_item is None:
            return

        try:
            maquina_id = int(id_item.text())
        except Exception:
            return

        maquina = next((item for item in self._visible_maquinas if item.get("id") == maquina_id), None)
        if not maquina:
            return

        ip_ou_host, _monitor_label, _monitor_status, _monitor_tooltip = self._resolve_monitoramento_visual(maquina)
        if not ip_ou_host or ip_ou_host == "-":
            notification_manager.error("Esta máquina não possui IP/Host configurado.", self.window(), 2500)
            return

        QApplication.clipboard().setText(str(ip_ou_host))
        notification_manager.success("IP/Host copiado para a área de transferência.", self.window(), 2500)

    def empresa_pronta(self):
        return company_filter_ready(self.empresa_filter)

    def empresa_param(self):
        return selected_company_value(self.empresa_filter)

    def _empresa_normalizada(self, value):
        return str(value or "").strip().upper()

    def _empresa_origem(self):
        return self._empresa_normalizada(self.usuario.get("empresa"))

    def _rota_para_empresa(self, empresa_destino):
        origem = self._empresa_origem()
        destino = self._empresa_normalizada(empresa_destino)
        if not origem or not destino or origem == destino:
            return None

        for link in self.lan_status.get("links", []):
            if self._empresa_normalizada(link.get("empresa")) == destino:
                return link
        return None

    def _resolve_monitoramento_visual(self, maquina):
        monitor = self.monitoramento_status.get(maquina.get("id"), {})
        ip_ou_host = maquina.get("ip_address") or monitor.get("alvo_monitoramento") or "-"
        monitor_label = monitor.get("monitor_label", "Sem leitura")
        monitor_status = monitor.get("monitor_status", "nao_configurado")
        monitor_tooltip = monitor.get("detalhe") or "Aguardando leitura de rede."
        latencia_ms = monitor.get("latencia_ms")
        if latencia_ms is not None:
            monitor_tooltip = f"{monitor_tooltip}\nLatencia: {latencia_ms} ms"

        if monitor_status == "online":
            qualidade = str(monitor_label or "").strip()
            monitor_label = "Online"
            if qualidade and qualidade.lower() != "online":
                monitor_tooltip = f"Qualidade da conexao: {qualidade}.\n{monitor_tooltip}"

        rota = self._rota_para_empresa(maquina.get("empresa"))
        if rota:
            rota_status = rota.get("status")
            if rota_status == "offline":
                monitor_status = "sem_rota"
                monitor_label = "Sem rota"
                monitor_tooltip = (
                    f"LAN-to-LAN indisponivel para {maquina.get('empresa')}.\n"
                    f"{rota.get('detalhe') or rota.get('servidor') or 'Sem resposta do firewall remoto.'}"
                )
            elif rota_status == "erro":
                monitor_status = "rota_com_erro"
                monitor_label = "Rota com erro"
                monitor_tooltip = (
                    f"A rota para {maquina.get('empresa')} nao pode ser validada.\n"
                    f"{rota.get('detalhe') or rota.get('servidor') or 'Falha na leitura do firewall remoto.'}"
                )
            elif rota_status == "online" and monitor_status == "offline":
                monitor_status = "sem_resposta"
                monitor_label = "Sem resposta"
                monitor_tooltip = (
                    f"A rota LAN-to-LAN para {maquina.get('empresa')} esta OK, "
                    "mas o host monitorado nao respondeu.\n"
                    f"{monitor.get('detalhe') or 'Sem resposta do equipamento.'}"
                )
        elif monitor_status == "offline":
            monitor_status = "sem_resposta"
            monitor_label = "Sem resposta"
            monitor_tooltip = (
                "A rede local respondeu, mas este host nao retornou resposta ao monitoramento.\n"
                f"{monitor.get('detalhe') or 'Sem resposta do equipamento.'}"
            )

        return ip_ou_host, monitor_label, monitor_status, monitor_tooltip

    def _carregar_preferencias(self):
        self._saved_preferences = get_widget_preferences(self.usuario, "maquinas")

    def _aplicar_preferencias_salvas(self):
        self._restoring_preferences = True
        try:
            self.pesquisa_edit.setText(str(self._saved_preferences.get("busca") or ""))
            apply_combo_data(self.empresa_filter, self._saved_preferences.get("empresa"))
            apply_combo_text(self.departamento_filter, self._saved_preferences.get("departamento"))
            apply_combo_text(self.status_filter, self._saved_preferences.get("status"))
            apply_combo_text(self.rede_filter, self._saved_preferences.get("rede"))
        finally:
            self._restoring_preferences = False

    def _preferencias_atuais(self):
        return {
            "busca": self.pesquisa_edit.text().strip(),
            "empresa": self.empresa_filter.currentData(),
            "departamento": self.departamento_filter.currentText(),
            "status": self.status_filter.currentText(),
            "rede": self.rede_filter.currentText(),
            "sort": get_table_sort_state(self.tabela),
            "widths": get_table_column_widths(self.tabela),
        }

    def _salvar_preferencias(self):
        if self._restoring_preferences:
            return
        self._saved_preferences = self._preferencias_atuais()
        save_widget_preferences(self.usuario, "maquinas", self._saved_preferences)

    def _ao_ordenar_tabela(self, *_args):
        self._salvar_preferencias()

    def _ao_redimensionar_coluna(self, *_args):
        self._salvar_preferencias()

    def _mostrar_prompt_empresa(self):
        self.maquinas = []
        self._visible_maquinas = []
        self.dados_cache = []
        self.monitoramento_status = {}
        self.lan_status = {"links": [], "resumo": {}}
        self.tabela.setRowCount(0)
        self.empresa_prompt.setVisible(True)
        self.monitoramento_label.setText("Selecione uma empresa para iniciar o monitoramento de rede.")
        self._set_summary_value("total", 0)
        self._set_summary_value("online", 0)
        self._set_summary_value("atencao", 0)
        self._set_summary_value("manutencao", 0)
        self._set_detail_empty()

    def ao_alterar_empresa(self):
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            self._salvar_preferencias()
            return
        self.carregar_maquinas()
        self._salvar_preferencias()

    def carregar_departamentos(self):
        """Carrega a lista de departamentos do backend para o filtro"""
        try:
            departamento_atual = self.departamento_filter.currentText()
            self.departamentos = api_client.get_departamentos_lista()
            self.departamento_filter.clear()
            self.departamento_filter.addItem("Todos os departamentos")

            for dept in self.departamentos:
                if dept and dept.strip():
                    self.departamento_filter.addItem(dept)

            print(f"✅ Departamentos carregados: {len(self.departamentos)}")
        except Exception as e:
            print(f"❌ Erro ao carregar departamentos: {e}")

    def carregar_empresas(self):
        """Carrega a lista de empresas do backend"""
        try:
            self.empresas = api_client.get_empresas()
            populate_company_filter(self.empresa_filter, self.empresas)
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")

    def carregar_maquinas(self):
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        try:
            self.maquinas = api_client.listar_maquinas(empresa=self.empresa_param())
            self.dados_cache = self.maquinas.copy()
            self._carregar_status_monitoramento()
            self.filtrar_maquinas()
            self.empresa_prompt.setVisible(False)
            print(f"✅ Máquinas carregadas: {len(self.maquinas)}")
        except Exception as e:
            print(f"❌ Erro ao carregar máquinas: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar máquinas: {e}")

    def _carregar_status_monitoramento(self):
        if not self.empresa_pronta():
            self.monitoramento_status = {}
            self.lan_status = {"links": [], "resumo": {}}
            self.monitoramento_label.setText("Selecione uma empresa para iniciar o monitoramento de rede.")
            return

        status_list = api_client.listar_status_maquinas_monitoramento(empresa=self.empresa_param())
        self.lan_status = api_client.get_status_lan_to_lan(self.usuario.get("empresa"))
        self.monitoramento_status = {item.get("id"): item for item in status_list}

        if not status_list:
            self.monitoramento_label.setText("Nenhuma máquina encontrada para monitoramento nesta seleção.")
            return

        online = sum(1 for item in status_list if item.get("monitor_status") == "online")
        offline = sum(1 for item in status_list if item.get("monitor_status") == "offline")
        pendentes = sum(1 for item in status_list if item.get("monitor_status") == "nao_configurado")
        erros = sum(1 for item in status_list if item.get("monitor_status") == "erro")

        resumo = [f"{online} online", f"{offline} offline"]
        if pendentes:
            resumo.append(f"{pendentes} sem alvo")
        if erros:
            resumo.append(f"{erros} com erro")

        lan_resumo = self.lan_status.get("resumo") or {}
        if lan_resumo.get("offline"):
            resumo.append(f"{lan_resumo.get('offline')} rota(s) offline")
        if lan_resumo.get("erro"):
            resumo.append(f"{lan_resumo.get('erro')} rota(s) com erro")

        empresa_selecionada = self._empresa_normalizada(self.empresa_param())
        rota_empresa = self._rota_para_empresa(empresa_selecionada)
        if rota_empresa and rota_empresa.get("status") != "online":
            resumo.append(f"rota para {empresa_selecionada} indisponivel")

        self.monitoramento_label.setText("Monitoramento de rede local: " + " | ".join(resumo))

    def atualizar_monitoramento_rede(self, show_feedback=False):
        if not self._loaded or not self.empresa_pronta():
            return

        try:
            self._carregar_status_monitoramento()
            self.filtrar_maquinas()
            if show_feedback:
                notification_manager.success("Monitoramento das maquinas atualizado.", self.window(), 2500)
        except Exception as e:
            print(f"Erro ao atualizar monitoramento das maquinas: {e}")
            self.monitoramento_label.setText("Não foi possível atualizar o monitoramento de rede nesta tentativa.")
            if show_feedback:
                notification_manager.error("Não foi possível atualizar o monitoramento das máquinas.", self.window(), 3000)

    def filtrar_maquinas(self):
        if not self.empresa_pronta():
            self._mostrar_prompt_empresa()
            return

        search_text = self.pesquisa_edit.text()
        empresa = self.empresa_filter.currentText()
        departamento = self.departamento_filter.currentText()
        status = self.status_filter.currentText()
        rede = self.rede_filter.currentText()

        filtered = []
        for maquina in self.dados_cache:
            _ip_ou_host, monitor_label, monitor_status, _monitor_tooltip = self._resolve_monitoramento_visual(maquina)

            # Filtro por status
            if not is_all_option(status) and not same_filter_value(maquina.get("status", ""), status):
                continue

            # Filtro por empresa
            if self.empresa_param() is None and not is_all_option(empresa) and not same_text(maquina.get("empresa"), empresa):
                continue

            # Filtro por departamento
            if not is_all_option(departamento) and not same_text(maquina.get("departamento"), departamento):
                continue

            if not self._match_rede_filter(rede, monitor_label, monitor_status):
                continue

            # Filtro por pesquisa (nome, modelo, IP/host, MAC)
            if contains_text(
                search_text,
                maquina.get("nome", ""),
                maquina.get("modelo", ""),
                maquina.get("ip_address", ""),
                maquina.get("mac_address", ""),
                monitor_label,
            ):
                filtered.append(maquina)

        self.atualizar_tabela(filtered)
        self._salvar_preferencias()

    def _atualizar_resumo(self, maquinas):
        total = len(maquinas)
        online = 0
        atencao = 0
        manutencao = 0

        for maquina in maquinas:
            _, _, monitor_status, _ = self._resolve_monitoramento_visual(maquina)
            if monitor_status == "online":
                online += 1
            elif monitor_status in {"sem_resposta", "sem_rota", "rota_com_erro", "nao_configurado", "erro", "offline"}:
                atencao += 1

            if str(maquina.get("status", "")).strip().lower() == "manutencao":
                manutencao += 1

        self._set_summary_value("total", total)
        self._set_summary_value("online", online)
        self._set_summary_value("atencao", atencao)
        self._set_summary_value("manutencao", manutencao)

    def _match_rede_filter(self, selected_value, monitor_label, monitor_status):
        if is_all_option(selected_value):
            return True

        normalized = str(selected_value or "").strip().lower()
        monitor_label_normalized = str(monitor_label or "").strip().lower()
        monitor_status_normalized = str(monitor_status or "").strip().lower()

        if normalized == "online":
            return monitor_status_normalized == "online"
        if normalized == "sem resposta":
            return monitor_status_normalized in {"sem_resposta", "offline"}
        if normalized == "sem rota":
            return monitor_status_normalized == "sem_rota"
        if normalized == "rota com erro":
            return monitor_status_normalized == "rota_com_erro"
        if normalized == "sem alvo":
            return monitor_status_normalized == "nao_configurado"
        if normalized == "com erro":
            return monitor_status_normalized == "erro"

        return monitor_label_normalized == normalized

    def _update_detail_from_selection(self):
        if self.tabela.rowCount() == 0:
            self._set_detail_empty()
            return

        current_row = self.tabela.currentRow()
        if current_row < 0:
            self._set_detail_empty()
            return

        id_item = self.tabela.item(current_row, 0)
        if id_item is None:
            self._set_detail_empty()
            return

        try:
            maquina_id = int(id_item.text())
        except Exception:
            self._set_detail_empty()
            return

        maquina = next((item for item in self._visible_maquinas if item.get("id") == maquina_id), None)
        if not maquina:
            self._set_detail_empty()
            return

        ip_ou_host, monitor_label, _monitor_status, monitor_tooltip = self._resolve_monitoramento_visual(maquina)
        self.detail_body.setText(self._build_detail_text(maquina, monitor_label, monitor_tooltip, ip_ou_host))
        if hasattr(self, "detail_copy_btn"):
            self.detail_copy_btn.setEnabled(bool(ip_ou_host and ip_ou_host != "-"))
        if hasattr(self, "detail_edit_btn"):
            self.detail_edit_btn.setEnabled(True)

    def _atualizar_tabela_legado(self, maquinas):
        self.tabela.setRowCount(len(maquinas))

        status_colors = {
            "ativo": QColor(42, 157, 143),
            "manutencao": QColor(233, 196, 106),
            "inativo": QColor(231, 111, 81)
        }

        for row, maquina in enumerate(maquinas):
            self.tabela.setItem(row, 0, number_item(maquina.get("id", "")))
            self.tabela.setItem(row, 1, QTableWidgetItem(maquina.get("nome", "")))
            self.tabela.setItem(row, 2, QTableWidgetItem(maquina.get("modelo", "-")))

            # Coluna Endereço MAC
            mac = maquina.get("mac_address", "")
            self.tabela.setItem(row, 3, QTableWidgetItem(mac if mac else "-"))

            self.tabela.setItem(row, 4, QTableWidgetItem(maquina.get("empresa", "-")))
            self.tabela.setItem(row, 5, QTableWidgetItem(maquina.get("departamento", "-")))

            status_item = QTableWidgetItem(maquina.get("status", "ativo").upper())
            status_color = status_colors.get(maquina.get("status", "ativo"), QColor(0, 0, 0))
            status_item.setForeground(status_color)
            self.tabela.setItem(row, 6, status_item)

            self.tabela.setItem(row, 7, QTableWidgetItem(maquina.get("observacoes", "-")[:50]))

        apply_table_sort_state(self.tabela, self._saved_preferences.get("sort"))
        refresh_data_table_layout(self.tabela)
        self._atualizar_resumo(maquinas)
        if maquinas:
            self.tabela.setCurrentCell(0, 0)
        else:
            self._set_detail_empty()

    def atualizar_tabela(self, maquinas):
        self._visible_maquinas = list(maquinas)
        sorting_enabled = self.tabela.isSortingEnabled()
        self.tabela.setSortingEnabled(False)
        self.tabela.clearContents()
        self.tabela.setRowCount(len(maquinas))

        status_colors = {
            "ativo": QColor(42, 157, 143),
            "manutencao": QColor(233, 196, 106),
            "inativo": QColor(231, 111, 81),
        }
        monitor_colors = {
            "online": QColor(34, 197, 94),
            "offline": QColor(239, 68, 68),
            "erro": QColor(245, 158, 11),
            "nao_configurado": QColor(148, 163, 184),
            "sem_resposta": QColor(239, 68, 68),
            "sem_rota": QColor(239, 68, 68),
            "rota_com_erro": QColor(245, 158, 11),
        }

        for row, maquina in enumerate(maquinas):
            ip_ou_host, monitor_label, monitor_status, monitor_tooltip = self._resolve_monitoramento_visual(maquina)
            monitor_color = monitor_colors.get(monitor_status, QColor(148, 163, 184))

            self.tabela.setItem(row, 0, number_item(maquina.get("id", "")))
            self.tabela.setItem(row, 1, QTableWidgetItem(maquina.get("nome", "")))
            self.tabela.setItem(row, 2, QTableWidgetItem(maquina.get("modelo", "-")))
            self.tabela.setItem(row, 3, QTableWidgetItem(ip_ou_host))

            mac = maquina.get("mac_address", "")
            self.tabela.setItem(row, 4, QTableWidgetItem(mac if mac else "-"))
            self.tabela.setItem(row, 5, QTableWidgetItem(maquina.get("empresa", "-")))
            self.tabela.setItem(row, 6, QTableWidgetItem(maquina.get("departamento", "-")))

            monitor_item = QTableWidgetItem(monitor_label)
            monitor_item.setForeground(monitor_color)
            monitor_item.setToolTip(monitor_tooltip)
            self.tabela.setItem(row, 7, monitor_item)

            status_item = QTableWidgetItem(maquina.get("status", "ativo").upper())
            status_color = status_colors.get(maquina.get("status", "ativo"), QColor(0, 0, 0))
            status_item.setForeground(status_color)
            self.tabela.setItem(row, 8, status_item)

            observacoes = maquina.get("observacoes") or "-"
            observacao_item = QTableWidgetItem(observacoes[:80] if observacoes != "-" else "-")
            if observacoes != "-":
                observacao_item.setToolTip(observacoes)
            self.tabela.setItem(row, 9, observacao_item)

        if sorting_enabled:
            self.tabela.setSortingEnabled(True)

        apply_table_sort_state(self.tabela, self._saved_preferences.get("sort"))
        refresh_data_table_layout(self.tabela)
        apply_table_column_widths(self.tabela, self._saved_preferences.get("widths"))
        self._atualizar_resumo(maquinas)
        if maquinas:
            self.tabela.setCurrentCell(0, 0)
        else:
            self._set_detail_empty()

    def nova_maquina(self):
        if not self._pode("maquinas.create"):
            self._avisar_sem_permissao("maquinas.create")
            return
        dialog = MaquinaDialog(item_data=None, parent=self)
        if dialog.exec():
            self.carregar_maquinas()
            self.carregar_departamentos()
            self.carregar_empresas()

    def editar_maquina(self):
        if not self._pode("maquinas.edit"):
            self._avisar_sem_permissao("maquinas.edit")
            return
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma máquina para editar")
            return

        maquina_id = int(self.tabela.item(current_row, 0).text())
        maquina = next((m for m in self.maquinas if m["id"] == maquina_id), None)

        if maquina:
            dialog = MaquinaDialog(item_data=maquina, parent=self)
            if dialog.exec():
                self.carregar_maquinas()
                self.carregar_departamentos()
                self.carregar_empresas()

    def deletar_maquina(self):
        if not self._pode("maquinas.delete"):
            self._avisar_sem_permissao("maquinas.delete")
            return
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma máquina para deletar")
            return

        maquina_id = int(self.tabela.item(current_row, 0).text())
        maquina_nome = self.tabela.item(current_row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar a máquina '{maquina_nome}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                success = api_client.deletar_maquina(maquina_id)
                QApplication.restoreOverrideCursor()

                if success:
                    notification_manager.success("Máquina deletada com sucesso!", self.window(), 3000)
                    self.carregar_maquinas()
                    self.carregar_departamentos()
                    self.carregar_empresas()
                else:
                    notification_manager.error("Erro ao deletar máquina", self.window(), 3000)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Erro", f"Erro ao deletar: {e}")


# CLASSE DO DIALOG COM CAMPO MAC
class MaquinaDialog(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.dados_item = item_data
        self.setWindowTitle("Cadastro de Máquina" if not item_data else "Editar Máquina")
        self.setModal(True)
        self.setMinimumWidth(500)

        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        self.init_ui()

        if item_data:
            self.carregar_dados_edicao()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        layout.addWidget(required_hint_label())

        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Ex: PC Administrativo 01")
        form_layout.addRow(required_label("Nome da Máquina:"), self.nome_edit)

        self.modelo_edit = QLineEdit()
        self.modelo_edit.setPlaceholderText("Ex: Dell Optiplex 3080")
        form_layout.addRow(optional_label("Modelo:"), self.modelo_edit)

        # NOVO: Campo Endereço MAC
        self.mac_edit = QLineEdit()
        self.mac_edit.setPlaceholderText("Ex: 00:1A:2B:3C:4D:5E")
        self.mac_edit.setMaxLength(17)
        form_layout.addRow(optional_label("Endereço MAC:"), self.mac_edit)

        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("Ex: 10.1.1.25 ou pc-rh-01")
        form_layout.addRow(optional_label("IP/Host:"), self.ip_edit)

        self.empresa_combo = QComboBox()
        self.empresa_combo.setEditable(False)
        self.empresa_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_empresas_combo()
        form_layout.addRow(required_label("Empresa:"), self.empresa_combo)


        self.departamento_combo = QComboBox()
        self.departamento_combo.setEditable(False)
        self.departamento_combo.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_departamentos_combo()
        form_layout.addRow(required_label("Departamento:"), self.departamento_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["ativo", "manutencao", "inativo"])
        form_layout.addRow(required_label("Status:"), self.status_combo)

        self.observacoes_edit = QTextEdit()
        self.observacoes_edit.setMaximumHeight(80)
        self.observacoes_edit.setPlaceholderText("Observações adicionais...")
        form_layout.addRow(optional_label("Observações:"), self.observacoes_edit)

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
        """Carrega empresas do backend para o combo"""
        try:
            empresas = api_client.get_empresas()
            self.empresa_combo.clear()
            for emp in empresas:
                self.empresa_combo.addItem(emp)
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")
            self.empresa_combo.addItems(["Matriz", "Filial 1", "Filial 2", "Filial 3"])

    def carregar_departamentos_combo(self):
        """Carrega os departamentos do backend para o combobox"""
        try:
            departamentos = api_client.get_departamentos_lista()
            self.departamento_combo.clear()
            for dept in departamentos:
                if dept and dept.strip():
                    self.departamento_combo.addItem(dept)
        except Exception as e:
            print(f"❌ Erro ao carregar departamentos: {e}")
            # Fallback em caso de erro
            default_depts = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"]
            for dept in default_depts:
                self.departamento_combo.addItem(dept)

    def carregar_dados_edicao(self):
        """Carrega os dados do item para edição"""
        if self.dados_item is None:
            return

        self.nome_edit.setText(str(self.dados_item.get("nome", "")))
        self.modelo_edit.setText(str(self.dados_item.get("modelo", "")))

        # NOVO: Carregar MAC
        mac = str(self.dados_item.get("mac_address", ""))
        self.mac_edit.setText(mac if mac != "None" else "")

        ip_address = str(self.dados_item.get("ip_address", ""))
        self.ip_edit.setText(ip_address if ip_address != "None" else "")

        empresa = str(self.dados_item.get("empresa", ""))
        idx = self.empresa_combo.findText(empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)

        departamento = str(self.dados_item.get("departamento", ""))
        idx = self.departamento_combo.findText(departamento)
        if idx >= 0:
            self.departamento_combo.setCurrentIndex(idx)

        status = str(self.dados_item.get("status", "ativo"))
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        self.observacoes_edit.setPlainText(str(self.dados_item.get("observacoes", "")))

    def salvar(self):
        dados = {
            "nome": self.nome_edit.text().strip(),
            "modelo": self.modelo_edit.text().strip() or None,
            "mac_address": self.mac_edit.text().strip() or None,  # NOVO
            "ip_address": self.ip_edit.text().strip() or None,
            "empresa": self.empresa_combo.currentText(),
            "departamento": self.departamento_combo.currentText(),
            "status": self.status_combo.currentText(),
            "observacoes": self.observacoes_edit.toPlainText().strip() or None
        }

        if not dados["nome"]:
            focus_invalid_field(self.nome_edit)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Nome da Máquina"))
            return

        if not dados["empresa"]:
            focus_invalid_field(self.empresa_combo)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Empresa"))
            return

        if not dados["departamento"]:
            focus_invalid_field(self.departamento_combo)
            QMessageBox.warning(self, "Campo obrigatorio", required_field_message("Departamento"))
            return

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

            if self.dados_item:
                response = api_client.atualizar_maquina(self.dados_item["id"], dados)
                if response and response.get("id"):
                    QMessageBox.information(self, "Sucesso", f"Maquina '{dados['nome']}' atualizada com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível atualizar a máquina. Revise os dados e tente novamente.")
            else:
                response = api_client.criar_maquina(dados)
                if response and response.get("id"):
                    QMessageBox.information(self, "Sucesso", f"Maquina '{dados['nome']}' criada com sucesso.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível criar a máquina. Revise os dados e tente novamente.")

            QApplication.restoreOverrideCursor()

        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar a máquina.\n\nDetalhes: {e}")
