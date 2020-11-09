# -*- coding: UTF-8 -*-

from resources.lib.modules import control
from resources.lib.modules.globoplay.auth import Auth as Authenticator


class SUBSCRIPTION_TYPE:
    ANONYMOUS = "ANONYMOUS"
    LOGGED_IN = "LOGGED_IN"
    SUBSCRIBER = "SUBSCRIBER"


class CADUN_SERVICES:
    BBB_SUBSCRIBER = 1007  # BBB
    GLOBOPLAY_SUBSCRIBER = 151  # Assinantes
    LOGGED_ONLY = 4654  # Globo Play
    SOAP_OPERA_SUBSCRIBER = 6004  # Íntegras fechadas
    PREMIERE = 6661  # Premiere OTT
    GSAT_CHANNELS = 6807  # Globoplay Mais Canais
    COMBATE = 6698  # Combate OTT
    DISNEY = 6940  # Disney+


def _authenticate():
    username = control.setting('globoplay_username')
    password = control.setting('globoplay_password')

    if not username or not password or username == '' or password == '':
        return {}, {}

    auth = Authenticator()

    credentials, user_data = auth.authenticate(username, password)

    return credentials, user_data, auth


def get_credentials():

    credentials, user_data, auth = _authenticate()

    return credentials


def get_token():
    return get_credentials().get('GLBID')


def get_user_id():
    credentials, user_data, auth = _authenticate()

    return user_data.get('globoId', '')


def get_token_and_user_id():
    credentials, user_data, auth = _authenticate()

    return credentials.get('GLBID'), user_data.get('globoId', '')


def get_service_data(service_id=None):
    allowed, userdata = Authenticator().check_service(service_id)

    return allowed, userdata


def is_service_allowed(service_id=None):
    allowed, userdata = get_service_data(service_id)
    return allowed


def is_subscribed():
    return is_service_allowed(CADUN_SERVICES.GLOBOPLAY_SUBSCRIBER)


def is_logged_in():
    username = control.setting('globoplay_username')
    password = control.setting('globoplay_password')

    return Authenticator().is_authenticated(username, password)


def get_subscription_type():
    if not is_logged_in():
        return SUBSCRIPTION_TYPE.ANONYMOUS

    if is_subscribed():
        return SUBSCRIPTION_TYPE.SUBSCRIBER

    return SUBSCRIPTION_TYPE.LOGGED_IN


def is_available_for(sub):
    return get_subscription_type() >= sub
