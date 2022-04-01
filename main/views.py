import datetime
import io
import json
import json as js
import os.path
import traceback

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login as do_login, logout as do_logout
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.files.base import ContentFile
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views import View, generic
from django.views.decorators.csrf import csrf_exempt
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework.views import APIView

import main.interactors as interactor
from core.settings import sched
from libs.utils import byte_to_str, str_to_json
from libs.utils import next_url
from main import forms
from main.forms import DataflowDownloadForm, LoginForm, RegisterUserForm, SfdcEnvEditForm, \
    SlackCustomerConversationForm, SlackMsgPusherForm, TreeRemoverForm, User, DataflowUploadForm, CompareDataflowForm, \
    DeprecateFieldsForm, SecpredToSaqlForm, ProfileForm, ReleaseForm, ParameterForm
from main.interactors.jobs_interactor import JobsInteractor
from .interactors.dataflow_tree_manager import TreeExtractorInteractor, TreeRemoverInteractor, show_in_browser, \
    RegisterLocatorInteractor
from .interactors.deprecate_fields_interactor import FieldDeprecationExcelInteractor
from .interactors.interactors import *
from .interactors.list_dataflow_interactor import DataflowListInteractor
from .interactors.response_interactor import ZipFileResponseInteractor, JsonFileResponseInteractor, \
    UploadedDataflowToZipResponse
from .interactors.sfdc_connection_interactor import OAuthLoginInteractor, SfdcConnectWithConnectedApp
from .interactors.slack_targetlist_interactor import SlackTarListInteractor
from .interactors.slack_webhook_interactor import SlackMessagePushInteractor
from .interactors.wdf_manager_interactor import *
from .models import SalesforceEnvironment as SfdcEnv, FileModel, Notifications, DataflowDeprecation, \
    DeprecationDetails, UploadNotifications, Profile, Job, Release, Parameter, DataflowUploadHistory

sched.start()


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
            messages.error(request, form.errors.as_data)
        # Si llegamos al final renderizamos el formulario
        return self.form_invalid(form)


def logout(request):
    do_logout(request)

    return render(request, "login/loginform.html")


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
            user.is_active = 0
            user.is_staff = user.is_superuser = 0
            user.save()

            if user is not None:
                messages.success(request, mark_safe(f"User <code>{user.username}</code> has been created successfully "
                                                    f"but it requires to be activated by an admin.<br/><br/>"
                                                    f"Contact the site admin to request the activation."))
                return redirect("main:home")
            else:
                messages.error(request, f"Error saving new user.")
        else:
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
                    name = name or f"[extracted] {dataflow[0].name}"
                    ext = name[-5:] if len(name) > 5 else None
                    if not ext or ext != '.json':
                        name = (name if name else f"[extracted] {dataflow[0].name}".strip()) + '.json'
                    ctx = TreeExtractorInteractor.call(dataflow=_dataflow, registers=registers, output_filename=name)

                response_ctx = JsonFileResponseInteractor.call(filepath=ctx.output)

                if response_ctx.exception:
                    raise response_ctx.exception

                return response_ctx.response
            except Exception as rt_e:
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
            slack_targets = request.POST.getlist('slack_target')
            target_names = []
            _values = {
                "case-number": form.cleaned_data['case_number'],
                "case-url": form.cleaned_data['case_url'],
                "case-description": form.cleaned_data['case_description'],
                "case-business-justification": form.cleaned_data['case_business_justification'],
                "case-manager-approval": form.cleaned_data['case_manager_approval'],
                "case-manager-name": form.cleaned_data['case_manager_name'],
                "case-contact": form.cleaned_data['case_contact'],
                "submitter": request.user.first_name + " " + request.user.last_name
                if len(request.user.first_name + request.user.last_name) else ""
            }

            if request.user.is_authenticated and request.user.first_name:
                _values['submitter'] = f"{request.user.first_name} {request.user.last_name}"

            ctx = SlackMessagePushInteractor.call(values=_values)

            _payload = js.dumps(ctx.payload)
            _header = {'Content-Type': "application/json"}
            for slack_target in slack_targets:
                _url = SlackMsgPusherForm.get_slack_webhook(key=slack_target)
                _target_name = SlackMsgPusherForm.get_slack_target_name(key=slack_target)
                response = requests.post(url=_url, data=_payload, headers=_header, json=True)

                if response.status_code != 200:
                    messages.error(request, response.text)
                    return redirect("main:slack")

                target_names.append(_target_name)

            target_names.sort()
            case_number = form.cleaned_data['case_number']
            push_msg_link = f"<a href='{form.cleaned_data['case_url']}' target='_blank'>" \
                            f"<strong>Case #{case_number}</strong></a>"
            message = f"Your approval request for the {push_msg_link} " \
                      f"has been <strong><code>successfully</code></strong> delivered " \
                      f"to the following user{'s' if len(slack_targets) > 1 else ''}:<br/><br/>" \
                      f"<ul><strong><li>{'</li><li>'.join(target_names)}</li></strong></ul>"
            messages.success(request, mark_safe(message))
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

                messages.success(request,
                                 mark_safe(f"New <code>{sfdc_env.name}</code> connection created successfully."))
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

    def get(self, request, *args, **kwargs):
        action = kwargs['action']
        pk = kwargs['pk']
        uri = None
        if action == "login":
            uri = '/services/oauth2/authorize'
        elif action == 'logout':
            uri = '/services/oauth2/revoke'

        if not uri:
            messages.warning(request, "No action selected. Choose beetwen 'login' or 'logout'.")
        else:
            try:
                env = SfdcEnv.objects.get(user=request.user, pk=pk)
                ctx = OAuthLoginInteractor.call(model=env, mode=action)

                if ctx.exception:
                    raise ctx.exception
                else:
                    messages.success(request, mark_safe(f"<code>{action.upper()}</code> performed successfully."))

            except Exception as e:
                messages.warning(request, mark_safe(e))

        return redirect('main:sfdc-env-list')


