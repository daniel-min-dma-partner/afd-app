import json as js
from urllib import parse

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login as do_login, logout as do_logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View, generic
from django.views.decorators.csrf import csrf_exempt
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework.views import APIView

from core.settings import SALESFORCE_INSTANCE_URLS
from libs.utils import byte_to_str, str_to_json
from libs.utils import next_url
from main.forms import LoginForm, RegisterUserForm, SfdcEnvEditForm, SlackCustomerConversationForm, \
    SlackMsgPusherForm, \
    TreeRemoverForm, User
from .interactors.dataflow_tree_manager import TreeExtractorInteractor, TreeRemoverInteractor
from .interactors.sfdc_connection_interactor import SfdcConnectWithConnectedApp, SfdcConnectWithConnectedApp2, \
    SfdcConnectionStatusCheck
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
    form_class = LoginForm
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


class RegisterUserView(generic.FormView):
    form_class = RegisterUserForm
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
            user: User = form.save(commit=False)  # guarda en el model.
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
    form_class = TreeRemoverForm
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


class SlackIntegrationView(generic.FormView):
    form_class = SlackMsgPusherForm
    success_url = '/slack/'
    template_name = 'slack/index.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Adds extra form context here...
        context['default_title'] = "Approval Request Message Pusher - Slack"
        context['slack_target'] = self.form_class.slack_target_choices()
        context['customer_conversation_form'] = SlackCustomerConversationForm()

        return context

    def post(self, request, *args, **kwargs):
        form = SlackMsgPusherForm(request.POST)
        form_customer_initial = SlackCustomerConversationForm(request.POST)

        if form.is_valid():
            _values = {
                "case-number": form.cleaned_data['case_number'],
                "case-url": form.cleaned_data['case_url'],
                "case-description": form.cleaned_data['case_description'],
                "case-business-justification": form.cleaned_data['case_business_justification'],
                "case-manager-approval": form.cleaned_data['case_manager_approval'],
                "case-manager-name": form.cleaned_data['case_manager_name'],
                "case-contact": form.cleaned_data['case_contact'],
                "submitter": ""
            }

            if request.user.is_authenticated and request.user.first_name:
                _values['submitter'] = f"{request.user.first_name} {request.user.last_name}"

            ctx = SlackMessagePushInteractor.call(values=_values)
            _payload = js.dumps(ctx.payload)

            _header = {'Content-Type': "application/json"}
            _url = SlackMsgPusherForm.get_slack_webhook(key=form.cleaned_data.get('slack_target'))
            response = requests.post(url=_url, data=_payload, headers=_header, json=True)

            if response.status_code != 200:
                print(response.text)
                messages.error(request, response.text)
                return self.form_invalid(form)
            else:
                messages.info(request, f"Response status: {response.status_code}")
                return redirect("main:slack")
        elif form_customer_initial.is_valid():
            messages.success(request, "Form 2 Works.")
            return redirect("main:slack")
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


class SfdcEnvListView(generic.ListView):
    context_object_name = 'sfdc_env_list'
    template_name = 'sfdc/env/credential-list-view.html'

    def get_queryset(self):
        return SfdcEnv.objects.filter(user=self.request.user)


class SfdcEnvUpdateView(generic.TemplateView):
    form_class = SfdcEnvEditForm
    template_name = 'sfdc/env/edit.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['form'] = self.form_class(self.request.POST or None, instance=self.get_object())
        context['pk'] = self.kwargs['pk']
        return context

    def get_object(self, queryset=None):
        obj = SfdcEnv.objects.filter(pk=self.kwargs['pk']).first()
        return obj

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=get_object_or_404(SfdcEnv, pk=kwargs['pk']))
        if form.is_valid():
            sfdc_env = form.save(commit=False)
            sfdc_env.user = request.user
            sfdc_env.save()
            messages.info(request, 'form valid')
            return redirect('main:sfdc-env-list')
        else:
            messages.error(request, f'form invalid:{form.errors.as_data}')

        return render(request, self.template_name, {'form': form})


class SfdcEnvCreateView(generic.FormView):
    form_class = SfdcEnvEditForm
    module = 'register'
    template_name = 'sfdc/env/create.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['environment_choice'] = SfdcEnv.environment_choice()
        context['default_category'] = "H.U.S.H."
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(data=request.POST)

        if form.is_valid():
            try:
                sfdc_env = form.save(commit=False)
                sfdc_env.user = request.user
                sfdc_env.save()

                messages.info(request, f"New '{sfdc_env.name}' env created successfully.")
                return redirect("main:sfdc-env-list")
            except Exception as e:
                messages.error(request, e)
        else:
            messages.error(request, form.errors.as_data)

        return self.form_invalid(form)


