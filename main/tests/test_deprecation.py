import os.path
import os.path
import os.path
import shutil

from django.test import TestCase

from libs.tcrm_automation.libs.deprecation_libs import delete_fields_of_deleted_node, perform_deprecation
from libs.tcrm_automation.libs.json_libs import get_nodes_by_action
from main.models import *


# Create your tests here.
class DeprecationTestCase(TestCase):
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

    def setUp(self) -> None:
        self.deprecation_md = json.load(open(os.getcwd() + "/main/fixtures/test-data/Field-Deprecation-Metadata.json"))
        self.objects = list(self.deprecation_md.keys())
        self.fields = [fields for _, fields in self.deprecation_md.items()]
        self.dataflows_path = f"{os.getcwd()}/main/fixtures/test-data/dataflows"
        self.media_path = "media/"
        self.test_temp_path = self.media_path + 'test-temp/'
        os.makedirs(self.test_temp_path) if not os.path.isdir(self.test_temp_path) else None

        [shutil.move(self.dataflows_path + file, self.test_temp_path + file) for file in os.listdir(self.dataflows_path)
         if os.path.isfile(self.dataflows_path + file) and '--modified' not in file]

        self.df_files = [self.test_temp_path + file for file in os.listdir(self.test_temp_path)
                         if os.path.isfile(self.test_temp_path + file) and '--modified' not in file]

    def tearDown(self) -> None:
        shutil.rmtree(self.test_temp_path)

    def test_field_deprecation(self):
        evaluations = []
        for file in self.df_files:
            basename = os.path.basename(file)
            with open(file, 'r') as df_file, open(self.test_temp_path + f"{basename} log.log", 'w') as log_file, \
                    open(file.replace('.json', '--modified.json'), 'r') as prev_deprecated_file:
                dataflow = json.load(df_file)
                prev_deprecated_df = json.load(prev_deprecated_file)
                field_md = []
                for obj in self.objects:
                    _fields = [
                        field for field in [field.strip() for field in self.fields[self.objects.index(obj)].split(',')]
                        if field not in [None, ""]
                    ]
                    _defaults = ["x" for _ in _fields]
                    md_row = {
                        "object": obj, "status": "active", "source-node": "",
                        "fields": _fields,
                        "defaults": {action: _defaults for action in self._ACTIONS}
                    }
                    field_md.append(md_row)
                node_list = get_nodes_by_action(df=dataflow, action=['sfdcDigest', 'digest', 'edgemart'])
                json_modified, collection = perform_deprecation(
                    df=dataflow, fieldlist=field_md,
                    node_list=node_list, df_name=basename,
                    log_file=log_file
                )
                json_modified = delete_fields_of_deleted_node(json_modified)

                evaluations.append(self.assertTrue(json.dumps(prev_deprecated_df) == json.dumps(json_modified)))

        self.assertTrue(all(evaluations))
