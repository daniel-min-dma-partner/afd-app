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
from django.urls import path

import main.views as main

app_name = 'main'

urlpatterns = [
    path('', main.Home.as_view(), name='home'),
    path('login/', main.LoginView.as_view(), name="login"),
    path('logout/', main.logout, name="logout"),
    path('sfdc/env/credentials-edit/', main.SfdcEnvEditView.as_view(), name="sfdc-env-edit"),
    path('register/', main.RegisterUserView.as_view(), name='register-user'),
    path('rest/', main.Rest.as_view(), name='rest'),
    path('slack-approval-request/', main.SlackApprovalRequestView.as_view(), name='slack-approval-request'),
    path('tree-remover/', main.TreeRemover.as_view(), name='tree-remover'),

    # API urls
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('sfdc/authenticate/', main.ajax_sfdc_authenticate, name='sfdc-authenticate'),
    path('sfdc-status/', main.ajax_sfdc_conn_status_view, name='sfdc_status'),
]
