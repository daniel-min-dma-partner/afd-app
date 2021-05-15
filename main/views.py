import os

from django.views import generic

# Create your views here.
import main.forms as forms
from libs.tcrm_automation.tree_remover import tree_remover
from libs.utils import byte_to_str, expand_home, str_to_json, current_datetime
from pathlib import Path


class Home(generic.TemplateView):
    """
    Home:
    """
    module = 'home'
    template_name = 'home/home.html'


class TreeRemover(generic.FormView):
    template_name = 'tree-remover/tree-remover.html'
    form_class = forms.TreeRemoverForm
    success_url = '/tree-remover/'

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(request.POST)

        if form.is_valid():
            dataflow = request.FILES.getlist('dataflow')
            replacers = request.FILES.getlist('replacer')

            _dataflow = str_to_json(byte_to_str(dataflow[0].read()))
            _replacers = [str_to_json(byte_to_str(replacer[0].read())) for replacer in replacers]

            today = current_datetime(add_time=False)
            outdir = os.path.join(Path(__file__).resolve().parent.parent, f'libs/tcrm_automation/{today}')
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
            _output = os.path.join(outdir, form.cleaned_data['name'].rstrip())

            tree_remover(dataflow=_dataflow, replacers=_replacers,
                         registers=[register.rstrip() for register in form.cleaned_data['registers'].split('\n')],
                         output=_output)

            original = request.FILES['dataflow'].temporary_file_path().replace(' ', "\\ ")
            print('Temporally uploaded at:', original)
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

            return self.form_valid(form)
        else:
            print('entro aqui')
            return self.form_invalid(form)
