import copy
import os.path
from pathlib import Path
from shutil import copy as filecopy

from core.settings import BASE_DIR
from main.models import SalesforceEnvironment as Env
from main.models import User

_tmp = """
sf.maxPoll = 20
sf.pollWaitMillis = 10000

sf.username = api-tcrm_field_deprecation@salesforce.com.org62stage
sf.password = gPM9vYTxK8oLj
sf.serverurl = https://test.salesforce.com
"""

_FILE_TEMPLATE = {
    "sf.username": "",
    "sf.password": "",

    "sf.metadataType": "WaveDataflow",

    "sf.serverurl": "",

    "sf.maxPoll": "20",
    "sf.pollWaitMillis": "10000",
    "sf.retriveAt": "retrieve/dataflow",
}

_PACKAGE_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        {{members}}
        <name>WaveDataflow</name>
    </types>
    <version>51.0</version>
</Package>
"""

_PACKAGE_SPEC_FILE = 'ant/{{user}}/dataflow/package.xml'
_PACKAGE_SPECF_FOLDER = 'ant/{{user}}/dataflow'


def generate_build_file(model: Env, user: User):
    build = copy.deepcopy(_FILE_TEMPLATE)
    build['sf.username'] = model.client_username
    build['sf.password'] = model.client_password
    build['sf.serverurl'] = model.environment

    file_lines = [f"{key} = {value}\n" for key, value in build.items()]

    with open(f'ant/{user.username}/build.properties', 'w') as file:
        file.writelines(file_lines)

    filecopy(BASE_DIR / 'ant/build_tmp.xml', BASE_DIR / f'ant/{user.username}/build.xml')


def generate_package(members: list, user: User):
    package = copy.deepcopy(_PACKAGE_TEMPLATE)
    package = package.splitlines()[1:]
    prev = []
    post = []
    processed = False
    member_indent = 0

    for line in package:
        if not processed and "{{members}}" not in line:
            prev.append(line)
        elif processed and "{{members}}" not in line:
            post.append(line)
        else:
            member_indent = len(line) - len("{{members}}")
            processed = True

    members = [f"{' ' * member_indent}{member}" for member in members]
    package = "\n".join(prev + members + post)
    _file = _PACKAGE_SPEC_FILE.replace("{{user}}", user.username)
    _folder = _PACKAGE_SPECF_FOLDER.replace("{{user}}", user.username)

    if not os.path.isfile(_file):
        Path(_folder).mkdir(parents=True, exist_ok=True)

    with open(_file, 'w') as f:
        f.write(package)
