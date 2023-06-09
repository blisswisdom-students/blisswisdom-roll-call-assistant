import base64
import dataclasses
import datetime
import enum
import itertools
import logging
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import time
from typing import Any, Callable, Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from .config import Config
from .log import get_logger
from .util import get_cache_dir


class RollCallState(enum.StrEnum):
    PRESENT: str = '出席'
    LEAVE: str = '請假'
    ABSENT: str = '未出席'
    UNKNOWN: str = '不明'


@dataclasses.dataclass
class RollCallListMember:
    name: str
    group_number: str
    page_number: int
    state: Optional[RollCallState]


class BlissWisdomCommitteePlatformElement(enum.Enum):
    ACCOUNT_INPUT_BOX: tuple[str, str] = (By.XPATH, '//input[@placeholder="請輸入帳號"]')
    PASSWORD_INPUT_BOX: tuple[str, str] = (By.XPATH, '//input[@placeholder="請輸入密碼"]')
    CAPTCHA_INPUT_BOX: tuple[str, str] = (By.XPATH, '//input[@placeholder="請輸入圖片中之文字"]')
    CAPTCHA_IMAGE: tuple[str, str] = (By.XPATH, '//img[contains(@src, ";base64,")]')
    CAPTCHA_WRONG_NOTICE: tuple[str, str] = (By.XPATH, '//div[text()="驗證碼錯誤，請重新輸入!!"]')
    LOGIN_BUTTON: tuple[str, str] = (By.XPATH, '//button[contains(span, "登入")]')
    LOGOUT_BUTTON: tuple[str, str] = (By.XPATH, '//a[@class="logoutBtn"]')
    CLASS_MANAGEMENT_SIDE_MENU: tuple[str, str] = (By.XPATH, '//div[@class="q-item-label" and text()="班級管理"')
    FORMAL_CLASS_ROLL_CALL_SIDE_MENU: tuple[str, str] = (
        By.XPATH, '//div[@class="q-item-label" AND text()="研討班點名"')
    CLASS_NAME_DROPDOWN_MENU: tuple[str, str] = (
        By.XPATH, '//span[text()="班級名稱"]/../..//div[contains(@class, " q-if-focusable ")]')
    ROLL_CALL_BUTTON: tuple[str, str] = (By.XPATH, '//button[contains(span, "點名")]')
    NO_LECTURE_TO_ROLL_CALL_NOTIFICATION: tuple[str, str] = (
        By.XPATH, '//*[contains(text(), "無上課時程表, 不須點名")]')
    ROW_PER_PAGE_DROPDOWN_MENU: tuple[str, str] = (
        By.XPATH, '//span[contains(@class, " q-if-addon-visible") and text()="行/頁"]')
    NEXT_PAGE_BUTTON: tuple[str, str] = (
        By.XPATH, '//i[text()="chevron_right"]/parent::a[contains(@class, "pagination__navigation")]')
    ENABLED_NEXT_PAGE_BUTTON: tuple[str, str] = (
        By.XPATH, '//i[text()="chevron_right"]/parent::a[@class="pagination__navigation"]')
    DISABLED_NEXT_PAGE_BUTTON: tuple[str, str] = (
        By.XPATH,
        '//i[text()="chevron_right"]/parent::a[@class="pagination__navigation pagination__navigation--disabled"]')
    ROLL_CALL_TABLE_GROUP_NUMBERS: tuple[str, str] = (
        By.XPATH, '//table[@class="datatable-resultset table-striped"]/tr/td[1]/div')
    ROLL_CALL_TABLE_NAMES: tuple[str, str] = (
        By.XPATH, '//table[@class="datatable-resultset table-striped"]/tr/td[2]/div')
    ROLL_CALL_TABLE_STATES: tuple[str, str] = (
        By.XPATH, '//table[@class="datatable-resultset table-striped"]'
                  '//div[contains(@class, "q-option-inner relative-position active")]')
    CLASS_DATE: tuple[str, str] = (By.XPATH, '//span[text()="上課日期："]/parent::div/following-sibling::div')
    CURRENT_PAGE_SPAN: tuple[str, str] = (By.XPATH, '//a[@class="pagination__item pagination__item--active"]/span')

    @classmethod
    def class_name_item(cls, class_name: str) -> tuple[str, str]:
        return By.XPATH, f'//div[text()="{class_name}"]'

    @classmethod
    def page_button(cls, page_number: int) -> tuple[str, str]:
        return By.XPATH, f'//span[text()="{page_number}"]/parent::a[contains(@class, "pagination__item")]'

    @classmethod
    def current_page_button(cls, page_number: int) -> tuple[str, str]:
        return By.XPATH, \
            f'//span[text()="{page_number}"]/parent::a[@class="pagination__item pagination__item--active"]'

    @classmethod
    def not_current_page_button(cls, page_number: int) -> tuple[str, str]:
        return By.XPATH, f'//span[text()="{page_number}"]/parent::a[@class="pagination__item"]'

    @classmethod
    def member_state_radio_button(cls, member: RollCallListMember) -> tuple[str, str]:
        state_value: str = 'B'
        if member.state == RollCallState.PRESENT:
            state_value = 'D'
        elif member.state == RollCallState.LEAVE:
            state_value = 'C'
        return By.XPATH, \
            f'//table[@class="datatable-resultset table-striped"]/tr/td[2]/div[text()="{member.name}"]' \
            f'/parent::td/preceding-sibling::td/div[text()="{member.group_number}"]' \
            f'/parent::td/parent::tr//td/div/div/div/div/div/div/input[@value="{state_value}"]' \
            f'/parent::div/parent::div'

    @classmethod
    def active_member_state_radio_button(cls, member: RollCallListMember) -> tuple[str, str]:
        state_value: str = 'B'
        if member.state == RollCallState.PRESENT:
            state_value = 'D'
        elif member.state == RollCallState.LEAVE:
            state_value = 'C'
        return By.XPATH, \
            f'//table[@class="datatable-resultset table-striped"]/tr/td[2]/div[text()="{member.name}"]' \
            f'/parent::td/preceding-sibling::td/div[text()="{member.group_number}"]' \
            f'/parent::td/parent::tr//td/div/div/div/div/div/div[contains(@class, " active ")]' \
            f'/input[@value="{state_value}"]/parent::div/parent::div'


