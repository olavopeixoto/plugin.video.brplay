# -*- coding: UTF-8 -*-

from resources.lib.modules import control
from resources.lib.modules.globoplay.auth import Auth as Authenticator


class TENANTS:
    GLOBO_PLAY_BETA = "globo-play-beta"
    GLOBO_PLAY = "globo-play"
    GLOBO_PLAY_US = "globo-play-us"
    GLOBO_PLAY_PT = "globo-play-pt"
    GLOBO_PLAY_EU = "globo-play-eu"


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
    TELECINE = 7033  # Telecine
    TELECINE_GLOBOPLAY = 7037  # Telecine e Globoplay
    TELECINE_GLOBOPLAY_CHANNELS = 7036  # Telecine e Globoplay Mais Canais
    STARZ = 7052  # STARZPLAY
    STARZ_GLOBOPLAY = 7053  # STARZPLAY e Globoplay
    STARZ_GLOBOPLAY_CHANNELS = 7054  # STARZPLAY e Globoplay Mais Canais
    STARZ_TELECINE = 7055  # STARZPLAY e Telecine
    STARZ_TELECINE_GLOBOPLAY = 7057  # STARZPLAY + Telecine e Globoplay
    STARZ_TELECINE_GLOBOPLAY_CHANNELS = 7056  # STARZPLAY + Telecine e Globoplay Mais Canais"
    GLOBOPLAY_INTERNATIONAL = 6828  # Globoplay Internacional
    DISCOVERY_PLUS = 7022  # Discovery+


auth = Authenticator(CADUN_SERVICES.LOGGED_ONLY)


def get_service_name(service_id):
    if str(service_id) == str(CADUN_SERVICES.GSAT_CHANNELS):
        return 'Globoplay +Canais'
    if str(service_id) == str(CADUN_SERVICES.COMBATE):
        return 'Combate'
    if str(service_id) == str(CADUN_SERVICES.DISNEY):
        return 'Disney+'
    if str(service_id) == str(CADUN_SERVICES.BBB_SUBSCRIBER):
        return 'Big Brother Brasil'
    if str(service_id) == str(CADUN_SERVICES.TELECINE):
        return 'Telecine'
    if str(service_id) == str(CADUN_SERVICES.PREMIERE):
        return 'Premiere'
    if str(service_id) == str(CADUN_SERVICES.GLOBOPLAY_INTERNATIONAL):
        return 'Globoplay Internacional'
    if str(service_id) == str(CADUN_SERVICES.DISCOVERY_PLUS):
        return 'Discovery+'
    if str(service_id) == str(CADUN_SERVICES.STARZ):
        return 'STARZPLAY'

    return 'Globoplay'


def _authenticate():
    username = control.setting('globoplay_username')
    password = control.setting('globoplay_password')

    if not username or not password or username == '' or password == '':
        return {}, {}

    credentials, user_data = auth.authenticate(username, password)

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


def get_service_data(service_id=None):
    allowed, userdata = auth.check_service(service_id)

    return allowed, userdata


def is_service_allowed(service_id=None):
    allowed, userdata = get_service_data(service_id)
    return allowed


def is_subscribed():
    return is_service_allowed(CADUN_SERVICES.GLOBOPLAY_SUBSCRIBER)


def is_logged_in():
    return auth.is_authenticated()


def get_subscription_type():
    if not is_logged_in():
        return SUBSCRIPTION_TYPE.ANONYMOUS

    if is_subscribed():
        return SUBSCRIPTION_TYPE.SUBSCRIBER

    return SUBSCRIPTION_TYPE.LOGGED_IN


def is_available_for(sub):
    return get_subscription_type() >= sub
