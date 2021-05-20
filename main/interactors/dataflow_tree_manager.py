import os
from pathlib import Path

from libs.interactor.interactor import Interactor
from libs.tcrm_automation.tree_remover import tree_remover
from libs.tcrm_automation.tree_extractor import tree_extractor
from libs.utils import current_datetime
import platform as pf
from appscript import *


def _prepare_output_directory(filename: str = None, allow_empty_name: bool = False):
    if not allow_empty_name and not filename:
        raise NameError("Missing file name")

    # Prepare the outout directory
    today = current_datetime(add_time=False)
    outdir = os.path.join(Path(__file__).resolve().parent.parent.parent, f'libs/tcrm_automation/{today}/managed_dataflows')

    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    if filename:
        outdir = os.path.join(outdir, filename)

    return outdir


class TreeRemoverInteractor(Interactor):
    def run(self):
        # Get output directory path
        _output = _prepare_output_directory(filename=self.context.name.rstrip())

        # Execute removal
        tree_remover(dataflow=self.context.dataflow, replacers=self.context.replacers, registers=self.context.registers,
                     output=_output)

        # Lands a page to show the difference due to the removal
        original = self.context.request.FILES['dataflow'].temporary_file_path().replace(' ', "\\ ")
        _output = _output.replace(' ', "\\ ")
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


class TreeExtractorInteractor(Interactor):
    def run(self):
        output = _prepare_output_directory(allow_empty_name=True)
        dataflow = self.context.dataflow
        filename = self.context.output_filename
        registers = self.context.registers

        tree_extractor(dataflow=dataflow, registers=registers, output_dir=output, output_filename=filename)

        if pf.system() == "Darwin":

            app("Finder").reveal(mactypes.Alias(output).alias)
