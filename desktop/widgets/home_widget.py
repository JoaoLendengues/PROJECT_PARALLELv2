from datetime import datetime

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from access_control import get_role_label, has_screen_access
from api_client import api_client
from version import get_release_date, get_version


class ClickableCard(QFrame):
    def __init__(self, callback=None, parent=None):
        super().__init__(parent)
        self._callback = callback
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and callable(self._callback):
            self._callback()
        super().mousePressEvent(event)


class MetricWaveDecoration(QWidget):
    def __init__(self, accent="#3b82f6", wide=False, parent=None):
        super().__init__(parent)
        self.accent = accent
        self.card_background = "#111827"
        self.wide = wide
        self.dark_mode = True
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFixedSize(178 if wide else 126, 82 if wide else 68)

    def set_visuals(self, accent, card_background, dark_mode):
        self.accent = accent or self.accent
        self.card_background = card_background or self.card_background
        self.dark_mode = bool(dark_mode)
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(1, 3, -1, -2)
        width = rect.width()
        height = rect.height()
        color = QColor(self.accent)

        fill_gradient = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        top_fill = QColor(color)
        bottom_fill = QColor(color)
        top_fill.setAlpha(12 if self.dark_mode else 18)
        bottom_fill.setAlpha(72 if self.dark_mode else 42)
        fill_gradient.setColorAt(0.0, top_fill)
        fill_gradient.setColorAt(0.55, bottom_fill)
        fill_gradient.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))

        primary = QPainterPath()
        primary.moveTo(rect.left() - width * 0.14, rect.bottom() - height * 0.18)
        if self.wide:
            primary.cubicTo(
                rect.left() + width * 0.10,
                rect.bottom() - height * 0.04,
                rect.left() + width * 0.30,
                rect.top() + height * 0.72,
                rect.left() + width * 0.52,
                rect.top() + height * 0.62,
            )
            primary.cubicTo(
                rect.left() + width * 0.68,
                rect.top() + height * 0.56,
                rect.left() + width * 0.82,
                rect.top() + height * 0.20,
                rect.right() + width * 0.06,
                rect.top() + height * 0.40,
            )
        else:
            primary.cubicTo(
                rect.left() + width * 0.12,
                rect.bottom() - height * 0.04,
                rect.left() + width * 0.34,
                rect.top() + height * 0.82,
                rect.left() + width * 0.54,
                rect.top() + height * 0.64,
            )
            primary.cubicTo(
                rect.left() + width * 0.74,
                rect.top() + height * 0.48,
                rect.left() + width * 0.88,
                rect.top() + height * 0.10,
                rect.right() + width * 0.08,
                rect.top() + height * 0.28,
            )

        area = QPainterPath(primary)
        area.lineTo(rect.right() + 2, rect.bottom() + 2)
        area.lineTo(rect.left() - 2, rect.bottom() + 2)
        area.closeSubpath()

        painter.fillPath(area, fill_gradient)

        main_pen = QPen(QColor(color.red(), color.green(), color.blue(), 168 if self.dark_mode else 122))
        main_pen.setWidthF(2.2 if self.wide else 1.9)
        painter.setPen(main_pen)
        painter.drawPath(primary)

        secondary = QPainterPath()
        secondary.moveTo(rect.left() - width * 0.10, rect.bottom() - height * 0.02)
        secondary.cubicTo(
            rect.left() + width * 0.20,
            rect.bottom() - height * 0.12,
            rect.left() + width * 0.44,
            rect.top() + height * 0.76,
            rect.left() + width * 0.68,
            rect.top() + height * 0.70,
        )
        secondary.cubicTo(
            rect.left() + width * 0.84,
            rect.top() + height * 0.66,
            rect.left() + width * 0.94,
            rect.top() + height * 0.34,
            rect.right() + width * 0.08,
            rect.top() + height * 0.52,
        )

        soft_pen = QPen(QColor(color.red(), color.green(), color.blue(), 74 if self.dark_mode else 52))
        soft_pen.setWidthF(1.2)
        painter.setPen(soft_pen)
        painter.drawPath(secondary)

        dot_color = QColor(color)
        dot_color.setAlpha(210 if self.dark_mode else 180)
        painter.setPen(Qt.NoPen)
        painter.setBrush(dot_color)
        dot_x = rect.right() - width * 0.12
        dot_y = rect.top() + height * (0.28 if self.wide else 0.22)
        painter.drawEllipse(int(dot_x), int(dot_y), 6, 6)


class NetworkPulseDecoration(QWidget):
    def __init__(self, accent="#22c55e", parent=None):
        super().__init__(parent)
        self.accent = accent
        self.dark_mode = True
        self.card_background = "#111827"
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFixedSize(134, 134)

    def set_visuals(self, accent, card_background, dark_mode):
        self.accent = accent or self.accent
        self.card_background = card_background or self.card_background
        self.dark_mode = bool(dark_mode)
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(4, 4, -4, -4)
        center = rect.center()
        accent = QColor(self.accent)

        for radius, alpha in ((52, 48), (38, 68), (24, 92)):
            pen = QPen(QColor(accent.red(), accent.green(), accent.blue(), alpha if self.dark_mode else alpha - 10))
            pen.setWidthF(1.1)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, radius, radius)

        halo = QRadialGradient(center, 24)
        glow = QColor(accent)
        glow.setAlpha(120 if self.dark_mode else 96)
        halo.setColorAt(0.0, glow)
        halo.setColorAt(0.55, QColor(accent.red(), accent.green(), accent.blue(), 40))
        halo.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(center, 24, 24)

        core = QRadialGradient(center, 11)
        core.setColorAt(0.0, QColor(255, 255, 255, 235))
        core.setColorAt(0.38, QColor(accent.red(), accent.green(), accent.blue(), 230))
        core.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 88))
        painter.setBrush(core)
        painter.drawEllipse(center, 11, 11)