class SfdcConnectedAppOauth2Callback(APIView):
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, format='api'):
        """
        Return a list of all users.
        """
        callback_state = request.GET.get('state')
        user_id = callback_state.split('.')[0].split(':')[1]
        env_id = callback_state.split('.')[1].split(':')[1]
        env = SfdcEnv.objects.get(user_id=user_id, pk=env_id,
                                  oauth_flow_stage=SfdcEnv.oauth_flow_stages()["AUTHORIZATION_CODE_REQUEST"])

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
        dataflows = dict(request.POST)['dataflow_selector'] if 'dataflow_selector' in request.POST.keys() else []
        download_all = 'all' in request.POST.keys() and request.POST.get('all') == 'on'

        if form.is_valid():
            try:
                env = get_object_or_404(SfdcEnv, pk=form.cleaned_data['env_selector'])

                if download_all:
                    down_all_ctx = DataflowListInteractor.call(model=env, search=None,
                                                               refresh_cache='true',
                                                               user=request.user)
                    if down_all_ctx.error:
                        raise Exception(down_all_ctx.error)

                    dataflows = [item['id'] for item in down_all_ctx.payload['results']]

                if not dataflows:
                    raise KeyError("No dataflow selected")

                _n_of_dataflows = len(dataflows)
                _context_aware_msg = f"<strong>{dataflows[0]}</strong> dataflow" if _n_of_dataflows == 1 else \
                    str(_n_of_dataflows) + ' dataflows'
                _data = {"dataflows": dataflows, "model": env, "user": request.user,
                         'job-message': f"Download {_context_aware_msg} from {env.name}"}
                ctx = JobsInteractor.call(data=_data, function="download_dataflow", scheduler=sched)
                messages.success(request, mark_safe(f"Downloadig dataflow{'s' if len(dataflows) > 0 else ''} from "
                                                    f"<code>{env.name}</code> started. Check the notifications later."))

                return redirect("main:job-list")
            except Exception as e:
                messages.error(request, mark_safe(e))
        else:
            messages.error(request, form.errors.as_data)

        return self.form_invalid(form)


