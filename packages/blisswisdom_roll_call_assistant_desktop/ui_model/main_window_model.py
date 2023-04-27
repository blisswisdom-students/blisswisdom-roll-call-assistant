import dataclasses
import datetime
import enum
import io
import pathlib
import threading
import time
from typing import Any, Optional

import dacite
import googleapiclient.errors
import tomli
from PySide6.QtCore import QThread, Signal

import blisswisdom_roll_call_assistant_sdk as sdk
from .ui_model import BaseUIModel


class JobResultCode(enum.IntEnum):
    SUCCEEDED: int = 1
    UNSET: int = 0
    UNABLE_TO_INITIALIZE_WEB_DRIVER: int = -1
    UNABLE_TO_LOG_IN: int = -2
    NO_LECTURE_TO_ROLL_CALL: int = -3
    UNABLE_TO_GET_CLASS_DATE: int = -4
    UNABLE_TO_GET_MEMBER_LIST: int = -5
    UNABLE_TO_ROLL_CALL: int = -6
    UNABLE_TO_READ_ATTENDANCE_REPORT_SHEET: int = -7


@dataclasses.dataclass
class JobResult:
    code: JobResultCode
    data: Any = None


class MainWindowModel(BaseUIModel):
    def __init__(self, config_path: pathlib.Path) -> None:
        super().__init__()
        self._qthread: Optional[QThread] = None
        self._in_progress: bool = False
        self._logging_in: bool = False
        self._status: str = ''
        self.job_result: JobResult = JobResult(JobResultCode.UNSET)
        self.captcha: str = ''
        self._captcha_path: Optional[pathlib.Path] = None
        self.captcha_lock: threading.Lock = threading.Lock()

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
            self.config = sdk.Config(
                account='',
                password='',
                character='',
                class_name='',
                google_api_private_key_id='',
                google_api_private_key='',
                attendance_report_sheet_links=list())
            self.config.save(config_path)

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
    def class_name(self) -> str:
        return self.config.class_name

    @class_name.setter
    def class_name(self, value: str) -> None:
        self.config.class_name = value

    @property
    def google_api_private_key_id(self) -> str:
        return self.config.google_api_private_key_id

    @google_api_private_key_id.setter
    def google_api_private_key_id(self, value: str) -> None:
        self.config.google_api_private_key_id = value

    @property
    def google_api_private_key(self) -> str:
        return self.config.google_api_private_key

    @google_api_private_key.setter
    def google_api_private_key(self, value: str) -> None:
        self.config.google_api_private_key = value

    @property
    def attendance_report_sheet_links(self) -> list[sdk.AttendanceReportSheetLink]:
        return self.config.attendance_report_sheet_links

    @attendance_report_sheet_links.setter
    def attendance_report_sheet_links(self, value: list[sdk.AttendanceReportSheetLink]) -> None:
        self.config.attendance_report_sheet_links = value

    @property
    def captcha_path(self) -> pathlib.Path:
        return self._captcha_path

    @captcha_path.setter
    def captcha_path(self, value: pathlib.Path) -> None:
        self._captcha_path = value

    def save(self) -> None:
        self.config.save(self.config_path)

    def start(self) -> None:
        if self._qthread:
            sdk.get_logger(__package__).info('Another task is already running')
            self.status = '另一項工作正在執行中'
            return
        self.in_progress = True
        sdk.get_logger(__package__).info('Importing ...')
        self.status = '開始匯入點名資料 ...'
        self._qthread = Start(self)
        self._qthread.status.connect(self.on_status_updated)
        self._qthread.finished.connect(self.on_start_finished)
        self.job_result = JobResult(JobResultCode.UNSET)
        self._qthread.start()

    def on_status_updated(self, status: str) -> None:
        self.status = status

    def on_start_finished(self) -> None:
        self.in_progress = False
        sdk.get_logger(__package__).info('Imported' if self.job_result.code > 0 else 'Failed to import')
        self.status = f'匯入「{"成功" if self.job_result.code > 0 else "失敗"}」'
        self._qthread = None
        self.captcha = ''
        self.captcha_path = None
        self.job_result = JobResult(JobResultCode.UNSET)

    def stop(self) -> None:
        sdk.get_logger(__package__).info('Stop importing ...')
        self.status = '停止匯入點名資料 ...'
        if self._qthread:
            self._qthread.terminate()
            self._qthread = None
            self.captcha = ''
            self.captcha_path = None
            self.job_result = JobResult(JobResultCode.UNSET)

    def log_in(self) -> None:
        if self._qthread:
            sdk.get_logger(__package__).info('Another task is already running')
            self.status = '另一項工作正在執行中'
            return
        self.logging_in = True
        sdk.get_logger(__package__).info('Logging in ...')
        self.status = '開始登入 ...'
        self._qthread = LogIn(self)
        self._qthread.status.connect(self.on_status_updated)
        self._qthread.finished.connect(self.on_log_in_finished)
        self.job_result = JobResult(JobResultCode.UNSET)
        self._qthread.start()

    def on_log_in_finished(self) -> None:
        self.logging_in = False
        sdk.get_logger(__package__).info('Logged in' if self.job_result.code > 0 else 'Failed to log in')
        self.status = f'登入「{"成功" if self.job_result.code > 0 else "失敗"}」'
        self._qthread = None
        self.captcha = ''
        self.captcha_path = None
        self.job_result = JobResult(JobResultCode.UNSET)

    def on_captcha_got(self, captcha_path: pathlib.Path) -> str:
        self.captcha_path = captcha_path
        while True:
            with self.captcha_lock:
                if self.captcha:
                    return self.captcha
            time.sleep(0.1)

    def on_captcha_sent(self) -> None:
        self.captcha_path = None


