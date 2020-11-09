# -*- coding: utf-8 -*-

import requests
from resources.lib.beatifulsoup import BeautifulSoup
import urlparse
import resources.lib.modules.control as control
import re
import datetime
import json
import traceback


def log(msg):
    control.log('[Telecine] - %s' % msg)


def get_device_id():
    device_id = control.setting('telecine_device_id')

    if not device_id:
        device_id = register_device()
        control.setSetting('telecine_device_id', device_id)

    return device_id


def get_auth_token():
    tokens = login()
    token = next((token.get('value') for token in tokens if token.get('type') == 'AuthorizationJWT'), None)
    # control.log('AUTH TOKEN: %s' % token)
    return token


def login():

    credentials = control.setting('telecine_credentials')
    if credentials:
        log('Found credentials from cache')
        credentials = json.loads(credentials)

        user_account_token_expiry_ts = credentials[0]['expirationDate']
        user_account_token_expiry = datetime.datetime.fromtimestamp(user_account_token_expiry_ts)

        if user_account_token_expiry > datetime.datetime.utcnow():
            return credentials
        else:
            log('Cached credentials expired: %s' % user_account_token_expiry)
            token = next((token.get('value') for token in credentials if token.get('type') == 'AuthorizationJWT'), None)
            try:
                log('trying to refresh...')
                credentials = refresh_token(token)
            except:
                log(traceback.format_exc())
                credentials = None

    if not credentials:
        user = control.setting('telecine_account')
        password = control.setting('telecine_password')
        idp_description = control.setting('telecine_provider')

        idp = get_provider_by_name(idp_description)

        try:
            credentials = _login_internal(user, password, idp)
        except Exception as ex:
            control.log(traceback.format_exc(), control.LOGERROR)
            control.infoDialog(ex.message, icon='ERROR')
            return []

    control.setSetting('telecine_credentials', json.dumps(credentials))

    return credentials


def refresh_token(token):
    url = 'https://bff.telecinecloud.com/api/v1/authentication/refresh'

    headers = {
        'authorization': 'Bearer ' + token,
        'x-version': '2.5.10',
        'user-agent': 'Telecine_iOS/2.5.10 (br.com.telecineplay; build:37; iOS 14.1.0) Alamofire/5.2.2',
        'x-device': 'Mobile-iOS'
    }

    log('POST %s' % url)

    result = requests.post(url, headers=headers)

    result.raise_for_status()

    return (result.json() or {}).get('tokens', [])


def register_device():
    auth = get_auth_token()

    if not auth:
        return

    url = 'https://bff.telecinecloud.com/api/v1/account/devices'
    headers = {
        'authorization': 'Bearer ' + auth,
        'user-agent': 'Telecine_iOS/2.5.10 (br.com.telecineplay; build:37; iOS 14.1.0) Alamofire/5.2.2',
        'x-device': 'Mobile-iOS',
        'x-version': '2.5.10'
    }
    data = {
        "name": "BR Play"
    }
    log('register_device')
    response = requests.post(url, json=data, headers=headers)

    response.raise_for_status()

    json_response = response.json()

    log(json_response)

    return json_response.get('id')


def get_provider_by_name(name):
    if not name:
        return None

    url = 'https://bff.telecinecloud.com/api/v1/authentication/providers-toolbox?filter=operadoras'

    result = requests.get(url, headers={
                        'x-version': '2.5.10',
                        'user-agent': 'Telecine_iOS/2.5.10 (br.com.telecineplay; build:37; iOS 14.1.0) Alamofire/5.2.2',
                        'x-device': 'Mobile-iOS'
                    }).json()

    idp = next((idp for idp in result if idp.get('description') == name), {})

    return idp.get('idpShortName')


