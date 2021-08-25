from apscheduler.schedulers.background import BackgroundScheduler
import random


class Scheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def add_job(self, func, _id=None, **kwargs):
        _name = _id or str(random.getrandbits(64))
        self.scheduler.add_job(func, id=_name or str(random.getrandbits(64)), kwargs=kwargs, name=_name)

    def start(self):
        print('>>>> scheduler started.')
        self.scheduler.start()

    def add(self, func, _id=None):
        self.scheduler.add_job(func, id=_id or str(random.getrandbits(64)))


def scheduler_configure():
    return Scheduler()
