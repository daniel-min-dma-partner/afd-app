import os

from libs.interactor.interactor import Interactor
from libs.tcrm_automation.tree_remover import tree_remover
from libs.utils import current_datetime
from pathlib import Path


class TreeRemoverInteractor(Interactor):
    def run(self):
        # Prepare the outout directory
        today = current_datetime(add_time=False)
        outdir = os.path.join(Path(__file__).resolve().parent.parent, f'libs/tcrm_automation/{today}')

        if not os.path.isdir(outdir):
            os.makedirs(outdir)

        _output = os.path.join(outdir, self.context.name.rstrip())

        # Execute removal
        tree_remover(dataflow=self.context.dataflow, replacers=self.context.replacers, registers=self.context.registers,
                     output=_output)

        # Lands a page to show the difference due to the removal
        original = self.context.request.FILES['dataflow'].temporary_file_path().replace(' ', "\\ ")
        diff_command = f"python diff2HtmlCompare.py -s {original} {_output}"
        cur_dir_tmp = "_CUR_DIR_TMP_"
        _cmd_queue = [
            F"export {cur_dir_tmp}=$(pwd)",
            "cd libs/diff2HtmlCompare",
            diff_command,
            f"cd ${cur_dir_tmp}",
            f"unset {cur_dir_tmp}"
        ]
        os.system(" && ".join(_cmd_queue))
