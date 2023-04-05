from __future__ import annotations

import importlib.resources
import pathlib

import PySide6.QtXml  # This is only for PyInstaller to process properly
from PySide6.QtGui import QCloseEvent, QIcon, QPaintEvent, QPixmap
from PySide6.QtWidgets import QLabel, QLineEdit, QMainWindow, QPlainTextEdit, QPushButton

import blisswisdom_roll_call_assistant_sdk as sdk


class QMainWindowExt(QMainWindow):
    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        self.setWindowTitle(f'{sdk.PROG_NAME} {sdk.VERSION}')

        self.banner_label: QLabel = getattr(self, 'banner_label')

        self.account_line_edit: QLineEdit = getattr(self, 'account_line_edit')
        self.password_line_edit: QLineEdit = getattr(self, 'password_line_edit')
        self.character_line_edit: QLineEdit = getattr(self, 'character_line_edit')
        self.class_line_edit: QLineEdit = getattr(self, 'class_line_edit')
        self.attendance_urls_plain_text_edit: QPlainTextEdit = getattr(self, 'attendance_urls_plain_text_edit')
        self.status_plain_text_edit: QPlainTextEdit = getattr(self, 'status_plain_text_edit')

        self.edit_push_button: QPushButton = getattr(self, 'edit_push_button')
        self.edit_push_button.clicked.connect(self.on_edit_push_button_clicked)

        self.save_push_button: QPushButton = getattr(self, 'save_push_button')
        self.save_push_button.clicked.connect(self.on_save_push_button_clicked)

        self.cancel_push_button: QPushButton = getattr(self, 'cancel_push_button')
        self.cancel_push_button.clicked.connect(self.on_cancel_push_button_clicked)

        self.start_push_button: QPushButton = getattr(self, 'start_push_button')

        self.stop_push_button: QPushButton = getattr(self, 'stop_push_button')

        self.log_in_push_button: QPushButton = getattr(self, 'log_in_push_button')

        self.help_push_button: QPushButton = getattr(self, 'help_push_button')

        app_icon: pathlib.Path
        with importlib.resources.path(__package__, 'icon.ico') as app_icon:
            self.setWindowIcon(QIcon(str(app_icon)))

        banner_path: pathlib.Path
        with importlib.resources.path(__package__, 'banner.png') as banner_path:
            self.banner_label.setPixmap(QPixmap(banner_path))

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)

    def set_edit_enabled(self, enabled: bool) -> None:
        self.account_line_edit.setEnabled(enabled)
        self.password_line_edit.setEnabled(enabled)
        self.character_line_edit.setEnabled(enabled)
        self.class_line_edit.setEnabled(enabled)
        self.attendance_urls_plain_text_edit.setEnabled(enabled)
        self.edit_push_button.setEnabled(not enabled)
        self.save_push_button.setEnabled(enabled)
        self.cancel_push_button.setEnabled(enabled)
        self.start_push_button.setEnabled(not enabled)
        self.log_in_push_button.setEnabled(not enabled)

    def on_edit_push_button_clicked(self) -> None:
        self.set_edit_enabled(True)

    def on_save_push_button_clicked(self) -> None:
        self.set_edit_enabled(False)

    def on_cancel_push_button_clicked(self) -> None:
        self.set_edit_enabled(False)