class BlissWisdomCommitteePlatformPage(enum.StrEnum):
    LOGIN: str = 'https://pw.blisswisdom.org/'
    HOME: str = 'https://pw.blisswisdom.org/#/HomePage'
    FORMAL_CLASS_ROLL_CALL: str = 'https://pw.blisswisdom.org/#/School/RollCall'


class NoCaptchaInputError(ValueError):
    pass


class TooManyWrongCaptchaError(ValueError):
    pass


class UnableToLogInError(RuntimeError):
    pass


class NoLectureToRollCallError(RuntimeError):
    pass


class UnableToSwitchPageError(RuntimeError):
    pass


class UnableToGetClassDateError(RuntimeError):
    pass


class UnableToCompleteRollCallError(RuntimeError):
    pass


class SimpleSelenium:
    def __init__(self, action_timeout: int = 10) -> None:
        self.action_timeout: int = action_timeout
        self.work_path: pathlib.Path = get_cache_dir() / 'browser-working-directory'

        self.clear_work_dir()
        if not self.work_path.is_dir():
            self.work_path.mkdir()

        LOGGER.setLevel(logging.INFO)
        os.environ['WDM_PROGRESS_BAR'] = '0'  # WebDriverManager progress bar hangs on some computers

        if os.name == 'nt':
            options: webdriver.EdgeOptions = webdriver.EdgeOptions()
        else:
            options: webdriver.ChromeOptions = webdriver.ChromeOptions()

        options.add_argument(f'user-data-dir={self.work_path}')
        options.add_experimental_option('detach', True)

        if os.name == 'nt':
            service: EdgeService = EdgeService(EdgeChromiumDriverManager().install())
            service.creation_flags = subprocess.CREATE_NO_WINDOW
            self.web_driver: webdriver.Edge = webdriver.Edge(options=options, service=service)
        else:
            self.web_driver: webdriver.Chrome = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    def clear_work_dir(self) -> None:
        def on_rm_error(func: Callable[[Any], None], path: str, _: Any):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        if self.work_path.is_dir():
            shutil.rmtree(self.work_path, onerror=on_rm_error)

    def quit(self) -> None:
        try:
            self.web_driver.quit()
        except Exception as e:
            get_logger(__package__).exception(e)


