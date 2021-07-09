import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from shutil import rmtree

from core.settings import BASE_DIR
from libs.amt_helpers import generate_build_file
from libs.interactor.interactor import Interactor
from main.models import User

_SELECT2_DATA_CACHE_FOLDER = 'select2-data-cache'
_SELECT2_DATA_CACHE_FN = 'cache.json'


@contextmanager
def status_wrapper(user: User):
    status_filenm = f'ant/{user.username}/status.json'
    status_filedir = f'ant/{user.username}'
    if not os.path.isfile(status_filenm):
        status = {'status': 0}
        Path(status_filedir).mkdir(parents=True, exist_ok=True)
        with open(status_filenm, 'w') as file:
            json.dump(status, file)

    with open(status_filenm, 'r') as f:
        jf = json.load(f)

    print(f"========== status es: {jf['status']}")
    if jf['status'] == 1:
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
        print('resetting status')
        status_filenm = f'ant/{user.username}/status.json'

        if os.path.isfile(status_filenm):
            with open(status_filenm, 'w+') as f:
                jf = json.load(f)
                jf['status'] = 0
        print('status reseted')

    def run(self):
        with status_wrapper(self.context.user):
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

            try:
                generate_build_file(self.context.model, user=self.context.user)
                payload = self._list_metadata_df()

            except Exception as e:
                status = 501
                error = str(e)
                payload = bad_payload

                if os.path.isfile(self.context.cache_filepath):
                    rmtree(self.context.cache_dir)

            self.context.payload = payload
            self.context.status_code = status
            self.context.error = error

            del self.context.model
            del self.context.cache_dir
            del self.context.cache_filepath

    def _list_metadata_df(self):
        self.context.cache_dir = f'ant/{self.context.user.username}/{_SELECT2_DATA_CACHE_FOLDER}/{self.context.model.name}'
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
                f"cd ant/{self.context.user.username}",

                "ant listMetadataDf",

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
        if not load_from_cache:
            print('============== >> REFRESHING CACHE ==============')
            filename = f'ant/{self.context.user.username}/listMetadata/list.log'

            with open(filename, 'r') as file:
                filelines = file.readlines()

                df_apis = [line.replace('FullName/Id: ', "").split('/')[0]
                           for line in filelines if "FullName/Id:" in line]

                payload = {"results": [
                    {"id": api, "text": api} for api in df_apis
                ]}

            with open(self.context.cache_filepath, 'w') as file:
                json.dump(payload, file)

            print('============== << REFRESHING CACHE ==============')
        else:
            with open(self.context.cache_filepath, 'r') as f:
                payload = json.load(fp=f)

        search = self.context.search
        if search:
            payload = {"results": [
                {"id": dataflow['id'], "text": dataflow['text']} for dataflow in payload['results']
                if search.strip().lower() in dataflow['text'].strip().lower()
            ]}

        return payload
