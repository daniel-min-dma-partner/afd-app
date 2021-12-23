import json
import os.path

from django.conf import settings

from libs.interactor.interactor import Interactor
from libs.tcrm_automation.libs.deprecation_libs import get_registers
from libs.tcrm_automation.libs.json_libs import get_nodes_by_action


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
                err_as_lst = ['Field ' + field + ': ' + message['message'] for field, msgs in err_as_json.items()
                              for message in msgs]
                plural = len(err_as_lst) > 1
                title = f"The following error{'s' if plural else ''} ha{'s' if not plural else 've'} been found"
                self.context.message = f"{title}:<br/><br/><ul><li>{'</li><li>'.join(err_as_lst)}</li></ul>"
            except Exception as e:
                self.context.exception = e