class Start(QThread):
    # https://stackoverflow.com/a/36561787/1592410
    status: Signal = Signal(str)

    def __init__(self, main_window_model: MainWindowModel, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.main_window_model: MainWindowModel = main_window_model
        self.config: sdk.Config = main_window_model.config

    def on_member_roll_called(self, member: sdk.RollCallListMember) -> None:
        sdk.get_logger(__package__).info(f'{member=}')
        self.status.emit(f'{member.group_number}-{member.name}：{member.state.value if member.state else "無資料"}')

    def run(self) -> None:
        try:
            try:
                sbwcp: sdk.SimpleBlissWisdomCommitteePlatform = sdk.SimpleBlissWisdomCommitteePlatform(self.config)
            except Exception:
                sdk.get_logger(__package__).info('Unable to launch the browser')
                self.status.emit('無法啟動瀏覽器')
                self.main_window_model.job_result = JobResult(JobResultCode.UNABLE_TO_INITIALIZE_WEB_DRIVER)
                raise

            try:
                sdk.get_logger(__package__).info('Logging in ...')
                self.status.emit('登入 ...')
                sbwcp.log_in(self.main_window_model.on_captcha_got, self.main_window_model.on_captcha_sent)
            except Exception:
                sdk.get_logger(__package__).info('Unable to log in')
                self.status.emit('無法登入')
                self.main_window_model.job_result = JobResult(JobResultCode.UNABLE_TO_LOG_IN)
                raise

            try:
                sdk.get_logger(__package__).info('Detecting the class date ...')
                self.status.emit('偵測上課時間 ...')
                date: datetime.date = sbwcp.get_activated_roll_call_class_date()
            except sdk.NoLectureToRollCallError:
                sdk.get_logger(__package__).info('No lecture to roll call')
                self.status.emit('無上課時程表，不須點名')
                self.main_window_model.job_result = JobResult(JobResultCode.NO_LECTURE_TO_ROLL_CALL)
                raise
            except Exception:
                sdk.get_logger(__package__).info('Unable to get the class date')
                self.status.emit('無法取得上課時間')
                self.main_window_model.job_result = JobResult(JobResultCode.UNABLE_TO_GET_CLASS_DATE)
                raise

            attendance_records: list[sdk.AttendanceRecord] = list()
            arsl: sdk.AttendanceReportSheetLink
            for arsl in self.main_window_model.attendance_report_sheet_links:
                if not arsl.link:
                    continue
                try:
                    sdk.get_logger(__package__).info(f'Obtaining the member statuses of group {arsl.note} ...')
                    self.status.emit(f'取得「{arsl.note}」出席狀況 ...')
                    attendance_records += sdk.AttendanceSheetParserBuilder(
                        link=arsl.link, google_api_private_key_id=self.config.google_api_private_key_id,
                        google_api_private_key=self.config.google_api_private_key).build() \
                        .get_attendance_records_by_date(date)
                except googleapiclient.errors.HttpError:
                    sdk.get_logger(__package__).info('Unable to read the attendance sheet')
                    self.status.emit(f'無法讀取「{arsl.note}」出勤結果表')
                    self.main_window_model.job_result = JobResult(
                        code=JobResultCode.UNABLE_TO_READ_ATTENDANCE_REPORT_SHEET,
                        data=arsl.note)
                    raise
                except sdk.NoRelevantStatusError:
                    sdk.get_logger(__package__).info('No data of the date in the attendance sheet')
                    self.status.emit(f'「{arsl.note}」無本次上課出席記錄')
            sdk.get_logger(__package__).info(f'{attendance_records=}')

            try:
                sdk.get_logger(__package__).info('Obtaining the member list on the committee platform ...')
                self.status.emit('取得學員平臺學員名單 ...')
                roll_call_list_members: list[sdk.RollCallListMember] = \
                    sbwcp.get_activated_roll_call_list_members(no_state=True)
            except Exception:
                sdk.get_logger(__package__).info('Unable to obtain the roll call list')
                self.status.emit(f'無法取得福智學員平臺名單')
                self.main_window_model.job_result = JobResult(JobResultCode.UNABLE_TO_GET_MEMBER_LIST)
                raise
            sdk.get_logger(__package__).info(f'{roll_call_list_members=}')

            member: sdk.RollCallListMember
            gnum_name_member_dict: dict[str, sdk.RollCallListMember] = \
                {f'{member.group_number}-{member.name}': member for member in roll_call_list_members}

            record: sdk.AttendanceRecord
            for record in attendance_records:
                state: sdk.RollCallState = sdk.RollCallState.PRESENT if \
                    record.state in [sdk.AttendanceState.IN_PERSON, sdk.AttendanceState.ONLINE] else \
                    sdk.RollCallState(record.state.value)
                key: str = f'{record.group_number}-{record.name}'
                if key in gnum_name_member_dict:
                    gnum_name_member_dict[key].state = state

            try:
                sbwcp.roll_call(roll_call_list_members, self.on_member_roll_called)
            except Exception:
                sdk.get_logger(__package__).info('Unable to roll call')
                self.status.emit(f'無法匯入出席狀況')
                self.main_window_model.job_result = JobResult(JobResultCode.UNABLE_TO_ROLL_CALL)
                raise

            attendance_list_group_number_name_set: set[str] = set(
                map(lambda a: f'{a.group_number}-{a.name}', attendance_records))
            roll_call_list_group_number_name_set: set[str] = set(
                map(lambda m: f'{m.group_number}-{m.name}', roll_call_list_members))

            members_not_on_the_platform: set[str] = \
                attendance_list_group_number_name_set - roll_call_list_group_number_name_set
            members_not_on_the_attendance_feedback: set[str] = \
                roll_call_list_group_number_name_set - attendance_list_group_number_name_set
            if members_not_on_the_platform:
                sdk.get_logger(__package__).info(f'{members_not_on_the_platform=}')
                self.main_window_model.status = \
                    f'不在點名系統的人員：{", ".join(sorted(list(members_not_on_the_platform)))}'
            if members_not_on_the_attendance_feedback:
                sdk.get_logger(__package__).info(f'{members_not_on_the_attendance_feedback=}')
                self.main_window_model.status = \
                    f'不在出席記錄試算表的人員：{", ".join(sorted(list(members_not_on_the_attendance_feedback)))}'
        except Exception as e:
            sdk.get_logger(__package__).exception(e)
        else:
            self.main_window_model.job_result = JobResult(JobResultCode.SUCCEEDED)
        finally:
            time.sleep(3)
            try:
                sbwcp.quit()
            except Exception as e:
                sdk.get_logger(__package__).exception(e)


class LogIn(QThread):
    # https://stackoverflow.com/a/36561787/1592410
    status: Signal = Signal(str)

    def __init__(self, main_window_model: MainWindowModel, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.main_window_model: MainWindowModel = main_window_model
        self.config: sdk.Config = main_window_model.config

    def run(self) -> None:
        sbwcp: Optional[sdk.SimpleBlissWisdomCommitteePlatform] = None
        try:
            try:
                sbwcp = sdk.SimpleBlissWisdomCommitteePlatform(self.config)
            except Exception:
                sdk.get_logger(__package__).info('Unable to launch the browser')
                self.status.emit('無法啟動瀏覽器')
                self.main_window_model.job_result = JobResult(JobResultCode.UNABLE_TO_INITIALIZE_WEB_DRIVER)
                raise

            try:
                sbwcp.log_in(self.main_window_model.on_captcha_got, self.main_window_model.on_captcha_sent)
            except Exception:
                sdk.get_logger(__package__).info('Unable to log in')
                self.status.emit('無法登入')
                self.main_window_model.job_result = JobResult(JobResultCode.UNABLE_TO_LOG_IN)
                raise
        except Exception as e:
            sdk.get_logger(__package__).exception(e)
        else:
            self.main_window_model.job_result = JobResult(JobResultCode.SUCCEEDED)
        finally:
            time.sleep(3)
            try:
                if sbwcp:
                    sbwcp.quit()
            except Exception as e:
                sdk.get_logger(__package__).exception(e)
