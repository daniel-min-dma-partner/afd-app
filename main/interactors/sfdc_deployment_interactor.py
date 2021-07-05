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
            j = json.loads(f.read())
            if 'nodes' in json.loads(j[0]):
                j = json.loads(j[0])['nodes']
            else:
                j = {}

            with open(self.context.json_filepath, 'w') as g:
                json.dump(j, g, indent=2)


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
        json_filepath = f"libs/tcrm_automation/2021-07-05/original_dataflows"

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
