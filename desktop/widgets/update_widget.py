from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

from updater import UpdateChecker, UpdateDownloader, UpdateInstaller
from version import CURRENT_VERSION


class UpdateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_version = CURRENT_VERSION
        self.update_info = None
        self.downloader = None
        self.init_ui()
        self.check_for_updates()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        titulo = QLabel("Atualizacoes")
        titulo.setProperty("class", "page-title")
        layout.addWidget(titulo)

        card = QFrame()
        card.setObjectName("infoCard")
        card_layout = QVBoxLayout(card)

        self.version_label = QLabel(f"Versao atual: v{self.current_version}")
        self.version_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        card_layout.addWidget(self.version_label)

        self.status_label = QLabel("Verificando atualizacoes...")
        self.status_label.setStyleSheet("color: #64748b;")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.changelog_label = QLabel("Novidades:")
        self.changelog_label.setVisible(False)
        self.changelog_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(self.changelog_label)

        self.changelog_text = QTextEdit()
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setMaximumHeight(200)
        self.changelog_text.setVisible(False)
        layout.addWidget(self.changelog_text)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.check_btn = QPushButton("Verificar")
        self.check_btn.clicked.connect(self.check_for_updates)
        btn_layout.addWidget(self.check_btn)

        self.update_btn = QPushButton("Instalar")
        self.update_btn.setVisible(False)
        self.update_btn.clicked.connect(self.install_update)
        btn_layout.addWidget(self.update_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def check_for_updates(self):
        self.status_label.setText("Verificando...")
        self.check_btn.setEnabled(False)

        self.checker = UpdateChecker()
        self.checker.update_available.connect(self.on_update_available)
        self.checker.no_update.connect(self.on_no_update)
        self.checker.error.connect(self.on_check_error)
        self.checker.start()

    def on_update_available(self, update_info):
        self.update_info = update_info
        self.status_label.setText(f"Nova versao {update_info['version']} disponivel.")
        self.status_label.setStyleSheet("color: #2a9d8f;")

        self.changelog_label.setVisible(True)
        self.changelog_text.setVisible(True)
        self.changelog_text.setText(update_info["changelog"])

        self.update_btn.setVisible(True)
        self.check_btn.setEnabled(True)

    def on_no_update(self):
        self.status_label.setText("Voce ja tem a versao mais recente.")
        self.status_label.setStyleSheet("color: #2a9d8f;")
        self.check_btn.setEnabled(True)

    def on_check_error(self, error_msg):
        self.status_label.setText(f"Erro: {error_msg}")
        self.status_label.setStyleSheet("color: #e76f51;")
        self.check_btn.setEnabled(True)

    def install_update(self):
        if not self.update_info:
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            f"Instalar a versao {self.update_info['version']}?\n\n"
            "O sistema sera fechado para concluir a atualizacao.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm != QMessageBox.Yes:
            return

        self.progress_bar.setVisible(True)
        self.update_btn.setEnabled(False)
        self.check_btn.setEnabled(False)

        self.downloader = UpdateDownloader(
            self.update_info["download_url"],
            self.update_info.get("asset_name", ""),
        )
        self.downloader.progress.connect(self.on_download_progress)
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.error.connect(self.on_download_error)
        self.downloader.start()

    def on_download_progress(self, value):
        self.progress_bar.setValue(value)

    def on_download_finished(self, file_path):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Preparando atualizacao...")

        success, message = UpdateInstaller.install_update(file_path)

        if success:
            QMessageBox.information(self, "Sucesso", message)
            QTimer.singleShot(1000, QApplication.instance().quit)
            return

        QMessageBox.critical(self, "Erro", f"Falha: {message}")
        self.update_btn.setEnabled(True)
        self.check_btn.setEnabled(True)

    def on_download_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Erro no download: {error_msg}")
        self.status_label.setStyleSheet("color: #e76f51;")
        self.update_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
