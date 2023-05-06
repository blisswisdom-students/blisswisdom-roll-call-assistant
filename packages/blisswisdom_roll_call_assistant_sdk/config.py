import dataclasses
import io
import pathlib

import tomli_w


@dataclasses.dataclass
class AttendanceReportSheetLink:
    link: str
    note: str = ''


@dataclasses.dataclass
class Config:
    account: str
    password: str
    character: str
    class_name: str
    attendance_report_sheet_links: list[AttendanceReportSheetLink]
    google_api_private_key_id: str = '71774a23a697776f9d1108c55ca01d90799633e8'
    google_api_private_key: str = \
        '-----BEGIN PRIVATE KEY-----\\n' \
        'MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC1fYpby7oN2RoY\\n' \
        '0U+7eUTudIXs+m4MrkIfYgQxnWOTFCFg0BsSZ+KX9W17yXRB1EAFUCoyubRpsUFF\\n' \
        'xdIKDG7rygGL7ONSEh/NivpwourGZy56zp/LfE9ZPxRk0VvV3+ujJaU5V+PAFVv7\\n' \
        '7z0HbAlm3eIstM5ms7F2or/ARMVeSdjY85jKkk+qQlRcekCLvdpE7pqggcgHaEIH\\n' \
        'X6Byx64344RNsiSMee4QLVO6TrRtzSBEZa5ZivtAPbZWu/Cl3IpuWdF5+2UsjL5l\\n' \
        'WkOOMNTj/3ktCGRxhcCpgXd8KCj7zrjJODsLw17z/r77XW4oWwR0gVAunxahh4MP\\n' \
        'TZCoxVNtAgMBAAECggEADxK9IgCalDnavALuT1C0E+XjlZn699ylKzwVwxUiRv3e\\n' \
        'A89k4DN2k05T6HsDx8/b/VT6HDpmLH0HQcc7OZBsyfJ+DGQBQTi2IXkQcbhmLVI2\\n' \
        'fwaYKOtLH8toYzMsIGg3htZCka+l/7cGa7cj53Dmmv+EoFfn6Im2DHdZ25salUkC\\n' \
        '9TLK9RecWkWYwQuRXm33svZK4iehdfU+bePAaCTKPWI/fAOkMo+lSn35LE+Ifoon\\n' \
        'FC5pSZ3osFj1GxN9LmTpKkZbUHlvY0SJbbtdlz0eURCCJzRiJtQ8Jsc0TAiaGMBh\\n' \
        'lMxQpHo58PAsxQHQpYoFf+aZtzqr0HsGUz+BDOcu9QKBgQDlQxzrq+vYl8sKoXNU\\n' \
        'aNu5mTUQc0VkPug0Ep33c0P+K6BSKOIDteSv45wJQg7fwi0Y0UzifpZsZSrFuF5w\\n' \
        'LqqI3PaU+nEuBv19isjKQlk/g8vam/pGJCOAk8iyWaLBANHHdUvseZBBYix2P8aj\\n' \
        'hI5SapWFaeh5iRxHNxLPy2Y7iwKBgQDKqCVm57BqSOKpscsfx0thlFmNisKXuhMz\\n' \
        'w6VJDlIMyeBKusuCU+7Y8+1xrooCwlvNZTL4uS0r1ueZ73gQNB9CvyxSPD9kgBn3\\n' \
        'tHs2SwJbeD5hM8OB6G7bJtMy8gjzdp1zRXEbaLkLpHDki05Ie7I20PWj1Uw5JLO4\\n' \
        'eA4m9Dfr5wKBgC2jPICViq9lGCAXn5OwA/1gSDXsHGYmN6cWBagao/BW0uVICiXe\\n' \
        '8ZUp5AfbxIY6ayvDjmCP/nW5ddhCKVp/j6cLBXMGn70f2xpApFPO/WEtZUkxP5Ly\\n' \
        '4rZXtN38BfARr7Da4rBCSrsZReyMKYinfIVffkA+ou5+oshyaCZBQSqdAoGAH0y9\\n' \
        'Chm6q4+6Qk9NegkD4XxSIIRP7bM1iActngzyKzt6ws/64pQoDaYPBEHa2vY9y4lX\\n' \
        'yAaBrYWxm5raxlXmhh6Ur9bSS6llWVasuQP4xzvZFpYyGfxWMs7aS8IKE+A8DTOq\\n' \
        'dntEKUIqlYHWg2dnbQP1DGrDLQg4IcOZG/cYM/0CgYBZWvBoxHt3i3sl5TQllB9V\\n' \
        'BpLCUAfL99RNTNGnnKpLBeAa0ksWWxPIu5sS+BiHzZbyMc1JYCrcBNYgfbKt7gLF\\n' \
        'X6eOqRC2JYwpSLlGUneqQJMHMCZW5AgbS3hknMUGSy52MZl9SFkTr8/4CFqo/kYd\\n' \
        'pQqeciySOj8GFf0SBP7s9g==\\n' \
        '-----END PRIVATE KEY-----\\n'

    def save(self, path: pathlib.Path) -> None:
        f: io.FileIO
        with open(path, 'wb') as f:
            tomli_w.dump(dataclasses.asdict(self), f)
