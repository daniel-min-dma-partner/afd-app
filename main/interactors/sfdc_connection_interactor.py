from urllib import parse

import requests

from libs.interactor.interactor import Interactor
from main.models import SalesforceEnvironment as Env

SFDC_APIUSER_REQUEST_HEADER = 'sfdc-apiuser-request-header'
SFDC_APIUSER_REQUEST_INSTANCE = 'sfdc-apiuser-request-instance'
SFDC_APIUSER_ACCESS_TOKEN = 'sfdc-apiuser-access-token'


def clear_session(session):
    for key in [SFDC_APIUSER_REQUEST_HEADER, SFDC_APIUSER_REQUEST_INSTANCE, SFDC_APIUSER_ACCESS_TOKEN]:
        if key in session.keys():
            del session[key]


class SFDCAuthenticateUserInteractor(Interactor):
    def run(self):
        env_model: Env = self.context.model
        mode = self.context.mode
        exception = None

        try:
            # Attempt to logout an already-logged-out env
            if env_model.is_logged_out() and mode == 'logout':
                raise Exception(f"<code>{env_model.name}</code> is already logged out.")

            resource = '/services/oauth2/authorize' if mode == 'login' else '/services/oauth2/revoke'

            url = env_model.environment + resource
            parms = {
                "response_type": "code",
                "client_id": env_model.client_key,
                "redirect_uri": "http://localhost:8000/sfdc/connected-app/oauth2/callback",
                "scope": "wave_api",
                "state": f":{env_model.user_id}.:{env_model.pk}"
            } if mode == 'login' else {
                "token": env_model.oauth_access_token
            }

            # url_parse = parse.urlparse(url)
            # query = url_parse.query
            # url_dict = dict(parse.parse_qsl(query))
            # url_dict.update(parms)
            # url_new_query = parse.urlencode(url_dict)
            # url_parse = url_parse._replace(query=url_new_query)
            # new_url = parse.urlunparse(url_parse)

            http_action = requests.post if mode == 'login' else requests.get
            response = http_action(url, params=parms)

            if mode == 'login' and response.status_code == 200:
                self.context.authorization_response = response
            elif mode == 'logout' and response.status_code == 200:
                env_model.flush_oauth_data()
                self.context.response = None
            else:
                raise ConnectionError(f"Response status: <code>{response.status_code}</code>: {response.text}")
        except Exception as e:
            exception = e
            env_model.flush_oauth_data()
        finally:
            env_model.save()
            self.context.exception = exception


class SFDCGetAccessTokenInteractor(Interactor):
    """
    Checks the status of the connection with SF Connected App.

    """

    def run(self):
        _message = "Access Token Request Process not executed. Contact the administrator."
        response_status_code = 500
        env_obj = self.context.env_object

        try:
            env_obj.set_oauth_flow_stage('ACCESS_TOKEN_REQUEST')
            env_obj.save()
            env_obj.refresh_from_db()

            url = f"{env_obj.environment}/services/oauth2/token?" \
                  f"client_id={env_obj.client_key}&" \
                  f"grant_type=authorization_code&" \
                  f"code={env_obj.oauth_authorization_code}&" \
                  f"redirect_uri=https://localhost:8080/sfdc/connected-app/oauth2/callback&" \
                  f"client_secret={env_obj.client_secret}"
            response = requests.post(url)
            response_status_code = response.status_code

            if response.text:
                response = response.json()

            if isinstance(response, dict) and 'error' in response.keys():
                _message = f"{response['error']}: {response['error_description']}"
            else:
                env_obj.set_oauth_access_token(response['access_token'])
                env_obj.set_oauth_flow_stage('ACCESS_TOKEN_RECEIVE')
                env_obj.instance_url = response['instance_url']
                env_obj.save()
                env_obj.refresh_from_db()

                del self.context.env_object
                self.context.env_object = env_obj

                _message = f"<code>LOGIN</code> performed successfully"
        except Exception as e:
            _message = str(e)

        self.context.message = _message
        self.context.response_status = response_status_code


class SfdcConnectionStatusCheck(Interactor):
    """
    Connects with the SF Connected App.

    """

    def run(self):
        self._set_context(data={
            'message': "There is an error.",
            'error': "Not authenticated yet.",
            'instance_url': ''
        }, status_code=400)

        if SFDC_APIUSER_ACCESS_TOKEN not in self.context.request.session.keys():
            return

        # Gets previous login data from session
        dataflows_url = '/services/data/v51.0/wave/dataflows/'
        header = self.context.request.session[SFDC_APIUSER_REQUEST_HEADER]
        instance_url = self.context.request.session[SFDC_APIUSER_REQUEST_INSTANCE]

        # Constructs full url and make a sample get request
        url = instance_url + dataflows_url
        response = requests.get(url, headers=header)

        # Collects status data
        message = ""
        error = ""
        status_code = response.status_code

        if response.text:
            response = response.json()

        if isinstance(response, list) and 'errorCode' in response[0].keys():
            # clear_session(self.context.request.session)
            error = response[0]['errorCode']
            message = "There is an error."
        elif 'dataflows' in response.keys():
            message = "Yes"

        self._set_context(data={
            'message': message,
            'error': error,
            'instance_url': instance_url
        }, status_code=status_code)

    def _set_context(self, data: dict, status_code):
        self.context.response = data
        self.context.status_code = status_code
