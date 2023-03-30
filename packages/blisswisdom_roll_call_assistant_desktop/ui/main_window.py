from __future__ import annotations

import importlib.resources

import PySide6.QtXml  # This is only for PyInstaller to process properly
from PySide6.QtGui import QCloseEvent, QPaintEvent, QPixmap
from PySide6.QtWidgets import (
    QMainWindow)

import blisswisdom_roll_call_assistant_sdk as sdk


class QMainWindowExt(QMainWindow):
    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        self.setWindowTitle(f'{sdk.PROG_NAME} {sdk.VERSION}')

        with importlib.resources.path(__package__, 'banner.png') as banner_path:
            self.banner_label.setPixmap(QPixmap(banner_path))

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
