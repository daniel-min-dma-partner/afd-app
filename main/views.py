import json as js
from urllib import parse

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login as do_login, logout as do_logout
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.safestring import mark_safe
from django.views import View, generic
from django.views.decorators.csrf import csrf_exempt
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework.views import APIView

from libs.utils import byte_to_str, str_to_json
from libs.utils import next_url
from main.forms import DataflowDownloadForm, LoginForm, RegisterUserForm, SfdcEnvEditForm, \
    SlackCustomerConversationForm, SlackMsgPusherForm, TreeRemoverForm, User, DataflowUploadForm, CompareDataflowForm, \
    DeprecateFieldsForm, SecpredToSaqlForm
from .interactors.dataflow_tree_manager import TreeExtractorInteractor, TreeRemoverInteractor, show_in_browser
from .interactors.deprecate_fields_interactor import FieldDeprecatorInteractor
from .interactors.download_dataflow_interactor import DownloadDataflowInteractor
from .interactors.list_dataflow_interactor import DataflowListInteractor
from .interactors.sfdc_connection_interactor import SfdcConnectWithConnectedApp
from .interactors.slack_webhook_interactor import SlackMessagePushInteractor
from .interactors.upload_dataflow_interactor import UploadDataflowInteractor
from .interactors.wdf_manager_interactor import *
from .models import SalesforceEnvironment as SfdcEnv, FileModel


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
                messages.error(request, mark_safe(f"<code>{username}</code> user doesn't exist."))
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
            messages.error(request, form.errors.as_data)

        return self.form_invalid(form)


class TreeRemover(generic.FormView):
    template_name = 'dataflow-manager/extract-update/form.html'
    form_class = TreeRemoverForm
    success_url = '/dataflow-manager/extract-update/'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['default_title'] = "Dataflow Updater"
        context['default_desc'] = "Tree Remover"
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
                    name = f"{dataflow[0].name.replace('.json', '')} with modified nodes.json"
                    ctx = TreeRemoverInteractor.call(dataflow=_dataflow, replacers=_replacers, registers=registers,
                                                     name=name, request=request)
                else:
                    ctx = TreeExtractorInteractor.call(dataflow=_dataflow, registers=registers, output_filename=name)

                print(form.cleaned_data)
                print(request.POST)
                message = ctx.output.replace('\\', '')
                message = mark_safe(f"File generated at <code>{message}</code>")
                thype = messages.INFO
            except RuntimeError as rt_e:
                print(rt_e)
                message = rt_e
                thype = messages.ERROR

            messages.add_message(request, thype, message)
            return self.form_valid(form)
        else:
            messages.error(request,
                           mark_safe("<br/>".join(str(value[0]) for _, value in form.errors.as_data().items())))
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


class SfdcEnvListView(generic.ListView):
    context_object_name = 'env_list'
    template_name = 'sfdc/env/index.html'

    def get_queryset(self):
        obj = SfdcEnv.objects.filter(user_id=self.request.user.pk)
        return obj


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
            messages.success(request, mark_safe(f"Connection <code>{sfdc_env.name}</code> modified succesfully."))
            return redirect('main:sfdc-env-list')
        else:
            messages.error(request, f'form invalid: {form.errors.as_data}')

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

                messages.success(request, mark_safe(f"New <code>{sfdc_env.name}</code> connection created successfully."))
                return redirect("main:sfdc-env-list")
            except Exception as e:
                messages.error(request, e)
        else:
            messages.error(request, form.errors.as_data)

        return self.form_invalid(form)


class SfdcEnvDelete(View):
    def post(self, request, *args, **kwargs):
        _obj = get_object_or_404(SfdcEnv, pk=request.POST.get('sfdc-id-field'))
        _obj.delete()
        messages.success(request, mark_safe(f"Connection <code>{_obj.name}</code> deleted succesfully."))

        return redirect("main:sfdc-env-list")


