import dataclasses
import io
import pathlib

import tomli_w


@dataclasses.dataclass
class Config:
    account: str
    password: str
    character: str
    class_name: str
    attendance_urls: list[str]
    google_api_private_key_id: str
    google_api_private_key: str

    def save(self, path: pathlib.Path) -> None:
        f: io.FileIO
        with open(path, 'wb') as f:
            tomli_w.dump(dataclasses.asdict(self), f)
