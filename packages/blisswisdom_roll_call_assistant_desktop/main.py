import importlib.resources
import pathlib
import sys

from PySide6.QtCore import QCoreApplication, QFile, QIODevice, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

import blisswisdom_roll_call_assistant_sdk as sdk
from . import ui


def main() -> int:
    sdk.init_logger(sdk.get_entry_file_path().parent / f'{sdk.PROG_NAME}.log')

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app: QApplication = QApplication(sys.argv)

    ui_loader: QUiLoader = QUiLoader()
    ui_loader.registerCustomWidget(ui.QMainWindowExt)

    ui_path: pathlib.Path
    with importlib.resources.path(ui, 'main_window.ui') as ui_path:
        ui_file: QFile = QFile(str(ui_path))
        if not ui_file.open(QIODevice.ReadOnly):
            raise RuntimeError(f"Cannot open {ui_path}: {ui_file.errorString()}")
        main_window: ui.QMainWindowExt = ui_loader.load(ui_file)
        ui_file.close()

    main_window.set_up(sdk.get_entry_file_path().parent / f'{sdk.PROG_NAME}.toml')
    sdk.get_logger(__package__).info('Showing the main window')
    main_window.show()
    res: int = app.exec_()
    sdk.get_logger(__package__).info('Exited from the main window')
    return res
