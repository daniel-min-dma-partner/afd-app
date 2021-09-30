from core.components.apscheduler.config import Scheduler
from libs.interactor.interactor import Interactor
from main.interactors.job_collection import *
from main.models import JobStage


def process_trigger(data: dict = None, function: str = ""):
    job = Job()
    job.message = data['job-message']
    job.user = data['user']
    job.save()
    job.generate_stages([])

    globals()[function](data, job)


class JobsInteractor(Interactor):
    def run(self):
        data = self.context.data
        user = data['user']
        callback_function = self.context.function
        sched: Scheduler = self.context.scheduler
        sched.add_job(process_trigger, _id=f"callback_function-job-{callback_function}-{user.username}",
                      data=data, function=callback_function)


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
