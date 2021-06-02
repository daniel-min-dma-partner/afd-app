import json as js
from urllib import parse

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login as do_login, logout as do_logout
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import generic
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.
import main.forms as forms
from libs.utils import byte_to_str, str_to_json
from libs.utils import next_url
from .interactors.dataflow_tree_manager import TreeExtractorInteractor, TreeRemoverInteractor
from .interactors.sfdc_connection_interactor import SfdcConnectWithConnectedApp, SfdcConnectionStatusCheck
from .interactors.slack_webhook_interactor import SlackMessagePushInteractor
from .models import SalesforceEnvironment as SfdcEnv


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

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You're already log in.")
            return redirect(next_url('get', request))

        form_class = self.get_form_class()
        form = form_class()
        return render(request, self.template_name, {'form': form})

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
                messages.success(request, "Loged in Successfully!")
                return redirect(next_url('post', request))
            else:
                messages.error(request, f"'{username}' user doesn't exist.")
        else:
            print('not valid', form.errors.as_data)
            messages.error(request, form.errors.as_data)
        # Si llegamos al final renderizamos el formulario
        return self.form_invalid(form)


def logout(request):
    do_logout(request)

    return render(request, "logout/logout.html")


class SfdcEnvEditView(generic.FormView):
    form_class = forms.SfdcEnvEditFormset
    module = 'register'
    template_name = 'sfdc/env/credential-edit-form.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['formset'] = forms.SfdcEnvEditFormset(queryset=SfdcEnv.objects.none())
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(data=request.POST)

        if form.is_valid():
            pass


class RegisterUserView(generic.FormView):
    form_class = forms.RegisterUserForm
    module = 'register'
    template_name = 'users/register_form.html'
    next_url = None

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['default_title'] = "Register New User"
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(data=request.POST)

        if form.is_valid():
            user: forms.User = form.save(commit=False)  # guarda en el model.
            user.is_active = 1
            user.save()

            if user is not None:
                messages.success(request, f"User '{user.username}' saved successfully.")
                return redirect("main:home")
            else:
                messages.error(request, f"Error saving new user.")
        else:
            print('form no valid', form.errors.as_data, request.POST)

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
        context['slack_target'] = self.form_class.slack_target_choices()

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
            _url = form_class.get_slack_webhook(key=form.cleaned_data.get('slack_target'))
            response = requests.post(url=_url, data=_payload, headers=_header, json=True)
            messages.info(request, response.status_code)

            return redirect("main:slack-approval-request")
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

    # print(payload, request.session['sfdc-apiuser-request-header'])
    return JsonResponse(payload, status=status_code)


def ajax_sfdc_authenticate(request):
    base_url = "https://test.salesforce.com/services/oauth2/authorize"
    parameters = {
        "client_id": "3MVG9GiqKapCZBwEtNyEQ0U2Pv34k4ziXjebvIMgh7mW2jGmX6h9ZIls_K9gMU0CFz_6kw5HcvNpE7kV5QFeo",
        "redirect_uri": "https://localhost:8080/rest",
        "response_type": "code"
    }

    url_parse = parse.urlparse(base_url)
    query = url_parse.query
    url_dict = dict(parse.parse_qsl(query))
    url_dict.update(parameters)
    url_new_query = parse.urlencode(url_dict)
    url_parse = url_parse._replace(query=url_new_query)
    new_url = parse.urlunparse(url_parse)

    return JsonResponse({"payload": new_url}, status=200)
