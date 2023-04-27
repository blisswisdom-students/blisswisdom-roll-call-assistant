import dataclasses
import datetime
import enum
import io
import pathlib
import time
from typing import Any, Optional

import dacite
import googleapiclient.errors
import tomli
from PySide6.QtCore import QMutex, QObject, QThread, Signal

import blisswisdom_roll_call_assistant_sdk as sdk


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


class MainWindowModel(QObject):
    importing_channel: Signal = Signal(bool)
    logging_in_channel: Signal = Signal(bool)
    captcha_path_channel: Signal = Signal(pathlib.Path)
    status_channel: Signal = Signal(str)
    job_result_channel: Signal = Signal(JobResult)

    def __init__(self, config_path: pathlib.Path) -> None:
        super().__init__()
        self._qthread: Optional[QThread] = None
        self._worker: Optional[LogInWorker] = None
        self._in_progress: bool = False
        self._logging_in: bool = False
        self._status: str = ''
        self._captcha_path: Optional[pathlib.Path] = None
        self._job_result: JobResult = JobResult(JobResultCode.UNSET)

        self.job_result_channel.connect(self.on_job_result_changed_from_task)

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

    def save(self) -> None:
        self.config.save(self.config_path)

    def send_captcha(self, captcha: str) -> None:
        if self._worker:
            self._worker.captcha = captcha

    def import_(self) -> None:
        if self._qthread:
            sdk.get_logger(__package__).info('Another task is already running')
            self.status_channel.emit('另一項工作正在執行中')
            return
        self.importing_channel.emit(True)
        sdk.get_logger(__package__).info('Importing ...')
        self.status_channel.emit('開始匯入點名資料 ...')

        self._job_result = JobResult(JobResultCode.UNSET)
        self._qthread = QThread()
        self._qthread.finished.connect(self.on_import_finished)
        self._qthread.start()
        self._worker: ImportWorker = ImportWorker(
            self.config, self.job_result_channel, self.status_channel, self.captcha_path_channel)
        self._worker.moveToThread(self._qthread)
        self._worker.start_signal.emit()
        self._qthread.exec()

    def on_import_finished(self) -> None:
        self.importing_channel.emit(False)
        sdk.get_logger(__package__).info('Imported' if self._job_result.code > 0 else 'Failed to import')
        self.status_channel.emit(f'匯入「{"成功" if self._job_result.code > 0 else "失敗"}」')
        self._qthread = None
        self._worker = None
        self.captcha_path_channel.emit('')
        self._job_result = JobResult(JobResultCode.UNSET)

    def stop_importing(self) -> None:
        sdk.get_logger(__package__).info('Stop importing ...')
        self.status_channel.emit('停止匯入點名資料 ...')
        if self._qthread:
            self._qthread.terminate()
            self._qthread = None
            self._worker = None
            self.captcha_path_channel.emit('')
            self._job_result = JobResult(JobResultCode.UNSET)

    def log_in(self) -> None:
        if self._qthread:
            sdk.get_logger(__package__).info('Another task is already running')
            self.status_channel.emit('另一項工作正在執行中')
            return
        self.logging_in_channel.emit(True)
        sdk.get_logger(__package__).info('Logging in ...')
        self.status_channel.emit('開始登入 ...')

        self._job_result = JobResult(JobResultCode.UNSET)
        self._qthread = QThread()
        self._qthread.finished.connect(self.on_log_in_finished)
        self._qthread.start()
        self._worker: LogInWorker = LogInWorker(
            self.config, self.job_result_channel, self.status_channel, self.captcha_path_channel)
        self._worker.moveToThread(self._qthread)
        self._worker.start_signal.emit()
        self._qthread.exec()

    def on_log_in_finished(self) -> None:
        self.logging_in_channel.emit(False)
        sdk.get_logger(__package__).info('Logged in' if self._job_result.code > 0 else 'Failed to log in')
        self.status_channel.emit(f'登入「{"成功" if self._job_result.code > 0 else "失敗"}」')
        self._qthread = None
        self._worker = None
        self.captcha_path_channel.emit('')
        self._job_result = JobResult(JobResultCode.UNSET)

    def on_job_result_changed_from_task(self, job_result: JobResult) -> None:
        if job_result.code == JobResultCode.UNABLE_TO_INITIALIZE_WEB_DRIVER:
            self.status_channel.emit('無法啟動瀏覽器')
        elif job_result.code == JobResultCode.UNABLE_TO_LOG_IN:
            self.status_channel.emit('無法登入')
        elif job_result.code == JobResultCode.UNABLE_TO_ROLL_CALL:
            self.status_channel.emit(f'無法匯入出席狀況')
        elif job_result.code == JobResultCode.UNABLE_TO_GET_MEMBER_LIST:
            self.status_channel.emit(f'無法取得福智學員平臺名單')
        elif job_result.code == JobResultCode.UNABLE_TO_READ_ATTENDANCE_REPORT_SHEET:
            self.status_channel.emit(f'無法讀取「{job_result.data}」出勤結果表')
        elif job_result.code == JobResultCode.UNABLE_TO_GET_CLASS_DATE:
            self.status_channel.emit('無法取得上課時間')
        elif job_result.code == JobResultCode.NO_LECTURE_TO_ROLL_CALL:
            self.status_channel.emit('無上課時程表，不須點名')
        self._job_result = job_result
        if self._qthread:
            try:
                self._qthread.quit()
            except Exception as e:
                sdk.get_logger(__package__).exception(e)


