import enum
import logging
import os
import pathlib
import shutil
import stat
from typing import Any, Callable, Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from .config import Config
from .util import get_entry_file_path


class BlissWisdomRollCallElementFinder:
    @classmethod
    def first_login_link(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, '//a[text()="第一次登入"]')
        except NoSuchElementException:
            return

    @classmethod
    def account_text_input(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, '//input[@placeholder="請輸入帳號"]')
        except NoSuchElementException:
            return

    @classmethod
    def password_text_input(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, '//input[@placeholder="請輸入密碼"]')
        except NoSuchElementException:
            return


class BlissWisdomRollCall(enum.StrEnum):
    HOME_PAGE: str = 'https://pw.blisswisdom.org/'


class SimpleBlissWisdomRollCallAssistant:
    def __init__(self, config: Config) -> None:
        self.work_path: pathlib.Path = get_entry_file_path().parent / '_work'
        self.config: Config = config

        self.clear_work_dir()
        if not self.work_path.is_dir():
            self.work_path.mkdir()

        LOGGER.setLevel(logging.WARNING)

        edge_options: webdriver.EdgeOptions = webdriver.EdgeOptions()
        edge_options.add_argument('--start-maximized')
        edge_options.add_argument(f'user-data-dir={self.work_path}')
        self.browser_driver: webdriver.Edge = webdriver.Edge(
            EdgeChromiumDriverManager().install(), options=edge_options)

    def clear_work_dir(self) -> None:
        def on_rm_error(func: Callable[[Any], None], path: str, exc_info: Any):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        if self.work_path.is_dir():
            shutil.rmtree(self.work_path, onerror=on_rm_error)

    def log_in(self) -> None:
        self.browser_driver.get(BlissWisdomRollCall.HOME_PAGE)

        WebDriverWait(self.browser_driver, 10).until(lambda d: BlissWisdomRollCallElementFinder.first_login_link(d))

        BlissWisdomRollCallElementFinder.account_text_input(self.browser_driver).send_keys(self.config.account)
        BlissWisdomRollCallElementFinder.password_text_input(self.browser_driver).send_keys(self.config.password)

        # WIP
        import time
        time.sleep(3)

