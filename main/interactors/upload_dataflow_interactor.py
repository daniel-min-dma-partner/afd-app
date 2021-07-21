import os

from libs.amt_helpers import move_retrieve_to_deploy, WDF_FILE
from libs.interactor.interactor import Interactor
from main.interactors.download_dataflow_interactor import DownloadDataflowInteractor as DownDf
from main.interactors.wdf_manager_interactor import JsonToWdfConverterInteractor as JsonToWdf
from core.settings import BASE_DIR


class UploadDataflowInteractor(Interactor):
    def run(self):
        _exc = None
        try:
            filemodel = self.context.filemodel
            user = self.context.user
            env = self.context.env
            remote_df_name = self.context.remote_df_name

            # generate_build_file(env, user)  # No needed since DownDf interactor already creates this

            ctx = DownDf.call(model=env, user=user, dataflow=[remote_df_name])
            if ctx.exception:
                raise ctx.exception

            move_retrieve_to_deploy(retrieve_path=f"{BASE_DIR}/ant/{user.username}/retrieve")
            wdf_file = WDF_FILE.replace("{{user}}", user.username).replace("{{dataflow_name}}", remote_df_name)
            output_file = filemodel.file.path.replace('.json', ' [REVERTED].JSON')
            _ = JsonToWdf.call(json_filepath=filemodel.file.path,
                               output_filepath=output_file,
                               wdf_filepath=wdf_file)

            filemodel.delete()
            os.remove(output_file)

            # Execute Ant
            cur_dir_tmp = "_CUR_DIR_TMP_"
            _cmd_queue = [
                F"export {cur_dir_tmp}=$(pwd)",
                f"cd {BASE_DIR}/ant/{self.context.user.username}",

                "ant uploadDataflows",

                f"cd ${cur_dir_tmp}",
                f"unset {cur_dir_tmp}"
            ]
            os.system(" && ".join(_cmd_queue))

        except Exception as e:
            _exc = e

        self.context.exception = _exc
