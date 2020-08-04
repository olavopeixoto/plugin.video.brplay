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


def get_globosat_token():
    return get_credentials()['GLBID']


def get_globosat_cookie(provider_id):
    credentials = get_credentials()
    credentials = credentials['GLBID']
    return {'WMPTOKEN_%s' % provider_id: credentials, 'GLOBO_ID': credentials} if provider_id else {'GLBID': credentials}