class LogInWorker(QObject):
    start_signal: Signal = Signal()

    @property
    def captcha(self) -> str:
        self._captcha_mutex.lock()
        captcha: str = self._captcha
        self._captcha_mutex.unlock()
        return captcha

    @captcha.setter
    def captcha(self, captcha: str) -> None:
        self._captcha_mutex.lock()
        self._captcha = captcha
        self._captcha_mutex.unlock()

    def on_captcha_image_downloaded(self, path: pathlib.Path) -> str:
        self.captcha_path_channel.emit(path)
        while not self.captcha:
            time.sleep(0.1)
        return self.captcha

    def on_captcha_sent(self) -> None:
        self.captcha_path_channel.emit('')

    def __init__(
            self,
            config: sdk.Config,
            job_result_channel: Signal,
            status_channel: Signal,
            captcha_path_channel: Signal,
            *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config: sdk.Config = config
        self.job_result_channel: Signal = job_result_channel
        self.status_channel: Signal = status_channel
        self.captcha_path_channel: Signal = captcha_path_channel
        self._captcha: str = ''
        self._captcha_mutex: QMutex = QMutex()

        self.start_signal.connect(self.run)

    def run(self) -> None:
        sbwcp: Optional[sdk.SimpleBlissWisdomCommitteePlatform] = None
        try:
            try:
                sbwcp = sdk.SimpleBlissWisdomCommitteePlatform(self.config)
            except Exception:
                sdk.get_logger(__package__).info('Unable to launch the browser')
                self.job_result_channel.emit(JobResult(JobResultCode.UNABLE_TO_INITIALIZE_WEB_DRIVER))
                raise

            try:
                sbwcp.log_in(self.on_captcha_image_downloaded, self.on_captcha_sent)
            except Exception:
                sdk.get_logger(__package__).info('Unable to log in')
                self.job_result_channel.emit(JobResult(JobResultCode.UNABLE_TO_LOG_IN))
                raise
        except Exception as e:
            sdk.get_logger(__package__).exception(e)
        else:
            self.job_result_channel.emit(JobResult(JobResultCode.SUCCEEDED))
        finally:
            time.sleep(3)
            try:
                if sbwcp:
                    sbwcp.quit()
            except Exception as e:
                sdk.get_logger(__package__).exception(e)


class ImportWorker(LogInWorker):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def on_member_roll_called(self, member: sdk.RollCallListMember) -> None:
        sdk.get_logger(__package__).info(f'{member=}')
        self.status_channel.emit(
            f'{member.group_number}-{member.name}：{member.state if member.state else "無資料"}')

    def run(self) -> None:
        try:
            try:
                sbwcp: sdk.SimpleBlissWisdomCommitteePlatform = sdk.SimpleBlissWisdomCommitteePlatform(self.config)
            except Exception:
                self.job_result_channel.emit(JobResult(JobResultCode.UNABLE_TO_INITIALIZE_WEB_DRIVER))
                raise

            try:
                sdk.get_logger(__package__).info('Logging in ...')
                self.status_channel.emit('登入 ...')
                sbwcp.log_in(self.on_captcha_image_downloaded, self.on_captcha_sent)
            except Exception:
                sdk.get_logger(__package__).info('Unable to log in')
                self.job_result_channel.emit(JobResult(JobResultCode.UNABLE_TO_LOG_IN))
                raise

            try:
                sdk.get_logger(__package__).info('Detecting the class date ...')
                self.status_channel.emit('偵測上課時間 ...')
                date: datetime.date = sbwcp.get_activated_roll_call_class_date()
            except sdk.NoLectureToRollCallError:
                sdk.get_logger(__package__).info('No lecture to roll call')
                self.job_result_channel.emit(JobResult(JobResultCode.NO_LECTURE_TO_ROLL_CALL))
                raise
            except Exception:
                sdk.get_logger(__package__).info('Unable to get the class date')
                self.job_result_channel.emit(JobResult(JobResultCode.UNABLE_TO_GET_CLASS_DATE))
                raise

            attendance_records: list[sdk.AttendanceRecord] = list()
            arsl: sdk.AttendanceReportSheetLink
            for arsl in self.config.attendance_report_sheet_links:
                if not arsl.link:
                    continue
                try:
                    sdk.get_logger(__package__).info(f'Obtaining the member statuses of group {arsl.note} ...')
                    self.status_channel.emit(f'取得「{arsl.note}」出席狀況 ...')
                    attendance_records += sdk.AttendanceSheetParserBuilder(
                        link=arsl.link, google_api_private_key_id=self.config.google_api_private_key_id,
                        google_api_private_key=self.config.google_api_private_key).build() \
                        .get_attendance_records_by_date(date)
                    time.sleep(1)
                except googleapiclient.errors.HttpError:
                    sdk.get_logger(__package__).info('Unable to read the attendance sheet')
                    self.job_result_channel.emit(JobResult(
                        code=JobResultCode.UNABLE_TO_READ_ATTENDANCE_REPORT_SHEET, data=arsl.note))
                    raise
                except sdk.NoRelevantStatusError:
                    sdk.get_logger(__package__).info('No data of the date in the attendance sheet')
                    self.status_channel.emit(f'「{arsl.note}」無本次上課出席記錄')
            sdk.get_logger(__package__).info(f'{attendance_records=}')

            try:
                sdk.get_logger(__package__).info('Obtaining the member list on the committee platform ...')
                self.status_channel.emit('取得學員平臺學員名單 ...')
                roll_call_list_members: list[sdk.RollCallListMember] = \
                    sbwcp.get_activated_roll_call_list_members(no_state=True)
            except Exception:
                sdk.get_logger(__package__).info('Unable to obtain the roll call list')
                self.job_result_channel.emit(JobResult(JobResultCode.UNABLE_TO_GET_MEMBER_LIST))
                raise
            sdk.get_logger(__package__).info(f'{roll_call_list_members=}')

            member: sdk.RollCallListMember
            gnum_name_member_dict: dict[str, sdk.RollCallListMember] = \
                {f'{member.group_number}-{member.name}': member for member in roll_call_list_members}

            record: sdk.AttendanceRecord
            for record in attendance_records:
                state: sdk.RollCallState = sdk.RollCallState.PRESENT if \
                    record.state in [sdk.AttendanceState.IN_PERSON, sdk.AttendanceState.ONLINE] else \
                    sdk.RollCallState(record.state)
                key: str = f'{record.group_number}-{record.name}'
                if key in gnum_name_member_dict:
                    gnum_name_member_dict[key].state = state

            try:
                sbwcp.roll_call(roll_call_list_members, self.on_member_roll_called)
            except Exception:
                sdk.get_logger(__package__).info('Unable to roll call')
                self.job_result_channel.emit(JobResult(JobResultCode.UNABLE_TO_ROLL_CALL))
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
                self.status_channel.emit(f'不在點名系統的人員：{", ".join(sorted(list(members_not_on_the_platform)))}')
            if members_not_on_the_attendance_feedback:
                sdk.get_logger(__package__).info(f'{members_not_on_the_attendance_feedback=}')
                self.status_channel.emit(
                    f'不在出席記錄試算表的人員：{", ".join(sorted(list(members_not_on_the_attendance_feedback)))}')
        except Exception as e:
            sdk.get_logger(__package__).exception(e)
        else:
            self.job_result_channel.emit(JobResult(JobResultCode.SUCCEEDED))
        finally:
            time.sleep(3)
            try:
                sbwcp.quit()
            except Exception as e:
                sdk.get_logger(__package__).exception(e)
