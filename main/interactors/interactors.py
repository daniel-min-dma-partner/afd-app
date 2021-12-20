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
