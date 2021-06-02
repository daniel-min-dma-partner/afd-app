import copy

from libs.interactor.interactor import Interactor

_SLACK_MESSAGE_PAYLOAD_TEMPLATE = {
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "You have a new request for approval:\n*<{{case_url}}|{{case_title}}>*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Description:*\n{{case_description}}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Business Justification?:*\n{{case_business_justification}}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Manager Approval?:*\n{{case_manager_approval}}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Manager Name:*\n{{case_manager_name}}"
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

        payload = copy.deepcopy(_SLACK_MESSAGE_PAYLOAD_TEMPLATE)

        payload['blocks'][0]['text']['text'] = payload['blocks'][0]['text']['text'].replace('{{case_url}}', url)
        payload['blocks'][0]['text']['text'] = payload['blocks'][0]['text']['text'].replace('{{case_title}}',
                                                                                            f"Case #{case_number}")

        payload['blocks'][1]['fields'] = [
            {
                "type": "mrkdwn",
                "text": field['text']
                    .replace('{{case_description}}', description)
                    .replace('{{case_business_justification}}', str(business_justif))
                    .replace('{{case_manager_approval}}', str(manager_approval))
                    .replace('{{case_manager_name}}', manager_name)
            }
            for field in payload['blocks'][1]['fields']
        ]

        return payload
