from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from .models import SalesforceEnvironment as SfdcEnv


class SfdcCRUDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'pk' in view_kwargs.keys():
            pk = view_kwargs['pk']
        elif 'sfdc-id-field' in request.POST:
            pk = request.POST.get('sfdc-id-field')
        else:
            return

        current_url = request.path
        sfdc_delt_url = reverse('main:sfdc-env-remove')
        sfdc_edit_url = reverse('main:sfdc-env-edit', kwargs={'pk': pk})

        if current_url in [sfdc_edit_url, sfdc_delt_url]:
            sfdc_env = get_object_or_404(SfdcEnv, pk=pk)
            if sfdc_env.oauth_flow_stage != SfdcEnv.oauth_flow_stages()['LOGOUT']:
                action = 'delete' if current_url == sfdc_delt_url else 'edit'
                messages.error(request, f"Cannot {action} env '{sfdc_env.name}': "
                                        f"The env is used to be connected now. Disconnect first.")
                return redirect('main:sfdc-env-list')
