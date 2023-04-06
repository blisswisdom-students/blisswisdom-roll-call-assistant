import io
import pathlib
from typing import Optional

import dacite
import tomli
from PySide6.QtCore import QThread

import blisswisdom_roll_call_assistant_sdk as sdk
from .ui_model import BaseUIModel


class MainWindowModel(BaseUIModel):
    def __init__(self, config_path: pathlib.Path) -> None:
        super().__init__()
        self._qthread: Optional[QThread] = None
        self._in_progress: bool = False
        self._logging_in: bool = False
        self._status: str = ''
        self.thread_result: bool = False

        self.config: Optional[sdk.Config] = None
        self.config_path: pathlib.Path = config_path
        try:
            if self.config_path.exists():
                f: io.FileIO
                with open(self.config_path, 'rb') as f:
                    self.config = dacite.from_dict(sdk.Config, tomli.load(f))
        except Exception as e:
            sdk.get_logger(__package__).exception(e)
        if not self.config:
            self.config = sdk.Config('', '', '', '', list())

    @property
    def in_progress(self) -> bool:
        return self._in_progress

    @in_progress.setter
    def in_progress(self, value: bool) -> None:
        self._in_progress = value

    @property
    def logging_in(self) -> bool:
        return self._logging_in

    @logging_in.setter
    def logging_in(self, value: bool) -> None:
        self._logging_in = value

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        self._status = value

    @property
    def account(self) -> str:
        return self.config.account

    @account.setter
    def account(self, value: str) -> None:
        self.config.account = value

    @property
    def password(self) -> str:
        return self.config.password

    @password.setter
    def password(self, value: str) -> None:
        self.config.password = value

    @property
    def character(self) -> str:
        return self.config.character

    @character.setter
    def character(self, value: str) -> None:
        self.config.character = value

    @property
    def class_(self) -> str:
        return self.config.class_

    @class_.setter
    def class_(self, value: str) -> None:
        self.config.class_ = value

    @property
    def attendance_urls(self) -> list[str]:
        return self.config.attendance_urls

    @attendance_urls.setter
    def attendance_urls(self, value: list[str]) -> None:
        self.config.attendance_urls = value

    def save(self) -> None:
        self.config.save(self.config_path)

    def start(self) -> None:
        if self._qthread:
            sdk.get_logger(__package__).info('Another task is already running')
            self.status = '另一項工作正在執行中'
            return
        self.in_progress = True
        self.status = '開始匯入點名資料 ...'
        self._qthread = Start(self)
        self._qthread.finished.connect(self.on_start_finish)
        self.thread_result = False
        self._qthread.start()

    def on_start_finish(self) -> None:
        self.in_progress = False
        self._qthread = None

    def stop(self) -> None:
        self.status = '停止匯入點名資料 ...'
        self._qthread.stop()

    def log_in(self) -> None:
        if self._qthread:
            sdk.get_logger(__package__).info('Another task is already running')
            self.status = '另一項工作正在執行中'
            return
        self.logging_in = True
        self.status = '開始登入 ...'
        self._qthread = LogIn(self)
        self._qthread.finished.connect(self.on_log_in_finish)
        self.thread_result = False
        self._qthread.start()

    def on_log_in_finish(self) -> None:
        self.logging_in = False
        sdk.get_logger(__package__).info('Logged in' if self.thread_result else 'Failed to log in')
        self.status = f'登入「{"成功" if self.thread_result else "失敗"}」'
        self._qthread = None


class Start(QThread):
    def __init__(self, main_window_model: MainWindowModel, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.main_window_model: MainWindowModel = main_window_model
        self.config: sdk.Config = main_window_model.config

    def run(self) -> None:
        pass

    def stop(self) -> None:
        pass


class LogIn(QThread):
    def __init__(self, main_window_model: MainWindowModel, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.main_window_model: MainWindowModel = main_window_model
        self.config: sdk.Config = main_window_model.config

    def run(self) -> None:
        self.main_window_model.thread_result = sdk.SimpleBlissWisdomRollCallAssistant(self.config).log_in()

    def stop(self) -> None:
        pass
