import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from shutil import rmtree

import requests

from core.settings import BASE_DIR
from libs.amt_helpers import generate_build_file
from libs.interactor.interactor import Interactor
from main.models import User

_SELECT2_DATA_CACHE_FOLDER = 'select2-data-cache'
_SELECT2_DATA_CACHE_FN = 'cache.json'


@contextmanager
def status_wrapper(user: User, refresh_cache: bool = False):
    status_filenm = f'{BASE_DIR}/ant/{user.username}/status.json'
    status_filedir = f'{BASE_DIR}/ant/{user.username}'
    if not os.path.isfile(status_filenm):
        status = {'status': 0}
        Path(status_filedir).mkdir(parents=True, exist_ok=True)
        with open(status_filenm, 'w') as file:
            json.dump(status, file)

    with open(status_filenm, 'r') as f:
        jf = json.load(f)

    if jf['status'] == 1 and not refresh_cache:
        raise BlockingIOError("Another request is already in queue.")

    with open(file=status_filenm, mode='r') as f:
        status = json.load(f)

    status['status'] = 1
    with open(status_filenm, 'w') as f:
        json.dump(fp=f, obj=status)

    yield

    with open(file=status_filenm, mode='w') as f:
        status['status'] = 0
        json.dump(fp=f, obj=status)


