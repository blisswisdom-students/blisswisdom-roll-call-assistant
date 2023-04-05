import importlib.resources
import pathlib
import webbrowser

from PySide6.QtGui import QCloseEvent, QIcon, QPixmap
from PySide6.QtWidgets import QLabel, QLineEdit, QMainWindow, QPlainTextEdit, QPushButton

import blisswisdom_roll_call_assistant_sdk as sdk
from .. import ui_model


class QMainWindowExt(QMainWindow):
    def closeEvent(self, event: QCloseEvent) -> None:
        sdk.get_logger(__package__).info('Close issued')
        super().closeEvent(event)

    def set_up(self, config_path: pathlib.Path) -> None:
        self.main_window_model: ui_model.MainWindowModel = ui_model.MainWindowModel(config_path)
        self.main_window_model.add_on_changed_observer(self.on_in_progress_changed, 'in_progress')

        self.setWindowTitle(f'{sdk.PROG_NAME} {sdk.VERSION}')

        self.banner_label: QLabel = getattr(self, 'banner_label')

        self.account_line_edit: QLineEdit = getattr(self, 'account_line_edit')
        self.account_line_edit.setText(self.main_window_model.account)

        self.password_line_edit: QLineEdit = getattr(self, 'password_line_edit')
        self.password_line_edit.setText(self.main_window_model.password)

        self.character_line_edit: QLineEdit = getattr(self, 'character_line_edit')
        self.character_line_edit.setText(self.main_window_model.character)

        self.class_line_edit: QLineEdit = getattr(self, 'class_line_edit')
        self.class_line_edit.setText(self.main_window_model.class_)

        self.attendance_urls_plain_text_edit: QPlainTextEdit = getattr(self, 'attendance_urls_plain_text_edit')
        self.attendance_urls_plain_text_edit.setPlainText('\n'.join(self.main_window_model.attendance_urls))

        self.status_plain_text_edit: QPlainTextEdit = getattr(self, 'status_plain_text_edit')

        self.edit_push_button: QPushButton = getattr(self, 'edit_push_button')
        self.edit_push_button.clicked.connect(self.on_edit_push_button_clicked)

        self.save_push_button: QPushButton = getattr(self, 'save_push_button')
        self.save_push_button.clicked.connect(self.on_save_push_button_clicked)

        self.cancel_push_button: QPushButton = getattr(self, 'cancel_push_button')
        self.cancel_push_button.clicked.connect(self.on_cancel_push_button_clicked)

        self.start_push_button: QPushButton = getattr(self, 'start_push_button')
        self.start_push_button.clicked.connect(self.on_start_push_button_clicked)

        self.stop_push_button: QPushButton = getattr(self, 'stop_push_button')
        self.stop_push_button.clicked.connect(self.on_stop_push_button_clicked)

        self.log_in_push_button: QPushButton = getattr(self, 'log_in_push_button')
        self.log_in_push_button.clicked.connect(self.on_log_in_push_button_clicked)

        self.help_push_button: QPushButton = getattr(self, 'help_push_button')
        self.help_push_button.clicked.connect(self.on_help_push_button_clicked)

        app_icon: pathlib.Path
        with importlib.resources.path(__package__, 'icon.ico') as app_icon:
            self.setWindowIcon(QIcon(str(app_icon)))

        banner_path: pathlib.Path
        with importlib.resources.path(__package__, 'banner.png') as banner_path:
            self.banner_label.setPixmap(QPixmap(banner_path))

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

    def set_in_progress(self, in_progress: bool) -> None:
        self.edit_push_button.setEnabled(not in_progress)
        self.start_push_button.setEnabled(not in_progress)
        self.stop_push_button.setEnabled(in_progress)
        self.log_in_push_button.setEnabled(not in_progress)

    def on_edit_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Edit clicked')
        self.set_edit_enabled(True)

    def on_save_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Save clicked')
        self.main_window_model.account = self.account_line_edit.text().strip()
        self.main_window_model.password = self.password_line_edit.text().strip()
        self.main_window_model.character = self.character_line_edit.text().strip()
        self.main_window_model.class_ = self.class_line_edit.text().strip()
        self.main_window_model.attendance_urls = self.attendance_urls_plain_text_edit.toPlainText().strip().split()
        self.main_window_model.save()
        self.set_edit_enabled(False)

    def on_cancel_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Cancel clicked')
        self.account_line_edit.setText(self.main_window_model.account)
        self.password_line_edit.setText(self.main_window_model.password)
        self.character_line_edit.setText(self.main_window_model.character)
        self.class_line_edit.setText(self.main_window_model.class_)
        self.attendance_urls_plain_text_edit.setPlainText('\n'.join(self.main_window_model.attendance_urls))
        self.set_edit_enabled(False)

    def on_start_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Start clicked')
        self.main_window_model.in_progress = True

    def on_stop_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Stop clicked')
        self.main_window_model.in_progress = False

    def on_log_in_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Log in clicked')
        self.main_window_model.in_progress = True

    def on_help_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Help clicked')
        webbrowser.open('https://github.com/changyuheng/blisswisdom-roll-call-assistant/issues')

    def on_in_progress_changed(self, value: bool) -> None:
        self.set_in_progress(value)
