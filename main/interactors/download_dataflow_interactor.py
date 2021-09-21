import datetime
import html
import json
import os
import shutil

import requests
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils.safestring import mark_safe

from core.settings import BASE_DIR
from libs.amt_helpers import generate_build_file, generate_package
from libs.interactor.interactor import Interactor
from main.interactors.dataflow_tree_manager import show_in_browser
from main.interactors.list_dataflow_interactor import DataflowListInteractor
from main.interactors.response_interactor import FileResponseInteractor
from main.models import DeprecationDetails


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


class DownloadSelectedDataflowInteractor(Interactor):
    def run(self):
        data = self.context.data
        only_dep = data["only_dep"] == 'true'
        errors = data["errors"] == 'true'
        none = data["none"] == 'true'
        request = data["request"]
        pk = data["pk"]

        username = request.user.username
        response = None

        try:

            # Generates a name for the file, based on the type of download
            filename = "filename"
            # This filename actually isn't being used at the end of the process
            # since the name is determined at client-side by XMLHtmlResponse response object in j-query.

            # Returns error if deprecation model doesn't exist
            queryset = DeprecationDetails.objects.filter(deprecation_id=pk)
            if not queryset.exists():
                raise Exception('Deprecation not found')

            # Gets deprecation detail based on the user selection
            status = (
                DeprecationDetails.SUCCESS if only_dep else
                DeprecationDetails.ERROR if errors else
                DeprecationDetails.NO_DEPRECATION if none else -1
            )
            details = queryset.filter(status=status).all()

            # Creates temporal media directory
            basepath = f"{os.getcwd()}/media/{datetime.datetime.now().strftime('%Y/%m/%d')}/{username}/"
            media_dir = f"{basepath}download-selected-dfs/"
            if not os.path.exists(media_dir):
                os.makedirs(media_dir)

            if not only_dep:
                # Dumps the dataflows to the media directory
                for detail in details:
                    json.dump(detail.deprecated_dataflow, open(media_dir + os.path.basename(detail.file_name), 'w+'))

                # Calls interactor to create .zip response
                ctx = FileResponseInteractor.call(zipfile_path=media_dir, zipfile_name=filename)
                if ctx.exception:
                    messages.error(request, mark_safe(f"Something went wrong: {str(ctx.exception)}"))
                    response = JsonResponse({"payload": "", "error": ""}, status=500)

                response = ctx.response
            else:
                # Dumps the dataflows to its own folder
                # Along with the list of removed fields.
                for detail in details:
                    zipfile_path = dump_deprecated(detail=detail, media_dir=media_dir)
                    zipfile = open(zipfile_path, 'rb')
                    response = HttpResponse(zipfile, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename={filename}'

            # Removes the media directory
            shutil.rmtree(basepath)
        except Exception as e:
            messages.error(request, mark_safe(str(e)))
            response = JsonResponse({"payload": "", "error": mark_safe(str(e))}, status=500)
        finally:
            self.context.response = response


def dump_deprecated(detail: DeprecationDetails, media_dir: str):
    df_name = os.path.basename(detail.file_name).replace('.json', '')
    df_own_folder = media_dir + df_name + "/"
    if not os.path.exists(df_own_folder):
        os.makedirs(df_own_folder)
    else:
        shutil.rmtree(media_dir)
        os.makedirs(df_own_folder)

    deprecated_path = df_own_folder + df_name + '--modified.json'
    original_path = df_own_folder + df_name + '.json'
    json.dump(detail.deprecated_dataflow, open(deprecated_path, 'w+'), indent=2)
    json.dump(detail.original_dataflow, open(original_path, 'w+'), indent=2)
    while not os.path.isfile(original_path) or not os.path.isfile(deprecated_path):
        pass

    show_in_browser(original_path, deprecated_path)
    html_filepath = f'{BASE_DIR}/main/templates/json_diff_output.html'
    while not os.path.isfile(html_filepath):
        pass
    shutil.copy(html_filepath, df_own_folder + 'diff_visualizer.html')
    os.remove(html_filepath)

    removed_fields = detail.removed_fields
    json.dump(removed_fields, open(f"{df_own_folder}Removed fields from {df_name}.json", 'w+'),
              indent=2)

    zipfile_path = media_dir + "../Only Deprecated.zip"
    shutil.make_archive(zipfile_path.replace('.zip', ''), 'zip', media_dir)

    return zipfile_path
