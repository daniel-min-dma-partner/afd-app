from apscheduler.schedulers.background import BackgroundScheduler
import random


class Scheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def add(self, func, _id=None):
        self.scheduler.add_job(func, id=_id or str(random.getrandbits(64)))


def scheduler_configure():
    return Scheduler()
