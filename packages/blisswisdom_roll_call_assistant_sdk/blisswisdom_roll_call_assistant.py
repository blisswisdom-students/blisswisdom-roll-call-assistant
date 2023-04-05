import base64
import enum
import logging
import os
import pathlib
import shutil
import stat
import tempfile
import time
from typing import Any, Callable, Optional

import easyocr
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from .config import Config
from .log import get_logger
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

    @classmethod
    def captcha_text_input(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, '//input[@placeholder="請輸入圖片中之文字"]')
        except NoSuchElementException:
            return

    @classmethod
    def captcha_image(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, '//img[contains(@src, ";base64,")]')
        except NoSuchElementException:
            return

    @classmethod
    def login_button(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, '//button[contains(span, "登入")]')
        except NoSuchElementException:
            return

    @classmethod
    def logout_button(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, '//*[text()="班級管理"]')
        except NoSuchElementException:
            return


class BlissWisdomRollCall(enum.Enum):
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
        def on_rm_error(func: Callable[[Any], None], path: str, _: Any):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        if self.work_path.is_dir():
            shutil.rmtree(self.work_path, onerror=on_rm_error)

    def log_in(self) -> bool:
        self.browser_driver.get(BlissWisdomRollCall.HOME_PAGE.value)

        try:
            WebDriverWait(self.browser_driver, 10).until(lambda d: BlissWisdomRollCallElementFinder.first_login_link(d))
        except TimeoutException:
            return False

        BlissWisdomRollCallElementFinder.account_text_input(self.browser_driver).send_keys(self.config.account)
        BlissWisdomRollCallElementFinder.password_text_input(self.browser_driver).send_keys(self.config.password)

        img_base64: str = BlissWisdomRollCallElementFinder.captcha_image(self.browser_driver).get_attribute(
            'src').removeprefix('data:image/png;base64,')
        fd: int
        f_path: str
        (fd, f_path) = tempfile.mkstemp(suffix='.png')
        os.write(fd, base64.b64decode(img_base64))
        captcha: str = easyocr.Reader(['en'], gpu=False).readtext(f_path)[0][1]
        get_logger(__package__).info(f'Captcha: {captcha}')
        os.close(fd)
        os.remove(f_path)

        BlissWisdomRollCallElementFinder.captcha_text_input(self.browser_driver).send_keys(captcha)
        BlissWisdomRollCallElementFinder.login_button(self.browser_driver).click()

        try:
            WebDriverWait(self.browser_driver, 10).until(lambda d: BlissWisdomRollCallElementFinder.logout_button(d))
        except TimeoutException:
            return False

        time.sleep(10)
        return True