class UploadDataflowView(PermissionRequiredMixin, generic.FormView):
    form_class = DataflowUploadForm
    module = 'dataflow-upload'
    permission_required = ['main.special_permission_upload_dataflows']
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
                if not remote_df_name:
                    raise KeyError("Missing required field <code>Remote dataflow name</code>.")

                _data = {
                    'env': env,
                    'remote_df_name': remote_df_name,
                    'user': request.user,
                    'filemodel': filemodel,
                    'job-message': f"Upload <code><strong>{remote_df_name}</strong></code> dataflow to {env.name}",
                    'comment': form.cleaned_data['comment']
                }
                ctx = JobsInteractor.call(data=_data, function="upload_dataflow", scheduler=sched)
            else:
                messages.error(request, form.errors.as_data)
                return self.form_invalid(form)
        except Exception as e:
            messages.error(request, mark_safe(e))

        return redirect("main:job-list")


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

                _method = form.cleaned_data['method']
                if _method == 'd2h':
                    show_in_browser(original=files_model.file1.path, compared=files_model.file2.path)
                    files_model.delete()
                    return render(request, 'json_diff_output.html')
                elif _method == 'jdd':
                    with files_model.file1.open('r') as f, files_model.file2.open('r') as g:
                        script = json.load(f)
                        left_script = json.dumps(script, indent=2)  # left shows the original json.
                        script = json.load(g)
                        right_script = json.dumps(script, indent=2)  # right shows the modified json.

                    return render(request, 'jdd/index.html', {
                        'left_script': left_script,
                        'right_script': right_script,
                    })

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
    media_dir = os.path.join(settings.BASE_DIR, 'media/')
    temp_file_dir = os.path.join(media_dir, "metadatafile-{{user}}-{{datetime}}")

    fields = None
    objects = None
    filepath = None

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        df_files = []
        ctx = None

        def get_filepath(filepath_template, name, username):
            now = datetime.datetime.now().strftime(f"%Y-%m-%d-{name}")
            _filepath = filepath_template.replace("{{user}}", username).replace('{{datetime}}', now)
            return _filepath

        try:
            if form.is_valid():
                # User indicated to read metadata from file
                if form.cleaned_data.get('from_file'):
                    filemodel = FileModel(file=request.FILES.getlist('file')[0])
                    filemodel.user = request.user
                    filemodel.save()

                    metadata = json.load(open(filemodel.file.path, 'r'))
                    self.filepath = filemodel.file.path
                    self.fields = [field for _, field in metadata.items()]
                    self.objects = [obj for obj, _ in metadata.items()]

                    filemodel.delete()
                else:
                    if request.POST.get('sobjects'):
                        # Prepare fields: Each row corresponds to an Object.
                        self.fields = [field.rstrip() for field in request.POST.get('fields').split('\n') if
                                       field.rstrip() not in [None, ""]]

                        # Prepare objects: Each row must specify only one Object.
                        self.objects = [obj.rstrip() for obj in request.POST.get('sobjects').split('\n') if
                                        obj.rstrip() not in [None, ""]]
                    else:
                        # object.field format input
                        usr_input = [line.strip() for line in request.POST.get('fields').split('\n')]
                        usr_input = [line for line in usr_input if line not in ['\n', ''] and len(line) > 0]
                        usr_input.sort()
                        print(usr_input)
                        usr_input = [line.split('.') for line in usr_input]

                        objects_fields = {}
                        for combo in usr_input:
                            obj_api_name = combo[0].strip()
                            field_api_name = combo[1].strip()

                            if obj_api_name not in objects_fields.keys():
                                objects_fields[obj_api_name] = []
                            objects_fields[obj_api_name].append(field_api_name)
                        objects_fields = {obj: ','.join([field for field in fields]) for obj, fields in
                                          objects_fields.items()}

                        self.objects = []
                        self.fields = []
                        for obj, fields in objects_fields.items():
                            self.objects.append(obj)
                            self.fields.append(fields)

                # User indicated to save metadata into a file
                if form.cleaned_data.get('save_metadata'):
                    metadata = {obj: self.fields[self.objects.index(obj)] for obj in self.objects}
                    filemodel = FileModel()
                    filemodel.user = request.user
                    filemodel.file.save("Field-Deprecation-Metadata", ContentFile(json.dumps(metadata, indent=2)))
                    self.filepath = filemodel.file.path

                # Prepare dataflow contents
                for file in request.FILES.getlist('files'):
                    filemodel = FileModel(file=file)
                    filemodel.user = request.user
                    filemodel.save()
                    df_files.append(filemodel)

                # Calls job
                job_msg = f"Run deprecation <strong>'{form.cleaned_data['name']}'</strong>"
                data = {'df_files': df_files, 'objects': self.objects, 'fields': self.fields, 'user': request.user,
                        'name': form.cleaned_data['name'], 'org': form.cleaned_data['org'],
                        'case_url': form.cleaned_data['case_url'], 'job-message': job_msg}
                ctx = JobsInteractor.call(data=data, function="deprecate_fields_from", scheduler=sched)

                message = f"Deprecation <code><strong>{form.cleaned_data['name']}</strong></code> for " \
                          f"<code>{form.cleaned_data['org']}</code> has been queued."
                flash_type = messages.SUCCESS

                # Returns a normal response or file-download response
                if form.cleaned_data.get('save_metadata'):
                    response_ctx = JsonFileResponseInteractor.call(filepath=self.filepath)

                    if response_ctx.exception:
                        raise response_ctx.exception

                    # Removes temporal file
                    os.remove(self.filepath)

                    _return = response_ctx.response
                else:
                    _return = redirect('main:job-list')
            else:
                message = "Submitted form contains error. Please review it."
                flash_type = messages.ERROR
                _return = render(request, 'dataflow-manager/deprecate-fields/form.html', {'form': form})
        except Exception as e:
            message = mark_safe(traceback.format_exc())
            flash_type = messages.ERROR
            _return = redirect("main:deprecate-fields")

        messages.add_message(request, flash_type, mark_safe(message))
        return _return


class ViewDeprecatedFieldsView(generic.ListView):
    context_object_name = 'list'
    template_name = 'dataflow-manager/deprecate-fields/list2.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ViewDeprecatedFieldsView, self).get_context_data(**kwargs)
        context['days'] = self.request.GET.get('days', '')
        return context

    def get_queryset(self):
        days = self.request.GET.get('days', '30') if 'days' in self.request.GET.keys() else '30'
        days = days if days else '30'
        today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        sql_days = (today - datetime.timedelta(days=int(days))).astimezone()

        lst = DataflowDeprecation.objects.filter(user=self.request.user, created_at__gt=sql_days).order_by(
            '-created_at')
        return lst


class DeprecationDetailsView(generic.ListView):
    context_object_name = 'list'
    template_name = 'dataflow-manager/deprecate-fields/details/_form.html'

    def get_context_data(self, **kwargs):
        context = super(DeprecationDetailsView, self).get_context_data(**kwargs)
        context['deprecation'] = get_object_or_404(DataflowDeprecation, pk=self.kwargs['pk'])
        return context

    def get_queryset(self):
        lst = DeprecationDetails.objects.filter(deprecation_id=self.kwargs['pk']).order_by('file_name')
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
            condition = 'upload' in kwargs.keys() and kwargs['upload'] == 'true'
            klass = DataflowUploadHistory if condition else DeprecationDetails
            model = get_object_or_404(klass, pk=kwargs['pk'])

            left_script = json.dumps(model.original_dataflow, indent=2)
            right_script = json.dumps(
                model.uploaded_dataflow if 'upload' in kwargs.keys() else
                model.deprecated_dataflow,
                indent=2
            )
        except Exception as e:
            left_script = str(e)
            right_script = "<< Not Found >>"

        context['left_script'] = left_script
        context['right_script'] = right_script
        return context


