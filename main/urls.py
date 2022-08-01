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
from django.conf.urls import include, re_path
from django.urls import path

import main.views as main

app_name = 'main'

urlpatterns = [
    path('', main.Home.as_view(), name='home'),
    path('login/', main.LoginView.as_view(), name="login"),
    path('logout/', main.logout, name="logout"),

    re_path(r'^sfdc/env/', include([
        re_path(r'^list/$', main.SfdcEnvListView.as_view(), name='sfdc-env-list'),
        re_path(r'^create/$', main.SfdcEnvCreateView.as_view(), name='sfdc-env-create'),
        re_path(r'^connect/(?P<pk>\w+)/(?P<action>\w+)/$', main.SfdcConnectView.as_view(), name='sfdc-connect'),
        re_path(r'^edit/(?P<pk>\d+)/$', main.SfdcEnvUpdateView.as_view(), name='sfdc-env-edit'),
        re_path(r'^delete/$', main.SfdcEnvDelete.as_view(), name='sfdc-env-remove'),
    ])),

    path('sfdc/connected-app/oauth2/callback', main.SfdcConnectedAppOauth2Callback.as_view(),
         name="sfdc-connected-app-callback"),

    path('register/', main.RegisterUserView.as_view(), name='register-user'),

    # re_path(r'^slack/', include([
    #     re_path(r'^$', main.SlackIntegrationView.as_view(), name='slack'),
    #     re_path(r'^interactive-endpoint/$', main.slack_interactive_endpoint, name='slack-interactive-endpoint'),
    #     re_path(r'^get-targets/$', main.ajax_slack_get_targets, name='slack-targets'),
    # ])),

    re_path(r'^dataflow-manager/', include([
        re_path(r'^edit/$', main.DataflowEditorView.as_view(), name='edit-dataflow'),
        re_path(r'^extract-update/$', main.TreeRemover.as_view(), name='extract-update-dataflow'),
        re_path(r'^extract-by-action/$', main.ExtractNodeByActionView.as_view(), name='extract-by-action'),
        re_path(r'^compare/$', main.CompareDataflows.as_view(), name='compare-dataflows'),
        re_path(r'^deprecate-fields/', include([
            re_path(r'^$', main.DeprecateFieldsView.as_view(), name='deprecate-fields'),
            re_path(r'^compare/(?P<pk>\d+)/$', main.CompareDeprecationView.as_view(), name='compare-deprecation'),
            re_path(r'^compare/(?P<pk>\d+)/(?P<upload>\w+)$', main.CompareDeprecationView.as_view(),
                    name='compare-deprecation'),
            re_path(r'^compare-side-by-side/(?P<pk>\d+)$', main.compare_deprecation, name='compare-side-by-side'),
            re_path(r'^compare-side-by-side/(?P<pk>\d+)/(?P<upload>\w+)$', main.compare_deprecation,
                    name='compare-side-by-side'),
            re_path(r'^delete/$', main.ajax_delete_deprecation, name='remove-deprecations'),
            re_path(r'^delete-all/$', main.deprecation_delete_all, name='deprecation-delete-all'),
            re_path(r'^view/$', main.ViewDeprecatedFieldsView.as_view(), name='view-deprecations'),
            re_path(r'^view/details/(?P<pk>\d+)$', main.DeprecationDetailsView.as_view(),
                    name='view-deprecation-detail'),
            re_path(f'^get-removed-fields/(?P<pk>\d+)/$', main.get_removed_fields_view, name='get-removed-fields'),
        ])),
        re_path(r'^locate-common-dataset/$', main.LocateCommonDataset.as_view(), name='locate-common-dataset'),
        re_path(r'^deprecation-checkerboard-excel/(?P<pk>\d+)/$',
                main.DeprecationCheckerboardExcelDownloadView.as_view(),
                name='deprecation-checkerboard-excel'),
        re_path(r'^download/$', main.DownloadDataflowView.as_view(), name='download-dataflow'),
        re_path(r'^download-deprecated/(?P<pk>\d+)$', main.dataflow_download_deprecated, name='download-deprecated'),
        re_path(r'^download-obj-fields/(?P<deprecation_pk>\d+)/$', main.download_obj_fields_md,
                name='download-obj-fields'),
        re_path(r'^download-removed-field-list/(?P<deprecation_detail_pk>\d+)/$', main.download_removed_field_list,
                name='download-removed-field-list'),
        re_path(r'^download-selected-dfs/(?P<pk>\d+)/(?P<only_dep>\w*)/(?P<errors>\w*)/(?P<none>\w*)/$',
                main.download_selected_dfs, name='download-selected-dfs'),
        re_path(r'^download-zip/(?P<pk>\d+)$', main.download_df_zip_view, name='download-zip'),
        re_path(r'^download-upload-backup/(?P<pk>\d+)/$', main.DownloadUploadBackupView.as_view(),
                name='download-upload-backup'),
        re_path(r'^generate-digest-node/$', main.DigestNodeGeneratorView.as_view(), name='digest-generator'),
        re_path(r'^list-node-from-df/$', main.list_nodes_from_df, name='list-node-from-df'),
        re_path(r'^list-datasets/$', main.DataflowListDatasetsView.as_view(), name='list-datasets'),
        re_path(r'^locate-register-node/$', main.RegisterLocalizerView.as_view(), name='register-localizer'),
        re_path(r'^merge-deprecator/$', main.MergeDeprecatorView.as_view(), name='merge-deprecator'),
        re_path(r'^select-df-file/$', main.DataflowFileSelectorView.as_view(), name='df-file-selector'),
        re_path(r'^upload/$', main.UploadDataflowView.as_view(), name='upload-dataflow'),
        re_path(r'^upload/view$', main.UploadHistoryView.as_view(), name='view-upload-history'),
    ])),

    re_path(r'^profile/', include([
        re_path(r'^create/$', main.ProfileCreateView.as_view(), name='profile-create'),
        re_path(r'^delete/(?P<pk>\d+)/$', main.profile_delete_view, name='profile-delete'),
        re_path(r'^edit/(?P<pk>\d+)/$', main.ProfileEditView.as_view(), name='profile-edit'),
        re_path(r'^view/$', main.ProfileShowView.as_view(), name='profile-view'),
        re_path(r'^$', main.ProfileShowView.as_view(), name='profile-view'),

        re_path(r'^get-type-list', main.profile_get_type_list, name='profile-get-type-list'),
    ])),

    re_path(r'^notifications/', include([
        # re_path(r'^list/$', main.ListNotificationView.as_view(), name='notification-list'),
        # re_path(r'^mark-as-read/(?P<pk>\d+)/$', main.MarkNotifAsReadView.as_view(), name='notification-read'),
        re_path(r'^mark-as-clicked/(?P<pk>\d+)/$', main.MarkNotifAsClickedView.as_view(), name='notification-clicked'),
        re_path(r'^mark-all-as-read-clicked/$', main.NotificationMarkAllAsReadClickedView.as_view(), name='mark-all'),
        re_path(r'^view/(?P<pk>\d+)$', main.NotificationDetailsView.as_view(), name='notification-detail'),
    ])),

    re_path(r'^dataset-manager/', include([
        re_path(r'^security-predicate/', include([
            re_path(r'^convert-to-saql/$', main.SecpredToSaqlView.as_view(), name='secpred-to-saql'),
        ])),
    ])),

    re_path(r'^job/', include([
        re_path(r'^list', main.JobListView.as_view(), name="job-list")
    ])),

    # re_path(r'^release/', include([
    #     re_path(r'^delete/(?P<pk>\d+)/$', main.release_delete_view, name='release-delete'),
    #     re_path(r'^create/$', main.ReleaseCreateView.as_view(), name='release-create'),
    #     re_path(r'^edit/(?P<pk>\d+)$', main.ReleaseEditView.as_view(), name='release-edit'),
    #     re_path(r'^view/$', main.ReleaseView.as_view(), name='release-view'),
    # ])),

    re_path(r'^parameter/', include([
        re_path(r'^delete/(?P<pk>\d+)/$', main.parameter_delete_view, name='parameter-delete'),
        re_path(r'^create/$', main.ParameterCreateView.as_view(), name='parameter-create'),
        re_path(r'^edit/(?P<pk>\d+)$', main.ParameterEditView.as_view(), name='parameter-edit'),
        re_path(r'^view/$', main.ParameterView.as_view(), name='parameter-view'),
    ])),

    # Ajax
    re_path(r'^ajax/', include([
        re_path(r'^list-dataflows/$', main.ajax_list_dataflows, name='ajax-list-dataflows'),
        re_path(r'^list-envs/$', main.ajax_list_envs, name='ajax-list-envs'),
        re_path(r'^get-env-key-secret/$', main.ajax_copy_key_to_clipboard, name='env-copy-secrets'),
    ])),
]
