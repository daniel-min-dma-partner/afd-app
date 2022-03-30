import collections
import html
import json
import os
import shutil

import requests

from core.settings import BASE_DIR
from libs.amt_helpers import move_retrieve_to_deploy, WDF_FILE
from libs.interactor.interactor import Interactor
from libs.utils import job_stage
from main.interactors.download_dataflow_interactor import DownloadDataflowInteractor as DownDf
from main.interactors.list_dataflow_interactor import DataflowListInteractor
from main.interactors.wdf_manager_interactor import JsonToWdfConverterInteractor as JsonToWdf
from main.models import DataflowUploadHistory


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
        comment = self.context.comment
        filemodel = self.context.filemodel
        remote_df_name = self.context.remote_df_name
        original_dataflow = {}

        message_collection = [
            ("connection-check", f"Checking status of <code>{model.name}</code> connection."),
            ("list-dataflows", "Listing dataflows."),
            ("backup", "Making a backup of the dataflow."),
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
            with job_stage(job=job, pk=_job_stages_ids[list(messages.keys()).index('connection-check')]):
                if not model.instance_url:
                    raise ConnectionError(f"The instance <code>{model.name}</code> is not logged in. Please login first.")

            # Lists remote dataflows for checking purpose
            with job_stage(job=job, pk=_job_stages_ids[list(messages.keys()).index('list-dataflows')]):
                down_all_ctx = DataflowListInteractor.call(model=model, search=None,
                                                           refresh_cache='true',
                                                           user=user)
                if down_all_ctx.error:
                    raise Exception(down_all_ctx.error)

            # Capturing backup dataflow
            with job_stage(job=job, pk=_job_stages_ids[list(messages.keys()).index('backup')]):
                resource = '/services/data/v51.0/wave/dataflows/'
                url = model.instance_url + resource + down_all_ctx.df_ids_api[remote_df_name]
                url = url.strip()
                header = {'Authorization': "Bearer " + model.oauth_access_token, 'Content-Type': 'application/json'}
                response = requests.get(url, headers=header)

                if response.status_code == 200:
                    response = response.text
                    replaces = [
                        ('&quot;', '\\"'),
                        ('&#92;', '\\\\'),
                    ]
                    for (a, b) in replaces:
                        response = response.replace(a, b)
                    response = html.unescape(response)
                    response = json.loads(response)
                    original_dataflow = response['definition']
                else:
                    raise ConnectionError(response.text)

            # Creates resource URI
            with job_stage(job=job, pk=_job_stages_ids[list(messages.keys()).index('uri')]):
                resource = '/services/data/v51.0/wave/dataflows/'
                url = model.instance_url + resource + down_all_ctx.df_ids_api[remote_df_name]
                url = url.strip()
                header = {'Authorization': "Bearer " + model.oauth_access_token, 'Content-Type': 'application/json'}
                with open(filemodel.file.path, 'r') as f:
                    definition = json.load(fp=f)
                    uploading_dataflow = definition
                    data = {
                        "definition": definition,
                        "historyLabel": f"{user.first_name + (' ' + user.last_name) if user.last_name else ''} through TCRM - Automation Web Upload: {comment}"
                    }

            # Initiates upload request
            with job_stage(job=job, pk=_job_stages_ids[list(messages.keys()).index('start-request')]):
                response = requests.patch(url, json=data, headers=header)

            # Checks returned response status
            with job_stage(job=job, pk=_job_stages_ids[list(messages.keys()).index('response-received')]):
                if response.status_code == 200:
                    response = response.json()
                    if 'historiesUrl' not in response.keys():
                        raise ConnectionError(response)
                else:
                    raise ConnectionError(response.text)

            # Finishes the job
            job.set_successful(save=True)

            # Save upload history
            DataflowUploadHistory.register_upload(original=original_dataflow, uploaded=uploading_dataflow, user=user,
                                                  dataflow_name=remote_df_name, salesforce_env=model)
        except Exception as e:
            _exc = e
            _stage = job.jobstage_set.filter(status='progress').order_by('-pk').first()
            stage_name = _stage.message
            failure_msg = f"Stage <code>{stage_name}</code> failed: {str(e)}"
            _stage.set_failed(save=True, msg=failure_msg)

            failure_msg = f"<code>{job.message}</code> failed: {str(e)}"
            job.set_failed(save=True, msg=failure_msg)
        finally:
            self.context.exception = _exc
            filemodel.delete()
