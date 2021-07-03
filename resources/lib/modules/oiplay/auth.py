import json
import datetime
import re
import requests
from resources.lib.beatifulsoup import BeautifulSoup
import urlparse
from json import JSONEncoder
import pickle
import resources.lib.modules.control as control
import base64
from private_data import get_user, get_password


ACCESS_TOKEN_URL = 'https://apim.oi.net.br/connect/oauth2/token_endpoint/access_token'

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
    response_full = requests.get(url, headers=headers)

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
        refresh_token = None
        if settings_data:
            auth_json = json.loads(settings_data, object_hook=as_python_object)
            refresh_token = auth_json['refresh_token']

            if auth_json['date'] + datetime.timedelta(seconds=auth_json['expires_in']) > datetime.datetime.utcnow():
                control.log('ACCESS TOKEN FROM FILE: ' + auth_json['access_token'])
                id_token = auth_json.get('id_token')
                return auth_json['access_token'], get_account_id(id_token)

        if not refresh_token:
            response = __login(user, password)
        else:
            success, response = __refresh_token(refresh_token)

            if not success:
                response = __login(user, password)

    control.log(response)

    response['date'] = datetime.datetime.utcnow()

    control.setSetting('oiplay_access_token_response', json.dumps(response, cls=PythonObjectEncoder))

    id_token = response.get('id_token')

    return response['access_token'], get_account_id(id_token)


def get_account_id(id_token):
    jwt = id_token.split('.')
    jwt_base64_string = jwt[1] + '====='
    jwt_json_string = base64.decodestring(jwt_base64_string)
    account_id = json.loads(jwt_json_string).get('cpfcnpj')

    return account_id


def __refresh_token(refresh_token):

    control.log('REFRESH TOKEN')

    body = {
        'client_id': 'e722caf1-7c47-4398-ac7f-f75a5f843906',
        'client_secret': 'b1e75e98-0833-4c67-aed7-9f1f232c8e0f',
        'grant_type': 'refresh_token',
        'refresh_token': str(refresh_token)
    }

    control.log(body)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'User-Agent': 'OiPlay-Store/5.1.1 (iPhone; iOS 13.3.1; Scale/3.00)'
    }

    response = requests.post(ACCESS_TOKEN_URL, json=body, headers=headers)

    # response.raise_for_status()

    response = response.json()

    if not response or 'access_token' not in response:
        return False, None

    return True, response


def __login(user, password):

    control.log('LOGIN OIPLAY')

    session = requests.session()

    url = 'https://apim.oi.net.br/oic?state=eyJzdGF0ZSI6InN0YXRlIiwidGFyZ2V0X3VyaSI6Ii9kby1sb2dpbiJ9&client_id=e722caf1-7c47-4398-ac7f-f75a5f843906&response_type=code&scope=openid%20customer_info%20oob&redirect_uri=https://oiplay.tv/login'

    response = session.get(url)

    url = re.findall(r'action="([^"]+)"', response.content)[0]

    url = 'https://logintv.oi.com.br' + url

    session.post(url)

    url_login = 'https://logintv.oi.com.br/nidp/wsfed/ep?sid=0'

    response = session.post(url_login, data={
        'option': 'credential',
        'urlRedirect': 'https://logintv.oi.com.br/nidp/wsfed/ep?sid=0',
        'Ecom_User_ID': user,
        'Ecom_Password': password
    })

    # control.log(response.content)

    url = re.findall(r"window.location.href='([^']+)';", response.content)[0]

    control.log('GET %s' % url)

    response = session.get(url)

    html = BeautifulSoup(response.content)

    url = html.find('form')['action']

    inputs = html.findAll('input')

    post = {}

    for input in inputs:
        post[input['name']] = input['value']

    response = session.post(url, data=post, allow_redirects=False)

    url_parsed = urlparse.urlparse(response.headers['Location'])

    qs = urlparse.parse_qs(url_parsed.query)

    code = qs['code']

    post = {
        'client_id': 'e722caf1-7c47-4398-ac7f-f75a5f843906',
        'client_secret': 'b1e75e98-0833-4c67-aed7-9f1f232c8e0f',
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://oiplay.tv/login'
    }

    token_response = session.post(ACCESS_TOKEN_URL, data=post)

    return json.loads(token_response.content, object_hook=as_python_object)


class PythonObjectEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return JSONEncoder.default(self, obj)
        return {'_python_object': pickle.dumps(obj)}


def as_python_object(dct):
    if '_python_object' in dct:
        return pickle.loads(str(dct['_python_object']))
    return dct
