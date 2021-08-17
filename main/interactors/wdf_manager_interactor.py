import json
import os
import shutil
from pathlib import Path

from core.settings import BASE_DIR
from libs.interactor.interactor import Interactor
from libs.utils import current_datetime

# In org62, sfdcDigest nodes can have 'name' key inside 'parameters' property.
# In Stage, for the moment, doesn't accept 'name' key inside 'parameters' property.
# The same happens with 'SFDCToken' key in 'parameters'.
forbidden_keys_in_parms = ['name', 'SFDCtoken']


class JsonStructReverterInteractor(Interactor):
    def run(self):
        # Parse to New Json
        with open(self.context.json_filepath, 'r') as f:
            js = json.load(f)
            for nn, node in js.items():
                if node['action'] == 'sfdcDigest':
                    node['action'] = "sobjectDigest"

                    if 'complexFilterConditions' in node['parameters'].keys():
                        node['parameters']['passthroughFilter'] = node['parameters']['complexFilterConditions']
                        del node['parameters']['complexFilterConditions']

                    for fbk in forbidden_keys_in_parms:
                        if fbk in node['parameters']:
                            del node['parameters'][fbk]

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
                        if ok in node['parameters'].keys():
                            node['parameters'][new[old.index(ok)]] = node['parameters'][ok]
                            del node['parameters'][ok]

                    corrects = ["multiField", "pathField"]
                    fields = ["multi_field", "path_field"]
                    for key in fields:
                        if key in node['parameters'].keys():
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

                    if 'folderid' in node['parameters']:
                        node['parameters']['runtime'] = {"folderid": node['parameters']['folderid']}
                        del node['parameters']['folderid']
                    elif 'folder' in node['parameters']:
                        node['parameters']['runtime'] = {"folder": node['parameters']['folder']}
                        del node['parameters']['folder']

                if node['action'] in ["sliceDataset", "computeRelative", "computeExpression", "filter", "dim2mea",
                                      "flatten"]:
                    if "source" in node['parameters'].keys():
                        node['sources'] = [node['parameters']['source']]
                        del node['parameters']['source']

                    if node['action'] in ['computeExpression', 'computeRelative']:
                        for field in node['parameters']['computedFields']:
                            idx = node['parameters']['computedFields'].index(field)

                            if 'precision' in field.keys():
                                del js[nn]['parameters']['computedFields'][idx]['precision']

                            if 'expression' in field.keys():
                                if 'precision' in field['expression'].keys():
                                    raise KeyError("Unexpected parameter <code><strong>precision</code></strong> "
                                                   "for <code>expression</code> parameter of the "
                                                   f"<code>{idx + 1}th</code> computed field of the node "
                                                   f"<code>{nn}</code>.")

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

                    if 'runtime' in node['parameters']:
                        for key in node['parameters']['runtime']:
                            node['parameters'][key] = node['parameters']['runtime'][key]
                        del node['parameters']['runtime']

                    if 'passthroughFilter' in node['parameters'].keys():
                        node['parameters']['complexFilterConditions'] = node['parameters']['passthroughFilter']
                        del node['parameters']['passthroughFilter']

                    for fbk in forbidden_keys_in_parms:
                        if fbk in node['parameters']:
                            del node['parameters'][fbk]

                if node['action'] == "dataset":
                    node['action'] = 'edgemart'
                    node['parameters']['alias'] = node['parameters']['name']
                    del node['parameters']['name']

                if node['action'] == 'append' and 'sources' in node.keys():
                    node['parameters']['sources'] = node['sources']
                    del node['sources']

                if node['action'] == 'flatten' and 'includeSelfId' in node['parameters'].keys():
                    print(node)
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

                if node['action'] in ['update', "augment"] and 'sources' in node.keys():
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

                if node['action'] == 'register' and 'sources' in node.keys():
                    node['action'] = "sfdcRegister"
                    node['parameters']['source'] = node['sources'][0]
                    node['parameters']['alias'] = node['parameters']['name']
                    node['parameters']['name'] = node['parameters']['label']
                    del node['sources']
                    del node['parameters']['label']

                    if 'runtime' in node['parameters'].keys():
                        if 'folderid' in node['parameters']['runtime']:
                            node['parameters']['folderid'] = node['parameters']['runtime']['folderid']
                        elif 'folder' in node['parameters']['runtime']:
                            node['parameters']['folder'] = node['parameters']['runtime']['folder']

                        del node['parameters']['runtime']

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
            a = json.load(f)

        b = json.dumps(a)
        b = b.replace("\\", "\\\\")
        b = b.replace('"', '\\"')
        b = b.replace(': [', ':[')
        b = b.replace(': {', ':{')
        b = b.replace(', [', ',[')
        b = b.replace(', {', ',{')
        b = b.replace(': ]', ':]')
        b = b.replace(': }', ':}')
        b = b.replace(', ]', ',]')
        b = b.replace(', }', ',}')
        b = b.replace(' ==', '==')
        b = b.replace(' >=', '>=')
        b = b.replace(' <=', '<=')
        b = b.replace(' !=', '!=')
        b = b.replace(' :', ':')
        b = b.replace('== ', '==')
        b = b.replace('>= ', '>=')
        b = b.replace('<= ', '<=')
        b = b.replace('!= ', '!=')
        b = b.replace(': ', ':')
        b = b.replace(', ', ',')
        b = b.replace(' > ', '>')
        b = b.replace(' < ', '<')

        c = f'[\"{{\\\"nodes\\\":{b}}}\",null]'
        with open(self.context.wdf_filepath, 'w') as f:
            f.write(c)


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


class JsonMoveInteractor(Interactor):
    def run(self):
        shutil.move(self.context.wdf_filepath, self.context.output_filepath)


class WdfManager(Interactor):
    _MODE = {
        "wdfToJson": WdfToJsonConverterInteractor,
        "jsonToWdf": JsonToWdfConverterInteractor,
        "moveJson": JsonMoveInteractor
    }

    def run(self):
        today = current_datetime()
        env = self.context.env
        user = self.context.user
        mode = self.context.mode
        klass = self._MODE[mode]
        wdf_filepath = f"{BASE_DIR}/ant/{user.username}/retrieve/dataflow/wave"
        json_filepath = f"{BASE_DIR}/libs/tcrm_automation/{today}/original_dataflows"

        if mode in ['moveJson', 'wdfToJson']:
            Path(json_filepath).mkdir(parents=True, exist_ok=True)
            output_filepath = json_filepath
            original_ext = '.wdf'
            output_ext = '.json'
            output_name_prefix = "[FIXED]" if mode == 'wdfToJson' else ''
            env_name = f"[{env.name}] "

            files = [f for f in os.listdir(wdf_filepath)
                     if os.path.isfile(os.path.join(wdf_filepath, f)) and f[-4:] == ".wdf"]

        else:
            output_filepath = None
            original_ext = '.json'
            output_ext = '.wdf'
            output_name_prefix = "[REVERTED]"
            env_name = ""

            files = [f for f in os.listdir(json_filepath)
                     if os.path.isfile(os.path.join(json_filepath, f)) and f[-5:] == ".json"]

        for file in files:
            print(f"\n === processing {file}...")
            klass.call(json_filepath=os.path.join(json_filepath, file.replace('.wdf', '.json')),
                       wdf_filepath=os.path.join(wdf_filepath, file.replace('.json', '.wdf')),
                       output_filepath=os.path.join(output_filepath,
                                                    f"{env_name}{output_name_prefix} {file.replace(original_ext, output_ext)}"))
            print(f" === end {file}")
