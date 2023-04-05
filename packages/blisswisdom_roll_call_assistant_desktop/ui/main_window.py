from __future__ import annotations

import importlib.resources
import pathlib

import PySide6.QtXml  # This is only for PyInstaller to process properly
from PySide6.QtGui import QCloseEvent, QIcon, QPaintEvent, QPixmap
from PySide6.QtWidgets import (
    QMainWindow)

import blisswisdom_roll_call_assistant_sdk as sdk


class QMainWindowExt(QMainWindow):
    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        self.setWindowTitle(f'{sdk.PROG_NAME} {sdk.VERSION}')

        app_icon: pathlib.Path
        with importlib.resources.path(__package__, 'icon.ico') as app_icon:
            self.setWindowIcon(QIcon(str(app_icon)))

        banner_path: pathlib.Path
        with importlib.resources.path(__package__, 'banner.png') as banner_path:
            self.banner_label.setPixmap(QPixmap(banner_path))

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
