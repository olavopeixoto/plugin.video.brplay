# -*- coding: utf-8 -*-

import json
import datetime
import re
import requests
from bs4 import BeautifulSoup
from json import JSONEncoder
import pickle
import resources.lib.modules.control as control
import base64
from .private_data import get_user, get_password, get_device_id
import traceback
import urllib.parse as urlparse
unicode = str

proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}

DEVICE_ID = get_device_id()

DEVICE_BRAND = 'Google'
DEVICE_MODEL = 'Chrome/105.0.0.0'

ACCESS_TOKEN_URL = 'https://apim.oi.net.br/app/oiplay/ummex/v1/oauth/token'

PROFILES_URL = 'https://apim.oi.net.br/app/oiplay/oapi/v1/users/accounts/{account}/list?useragent=web&deviceId={deviceid}'

ENTITLEMENTS_URL = 'https://apim.oi.net.br/app/oiplay/oapi/v1/users/accounts/{account}/entitlements/list?useragent=web'


def get_default_profile(account, deviceid, token):
    response = get_account_details(account, deviceid, token)

    default_profile = response['oiplay_default_profile']

    return default_profile


def get_account_details(account, deviceid, token):
    details = {
        'oiplay_default_profile': control.setting('oiplay_default_profile')
    }

    if details['oiplay_default_profile']:
        control.log('ACCOUNT DETAILS FROM CACHE: ' + json.dumps(details))
        return details

    headers = {
        'Accept': 'application/json',
        'X-Forwarded-For': '189.1.125.97',
        'User-Agent': 'OiPlay-Store/5.1.1 (iPhone; iOS 13.3.1; Scale/3.00)',  # if format == 'm3u8' else 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Authorization': 'Bearer ' + token
    }
    url = PROFILES_URL.format(account=account, deviceid=deviceid)

    control.log('GET %s' % url)
    response_full = requests.get(url, headers=headers, proxies=proxy)

    control.log(response_full.content)

    response = response_full.json() or {}

    if not response.get('upmProfiles'):
        control.log(response_full.status_code)
        control.log(response_full.content)
        return details

    profiles = sorted(response['upmProfiles'], key=lambda k: k['upmProfileType']['id'])

    for profile in profiles:
        if profile['upmProfileStatus']['name'] == 'Active':
            default_profile = profile['id']
            break

    response['oiplay_default_profile'] = default_profile

    control.setSetting('oiplay_default_profile', str(default_profile))

    control.log('ACCOUNT DETAILS FROM URL: ' + json.dumps(response))

    return response


def gettoken(force_new=False):

    user = get_user()
    password = get_password()

    if force_new:
        response = __login(user, password)
    else:
        settings_data = control.setting('oiplay_access_token_response')
        access_token = None
        if settings_data:
            try:
                auth_json = json.loads(settings_data, object_hook=as_python_object)
                access_token = auth_json['access_token']

                if auth_json['date'] + datetime.timedelta(seconds=auth_json['expires_in']) > datetime.datetime.utcnow():
                    control.log('ACCESS TOKEN FROM FILE: ' + auth_json['access_token'])
                    user_info = auth_json.get('userInfo', {}) or {}
                    account = user_info.get('cpfcnpj')
                    return auth_json['access_token'], account
            except:
                control.log(traceback.format_exc(), control.LOGERROR)

        if not access_token:
            response = __login(user, password)
        else:
            success, response = __refresh_token(access_token)

            if not success:
                response = __login(user, password)

    control.log(response)

    response['date'] = datetime.datetime.utcnow()

    control.setSetting('oiplay_access_token_response', json.dumps(response, cls=PythonObjectEncoder))

    user_info = auth_json.get('userInfo', {}) or {}
    account = user_info.get('cpfcnpj')

    return response['access_token'], account


def __refresh_token(access_token):

    control.log('REFRESH TOKEN')

    body = {
        "device_id": DEVICE_ID
    }

    control.log(body)

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Forwarded-For': '177.2.105.143',
        'User-Agent': 'OiPlay-Store/5.9.0 (iPhone; iOS 15.6.1; Scale/3.00)',
        'Authorization': 'Bearer %s' % access_token
    }

    control.log(headers)

    response = requests.post(ACCESS_TOKEN_URL, json=body, headers=headers, proxies=proxy)

    # response.raise_for_status()

    response = response.json()

    if not response or 'access_token' not in response:
        return False, None

    return True, response


def __login(user, password):

    control.log('LOGIN OIPLAY')

    session = requests.session()

    url = 'https://apim.oi.net.br/oauth/oi/authorize?state=csrf_oiplay&client_id=31a0c8f7-aef3-45c2-8812-8f7c6ce87411&response_type=code&scope=openid%20customer_info%20oob%20oiplay&redirect_uri=https://oiplay.tv/login'

    response = session.get(url, proxies=proxy)

    url = re.findall(r'action="([^"]+)"', response.content.decode('utf-8'))[0]

    url = 'https://logintv.oi.com.br' + url

    response = session.post(url, proxies=proxy)

    html = BeautifulSoup(response.content, features="html.parser")

    url_login = html.find('form')['action']

    response = session.post(url_login, data={
        'option': 'credential',
        'urlRedirect': url_login,
        'Ecom_User_ID': user,
        'Ecom_Password': password
    }, proxies=proxy)

    response.raise_for_status()

    url = re.findall(r"window.location.href='([^']+)';", response.content.decode('utf-8'))[0]

    control.log('GET %s' % url)

    response = session.get(url, proxies=proxy)

    response.raise_for_status()

    url_parsed = urlparse.urlparse(response.url)

    qs = urlparse.parse_qs(url_parsed.query)

    code = qs['code'][0]

    post = {
        "brand": DEVICE_BRAND,
        "code": code,
        "device_id": DEVICE_ID,
        "grant_type": "authorization_code",
        "model": DEVICE_MODEL,
        "serial": DEVICE_ID
    }

    token_response = session.post(ACCESS_TOKEN_URL, json=post, proxies=proxy)

    token_response.raise_for_status()

    return json.loads(token_response.content, object_hook=as_python_object)


class PythonObjectEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return JSONEncoder.default(self, obj)
        return {'_python_object': pickle.dumps(obj).decode('cp437')}


def as_python_object(dct):
    if '_python_object' in dct:
        return pickle.loads(dct['_python_object'].encode('cp437'))
    return dct
