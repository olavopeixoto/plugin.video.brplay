from resources.lib.modules import control
from resources.lib.modules.globoplay.auth import auth as authenticator


def get_credentials():
    username = control.setting('globoplay_username')
    password = control.setting('globoplay_password')

    if not username or not password or username == '' or password == '':
        return None

    credentials = authenticator().authenticate(username, password)

    return credentials
