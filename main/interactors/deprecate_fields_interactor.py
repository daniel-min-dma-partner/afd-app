import copy
import json
import os.path
from pathlib import Path

from libs.interactor.interactor import Interactor
from libs.tcrm_automation.libs.deprecation_libs import delete_fields_of_deleted_node, perform_deprecation
from libs.tcrm_automation.libs.json_libs import get_nodes_by_action
from libs.utils import current_datetime
from main.models import DataflowDeprecation, Notifications, DeprecationDetails


class FieldDeprecatorInteractor(Interactor):
    _ACTIONS = [
        "digest",
        "sfdcDigest",
        "edgemart",
        "augment",
        "append",
        "update",
        "filter",
        "dim2mea",
        "computeExpression",
        "computeRelative",
        "flatten",
        "sliceDataset",
        "prediction",
        "sfdcRegister",
    ]

    def run(self):
        _exc = None
        _original_df_name = None
        _error_notification = False

        deprecation_detail = None
        deprecation_model = None
        deprecation_models = []
        not_deprecated_dfs = []

        try:
            df_file_models = self.context.df_files
            objects = self.context.objects
            fields = self.context.fields
            user = self.context.user
            name = self.context.name
            org = self.context.org
            case_url = self.context.case_url

            # Validates input data
            if len(objects) != len(fields):
                raise ValueError("<code>Objects</code> and <code>Fields</code> amount has to match.")

            # Prepares fields_to_deprecate.md file
            field_md = []
            for obj in objects:
                _fields = [
                    field for field in [field.strip() for field in fields[objects.index(obj)].split(',')]
                    if field not in [None, ""]
                ]
                _defaults = ["x" for _ in _fields]
                md_row = {
                    "object": obj, "status": "active", "source-node": "",
                    "fields": _fields,
                    "defaults": {action: _defaults for action in self._ACTIONS}
                }
                field_md.append(md_row)

            # Call deprecation function
            today = current_datetime(add_time=True)
            _field_md_original = copy.deepcopy(field_md)

            for df_file in df_file_models:
                with open(df_file.file.path, 'r') as f:
                    df_name = os.path.basename(df_file.file.name)
                    today_dir = df_file.file.path.replace(df_name, "")
                    deprecation_dir = os.path.join(today_dir, 'field-deprecations')

                    if not os.path.isdir(deprecation_dir):
                        Path(deprecation_dir).mkdir(parents=True, exist_ok=True)

                    dataflow = json.load(f)
                    _original = copy.deepcopy(dataflow)
                    _original_df_name = os.path.basename(df_file.file.path)

                    try:
                        with open(os.path.join(deprecation_dir, f"{df_name}.log"),
                                  'w') as log_file:

                            if not deprecation_model:
                                deprecation_model = DataflowDeprecation()
                                deprecation_model.user = user
                                deprecation_model.name = name
                                deprecation_model.salesforce_org = org
                                deprecation_model.case_url = case_url
                                deprecation_model.sobjects = "|".join(objects)
                                deprecation_model.fields = "|".join(fields)
                                deprecation_model.save()
                                deprecation_model.refresh_from_db()

                            deprecation_detail = DeprecationDetails()
                            deprecation_detail.file_name = f"[{today}] {df_name}"
                            deprecation_detail.original_dataflow = _original
                            deprecation_detail.deprecated_dataflow = _original
                            deprecation_detail.meta = _field_md_original
                            deprecation_detail.deprecation = deprecation_model
                            deprecation_detail.save()

                            node_list = get_nodes_by_action(df=dataflow, action=['sfdcDigest', 'digest', 'edgemart'])
                            json_modified, collection = perform_deprecation(df=dataflow, fieldlist=field_md,
                                                                node_list=node_list, df_name=df_name,
                                                                log_file=log_file)
                            json_modified = delete_fields_of_deleted_node(json_modified)

                            equal = json.dumps(_original) == json.dumps(json_modified)

                            if not equal:
                                deprecation_detail.deprecated_dataflow = json_modified
                                deprecation_detail.status = DeprecationDetails.SUCCESS
                                deprecation_detail.save()
                            else:
                                deprecation_detail.status = DeprecationDetails.NO_DEPRECATION
                                deprecation_detail.message = "The dataflow doesn't have any reference to the listed object/fields."
                                deprecation_detail.save()
                                not_deprecated_dfs.append(_original_df_name)
                    except Exception as e:
                        deprecation_detail.status = DeprecationDetails.ERROR
                        deprecation_detail.message = str(e)
                        deprecation_detail.save()

                        _error_notification = True
                        notif = Notifications()
                        notif.user = self.context.user
                        notif.status = 1
                        notif.message = f"Deprecation failed for <code><strong>{_original_df_name}</code></strong>" \
                                        f"<br/><strong>Reason:</strong><br/>- {str(e)}"
                        notif.type = 'danger'
                        notif.save()
                        notif.link = f'/notifications/view/{notif.pk}'
                        notif.save()

        except Exception as e:
            _exc = e

        if _error_notification:
            _exc = Exception("Deprecation finishes with error. Check notification.")

        self.context.exception = _exc
        self.context.deprecation_models = deprecation_models
        self.context.not_deprecated_dfs = not_deprecated_dfs
