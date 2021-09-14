import copy

from libs.interactor.interactor import Interactor
from main.forms import SlackMsgPusherForm as Slack


class SlackTarListInteractor(Interactor):
    def run(self):
        bad_payload = {
            "results": [
                {
                    "id": "",
                    "text": "Select one",
                },
            ],
        }
        error = None

        try:
            targets = copy.deepcopy(Slack.slack_webhook_links())

            if len(targets):
                payload = copy.deepcopy(bad_payload)
                payload["results"] = [{"id": key, "text": targets[key]['name']} for key in targets.keys()]
                status = 200
            else:
                raise KeyError("Slack target list not found in system parameter")
        except Exception as e:
            error = e
            payload = bad_payload
            status = 409

        self.context.exception = error
        self.context.status = status
        self.context.payload = payload
