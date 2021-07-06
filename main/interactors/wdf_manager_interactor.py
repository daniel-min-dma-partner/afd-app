import json
import os
from pathlib import Path

from libs.interactor.interactor import Interactor
from libs.utils import current_datetime


class JsonStructReverterInteractor(Interactor):
    def run(self):
        # Parse to New Json
        with open(self.context.json_filepath, 'r') as f:
            js = json.load(f)
            for nn, node in js.items():
                if node['action'] == 'sfdcDigest':
                    node['action'] = "sobjectDigest"

                if node['action'] == "edgemart":
                    node['action'] = 'dataset'
                    node['parameters']['name'] = node['parameters']['alias']
                    del node['parameters']['alias']

                if node['action'] == 'append':
                    node['sources'] = node['parameters']['sources']
                    del node['parameters']['sources']

                if node['action'] == 'flatten':
                    new = ['includeSelfId', 'parentField', 'selfField']
                    old = ['include_self_id', 'parent_field', 'self_field']
                    for ok in old:
                        node['parameters'][new[old.index(ok)]] = node['parameters'][ok]
                        del node['parameters'][ok]

                    corrects = ["multiField", "pathField"]
                    fields = ["multi_field", "path_field"]
                    for key in fields:
                        node['parameters'][corrects[int(fields.index(key))]] = {"name": node['parameters'][key]}
                        del node['parameters'][key]

                if node['action'] in ['update', "augment"]:
                    node['sources'] = [node['parameters']['left'], node['parameters']['right']]
                    del node['parameters']['left']
                    del node['parameters']['right']

                    if 'update_columns' in node['parameters']:
                        node['parameters']['updateColumns'] = node['parameters']['update_columns']
                        del node['parameters']['update_columns']

                    if 'left_key' in node['parameters'].keys():
                        node['parameters']['leftKey'] = node['parameters']['left_key']
                        del node['parameters']['left_key']
                    if 'right_key' in node['parameters'].keys():
                        node['parameters']['rightKey'] = node['parameters']['right_key']
                        del node['parameters']['right_key']
                    if 'right_select' in node['parameters'].keys():
                        node['parameters']['rightSelect'] = node['parameters']['right_select']
                        del node['parameters']['right_select']

                if node['action'] == 'sfdcRegister':
                    node['action'] = "register"
                    node['sources'] = [node['parameters']['source']]
                    node['parameters']['name'] = node['parameters']['alias']
                    node['parameters']['label'] = node['parameters']['name']
                    del node['parameters']['source']
                    del node['parameters']['alias']

                if node['action'] in ["sliceDataset", "computeRelative", "computeExpression", "filter", "dim2mea",
                                      "flatten"]:
                    if "source" in node['parameters'].keys():
                        node['sources'] = [node['parameters']['source']]
                        del node['parameters']['source']

        with open(self.context.output_filepath, 'w') as fixed:
            json.dump(js, fixed, indent=2)


class JsonStructFixerInteractor(Interactor):
    def run(self):
        # Parse to New Json
        with open(self.context.json_filepath, 'r') as f:
            js = json.load(f)
            for nn, node in js.items():
                if node['action'] == 'sobjectDigest':
                    node['action'] = "sfdcDigest"

                if node['action'] == "dataset":
                    node['action'] = 'edgemart'
                    node['parameters']['alias'] = node['parameters']['name']
                    del node['parameters']['name']

                if node['action'] == 'append' and 'sources' in node.keys():
                    node['parameters']['sources'] = node['sources']
                    del node['sources']

                if node['action'] == 'flatten':
                    new = ['include_self_id', 'parent_field', 'self_field']
                    old = ['includeSelfId', 'parentField', 'selfField']
                    for ok in old:
                        node['parameters'][new[old.index(ok)]] = node['parameters'][ok]
                        del node['parameters'][ok]

                    fields = ["multiField", "pathField"]
                    corrects = ["multi_field", "path_field"]
                    for key in fields:
                        node['parameters'][corrects[int(fields.index(key))]] = node['parameters'][key]['name']
                        del node['parameters'][key]

                if node['action'] in ['update', "augment"]:
                    node['parameters']['left'] = node['sources'][0]
                    node['parameters']['right'] = node['sources'][1]
                    del node['sources']

                    if 'updateColumns' in node['parameters']:
                        node['parameters']['update_columns'] = node['parameters']['updateColumns']
                        del node['parameters']['updateColumns']

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

                if node['action'] in ["sliceDataset", "computeRelative", "computeExpression", "filter", "dim2mea",
                                      "flatten"]:
                    if "sources" in node.keys():
                        node['parameters']['source'] = node['sources'][0]
                        del node['sources']
                    if "source" in node.keys():
                        node['parameters']['source'] = node['source'][0]
                        del node['source']

        with open(self.context.output_filepath, 'w') as fixed:
            json.dump(js, fixed, indent=2)


class JsonToWdfConverterInteractor(Interactor):
    def run(self):
        import json

        _ = JsonStructReverterInteractor.call(json_filepath=self.context.json_filepath,
                                              output_filepath=self.context.output_filepath)

        with open(self.context.output_filepath, 'r') as f:
            j = json.load(f)
            j = [str({'nodes': j}), None]
            j[0] = j[0].replace("\"", '\\\"').replace("'", '\"').replace(', ', ',').replace(': ', ':')

            with open(self.context.wdf_filepath, 'w') as g:
                g.write(f"{str(json.dumps(j))}")


class WdfToJsonConverterInteractor(Interactor):
    def run(self):
        import json

        with open(self.context.wdf_filepath, 'r') as f:
            j = json.loads(f.read())[0]

        k = json.loads(j)
        if 'nodes' in k:
            pld = k['nodes']
        else:
            pld = {}

        with open(self.context.json_filepath, 'w') as g:
            json.dump(pld, g, indent=2)

        _ = JsonStructFixerInteractor.call(json_filepath=self.context.json_filepath,
                                           output_filepath=self.context.output_filepath)


class WdfManager(Interactor):
    _MODE = {
        "wdfToJson": WdfToJsonConverterInteractor,
        "jsonToWdf": JsonToWdfConverterInteractor
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
            output_filepath = json_filepath
            original_ext = '.wdf'
            output_ext = '.json'
            output_name_prefix = "[FIXED]"

            files = [f for f in os.listdir(wdf_filepath)
                     if os.path.isfile(os.path.join(wdf_filepath, f)) and f[-4:] == ".wdf"]

        else:
            output_filepath = None
            original_ext = '.json'
            output_ext = '.wdf'
            output_name_prefix = "[REVERTED]"

            files = [f for f in os.listdir(json_filepath)
                     if os.path.isfile(os.path.join(json_filepath, f)) and f[-5:] == ".json"]

        for file in files:
            print(f"processing {file}...")
            klass.call(json_filepath=os.path.join(json_filepath, file.replace('.wdf', '.json')),
                       wdf_filepath=os.path.join(wdf_filepath, file.replace('.json', '.wdf')),
                       output_filepath=os.path.join(output_filepath,
                                                    f"{output_name_prefix} {file.replace(original_ext, output_ext)}"))
