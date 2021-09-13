import html
import json
import os
import shutil

import requests

from core.settings import BASE_DIR
from libs.amt_helpers import generate_build_file, generate_package
from libs.interactor.interactor import Interactor
from main.interactors.list_dataflow_interactor import DataflowListInteractor
from main.interactors.file_interactor import FileCompressorInteractor as FCompressor


class DownloadDataflowInteractor(Interactor):
    def run(self):
        _exc = None
        try:
            # Deletes first the retrieve folder.
            if os.path.isdir(f"{BASE_DIR}/ant/{self.context.user.username}/retrieve"):
                shutil.rmtree(f"{BASE_DIR}/ant/{self.context.user.username}/retrieve")

            generate_build_file(self.context.model, self.context.user)

            members = [f"<members>{dataflow_name}</members>" for dataflow_name in self.context.dataflow]
            generate_package(members, self.context.user)

            cur_dir_tmp = "_CUR_DIR_TMP_"
            _cmd_queue = [
                F"export {cur_dir_tmp}=$(pwd)",
                f"cd {BASE_DIR}/ant/{self.context.user.username}",

                f"{BASE_DIR}/libs/apache_ant/bin/ant downloadDataflows",

                f"cd ${cur_dir_tmp}",
                f"unset {cur_dir_tmp}"
            ]
            os.system(" && ".join(_cmd_queue))
        except Exception as e:
            _exc = e

        self.context.exception = _exc


class DownloadDataflowInteractorNoAnt(Interactor):
    def run(self):
        _exc = None
        output_path = None
        job = self.context.job  # Receive Job object
        user = self.context.user
        model = self.context.model
        dataflows = self.context.dataflow

        _job_stages_ids = job.generate_stages([{'message': f"Download <code>{dataflow}.json</code>"} for dataflow in dataflows])  # Create Stages

        downloaded_dataflows_defs = {}

        try:
            # Verifies whether the instance object is logged in.
            if not model.instance_url:
                raise ConnectionError(f"The instance <code>{model.name}</code> is not loged in. Please login first.")

            # Downloads all dataflows name list
            down_all_ctx = DataflowListInteractor.call(model=model, search=None,
                                                       refresh_cache='true',
                                                       user=user)
            if down_all_ctx.error:
                raise Exception(down_all_ctx.error)

            # Deletes first the retrieve folder.
            if os.path.isdir(f"{BASE_DIR}/ant/{self.context.user.username}/retrieve"):
                shutil.rmtree(f"{BASE_DIR}/ant/{self.context.user.username}/retrieve")

            # Makedirs the output_path.
            output_path = f"{BASE_DIR}/ant/{self.context.user.username}/retrieve/dataflow/wave/"
            os.makedirs(output_path)

            job.set_progress(save=True)

            # Downloads each dataflow listed in 'dataflows' list.
            for dataflow in dataflows:
                resource = '/services/data/v51.0/wave/dataflows/'
                url = model.instance_url + resource + down_all_ctx.df_ids_api[dataflow]
                url = url.strip()
                header = {'Authorization': "Bearer " + model.oauth_access_token, 'Content-Type': 'application/json'}

                job.jobstage_set.filter(pk=_job_stages_ids[dataflows.index(dataflow)]).first().set_progress(save=True)  # Set stage as 'in progress'
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
                    definition = response['definition']
                    filename = f"{dataflow}.json"
                    filepath = output_path + filename
                    with open(filepath, 'w') as f:
                        json.dump(definition, f, indent=2)

                    job.jobstage_set.filter(pk=_job_stages_ids[dataflows.index(dataflow)]).first().set_successful(save=True)  # Set stage as 'successful'
                else:
                    stage = job.jobstage_set.filter(pk=_job_stages_ids[dataflows.index(dataflow)]).first()
                    stage.set_failed(save=True, msg=f"Failed to download <code>{dataflow}</code>: {str(response.text)}")  # Set stage as failed

                    raise ConnectionError(response.text)

            job.set_successful(save=True)
        except Exception as e:
            job.set_failed(save=True, msg=f"Failed downloading dataflows: {str(e)}")  # Fail the job
            _exc = e
            output_path = None
            downloaded_dataflows_defs = {}
        finally:
            self.context.exception = _exc
            self.context.downloaded_df_defs = downloaded_dataflows_defs
            self.context.output_filepath = output_path
