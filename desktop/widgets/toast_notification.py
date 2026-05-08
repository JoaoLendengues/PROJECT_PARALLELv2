from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QCursor, QFont
from PySide6.QtGui import QPainterPath, QRegion
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ToastNotification(QWidget):
    """Popup em estilo capsula no topo da aplicacao."""

    def __init__(
        self,
        message: str,
        tipo: str = "info",
        parent: Optional[QWidget] = None,
        duration: int = 5000,
        prioridade: str = "baixa",
        acao: Optional[Callable] = None,
        acao_id=None,
        notificacao_id=None,
        title: Optional[str] = None,
    ):
        super().__init__(None)

        self.parent_window = parent
        self.duration = duration
        self.prioridade = prioridade
        self.acao = acao
        self.acao_id = acao_id
        self.notificacao_id = notificacao_id
        self.message = message or "Nova notificacao"
        self.title = (title or "").strip() or self._default_title(tipo, prioridade)
        self.tipo = tipo

        self._collapsed_width = 34
        self._collapsed_height = 34
        self._mid_width = 112
        self._mid_height = 44
        self._entry_width = 184
        self._entry_height = 54
        self._content_ready = False
        self._closing = False

        self.palette_map = self._resolve_palette()

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setCursor(QCursor(Qt.PointingHandCursor if acao else Qt.ArrowCursor))

        self._build_ui()
        self._apply_styles()
        self._configure_effects()
        self._setup_animations()
        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.timeout.connect(self.fechar_animado)

        self.show_animation()

    def _default_title(self, tipo: str, prioridade: str) -> str:
        if prioridade == "alta":
            return "Nova demanda alta!"
        mapping = {
            "success": "Atualizacao",
            "warning": "Atencao",
            "error": "Falha no sistema",
            "info": "Atualizacao",
        }
        return mapping.get(tipo, "Atualizacao")

    def _resolve_palette(self) -> dict:
        app = QApplication.instance()
        dark_theme = True
        if app is not None:
            dark_theme = app.palette().window().color().lightness() < 140

        accent_map = {
            "success": "#3DDC97",
            "warning": "#FFB020",
            "error": "#FF6363",
            "info": "#3B82F6",
        }
        accent = accent_map.get(self.tipo, "#3B82F6")

        if dark_theme:
            return {
                "bg": "rgba(6, 11, 22, 248)",
                "bg_secondary": "rgba(10, 18, 32, 245)",
                "border": self._hex_to_rgba(accent, 0.24),
                "text": "#F8FBFF",
                "muted": "#A5B4CF",
                "shadow": QColor(3, 8, 18, 190),
                "accent": accent,
                "accent_soft": self._hex_to_rgba(accent, 0.18),
                "close_text": "#D6E2FF",
                "close_hover": "rgba(255, 255, 255, 0.08)",
            }

        return {
            "bg": "rgba(252, 254, 255, 250)",
            "bg_secondary": "rgba(245, 249, 255, 245)",
            "border": self._hex_to_rgba(accent, 0.18),
            "text": "#0F172A",
            "muted": "#5B6577",
            "shadow": QColor(15, 23, 42, 45),
            "accent": accent,
            "accent_soft": self._hex_to_rgba(accent, 0.12),
            "close_text": "#425168",
            "close_hover": "rgba(15, 23, 42, 0.06)",
        }

    def _hex_to_rgba(self, color: str, alpha: float) -> str:
        qcolor = QColor(color)
        return f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {alpha:.3f})"

    def _icon_glyph(self) -> str:
        icon_map = {
            "success": "✓",
            "warning": "!",
            "error": "•",
            "info": "•",
        }
        return icon_map.get(self.tipo, "•")

    def _build_ui(self) -> None:
        self.setObjectName("toastRoot")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.shell = QFrame()
        self.shell.setObjectName("toastShell")
        self.shell_layout = QHBoxLayout(self.shell)
        self.shell_layout.setContentsMargins(16, 12, 14, 12)
        self.shell_layout.setSpacing(12)

        self.indicator_wrap = QFrame()
        self.indicator_wrap.setObjectName("toastIndicatorWrap")
        self.indicator_wrap.setFixedSize(18, 18)
        indicator_layout = QVBoxLayout(self.indicator_wrap)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.setAlignment(Qt.AlignCenter)

        self.indicator = QLabel(self._icon_glyph())
        self.indicator.setObjectName("toastIndicator")
        self.indicator.setAlignment(Qt.AlignCenter)
        self.indicator.setFixedSize(14, 14)
        indicator_layout.addWidget(self.indicator)
        self.shell_layout.addWidget(self.indicator_wrap, 0, Qt.AlignVCenter)

        self.content_frame = QFrame()
        self.content_frame.setObjectName("toastContentFrame")
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("toastTitle")
        self.title_label.setWordWrap(False)
        content_layout.addWidget(self.title_label)

        self.message_label = QLabel(self.message)
        self.message_label.setObjectName("toastMessage")
        self.message_label.setWordWrap(False)
        self.message_label.setMaximumWidth(276)
        content_layout.addWidget(self.message_label)

        self.shell_layout.addWidget(self.content_frame, 1)

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("toastCloseButton")
        self.close_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_button.setFixedSize(24, 24)
        self.close_button.clicked.connect(self.fechar_animado)
        self.shell_layout.addWidget(self.close_button, 0, Qt.AlignVCenter)

        outer_layout.addWidget(self.shell)

        self.content_effect = QGraphicsOpacityEffect(self.content_frame)
        self.content_frame.setGraphicsEffect(self.content_effect)
        self.content_effect.setOpacity(0.0)

        self.close_effect = QGraphicsOpacityEffect(self.close_button)
        self.close_button.setGraphicsEffect(self.close_effect)
        self.close_effect.setOpacity(0.0)

        self.adjustSize()
        final_width = max(332, min(self.sizeHint().width() + 24, 438))
        self.final_size = QPoint(final_width, 68)
        self.setMinimumSize(0, 0)
        self.resize(self.final_size.x(), self.final_size.y())

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            QFrame#toastShell {{
                background: {self.palette_map['bg']};
                border: 1px solid {self.palette_map['border']};
                border-radius: 999px;
                padding: 0;
            }}
            QFrame#toastIndicatorWrap {{
                background: transparent;
                border: none;
            }}
            QLabel#toastIndicator {{
                color: {self.palette_map['accent']};
                font-size: 14px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            QFrame#toastContentFrame {{
                background: transparent;
                border: none;
            }}
            QLabel#toastTitle {{
                color: {self.palette_map['text']};
                font-size: 12px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            QLabel#toastMessage {{
                color: {self.palette_map['muted']};
                font-size: 11px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
            QPushButton#toastCloseButton {{
                color: {self.palette_map['close_text']};
                font-size: 16px;
                font-weight: 500;
                background: transparent;
                border: none;
                border-radius: 999px;
                padding: 0;
            }}
            QPushButton#toastCloseButton:hover {{
                background: {self.palette_map['close_hover']};
            }}
            """
        )

        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.message_label.setFont(QFont("Segoe UI", 10))
        self.indicator.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.close_button.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        self._apply_capsule_mask()

    def _configure_effects(self) -> None:
        self.shell.setGraphicsEffect(None)

    def _apply_capsule_mask(self) -> None:
        rect = self.rect()
        if rect.isNull():
            return

        radius = max(8.0, min(rect.height() / 2.0, rect.width() / 2.0))
        path = QPainterPath()
        path.addRoundedRect(rect.adjusted(0, 0, -1, -1), radius, radius)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_capsule_mask()

    def _set_collapsed_layout_state(self) -> None:
        self.content_frame.hide()
        self.close_button.hide()
        self.shell_layout.setContentsMargins(8, 8, 8, 8)
        self.shell_layout.setSpacing(0)
        self.shell_layout.setAlignment(Qt.AlignCenter)

    def _set_entry_layout_state(self) -> None:
        self.content_frame.hide()
        self.close_button.hide()
        self.shell_layout.setContentsMargins(14, 10, 14, 10)
        self.shell_layout.setSpacing(0)
        self.shell_layout.setAlignment(Qt.AlignCenter)

    def _set_final_layout_state(self) -> None:
        self.content_frame.show()
        self.close_button.show()
        self.shell_layout.setContentsMargins(16, 12, 14, 12)
        self.shell_layout.setSpacing(12)
        self.shell_layout.setAlignment(Qt.AlignVCenter)

    def _setup_animations(self) -> None:
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self.opacity_anim.setDuration(180)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.expand_anim = QPropertyAnimation(self, b"geometry", self)
        self.expand_anim.setDuration(520)
        self.expand_anim.setEasingCurve(QEasingCurve.Linear)
        self.expand_anim.finished.connect(self._on_expand_finished)

        self.content_anim = QPropertyAnimation(self.content_effect, b"opacity", self)
        self.content_anim.setDuration(190)
        self.content_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.close_icon_anim = QPropertyAnimation(self.close_effect, b"opacity", self)
        self.close_icon_anim.setDuration(150)
        self.close_icon_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.collapse_anim = QPropertyAnimation(self, b"geometry", self)
        self.collapse_anim.setDuration(430)
        self.collapse_anim.setEasingCurve(QEasingCurve.Linear)
        self.collapse_anim.finished.connect(self._close_now)

    def _anchor_rect(self) -> QPoint:
        if self.parent_window is not None:
            try:
                target_window = self.parent_window.window()
                pos = target_window.mapToGlobal(QPoint(0, 0))
                return QPoint(
                    pos.x() + max(0, (target_window.width() - self.final_size.x()) // 2),
                    pos.y() + 18,
                )
            except Exception:
                pass

        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QApplication.primaryScreen().geometry()
        return QPoint(
            available.x() + max(0, (available.width() - self.final_size.x()) // 2),
            available.y() + 18,
        )

    def show_animation(self) -> None:
        anchor = self._anchor_rect()
        final_rect = self._rect_from_center(anchor, self.final_size.x(), self.final_size.y())
        overshoot_rect = self._rect_from_center(anchor, self.final_size.x() + 20, self.final_size.y())
        entry_rect = self._rect_from_center(anchor, self._entry_width, self._entry_height)
        mid_rect = self._rect_from_center(anchor, self._mid_width, self._mid_height)
        collapsed_rect = self._rect_from_center(anchor, self._collapsed_width, self._collapsed_height)

        self._final_rect = final_rect
        self._overshoot_rect = overshoot_rect
        self._entry_rect = entry_rect
        self._mid_rect = mid_rect
        self._collapsed_rect = collapsed_rect

        self._set_collapsed_layout_state()
        self.content_effect.setOpacity(0.0)
        self.close_effect.setOpacity(0.0)
        self.setWindowOpacity(0.0)
        self.setGeometry(collapsed_rect)
        self.show()
        self.raise_()

        self.opacity_anim.stop()
        self.expand_anim.stop()
        self.content_anim.stop()
        self.close_icon_anim.stop()

        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)

        self.expand_anim.setStartValue(collapsed_rect)
        self.expand_anim.setKeyValueAt(0.22, mid_rect)
        self.expand_anim.setKeyValueAt(0.56, entry_rect)
        self.expand_anim.setKeyValueAt(0.84, overshoot_rect)
        self.expand_anim.setEndValue(final_rect)
        self.content_anim.setStartValue(0.0)
        self.content_anim.setEndValue(1.0)
        self.close_icon_anim.setStartValue(0.0)
        self.close_icon_anim.setEndValue(1.0)

        self.opacity_anim.start()
        QTimer.singleShot(250, self._set_entry_layout_state)
        self.expand_anim.start()

    def _on_expand_finished(self) -> None:
        self._content_ready = True
        self._set_final_layout_state()
        self.content_anim.start()
        self.close_icon_anim.start()
        if self.duration > 0 and not self._closing:
            self._hold_timer.start(self.duration)

    def fechar_animado(self) -> None:
        if self._closing:
            return

        self._closing = True
        self._hold_timer.stop()

        self.content_anim.stop()
        self.close_icon_anim.stop()
        self.expand_anim.stop()
        self.opacity_anim.stop()
        self.collapse_anim.stop()

        reverse_content = QPropertyAnimation(self.content_effect, b"opacity", self)
        reverse_content.setDuration(100)
        reverse_content.setStartValue(self.content_effect.opacity())
        reverse_content.setEndValue(0.0)
        reverse_content.setEasingCurve(QEasingCurve.InCubic)

        reverse_close = QPropertyAnimation(self.close_effect, b"opacity", self)
        reverse_close.setDuration(100)
        reverse_close.setStartValue(self.close_effect.opacity())
        reverse_close.setEndValue(0.0)
        reverse_close.setEasingCurve(QEasingCurve.InCubic)

        pinch_rect = self._rect_from_center(
            self._anchor_rect(),
            max(self._entry_width, self.final_size.x() - 112),
            self._entry_height,
        )

        self.collapse_anim.setStartValue(self.geometry())
        self.collapse_anim.setKeyValueAt(0.30, pinch_rect)
        self.collapse_anim.setKeyValueAt(0.68, self._mid_rect)
        self.collapse_anim.setEndValue(self._collapsed_rect)

        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self.fade_out_anim.setDuration(180)
        self.fade_out_anim.setStartValue(self.windowOpacity())
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.InCubic)

        reverse_content.start()
        reverse_close.start()
        QTimer.singleShot(70, self._set_entry_layout_state)
        QTimer.singleShot(90, self.collapse_anim.start)
        QTimer.singleShot(130, self.fade_out_anim.start)

    def _close_now(self) -> None:
        self.hide()
        self.deleteLater()

    def _rect_from_center(self, anchor: QPoint, width: int, height: int):
        x = anchor.x() + (self.final_size.x() - width) // 2
        y = anchor.y() + (self.final_size.y() - height) // 2
        from PySide6.QtCore import QRect

        return QRect(x, y, width, height)

    def _run_action(self) -> None:
        if callable(self.acao):
            self.acao()
            return

        if not self.parent_window or not self.acao:
            return

        handler = getattr(self.parent_window, self.acao, None)
        if not callable(handler):
            return

        if self.acao_id is not None:
            try:
                handler(self.acao_id)
                return
            except TypeError:
                pass

        handler()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.acao:
                try:
                    self._run_action()
                finally:
                    self.fechar_animado()
            else:
                self.fechar_animado()
            event.accept()
            return
        super().mousePressEvent(event)

class NotificationManager:
    """Fila simples de notificacoes capsula."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._fila = []
        self._notificacao_atual = None
        self._parent = None
        self._sons_habilitados = True

    def set_parent(self, parent):
        self._parent = parent

    def set_sons_habilitados(self, habilitado):
        self._sons_habilitados = habilitado
        try:
            from core.sound_manager import sound_manager

            sound_manager.set_habilitado(habilitado)
        except Exception:
            pass

    def show(
        self,
        message,
        tipo="info",
        duration=5000,
        parent=None,
        prioridade="baixa",
        acao=None,
        acao_id=None,
        notificacao_id=None,
        title=None,
    ):
        if self._sons_habilitados:
            try:
                from core.sound_manager import sound_manager

                sound_manager.tocar(prioridade)
            except Exception:
                pass

        if parent is None:
            parent = self._parent or QApplication.activeWindow()

        self._fila.append(
            {
                "message": message,
                "tipo": tipo,
                "duration": duration,
                "parent": parent,
                "prioridade": prioridade,
                "acao": acao,
                "acao_id": acao_id,
                "notificacao_id": notificacao_id,
                "title": title,
            }
        )

        if self._notificacao_atual is None:
            self._exibir_proxima()

    def _exibir_proxima(self):
        if not self._fila:
            self._notificacao_atual = None
            return

        item = self._fila.pop(0)
        parent = item["parent"]
        if parent is not None and hasattr(parent, "window"):
            try:
                parent = parent.window()
            except Exception:
                pass

        self._notificacao_atual = ToastNotification(
            message=item["message"],
            tipo=item["tipo"],
            parent=parent,
            duration=item["duration"],
            prioridade=item["prioridade"],
            acao=item["acao"],
            acao_id=item["acao_id"],
            notificacao_id=item["notificacao_id"],
            title=item["title"],
        )
        self._notificacao_atual.destroyed.connect(self._proxima)

    def _proxima(self):
        self._notificacao_atual = None
        QTimer.singleShot(80, self._exibir_proxima)

    def success(self, message, parent=None, duration=4000, acao=None, acao_id=None, title=None):
        return self.show(message, "success", duration, parent, "baixa", acao, acao_id, title=title)

    def warning(self, message, parent=None, duration=5000, acao=None, acao_id=None, title=None):
        return self.show(message, "warning", duration, parent, "media", acao, acao_id, title=title)

    def error(self, message, parent=None, duration=6000, acao=None, acao_id=None, title=None):
        return self.show(message, "error", duration, parent, "alta", acao, acao_id, title=title)

    def info(self, message, parent=None, duration=4000, acao=None, acao_id=None, title=None):
        return self.show(message, "info", duration, parent, "baixa", acao, acao_id, title=title)

    def limpar_fila(self):
        self._fila.clear()
        if self._notificacao_atual is not None:
            self._notificacao_atual.fechar_animado()


notification_manager = NotificationManager()
