# -*- coding: UTF-8 -*-

import requests
from resources.lib.modules import control
from . import cache
import hashlib
from threading import Lock

try:
    import HTMLParser
except:
    import html.parser as HTMLParser

try:
    import cPickle as pickle
except:
    import pickle

auth_lock = Lock()

SERVICES_LOCKS = {}


class Auth:

    ENDPOINT_URL = 'https://login.globo.com/api/authentication'
    PROVIDER_ID = None

    def __init__(self, tenant='globoplay'):
        try:
            self.tenant = tenant
            credentials = control.setting(self.get_credentials_key())
            user_data = control.setting(self.get_userdata_key())
            self.credentials = pickle.loads(credentials)
            self.user_data = pickle.loads(user_data)
        except:
            self.credentials = {}
            self.user_data = {}

    def get_credentials_key(self):
        return '%s_credentials' % self.tenant

    def get_userdata_key(self):
        return '%s_user_data' % self.tenant

    def _save_credentials(self):
        control.setSetting(self.get_credentials_key(), pickle.dumps(self.credentials))
        control.setSetting(self.get_userdata_key(), pickle.dumps(self.user_data))

    def is_authenticated(self, username, password):
        if self.credentials and 'GLBID' in self.credentials.keys() and 'brplay_id' in self.credentials.keys():
            brplay_id = self.hash_user_credentials(username, password)
            if brplay_id == self.credentials.get('brplay_id'):

                if self.credentials.get('success') is False:
                    control.log('Authentication has failed before')
                    return True

                is_authorized, userdata = self.check_service()
                return is_authorized

        return False

    def authenticate(self, username, password):

        if not self.is_authenticated(username, password) and (username and password):
            control.log('username/password set. trying to authenticate')
            self.credentials = self._authenticate(username, password)

            success = self.credentials.get('success')
            if success is False:
                error_message = self.credentials.get('error_message')
                control.log('authentication error: %s' % error_message)
                control.infoDialog(error_message, icon='ERROR')
                return {}, {}

            is_authenticated, self.user_data = self.check_service(bypass_cache=True)
            if is_authenticated and self.is_authenticated(username, password):
                control.log('successfully authenticated')
                self._save_credentials()
            else:
                control.log('wrong username or password')
                message = '[%s] %s' % (self.__class__.__name__, control.lang(32003))
                control.infoDialog(message, icon='ERROR')
                return {}, {}
        elif self.is_authenticated(username, password):
            control.log('[GLOBO AUTH] - already authenticated')
        else:
            control.log('no username set to authenticate', control.LOGWARNING)
            message = 'Missing user credentials'
            control.infoDialog(message, icon='ERROR')
            control.openSettings()
            return {}, {}

        control.log(repr(self.credentials))

        returned_credentials = dict(self.credentials)
        del returned_credentials['brplay_id']
        del returned_credentials['success']
        del returned_credentials['error_message']

        return returned_credentials, self.user_data

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
        with auth_lock:
            response = cache.get(requests.post, 1, self.ENDPOINT_URL,
                                     json=payload,
                                     headers={'content-type': 'application/json; charset=UTF-8',
                                              'accept': 'application/json, text/javascript',
                                              'Accept-Encoding': 'gzip',
                                              'referer': 'https://login.globo.com/login/4654?url=https://globoplay.globo.com/&tam=WIDGET',
                                              'origin': 'https://login.globo.com'}, table='globoplay')

        control.log('GLOBOPLAY AUTHENTICATION RESPONSE: %s' % response.status_code)
        control.log(response.content)

        success = response.status_code < 400
        try:
            message = (response.json().get('userMessage') or '').encode('utf-8')
        except:
            message = response.content

        brplay_id = self.hash_user_credentials(username, password)
        return {'GLBID': response.cookies.get('GLBID'), 'brplay_id': brplay_id, 'success': success, 'error_message': message}

    def check_service_api(self, service_id):
        token = self.credentials.get('GLBID')

        url = 'https://login.globo.com/api/authorization/' + service_id
        control.log('HEAD %s' % url)
        response = requests.head(url, headers={
                                                    'glbid': token,
                                                    'user-agent': 'Globoplay/1 CFNetwork/1197 Darwin/20.0.0'
                                                })

        is_authorized = response.status_code == 200

        control.log('is_authorized service %s: %s' % (service_id, is_authorized))

        return is_authorized

    def check_service(self, service_id=None, bypass_cache=False):
        token = self.credentials.get('GLBID')

        if not token:
            return False, {}

        service_str = ''

        if service_id:
            service_str = '?servico_id=' + str(service_id)

        # https://cocoon.globo.com/v2/user/logged?servico_id=4654
        url = 'https://cocoon.globo.com/v2/user/logged' + service_str
        control.log('POST %s' % url)

        control.log('Getting lock for service %s' % service_id)
        lock = self.get_service_lock(token, service_id)
        control.log('About to lock code...')
        with lock:
            control.log('Requesting locked:')
            response = cache.get(requests.post, 168, url, headers={
                                                        'Origin': 'https://globoplay.globo.com',
                                                        'Cookie': 'GLBID=%s' % token
                                                    }, force_refresh=bypass_cache, table='globoplay')

        control.log('Lock released for service %s' % service_id)
        control.log('GLOBOPLAY SERVICE (%s | %s) CHECK RESPONSE: %s' % (self.tenant, service_id, response.status_code))
        control.log(response.content)

        user_data = response.json()
        is_authenticated = user_data.get('status') == 'authorized'

        control.log('is_authenticated (%s): %s' % (self.tenant, is_authenticated))

        return is_authenticated, user_data

    def hash_user_credentials(self, username, password):
        return hashlib.sha256('%s|%s' % (username.encode('utf-8'), password.encode('utf-8'))).hexdigest()

    def logout(self, token):
        # https://login.globo.com/logout?realm=globo.com
        url = 'https://login.globo.com/api/logout'

        requests.delete(url, headers={
                                        'glbid': token,
                                        'user-agent': '	Globoplay/1 CFNetwork/1197 Darwin/20.0.0'
                                    })

    def get_service_lock(self, token, service_id):
        key = '%s|%s' % (token, service_id)
        lock = SERVICES_LOCKS.get(key)
        if not lock:
            lock = Lock()
            SERVICES_LOCKS[key] = lock

        return lock