class SfdcConnectView(View):
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
                        env.flush_oauth_data()
                        env.set_oauth_flow_stage("LOGOUT")
                        env.save()

                        if self.session_var in self.request.session.keys():
                            del self.request.session[self.session_var]

                        if response.status_code == 200:
                            messages.success(request, mark_safe(
                                f"Logout connection <code>{env.name}</code> performed successfully"))
                        else:
                            messages.warning(request, mark_safe(f"Logout response status: {response.status_code}"))
                    else:
                        env.flush_oauth_data()
                        env.set_oauth_flow_stage("AUTHORIZATION_CODE_REQUEST")
                        env.save()
                        self.request.session[self.session_var] = request.user.pk

                        return redirect(new_url)
            except Exception as e:
                messages.warning(request, e)

        return redirect('main:sfdc-env-list')


class SfdcConnectedAppOauth2Callback(APIView):
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, format='api'):
        """
        Return a list of all users.
        """

        env = SfdcEnv.objects.get(user_id=request.session[SfdcConnectView.session_var],
                                  oauth_flow_stage=SfdcEnv.oauth_flow_stages()["AUTHORIZATION_CODE_REQUEST"])
        del request.session[SfdcConnectView.session_var]

        if 'code' in request.GET:
            env.set_oauth_flow_stage(stage="AUTHORIZATION_CODE_RECEIVE")
            env.set_oauth_authorization_code(code=request.GET.get('code'))
            env.save()
            env.refresh_from_db()

            ctx = SfdcConnectWithConnectedApp.call(env_object=env)
            response_status = ctx.response_status

            if response_status != 200:
                messages.error(request, f"Response status: {response_status}: {ctx.message}")
                env.flush_oauth_data()
                env.save()
            else:
                messages.success(request, ctx.message)

            return redirect("main:sfdc-env-list")

        return Response("'code' not received.")


class DownloadDataflowView(generic.FormView):
    form_class = DataflowDownloadForm
    module = 'dataflow-download'
    template_name = 'dataflow-manager/download/form.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(data=request.POST)
        dataflows = dict(request.POST)['dataflow_selector']

        if form.is_valid():
            try:
                env = get_object_or_404(SfdcEnv, pk=form.cleaned_data['env_selector'])
                download_ctx = DownloadDataflowInteractor.call(dataflow=dataflows, model=env, user=request.user)

                if not download_ctx.exception:
                    wdf_manager_ctx = WdfManager.call(user=request.user, mode="wdfToJson", env=env)
                else:
                    raise download_ctx.exception

                messages.info(request, "OK")

                return redirect("main:download-dataflow")
            except Exception as e:
                messages.error(request, e)
                raise e
        else:
            print(form.errors.as_data)
            messages.error(request, form.errors.as_data)

        return self.form_invalid(form)


class UploadDataflowView(generic.FormView):
    form_class = DataflowUploadForm
    module = 'dataflow-upload'
    template_name = 'dataflow-manager/upload/form.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        return context

    def post(self, request, *args, **kwargs):
        try:
            form_class = self.get_form_class()
            form: DataflowUploadForm = form_class(request.POST, request.FILES)

            if form.is_valid():
                filemodel = form.save(commit=False)
                filemodel.user = request.user
                filemodel.save()

                env = get_object_or_404(SfdcEnv, pk=form.cleaned_data['env_selector'])
                remote_df_name = form.cleaned_data['dataflow_selector']
                ctx = UploadDataflowInteractor.call(env=env, remote_df_name=remote_df_name, user=request.user,
                                                    filemodel=filemodel)
                if ctx.exception:
                    raise ctx.exception
                else:
                    msg = "Uploading <code>{0}</code> local dataflow to <code>{1}</code> dataflow to " \
                          "<code>{2}</code> connection has finished."\
                        .format(
                            os.path.basename(filemodel.file.name), remote_df_name, env.name
                        )
                    messages.info(request, mark_safe(msg))
            else:
                messages.error(request, form.errors.as_data)
        except Exception as e:
            messages.error(request, str(e))
            raise e

        return redirect("main:upload-dataflow")


