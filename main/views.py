from django.views import generic

# Create your views here.
import main.forms as forms
from libs.utils import byte_to_str, str_to_json
from .interactors.dataflow_tree_manager import TreeExtractorInteractor, TreeRemoverInteractor


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

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['default_title'] = "Tree Remover"
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(request.POST)

        if form.is_valid():
            dataflow = request.FILES.getlist('dataflow')
            replacers = request.FILES.getlist('replacer')
            name = form.cleaned_data['name']
            extract = form.cleaned_data['extract']
            registers = [register.rstrip() for register in form.cleaned_data['registers'].split('\n')]

            _dataflow = str_to_json(byte_to_str(dataflow[0].read()))
            _replacers = [str_to_json(byte_to_str(replacer[0].read())) for replacer in replacers]

            try:
                if not extract:
                    _ = TreeRemoverInteractor.call(dataflow=_dataflow, replacers=_replacers, registers=registers,
                                                   name=name, request=request)
                else:
                    _ = TreeExtractorInteractor.call(dataflow=_dataflow, registers=registers, output_filename=name)
            except RuntimeError as rt_e:
                print(rt_e)

            return self.form_valid(form)

            # tree_remover(dataflow=_dataflow, replacers=_replacers, registers=registers, output=_output)
            # original = request.FILES['dataflow'].temporary_file_path().replace(' ', "\\ ")
            # diff_command = f"python diff2HtmlCompare.py -s {original} {_output}"
            # cur_dir_tmp = "_CUR_DIR_TMP_"
            # _cmd_queue = [
            #     F"export {cur_dir_tmp}=$(pwd)",
            #     "cd libs/diff2HtmlCompare",
            #     diff_command,
            #     f"cd ${cur_dir_tmp}",
            #     f"unset {cur_dir_tmp}"
            # ]
            # os.system(" && ".join(_cmd_queue))
            #
            # return self.form_valid(form)
        else:
            print('entro aqui')
            print(form.errors.as_data())
            return self.form_invalid(form)
