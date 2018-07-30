from resources.lib.modules import control
from resources.lib.modules.globoplay.auth import auth as authenticator


def get_credentials():
    if control.setting('use_globoplay_credentials_for_globosat') == 'true':
        username = control.setting('globoplay_username')
        password = control.setting('globoplay_password')
    else:
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

    if not username or not password or username == '' or password == '':
        return None

    credentials = authenticator().authenticate(username, password)

    return credentials
