# -*- coding: UTF-8 -*-

import requests
from resources.lib.modules import control
from . import cache
from threading import Lock
import json

auth_lock = Lock()

SERVICES_LOCKS = {}


class Auth:

    ENDPOINT_URL = 'https://login.globo.com/api/authentication/sdk'
    PROVIDER_ID = None

    def __init__(self, service_id):
        try:
            control.log('Auth: Creating Authenticator for service %s' % service_id)
            self.service_id = service_id
            self._read_credentials()
        except Exception as e:
            control.log('ERROR Loading auth cache: %s' % e)
            control.log('Auth: No cached auth token for service: %s' % service_id)
            self.credentials = {}
            self.user_data = {}

    def get_credentials_key(self):
        return '%s_credentials' % self.service_id

    def get_userdata_key(self):
        return '%s_user_data' % self.service_id

    def _read_credentials(self):
        credentials = control.setting(self.get_credentials_key())
        user_data = control.setting(self.get_userdata_key())
        self.credentials = json.loads(credentials)
        self.user_data = json.loads(user_data)

    def _save_credentials(self):
        control.setSetting(self.get_credentials_key(), json.dumps(self.credentials))
        control.setSetting(self.get_userdata_key(), json.dumps(self.user_data))

    def is_authenticated(self):
        if self.credentials and 'GLBID' in self.credentials.keys():
            if self.credentials.get('success') is False:
                control.log('Authentication has failed before')
                return False
            return True

        return False

    def authenticate(self, username, password):

        if not self.is_authenticated() and (username and password):
            control.log('username/password set. trying to authenticate')
            self.credentials = self._authenticate(username, password)

            success = self.credentials.get('success', False)
            if success is False:
                error_message = self.credentials.get('error_message')
                control.log('authentication error: %s' % error_message)
                control.infoDialog(error_message, icon='ERROR')
                return {}, {}

            is_authenticated, self.user_data = self.check_service(bypass_cache=True)
            if is_authenticated and self.is_authenticated():
                control.log('successfully authenticated')
                self._save_credentials()
            else:
                control.log('wrong username [%s] or password [***]' % username)
                message = '[%s] %s' % (self.__class__.__name__, control.lang(32003))
                control.infoDialog(message, icon='ERROR')
                return {}, {}
        elif self.is_authenticated():
            control.log('[GLOBO AUTH] - already authenticated')
        else:
            control.log('no username set to authenticate', control.LOGWARNING)
            message = 'Missing user credentials'
            control.infoDialog(message, icon='ERROR')
            control.openSettings()
            return {}, {}

        control.log(repr(self.credentials))

        returned_credentials = dict(self.credentials)
        del returned_credentials['success']
        del returned_credentials['error_message']

        return returned_credentials, self.user_data

    def error(self, msg):
        control.infoDialog('[%s] %s' % (self.__class__.__name__, msg), 'ERROR')

    def get_instance_id(self):
        globoplay_instance_id = control.setting('globoplay_instance_id')

        if not globoplay_instance_id:
            checkin_url = 'https://device-provisioning.googleapis.com/checkin'
            post_data = {
                    "checkin": {
                        "iosbuild": {
                            "model": "iPhone10,6",
                            "os_version": "IOS_14.4"
                        },
                        "last_checkin_msec": 0,
                        "type": 2,
                        "user_number": 0
                    },
                    "digest": "",
                    "fragment": 0,
                    "id": 0,
                    "locale": "pt",
                    "security_token": 0,
                    "time_zone": "America/Sao_Paulo",
                    "user_serial_number": 0,
                    "version": 2
                }
            control.log('POST %s' % checkin_url)
            response = requests.post(checkin_url, json=post_data, headers={
                'User-Agent': 'Globoplay/1 CFNetwork/1220.1 Darwin/20.3.0'
            })

            control.log(response.text)

            response.raise_for_status()
            response = response.json()

            security_token = response.get('security_token')
            android_id = response.get('android_id')
            version_info = response.get('version_info')

            installations_url = 'https://firebaseinstallations.googleapis.com/v1/projects/globo-play/installations/'
            post_data = {
                    "appId": "1:846115935537:ios:c91952b14380e445",
                    "authVersion": "FIS_v2",
                    "sdkVersion": "i:7.1.0"
                }
            control.log('POST %s' % installations_url)
            response = requests.post(installations_url, json=post_data, headers={
                'User-Agent': 'Globoplay/1 CFNetwork/1220.1 Darwin/20.3.0',
                'x-goog-api-key': 'AIzaSyDbGxO8Bw7cfT5BYiAQTnReVItGEXlpnhY',
                'x-firebase-client': 'apple-platform/ios apple-sdk/18B79 appstore/true deploy/cocoapods device/iPhone10,6 fire-abt/7.1.0 fire-analytics/7.3.0 fire-fcm/7.1.0 fire-iid/7.1.0 fire-install/7.1.0 fire-ios/7.1.0 fire-perf/7.0.1 fire-rc/7.1.0 firebase-crashlytics/7.1.0 os-version/14.4 swift/true xcode/12B45b',
                'x-firebase-client-log-type': '3',
                'x-ios-bundle-identifier': 'com.globo.hydra'
            })

            control.log(response.text)
            response.raise_for_status()

            response = response.json()

            fid = response.get('fid')
            auth_token = response.get('authToken', {}).get('token')

            register_url = 'https://fcmtoken.googleapis.com/register'
            post_data = {
                'X-osv': '14.4',
                'device': android_id,
                'X-scope': '*',
                'plat': '2',
                'app': 'com.globo.hydra',
                'app_ver': '3.91.0',
                'X-cliv': 'fiid-7.1.0',
                'sender': '846115935537',
                'X-subtype': '846115935537',
                'appid': fid,
                'gmp_app_id': '1:846115935537:ios:c91952b14380e445'
            }

            headers = {
                'x-firebase-client': 'apple-platform/ios apple-sdk/18B79 appstore/true deploy/cocoapods device/iPhone10,6 fire-abt/7.1.0 fire-analytics/7.3.0 fire-fcm/7.1.0 fire-iid/7.1.0 fire-install/7.1.0 fire-ios/7.1.0 fire-perf/7.0.1 fire-rc/7.1.0 firebase-crashlytics/7.1.0 os-version/14.4 swift/true xcode/12B45b',
                'authorization': 'AidLogin %s:%s' % (android_id, security_token),
                'x-firebase-client-log-type': '1',
                'app': 'com.globo.hydra',
                'user-agent': 'Globoplay/1 CFNetwork/1220.1 Darwin/20.3.0',
                'info': version_info,
                'x-goog-firebase-installations-auth': auth_token,
                'content-type': 'application/x-www-form-urlencoded'
            }

            control.log('POST %s' % register_url)
            control.log(headers)
            control.log(post_data)

            response = requests.post(register_url, data=post_data, headers=headers).text

            if not response.startswith('token='):
                raise Exception(response)

            globoplay_instance_id = response.replace('token=', '')

            control.log('NEW INSTANCE_ID: %s' % globoplay_instance_id)

            control.setSetting('globoplay_instance_id', globoplay_instance_id)

        return globoplay_instance_id

    def _authenticate(self, username, password, retry=1):

        instance_id = self.get_instance_id()

        payload = {
            'payload': {
                'email': username,
                'password': password,
                'serviceId': self.service_id
            }
        }
        headers = {'content-type': 'application/json; charset=UTF-8',
                                              'accept': 'application/json, text/javascript',
                                              'Accept-Encoding': 'gzip',
                                              'Authorization': 'IIDToken com.globo.hydra|%s' % instance_id}

        control.log('POST %s' % self.ENDPOINT_URL)
        control.log(headers)

        response = cache.get(requests.post, 1, self.ENDPOINT_URL,
                                 json=payload,
                                 headers=headers, lock_obj=auth_lock, table='globoplay')

        control.log('GLOBOPLAY (%s) AUTHENTICATION RESPONSE: %s' % (self.service_id, response.status_code))
        control.log(response)

        success = response.status_code < 400

        if not success:
            cache.clear_item(requests.post, self.ENDPOINT_URL,
                                 json=payload,
                                 headers=headers, table='globoplay')

        if response.status_code == 500 or response.status_code == 498:
            control.setSetting('globoplay_instance_id', None)
            if retry > 0:
                return self._authenticate(username, password, retry-1)

        try:
            message = (response.json().get('userMessage') or '')
        except:
            message = response.text

        return {'GLBID': response.cookies.get('GLBID'), 'success': success, 'error_message': message}

    def check_service_api(self, service_id):
        token = self.credentials.get('GLBID')

        if not token:
            control.log('check_service_api: NO GLBID TOKEN')
            return False

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
            control.log('check_service: NO GLBID TOKEN')
            return False, {}

        service_str = ''

        if service_id:
            service_str = '?servico_id=' + str(service_id)

        # https://cocoon.globo.com/v2/user/logged?servico_id=4654
        url = 'https://cocoon.globo.com/v2/user/logged' + service_str
        control.log('POST %s' % url)

        lock = self.get_service_lock(token, service_id)
        response = cache.get(requests.post, 168, url, headers={
                                                    'Origin': 'https://globoplay.globo.com',
                                                    'Cookie': 'GLBID=%s' % token
                                                }, force_refresh=bypass_cache, lock_obj=lock, table='globoplay')

        control.log('GLOBOPLAY SERVICE (%s) CHECK RESPONSE: %s' % (service_id, response.status_code))
        control.log(response.text)

        user_data = response.json()
        is_authenticated = user_data.get('status') == 'authorized'

        control.log('is_authenticated (%s): %s' % (service_id, is_authenticated))

        return is_authenticated, user_data

    def logout(self, token):
        # https://login.globo.com/logout?realm=globo.com
        url = 'https://login.globo.com/api/logout'

        requests.delete(url, headers={
                                        'glbid': token,
                                        'user-agent': '	Globoplay/1 CFNetwork/1197 Darwin/20.0.0'
                                    })

        self.credentials = {}
        self.user_data = {}
        self._save_credentials()

    def get_service_lock(self, token, service_id):
        key = '%s|%s' % (token, service_id)
        lock = SERVICES_LOCKS.get(key)
        if not lock:
            lock = Lock()
            SERVICES_LOCKS[key] = lock

        return lock
