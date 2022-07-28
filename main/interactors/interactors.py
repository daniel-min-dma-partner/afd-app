import copy
import json
import os.path
import traceback
from typing import List

from django.conf import settings

from libs.interactor.interactor import Interactor
from libs.tcrm_automation.libs.deprecation_libs import get_registers
from libs.tcrm_automation.libs.json_libs import get_nodes_by_action, node_is
from main.models import DataflowDeprecation, DeprecationDetails


class DataflowDatasetListingInteractor(Interactor):
    def run(self):
        _exc = None
        _dataset_list = []

        try:
            dataflow_definition: dict = self.context.dataflow_definition
            digest_nodes = get_nodes_by_action(df=dataflow_definition, action=['sfdcDigest', 'digest', 'edgemart'])
            register_nodes = get_registers(nodes=digest_nodes, df=dataflow_definition)
            _dataset_list = [f"{node['dataset-name']} ({node['dataset-alias']})"
                             for _, node in register_nodes.items()]
        except Exception as e:
            _exc = e

        finally:
            self.context.exception = _exc
            self.context.dataset_list = _dataset_list


class DataflowInteractors:
    class ExtractNodeByType(Interactor):
        def run(self):
            try:
                dataflow_definition: dict = self.context.dataflow
                node_type: str = self.context.node_type
                nodes = get_nodes_by_action(df=dataflow_definition, action=node_type.strip())
                nodes = {nodename: node for (nodename, node) in nodes}
                self.context.nodes = nodes
            except Exception as e:
                self.context.exception = e

    class DeprecatorGeneratorOne(Interactor):
        def run(self):
            try:
                file = self.context.file
                lines = [line.strip() for line in file.readlines()]
                lines.sort()
                deprecator = {}
                for line in lines:
                    obj_fld = line.split('.')
                    obj = obj_fld[0].strip()
                    fld = obj_fld[1].strip()
                    if obj not in deprecator.keys():
                        deprecator[obj] = []
                    deprecator[obj].append(fld)
                for _, fields in deprecator.items():
                    fields.sort()
                deprecator = {key: ','.join([field for field in fields]) for key, fields in deprecator.items()}
                self.context.deprecator = deprecator
            except Exception as e:
                self.context.exception = e

    class ComplementFromRegister(Interactor):
        def run(self):
            try:
                registers = self.context.registers
                dataflow = self.context.dataflow

                _copy_df = copy.deepcopy(dataflow)
                for register_name in registers.keys():
                    del _copy_df[register_name]
                dataflow = copy.deepcopy(_copy_df)

                while True:
                    deleted = False
                    names = _copy_df.keys()  # names: node names or 1st-lvl keys in the df definition
                    for name in names:
                        if 'deleted' not in _copy_df[name].keys() and \
                                not node_is(action=['digest', 'sfdcDigest', 'sfdcRegister'], node=_copy_df[name]):
                            df_as_string = json.dumps(dataflow)
                            if df_as_string.count(f"\"{name}\"") == 1:
                                del dataflow[name]
                                _copy_df[name]['deleted'] = 1
                                deleted = True
                    if not deleted:
                        break

                self.context.complement = dataflow
            except Exception as e:
                self.context.exception = e

    class GetRegistersFromDatasetNameList(Interactor):
        def run(self):
            try:
                dataflow = self.context.dataflow
                datasets = self.context.datasets
                registers = {
                    nodename: {'dataset-name': node['parameters']['name'], 'dataset-alias': node['parameters']['alias']}
                    for nodename, node in dataflow.items()
                    if node_is(action='sfdcRegister', node=node) and node['parameters']['alias'] in datasets
                }
                self.context.registers = registers
            except Exception as e:
                self.context.exception = e

    class CommonDatasetLocator(Interactor):
        def run(self):
            try:
                dataflows = self.context.dataflows
                filenames = self.context.filenames
                dataset_name = self.context.dataset_name

                detected_dataflows = []
                for i in range(len(dataflows)):
                    df = dataflows[i]
                    filename = filenames[i]

                    digest_nodes = get_nodes_by_action(df=df,
                                                       action=['sfdcDigest', 'digest', 'edgemart'])
                    register_nodes = list(get_registers(nodes=digest_nodes, df=df).keys())
                    register_nodes = list(filter(
                        lambda nn: dataset_name in [df[nn]['parameters']['name'], df[nn]['parameters']['alias']],
                        register_nodes
                    ))

                    if len(register_nodes):
                        detected_dataflows.append(filename.replace('.json', ''))

                self.context.detected_dataflows = detected_dataflows
            except Exception as e:
                self.context.exception = traceback.format_exc()


class FileSystemInteractors:
    class TemporaryFolderCreator(Interactor):
        def run(self):
            try:
                directory_name = self.context.directory_name
                path = os.path.join(settings.MEDIA_ROOT, directory_name)
                if not os.path.isdir(path):
                    os.makedirs(path)
                self.context.path = path
            except Exception as e:
                self.context.exception = e


class ViewInteractors:
    class FormErrorAsMessage(Interactor):
        def run(self):
            try:
                form = self.context.form
                err_as_json = json.loads(form.errors.as_json())
                labels = {field.name: field.label for field in form}
                err_as_lst = ['Field <strong><code>' + labels[field] + '</code></strong>: ' +
                              message['message'] for field, msgs in err_as_json.items()
                              for message in msgs]
                plural = len(err_as_lst) > 1
                title = f"The following error{'s' if plural else ''} ha{'s' if not plural else 've'} been found"
                self.context.message = f"{title}:<br/><br/><ul><li>{'</li><li>'.join(err_as_lst)}</li></ul>"
            except Exception as e:
                self.context.exception = e


class JsonInteractors:
    class DeprecationMetaFileMerger(Interactor):
        def run(self):
            try:
                a = self.context.json_a
                b = self.context.json_b
                c = copy.deepcopy(a)

                for key, value in b.items():
                    if key not in a.keys():
                        c[key] = copy.deepcopy(b[key])
                        continue
                    c[key] = list(set(a[key] + b[key]))

                self.context.merged = c
            except Exception as e:
                self.context.exception = e


class DeprecationInteractors:
    class RemovedFieldsCollector(Interactor):
        def run(self):
            try:
                model: DataflowDeprecation = self.context.deprecation_model
                details: List[DeprecationDetails] = model.deprecationdetails_set.filter(
                    status=DeprecationDetails.SUCCESS).all()
                removed_fields_collection = {}
                for detail in details:
                    for object, fields in detail.removed_fields.items():
                        if not object in removed_fields_collection.keys():
                            removed_fields_collection[object] = []
                        removed_fields_collection[object] = removed_fields_collection[object] + fields
                removed_fields_collection = {key: list(set(fields)) for key, fields in
                                             removed_fields_collection.items()}
                removed_fields_flatten = [
                    f"{objct}.{field}"
                    for objct, fields in removed_fields_collection.items() for field in fields
                ]
                removed_fields_flatten.sort()
                self.context.removed_fields = "\n".join(removed_fields_flatten)
            except Exception as e:
                self.context.exception = e
