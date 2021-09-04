import json
import os
import zipfile

from django.http import HttpResponse

from libs.interactor.interactor import Interactor


# Source: https://pybit.es/articles/django-zipfiles/
class FileResponseInteractor(Interactor):
    def run(self):
        _exception = None

        try:
            response = HttpResponse(content_type='application/zip')
            zf = zipfile.ZipFile(response, 'w')
            mypath = self.context.zipfile_path
            onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
            for file in onlyfiles:
                with open(f"{mypath}{file}") as f:
                    json_str = json.dumps(json.load(f), indent=2)
                    zf.writestr(file, json_str)
            response['Content-Disposition'] = f'attachment; filename={self.context.env.name} dataflows.zip'
        except Exception as e:
            _exception = e
            response = None
        finally:
            self.context.response = response
            self.context.exception = _exception


class ZipFileResponseInteractor(Interactor):
    def run(self):
        _exception = None

        try:
            zipfile = open(self.context.zipfile_path, 'rb')
            response = HttpResponse(zipfile, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={self.context.envname} dataflows.zip'
        except Exception as e:
            _exception = e
            response = None
        finally:
            self.context.response = response
            self.context.exception = _exception


class JsonFileResponseInteractor(Interactor):
    def run(self):
        _exception = None

        try:
            filepath = self.context.filepath
            filename = os.path.basename(filepath)
            file = open(filepath, 'rb')
            response = HttpResponse(file,
                                    content_type='application/json',
                                    headers={'Content-Disposition': f'attachment; filename={filename}.json'})
        except Exception as e:
            _exception = e
            response = None
        finally:
            self.context.response = response
            self.context.exception = _exception
