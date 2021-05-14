import os
from datetime import datetime
from pathlib import Path

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
