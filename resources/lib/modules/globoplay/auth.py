# -*- coding: UTF-8 -*-

import json
import requests

from resources.lib.modules import control

try:
    import HTMLParser
except:
    import html.parser as HTMLParser

try:
    import cPickle as pickle
except:
    import pickle


class auth:

    ENDPOINT_URL = 'https://login.globo.com/api/authentication'
    PROVIDER_ID = None

    GLOBOPLAY_CREDENTIALS = 'globoplay_credentials'
    GLOBOPLAY_USER_DATA = 'globoplay_user_data'

    def __init__(self):
        try:
            credentials = control.setting(self.GLOBOPLAY_CREDENTIALS)
            user_data = control.setting(self.GLOBOPLAY_USER_DATA)
            self.credentials = pickle.loads(credentials)
            self.user_data = pickle.loads(user_data)
        except:
            self.credentials = {}
            self.user_data = {}

    def _save_credentials(self):
        control.setSetting(self.GLOBOPLAY_CREDENTIALS, pickle.dumps(self.credentials))
        control.setSetting(self.GLOBOPLAY_USER_DATA, pickle.dumps(self.user_data))

    def is_authenticated(self):
        authProvider = False
        for key in self.credentials.keys():
            authProvider = authProvider or key == 'GLBID' and self.credentials[key] is not None
        return authProvider

    def authenticate(self, username, password):

        if not self.is_authenticated() and (username and password):
            control.log('username/password set. trying to authenticate')
            self.credentials = self._authenticate(username, password)
            is_authenticated, self.user_data = self.set_token(self.credentials.get('GLBID'))
            if self.is_authenticated():
                control.log('successfully authenticated')
                self._save_credentials()
            else:
                control.log('wrong username or password')
                message = '[%s] %s' % (self.__class__.__name__, control.lang(32003))
                control.infoDialog(message, icon='ERROR')
                return None
        elif self.is_authenticated():
            control.log('already authenticated')
        else:
            control.log_warning('no username set to authenticate')
            message = 'Missing user credentials'
            control.infoDialog(message, icon='ERROR')
            control.openSettings()
            return None

        control.log(repr(self.credentials))

        return self.credentials, self.user_data

    def error(self, msg):
        control.infoDialog('[%s] %s' % (self.__class__.__name__, msg), 'ERROR')

    def _authenticate(self, username, password):
        payload = {
            'captcha': '',
            'payload': {
                'email': username,
                'password': password,
                'serviceId': 4654
            }
        }
        response = requests.post(self.ENDPOINT_URL,
                                 data=json.dumps(payload),
                                 headers={'content-type': 'application/json; charset=UTF-8',
                                          'accept': 'application/json, text/javascript',
                                          'Accept-Encoding': 'gzip',
                                          'referer': 'https://login.globo.com/login/4654?url=https://globoplay.globo.com/&tam=WIDGET',
                                          'origin': 'https://login.globo.com'},
                                 verify=True)

        return {'GLBID': response.cookies.get('GLBID')}

    def set_token(self, token):
        url = 'https://cocoon.globo.com/v2/user/logged'
        user_data = requests.post(url, headers={
                                                        'Origin': 'https://globoplay.globo.com',
                                                        'Cookie': 'GLBID=%s' % token
                                                    }).json()
        is_authenticated = self.user_data.get('status', '') == 'authorized'

        return is_authenticated, user_data