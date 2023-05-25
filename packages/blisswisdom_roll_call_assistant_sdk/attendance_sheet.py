import abc
import dataclasses
import datetime
import enum
import json
import os
import tempfile

import pygsheets


class NoRelevantStatusError(RuntimeError):
    pass


class UnsupportedSheetError(ValueError):
    pass


class AttendanceState(enum.StrEnum):
    IN_PERSON: str = '現場'
    ONLINE: str = '線上'
    LEAVE: str = '請假'
    ABSENT: str = '未出席'
    UNKNOWN: str = '不明'


@dataclasses.dataclass
class AttendanceRecord:
    name: str
    state: AttendanceState
    group_number: str
    date: datetime.date


class AttendanceSheetHelper:
    @classmethod
    def convert_to_name(cls, text: str) -> str:
        c: str
        for c in '[':
            if c in text:
                text = text[text.index(c) + 1:]
        for c in '](（':
            if c in text:
                text = text[:text.index(c)]
        return text.strip()

    @classmethod
    def convert_to_group_number(cls, text: str) -> str:
        c: str
        return ''.join(c for c in text if c.isdigit())

    @classmethod
    def convert_to_date(cls, text: str) -> datetime.date:
        try:
            return datetime.datetime.strptime(text.strip(), '%Y/%m/%d').date()
        except ValueError:
            return datetime.datetime.strptime(text.strip(), '%m/%d/%Y').date()

    @classmethod
    def convert_to_state_value(cls, text: str) -> str:
        value: str = text.strip()
        state: AttendanceState
        for state in AttendanceState:
            if value.startswith(state):
                value = value[:len(state)]
                break
        else:
            value = AttendanceState.UNKNOWN
        return value


class BaseAttendanceSheetParser(metaclass=abc.ABCMeta):
    def __init__(self, wks: pygsheets.Worksheet) -> None:
        self.wks: pygsheets.Worksheet = wks

    @abc.abstractmethod
    def get_attendance_records_by_date(self, date: datetime.date) -> list[AttendanceRecord]:
        raise NotImplementedError


class AttendanceSheetParser(BaseAttendanceSheetParser):
    def get_relevant_data_index(self, date: datetime.date) -> int:
        relevant_column_index: int
        cell: pygsheets.Cell
        for cell in self.wks.get_row(1, returnas='cell', include_tailing_empty=False)[1:]:
            if AttendanceSheetHelper.convert_to_date(cell.value) == date:
                relevant_column_index = cell.col
                break
        else:
            raise NoRelevantStatusError
        return relevant_column_index

    def get_group_number(self) -> str:
        return AttendanceSheetHelper.convert_to_group_number(self.wks.cell((2, 1)).value)

    def get_attendance_records_by_date(self, date: datetime.date) -> list[AttendanceRecord]:
        res: list[AttendanceRecord] = list()
        name_column: list[pygsheets.Cell] = self.wks.get_col(1, returnas='cell', include_tailing_empty=False)[2:]
        state_column: list[pygsheets.Cell] = self.wks.get_col(
            self.get_relevant_data_index(date), returnas='cell', include_tailing_empty=False)[2:]
        group_number: str = self.get_group_number()
        name_column_cell: pygsheets.Cell
        state_column_cell: pygsheets.Cell
        for name_column_cell, state_column_cell in zip(name_column, state_column):
            if not name_column_cell.value:
                continue
            name: str = AttendanceSheetHelper.convert_to_name(name_column_cell.value)
            state: AttendanceState = AttendanceState(AttendanceSheetHelper.convert_to_state_value(
                state_column_cell.value)) if state_column_cell.value else AttendanceState.ABSENT
            res.append(AttendanceRecord(name=name, state=state, group_number=group_number, date=date))
        return res


class AttendanceFormReportSheetParser(BaseAttendanceSheetParser):
    def get_relevant_data_index(self, date: datetime.date) -> int:
        last_relevant_row_index: int
        cell: pygsheets.Cell
        for cell in reversed(self.wks.get_col(
                2, returnas='cells', include_tailing_empty=False,
                date_time_render_option=pygsheets.DateTimeRenderOption.FORMATTED_STRING)[1:]):
            if AttendanceSheetHelper.convert_to_date(cell.value) == date:
                last_relevant_row_index = cell.row
                break
        else:
            raise NoRelevantStatusError
        return last_relevant_row_index

    def get_group_number_from_row(self, row_index: int) -> str:
        return AttendanceSheetHelper.convert_to_group_number(self.wks.cell((row_index, 3)).value_unformatted)

    def get_attendance_records_by_date(self, date: datetime.date) -> list[AttendanceRecord]:
        res: list[AttendanceRecord] = list()

        last_relevant_row_index: int = self.get_relevant_data_index(date)
        group_number: str = self.get_group_number_from_row(last_relevant_row_index)
        title_row: list[pygsheets.Cell] = self.wks.get_row(1, returnas='cell', include_tailing_empty=False)
        data_row: list[pygsheets.Cell] = self.wks.get_row(
            last_relevant_row_index, returnas='cell', include_tailing_empty=False)

        title_cell: pygsheets.Cell
        data_cell: pygsheets.Cell
        for title_cell, data_cell in zip(title_row, data_row):
            if not title_cell.value.startswith('出席記錄 ['):
                continue

            name: str = AttendanceSheetHelper.convert_to_name(title_cell.value)
            state: AttendanceState = AttendanceState(data_cell.value) if data_cell.value else AttendanceState.ABSENT
            res.append(AttendanceRecord(name=name, state=state, group_number=group_number, date=date))

        return res


class AttendanceSheetParserBuilder:
    def __init__(self, link: str, google_api_private_key_id: str, google_api_private_key: str) -> None:
        self.link: str = link
        self.google_api_private_key_id: str = google_api_private_key_id
        self.google_api_private_key: str = google_api_private_key

        fd: int
        f_path: str
        (fd, f_path) = tempfile.mkstemp(suffix='.json')
        os.write(fd, json.dumps({
            'type': 'service_account',
            'project_id': 'bw-roll-call-assistant',
            'private_key_id': google_api_private_key_id,
            'private_key': google_api_private_key.replace(r'\n', '\n'),
            'client_email': 'roll-call-assistant@bw-roll-call-assistant.iam.gserviceaccount.com',
            'client_id': '109878451176419024232',
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/'
                                    'roll-call-assistant%40bw-roll-call-assistant.iam.gserviceaccount.com',
        }).encode())
        os.close(fd)
        self.wks: pygsheets.Worksheet = pygsheets.authorize(service_file=f_path).open_by_url(link).sheet1
        os.remove(f_path)

    def build(self) -> BaseAttendanceSheetParser:
        first_cell_value: str = self.wks.cell((1, 1)).value
        v: str
        if any([first_cell_value.lower().endswith(v) for v in (' am', ' pm')]) or \
                any([first_cell_value.startswith(v) for v in ('上午 ', '下午 ')]):
            return AttendanceSheetParser(self.wks)
        if first_cell_value in ['Timestamp', '時間戳記']:
            return AttendanceFormReportSheetParser(self.wks)
        raise UnsupportedSheetError
