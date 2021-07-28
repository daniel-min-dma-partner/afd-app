import os
import shutil

from core.settings import BASE_DIR
from libs.amt_helpers import generate_build_file, generate_package
from libs.interactor.interactor import Interactor


class DownloadDataflowInteractor(Interactor):
    def run(self):
        _exc = None
        try:
            # Deletes first the retrieve folder.
            if os.path.isdir(f"{BASE_DIR}/ant/{self.context.user.username}/retrieve"):
                shutil.rmtree(f"{BASE_DIR}/ant/{self.context.user.username}/retrieve")

            generate_build_file(self.context.model, self.context.user)

            members = [f"<members>{dataflow_name}</members>" for dataflow_name in self.context.dataflow]
            generate_package(members, self.context.user)

            cur_dir_tmp = "_CUR_DIR_TMP_"
            _cmd_queue = [
                F"export {cur_dir_tmp}=$(pwd)",
                f"cd {BASE_DIR}/ant/{self.context.user.username}",

                f"{BASE_DIR}/libs/apache_ant/bin/ant downloadDataflows",

                f"cd ${cur_dir_tmp}",
                f"unset {cur_dir_tmp}"
            ]
            os.system(" && ".join(_cmd_queue))
        except Exception as e:
            _exc = e

        self.context.exception = _exc
