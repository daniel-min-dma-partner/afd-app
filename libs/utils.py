import datetime
import inspect
import logging
import os
import random
import string
from datetime import datetime
from pathlib import Path

import pytz
import tzlocal
from django.core.cache import cache

logger = logging.getLogger('main')
logger.level = logging.DEBUG

DEFAULT_CHAR_STRING = string.ascii_lowercase + string.digits


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


def generate_random_string(chars=DEFAULT_CHAR_STRING, size=6):
    return ''.join(random.choice(chars) for _ in range(size))


def next_url(action='get', request=None):
    _next_url = '/'

    if action == 'get':
        _next_url = request.GET.get('next', '/')
        if _next_url and _next_url != '/':
            cache.set('next', _next_url)
        else:
            _next_url = request.META.get('HTTP_REFERER', '/')
    elif action == 'post':
        _next_url = cache.get('next', '/')
        cache.delete('next') if _next_url else None

    return _next_url


def replace_leading(source, char="&nbsp;"):
    stripped = source.lstrip()
    return char * (len(source) - len(stripped)) + stripped


def get_time_localized(date_time=None, timezone=None):
    local_tz = pytz.timezone('UTC' if not timezone or timezone not in pytz.all_timezones else timezone)
    date_time = datetime.datetime.now() if not date_time else date_time
    localized_dt = date_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
    localized_dt_str = localized_dt.strftime("%Y-%m-%d - %H.%M.%S %z")
    print(f"From {inspect.stack()[0][3]}():\n - Original: {date_time}\n - Localized: {localized_dt_str}")
    return localized_dt_str
