from resources.lib.modules import control
from resources.lib.modules.globoplay.auth import auth as Authenticator

GLOBOSAT_CREDENTIALS = 'globosat_credentials'


def get_credentials():
    authenticator = Authenticator()

    if control.setting('use_globoplay_credentials_for_globosat') == 'true':
        username = control.setting('globoplay_username')
        password = control.setting('globoplay_password')
    else:
        authenticator.GLOBOPLAY_CREDENTIALS = GLOBOSAT_CREDENTIALS
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

    if not username or not password or username == '' or password == '':
        return None

    credentials, user_id = authenticator.authenticate(username, password)

    return credentials


def get_globosat_token():
    return get_credentials().get('GLBID')


def get_globosat_cookie(provider_id):
    credentials = get_credentials()
    credentials = credentials.get('GLBID')
    return {'WMPTOKEN_%s' % provider_id: credentials, 'GLOBO_ID': credentials} if provider_id else {'GLBID': credentials}