class CompareDataflows(generic.FormView):
    template_name = 'dataflow-manager/compare/form.html'
    form_class = CompareDataflowForm
    success_url = '/dataflow-manager/compare/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def post(self, request, *args, **kwargs):
        try:
            form_class = self.get_form_class()
            form = form_class(request.POST, request.FILES)

            if form.is_valid():
                files_model = form.save(commit=False)
                files_model.user = request.user
                files_model.save()

                show_in_browser(original=files_model.file1.path, compared=files_model.file2.path)
                files_model.delete()

                messages.info(request, "Showing diff in browser.")
                return self.form_valid(form)
            else:
                messages.error(request, form.errors.as_data)
                return self.form_invalid(form)
        except Exception as e:
            messages.error(request, str(e))

        return redirect("main:compare-dataflows")


class DeprecateFieldsView(generic.FormView):
    template_name = 'dataflow-manager/deprecate-fields/form.html'
    form_class = DeprecateFieldsForm
    success_url = '/dataflow-manager/deprecate-fields/'

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        df_files = []

        try:
            if form.is_valid():
                # Prepare fields
                fields = [field.rstrip() for field in request.POST.get('fields').split('\n') if
                          field.rstrip() not in [None, ""]]

                # Prepare objects
                objects = [obj.rstrip() for obj in request.POST.get('objects').split('\n') if
                           obj.rstrip() not in [None, ""]]
                _objects = []

                for obj in objects:
                    if "," in obj:
                        _objects += [_object.strip() for _object in obj.split(',') if _object.strip() not in [None, ""]]
                        objects.remove(obj)
                    elif not obj:
                        objects.remove(obj)
                objects += _objects
                objects = list(set(objects))

                # Prepare dataflow contents
                for file in request.FILES.getlist('files'):
                    filemodel = FileModel(file=file)
                    filemodel.user = request.user
                    filemodel.save()
                    df_files.append(filemodel)

                # Calls interactor
                ctx = FieldDeprecatorInteractor.call(df_files=df_files, objects=objects, fields=fields)

                if ctx.exception:
                    raise ctx.exception

                for fm in df_files:
                    fm.delete()

                messages.info(request, "Ok")
                return self.form_valid(form)
            else:
                messages.error(request, form.errors.as_data())
                return self.form_invalid(form)
        except Exception as e:
            for fm in df_files:
                fm.delete()

            messages.error(request, mark_safe(str(e)))
            return redirect("main:deprecate-fields")


class ViewDeprecatedFieldsView(generic.ListView):
    context_object_name = 'list'
    template_name = 'dataflow-manager/deprecate-fields/list.html'

    def get_queryset(self):
        lst = FileModel.objects.filter(user_id=self.request.user.pk).filter(
            Q(file__icontains="field-deprecations") &
            ~Q(file__icontains="DEPRECATED__")
        ).order_by('-file')
        return lst


class SecpredToSaqlView(generic.FormView):
    template_name = 'dataset-manager/secpred-to-saql-converter/form.html'
    form_class = SecpredToSaqlForm
    success_url = '/dataset-manager/security-predicate/convert-to-saql/'


class CompareDeprecationView(generic.TemplateView):
    template_name = 'jdd/index.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        try:
            filemodel = get_object_or_404(FileModel, pk=int(kwargs['pk']))

            second_fm = FileModel.objects.filter(
                Q(file__icontains=filemodel.file.name.replace('ORIGINAL__', 'DEPRECATED__'))
            )

            if second_fm.exists():
                second_fm = second_fm.first()

                with filemodel.file.open('r') as f, second_fm.file.open('r') as g:
                    script = json.load(f)
                    left_script = json.dumps(script, indent=2)
                    script = json.load(g)
                    right_script = json.dumps(script, indent=2)
            else:
                left_script = "<< Not Found >>"
                right_script = "<< Not Found >>"
        except Exception as e:
            left_script = str(e)
            right_script = "<< Not Found >>"

        context['left_script'] = left_script
        context['right_script'] = right_script
        return context


