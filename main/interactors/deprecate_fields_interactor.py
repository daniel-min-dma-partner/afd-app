import copy
import json
import os.path
from pathlib import Path

from libs.interactor.interactor import Interactor
from libs.tcrm_automation.libs.deprecation_libs import delete_fields_of_deleted_node, perform_deprecation
from libs.tcrm_automation.libs.json_libs import get_nodes_by_action
from libs.utils import current_datetime
from main.models import DataflowDeprecation


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
        deprecation_models = []

        try:
            df_file_models = self.context.df_files
            objects = self.context.objects
            fields = self.context.fields
            user = self.context.user

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

            for df_file in df_file_models:
                with open(df_file.file.path, 'r') as f:
                    df_name = os.path.basename(df_file.file.name)
                    today_dir = df_file.file.path.replace(df_name, "")
                    deprecation_dir = os.path.join(today_dir, 'field-deprecations')

                    if not os.path.isdir(deprecation_dir):
                        Path(deprecation_dir).mkdir(parents=True, exist_ok=True)

                    dataflow = json.load(f)
                    _original = copy.deepcopy(dataflow)

                    with open(os.path.join(deprecation_dir, f"{df_name}.log"),
                              'w') as log_file:
                        node_list = get_nodes_by_action(df=dataflow, action=['sfdcDigest', 'digest', 'edgemart'])
                        json_modified = perform_deprecation(df=dataflow, fieldlist=field_md,
                                                            node_list=node_list, df_name=df_name,
                                                            log_file=log_file)
                        json_modified = delete_fields_of_deleted_node(json_modified)

                        deprecation_model = DataflowDeprecation()
                        deprecation_model.original_dataflow = _original
                        deprecation_model.deprecated_dataflow = json_modified
                        deprecation_model.user = user
                        deprecation_model.file_name = f"[{today}] {df_name}"
                        deprecation_models.append(deprecation_model)

        except Exception as e:
            _exc = e

        self.context.exception = _exc
        self.context.deprecation_models = deprecation_models
