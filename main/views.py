import requests
from django.http import JsonResponse
from django.views import generic
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.
import main.forms as forms
from libs.utils import byte_to_str, str_to_json
from .interactors.dataflow_tree_manager import TreeExtractorInteractor, TreeRemoverInteractor


def ajax_sfdc_conn_status_view(request):
    # request should be ajax and method should be POST.
    error_msg = ""
    response = ""
    response_status = 200

    if request.is_ajax and request.method == "GET":
        # get the form data
        response = _sfdc_status_check(request)

        if response != "Yes":
            error_msg = response
            response_status = 400

    return JsonResponse({"message": response, "error": error_msg}, status=response_status)


def _sfdc_status_check(request):
    if 'sfdc-apiuser-access-token' not in request.session.keys():
        return "No"

    sfdc_apiuser_request_header = 'sfdc-apiuser-request-header'
    sfdc_apiuser_request_instance = 'sfdc-apiuser-request-instance'

    header = request.session[sfdc_apiuser_request_header]
    instance_url = request.session[sfdc_apiuser_request_instance]
    dataflows_url = '/services/data/v51.0/wave/dataflows/'

    url = instance_url + dataflows_url
    response = requests.get(url, headers=header)
    status = response.status_code

    if response.text:
        response = response.json()

    if isinstance(response, list) and 'errorCode' in response[0].keys():
        return response[0]['errorCode']

    if 'dataflows' in response.keys():
        return "Yes"

    return "No"


class Home(generic.TemplateView):
    """
    Home:
    """
    module = 'home'
    template_name = 'home/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # login_status = _sfdc_status_check(self.request)
        # context['sfdc_login_status'] = login_status
        return context


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
                    name = f"{dataflow[0].name.replace('.json', '')} with removed nodes.json"
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


class Rest(APIView):
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, format='api'):
        """
        Return a list of all users.
        """

        if 'code' in request.GET:
            env = 'test'
            auth_code = request.GET.get('code')
            secret = '27A8FA1974441479425E8372A3F8A0D6F2F10F55F9EF62B92E430D049A238E2E'
            key = '3MVG9GiqKapCZBwEtNyEQ0U2Pv34k4ziXjebvIMgh7mW2jGmX6h9ZIls_K9gMU0CFz_6kw5HcvNpE7kV5QFeo'

            url = f"https://{env}.salesforce.com/services/oauth2/token?client_id=" \
                  f"{key}&grant_type=authorization_code" \
                  f"&code={str(auth_code)}&redirect_uri=https://localhost:8080/rest&client_secret={str(secret)}"
            response = requests.get(url)

            if response.text:
                response = response.json()

            header = {'Authorization': "Bearer " + response["access_token"], 'Content-Type': "application/json"}

            sfdc_apiuser_request_header = 'sfdc-apiuser-request-header'
            sfdc_apiuser_request_instance = 'sfdc-apiuser-request-instance'
            sfdc_apiuser_access_token = 'sfdc-apiuser-access-token'

            request.session[sfdc_apiuser_request_header] = header
            request.session[sfdc_apiuser_request_instance] = response['instance_url']
            request.session[sfdc_apiuser_access_token] = response["access_token"]

            return Response("Authentication Success!!!")

        else:
            return Response("Someting went wrong" + str(request))
