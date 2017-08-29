from resources.lib.modules import control
import auth


def get_globosat_token():
    provider = control.setting('globosat_provider').lower().replace(' ', '_')
    username = control.setting('globosat_username')
    password = control.setting('globosat_password')

    if not username or not password or username == '' or password == '':
        return None

    authenticator = getattr(auth, provider)()
    token, sessionKey = authenticator.get_token(username, password)

    return token