class HomeWidget(QWidget):
    CARD_CONFIGS = (
        {
            "name": "internet",
            "screen": None,
            "eyebrow": "REDE LOCAL",
            "title": "Status da Rede Local",
            "accent": "#22c55e",
            "cta": "Atualizar painel",
            "action": "atualizar_status_internet",
            "featured": True,
        },
        {
            "name": "materiais",
            "screen": "materiais",
            "eyebrow": "ESTOQUE",
            "title": "Materiais em Estoque",
            "accent": "#3b82f6",
            "cta": "Abrir materiais",
            "action": "show_materiais",
        },
        {
            "name": "maquinas",
            "screen": "maquinas",
            "eyebrow": "OPERACAO",
            "title": "Maquinas Ativas",
            "accent": "#10b981",
            "cta": "Abrir maquinas",
            "action": "show_maquinas",
        },
        {
            "name": "manutencoes",
            "screen": "manutencoes",
            "eyebrow": "SUPORTE",
            "title": "Manutencoes Pendentes",
            "accent": "#f59e0b",
            "cta": "Abrir manutencoes",
            "action": "show_manutencoes",
        },
        {
            "name": "pedidos",
            "screen": "pedidos",
            "eyebrow": "COMPRAS",
            "title": "Pedidos Pendentes",
            "accent": "#8b5cf6",
            "cta": "Abrir pedidos",
            "action": "show_pedidos",
        },
        {
            "name": "demandas",
            "screen": "demandas",
            "eyebrow": "ATENDIMENTO",
            "title": "Demandas Abertas",
            "accent": "#ef4444",
            "cta": "Abrir demandas",
            "action": "show_demandas",
            "wide": True,
        },
    )

    def __init__(self):
        super().__init__()
        self.usuario_nome = None
        self.usuario_context = {}
        self.main_window = None
        self.metric_cards = {}
        self.internet_card_data = {}
        self.technical_cards = {}
        self.lan_cards = {}
        self.last_internet_refresh = None
        self.last_technical_refresh = None
        self._applying_theme_styles = False

        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)

        self.timer_internet = QTimer(self)
        self.timer_internet.timeout.connect(self.atualizar_monitoramento_tecnico)
        self.timer_internet.start(30000)

        self.update_datetime()

    def set_usuario(self, nome):
        self.usuario_nome = nome
        self.update_saudacao()

    def set_usuario_context(self, usuario):
        self.usuario_context = usuario or {}
        self.role_value_label.setText(get_role_label(self.usuario_context.get("nivel_acesso")))
        self._rebuild_lan_cards()
        self._rebuild_cards()

    def set_main_window(self, main_window):
        self.main_window = main_window

    def init_ui(self):
        self.setObjectName("homeRoot")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("homeScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.content = QWidget()
        self.content.setObjectName("homeContent")
        self.scroll_area.setWidget(self.content)
        root_layout.addWidget(self.scroll_area)

        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(28, 28, 28, 28)
        self.content_layout.setSpacing(22)

        self.header_frame = QFrame()
        self.header_frame.setObjectName("homeHeaderFrame")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)

        header_text_layout = QVBoxLayout()
        header_text_layout.setContentsMargins(0, 0, 0, 0)
        header_text_layout.setSpacing(8)

        self.saudacao_label = QLabel()
        self.saudacao_label.setObjectName("homeGreeting")
        self.saudacao_label.setFont(QFont("Segoe UI", 25, QFont.Weight.Bold))
        header_text_layout.addWidget(self.saudacao_label)

        self.data_hora_label = QLabel()
        self.data_hora_label.setObjectName("homeTimestamp")
        header_text_layout.addWidget(self.data_hora_label)

        self.context_label = QLabel(
            "Painel principal com acompanhamento de estoque, operacao, compras, suporte e rede local."
        )
        self.context_label.setObjectName("homeContext")
        self.context_label.setWordWrap(True)
        header_text_layout.addWidget(self.context_label)

        header_layout.addLayout(header_text_layout, 1)

        self.role_chip = QFrame()
        self.role_chip.setObjectName("homeRoleChip")
        role_layout = QVBoxLayout(self.role_chip)
        role_layout.setContentsMargins(16, 12, 16, 12)
        role_layout.setSpacing(4)

        role_label = QLabel("Perfil atual")
        role_label.setObjectName("homeRoleLabel")
        role_layout.addWidget(role_label)

        self.role_value_label = QLabel("Usuario")
        self.role_value_label.setObjectName("homeRoleValue")
        role_layout.addWidget(self.role_value_label)

        header_layout.addWidget(self.role_chip, 0, Qt.AlignTop)
        self.content_layout.addWidget(self.header_frame)

        self.cards_layout = QGridLayout()
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setHorizontalSpacing(18)
        self.cards_layout.setVerticalSpacing(18)
        self.cards_layout.setColumnStretch(0, 1)
        self.cards_layout.setColumnStretch(1, 1)
        self.content_layout.addLayout(self.cards_layout)

        self.technical_panel = self._create_technical_panel()
        self.content_layout.addWidget(self.technical_panel)
        self.lan_panel = self._create_lan_panel()
        self.content_layout.addWidget(self.lan_panel)
        self.content_layout.addStretch()

        self._apply_theme_styles()
        self._rebuild_cards()

    def on_show(self):
        self._apply_theme_styles()
        self.update_datetime()
        self.carregar_dados()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_theme_styles()

    def changeEvent(self, event):
        super().changeEvent(event)
        if self._applying_theme_styles:
            return
        if event.type() in (QEvent.StyleChange, QEvent.PaletteChange, QEvent.ApplicationPaletteChange):
            QTimer.singleShot(0, self._apply_theme_styles)

    def update_datetime(self):
        now = datetime.now()
        dias_semana = [
            "Segunda-feira",
            "Terca-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sabado",
            "Domingo",
        ]
        meses = [
            "janeiro",
            "fevereiro",
            "marco",
            "abril",
            "maio",
            "junho",
            "julho",
            "agosto",
            "setembro",
            "outubro",
            "novembro",
            "dezembro",
        ]

        dia_semana = dias_semana[now.weekday()]
        dia = now.day
        mes = meses[now.month - 1]
        ano = now.year
        hora = now.strftime("%H:%M")

        self.data_hora_label.setText(f"{dia_semana}, {dia} de {mes} de {ano} - {hora}")
        self.update_saudacao()

    def update_saudacao(self):
        hora = datetime.now().hour
        if hora < 12:
            saudacao = "Bom dia"
        elif hora < 18:
            saudacao = "Boa tarde"
        else:
            saudacao = "Boa noite"

        if self.usuario_nome:
            self.saudacao_label.setText(f"{saudacao}, {self.usuario_nome}!")
        else:
            self.saudacao_label.setText(f"{saudacao}!")

    def executar_acao(self, acao):
        if acao == "atualizar_status_internet":
            self.atualizar_monitoramento_tecnico(show_feedback=True)
            return

        if self.main_window and hasattr(self.main_window, acao):
            getattr(self.main_window, acao)()

    def carregar_dados(self):
        try:
            dados = api_client.get_dashboard_resumo()
            resumo = dados.get("resumo", {})
        except Exception as exc:
            print(f"Erro ao carregar dashboard: {exc}")
            resumo = {}

        for config in self.CARD_CONFIGS:
            if config["name"] == "internet":
                continue
            if config["name"] not in self.metric_cards:
                continue
            self._apply_metric_data(config["name"], resumo)

        self.atualizar_monitoramento_tecnico()

    def atualizar_monitoramento_tecnico(self, show_feedback=False):
        network_status = self.atualizar_status_internet(show_feedback=show_feedback)
        self.atualizar_painel_tecnico(network_status)

    def atualizar_status_internet(self, show_feedback=False):
        try:
            status = api_client.get_status_internet(self.usuario_context.get("empresa"))
        except Exception as exc:
            print(f"Erro ao atualizar status da rede local: {exc}")
            status = {"status": "erro", "qualidade": "erro", "latencia_ms": None, "servidor": "Falha na medicao"}

        self.last_internet_refresh = datetime.now()
        if not self.internet_card_data:
            return status

        palette = self._theme_palette()
        quality = str(status.get("qualidade", "erro")).lower()
        online = status.get("status") == "online"
        accent = status.get("cor") or "#22c55e"
        server = status.get("servidor") or "Rede local"

        if online:
            quality_map = {
                "excelente": ("Excelente", "Conexao local muito estavel.", "good", "OK"),
                "bom": ("Boa", "Resposta consistente para uso diario.", "info", "ON"),
                "regular": ("Regular", "Existe oscilacao leve na resposta.", "warn", "AT"),
                "ruim": ("Instavel", "A rede esta respondendo com lentidao.", "critical", "BX"),
            }
            value_text, detail_text, tone, orb_text = quality_map.get(
                quality, ("Online", "Conexao local disponivel.", "good", "ON")
            )
            latency = status.get("latencia_ms")
            latency_text = f"Latencia local: {latency} ms" if latency is not None else "Latencia local indisponivel"
            badge_text = "Online"
        elif status.get("status") == "offline":
            value_text = "Offline"
            detail_text = "A base local nao respondeu dentro do tempo esperado."
            tone = "critical"
            orb_text = "OFF"
            latency_text = "Sem resposta da rede local"
            badge_text = "Sem conexao"
            accent = "#ef4444"
        else:
            value_text = "Erro"
            detail_text = "Nao foi possivel validar a conectividade neste momento."
            tone = "critical"
            orb_text = "ERR"
            latency_text = "Falha ao medir a latencia"
            badge_text = "Falha"
            accent = "#ef4444"

        updated_at = self.last_internet_refresh.strftime("%H:%M")
        self.internet_card_data["status"].setText(value_text)
        self.internet_card_data["latency"].setText(latency_text)
        self.internet_card_data["server"].setText(server)
        self.internet_card_data["detail"].setText(detail_text)
        self.internet_card_data["updated"].setText(f"Atualizado as {updated_at}")
        self.internet_card_data["orb"].setText(orb_text)
        self.internet_card_data["current_accent"] = accent

        badge_bg, badge_fg = self._tone_colors(tone, palette)
        self.internet_card_data["badge"].setText(badge_text)
        self.internet_card_data["badge"].setStyleSheet(self._build_badge_style(badge_bg, badge_fg))
        self.internet_card_data["status"].setStyleSheet(
            f"color: {accent}; font-size: 34px; font-weight: 800; background: transparent;"
        )
        self.internet_card_data["orb"].setStyleSheet(
            self._build_orb_style(accent, palette["card_bg"], palette["text_primary"])
        )
        self.internet_card_data["pulse"].set_visuals(accent, palette["card_bg"], self._is_dark_theme())
        self.internet_card_data["accent"].setStyleSheet(
            f"background-color: {accent}; border-top-left-radius: 22px; border-top-right-radius: 22px;"
        )
        self.internet_card_data["pill"].setStyleSheet(self._build_pill_style(accent, palette))
        self.internet_card_data["cta"].setStyleSheet(
            f"color: {accent}; font-size: 13px; font-weight: 600; background: transparent;"
        )

        if show_feedback:
            from widgets.toast_notification import notification_manager

            if online:
                notification_manager.success(
                    f"Rede local atualizada: {value_text.lower()}",
                    self.window(),
                    2500,
                )
            else:
                notification_manager.error(
                    "Nao foi possivel confirmar a conectividade local.",
                    self.window(),
                    3000,
                )

        return status

    def atualizar_painel_tecnico(self, network_status=None):
        palette = self._theme_palette()
        self.last_technical_refresh = datetime.now()

        if not self.technical_cards:
            return

        health = api_client.get_health_status()
        api_online = str(health.get("status", "")).lower() == "healthy"
        db_connected = str(health.get("database", "")).lower() == "connected"
        pool_status = health.get("pool_status") or {}

        api_value = "Online" if api_online else "Offline"
        api_meta = api_client.base_url
        if api_online and health.get("timestamp"):
            api_meta = f"{api_client.base_url} - leitura normal"
        elif health.get("error"):
            api_meta = str(health.get("error"))
        self._set_technical_card_state(
            "api",
            api_value,
            api_meta,
            "Saudavel" if api_online else "Falha",
            "good" if api_online else "critical",
            "#22c55e" if api_online else "#ef4444",
        )

        db_value = "Conectado" if db_connected else "Desconectado"
        if db_connected:
            db_meta = (
                f"Pool {pool_status.get('pool_size', 0)} · "
                f"em uso {pool_status.get('checked_out', 0)} · "
                f"livres {pool_status.get('checked_in', 0)}"
            )
        else:
            db_meta = str(health.get("error") or "Nao houve resposta do banco.")
        self._set_technical_card_state(
            "database",
            db_value,
            db_meta,
            "Disponivel" if db_connected else "Offline",
            "good" if db_connected else "critical",
            "#10b981" if db_connected else "#ef4444",
        )

        if network_status is None:
            network_status = self.atualizar_status_internet()
        network_quality = str(network_status.get("qualidade", "erro")).lower()
        network_online = network_status.get("status") == "online"
        network_value_map = {
            "excelente": "Excelente",
            "bom": "Boa",
            "regular": "Regular",
            "ruim": "Instavel",
            "erro": "Erro",
            "offline": "Offline",
        }
        network_tone_map = {
            "excelente": "good",
            "bom": "info",
            "regular": "warn",
            "ruim": "critical",
            "erro": "critical",
            "offline": "critical",
        }
        network_value = network_value_map.get(network_quality, "Online" if network_online else "Offline")
        latency = network_status.get("latencia_ms")
        if latency is not None:
            network_meta = f"Latencia local de {latency} ms"
        else:
            network_meta = str(network_status.get("servidor") or "Sem leitura da rede local.")
        self._set_technical_card_state(
            "network",
            network_value,
            network_meta,
            "Monitorado" if network_online else "Sem resposta",
            network_tone_map.get(network_quality, "info"),
            network_status.get("cor") or ("#22c55e" if network_online else "#ef4444"),
        )

        release_date = get_release_date()
        app_meta = f"Release {release_date}" if release_date else "Instalacao local atual"
        self._set_technical_card_state(
            "app",
            f"v{get_version()}",
            app_meta,
            "Desktop",
            "info",
            "#3b82f6",
        )

        lan_status = api_client.get_status_lan_to_lan(self.usuario_context.get("empresa"))
        lan_links = lan_status.get("links") or []
        lan_resumo = lan_status.get("resumo") or {}
        lan_value_map = {
            "excelente": "Excelente",
            "bom": "Boa",
            "regular": "Regular",
            "ruim": "Instavel",
            "erro": "Erro",
            "offline": "Offline",
        }
        lan_tone_map = {
            "excelente": "good",
            "bom": "info",
            "regular": "warn",
            "ruim": "critical",
            "erro": "critical",
            "offline": "critical",
        }

        if lan_links and set(self.lan_cards.keys()) != {link.get("empresa") for link in lan_links if link.get("empresa")}:
            self._rebuild_lan_cards()

        for link in lan_links:
            company_name = link.get("empresa")
            if not company_name:
                continue
            quality = str(link.get("qualidade", "erro")).lower()
            value = lan_value_map.get(quality, "Online" if link.get("status") == "online" else "Offline")
            latency = link.get("latencia_ms")
            if latency is not None:
                meta = f"{link.get('host')}:{link.get('port')} · {latency} ms"
            else:
                meta = str(link.get("detalhe") or link.get("servidor") or "Sem leitura da malha.")
            badge_text = "Tunel OK" if link.get("status") == "online" else "Sem rota"
            self._set_lan_card_state(
                company_name,
                value,
                meta,
                badge_text,
                lan_tone_map.get(quality, "info"),
                link.get("cor") or "#3b82f6",
            )

        self.technical_panel_subtitle.setText(
            f"API, banco, rede local, malha LAN-to-LAN e versao atual da instalacao. Atualizado as {self.last_technical_refresh.strftime('%H:%M')}."
        )
        if hasattr(self, "lan_panel_subtitle"):
            empresa_origem = lan_status.get("empresa_origem") or self.usuario_context.get("empresa") or "unidade atual"
            self.lan_panel_subtitle.setText(
                f"Malha entre {empresa_origem} e as demais unidades. "
                f"{lan_resumo.get('online', 0)} online, {lan_resumo.get('offline', 0)} offline, {lan_resumo.get('erro', 0)} com erro."
            )
        self._refresh_technical_card_styles(palette)

    def _rebuild_cards(self):
        self._clear_layout(self.cards_layout)
        self.metric_cards = {}
        self.internet_card_data = {}

        visible_configs = []
        for config in self.CARD_CONFIGS:
            screen_key = config.get("screen")
            if screen_key and not has_screen_access(self.usuario_context, screen_key):
                continue
            visible_configs.append(config)

        row = 0

        featured = next((config for config in visible_configs if config.get("featured")), None)
        if featured:
            card = self._create_featured_network_card(featured)
            self.cards_layout.addWidget(card, row, 0, 1, 2)
            row += 1

        general_configs = [config for config in visible_configs if not config.get("featured") and not config.get("wide")]
        wide_configs = [config for config in visible_configs if config.get("wide")]

        for index, config in enumerate(general_configs):
            card = self._create_metric_card(config)
            self.cards_layout.addWidget(card, row + (index // 2), index % 2)

        if general_configs:
            row += (len(general_configs) + 1) // 2

        for config in wide_configs:
            card = self._create_metric_card(config, wide=True)
            self.cards_layout.addWidget(card, row, 0, 1, 2)
            row += 1

        self._apply_theme_styles()

    def _create_metric_card(self, config, wide=False):
        card = ClickableCard(lambda action=config["action"]: self.executar_acao(action))
        card.setObjectName("homeCard")
        card.setMinimumHeight(188 if not wide else 198)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        accent = QFrame()
        accent.setFixedHeight(4)
        accent.setObjectName("homeAccentBar")
        card_layout.addWidget(accent)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 18, 20, 18)
        body_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        pill = QLabel(config["eyebrow"])
        pill.setObjectName("homeCardPill")
        pill.setAlignment(Qt.AlignCenter)
        top_row.addWidget(pill, 0, Qt.AlignLeft)

        top_row.addStretch()

        badge = QLabel("Carregando")
        badge.setObjectName("homeCardBadge")
        badge.setAlignment(Qt.AlignCenter)
        top_row.addWidget(badge, 0, Qt.AlignRight)
        body_layout.addLayout(top_row)

        title = QLabel(config["title"])
        title.setObjectName("homeCardTitle")
        title.setWordWrap(True)
        body_layout.addWidget(title)

        value = QLabel("--")
        value.setObjectName("homeCardValue")
        body_layout.addWidget(value)

        description = QLabel("Atualizando indicadores...")
        description.setObjectName("homeCardDescription")
        description.setWordWrap(True)
        body_layout.addWidget(description)

        body_layout.addStretch()

        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.setSpacing(12)

        cta = QLabel(f"{config['cta']}  >")
        cta.setObjectName("homeCardCta")
        footer_row.addWidget(cta, 0, Qt.AlignLeft | Qt.AlignBottom)
        footer_row.addStretch()

        decoration = MetricWaveDecoration(config["accent"], wide=wide)
        footer_row.addWidget(decoration, 0, Qt.AlignRight | Qt.AlignBottom)
        body_layout.addLayout(footer_row)

        card_layout.addWidget(body)

        self.metric_cards[config["name"]] = {
            "config": config,
            "card": card,
            "accent": accent,
            "pill": pill,
            "badge": badge,
            "title": title,
            "value": value,
            "description": description,
            "cta": cta,
            "decoration": decoration,
        }
        return card

    def _create_featured_network_card(self, config):
        card = ClickableCard(lambda action=config["action"]: self.executar_acao(action))
        card.setObjectName("homeFeaturedCard")
        card.setMinimumHeight(228)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        accent = QFrame()
        accent.setFixedHeight(4)
        accent.setObjectName("homeAccentBar")
        card_layout.addWidget(accent)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(24, 22, 24, 22)
        body_layout.setSpacing(22)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)

        pill = QLabel(config["eyebrow"])
        pill.setObjectName("homeCardPill")
        pill.setAlignment(Qt.AlignCenter)
        header_row.addWidget(pill, 0, Qt.AlignLeft)

        badge = QLabel("Verificando")
        badge.setObjectName("homeCardBadge")
        badge.setAlignment(Qt.AlignCenter)
        header_row.addWidget(badge, 0, Qt.AlignLeft)
        header_row.addStretch()
        left_col.addLayout(header_row)

        title = QLabel(config["title"])
        title.setObjectName("homeFeaturedTitle")
        left_col.addWidget(title)

        status = QLabel("Verificando...")
        status.setObjectName("homeFeaturedValue")
        left_col.addWidget(status)

        latency = QLabel("Medindo latencia local...")
        latency.setObjectName("homeFeaturedMeta")
        left_col.addWidget(latency)

        server = QLabel("Preparando leitura do host monitorado.")
        server.setObjectName("homeFeaturedDetail")
        server.setWordWrap(True)
        left_col.addWidget(server)

        detail = QLabel("Aguardando a primeira leitura do painel.")
        detail.setObjectName("homeFeaturedMeta")
        detail.setWordWrap(True)
        left_col.addWidget(detail)

        updated = QLabel("Atualizado agora")
        updated.setObjectName("homeFeaturedUpdated")
        left_col.addWidget(updated)
        left_col.addStretch()

        cta = QLabel(f"{config['cta']}  >")
        cta.setObjectName("homeCardCta")
        left_col.addWidget(cta)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(12)

        pulse_container = QWidget()
        pulse_layout = QGridLayout(pulse_container)
        pulse_layout.setContentsMargins(0, 0, 0, 0)
        pulse_layout.setSpacing(0)

        pulse = NetworkPulseDecoration(config["accent"])
        pulse_layout.addWidget(pulse, 0, 0, Qt.AlignCenter)

        orb = QLabel("OK")
        orb.setObjectName("homeNetworkOrb")
        orb.setAlignment(Qt.AlignCenter)
        orb.setAttribute(Qt.WA_TransparentForMouseEvents)
        pulse_layout.addWidget(orb, 0, 0, Qt.AlignCenter)

        right_col.addWidget(pulse_container, 0, Qt.AlignRight)
        right_col.addStretch()

        body_layout.addLayout(left_col, 1)
        body_layout.addLayout(right_col)
        card_layout.addWidget(body)

        self.internet_card_data = {
            "card": card,
            "accent": accent,
            "pill": pill,
            "badge": badge,
            "title": title,
            "status": status,
            "latency": latency,
            "server": server,
            "detail": detail,
            "updated": updated,
            "cta": cta,
            "orb": orb,
            "pulse": pulse,
        }
        return card

    def _create_technical_panel(self):
        panel = QFrame()
        panel.setObjectName("homeTechPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        title = QLabel("Painel Tecnico")
        title.setObjectName("homeTechTitle")
        header_layout.addWidget(title)

        self.technical_panel_subtitle = QLabel(
            "API, banco, rede local e versao atual da instalacao."
        )
        self.technical_panel_subtitle.setObjectName("homeTechSubtitle")
        self.technical_panel_subtitle.setWordWrap(True)
        header_layout.addWidget(self.technical_panel_subtitle)

        layout.addLayout(header_layout)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        configs = (
            ("api", "API", "#22c55e"),
            ("database", "Banco", "#10b981"),
            ("network", "Rede", "#3b82f6"),
            ("app", "Aplicacao", "#8b5cf6"),
        )

        self.technical_cards = {}
        for index, (name, label, accent) in enumerate(configs):
            card = self._create_technical_card(name, label, accent)
            grid.addWidget(card, index // 2, index % 2)

        layout.addLayout(grid)
        return panel

    def _create_lan_panel(self):
        panel = QFrame()
        panel.setObjectName("homeTechPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        title = QLabel("Malha LAN-to-LAN")
        title.setObjectName("homeTechTitle")
        header_layout.addWidget(title)

        self.lan_panel_subtitle = QLabel(
            "Conectividade entre a unidade atual e os demais firewalls Netdeep."
        )
        self.lan_panel_subtitle.setObjectName("homeTechSubtitle")
        self.lan_panel_subtitle.setWordWrap(True)
        header_layout.addWidget(self.lan_panel_subtitle)
        layout.addLayout(header_layout)

        self.lan_grid = QGridLayout()
        self.lan_grid.setContentsMargins(0, 0, 0, 0)
        self.lan_grid.setHorizontalSpacing(14)
        self.lan_grid.setVerticalSpacing(14)
        self.lan_grid.setColumnStretch(0, 1)
        self.lan_grid.setColumnStretch(1, 1)
        layout.addLayout(self.lan_grid)

        self._rebuild_lan_cards()
        return panel

    def _lan_targets_for_context(self):
        companies = ["PINHEIRO TAGUATINGA", "PINHEIRO SIA", "PINHEIRO INDUSTRIA"]
        current_company = str(self.usuario_context.get("empresa") or "").strip().upper()
        targets = [company for company in companies if not current_company or company != current_company]
        return targets or companies

    def _rebuild_lan_cards(self):
        if not hasattr(self, "lan_grid"):
            return

        current_company = str(self.usuario_context.get("empresa") or "").strip()
        if hasattr(self, "lan_panel_subtitle"):
            if current_company:
                self.lan_panel_subtitle.setText(
                    f"Conectividade entre {current_company} e os demais firewalls Netdeep."
                )
            else:
                self.lan_panel_subtitle.setText(
                    "Conectividade entre a unidade atual e os demais firewalls Netdeep."
                )

        self._clear_layout(self.lan_grid)
        self.lan_cards = {}

        for index, company in enumerate(self._lan_targets_for_context()):
            card = self._create_lan_card(company)
            self.lan_grid.addWidget(card, index // 2, index % 2)

    def _create_lan_card(self, company_name):
        card = QFrame()
        card.setObjectName("homeTechCard")
        card.setMinimumHeight(128)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        accent = QFrame()
        accent.setObjectName("homeTechAccent")
        accent.setFixedHeight(3)
        card_layout.addWidget(accent)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(18, 16, 18, 16)
        body_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        label = QLabel(company_name)
        label.setObjectName("homeTechLabel")
        top_row.addWidget(label, 0, Qt.AlignLeft)

        top_row.addStretch()

        badge = QLabel("Aguardando")
        badge.setObjectName("homeTechBadge")
        badge.setAlignment(Qt.AlignCenter)
        top_row.addWidget(badge, 0, Qt.AlignRight)
        body_layout.addLayout(top_row)

        value = QLabel("--")
        value.setObjectName("homeTechValue")
        body_layout.addWidget(value)

        meta = QLabel("Leitura ainda nao iniciada.")
        meta.setObjectName("homeTechMeta")
        meta.setWordWrap(True)
        body_layout.addWidget(meta)
        body_layout.addStretch()

        card_layout.addWidget(body)

        self.lan_cards[company_name] = {
            "card": card,
            "accent": accent,
            "label": label,
            "badge": badge,
            "value": value,
            "meta": meta,
            "default_accent": "#3b82f6",
            "current_accent": "#3b82f6",
            "badge_tone": "info",
        }
        return card

    def _create_technical_card(self, name, label_text, accent_color):
        card = QFrame()
        card.setObjectName("homeTechCard")
        card.setMinimumHeight(128)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        accent = QFrame()
        accent.setObjectName("homeTechAccent")
        accent.setFixedHeight(3)
        card_layout.addWidget(accent)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(18, 16, 18, 16)
        body_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        label = QLabel(label_text)
        label.setObjectName("homeTechLabel")
        top_row.addWidget(label, 0, Qt.AlignLeft)

        top_row.addStretch()

        badge = QLabel("Aguardando")
        badge.setObjectName("homeTechBadge")
        badge.setAlignment(Qt.AlignCenter)
        top_row.addWidget(badge, 0, Qt.AlignRight)
        body_layout.addLayout(top_row)

        value = QLabel("--")
        value.setObjectName("homeTechValue")
        body_layout.addWidget(value)

        meta = QLabel("Leitura ainda nao iniciada.")
        meta.setObjectName("homeTechMeta")
        meta.setWordWrap(True)
        body_layout.addWidget(meta)
        body_layout.addStretch()

        card_layout.addWidget(body)

        self.technical_cards[name] = {
            "card": card,
            "accent": accent,
            "label": label,
            "badge": badge,
            "value": value,
            "meta": meta,
            "default_accent": accent_color,
            "current_accent": accent_color,
            "badge_tone": "info",
        }
        return card

    def _set_technical_card_state(self, card_name, value, meta, badge_text, tone, accent):
        card = self.technical_cards.get(card_name)
        if not card:
            return

        card["value"].setText(str(value))
        card["meta"].setText(str(meta))
        card["badge"].setText(str(badge_text))
        card["badge_tone"] = tone or "info"
        card["current_accent"] = accent or card["default_accent"]

    def _set_lan_card_state(self, card_name, value, meta, badge_text, tone, accent):
        card = self.lan_cards.get(card_name)
        if not card:
            return

        card["value"].setText(str(value))
        card["meta"].setText(str(meta))
        card["badge"].setText(str(badge_text))
        card["badge_tone"] = tone or "info"
        card["current_accent"] = accent or card["default_accent"]

    def _refresh_technical_card_styles(self, palette):
        for card_group in (self.technical_cards, self.lan_cards):
            for card in card_group.values():
                accent = card.get("current_accent") or card["default_accent"]
                badge_bg, badge_fg = self._tone_colors(card.get("badge_tone"), palette)
                card["accent"].setStyleSheet(
                    f"background-color: {accent}; border-top-left-radius: 18px; border-top-right-radius: 18px;"
                )
                card["badge"].setStyleSheet(self._build_badge_style(badge_bg, badge_fg))
                card["value"].setStyleSheet(
                    f"color: {accent}; font-size: 26px; font-weight: 800; background: transparent;"
                )

    def _apply_metric_data(self, card_name, resumo):
        card = self.metric_cards.get(card_name)
        if not card:
            return

        values = {
            "materiais": int(resumo.get("total_materiais", 0) or 0),
            "maquinas": int(resumo.get("maquinas_ativas", 0) or 0),
            "manutencoes": int(resumo.get("manutencoes_pendentes", 0) or 0),
            "pedidos": int(resumo.get("pedidos_pendentes", 0) or 0),
            "demandas": int(resumo.get("demandas_abertas", 0) or 0),
        }
        value = values.get(card_name, 0)
        badge_text, tone, description = self._resolve_metric_status(card_name, value, resumo)

        card["value"].setText(self._format_number(value))
        card["description"].setText(description)
        card["badge"].setText(badge_text)

        palette = self._theme_palette()
        accent = card["config"]["accent"]
        badge_bg, badge_fg = self._tone_colors(tone, palette)
        card["accent"].setStyleSheet(
            f"background-color: {accent}; border-top-left-radius: 22px; border-top-right-radius: 22px;"
        )
        card["pill"].setStyleSheet(self._build_pill_style(accent, palette))
        card["badge"].setStyleSheet(self._build_badge_style(badge_bg, badge_fg))
        card["cta"].setStyleSheet(
            f"color: {accent}; font-size: 13px; font-weight: 600; background: transparent;"
        )
        card["decoration"].set_visuals(accent, palette["card_bg"], self._is_dark_theme())

    def _resolve_metric_status(self, card_name, value, resumo):
        if card_name == "materiais":
            itens_baixo = int(resumo.get("itens_baixo_estoque", 0) or 0)
            if value <= 0:
                return "Sem estoque", "critical", "Nenhum material ativo localizado para a empresa atual."
            if itens_baixo > 0:
                return (
                    f"{itens_baixo} em alerta",
                    "warn",
                    f"{value} materiais ativos monitorados, com atencao para itens em nivel baixo.",
                )
            return "Estavel", "good", f"{value} materiais ativos disponiveis para operacao."

        if card_name == "maquinas":
            if value <= 0:
                return "Sem operacao", "critical", "Nao ha maquinas ativas no momento."
            if value == 1:
                return "Em operacao", "good", "1 maquina ativa e liberada para uso."
            return "Em operacao", "good", f"{value} maquinas ativas em acompanhamento."

        if card_name == "manutencoes":
            if value <= 0:
                return "Em dia", "good", "Nao existem manutencoes pendentes nesta leitura."
            if value == 1:
                return "Atencao", "warn", "1 manutencao pendente aguardando tratativa."
            return "Atencao", "warn", f"{value} manutencoes pendentes aguardando tratativa."

        if card_name == "pedidos":
            if value <= 0:
                return "Sem fila", "good", "Nenhum pedido aguardando aprovacao no momento."
            if value == 1:
                return "Aguardando", "info", "1 pedido pendente na fila de aprovacao."
            return "Aguardando", "info", f"{value} pedidos pendentes na fila de aprovacao."

        if card_name == "demandas":
            if value <= 0:
                return "Sem fila", "good", "Nenhuma demanda aberta para a equipe neste momento."
            if value <= 3:
                return "Fila aberta", "warn", f"{value} demandas abertas aguardando atendimento."
            return "Prioridade", "critical", f"{value} demandas abertas pedindo atencao mais rapida."

        return "Atualizado", "info", "Indicador atualizado."

    def _apply_theme_styles(self):
        if self._applying_theme_styles:
            return

        self._applying_theme_styles = True
        palette = self._theme_palette()
        try:
            self.setStyleSheet(
                f"""
                QWidget#homeRoot {{
                    background-color: {palette['page_bg']};
                }}
                QScrollArea#homeScrollArea {{
                    border: none;
                    background: transparent;
                }}
                QScrollArea#homeScrollArea > QWidget > QWidget {{
                    background: transparent;
                }}
                QScrollArea#homeScrollArea QScrollBar:vertical {{
                    border: none;
                    background: {palette['scroll_track']};
                    width: 10px;
                    margin: 8px 2px 8px 0;
                    border-radius: 5px;
                }}
                QScrollArea#homeScrollArea QScrollBar::handle:vertical {{
                    background: {palette['scroll_handle']};
                    border-radius: 5px;
                    min-height: 34px;
                }}
                QScrollArea#homeScrollArea QScrollBar::handle:vertical:hover {{
                    background: {palette['scroll_handle_hover']};
                }}
                QScrollArea#homeScrollArea QScrollBar::add-line:vertical,
                QScrollArea#homeScrollArea QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                QFrame#homeHeaderFrame {{
                    background: transparent;
                    border: none;
                }}
                QLabel#homeGreeting {{
                    color: {palette['text_primary']};
                    font-size: 30px;
                    font-weight: 800;
                    background: transparent;
                }}
                QLabel#homeTimestamp {{
                    color: {palette['text_secondary']};
                    font-size: 13px;
                    font-weight: 500;
                    background: transparent;
                }}
                QLabel#homeContext {{
                    color: {palette['text_muted']};
                    font-size: 13px;
                    line-height: 1.4;
                    background: transparent;
                }}
                QFrame#homeRoleChip {{
                    background-color: {palette['panel_bg']};
                    border: 1px solid {palette['border']};
                    border-radius: 18px;
                }}
                QLabel#homeRoleLabel {{
                    color: {palette['text_muted']};
                    font-size: 12px;
                    font-weight: 600;
                    background: transparent;
                }}
                QLabel#homeRoleValue {{
                    color: {palette['text_primary']};
                    font-size: 17px;
                    font-weight: 700;
                    background: transparent;
                }}
                QFrame#homeTechPanel {{
                    background-color: {palette['panel_bg']};
                    border: 1px solid {palette['border']};
                    border-radius: 20px;
                }}
                QLabel#homeTechTitle {{
                    color: {palette['text_primary']};
                    font-size: 17px;
                    font-weight: 700;
                    background: transparent;
                }}
                QLabel#homeTechSubtitle {{
                    color: {palette['text_muted']};
                    font-size: 12px;
                    line-height: 1.4;
                    background: transparent;
                }}
                QFrame#homeTechCard {{
                    background-color: {palette['card_bg']};
                    border: 1px solid {palette['border']};
                    border-radius: 18px;
                }}
                QLabel#homeTechLabel {{
                    color: {palette['text_secondary']};
                    font-size: 12px;
                    font-weight: 700;
                    background: transparent;
                }}
                QLabel#homeTechBadge {{
                    background: transparent;
                }}
                QLabel#homeTechValue {{
                    color: {palette['text_primary']};
                    font-size: 26px;
                    font-weight: 800;
                    background: transparent;
                }}
                QLabel#homeTechMeta {{
                    color: {palette['text_muted']};
                    font-size: 12px;
                    line-height: 1.45;
                    background: transparent;
                }}
                QFrame#homeCard,
                QFrame#homeFeaturedCard {{
                    background-color: {palette['card_bg']};
                    border: 1px solid {palette['border']};
                    border-radius: 22px;
                }}
                QFrame#homeCard:hover,
                QFrame#homeFeaturedCard:hover {{
                    background-color: {palette['card_hover']};
                    border: 1px solid {palette['border_hover']};
                }}
                QLabel#homeCardTitle {{
                    color: {palette['text_primary']};
                    font-size: 18px;
                    font-weight: 700;
                    background: transparent;
                }}
                QLabel#homeCardValue {{
                    color: {palette['text_primary']};
                    font-size: 36px;
                    font-weight: 800;
                    background: transparent;
                }}
                QLabel#homeCardDescription {{
                    color: {palette['text_secondary']};
                    font-size: 13px;
                    line-height: 1.45;
                    background: transparent;
                }}
                QLabel#homeFeaturedTitle {{
                    color: {palette['text_primary']};
                    font-size: 19px;
                    font-weight: 700;
                    background: transparent;
                }}
                QLabel#homeFeaturedValue {{
                    color: {palette['text_primary']};
                    font-size: 34px;
                    font-weight: 800;
                    background: transparent;
                }}
                QLabel#homeFeaturedMeta {{
                    color: {palette['text_secondary']};
                    font-size: 13px;
                    background: transparent;
                }}
                QLabel#homeFeaturedDetail {{
                    color: {palette['text_muted']};
                    font-size: 13px;
                    line-height: 1.45;
                    background: transparent;
                }}
                QLabel#homeFeaturedUpdated {{
                    color: {palette['text_muted']};
                    font-size: 12px;
                    font-weight: 600;
                    background: transparent;
                }}
                QLabel#homeNetworkOrb {{
                    background: transparent;
                }}
                """
            )

            for card_name, card_data in self.metric_cards.items():
                accent = card_data["config"]["accent"]
                card_data["accent"].setStyleSheet(
                    f"background-color: {accent}; border-top-left-radius: 22px; border-top-right-radius: 22px;"
                )
                card_data["pill"].setStyleSheet(self._build_pill_style(accent, palette))
                card_data["cta"].setStyleSheet(
                    f"color: {accent}; font-size: 13px; font-weight: 600; background: transparent;"
                )
                card_data["decoration"].set_visuals(accent, palette["card_bg"], self._is_dark_theme())

            if self.internet_card_data:
                accent = self.internet_card_data.get("current_accent", "#22c55e")
                self.internet_card_data["accent"].setStyleSheet(
                    f"background-color: {accent}; border-top-left-radius: 22px; border-top-right-radius: 22px;"
                )
                self.internet_card_data["pill"].setStyleSheet(self._build_pill_style(accent, palette))
                self.internet_card_data["cta"].setStyleSheet(
                    f"color: {accent}; font-size: 13px; font-weight: 600; background: transparent;"
                )
                self.internet_card_data["pulse"].set_visuals(accent, palette["card_bg"], self._is_dark_theme())

            if self.technical_cards:
                self._refresh_technical_card_styles(palette)
        finally:
            self._applying_theme_styles = False

    def _theme_palette(self):
        app = QApplication.instance()
        theme = "Claro"
        if app is not None:
            theme = app.property("accessibility_theme") or "Claro"

        if theme == "Escuro":
            return {
                "page_bg": "#0f172a",
                "panel_bg": "#121c30",
                "card_bg": "#111827",
                "card_hover": "#152238",
                "border": "#263447",
                "border_hover": "#3b4e68",
                "text_primary": "#f8fafc",
                "text_secondary": "#cbd5e1",
                "text_muted": "#8fa3ba",
                "scroll_track": "#172235",
                "scroll_handle": "#42546b",
                "scroll_handle_hover": "#5c718c",
            }

        return {
            "page_bg": "#f3f7fb",
            "panel_bg": "#ffffff",
            "card_bg": "#ffffff",
            "card_hover": "#f8fbff",
            "border": "#dbe5f0",
            "border_hover": "#c4d3e5",
            "text_primary": "#0f172a",
            "text_secondary": "#334155",
            "text_muted": "#64748b",
            "scroll_track": "#e5edf6",
            "scroll_handle": "#b7c4d3",
            "scroll_handle_hover": "#90a3b8",
        }

    def _is_dark_theme(self):
        app = QApplication.instance()
        if app is None:
            return False
        return (app.property("accessibility_theme") or "Claro") == "Escuro"

    def _build_pill_style(self, accent, palette):
        return (
            "background-color: "
            f"{self._hex_to_rgba(accent, 0.16)};"
            f"color: {accent};"
            "border: none;"
            "border-radius: 10px;"
            "padding: 6px 10px;"
            "font-size: 11px;"
            "font-weight: 700;"
            "letter-spacing: 0;"
        )

    def _build_badge_style(self, background, foreground):
        return (
            f"background-color: {background};"
            f"color: {foreground};"
            "border: none;"
            "border-radius: 10px;"
            "padding: 6px 10px;"
            "font-size: 11px;"
            "font-weight: 700;"
            "letter-spacing: 0;"
        )

    def _build_orb_style(self, accent, card_background, text_color):
        return (
            "background-color: transparent;"
            f"color: {accent if accent else text_color};"
            "border: none;"
            "font-size: 13px;"
            "font-weight: 800;"
            "letter-spacing: 0;"
            "padding: 0px;"
        )

    def _tone_colors(self, tone, palette):
        tones = {
            "good": ("rgba(34, 197, 94, 0.16)", "#22c55e"),
            "info": ("rgba(59, 130, 246, 0.16)", "#3b82f6"),
            "warn": ("rgba(245, 158, 11, 0.18)", "#f59e0b"),
            "critical": ("rgba(239, 68, 68, 0.18)", "#ef4444"),
        }
        return tones.get(tone, ("rgba(148, 163, 184, 0.18)", palette["text_secondary"]))

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(child_layout)

    def _format_number(self, value):
        try:
            return f"{int(value):,}".replace(",", ".")
        except Exception:
            return str(value)

    def _hex_to_rgba(self, hex_color, alpha):
        color = str(hex_color or "#000000").lstrip("#")
        if len(color) != 6:
            return "rgba(0, 0, 0, 0.12)"
        red = int(color[0:2], 16)
        green = int(color[2:4], 16)
        blue = int(color[4:6], 16)
        return f"rgba({red}, {green}, {blue}, {alpha:.2f})"
