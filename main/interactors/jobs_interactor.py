from main.interactors.download_dataflow_interactor import DownloadDataflowInteractorNoAnt
import logging
import os

from core.apscheduler_config import Scheduler
from libs.interactor.interactor import Interactor
from main.interactors.download_dataflow_interactor import DownloadDataflowInteractorNoAnt
from main.interactors.file_interactor import FileCompressorInteractor
from main.interactors.notification_interactor import SetNotificationInteractor
from main.models import Notifications

logger = logging.getLogger("datafllow-download-job-logger")
logger.setLevel(logging.INFO)


def df_down_job(data: dict = None):
    dataflows = data['dataflows']
    model = data['model']
    user = data['user']

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
                msg = os.path.isfile(zipfile_path)
                notif_data = {
                    'user': user,
                    'message': msg,
                    'status': Notifications.get_initial_status(),
                    'link': "__self__",
                    'type': "success"
                }
            except Exception as e:
                print("internal", e)
                notif_data = {
                    'user': user,
                    'message': str(e),
                    'status': Notifications.get_initial_status(),
                    'link': "__self__",
                    'type': "error"
                }

    ctx = SetNotificationInteractor.call(data=notif_data)
    print("external", ctx.exception)


class JobsInteractor(Interactor):
    def run(self):
        data = self.context.data
        sched: Scheduler = self.context.scheduler
        sched.add_job(df_down_job, _id="df_down_job", data=data)