def _login_internal(user, password, idp):

    if not user or not password or not idp:
        raise Exception('Missing credentials')

    idp_func_name = '%s_login' % idp

    if idp_func_name not in globals():
        raise Exception(control.lang(34129).encode('utf-8'))

    log('Logging in using provider: %s' % idp)

    session = requests.session()

    #            https://sp.tbxnet.com/v2/auth/telecine/login.html?idp=oitv&return=https%3A%2F%2Fwww.telecineplay.com.br%2Fauthentication%3Fcallback_url%3D%2F&country=BR
    login_url = 'https://sp.tbxnet.com/v2/auth/telecine/login.html?return=https%3A%2F%2Fwww.telecineplay.com.br%2Ftoolbox%2Fcallback%3Fselected_idp%3D{idp}&country=BR&idp={idp}'.format(idp=idp)

    log('POST %s' % login_url)

    response = session.get(login_url)

    response.raise_for_status()

    # idp provider login
    response = globals()[idp_func_name](session, response, user, password)

    # continue tnt login

    url_parsed = urlparse.urlparse(response.url)

    qs = urlparse.parse_qs(url_parsed.query)

    auth_token = qs['toolbox_user_token'][0]

    log('auth_token:')
    log(auth_token)

    #################################################################

    url = 'https://bff.telecinecloud.com/api/v1/authentication'

    data = {
        "authToken": auth_token,
        "authProvider": idp
    }

    headers = {
        'user-agent': 'Telecine_iOS/2.5.10 (br.com.telecineplay; build:37; iOS 14.1.0) Alamofire/5.2.2',
        'x-device': 'Mobile-iOS',
        'x-version': '2.5.10'
    }

    log('POST %s' % url)
    log(data)

    response = requests.post(url, json=data, headers=headers)

    response.raise_for_status()

    tokens = response.json().get('tokens', [])

    log('TOKENS:')
    log(tokens)

    return tokens


def oitv_login(session, response, username, password):

    login_path = re.findall(r'action="([^"]+)"', response.content)[0]

    url = urlparse.urljoin(response.url, login_path)

    log('POST %s' % url)

    response = session.post(url)

    response.raise_for_status()

    html = BeautifulSoup(response.content)

    url = html.find('form')['action']

    inputs = html.findAll('input')

    post = {}

    for ipt in inputs:
        if ipt['name'] == 'Ecom_User_ID':
            value = username
        elif ipt['name'] == 'Ecom_Password':
            value = password
        else:
            value = ipt.get('value', '')

        post[ipt['name']] = value

    log('POST (AUTH) %s' % url)

    response = session.post(url, data=post)

    log(response.status_code)
    log(response.content)

    response.raise_for_status()

    url = re.findall(r"window.location.href='([^']+)';", response.content)[0]

    log('GET %s' % url)

    response = session.get(url)

    html = BeautifulSoup(response.content)

    url = html.find('form')['action']

    inputs = html.findAll('input')

    post = {}

    for ipt in inputs:
        post[ipt['name']] = ipt['value']

    log('POST %s' % url)
    log(post)

    response = session.post(url, data=post)

    log(response.status_code)
    log(response.content)

    response.raise_for_status()

    return response


def claro_login(session, response, username, password):
    return net_login(session, response, username, password)


def net_login(session, response, username, password):

    p = urlparse.urlparse(response.url)
    qs = urlparse.parse_qs(p.query)

    html = BeautifulSoup(response.content)

    form = html.find('form')

    if not form:
        raise Exception('Failed to login: %s' % response.url)

    fields = form.findAll('input')

    form_data = dict((field.get('name'), field.get('value')) for field in fields)

    form_data['Username'] = username
    form_data['password'] = password
    form_data['Auth_method'] = 'UP'

    for key in qs.keys():
        form_data[key] = qs[key][0]

    post_url = urlparse.urljoin(response.url, form['action'])

    response = session.post(post_url, data=form_data)

    response.raise_for_status()

    p = urlparse.urlparse(response.url)
    qs = urlparse.parse_qs(p.query)

    if 'error' in qs and 'error_description' in qs:
        raise Exception(qs.get('error_description')[0].encode('utf-8'))

    return response
