from main.interactors.download_dataflow_interactor import DownloadDataflowInteractorNoAnt
import logging
import os
from typing import Union

from core.apscheduler_config import Scheduler
from libs.interactor.interactor import Interactor
from main.interactors.download_dataflow_interactor import DownloadDataflowInteractorNoAnt
from main.interactors.file_interactor import FileCompressorInteractor
from main.interactors.notification_interactor import SetNotificationInteractor
from main.models import Notifications, UploadNotifications, Job, JobStage

logger = logging.getLogger("datafllow-download-job-logger")
logger.setLevel(logging.INFO)


def df_down_job(data: dict = None):
    dataflows = data['dataflows']
    model = data['model']
    user = data['user']
    klass = Notifications

    logger.info(">>>> Downloading Dataflow json definitions.")
    download_ctx = DownloadDataflowInteractorNoAnt.call(dataflow=dataflows, model=model, user=user)

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
        zipfile_path = os.path.join(path, f"{model.name}--dataflows.zip")
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
                print("internal", e)
                notif_data = {
                    'user': user,
                    'message': str(e),
                    'status': Notifications.get_initial_status(),
                    'link': "__self__",
                    'type': "error"
                }
                klass = Notifications

    ctx = SetNotificationInteractor.call(data=notif_data, klass=klass)
    print("external", ctx.exception)


class JobsInteractor(Interactor):
    def run(self):
        data = self.context.data
        sched: Scheduler = self.context.scheduler
        sched.add_job(df_down_job, _id="df_down_job", data=data)


class BackgroundJobsInteractor(Interactor):
    def run(self):
        self.context.exception = None
        
        try:
            stages_descriptor = self.context.stages_descriptor
            job = self.context.job

            if not job.pk:
                raise SystemError("Unsaved Job can't generate and/or associate itself new stages.")

            if stages_descriptor and isinstance(stages_descriptor, list):
                for descriptor in stages_descriptor:
                    job_stage = JobStage()
                    job_stage.set(descriptor)
                    job_stage.job = job
                    job_stage.save()
        except Exception as e:
            self.context.exception = e
