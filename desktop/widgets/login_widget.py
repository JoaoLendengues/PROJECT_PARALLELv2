from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from api_client import api_client


class LoginWidget(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.usuario_preview_codigo = ""
        self.usuario_preview_nome = ""

        self.lookup_timer = QTimer(self)
        self.lookup_timer.setSingleShot(True)
        self.lookup_timer.setInterval(280)
        self.lookup_timer.timeout.connect(self.buscar_usuario_por_codigo)

        self.init_ui()

    def init_ui(self):
        self.setObjectName("loginRoot")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(28, 28, 28, 28)

        self.card = QFrame()
        self.card.setObjectName("loginCard")
        self.card.setMinimumWidth(430)
        self.card.setMaximumWidth(500)

        card_layout = QVBoxLayout(self.card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(36, 34, 36, 34)

        self.logo = QLabel("Project Parallel")
        self.logo.setObjectName("loginLogo")
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        card_layout.addWidget(self.logo)

        self.title = QLabel("Acesso ao Sistema")
        self.title.setObjectName("loginTitle")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        card_layout.addWidget(self.title)

        card_layout.addSpacing(8)

        self.label_codigo = QLabel("Codigo")
        self.label_codigo.setObjectName("loginFieldLabel")
        card_layout.addWidget(self.label_codigo)

        self.codigo_input = QLineEdit()
        self.codigo_input.setObjectName("loginInput")
        self.codigo_input.setPlaceholderText("Digite seu codigo")
        self.codigo_input.setClearButtonEnabled(True)
        self.codigo_input.setMinimumHeight(46)
        self.codigo_input.returnPressed.connect(self.ao_pressionar_enter)
        self.codigo_input.textChanged.connect(self.ao_mudar_codigo)
        card_layout.addWidget(self.codigo_input)

        self.usuario_nome_label = QLabel("")
        self.usuario_nome_label.setObjectName("loginUserInfo")
        self.usuario_nome_label.setTextFormat(Qt.RichText)
        self.usuario_nome_label.setWordWrap(True)
        self.usuario_nome_label.setMinimumHeight(64)
        self.usuario_nome_label.hide()
        card_layout.addWidget(self.usuario_nome_label)

        card_layout.addSpacing(10)

        self.label_senha = QLabel("Senha")
        self.label_senha.setObjectName("loginFieldLabel")
        card_layout.addWidget(self.label_senha)

        self.senha_input = QLineEdit()
        self.senha_input.setObjectName("loginInput")
        self.senha_input.setPlaceholderText("Digite sua senha")
        self.senha_input.setEchoMode(QLineEdit.Password)
        self.senha_input.setMinimumHeight(46)
        self.senha_input.setEnabled(False)
        self.senha_input.returnPressed.connect(self.ao_pressionar_enter)
        self.senha_input.textChanged.connect(self.atualizar_estado_login)
        card_layout.addWidget(self.senha_input)

        card_layout.addSpacing(6)

        self.login_btn = QPushButton("Entrar")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setEnabled(False)
        self.login_btn.clicked.connect(self.fazer_login)
        card_layout.addWidget(self.login_btn)

        self.status_label = QLabel("")
        self.status_label.setObjectName("loginStatus")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        card_layout.addWidget(self.status_label)

        layout.addWidget(self.card)

        self.codigo_input.setFocus()
        self._apply_theme_styles()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_theme_styles()

    def _current_theme(self):
        app = QApplication.instance()
        if app is not None and app.property("accessibility_theme") == "Escuro":
            return "Escuro"
        return "Claro"

    def _apply_theme_styles(self):
        dark = self._current_theme() == "Escuro"
        palette = self._theme_palette(dark)

        self.setStyleSheet(
            f"""
            QWidget#loginRoot {{
                background-color: {palette['window']};
            }}

            QFrame#loginCard {{
                background-color: {palette['card']};
                border: 1px solid {palette['card_border']};
                border-radius: 18px;
            }}

            QLabel#loginLogo {{
                color: {palette['accent']};
                background: transparent;
                border: none;
                padding: 0;
            }}

            QLabel#loginTitle {{
                color: {palette['title']};
                background: transparent;
                border: none;
                padding: 0;
            }}

            QLabel#loginFieldLabel {{
                color: {palette['label']};
                font-size: 13px;
                background: transparent;
                border: none;
                padding: 0;
            }}

            QLabel#loginUserInfo {{
                color: {palette['accent']};
                font-size: 12px;
                font-weight: 600;
                background: transparent;
                border: none;
                padding: 0 0 2px 2px;
            }}

            QLabel#loginStatus {{
                color: {palette['danger']};
                font-size: 14px;
                min-height: 30px;
                background: transparent;
                border: none;
                padding: 6px 0 0 0;
            }}

            QLineEdit#loginInput {{
                background-color: {palette['input_bg']};
                color: {palette['text']};
                border: 1px solid {palette['input_border']};
                border-radius: 10px;
                padding: 10px 14px;
                selection-background-color: {palette['accent_fill']};
                selection-color: {palette['button_text']};
            }}

            QLineEdit#loginInput:focus {{
                border-color: {palette['accent']};
            }}

            QLineEdit#loginInput:disabled {{
                color: {palette['disabled_text']};
                background-color: {palette['input_disabled']};
                border-color: {palette['input_disabled_border']};
            }}

            QPushButton#loginButton {{
                background-color: {palette['button_bg']};
                color: {palette['button_text']};
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 16px;
            }}

            QPushButton#loginButton:hover:!disabled {{
                background-color: {palette['button_hover']};
            }}

            QPushButton#loginButton:pressed:!disabled {{
                background-color: {palette['button_pressed']};
            }}

            QPushButton#loginButton:disabled {{
                background-color: {palette['button_disabled']};
                color: {palette['disabled_text']};
            }}
            """
        )

    def _theme_palette(self, dark):
        if dark:
            return {
                "window": "#0f172a",
                "card": "#111827",
                "card_border": "#223047",
                "accent": "#60a5fa",
                "accent_fill": "#1d4ed8",
                "title": "#f8fafc",
                "label": "#cbd5e1",
                "text": "#e2e8f0",
                "disabled_text": "#7b8aa0",
                "input_bg": "#0f172a",
                "input_border": "#334155",
                "input_disabled": "#0c1422",
                "input_disabled_border": "#243547",
                "button_bg": "#2563eb",
                "button_hover": "#1d4ed8",
                "button_pressed": "#1e40af",
                "button_disabled": "#243547",
                "button_text": "#f8fafc",
                "danger": "#fda4af",
            }

        return {
            "window": "#eef2f6",
            "card": "#ffffff",
            "card_border": "#e5eaf0",
            "accent": "#2c7da0",
            "accent_fill": "#dbeafe",
            "title": "#0f172a",
            "label": "#475569",
            "text": "#0f172a",
            "disabled_text": "#94a3b8",
            "input_bg": "#f8fafc",
            "input_border": "#d8e0e8",
            "input_disabled": "#f1f5f9",
            "input_disabled_border": "#e2e8f0",
            "button_bg": "#2c7da0",
            "button_hover": "#256b8b",
            "button_pressed": "#1f5a76",
            "button_disabled": "#cbd5e1",
            "button_text": "#ffffff",
            "danger": "#dc2626",
        }

    def ao_mudar_codigo(self, texto):
        codigo = texto.strip()
        self.lookup_timer.stop()
        self.usuario_preview_codigo = ""
        self.usuario_preview_nome = ""
        self.usuario_nome_label.hide()
        self.usuario_nome_label.setText("")
        self._set_status_message("")

        self.senha_input.clear()
        self.senha_input.setEnabled(False)
        self.atualizar_estado_login()

        if not codigo:
            return

        self.lookup_timer.start()

    def buscar_usuario_por_codigo(self, focus_password=False):
        codigo = self.codigo_input.text().strip()
        if not codigo:
            return False

        resultado = api_client.buscar_usuario_preview(codigo)

        if codigo != self.codigo_input.text().strip():
            return False

        if resultado["success"]:
            usuario = resultado["usuario"]
            self.usuario_preview_codigo = usuario.get("codigo", codigo)
            self.usuario_preview_nome = usuario.get("nome", "")
            self._set_preview_message("Usuario identificado", "success", self.usuario_preview_nome)
            self.usuario_nome_label.show()
            self.senha_input.setEnabled(True)
            if focus_password:
                self.senha_input.setFocus()
            self.atualizar_estado_login()
            return True

        self.usuario_preview_codigo = ""
        self.usuario_preview_nome = ""
        preview_error = "Codigo nao encontrado"
        if resultado.get("error") and resultado["error"] != "Codigo nao encontrado":
            preview_error = "Nao foi possivel identificar o usuario agora"
            self._set_status_message(str(resultado["error"]), "error")
        else:
            self._set_status_message("")
        self._set_preview_message(preview_error, "error")
        self.usuario_nome_label.show()
        self.senha_input.setEnabled(False)
        self.atualizar_estado_login()
        return False

    def atualizar_estado_login(self):
        pode_entrar = bool(self.usuario_preview_codigo and self.senha_input.text().strip())
        self.login_btn.setEnabled(pode_entrar)

    def ao_pressionar_enter(self):
        if self.sender() is self.codigo_input:
            if self.buscar_usuario_por_codigo(focus_password=True):
                return
            self._set_status_message("Informe um codigo valido para continuar.", "error")
            return

        self.fazer_login()

    def fazer_login(self):
        codigo = self.codigo_input.text().strip()
        senha = self.senha_input.text()

        if not codigo or not senha:
            self._set_status_message("Preencha codigo e senha.", "error")
            return

        if not self.usuario_preview_codigo:
            self._set_status_message("Informe um codigo valido para continuar.", "error")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Entrando...")
        self._set_status_message("")

        result = api_client.login(codigo, senha)

        if result["success"]:
            self._set_status_message("Login realizado com sucesso!", "success")
            QTimer.singleShot(500, lambda: self.on_login_success(result["usuario"]))
            return

        self.login_btn.setText("Entrar")
        self.atualizar_estado_login()
        error_msg = result["error"]
        if isinstance(error_msg, list):
            error_msg = ", ".join(error_msg)
        elif isinstance(error_msg, dict):
            error_msg = str(error_msg)
        self._set_status_message(str(error_msg), "error")

    def _set_preview_message(self, text, tone="neutral", detail=""):
        colors = {
            "neutral": "#94a3b8" if self._current_theme() == "Escuro" else "#64748b",
            "success": "#7dd3fc" if self._current_theme() == "Escuro" else "#2c7da0",
            "error": "#fda4af" if self._current_theme() == "Escuro" else "#dc2626",
        }
        color = colors.get(tone, colors["neutral"])
        self.usuario_nome_label.setStyleSheet(
            "background: transparent; border: none; padding: 6px 0 10px 2px;"
        )

        if detail:
            self.usuario_nome_label.setText(
                f"<div style='color:{color};'>"
                f"<div style='font-size:13px; font-weight:600;'>{text}</div>"
                f"<div style='font-size:22px; font-weight:800; margin-top:4px; line-height:1.2;'>{detail}</div>"
                f"</div>"
            )
            return

        self.usuario_nome_label.setText(
            f"<div style='color:{color}; font-size:16px; font-weight:700;'>{text}</div>"
        )

    def _set_status_message(self, text, tone="error"):
        colors = {
            "neutral": "#94a3b8" if self._current_theme() == "Escuro" else "#64748b",
            "success": "#86efac" if self._current_theme() == "Escuro" else "#15803d",
            "error": "#fda4af" if self._current_theme() == "Escuro" else "#dc2626",
        }
        self.status_label.setStyleSheet(
            f"color: {colors.get(tone, colors['error'])}; font-size: 14px; font-weight: 700; min-height: 30px; background: transparent; border: none; padding: 6px 0 0 0;"
        )
        self.status_label.setText(text)
