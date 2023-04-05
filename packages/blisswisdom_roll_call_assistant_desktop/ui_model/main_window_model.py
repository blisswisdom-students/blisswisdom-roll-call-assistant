import io
import pathlib
import tomllib
from typing import Optional

import dacite
from PySide6.QtCore import QThread

import blisswisdom_roll_call_assistant_sdk as sdk
from .ui_model import BaseUIModel


class MainWindowModel(BaseUIModel):
    def __init__(self, config_path: pathlib.Path) -> None:
        super().__init__()
        self._qthread: Optional[QThread] = None
        self._in_progress: bool = False

        self._config: Optional[sdk.Config] = None
        self.config_path: pathlib.Path = config_path
        try:
            if self.config_path.exists():
                f: io.FileIO
                with open(self.config_path, 'rb') as f:
                    self._config = dacite.from_dict(sdk.Config, tomllib.load(f))
        except Exception as e:
            sdk.get_logger(__package__).exception(e)
        if not self._config:
            self._config = sdk.Config('', '', '', '', list())

    @property
    def in_progress(self) -> bool:
        return self._in_progress

    @in_progress.setter
    def in_progress(self, value: bool) -> None:
        self._in_progress = value

    @property
    def account(self) -> str:
        return self._config.account

    @account.setter
    def account(self, value: str) -> None:
        self._config.account = value

    @property
    def password(self) -> str:
        return self._config.password

    @password.setter
    def password(self, value: str) -> None:
        self._config.password = value

    @property
    def character(self) -> str:
        return self._config.character

    @character.setter
    def character(self, value: str) -> None:
        self._config.character = value

    @property
    def class_(self) -> str:
        return self._config.class_

    @class_.setter
    def class_(self, value: str) -> None:
        self._config.class_ = value

    @property
    def attendance_urls(self) -> list[str]:
        return self._config.attendance_urls

    @attendance_urls.setter
    def attendance_urls(self, value: list[str]) -> None:
        self._config.attendance_urls = value

    def save(self) -> None:
        self._config.save(self.config_path)

    def start(self) -> None:
        self.in_progress = True
        try:
            self._qthread = Start(self._config)
            self._qthread.finished.connect(self.on_start_finish)
            self._qthread.start()
        except Exception as e:
            sdk.get_logger(__package__).exception(e)

    def on_start_finish(self) -> None:
        self.in_progress = False

    def stop(self) -> None:
        self._qthread.stop()

    def log_in(self) -> None:
        self.in_progress = True
        self._qthread = LogIn(self._config)
        self._qthread.finished.connect(self.on_log_in_finish)
        self._qthread.start()

    def on_log_in_finish(self) -> None:
        self.in_progress = False


class Start(QThread):
    def __init__(self, config: sdk.Config, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config: sdk.Config = config

    def run(self) -> None:
        pass

    def stop(self) -> None:
        pass


class LogIn(QThread):
    def __init__(self, config: sdk.Config, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config: sdk.Config = config

    def run(self) -> None:
        sdk.SimpleBlissWisdomRollCallAssistant(self.config).log_in()

    def stop(self) -> None:
        pass