class SimpleBlissWisdomCommitteePlatform(SimpleSelenium):
    def __init__(self, config: Config, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.config: Config = config
        self.web_driver.maximize_window()

    def log_in(
            self,
            on_captcha_image_downloaded: Callable[[pathlib.Path], str],
            on_captcha_sending: Callable[[], None],
            on_captcha_sent: Callable[[bool], None]) -> None:
        for _ in range(5):
            self.web_driver.get(BlissWisdomCommitteePlatformPage.LOGIN)

            login_page_helper: LoginPageHelper = LoginPageHelper(self.web_driver, self.action_timeout)
            login_page_helper.input_account(self.config.account)
            login_page_helper.input_password(self.config.password)

            img_base64: str = login_page_helper.get_captcha_base64_image()
            fd: int
            f_path: str
            (fd, f_path) = tempfile.mkstemp(suffix='.png')
            os.write(fd, base64.b64decode(img_base64))
            captcha: str = on_captcha_image_downloaded(pathlib.Path(f_path))
            os.close(fd)
            os.remove(f_path)

            if not captcha:
                raise NoCaptchaInputError

            on_captcha_sending()
            login_page_helper.input_captcha(captcha)
            login_page_helper.click_login_button()

            if not login_page_helper.is_captcha_wrong():
                on_captcha_sent(True)
                break
            on_captcha_sent(False)
        else:
            raise TooManyWrongCaptchaError

        if not login_page_helper.is_logged_in():
            raise UnableToLogInError

    def go_to_activated_roll_call_page(self) -> None:
        self.web_driver.get(BlissWisdomCommitteePlatformPage.FORMAL_CLASS_ROLL_CALL)

        roll_call_page_helper: RollCallPageHelper = RollCallPageHelper(self.web_driver, self.action_timeout)
        roll_call_page_helper.choose_class(self.config.class_name)
        roll_call_page_helper.go_to_activated_roll_call_page()

    def get_activated_roll_call_class_date(self) -> datetime.date:
        self.go_to_activated_roll_call_page()

        activated_roll_call_page_helper: ActivatedRollCallPageHelper = \
            ActivatedRollCallPageHelper(self.web_driver, self.action_timeout)
        return activated_roll_call_page_helper.get_class_date()

    def get_activated_roll_call_list_members(self, no_state: bool = False) -> list[RollCallListMember]:
        self.go_to_activated_roll_call_page()

        activated_roll_call_page_helper: ActivatedRollCallPageHelper = \
            ActivatedRollCallPageHelper(self.web_driver, self.action_timeout)
        return activated_roll_call_page_helper.get_members(no_state)

    def roll_call(
            self, members: list[RollCallListMember],
            processed_call_back: Optional[Callable[[RollCallListMember], None]] = None) -> None:
        processed_members: list[RollCallListMember] = list()
        for _ in range(10):
            self.go_to_activated_roll_call_page()
            processed_members += ActivatedRollCallPageHelper(self.web_driver, self.action_timeout).roll_call(
                members[len(processed_members):], processed_call_back)
            get_logger(__package__).info(f'{processed_members=}')
            get_logger(__package__).info(f'{members=}')
            if processed_members == members:
                break
        else:
            raise UnableToCompleteRollCallError


class PageHelper:
    def __init__(self, web_driver: WebDriver, action_timeout: int) -> None:
        self.web_driver: WebDriver = web_driver
        self.action_timeout: int = action_timeout


class LoginPageHelper(PageHelper):
    def input_account(self, account: str) -> None:
        WebDriverWait(self.web_driver, self.action_timeout).until(
            EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.ACCOUNT_INPUT_BOX.value)).send_keys(account)

    def input_password(self, account: str) -> None:
        WebDriverWait(self.web_driver, self.action_timeout).until(
            EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.PASSWORD_INPUT_BOX.value)).send_keys(account)

    def input_captcha(self, captcha: str) -> None:
        WebDriverWait(self.web_driver, self.action_timeout).until(
            EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.CAPTCHA_INPUT_BOX.value)).clear()
        WebDriverWait(self.web_driver, self.action_timeout).until(
            EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.CAPTCHA_INPUT_BOX.value)).send_keys(captcha)

    def click_login_button(self) -> None:
        WebDriverWait(self.web_driver, self.action_timeout).until(
            EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.LOGIN_BUTTON.value)).click()

    def get_captcha_base64_image(self) -> str:
        return WebDriverWait(self.web_driver, self.action_timeout).until(
            EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.CAPTCHA_IMAGE.value)).get_attribute(
            'src').removeprefix('data:image/png;base64,')

    def is_captcha_wrong(self) -> bool:
        try:
            WebDriverWait(self.web_driver, 2).until(
                EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.CAPTCHA_WRONG_NOTICE.value))
            return True
        except TimeoutException:
            return False

    def is_logged_in(self) -> bool:
        try:
            WebDriverWait(self.web_driver, self.action_timeout).until(
                EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.LOGOUT_BUTTON.value))
            return True
        except TimeoutException:
            return False


