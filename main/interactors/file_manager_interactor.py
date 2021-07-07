from django.core.files import File

from libs.interactor.interactor import Interactor


class SaveFileToTempInteractor(Interactor):
    def run(self):
        file = File(self.context.file)
        print(file.name)
