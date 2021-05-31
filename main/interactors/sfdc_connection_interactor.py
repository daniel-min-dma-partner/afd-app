import requests

from libs.interactor.interactor import Interactor
from libs.tcrm_automation.libs.utils import get_connapp_credential_from_env

SFDC_APIUSER_REQUEST_HEADER = 'sfdc-apiuser-request-header'
SFDC_APIUSER_REQUEST_INSTANCE = 'sfdc-apiuser-request-instance'
SFDC_APIUSER_ACCESS_TOKEN = 'sfdc-apiuser-access-token'


def clear_session(session):
    for key in [SFDC_APIUSER_REQUEST_HEADER, SFDC_APIUSER_REQUEST_INSTANCE, SFDC_APIUSER_ACCESS_TOKEN]:
        if key in session.keys():
            del session[key]


class SfdcConnectWithConnectedApp(Interactor):
    """
    Checks the status of the connection with SF Connected App.

    """

    def run(self):
        _message = ""

        if 'code' in self.context.request.GET:
            env = 'test'
            auth_code = self.context.request.GET.get('code')
            key, secret, _, _ = get_connapp_credential_from_env()

            url = f"https://{env}.salesforce.com/services/oauth2/token?" \
                  f"client_id={key}&" \
                  f"grant_type=authorization_code&" \
                  f"code={str(auth_code)}&" \
                  f"redirect_uri=https://localhost:8080/rest&" \
                  f"client_secret={str(secret)}"
            response = requests.get(url)

            if response.text:
                response = response.json()

            header = {'Authorization': "Bearer " + response["access_token"], 'Content-Type': "application/json"}

            self.context.request.session[SFDC_APIUSER_REQUEST_HEADER] = header
            self.context.request.session[SFDC_APIUSER_REQUEST_INSTANCE] = response['instance_url']
            self.context.request.session[SFDC_APIUSER_ACCESS_TOKEN] = response["access_token"]
            self.context.response = response

            _message = "Authentication Success!!!"
        else:
            _message = "Someting went wrong" + str(self.context.request)

        self.context.message = _message


class SfdcConnectionStatusCheck(Interactor):
    """
    Connects with the SF Connected App.

    """

    def run(self):
        status = "No"

        # if SFDC_APIUSER_ACCESS_TOKEN not in self.context.request.session.keys():
        #     return status

        header = self.context.request.session[SFDC_APIUSER_REQUEST_HEADER]
        instance_url = self.context.request.session[SFDC_APIUSER_REQUEST_INSTANCE]
        dataflows_url = '/services/data/v51.0/wave/dataflows/'

        url = instance_url + dataflows_url
        response = requests.get(url, headers=header)
        response_status = response.status_code

        if response.text:
            response = response.json()

        if isinstance(response, list) and 'errorCode' in response[0].keys():
            clear_session(self.context.request.session)
            status = response[0]['errorCode']
        elif 'dataflows' in response.keys():
            status = "Yes"

        self.context.instance_url = instance_url
        self.context.response = response
        self.context.response_status = response_status
        self.context.status = status
