import datetime
import importlib.resources
import pathlib
import webbrowser

from PySide6.QtGui import QCloseEvent, QIcon, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

import blisswisdom_roll_call_assistant_sdk as sdk
from .. import ui_model


class QMainWindowExt(QMainWindow):
    def closeEvent(self, event: QCloseEvent) -> None:
        sdk.get_logger(__package__).info('Close issued')
        super().closeEvent(event)

    def set_up(self, model: ui_model.MainWindowModel) -> None:
        self.main_window_model: ui_model.MainWindowModel = model
        self.main_window_model.add_on_changed_observer(self.on_in_progress_changed, 'in_progress')
        self.main_window_model.add_on_changed_observer(self.on_logging_in_changed, 'logging_in')
        self.main_window_model.add_on_changed_observer(self.on_status_changed, 'status')

        self.setWindowTitle(f'{sdk.PROG_NAME} {sdk.VERSION}')

        self.banner_label: QLabel = getattr(self, 'banner_label')

        self.account_line_edit: QLineEdit = getattr(self, 'account_line_edit')
        self.account_line_edit.setText(self.main_window_model.account)

        self.password_line_edit: QLineEdit = getattr(self, 'password_line_edit')
        self.password_line_edit.setText(self.main_window_model.password)

        self.character_line_edit: QLineEdit = getattr(self, 'character_line_edit')
        self.character_line_edit.setText(self.main_window_model.character)

        self.class_name_line_edit: QLineEdit = getattr(self, 'class_name_line_edit')
        self.class_name_line_edit.setText(self.main_window_model.class_name)

        self.google_api_private_key_id_line_edit: QLineEdit = getattr(self, 'google_api_private_key_id_line_edit')
        self.google_api_private_key_id_line_edit.setText(self.main_window_model.google_api_private_key_id)

        self.google_api_private_key_line_edit: QLineEdit = getattr(self, 'google_api_private_key_line_edit')
        self.google_api_private_key_line_edit.setText(self.main_window_model.google_api_private_key)

        self.attendance_report_sheet_links_table_widget: QTableWidget = \
            getattr(self, 'attendance_report_sheet_links_table_widget')
        item_delegate: QStyledItemDelegate = QStyledItemDelegate(self)
        item_delegate.closeEditor.connect(self.on_attendance_report_sheet_links_editing_finished)
        self.attendance_report_sheet_links_table_widget.setItemDelegate(item_delegate)
        self.attendance_report_sheet_links_table_widget.horizontalHeader().setStretchLastSection(True)
        self.attendance_report_sheet_links_table_widget.verticalHeader().hide()
        self.attendance_report_sheet_links_table_widget.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.load_attendance_report_links()

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
        # self.character_line_edit.setEnabled(enabled)
        self.class_name_line_edit.setEnabled(enabled)
        self.google_api_private_key_id_line_edit.setEnabled(enabled)
        self.google_api_private_key_line_edit.setEnabled(enabled)
        self.attendance_report_sheet_links_table_widget.setEnabled(enabled)
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

    def set_logging_in(self, in_progress: bool) -> None:
        self.edit_push_button.setEnabled(not in_progress)
        self.start_push_button.setEnabled(not in_progress)
        self.log_in_push_button.setEnabled(not in_progress)

    def on_edit_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Edit clicked')
        self.set_edit_enabled(True)

    def on_save_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Save clicked')
        self.main_window_model.account = self.account_line_edit.text().strip()
        self.main_window_model.password = self.password_line_edit.text().strip()
        self.main_window_model.character = self.character_line_edit.text().strip()
        self.main_window_model.class_name = self.class_name_line_edit.text().strip()
        self.main_window_model.google_api_private_key_id = self.google_api_private_key_id_line_edit.text().strip()
        self.main_window_model.google_api_private_key = self.google_api_private_key_line_edit.text().strip()
        self.save_attendance_report_links()
        self.main_window_model.save()
        self.set_edit_enabled(False)

    def on_cancel_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Cancel clicked')
        self.account_line_edit.setText(self.main_window_model.account)
        self.password_line_edit.setText(self.main_window_model.password)
        self.character_line_edit.setText(self.main_window_model.character)
        self.class_name_line_edit.setText(self.main_window_model.class_name)
        self.google_api_private_key_id_line_edit.setText(self.main_window_model.google_api_private_key_id)
        self.google_api_private_key_line_edit.setText(self.main_window_model.google_api_private_key)
        self.load_attendance_report_links()
        self.set_edit_enabled(False)

    def on_start_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Start clicked')
        self.main_window_model.start()

    def on_stop_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Stop clicked')
        self.main_window_model.stop()

    def on_log_in_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Log in clicked')
        self.main_window_model.log_in()

    def on_help_push_button_clicked(self) -> None:
        sdk.get_logger(__package__).info('Help clicked')
        webbrowser.open('https://github.com/changyuheng/blisswisdom-roll-call-assistant/issues')

    def on_in_progress_changed(self, value: bool) -> None:
        self.set_in_progress(value)

    def on_logging_in_changed(self, value: bool) -> None:
        self.set_logging_in(value)

    def on_status_changed(self, value: str) -> None:
        self.status_plain_text_edit.moveCursor(QTextCursor.End)
        self.status_plain_text_edit.insertPlainText(
            f'[{datetime.datetime.now().time().strftime("%H:%M:%S")}] {value}\n')

    def on_attendance_report_sheet_links_editing_finished(
            self, editor: QWidget,
            hint: QAbstractItemDelegate.EndEditHint = QAbstractItemDelegate.EndEditHint.NoHint) -> None:
        i: int
        for i in range(self.attendance_report_sheet_links_table_widget.rowCount() - 1, -1, -1):
            note: str = self.attendance_report_sheet_links_table_widget.item(i, 0).text()
            link: str = self.attendance_report_sheet_links_table_widget.item(i, 1).text()
            if not any([note, link]):
                self.attendance_report_sheet_links_table_widget.removeRow(i)

        new_row_index: int = self.attendance_report_sheet_links_table_widget.rowCount()
        self.attendance_report_sheet_links_table_widget.insertRow(new_row_index)
        self.attendance_report_sheet_links_table_widget.setItem(new_row_index, 0, QTableWidgetItem())
        self.attendance_report_sheet_links_table_widget.setItem(new_row_index, 1, QTableWidgetItem())

        self.attendance_report_sheet_links_table_widget.resizeColumnToContents(0)

    def load_attendance_report_links(self) -> None:
        while self.attendance_report_sheet_links_table_widget.rowCount():
            self.attendance_report_sheet_links_table_widget.removeRow(
                self.attendance_report_sheet_links_table_widget.rowCount() - 1)

        arsl: sdk.AttendanceReportSheetLink
        for arsl in self.main_window_model.config.attendance_report_sheet_links:
            new_row_index: int = self.attendance_report_sheet_links_table_widget.rowCount()
            self.attendance_report_sheet_links_table_widget.insertRow(new_row_index)
            self.attendance_report_sheet_links_table_widget.setItem(new_row_index, 0, QTableWidgetItem(arsl.note))
            self.attendance_report_sheet_links_table_widget.setItem(new_row_index, 1, QTableWidgetItem(arsl.link))

        new_row_index: int = self.attendance_report_sheet_links_table_widget.rowCount()
        self.attendance_report_sheet_links_table_widget.insertRow(new_row_index)
        self.attendance_report_sheet_links_table_widget.setItem(new_row_index, 0, QTableWidgetItem())
        self.attendance_report_sheet_links_table_widget.setItem(new_row_index, 1, QTableWidgetItem())

        self.attendance_report_sheet_links_table_widget.resizeColumnToContents(0)

    def save_attendance_report_links(self) -> None:
        links: list[sdk.AttendanceReportSheetLink] = list()
        i: int
        for i in range(self.attendance_report_sheet_links_table_widget.rowCount()):
            note: str = self.attendance_report_sheet_links_table_widget.item(i, 0).text()
            link: str = self.attendance_report_sheet_links_table_widget.item(i, 1).text()
            if not any([note, link]):
                continue
            links.append(sdk.AttendanceReportSheetLink(link=link, note=note))
        self.main_window_model.config.attendance_report_sheet_links = links