class MarkNotifAsClickedView(generic.View):
    def get(self, request, *args, **kwargs):
        if 'pk' not in kwargs:
            raise KeyError(f"The <code><strong>pk</strong></code> for the notification clicked was not sent.")
        else:
            notification = get_object_or_404(Notifications, pk=kwargs['pk'], user=request.user)
            notification.set_read_clicked()
            notification.save()
            return redirect(f"/notifications/view/{kwargs['pk']}")


class NotificationMarkAllAsReadClickedView(generic.View):
    def get(self, request, *args, **kwargs):
        try:
            notifications = Notifications.objects.filter(user=request.user,
                                                         status__lt=Notifications.get_max_status_level())

            if notifications.exists():
                for notification in notifications.all():
                    notification.set_read_clicked()
                    notification.save()
        except Exception as e:
            messages.error(request, str(e))

        return redirect('main:home')


class NotificationDetailsView(generic.TemplateView):
    template_name = 'notifications/view.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        notification = UploadNotifications.objects.filter(pk=kwargs['pk'])
        if notification.exists():
            notification = notification.first()
        else:
            notification = get_object_or_404(Notifications, pk=kwargs['pk'])
        context['notification'] = notification
        # notification.delete()
        return context


class ProfileCreateView(generic.FormView):
    form_class = ProfileForm
    success_url = '/profile/create/'
    template_name = 'profile/create.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Adds extra form context here...

        return context

    def get(self, request, *args, **kwargs):
        form = ProfileForm()

        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = ProfileForm(request.POST)

        try:
            if form.is_valid():
                model: Profile = form.save(commit=False)
                model.user = request.user
                model.save()

                messages.success(request, mark_safe(f"<strong><code>{model.key}</code></strong> stored successfully."))
                return redirect('main:profile-view')
        except Exception as e:
            form.add_error(None, mark_safe(str(e)))

        return render(request, self.template_name, {"form": form})


class ProfileEditView(generic.FormView):
    form_class = ProfileForm
    success_url = '/profile/view/'
    template_name = 'profile/edit.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        profile = self.get_object()
        context['form'] = self.form_class(None, instance=profile)
        context['profile'] = profile
        return context

    def get_object(self, queryset=None):
        obj = Profile.objects.filter(pk=self.kwargs['pk']).first()
        return obj

    def post(self, request, *args, **kwargs):
        try:
            profile = get_object_or_404(Profile, pk=kwargs['pk'])
            form = self.form_class(request.POST, instance=profile)

            if form.is_valid():
                model: Profile = form.save(commit=False)
                model.user = request.user
                model.save()

                messages.success(request, mark_safe(f"<strong><code>{model.key}</code></strong> stored successfully."))
                return redirect('main:profile-view')
            else:
                return render(request, self.template_name, {"form": form, "profile": profile})
        except Exception as e:
            messages.error(request, mark_safe(str(e)))
            return redirect('main:profile-view')


class ProfileShowView(generic.ListView):
    template_name = 'profile/view.html'

    def get_queryset(self):
        lst = Profile.objects.filter(user=self.request.user).order_by('key')
        return lst


class JobListView(generic.ListView):
    template_name = 'jobs/list.html'

    def get_queryset(self):
        days = self.request.GET.get('days', '1') if 'days' in self.request.GET.keys() else '1'
        days = days if days else '1'
        today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        sql_days = (today - datetime.timedelta(days=int(days))).astimezone()
        queryset = Job.objects \
            .filter(user_id=self.request.user.pk, started_at__gt=sql_days) \
            .order_by('-started_at', '-pk')
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(JobListView, self).get_context_data(**kwargs)
        context['days'] = self.request.GET.get('days', '')
        return context


class ReleaseCreateView(PermissionRequiredMixin, generic.FormView):
    form_class = ReleaseForm
    permission_required = ('main.add_release',)
    success_url = '/release/view/'
    template_name = 'release/create.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()

        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            model = form.save(commit=False)
            model.publisher = request.user
            model.save()
            messages.success(request, "Release note stored successfully.")

            return redirect("main:release-view")
        else:
            messages.error(request, "Release wasn't able to create new entry. Check the form.")

        return render(request, self.template_name, {"form": form})


class ReleaseEditView(PermissionRequiredMixin, generic.FormView):
    form_class = ReleaseForm
    permission_required = ('main.change_release',)
    success_url = '/release/view/'
    template_name = 'release/edit.html'

    def get_object(self, queryset=None):
        obj = get_object_or_404(Release, pk=self.kwargs['pk'])
        return obj

    def get(self, request, *args, **kwargs):
        release = self.get_object()
        form = self.form_class(None, instance=release)

        return render(request, self.template_name, {"form": form, "release": release})

    def post(self, request, *args, **kwargs):
        release = self.get_object()
        form = self.form_class(request.POST, instance=release)

        if form.is_valid():
            model = form.save(commit=False)
            model.save()
            messages.success(request, "Release note stored successfully.")

            form = self.form_class()
            return redirect("main:release-view")
        else:
            messages.error(request, "Release wasn't able to create new entry. Check the form.")

        return render(request, self.template_name, {"form": form, "release": release})


class ReleaseView(generic.ListView):
    template_name = 'release/view.html'

    def get_queryset(self):
        queryset = Release.objects.order_by('-created_at')
        return queryset


