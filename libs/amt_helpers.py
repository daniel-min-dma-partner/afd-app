import copy
import os.path
from pathlib import Path
from shutil import copy as filecopy, rmtree, move
from typing import Union

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

_BUILD_PROP_TEMPLATE = {
    "sf.username": "",
    "sf.password": "",

    "sf.metadataType": "WaveDataflow",

    "sf.serverurl": "",

    "sf.maxPoll": "20",
    "sf.pollWaitMillis": "10000",
    "sf.retriveAt": "retrieve/dataflow",
    "sf.deployFrom": "deploy/dataflow",
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

_WDF_XML_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8"?>
<WaveDataflow xmlns="http://soap.sforce.com/2006/04/metadata" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <content xsi:nil="true"/>
    <application>WAVE_PUBLIC_DATAFLOWS</application>
    <dataflowType>User</dataflowType>
    <masterLabel>{{label}}</masterLabel>
</WaveDataflow>
"""

_PACKAGE_SPEC_FILE = 'ant/{{user}}/dataflow/package.xml'
_PACKAGE_SPECF_FOLDER = 'ant/{{user}}/dataflow'

_PACKAGE_UP_SPEC_FILE = 'ant/{{user}}/deploy/dataflow/package.xml'
_PACKAGE_UP_SPECF_FOLDER = 'ant/{{user}}/deploy/dataflow'
_XML_FILE = 'ant/{{user}}/deploy/dataflow/wave/{{dataflow_name}}-meta.xml'
WDF_FILE = 'ant/{{user}}/deploy/dataflow/wave/{{dataflow_name}}.wdf'
_WDF_XML_FOLDER = 'ant/{{user}}/deploy/dataflow/wave'


def generate_build_file(model: Env, user: User):
    build = copy.deepcopy(_BUILD_PROP_TEMPLATE)
    build['sf.username'] = model.client_username
    build['sf.password'] = model.client_password
    build['sf.serverurl'] = model.environment

    file_lines = [f"{key} = {value}\n" for key, value in build.items()]

    with open(f'{BASE_DIR}/ant/{user.username}/build.properties', 'w') as file:
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


def create_deploy_folders(user: User):
    deploy_folder = _PACKAGE_UP_SPECF_FOLDER.replace("{{user}}", user.username)
    wave_folder = _WDF_XML_FOLDER.replace("{{user}}", user.username)

    for _dir in [deploy_folder, wave_folder]:
        if os.path.isdir(_dir):
            rmtree(_dir)

        Path(_dir).mkdir(parents=True, exist_ok=True)


def move_retrieve_to_deploy(retrieve_path: Union[str, list]):
    def move_wdf_files(_from, _to):
        if os.path.isdir(_to):
            rmtree(_to)

        move(_from, _to)

    if type(retrieve_path) == list:
        for dfname in retrieve_path:
            move_wdf_files(dfname, dfname.replace("retrieve", "deploy"))
    elif type(retrieve_path) == str:
        move_wdf_files(retrieve_path, retrieve_path.replace("retrieve", "deploy"))