class RollCallPageHelper(PageHelper):
    def choose_class(self, class_name: str) -> None:
        WebDriverWait(self.web_driver, self.action_timeout).until(
            EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.CLASS_NAME_DROPDOWN_MENU.value)).click()
        WebDriverWait(self.web_driver, self.action_timeout).until(
            EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.class_name_item(class_name))).click()

    def go_to_activated_roll_call_page(self) -> None:
        WebDriverWait(self.web_driver, self.action_timeout).until(
            EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.ROLL_CALL_BUTTON.value)).click()
        try:
            WebDriverWait(self.web_driver, 3).until(
                EC.element_to_be_clickable(
                    BlissWisdomCommitteePlatformElement.NO_LECTURE_TO_ROLL_CALL_NOTIFICATION.value))
            raise NoLectureToRollCallError
        except TimeoutException:
            pass
        try:
            WebDriverWait(self.web_driver, self.action_timeout).until(
                EC.element_to_be_clickable(
                    BlissWisdomCommitteePlatformElement.ROW_PER_PAGE_DROPDOWN_MENU.value))
        except TimeoutException:
            raise UnableToSwitchPageError


class TablePageHelper(PageHelper):
    def is_on_page(self, page_number: int) -> bool:
        try:
            WebDriverWait(self.web_driver, self.action_timeout).until(
                EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.page_button(page_number)))
        except TimeoutException:
            raise UnableToSwitchPageError

        try:
            self.web_driver.find_element(*BlissWisdomCommitteePlatformElement.current_page_button(page_number))
            return True
        except NoSuchElementException:
            return False

    def go_to_page(self, page_number: int) -> None:
        try:
            target_page_button: WebElement = WebDriverWait(self.web_driver, self.action_timeout).until(
                EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.not_current_page_button(page_number)))
        except TimeoutException:
            raise UnableToSwitchPageError

        action_helper: ActionHelper = ActionHelper(self.web_driver)
        action_helper.scroll_to(target_page_button, offset_x=-180)
        target_page_button.click()

        if not self.is_on_page(page_number):
            raise UnableToSwitchPageError

    def get_current_page(self) -> int:
        try:
            return int(WebDriverWait(self.web_driver, self.action_timeout).until(
                EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.CURRENT_PAGE_SPAN.value)).text)
        except TimeoutException:
            raise UnableToSwitchPageError

    def go_to_next_page(self) -> None:
        original_page: int = self.get_current_page()

        try:
            enabled_next_page_button: WebElement = WebDriverWait(self.web_driver, self.action_timeout).until(
                EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.ENABLED_NEXT_PAGE_BUTTON.value))
        except TimeoutException:
            raise UnableToSwitchPageError

        action_helper: ActionHelper = ActionHelper(self.web_driver)
        action_helper.scroll_to(enabled_next_page_button, offset_x=-180)
        enabled_next_page_button.click()

        if self.get_current_page() != original_page + 1:
            raise UnableToSwitchPageError

    def is_on_last_page(self) -> bool:
        try:
            WebDriverWait(self.web_driver, self.action_timeout).until(
                EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.NEXT_PAGE_BUTTON.value))
        except TimeoutException:
            raise RuntimeError

        try:
            self.web_driver.find_element(
                *BlissWisdomCommitteePlatformElement.DISABLED_NEXT_PAGE_BUTTON.value)
            return True
        except NoSuchElementException:
            return False


