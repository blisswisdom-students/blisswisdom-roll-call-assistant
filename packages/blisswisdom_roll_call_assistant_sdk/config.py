import dataclasses
import io
import pathlib

import tomli_w


@dataclasses.dataclass
class Config:
    account: str
    password: str
    character: str
    class_: str
    attendance_urls: list[str]

    def save(self, path: pathlib.Path):
        f: io.FileIO
        with open(path, 'wb') as f:
            tomli_w.dump(dataclasses.asdict(self), f)
