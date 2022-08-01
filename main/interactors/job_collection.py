import logging
import os

from main.interactors.deprecate_fields_interactor import FieldDeprecatorInteractor
from main.interactors.download_dataflow_interactor import DownloadDataflowInteractorNoAnt
from main.interactors.file_interactor import FileCompressorInteractor
from main.interactors.notification_interactor import SetNotificationInteractor
from main.interactors.upload_dataflow_interactor import UploadDataflowInteractorNoAnt
from main.models import Notifications, UploadNotifications, Job

logger = logging.getLogger("datafllow-download-job-logger")
logger.setLevel(logging.INFO)


def download_dataflow(data: dict = None, job: Job = None):
    dataflows = data['dataflows']
    model = data['model']
    user = data['user']
    klass = Notifications

    logger.info(">>>> Downloading Dataflow json definitions.")
    download_ctx = DownloadDataflowInteractorNoAnt.call(dataflow=dataflows, model=model, user=user, job=job)

    if download_ctx.exception:
        notif_data = {
            'user': user,
            'message': str(download_ctx.exception),
            'status': Notifications.get_initial_status(),
            'link': "__self__",
            'type': "error"
        }
    else:
        logger.info(">>>> Compressing all json files into a zip file.")
        path = download_ctx.output_filepath
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        zipfile_path = path.replace('retrieve/dataflow/wave', 'zipfiles')
        os.makedirs(zipfile_path) if not os.path.exists(zipfile_path) else None
        zipfile_path = os.path.join(zipfile_path, f"{model.name}--dataflows.zip")
        os.remove(zipfile_path) if os.path.isfile(zipfile_path) else None
        compressor_ctx = FileCompressorInteractor.call(files=files, path=path, zip_path=zipfile_path)

        if compressor_ctx.exception:
            notif_data = {
                'user': user,
                'message': str(compressor_ctx.exception),
                'status': Notifications.get_initial_status(),
                'link': "__self__",
                'type': "error"
            }
        else:
            # Deletes all json file
            files_in_directory = os.listdir(download_ctx.output_filepath)
            filtered_files = [file for file in files_in_directory if file.endswith(".json")]
            for file in filtered_files:
                path_to_file = os.path.join(download_ctx.output_filepath, file)
                os.remove(path_to_file)

            # Creates notification
            try:
                logger.info(">>>> Creating notifications for zip file.")
                msg = f"The zip file for the {'Dataflow <code>' + dataflows[0] + '</code>' if len(dataflows) == 1 else str(len(dataflows)) + ' dataflows'} from <code>{model.name}</code> is ready for download."
                notif_data = {
                    'user': user,
                    'message': msg,
                    'status': Notifications.get_initial_status(),
                    'link': "/dataflow-manager/download-zip/{{pk}}",
                    'type': "success",
                    'zipfile_path': zipfile_path,
                    'envname': model.name
                }
                klass = UploadNotifications
            except Exception as e:
                notif_data = {
                    'user': user,
                    'message': str(e),
                    'status': Notifications.get_initial_status(),
                    'link': "__self__",
                    'type': "error"
                }
                klass = Notifications

    ctx = SetNotificationInteractor.call(data=notif_data, klass=klass)


def upload_dataflow(data: dict = None, job: Job = None):
    env = data['env']
    remote_df_name = data['remote_df_name']
    user = data['user']
    filemodel = data['filemodel']
    comment = data['comment']
    ctx = UploadDataflowInteractorNoAnt.call(env=env, remote_df_name=remote_df_name, user=user,
                                             filemodel=filemodel, job=job, comment=comment)

    if ctx.exception:
        raise ctx.exception
    
    
def deprecate_fields_from(data: dict = None, job: Job = None):
    df_files = data['df_files']
    objects = data['objects']
    fields = data['fields']
    user = data['user']
    name = data['name']
    org = data['org']
    case_url = data['case_url']
    
    # Calls interactor
    ctx = FieldDeprecatorInteractor.call(df_files=df_files, objects=objects, fields=fields,
                                         user=user, name=name,
                                         org=org,
                                         case_url=case_url,
                                         job=job)
