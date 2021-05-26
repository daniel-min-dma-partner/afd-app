from libs.interactor.interactor import Interactor


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
            j = json.loads(j[0])['nodes']
            with open(self.context.json_filepath, 'a') as g:
                json.dump(j, g, indent=2)