def sfdc_env_delete(request, pk):
    if request.method == "GET":
        _obj = get_object_or_404(SfdcEnv, pk=pk)
        # _obj.delete()
        messages.info(request, f"SF Env '{_obj.name}' deleted successfully.")

    return redirect('main:sfdc-env-list')


class SfdcEnvDelete(View):
    def post(self, request, *args, **kwargs):
        _obj = get_object_or_404(SfdcEnv, pk=request.POST.get('sfdc-id-field'))
        # _obj.delete()
        messages.info(request, f"Sfdc Env '{_obj.name}' deleted succesfully.")

        return redirect("main:sfdc-env-list")


class ConnectionStatus(generic.ListView):
    """
    Connections:
    """
    module = 'connections'
    template_name = 'connections/index.html'
    context_object_name = 'env_list'

    def get_queryset(self):
        obj = SfdcEnv.objects.filter(user_id=self.request.user.pk)
        return obj


class SfdcConnect(View):
    module = 'sfdc-connect'
    session_var = "request.user.id"

    def get(self, request, *args, **kwargs):
        action = kwargs['action']
        env_nm = kwargs['env_name']
        uri = None
        if action == "login":
            uri = '/services/oauth2/authorize'
        elif action == 'logout':
            uri = '/services/oauth2/revoke'

        if not uri:
            messages.warning(request, "No action selected. Choose beetwen 'login' or 'logout'.")
        else:
            try:
                env = SfdcEnv.objects.get(user=request.user, name=env_nm)

                if env.oauth_flow_stage == 0 and action == 'logout':
                    messages.info(request, 'You already have been logout.')
                else:
                    url = env.environment + uri
                    parms = {
                        "client_id": env.client_key,
                        "redirect_uri": "https://localhost:8080/sfdc/connected-app/oauth2/callback",
                        "response_type": "code"
                    } if action == "login" else {
                        "token": env.oauth_access_token
                    }

                    url_parse = parse.urlparse(url)
                    query = url_parse.query
                    url_dict = dict(parse.parse_qsl(query))
                    url_dict.update(parms)
                    url_new_query = parse.urlencode(url_dict)
                    url_parse = url_parse._replace(query=url_new_query)
                    new_url = parse.urlunparse(url_parse)

                    if action == 'logout':
                        response = requests.post(new_url)

                        if response.status_code == 200:
                            env.flush_oauth_data()
                            env.set_oauth_flow_stage("LOGOUT")
                            env.save()

                            messages.success(request, f"Logout successfully from '{env.name}' environment.")

                            if self.session_var in self.request.session.keys():
                                del self.request.session[self.session_var]
                        else:
                            messages.warning(request, f"Logout response status: {response.status_code}")
                    else:
                        env.flush_oauth_data()
                        env.set_oauth_flow_stage("AUTHORIZATION_CODE_REQUEST")
                        env.save()
                        self.request.session[self.session_var] = request.user.pk

                        return redirect(new_url)
            except Exception as e:
                messages.warning(request, e)
                raise e

        return redirect('main:sfdc-env-list')


class SfdcConnectedAppOauth2Callback(APIView):
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, format='api'):
        """
        Return a list of all users.
        """

        env = SfdcEnv.objects.get(user_id=request.session[SfdcConnect.session_var],
                                  oauth_flow_stage=SfdcEnv.oauth_flow_stages()["AUTHORIZATION_CODE_REQUEST"])
        del request.session[SfdcConnect.session_var]

        if 'code' in request.GET:
            env.set_oauth_flow_stage(stage="AUTHORIZATION_CODE_RECEIVE")
            env.set_oauth_authorization_code(code=request.GET.get('code'))
            env.save()
            env.refresh_from_db()
            ctx = SfdcConnectWithConnectedApp2.call(env_object=env)
            messages.info(request, ctx.message)
            return redirect("main:sfdc-env-list")

        return Response("'code' not received.")


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


def ajax_sfdc_authenticate(request, env="Sandbox"):
    instance_url = SALESFORCE_INSTANCE_URLS[env]
    base_url = f"{instance_url}/services/oauth2/authorize"
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


@csrf_exempt
def slack_interactive_endpoint(request):
    if request.method == "POST":
        print("Someone clicked in the link", request.POST.get('payload'))
        return JsonResponse({"message": "ok"}, status=200)
    if request.method == "GET":
        return redirect("main:home")
