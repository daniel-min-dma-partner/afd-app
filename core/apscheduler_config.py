import random
import logging

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Scheduler:
    def __init__(self):
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        }
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        self.scheduler = BackgroundScheduler()
        self.scheduler.configure(executors=executors, jobstores=jobstores)

    def add_job(self, func, _id=None, **kwargs):
        logger.info(f">>>> Adding {_id} job")
        _name = _id or str(random.getrandbits(64))
        self.scheduler.add_job(func, id=f"{_name}-by-{kwargs['data']['user'].username}",
                               kwargs=kwargs, name=_name)

    def start(self):
        print('>>>> scheduler started.')
        self.scheduler.start()

    def add(self, func, _id=None):
        self.scheduler.add_job(func, id=_id or str(random.getrandbits(64)))


def scheduler_configure():
    return Scheduler()
