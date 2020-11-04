from resources.lib.modules import control
from resources.lib.modules.globoplay.auth import auth as authenticator


def _authenticate():
    username = control.setting('globoplay_username')
    password = control.setting('globoplay_password')

    if not username or not password or username == '' or password == '':
        return {}, {}

    credentials, user_data = authenticator().authenticate(username, password)

    return credentials, user_data


def get_credentials():

    credentials, user_data = _authenticate()

    return credentials


def get_token():
    return get_credentials().get('GLBID')


def get_user_id():
    credentials, user_data = _authenticate()

    return user_data.get('globoId', '')


def get_token_and_user_id():
    credentials, user_data = _authenticate()

    return credentials.get('GLBID'), user_data.get('globoId', '')
