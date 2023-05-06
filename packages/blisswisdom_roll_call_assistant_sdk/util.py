import pathlib

import xdg_base_dirs

from .constant import PROG_NAME


def get_cache_dir() -> pathlib.Path:
    path: pathlib.Path = xdg_base_dirs.xdg_cache_home() / PROG_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_dir() -> pathlib.Path:
    path: pathlib.Path = xdg_base_dirs.xdg_config_home() / PROG_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir() -> pathlib.Path:
    path: pathlib.Path = xdg_base_dirs.xdg_data_home() / PROG_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path