class ParameterCreateView(PermissionRequiredMixin, generic.FormView):
    form_class = ParameterForm
    permission_required = ('main.add_parameter',)
    success_url = '/parameter/view/'
    template_name = 'parameters/create.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        sample = '{"Samples": {"Number":1,"String": "sample-text", "Boolean": true, "Array": [1,2,"three"],' \
                 '"Object": {"Number":2,"String": "sample-text-two", "Boolean": false, "Array": [4,5,"six"]}}}'

        return render(request, self.template_name, {"form": form, "sample": sample})

    def post(self, request, *args, **kwargs):
        if Parameter.objects.exists():
            messages.warning(request, "There is a system parameter JSON schema already defined. "
                                      "Update it to add new parmameters.")
            return redirect('main:parameter-view')

        form = self.form_class(request.POST)

        if form.is_valid():
            model = form.save(commit=False)
            model.save()
            messages.success(request, "Parameter stored successfully.")

            return redirect("main:parameter-view")
        else:
            messages.error(request, "Parameter wasn't able to create new entry. Check the form.")

        return render(request, self.template_name, {"form": form})


class ParameterEditView(PermissionRequiredMixin, generic.FormView):
    form_class = ParameterForm
    permission_required = ('main.change_parameter',)
    success_url = '/parameter/view/'
    template_name = 'parameters/edit.html'

    def get_object(self, queryset=None):
        obj = get_object_or_404(Parameter, pk=self.kwargs['pk'])
        return obj

    def get(self, request, *args, **kwargs):
        parameter = self.get_object()
        form = self.form_class(None, instance=parameter)

        return render(request, self.template_name, {"form": form, "parameter": parameter})

    def post(self, request, *args, **kwargs):
        parameter = self.get_object()
        form = self.form_class(request.POST, instance=parameter)

        if form.is_valid():
            model = form.save(commit=False)
            model.save()
            messages.success(request, "Parameter note stored successfully.")

            form = self.form_class()
            return redirect("main:parameter-view")
        else:
            messages.error(request, "Parameter wasn't able to create new entry. Check the form.")

        return render(request, self.template_name, {"form": form, "parameter": parameter})


class ParameterView(generic.ListView):
    template_name = 'parameters/view.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ParameterView, self).get_context_data(**kwargs)
        context['parameter_exists'] = Parameter.objects.exists()
        return context

    def get_queryset(self):
        queryset = Parameter.objects.order_by('-created_at')
        return queryset


class DataflowFileSelectorView(generic.FormView):
    template_name = 'dataflow-manager/edit/edit-form.html'
    form_class = forms.DataflowEditForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        dataflow_file = request.FILES.get('dataflow_file_selector_field')
        dataflow = json.dumps(str_to_json(byte_to_str(dataflow_file.read())), indent=2)

        return render(request, self.template_name, {'form': form, 'dataflow': dataflow, 'filename': dataflow_file.name})


class DataflowEditorView(generic.FormView):
    template_name = 'dataflow-manager/edit/edit-form.html'
    form_class = forms.DataflowEditForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        filename = request.POST.get('filename')

        if form.is_valid():
            dataflow = request.POST.get('dataflow')
            return HttpResponse(dataflow,
                                content_type='application/json',
                                headers={
                                    'Content-Disposition': f"attachment; filename={filename}"
                                })
        else:
            return render(request, self.template_name, {'form': form, 'filename': filename})


class DigestNodeGeneratorView(generic.TemplateView):
    template_name = 'dataflow-manager/edit/digest-generator-form.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['default_value'] = {
            "Digest-Node-Name": {
                "action": "sfdcDigest",
                "parameters": {
                    "object": "Account",
                    "fields": [
                        {
                            "name": "Field-Name"
                        }
                    ]
                }
            },
            "Register-Dataset": {
                "action": "sfdcRegister",
                "parameters": {
                    "name": "Dataset-Name",
                    "alias": "Dataset-Alias",
                    "source": "Digest-Node-Name"
                }
            }
        }
        return context


class RegisterLocalizerView(generic.FormView):
    template_name = 'dataflow-manager/edit/register-localizer-form.html'
    form_class = forms.RegisterNodeForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        status = 200
        error_msg = ""
        registers = []

        if form.is_valid():
            dataflow_file = request.FILES.get('dataflow')
            nodes = dict(request.POST)['node'] if 'node' in request.POST.keys() else []

            if not dataflow_file or not nodes:
                status = 500
                error_msg = "No dataflow specified." if not dataflow_file else "Missing node name."
            else:
                dataflow = str_to_json(byte_to_str(dataflow_file.read()))
                ctx = RegisterLocatorInteractor.call(dataflow=dataflow, nodes=nodes)
                registers = ctx.registers
        else:
            status = 500
            error_msg = form.errors.as_data

        if request.is_ajax():
            return JsonResponse({"error": error_msg} if status == 500 else {"registers": registers}, status=status)
        return render(request, self.template_name, {'form': form})


