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

    def __init__(self):
        try:
            credentials = control.setting(self.GLOBOPLAY_CREDENTIALS)
            self.credentials = pickle.loads(credentials)
        except:
            self.credentials = {}

    def _save_credentials(self):
        control.setSetting(self.GLOBOPLAY_CREDENTIALS, pickle.dumps(self.credentials))

    def is_authenticated(self):
        authProvider = False
        for key in self.credentials.keys():
            authProvider = authProvider or key == 'GLBID' and self.credentials[key] is not None
        return authProvider

    def authenticate(self, username, password):

        if not self.is_authenticated() and (username and password):
            control.log('username/password set. trying to authenticate')
            self.credentials = self._authenticate(username, password)
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

        return self.credentials

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