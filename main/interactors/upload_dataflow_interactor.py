import collections
import json
import os
import shutil

import requests

from core.settings import BASE_DIR
from libs.amt_helpers import move_retrieve_to_deploy, WDF_FILE
from libs.interactor.interactor import Interactor
from main.interactors.download_dataflow_interactor import DownloadDataflowInteractor as DownDf
from main.interactors.list_dataflow_interactor import DataflowListInteractor
from main.interactors.wdf_manager_interactor import JsonToWdfConverterInteractor as JsonToWdf


class UploadDataflowInteractor(Interactor):
    def run(self):
        _exc = None
        try:
            filemodel = self.context.filemodel
            user = self.context.user
            env = self.context.env
            remote_df_name = self.context.remote_df_name

            # generate_build_file(env, user)  # No needed since DownDf interactor already creates this

            # Deletes first the retrieve folder.
            if os.path.isdir(f"{BASE_DIR}/ant/{user.username}/retrieve"):
                shutil.rmtree(f"{BASE_DIR}/ant/{user.username}/retrieve")

            ctx = DownDf.call(model=env, user=user, dataflow=[remote_df_name])
            if ctx.exception:
                raise ctx.exception

            move_retrieve_to_deploy(retrieve_path=f"{BASE_DIR}/ant/{user.username}/retrieve")
            wdf_file = WDF_FILE.replace("{{user}}", user.username).replace("{{dataflow_name}}", remote_df_name)
            output_file = filemodel.file.path.replace('.json', ' [REVERTED].JSON')
            _ = JsonToWdf.call(json_filepath=filemodel.file.path,
                               output_filepath=output_file,
                               wdf_filepath=wdf_file)

            filemodel.delete()
            os.remove(output_file)

            # Execute Ant
            cur_dir_tmp = "_CUR_DIR_TMP_"
            _cmd_queue = [
                F"export {cur_dir_tmp}=$(pwd)",
                f"cd {BASE_DIR}/ant/{self.context.user.username}",

                "ant uploadDataflows",

                f"cd ${cur_dir_tmp}",
                f"unset {cur_dir_tmp}"
            ]
            os.system(" && ".join(_cmd_queue))

        except Exception as e:
            _exc = e

        self.context.exception = _exc


class UploadDataflowInteractorNoAnt(Interactor):
    def run(self):
        _exc = None
        job = self.context.job  # Receive Job object
        user = self.context.user
        model = self.context.env
        filemodel = self.context.filemodel
        remote_df_name = self.context.remote_df_name

        message_collection = [
            ("connection-check", f"Checking status of <code>{model.name}</code> connection."),
            ("list-dataflows", "Listing dataflows."),
            ("uri", "Creating target resource URL."),
            ("start-request", "Request Initiated."),
            ("response-received", "Response received."),
        ]

        messages = collections.OrderedDict(message_collection)

        _job_stages_ids = job.generate_stages(
            [{'message': message} for _, message in message_collection])  # Create Stages

        try:
            job.set_progress(save=True)

            # Check connection status
            job.jobstage_set.filter(
                pk=_job_stages_ids[list(messages.keys()).index('connection-check')]).first().set_progress(save=True)
            if not model.instance_url:
                raise ConnectionError(f"The instance <code>{model.name}</code> is not logged in. Please login first.")
            job.jobstage_set.filter(
                pk=_job_stages_ids[list(messages.keys()).index('connection-check')]).first().set_successful(save=True)

            # Lists remote dataflows for checking purpose
            job.jobstage_set.filter(
                pk=_job_stages_ids[list(messages.keys()).index('list-dataflows')]).first().set_progress(save=True)
            down_all_ctx = DataflowListInteractor.call(model=model, search=None,
                                                       refresh_cache='true',
                                                       user=user)
            if down_all_ctx.error:
                raise Exception(down_all_ctx.error)
            job.jobstage_set.filter(
                pk=_job_stages_ids[list(messages.keys()).index('list-dataflows')]).first().set_successful(save=True)

            # Creates resource URI
            job.jobstage_set.filter(pk=_job_stages_ids[list(messages.keys()).index('uri')]).first().set_progress(
                save=True)
            resource = '/services/data/v51.0/wave/dataflows/'
            url = model.instance_url + resource + down_all_ctx.df_ids_api[remote_df_name]
            url = url.strip()
            header = {'Authorization': "Bearer " + model.oauth_access_token, 'Content-Type': 'application/json'}
            with open(filemodel.file.path, 'r') as f:
                data = {
                    "definition": json.load(fp=f),
                    "historyLabel": "TCRM - Automation Web Upload"
                }
            job.jobstage_set.filter(pk=_job_stages_ids[list(messages.keys()).index('uri')]).first().set_successful(
                save=True)

            # Initiates upload request
            job.jobstage_set.filter(
                pk=_job_stages_ids[list(messages.keys()).index('start-request')]).first().set_progress(save=True)
            response = requests.patch(url, json=data, headers=header)
            job.jobstage_set.filter(
                pk=_job_stages_ids[list(messages.keys()).index('start-request')]).first().set_successful(save=True)

            # Checks returned response status
            job.jobstage_set.filter(
                pk=_job_stages_ids[list(messages.keys()).index('response-received')]).first().set_progress(save=True)
            if response.status_code == 200:
                response = response.json()
                if 'historiesUrl' not in response.keys():
                    raise ConnectionError(response)
            else:
                raise ConnectionError(response.text)
            job.jobstage_set.filter(
                pk=_job_stages_ids[list(messages.keys()).index('response-received')]).first().set_successful(save=True)

            # Finishes the job
            job.set_successful(save=True)
        except Exception as e:
            _exc = e
            job.jobstage_set.filter(status='progress').order_by('-pk').first().set_failed(save=True, msg=str(e))
            job.set_failed(save=True, msg=str(e))
        finally:
            self.context.exception = _exc
            filemodel.delete()
