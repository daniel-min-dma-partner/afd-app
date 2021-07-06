import os
from pathlib import Path

from libs.interactor.interactor import Interactor
from libs.utils import current_datetime


class JsonToWdfInteractor(Interactor):
    def run(self):
        import json

        with open(self.context.json_filepath, 'r') as f:
            j = json.load(f)
            j = [str({'nodes': j}), None]
            j[0] = j[0].replace("\"", '\\\"').replace("'", '\"').replace(', ', ',').replace(': ', ':')

            with open(self.context.wdf_filepath, 'w') as g:
                g.write(f"{str(json.dumps(j))}")


class WdfToJsonInteractor(Interactor):
    def run(self):
        import json

        with open(self.context.wdf_filepath, 'r') as f:
            j = json.loads(f.read())[0]

        os.system('clear')
        k = json.loads(j)
        if 'nodes' in k:
            pld = k['nodes']
        else:
            pld = {}

        with open(self.context.json_filepath, 'w') as g:
            json.dump(pld, g, indent=2)

        # Parse to New Json
        with open(self.context.json_filepath, 'r') as f:
            js = json.load(f)
            for nn, node in js.items():
                if node['action'] == 'sobjectDigest':
                    node['action'] = "sfdcDigest"

                if node['action'] == 'computeExpression':
                    node['parameters']['source'] = node['sources'][0]
                    del node['sources']

                if node['action'] in ['update', "augment"]:
                    node['parameters']['left'] = node['sources'][0]
                    node['parameters']['right'] = node['sources'][1]
                    if 'updateColumns' in node['parameters']:
                        node['parameters']['update_columns'] = node['parameters']['updateColumns']
                        del node['parameters']['updateColumns']

                    del node['sources']

                    if 'leftKey' in node['parameters'].keys():
                        node['parameters']['left_key'] = node['parameters']['leftKey']
                        del node['parameters']['leftKey']
                    if 'rightKey' in node['parameters'].keys():
                        node['parameters']['right_key'] = node['parameters']['rightKey']
                        del node['parameters']['rightKey']
                    if 'rightSelect' in node['parameters'].keys():
                        node['parameters']['right_select'] = node['parameters']['rightSelect']
                        del node['parameters']['rightSelect']

                if node['action'] == 'register':
                    node['action'] = "sfdcRegister"
                    node['parameters']['source'] = node['sources'][0]
                    node['parameters']['alias'] = node['parameters']['name']
                    node['parameters']['name'] = node['parameters']['label']
                    del node['sources']
                    del node['parameters']['label']

                if node['action'] in ["sliceDataset", "computeRelative", "filter"] and "sources" in node.keys():
                    node['parameters']['source'] = node['sources'][0]
                    del node['sources']

                if node['action'] == "dataset":
                    node['action'] = 'edgemart'

                if 'sources' in node.keys() and len(node['sources']) == 1:
                    node['source'] = node['sources'][0]
                    del node['sources']

        with open(self.context.json_filepath, 'w') as fixed:
            json.dump(js, fixed, indent=2)


class WdfManager(Interactor):
    _MODE = {
        "wdfToJson": WdfToJsonInteractor,
        "jsonToWdf": JsonToWdfInteractor
    }

    def run(self):
        today = current_datetime()
        user = self.context.user
        mode = self.context.mode
        klass = self._MODE[mode]
        wdf_filepath = f"ant/{user.username}/retrieve/dataflow/wave"
        json_filepath = f"libs/tcrm_automation/{today}/original_dataflows"

        if mode == 'wdfToJson':
            Path(json_filepath).mkdir(parents=True, exist_ok=True)

            files = [f for f in os.listdir(wdf_filepath)
                     if os.path.isfile(os.path.join(wdf_filepath, f)) and f[-4:] == ".wdf"]

        else:
            files = [f for f in os.listdir(json_filepath)
                     if os.path.isfile(os.path.join(json_filepath, f)) and f[-5:] == ".json"]

        for file in files:
            print(f"processing {file}...")
            klass.call(json_filepath=os.path.join(json_filepath, file.replace('.wdf', '.json')),
                       wdf_filepath=os.path.join(wdf_filepath, file.replace('.json', '.wdf')))
