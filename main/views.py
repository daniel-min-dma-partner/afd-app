import json as js
from urllib import parse

import requests
from django.contrib.auth import authenticate, login as do_login
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import generic
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.
import main.forms as forms
from libs.utils import byte_to_str, str_to_json
from .interactors.dataflow_tree_manager import TreeExtractorInteractor, TreeRemoverInteractor
from .interactors.sfdc_connection_interactor import SfdcConnectWithConnectedApp, SfdcConnectionStatusCheck
from .interactors.slack_webhook_interactor import SlackMessagePushInteractor


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


class LoginView(generic.FormView):
    """
    Login view:
    """
    form_class = forms.LoginForm
    module = 'login'
    template_name = 'login/loginform.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['default_title'] = "Login"
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(data=request.POST)

        if form.is_valid():
            # Recuperamos las credenciales validadas
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Verificamos las credenciales del usuario
            user = authenticate(username=username, password=password)

            # Si existe un usuario con ese nombre y contraseña
            if user is not None:
                # Hacemos el login manualmente
                do_login(request, user)
                # Y le redireccionamos a la portada
                return redirect('/')
            else:
                print(user)
        else:
            print('not valid', form.errors.as_data)
        # Si llegamos al final renderizamos el formulario
        return self.form_invalid(form)


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
            replacers = request.FILES.getlist('replacers')
            name = form.cleaned_data['name']
            extract = form.cleaned_data['extract']
            registers = [register.rstrip() for register in form.cleaned_data['registers'].split('\n')]

            _dataflow = str_to_json(byte_to_str(dataflow[0].read()))
            _replacers = [str_to_json(byte_to_str(replacer.read())) for replacer in replacers]

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
        else:
            print('entro aqui')
            print(form.errors.as_data())
            return self.form_invalid(form)


class SlackApprovalRequestView(generic.FormView):
    template_name = 'slack-approval-request-form/index.html'
    form_class = forms.SlackMsgPusherForm
    success_url = '/slack-approval-request/'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Adds extra form context here...
        context['default_title'] = "Approval Request Message Pusher - Slack"

        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(request.POST)

        if form.is_valid():
            _values = {
                "case-number": form.cleaned_data['case_number'],
                "case-url": form.cleaned_data['case_url'],
                "case-description": form.cleaned_data['case_description'],
                "case-business-justification": form.cleaned_data['case_business_justification'],
                "case-manager-approval": form.cleaned_data['case_manager_approval'],
                "case-manager-name": form.cleaned_data['case_manager_name'],
            }

            ctx = SlackMessagePushInteractor.call(values=_values)
            _payload = js.dumps(ctx.payload)

            _header = {'Content-Type': "application/json"}
            _url = "https://hooks.slack.com/services/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"  # channel
            _url_dpark = "https://hooks.slack.com/services/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"
            response = requests.post(url=_url, data=_payload, headers=_header, json=True)
            print(response)

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class Rest(APIView):
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, format='api'):
        """
        Return a list of all users.
        """
        print(request)
        ctx = SfdcConnectWithConnectedApp.call(request=request)
        return Response(ctx.message)


def ajax_sfdc_conn_status_view(request):
    # request should be ajax and method should be POST.
    payload = None
    status_code = 500

    if request.is_ajax and request.method == "GET":
        ctx = SfdcConnectionStatusCheck.call(request=request)
        payload = ctx.response
        status_code = ctx.status_code

    print(payload, request.session['sfdc-apiuser-request-header'])
    return JsonResponse(payload, status=status_code)


            clear_session(request.session)

    print(error_msg, response, response_status)
    return JsonResponse({"message": response, "error": error_msg, "instance_url": instance}, status=response_status)