class DataflowListInteractor(Interactor):
    """
    Download dataflows from Salesforce instance.

    """

    @classmethod
    def reset_status(cls, user: User):
        status_filenm = f'{BASE_DIR}/ant/{user.username}/status.json'

        if os.path.isfile(status_filenm):
            with open(status_filenm, 'r') as f:
                jf = json.load(f)

            jf['status'] = 0

            with open(status_filenm, 'w') as f:
                json.dump(jf, f, indent=2)

    def run(self):
        with status_wrapper(self.context.user, self.context.refresh_cache and self.context.refresh_cache == 'true'):
            error = None
            bad_payload = {
                "results": [
                    {
                        "id": "",
                        "text": "Select one",
                    },
                ],
            }
            status = 200
            df_ids_api = {}

            try:
                # generate_build_file(self.context.model, user=self.context.user)
                payload, df_ids_api = self._list_wave_dataflows()

            except Exception as e:
                status = 501
                error = str(e)
                payload = bad_payload

                if os.path.isfile(self.context.cache_filepath):
                    rmtree(self.context.cache_dir)

            self.context.payload = payload
            self.context.status_code = status
            self.context.error = error
            self.context.df_ids_api = df_ids_api

            del self.context.model
            del self.context.cache_dir
            del self.context.cache_filepath

    def _list_wave_dataflows(self):
        self.context.cache_dir = f'{BASE_DIR}/ant/{self.context.user.username}/{_SELECT2_DATA_CACHE_FOLDER}/{self.context.model.name}'
        self.context.cache_filepath = f'{self.context.cache_dir}/{_SELECT2_DATA_CACHE_FN}'
        is_new_file = False
        load_from_cache = True
        select2_items = {
            "results": [
                {
                    "id": "",
                    "text": "Select one",
                },
            ],
        }
        ids = {}
        refresh_cache = self.context.refresh_cache and self.context.refresh_cache == 'true'

        if not os.path.isfile(self.context.cache_filepath):
            Path(self.context.cache_dir).mkdir(parents=True, exist_ok=True)
            open(self.context.cache_filepath, 'w').close()
            is_new_file = True
            load_from_cache = False

        diff = (time.time() - os.path.getmtime(self.context.cache_filepath)) / 3600  # in hours

        if refresh_cache or is_new_file or (diff > 15):
            env = self.context.model
            resource = '/services/data/v51.0/wave/dataflows/'
            url = env.instance_url + resource
            url = url.strip()
            header = {'Authorization': "Bearer " + env.oauth_access_token, 'Content-Type': 'application/json'}

            response = requests.get(url, headers=header)

            if response.status_code == 200:
                select2_items, ids = self._build_select2_items(response.json()['dataflows'])
                self._update_select2_cache(select2_items, ids)
            else:
                raise Exception(response.text)
        elif load_from_cache:
            with open(self.context.cache_filepath, 'r') as f:
                cache = json.load(fp=f)
                select2_items = cache['select2_items']
                ids = cache['ids']

        search = self.context.search
        if search and isinstance(search, str):
            select2_items = {"results": [
                {"id": dataflow['id'], "text": dataflow['text']} for dataflow in select2_items['results']
                if search.strip().lower() in dataflow['text'].strip().lower() or
                   search.replace(' ', '_').strip().lower() in dataflow['text'].strip().lower()
            ]}

        return select2_items, ids

    def _build_select2_items(self, dataflows: list):
        ids = {}
        select2_items = {
            "results": [],
        }

        for dataflow in dataflows:
            _item = {"id": dataflow['name'], "text": f"{dataflow['label']} ({dataflow['name']})"}
            select2_items['results'].append(_item)
            ids[dataflow['name']] = dataflow['id']

        select2_items['results'] = sorted(select2_items['results'], key=lambda k: k['text'])

        return select2_items, ids

    def _update_select2_cache(self, select2_items, ids):
        with open(self.context.cache_filepath, 'w') as file:
            json.dump({"select2_items": select2_items, "ids": ids}, file)

    def _list_metadata_df(self):
        self.context.cache_dir = f'{BASE_DIR}/ant/{self.context.user.username}/{_SELECT2_DATA_CACHE_FOLDER}/{self.context.model.name}'
        self.context.cache_filepath = f'{self.context.cache_dir}/{_SELECT2_DATA_CACHE_FN}'
        is_new_file = False
        load_from_cache = True
        refresh_cache = self.context.refresh_cache and self.context.refresh_cache == 'true'

        if not os.path.isfile(self.context.cache_filepath):
            Path(self.context.cache_dir).mkdir(parents=True, exist_ok=True)
            open(self.context.cache_filepath, 'w').close()
            is_new_file = True
            load_from_cache = False

        diff = (time.time() - os.path.getmtime(self.context.cache_filepath)) / 3600  # in hours

        # print(f"============== >> CONDITION ==============")
        # print(f"refresh? {refresh_cache}\nis new file? {is_new_file}\ndiff > 15? {diff > 24}")
        # print(f"============== << CONDITION ==============")

        if refresh_cache or is_new_file or (diff > 15):
            cur_dir_tmp = "_CUR_DIR_TMP_"
            _cmd_queue = [
                F"export {cur_dir_tmp}=$(pwd)",
                f"cd {BASE_DIR}/ant/{self.context.user.username}",

                f"{str(BASE_DIR)}/libs/apache_ant/bin/ant listMetadataDf",

                f"cd ${cur_dir_tmp}",
                f"unset {cur_dir_tmp}"
            ]
            listfile = BASE_DIR / f'ant/{self.context.user.username}/listMetadata/list.log'
            if os.path.isfile(listfile):
                os.remove(listfile)
            os.system(" && ".join(_cmd_queue))
            print("============== >> EXECUTED << ==============")
            load_from_cache = False

        return self._prepare_data(load_from_cache)

    def _prepare_data(self, load_from_cache: bool):
        df_ids = {}

        if not load_from_cache:
            print('============== >> REFRESHING CACHE ==============')
            filename = f'{BASE_DIR}/ant/{self.context.user.username}/listMetadata/list.log'

            if os.path.isfile(filename):
                with open(filename, 'r') as file:
                    filelines = file.readlines()

                    df_apis = [line.replace('FullName/Id: ', "").split('/')[0]
                               for line in filelines if "FullName/Id:" in line]
                    df_ids = {
                        line.replace('FullName/Id: ', "").split('/')[0]: line.replace('FullName/Id: ', "").split('/')[1]
                        for line in filelines if "FullName/Id:" in line
                    }

                    df_apis.sort()

                    payload = {"results": [
                        {"id": api, "text": api} for api in df_apis
                    ]}

                with open(self.context.cache_filepath, 'w') as file:
                    json.dump(payload, file)
            else:
                raise FileExistsError("Wave Dataflow list <strong>can not be retrieved</strong>. Contact with admin.")

            print('============== << REFRESHING CACHE ==============')
        else:
            with open(self.context.cache_filepath, 'r') as f:
                payload = json.load(fp=f)

        search = self.context.search
        if search and isinstance(search, str):
            payload = {"results": [
                {"id": dataflow['id'], "text": dataflow['text']} for dataflow in payload['results']
                if search.strip().lower() in dataflow['text'].strip().lower() or
                   search.replace(' ', '_').strip().lower() in dataflow['text'].strip().lower()
            ]}

        return payload, df_ids
