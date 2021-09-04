import zipfile

from libs.interactor.interactor import Interactor


# Source: https://stackoverflow.com/questions/47438424/python-zip-compress-multiple-files/47440162
class FileCompressorInteractor(Interactor):
    def run(self):
        files = self.context.files
        path = self.context.path
        zip_path = self.context.zip_path

        _exception = None
        zf = zipfile.ZipFile(zip_path, mode="w")

        try:
            # Select the compression mode ZIP_DEFLATED for compression
            # or zipfile.ZIP_STORED to just store the file
            compression = zipfile.ZIP_DEFLATED

            # create the zip file first parameter path/name, second mode
            for file in files:
                # Add file to the zip file
                # first parameter file to zip, second filename in zip
                zf.write(path + file, file, compress_type=compression)
        except Exception as e:
            _exception = e
        finally:
            self.context.exception = _exception
            zf.close()
