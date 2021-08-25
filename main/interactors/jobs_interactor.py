import time

from libs.interactor.interactor import Interactor
from core.apscheduler_config import Scheduler


def df_down_job(data: dict = None):
    c = 1
    while True:
        print('estupido', data)
        time.sleep(3)
        if c % 15 == 0:
            break
        c += 1


class JobsInteractor(Interactor):
    def run(self):
        data = self.context.data
        sched: Scheduler = self.context.scheduler
        sched.add_job(df_down_job, _id="df_down_job", data=data)
