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
                            "text": "*Business Justification?* {{case_business_justification}}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Manager Approval?* {{case_manager_approval}}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Manager Name:* {{case_manager_name}}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Submiter:* {{submitter}}"
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
        print(json.dumps(payload))

    def _construct_payload(self):
        values = self.context.values

        business_justif = values['case-business-justification']
        description = values['case-description']
        manager_approval = values['case-manager-approval']
        manager_name = values['case-manager-name']
        url = values['case-url']
        case_number = values['case-number']
        submitter = values['submitter']
        contact = values['case-contact']

        payload = copy.deepcopy(_SLACK_MESSAGE_PAYLOAD_TEMPLATE)
        print(description)

        payload = json.loads(json.dumps(payload)
                             .replace('{{case_header}}', f"Case #{case_number} - {contact}")
                             .replace('{{case_description}}', f"<{url}|_{description}_>".replace('"', "\\\""))
                             .replace('{{case_url}}', url)
                             .replace('{{case_business_justification}}', self._set_icon(business_justif))
                             .replace('{{case_manager_approval}}', self._set_icon(manager_approval))
                             .replace('{{case_manager_name}}', f"_{manager_name}_ :checked:" if manager_name else "")
                             .replace('{{submitter}}', submitter))

        idx = 0
        for field in payload['attachments'][0]['blocks'][3]['fields']:
            if 'Manager Name' in field['text'] and not manager_name:
                del payload['attachments'][0]['blocks'][3]['fields'][idx]
                break
            idx += 1

        idx = 0
        for field in payload['attachments'][0]['blocks'][3]['fields']:
            if 'Submiter' in field['text'] and not submitter:
                del payload['attachments'][0]['blocks'][3]['fields'][idx]
                break
            idx += 1

        return payload

    @classmethod
    def _set_icon(cls, bool_val: bool):
        _icon_map = {
            True: ":checkmark:",
            False: ":x:"
        }

        return _icon_map[bool_val]
