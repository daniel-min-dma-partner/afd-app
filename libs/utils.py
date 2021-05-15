import os
from datetime import datetime
from pathlib import Path

import django.core.files.uploadedfile
import tzlocal


def current_datetime(add_time=False):
    utc = tzlocal.get_localzone()
    return datetime.now(tz=utc).strftime(f"%Y-%m-%d{' %H.%M.%S%z' if add_time else ''}")


def expand_home(path):
    if path:
        home = str(Path.home())
        path = path.replace('~', home)
        path = path.replace('~', home)

    return path


def relative_mkdir(name="", as_pymodule=True):
    if name:
        Path(name).mkdir(parents=True, exist_ok=True)
        if as_pymodule:
            init_file_path = f"{os.getcwd()}/{name}/__init__.py"
            if not (os.path.isfile(init_file_path) or os.path.isdir(init_file_path)):
                open(init_file_path, 'w').close()


def byte_to_str(in_mem_data: bytes):
    if isinstance(in_mem_data, bytes):
        return in_mem_data.decode('utf-8')


def str_to_json(string: str):
    if isinstance(string, str):
        import json as js
        return js.loads(string)
