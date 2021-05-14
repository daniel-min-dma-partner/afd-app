from django.views import generic
import os
from libs.utils import current_datetime, relative_mkdir, expand_home


# Create your views here.
import main.forms as forms


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
        dataflows = request.FILES.getlist('dataflows')
        replacer = request.FILES.getlist('replacer')

        if form.is_valid():
            # print(form.cleaned_data.get('registers'))
            # print(form.cleaned_data.get('result'))
            today = current_datetime(add_time=False)
            path = expand_home(f'~/Git/dataflow-json-sync/{today}')
            if not os.path.isdir(path):
                os.mkdir(path)


            return self.form_valid(form)
        else:
            print('entro aqui')
            return self.form_invalid(form)