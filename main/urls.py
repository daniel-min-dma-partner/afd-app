"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.urls import path

import main.views as main

app_name = 'main'

urlpatterns = [
    path('', main.Home.as_view(), name='home'),
    path('login/', main.LoginView.as_view(), name="login"),
    path('logout/', main.logout, name="logout"),

    url(r'^sfdc/env/', include([
        url(r'^list/$', main.ConnectionStatus.as_view(), name='sfdc-env-list'),
        url(r'^create/$', main.SfdcEnvCreateView.as_view(), name='sfdc-env-create'),
        url(r'^connect/(?P<env_name>\w+)/(?P<action>\w+)/$', main.SfdcConnect.as_view(), name='sfdc-connect'),
        url(r'^edit/(?P<pk>\d+)/$', main.SfdcEnvUpdateView.as_view(), name='sfdc-env-edit'),
        url(r'^delete/$', main.SfdcEnvDelete.as_view(), name='sfdc-env-remove'),
    ])),

    path('sfdc/connected-app/oauth2/callback/', main.SfdcConnectedAppOauth2Callback.as_view(), name="sfdc-connected-app-callback"),
    path('rest/', main.Rest.as_view(), name='rest'),

    path('register/', main.RegisterUserView.as_view(), name='register-user'),

    path('slack/', main.SlackIntegrationView.as_view(), name='slack'),
    path('slack/interactive-endpoint/', main.slack_interactive_endpoint, name='slack-interactive-endpoint'),
    path('tree-remover/', main.TreeRemover.as_view(), name='tree-remover'),

    # API urls
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('sfdc/authenticate/', main.ajax_sfdc_authenticate, name='sfdc-authenticate'),
    path('sfdc-status/', main.ajax_sfdc_conn_status_view, name='sfdc_status'),
]
