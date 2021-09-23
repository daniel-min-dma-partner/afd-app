import json
import logging
import os
import pathlib
from pathlib import Path

import environ
from split_settings.tools import optional, include

from .components.apscheduler.config import scheduler_configure

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

sched = scheduler_configure()

BASE_DIR = Path(__file__).resolve().parent.parent

environment = os.environ.get('ENVIRONMENT', '').lower()
env_settings_file = f"envs/{environment}/settings.py"

include(
    'core_settings.py',
    optional(env_settings_file),  # Includes if file exist
    optional('local_settings.py')
)

print("DEBUG:", DEBUG)
print(env_settings_file)
