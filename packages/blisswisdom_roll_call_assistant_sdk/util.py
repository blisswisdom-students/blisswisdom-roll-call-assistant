import pathlib
import platform
import sys

import macos_application_location


def get_cache_dir() -> pathlib.Path:
    return macos_application_location.get().parent if platform.system() == 'Darwin' else \
        (pathlib.Path.cwd() / sys.argv[0]).parent


def get_config_dir() -> pathlib.Path:
    return macos_application_location.get().parent if platform.system() == 'Darwin' else \
        (pathlib.Path.cwd() / sys.argv[0]).parent


def get_data_dir() -> pathlib.Path:
    return macos_application_location.get().parent if platform.system() == 'Darwin' else \
        (pathlib.Path.cwd() / sys.argv[0]).parent