class ExtractNodeByActionView(generic.FormView):
    template_name = 'dataflow-manager/edit/extract-node-by-type-form.html'
    form_class = forms.ExtractNodeByActionForm

    def post(self, request, *args, **kwargs):
        print("POST")
        form = self.form_class(request.POST)

        if not form.is_valid():
            messages.error(request, mark_safe(ViewInteractors.FormErrorAsMessage.call(form=form).message))
            return self.form_invalid(form)

        try:
            dataflow_file = request.FILES.get('dataflow')
            node_type = request.POST.get('type') if 'type' in request.POST.keys() else None

            if not dataflow_file or not node_type:
                raise Exception("No dataflow specified." if not dataflow_file else "Node type is required.")

            dataflow = str_to_json(byte_to_str(dataflow_file.read()))
            ctx = DataflowInteractors.ExtractNodeByType.call(dataflow=dataflow, node_type=node_type)
            if ctx.exception:
                raise ctx.exception
            nodes = ctx.nodes

            ctx = FileSystemInteractors.TemporaryFolderCreator.call(directory_name='nodes-by-action')
            if ctx.exception:
                raise ctx.exception
            path = ctx.path
            filename = f"{node_type} from {dataflow_file.name}.json"
            filepath = os.path.join(path, filename)

            with open(filepath, "w+") as file:
                json.dump(nodes, file, indent=2)

            ctx = JsonFileResponseInteractor.call(filepath=filepath)
            if ctx.exception:
                raise ctx.exception
            return ctx.response
        except Exception as e:
            error_msg = traceback.format_exc()
            messages.error(request, mark_safe(error_msg))

        return render(request, self.template_name, {'form': form})


class UploadHistoryView(PermissionRequiredMixin, generic.TemplateView):
    template_name = 'dataflow-manager/upload/list.html'
    permission_required = ['main.special_permission_upload_dataflows']

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        query = DataflowUploadHistory.objects.filter(user=self.request.user).order_by('-created_at')
        context['list'] = query.all()
        return context


class DownloadUploadBackupView(View):
    def get(self, request, *args, **kwargs):
        model: DataflowUploadHistory = get_object_or_404(DataflowUploadHistory, pk=kwargs['pk'])
        context = UploadedDataflowToZipResponse.call(model=model, user=request.user)
        return context.response


class DeprecationCheckerboardExcelDownloadView(View):
    def get(self, request, *args, **kwargs):
        model: DataflowDeprecation = get_object_or_404(DataflowDeprecation, pk=kwargs['pk'])
        details: DeprecationDetails = model.details()
        msg = None
        msg_type = messages.SUCCESS

        if not details:
            msg = "There are no modified dataflows by this deprecation."
            msg_type = messages.INFO

        ctx = FieldDeprecationExcelInteractor.call(model=model, models=details, user=request.user)
        if ctx.exception:
            msg = str(ctx.exception)
            msg_type = messages.ERROR

        if not msg:
            filepath = ctx.filepath
            with open(filepath, "rb") as file:
                response = HttpResponse(
                    file.read(),
                    content_type='mimetype/submimetype',
                    headers={'Content-Disposition': f'attachment; filename="{model.name} Checkerboard.xlsx'},
                )
            shutil.rmtree('/'.join(filepath.split('/')[:-1]))
            return response
        else:
            messages.add_message(request, msg, msg_type)
            return redirect("main:view-deprecations")


class DataflowListDatasetsView(generic.FormView):
    template_name = 'dataflow-manager/edit/dataset-list.html'  # When GET, render the template.
    form_class = forms.RegisterNodeForm  # Just reusing the form

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        status = 200
        error_msg = ""
        datasets = []

        if form.is_valid():
            dataflow_file = request.FILES.get('dataflow')

            if dataflow_file:
                dataflow = str_to_json(byte_to_str(dataflow_file.read()))
                ctx = DataflowDatasetListingInteractor.call(dataflow_definition=dataflow)
                datasets = ctx.dataset_list
        else:
            status = 500
            error_msg = form.errors.as_data

        if request.is_ajax():
            return JsonResponse({"error": error_msg} if status == 500 else {"datasets": datasets}, status=status)
        return render(request, self.template_name, {'form': form})


class MergeDeprecatorView(generic.FormView):
    template_name = 'dataflow-manager/metadata-files/deprecator-merge-form.html'  # When GET, render the template.
    form_class = forms.DeprecatorMergeForm  # Just reusing the form

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        try:
            if form.is_valid():
                files = request.FILES.getlist('files')

                if len(files) < 2:
                    raise Exception("You need to select at least 2 files.")

                merged = {}
                for file in request.FILES.getlist('files'):
                    definition = json.load(file)
                    definition = {key: fields.split(',') for key, fields in definition.items()}

                    if not merged:
                        merged = copy.deepcopy(definition)
                        continue

                    ctx = JsonInteractors.DeprecationMetaFileMerger.call(json_a=merged, json_b=definition)
                    if ctx.exception:
                        raise ctx.exception

                    merged = ctx.merged
                merged = {key: ','.join(fields) for key, fields in merged.items()}

                response = HttpResponse(io.StringIO(json.dumps(merged)),
                                        content_type='application/json',
                                        headers={
                                            'Content-Disposition': f"attachment; filename=Merged Deprecator.json"
                                        })
                return response

            return self.form_invalid(form)
        except Exception as e:
            messages.error(request, mark_safe(str(e)))
            return redirect("main:merge-deprecator")


