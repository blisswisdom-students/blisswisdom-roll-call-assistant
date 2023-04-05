import io
import pathlib
import tomllib
from typing import Optional

import dacite

import blisswisdom_roll_call_assistant_sdk as sdk
from .ui_model import BaseUIModel


class MainWindowModel(BaseUIModel):
    def __init__(self, config_path: pathlib.Path) -> None:
        super().__init__()
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

    def save(self):
        self._config.save(self.config_path)
