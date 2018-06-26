from resources.lib.modules import control
from resources.lib.modules.sexyhotplay.auth import auth as authenticator


def get_credentials():
    username = control.setting('globoplay_username')
    password = control.setting('globoplay_password')

    if not username or not password or username == '' or password == '':
        return None

    credentials = authenticator().authenticate(username, password)

    return credentials


def get_token():
    return get_credentials()


def get_session_cookie():
    return {authenticator.GLOBOSATPLAY_TOKEN_ID: get_credentials()}


def clear_credentials():
    authenticator.clear_credentials()