from resources.lib.modules import control
from resources.lib.modules.globoplay.auth import Auth as Authenticator
from resources.lib.modules.globoplay.auth_helper import SUBSCRIPTION_TYPE, CADUN_SERVICES


def get_user_credentials():
    if control.setting('use_globoplay_credentials_for_globosat') == 'true':
        username = control.setting('globoplay_username')
        password = control.setting('globoplay_password')
    else:
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

    return username, password


def get_authenticator():
    if control.setting('use_globoplay_credentials_for_globosat') != 'true':
        return Authenticator('globosat')

    return Authenticator()


def get_credentials_from_authenticator(auth):
    username, password = get_user_credentials()

    if not username or not password or username == '' or password == '':
        return None

    credentials, user_id = auth.authenticate(username, password)

    return credentials


def get_credentials():
    auth = get_authenticator()
    return get_credentials_from_authenticator(auth)


def get_globosat_token():
    return get_credentials().get('GLBID')


def get_globosat_cookie(provider_id):
    credentials = get_credentials()
    credentials = credentials.get('GLBID')
    return {'WMPTOKEN_%s' % provider_id: credentials, 'GLOBO_ID': credentials} if provider_id else {'GLBID': credentials}


def get_service_data(service_id=None):
    auth = get_authenticator()
    allowed, userdata = auth.check_service(service_id)

    return allowed, userdata


def is_service_allowed(service_id=None):
    allowed, userdata = get_service_data(service_id)
    return allowed


def is_subscribed():
    return is_service_allowed(CADUN_SERVICES.GLOBOPLAY_SUBSCRIBER)


def is_logged_in():
    username, password = get_user_credentials()

    return get_authenticator().is_authenticated(username, password)


def get_subscription_type():
    if not is_logged_in():
        return SUBSCRIPTION_TYPE.ANONYMOUS

    if is_subscribed():
        return SUBSCRIPTION_TYPE.SUBSCRIBER

    return SUBSCRIPTION_TYPE.LOGGED_IN


def is_available_for(sub):
    return get_subscription_type() >= sub
