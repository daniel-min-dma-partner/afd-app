import copy
import json

from libs.interactor.interactor import Interactor

_SLACK_MESSAGE_PAYLOAD_TEMPLATE = {
    "attachments": [
        {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "{{case_header}}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "{{case_description}}"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Link",
                            "emoji": True
                        },
                        "value": "case_url",
                        "url": "{{case_url}}",
                        "action_id": "button-action"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Business Justification?*\n{{case_business_justification}}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Manager Approval?*\n{{case_manager_approval}}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Manager Name:*\n{{case_manager_name}}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Submiter:*\n{{submitter}}"
                        }
                    ]
                }
            ]
        }
    ]
}


class SlackMessagePushInteractor(Interactor):
    def run(self):
        payload = self._construct_payload()

        self.context.payload = payload

    def _construct_payload(self):
        values = self.context.values

        business_justif = values['case-business-justification']
        description = values['case-description']
        manager_approval = values['case-manager-approval']
        manager_name = values['case-manager-name']
        url = values['case-url']
        case_number = values['case-number']
        submitter = values['submitter']

        payload = copy.deepcopy(_SLACK_MESSAGE_PAYLOAD_TEMPLATE)

        payload = json.loads(json.dumps(payload)
                             .replace('{{case_header}}', f"Case #{case_number}")
                             .replace('{{case_description}}', f"_{description}_")
                             .replace('{{case_url}}', url)
                             .replace('{{case_business_justification}}', self._set_icon(business_justif))
                             .replace('{{case_manager_approval}}', self._set_icon(manager_approval))
                             .replace('{{case_manager_name}}', manager_name if manager_name else ":warning:")
                             .replace('{{submitter}}', submitter))

        if not submitter:
            del payload['attachments'][0]['blocks'][3]['fields'][3]

        return payload

    @classmethod
    def _set_icon(cls, bool_val: bool):
        _icon_map = {
            True: ":check:",
            False: ":x:"
        }

        return _icon_map[bool_val]
