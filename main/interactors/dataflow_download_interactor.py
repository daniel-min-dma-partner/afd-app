import requests

from libs.interactor.interactor import Interactor
from libs.tcrm_automation.libs.workbench_api_libs import DATAFLOWS_URL
from main.models import SalesforceEnvironment as Env


class DataflowDownloadInteractor(Interactor):
    """
    Download dataflows from Salesforce instance.

    """

    def run(self):
        error = None
        _payload = {
            "results": [
                {
                    "id": "",
                    "text": "Select one",
                },
            ],
        }

        try:
            env: Env = self.context.model
            search = self.context.search
            get_metadata = self.context.get_metadata
            dataflow_id = self.context.dataflow_id

            instance_url = env.instance_url
            uri = DATAFLOWS_URL[env.get_environment_name()]
            url = instance_url + uri

            response = requests.get(url=url, headers=env.get_header())
            status = response.status_code

            if status == 200:
                response = response.json()
                payload = {"results": [
                    {"id": dataflow['id'], "text": dataflow['name']} for dataflow in response['dataflows']
                ]}

                if not get_metadata:
                    if search:
                        payload = {"results": [
                            {"id": dataflow['id'], "text": dataflow['text']} for dataflow in payload['results']
                            if search.strip().lower() in dataflow['text'].strip().lower()
                        ]}
                else:
                    payload = [dataflow for dataflow in response['dataflows'] if dataflow['id'] == dataflow_id]

                    if len(payload):
                        payload = payload[0]
            else:
                error = response.text
                payload = _payload

        except Exception as e:
            status = 501
            error = str(e)
            payload = _payload

        self.context.payload = payload
        self.context.status_code = status
        self.context.error = error

        del self.context.model