class LocateCommonDataset(generic.FormView):
    template_name = "dataflow-manager/inspect/form.html"
    form_class = forms.LocateCommonDatasetForm
    success_url = reverse_lazy("main:locate-common-dataset")

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            dataflows = []
            filenames = []
            dataset_name = form.cleaned_data['dataset_name']

            for file in request.FILES.getlist('dataflows'):
                dataflows.append(json.load(file))
                filenames.append(file.name)

            ctx = DataflowInteractors.CommonDatasetLocator.call(dataflows=dataflows, filenames=filenames,
                                                                dataset_name=dataset_name)

            if ctx.exception:
                messages.error(request, mark_safe(ctx.exception))
                return self.form_invalid(form)
            else:
                messages.success(request, mark_safe('<br/>'.join(ctx.detected_dataflows)))
                return self.form_valid(form)


def list_nodes_from_df(request):
    error_msg = ""
    nodes = []
    status = 200

    try:
        form_class = forms.RegisterNodeForm
        form = form_class(request.POST)

        if form.is_valid():
            dataflow_file = request.FILES.get('dataflow')

            if dataflow_file:
                dataflow = str_to_json(byte_to_str(dataflow_file.read()))
                nodes = [key for key in dataflow.keys()]
        else:
            status = 500
            error_msg = form.errors.as_data
    except Exception as e:
        status = 500
        print(e)
        error_msg = mark_safe(e)

    print(error_msg)
    return JsonResponse({"error": error_msg} if status == 500 else {"nodes": nodes}, status=status)