class ActivatedRollCallPageHelper(TablePageHelper):
    def get_class_date(self) -> datetime.date:
        try:
            date_text: str = WebDriverWait(self.web_driver, self.action_timeout).until(
                EC.element_to_be_clickable(BlissWisdomCommitteePlatformElement.CLASS_DATE.value)).text
            date: datetime.date = datetime.datetime.strptime(date_text, '%Y/%m/%d').date()
        except TimeoutException:
            raise UnableToGetClassDateError
        return date

    def get_members(self, ignore_state: bool = False) -> list[RollCallListMember]:
        res: list[RollCallListMember] = list()

        while True:
            e: WebElement
            group_numbers: list[str] = list()
            for e in self.web_driver.find_elements(
                    *BlissWisdomCommitteePlatformElement.ROLL_CALL_TABLE_GROUP_NUMBERS.value):
                group_numbers.append(e.text)

            group_names: list[str] = list()
            for e in self.web_driver.find_elements(*BlissWisdomCommitteePlatformElement.ROLL_CALL_TABLE_NAMES.value):
                group_names.append(e.text)

            states: list[RollCallState] = list()
            if not ignore_state:
                for e in self.web_driver.find_elements(
                        *BlissWisdomCommitteePlatformElement.ROLL_CALL_TABLE_STATES.value):
                    v: str = e.find_element(By.XPATH, './input').get_attribute('value')
                    if v == 'D':
                        state: RollCallState = RollCallState.PRESENT
                    elif v == 'C':
                        state: RollCallState = RollCallState.LEAVE
                    else:
                        state: RollCallState = RollCallState.ABSENT
                    states.append(state)

            res += map(
                lambda t: RollCallListMember(name=t[0], group_number=t[1], page_number=t[2], state=t[3]),
                zip(group_names,
                    group_numbers,
                    itertools.repeat(self.get_current_page()),
                    itertools.repeat(None) if ignore_state else states))

            if self.is_on_last_page():
                break

            self.go_to_next_page()
            time.sleep(1)
        return res

    def roll_call(
            self, members: list[RollCallListMember],
            processed_call_back: Optional[Callable[[RollCallListMember], None]] = None) -> list[RollCallListMember]:
        processed_members: list[RollCallListMember] = list()
        try:
            member: RollCallListMember
            for member in members:
                get_logger(__package__).info(f'{member=}')
                if not self.is_on_page(member.page_number):
                    self.go_to_page(member.page_number)
                if member.state:
                    element: WebElement = WebDriverWait(self.web_driver, self.action_timeout).until(
                        EC.element_to_be_clickable(
                            BlissWisdomCommitteePlatformElement.member_state_radio_button(member)))
                    already_roll_called: bool = False
                    try:
                        self.web_driver.find_element(
                            *BlissWisdomCommitteePlatformElement.active_member_state_radio_button(member))
                        already_roll_called: bool = True
                    except NoSuchElementException:
                        pass
                    if not already_roll_called:
                        action_helper: ActionHelper = ActionHelper(self.web_driver)
                        action_helper.scroll_to(element, offset_y=-100)
                        element.click()
                        time.sleep(1)
                processed_members.append(member)
                if processed_call_back:
                    processed_call_back(member)
        except Exception as e:
            get_logger(__package__).exception(e)
        return processed_members


class ActionHelper:
    def __init__(self, web_driver: WebDriver) -> None:
        self.web_driver: WebDriver = web_driver

    def scroll_to(self, element: WebElement, align_to_top: bool = True, offset_x: int = 0, offset_y: int = 0) -> None:
        self.web_driver.execute_script(f'arguments[0].scrollIntoView({str(align_to_top).lower()});', element)
        self.web_driver.execute_script(f'window.scrollBy({offset_x}, {offset_y})')

    @classmethod
    def scroll_to_end(cls, driver: WebDriver) -> None:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
