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
handler500 = 'main.views.handler500'

urlpatterns = [
    path('', main.Home.as_view(), name='home'),
    path('login/', main.LoginView.as_view(), name="login"),
    path('logout/', main.logout, name="logout"),

    url(r'^sfdc/env/', include([
        url(r'^list/$', main.SfdcEnvListView.as_view(), name='sfdc-env-list'),
        url(r'^create/$', main.SfdcEnvCreateView.as_view(), name='sfdc-env-create'),
        url(r'^connect/(?P<pk>\w+)/(?P<action>\w+)/$', main.SfdcConnectView.as_view(), name='sfdc-connect'),
        url(r'^edit/(?P<pk>\d+)/$', main.SfdcEnvUpdateView.as_view(), name='sfdc-env-edit'),
        url(r'^delete/$', main.SfdcEnvDelete.as_view(), name='sfdc-env-remove'),
    ])),

    path('sfdc/connected-app/oauth2/callback/', main.SfdcConnectedAppOauth2Callback.as_view(),
         name="sfdc-connected-app-callback"),

    path('register/', main.RegisterUserView.as_view(), name='register-user'),

    url(r'^slack/', include([
        url(r'^$', main.SlackIntegrationView.as_view(), name='slack'),
        url(r'^interactive-endpoint/$', main.slack_interactive_endpoint, name='slack-interactive-endpoint'),
        url(r'^get-targets/$', main.ajax_slack_get_targets, name='slack-targets'),
    ])),

    url(r'^dataflow-manager/', include([
        url(r'^extract-update/$', main.TreeRemover.as_view(), name='extract-update-dataflow'),
        url(r'^compare/$', main.CompareDataflows.as_view(), name='compare-dataflows'),
        url(r'^deprecate-fields/', include([
            url(r'^$', main.DeprecateFieldsView.as_view(), name='deprecate-fields'),
            url(r'^view/$', main.ViewDeprecatedFieldsView.as_view(), name='view-deprecations'),
            url(r'^view/details/(?P<pk>\d+)$', main.DeprecationDetailsView.as_view(), name='view-deprecation-detail'),
            url(r'^compare-side-by-side/(?P<pk>\d+)$', main.compare_deprecation, name='compare-side-by-side'),
            url(r'^compare/(?P<pk>\d+)/$', main.CompareDeprecationView.as_view(), name='compare-deprecation'),
            url(r'^delete/$', main.ajax_delete_deprecation, name='remove-deprecations'),
            url(r'^delete-all/$', main.deprecation_delete_all, name='deprecation-delete-all'),
        ])),
        url(r'^download/$', main.DownloadDataflowView.as_view(), name='download-dataflow'),
        url(r'^download-zip/(?P<pk>\d+)$', main.download_df_zip_view, name='download-zip'),
        url(r'^download-deprecated/(?P<pk>\d+)$', main.dataflow_download_deprecated, name='download-deprecated'),
        url(r'^upload/$', main.UploadDataflowView.as_view(), name='upload-dataflow'),
    ])),

    url(r'^profile/', include([
        url(r'^create/', main.ProfileCreateView.as_view(), name='profile-create'),
        url(r'^delete/(?P<pk>\d+)/$', main.profile_delete_view, name='profile-delete'),
        url(r'^edit/(?P<pk>\d+)/$', main.ProfileEditView.as_view(), name='profile-edit'),
        url(r'^view/', main.ProfileShowView.as_view(), name='profile-view'),
        url(r'^$', main.ProfileShowView.as_view(), name='profile-view'),

        url(r'^get-type-list', main.profile_get_type_list, name='profile-get-type-list'),
    ])),

    url(r'^notifications/', include([
        # url(r'^list/$', main.ListNotificationView.as_view(), name='notification-list'),
        # url(r'^mark-as-read/(?P<pk>\d+)/$', main.MarkNotifAsReadView.as_view(), name='notification-read'),
        url(r'^mark-as-clicked/(?P<pk>\d+)/$', main.MarkNotifAsClickedView.as_view(), name='notification-clicked'),
        url(r'^mark-all-as-read-clicked/$', main.NotificationMarkAllAsReadClickedView.as_view(), name='mark-all'),
        url(r'^view/(?P<pk>\d+)$', main.NotificationDetailsView.as_view(), name='notification-detail'),
    ])),

    url(r'^dataset-manager/', include([
        url(r'^security-predicate/', include([
            url(r'^convert-to-saql/$', main.SecpredToSaqlView.as_view(), name='secpred-to-saql'),
        ])),
    ])),

    # Ajax
    url(r'^ajax/', include([
        url(r'^list-dataflows/$', main.ajax_list_dataflows, name='ajax-list-dataflows'),
        url(r'^list-envs/$', main.ajax_list_envs, name='ajax-list-envs'),
        url(r'^get-env-key-secret/$', main.ajax_copy_key_to_clipboard, name='env-copy-secrets'),
    ])),
]