def download_removed_field_list(request, deprecation_detail_pk=None):
    deprecation = get_object_or_404(DeprecationDetails, pk=deprecation_detail_pk)

    basepath = f"{os.getcwd()}/media/{datetime.datetime.now().strftime('%Y/%m/%d')}/{request.user.username}/"
    media_dir = f"{basepath}download-selected-dfs/"
    filename = f'Deprecation for {os.path.basename(deprecation.file_name).replace(".json", ".zip")}'
    zipfilepath = interactor.download_dataflow_interactor.dump_deprecated(deprecation, media_dir)
    zipfile = open(zipfilepath, 'rb')
    response = HttpResponse(zipfile, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    shutil.rmtree(basepath)
    return response


def download_obj_fields_md(request, deprecation_pk=None):
    deprecation = get_object_or_404(DataflowDeprecation, pk=deprecation_pk)
    md_json = deprecation.get_objects_fields_metadata()
    return HttpResponse(md_json,
                        content_type='application/json',
                        headers={'Content-Disposition': f"attachment; filename=Objects & fields.json"})


def download_selected_dfs(request, only_dep="", errors="", none="", pk=None):
    InteractorClass = interactor.download_dataflow_interactor.DownloadSelectedDataflowInteractor
    request_data = {
        "only_dep": only_dep,
        "errors": errors,
        "none": none,
        "pk": pk,
        "request": request
    }
    ctx = InteractorClass.call(data=request_data)

    # Return final response
    return ctx.response


@permission_required("main.delete_release", raise_exception=True)
def release_delete_view(request, pk=None):
    release = get_object_or_404(Release, pk=pk)
    release.delete()
    messages.success(request, mark_safe(f"Release <code>{release.title}</code> deleted successfully"))

    return redirect("main:release-view")


@permission_required("main.delete_release", raise_exception=True)
def parameter_delete_view(request, pk=None):
    parameter = get_object_or_404(Parameter, pk=pk)
    parameter.delete()
    messages.success(request, mark_safe(f"Parameter deleted successfully"))

    return redirect("main:parameter-view")


def profile_delete_view(request, pk=None):
    user = request.user
    profile = Profile.objects.filter(user=user, pk=pk)
    status = 200

    if user.is_authenticated:
        if profile.exists():
            profile = profile.first()
            profile.delete()
            messages.success(request, mark_safe(f"<code><strong>{profile.key}</strong></code> has been removed."))
        else:
            messages.info(request, mark_safe(f"Profile with key <code>{pk}</code> not found"))
    else:
        status = 500
        messages.error(request, mark_safe(f"User <code>{user.username}</code> is not authenticated."))

    return JsonResponse({"payload": "", "error": ""}, status=status)


def profile_get_type_list(request):
    try:
        payload = {
            "results": Profile.TYPE_CHOICE_SELECT2
        }

        search = request.GET.get('search')

        if search:
            payload['results'] = [item for item in payload['results'] if
                                  search.strip().lower() in item['text'].strip().lower()]

        status = 200
        error = None
    except Exception as e:
        error = str(e)
        status = 500
        payload = None

    return JsonResponse({"payload": payload, "error": error}, status=status)


def dataflow_download_deprecated(request, pk=None):
    try:
        deprecation_detail = get_object_or_404(DeprecationDetails, pk=pk)
        filename = deprecation_detail.file_name
        if deprecation_detail.status != DeprecationDetails.SUCCESS:
            json_str = json.dumps(deprecation_detail.deprecated_dataflow, indent=2)
            response = HttpResponse(json_str,
                                    content_type='application/json',
                                    headers={'Content-Disposition': f'attachment; filename={filename}.json'})
        else:
            # Creates temporal media directory
            basedir = f"{os.getcwd()}/media/{datetime.datetime.now().strftime('%Y/%m/%d')}/{request.user.username}/"
            media_dir = basedir + 'download-selected-dfs/'
            if not os.path.exists(media_dir):
                os.makedirs(media_dir)

            zipfile_path = interactor.download_dataflow_interactor.dump_deprecated(
                detail=deprecation_detail, media_dir=media_dir
            )
            zipfile = open(zipfile_path, 'rb')
            response = HttpResponse(zipfile, content_type='application/zip')
            filename = filename.replace('.json', '.zip')
            response['Content-Disposition'] = f'attachment; filename={filename}'

            # Removes the media directory
            shutil.rmtree(basedir)
    except Exception as e:
        messages.error(request, mark_safe(str(e)))
        response = redirect('main:view-deprecations')

    return response


@permission_required("main.special_permission_delete_all_deprecation", raise_exception=True)
def deprecation_delete_all(request):
    user = request.user
    deprecations = DataflowDeprecation.objects.filter(user=user)
    status = 200

    if user.is_authenticated:
        if deprecations.exists():
            for dep in deprecations.all():
                dep.delete()
            messages.success(request, "All deprecation has been removed.")
        else:
            messages.info(request, "No deprecation has been found.")
    else:
        status = 500
        messages.error(request, mark_safe(f"User <code>{user.username}</code> is not authenticated."))

    return JsonResponse({"payload": "", "error": ""}, status=status)


def handler500(request, exception=None):
    return render(request, '500.html', {"exception": mark_safe(str(exception))}, status=500)


def handler403(request, exception=None):
    return render(request, '403.html', {"exception": mark_safe(str(exception))}, status=403)


@csrf_exempt
def compare_deprecation(request, pk=None, upload=None):
    error = "Code not executed"
    try:
        if request.method == 'GET' and pk is not None:
            condition = upload and upload == 'true'
            klass = DataflowUploadHistory if condition else DeprecationDetails
            print(condition)

            model = get_object_or_404(klass, pk=pk)

            filemodel = FileModel()
            filemodel.user = request.user
            filemodel.file.save('Original.json',
                                ContentFile(json.dumps(model.original_dataflow, indent=2)))
            second_fm = FileModel()
            second_fm.user = request.user
            second_fm.file.save('Deprecated.json',
                                ContentFile(json.dumps(
                                    model.uploaded_dataflow if condition
                                    else model.deprecated_dataflow,
                                    indent=2
                                )))

            show_in_browser(filemodel.file.path, second_fm.file.path)

            filemodel.delete()
            second_fm.delete()

            messages.info(request, "Showing difference in a new tab.")

            return render(request, 'json_diff_output.html')

    except Exception as e:
        error = mark_safe(str(e))

    messages.error(request, error)
    return redirect('main:view-deprecations')


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
            deprecation_name = request.POST.get('name-field')
            deprecation_model = get_object_or_404(DataflowDeprecation, pk=int(request.POST.get('id-field')))

            deprecation_model.delete()
            message = mark_safe(f"Deprecation <strong><code>{deprecation_name}</code></strong> deleted successfully.")
            typ = messages.SUCCESS
    except Exception as e:
        message = mark_safe(str(e))
        typ = messages.ERROR

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
            payload = {
                "results": [
                    {
                        "id": model.pk,
                        "text": model.name
                    }
                    for model in SfdcEnv.objects.filter(user=request.user.pk).all()
                ]
            }

            search = request.GET.get('search')

            if search:
                payload['results'] = (item for item in payload['results'] if search in item['text'])

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


def ajax_slack_get_targets(request):
    payload = {
        "results": [
            {
                "id": "",
                "text": "Select one",
            },
        ],
    }

    try:
        if request.is_ajax() and request.method == 'GET':
            ctx = SlackTarListInteractor.call()

            if ctx.exception:
                raise ctx.exception

            status = ctx.status
            error = None
            payload = ctx.payload
        else:
            raise Exception("The type of the request must be either ajax and GET method.")
    except Exception as e:
        error = mark_safe(e)
        status = 400

    return JsonResponse({"payload": payload, "error": error}, status=status)


def download_df_zip_view(request, pk=None):
    notif = UploadNotifications.objects.filter(pk=pk)
    message = ""
    thype = messages.ERROR

    if notif.exists():
        notif = notif.first()
        zipfile_path = notif.zipfile_path

        if not os.path.isfile(zipfile_path):
            notif.delete()
            message = "The file doesn't exist anymore. Try to re-download it."
        else:
            envname = notif.envname
            ctx = ZipFileResponseInteractor.call(zipfile_path=zipfile_path, envname=envname)

            if ctx.exception:
                message = mark_safe(ctx.exception)
            else:
                notif.delete()
                os.remove(zipfile_path)
                return ctx.response
    else:
        message = "This in an expired notification."
        thype = messages.WARNING

    messages.add_message(request, thype, message)
    return redirect('main:home')


def get_removed_fields_view(request, pk=None):
    payload = None
    error = "System Error: No code executed. Contact the site administrator."
    status = 500
    try:
        if request.is_ajax() and request.method == 'GET':
            deprecation_model = DataflowDeprecation.objects.get(pk=pk)
            if not deprecation_model:
                raise Exception("The deprecation record doesn't exist.")

            ctx = DeprecationInteractors.RemovedFieldsCollector.call(deprecation_model=deprecation_model)
            if ctx.exception:
                raise ctx.exception

            status = 200
            payload = ctx.removed_fields
    except Exception as e:
        error = mark_safe(traceback.format_exc())
        status = 400
        payload = None

    return JsonResponse({"payload": payload, "error": error}, status=status)
