import dataclasses
import datetime
import enum
import json
import os
import tempfile

import pygsheets

from .log import get_logger


class AttendanceState(enum.Enum):
    IN_PERSON: str = '現場'
    ONLINE: str = '線上'
    LEAVE: str = '請假'
    ABSENT: str = '未出席'


@dataclasses.dataclass
class AttendanceRecord:
    name: str
    state: AttendanceState
    group_number: int
    date: datetime.date


def convert_to_name(text: str) -> str:
    c: str
    for c in '[':
        if c in text:
            text = text[text.index(c) + 1:]
    for c in '](（':
        if c in text:
            text = text[:text.index(c)]
    return text.strip()


def convert_to_group_number(text: str) -> int:
    c: str
    for c in '第':
        if c in text:
            text = text[text.index(c) + 1:]
    for c in '組':
        if c in text:
            text = text[:text.index(c)]
    return int(text.strip())


def convert_to_date(text: str) -> datetime.date:
    return datetime.datetime.strptime(text.strip(), '%Y/%m/%d').date()


def get_attendance_records(
        date: datetime.date,
        attendance_sheet_url: str,
        google_api_private_key_id: str,
        google_api_private_key: str) -> list[AttendanceRecord]:
    res: list[AttendanceRecord] = list()
    f_path: str = ''
    try:
        fd: int
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

        wks: pygsheets.Worksheet = pygsheets.authorize(service_file=f_path).open_by_url(attendance_sheet_url).sheet1

        names: list[str] = list()
        last_relevant_column_index: int = -1
        i: int
        cell: pygsheets.Cell
        for i, cell in enumerate(wks.get_row(1, returnas='cells', include_tailing_empty=False)[3:]):
            if cell.value_unformatted.startswith('請假原因：'):
                break
            names.append(convert_to_name(cell.value_unformatted))
            last_relevant_column_index = i + 4
        get_logger(__package__).info(f'{names=}')
        get_logger(__package__).info(f'{last_relevant_column_index=}')

        last_relevant_row_index: int = -1
        for i, cell in enumerate(wks.get_col(2, returnas='cells', include_tailing_empty=False,
                                             date_time_render_option=pygsheets.DateTimeRenderOption.FORMATTED_STRING)[
                                 1:]):
            value: str = cell.value
            if convert_to_date(value) != date:
                continue
            last_relevant_row_index = i + 2
        get_logger(__package__).info(f'{last_relevant_row_index=}')

        states: list[AttendanceState] = list()
        cell: pygsheets.Cell
        for cell in wks.get_row(
                last_relevant_row_index, returnas='cells',
                include_tailing_empty=False)[3:last_relevant_column_index + 1]:
            states.append(AttendanceState(cell.value_unformatted))
        get_logger(__package__).info(f'{states=}')

        group_number: int = convert_to_group_number(wks.cell((last_relevant_row_index, 3)).value_unformatted)
        get_logger(__package__).info(f'{group_number=}')

        res = list(map(lambda t: AttendanceRecord(
            name=t[0], state=t[1], group_number=group_number, date=date), zip(names, states)))
    finally:
        try:
            if f_path:
                os.remove(f_path)
        except Exception as e:
            get_logger(__package__).exception(e)
    return res