@csrf_exempt
def ajax_compare_deprecation(request):
    payload = None
    error = "Code not executed"
    status = 400
    try:
        if request.is_ajax() and request.method == 'GET' and request.GET.getlist('pk') is not None:
            error = None
            status = 200

            filemodel = get_object_or_404(FileModel, pk=int(request.GET.getlist('pk')[0]))
            second_fm = FileModel.objects.filter(
                Q(file__icontains=filemodel.file.name.replace('ORIGINAL__', 'DEPRECATED__'))
            )
            if second_fm.exists():
                second_fm = second_fm.first()
                show_in_browser(filemodel.file.path, second_fm.file.path)
                messages.info(request, "Showing difference in a new tab.")
            else:
                raise ValueError(f"<code>{os.path.basename(filemodel.file.name.replace('ORIGINAL__', 'DEPRECATED__'))}"
                                 f"</code> doesn't exist.")
    except Exception as e:
        payload = None
        error = mark_safe(str(e))
        status = 401

    return JsonResponse({"payload": payload, "error": error}, status=status)


def ajax_copy_key_to_clipboard(request):
    payload = None
    error = "Code not executed. Contact web admin."
    status = 500

    try:
        if request.is_ajax() and request.method == "GET":
            env = get_object_or_404(SfdcEnv, pk=request.GET['pk'])
            field = "client_{0}".format(request.GET['field'])
            payload = getattr(env, field)
            error = None
            status = 200
    except Exception as e:
        payload = None
        error = str(e)
        status = 501

    return JsonResponse({"payload": payload, "error": error}, status=status)


@csrf_exempt
def ajax_delete_deprecation(request):
    message = "Code not executed. Contact to the web admin."
    typ = messages.ERROR
    try:
        if request.method == 'POST' and request.POST.getlist('id-field') is not None:

            filemodel = get_object_or_404(FileModel, pk=int(request.POST.getlist('id-field')[0]))
            second_fm = FileModel.objects.filter(
                Q(file__icontains=filemodel.file.name.replace('ORIGINAL__', 'DEPRECATED__'))
            )
            if second_fm.exists():
                second_fm = second_fm.first()
                if second_fm.parent_file.file.name == filemodel.file.name:
                    filemodel.delete()
                    message = "Deprecation deleted successfully."
                    typ = messages.SUCCESS
                else:
                    raise ValueError("For some reason, the main file and the queried parent file aren't the same.")
            else:
                raise ValueError(f"<code>{os.path.basename(filemodel.file.name.replace('ORIGINAL__', 'DEPRECATED__'))}"
                                 f"</code> doesn't exist.")
    except Exception as e:
        message = mark_safe(str(e))
        typ = messages.ERROR
        raise e

    messages.add_message(request, typ, message)
    return redirect("main:view-deprecations")


def ajax_list_dataflows(request):
    payload = {
        "results": [
            {
                "id": "",
                "text": "Select one",
            },
        ],
    }
    status = 400
    error = "There is an error. Check if the <code>Environment</code> is selected."

    if request.is_ajax and request.GET.get('q'):
        try:
            env = get_object_or_404(SfdcEnv, pk=request.GET.get('q'))
            # if env.oauth_flow_stage != SfdcEnv.oauth_flow_stages()[SfdcEnv.STATUS_ACCESS_TOKEN_RECEIVE]:
            #     raise ConnectionError(f"Env '{env.name}' is not connected.")
            ctx = DataflowListInteractor.call(model=env, search=request.GET.get('search', None),
                                              refresh_cache=request.GET.get('rc', None), user=request.user)
            payload = ctx.payload
            status = ctx.status_code
            error = ctx.error
        except Exception as e:
            status = 400
            error = str(e)
            _ = DataflowListInteractor.reset_status(request.user)

    return JsonResponse({"payload": payload, "error": error}, status=status)


def ajax_list_envs(request):
    try:
        if SfdcEnv.objects.filter(user=request.user.pk).exists():
            payload = [(model.pk, model.name)
                       for model in SfdcEnv.objects.filter(user=request.user.pk).all()]
            status = 200
            error = None
        else:
            error = "No 'Environment' has been found."
            status = 400
            payload = None
    except Exception as error:
        error = str(error)
        status = 500
        payload = None

    return JsonResponse({"payload": payload, "error": error}, status=status)


@csrf_exempt
def slack_interactive_endpoint(request):
    if request.method == "POST":
        print("Someone clicked in the link", request.POST.get('payload'))
        return JsonResponse({"message": "ok"}, status=200)
    if request.method == "GET":
        return redirect("main:home")
