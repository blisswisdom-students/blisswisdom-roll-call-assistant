import importlib.resources
import logging
import logging.handlers
import pathlib
import sys

from PySide6.QtCore import QCoreApplication, QFile, QIODevice, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from . import ui


def init_logger() -> None:
    logger: logging.Logger = logging.getLogger()
    formatter: logging.Formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')

    handler: logging.Handler = logging.handlers.RotatingFileHandler(f'{__package__}.log', maxBytes=10**5, backupCount=1)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)


def main() -> int:
    init_logger()

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

    logging.getLogger(__package__).info('Showing the main window')
    main_window.show()
    res: int = app.exec_()
    logging.getLogger(__package__).info('Exited from the main window')
    return res
