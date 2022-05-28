# -*- coding: utf-8 -*-

import requests
import urllib.parse as urlparse
import re
from bs4 import BeautifulSoup
import resources.lib.modules.control as control

TNT_PROVIDERS = [
    {
        'description': "TV Alphaville",
        'slug': "alp",
        'logo': "https://sp-'logo's.tbxnet.com/alp.png"
    }, {
        'description': "BluTV",
        'slug': "blu",
        'logo': "https://sp-'logo's.tbxnet.com/blu.png"
    }, {
        'description': "Vivo Banda Larga ou TV",
        'slug': "viv_br",
        'logo': "https://sp-'logo's.tbxnet.com/viv_br.png"
    }, {
        'description': "Claro tv",
        'slug': "claro",
        'logo': "https://sp-'logo's.tbxnet.com/claro.png"
    }, {
        'description': "TVN",
        'slug': "tvn",
        'logo': "https://sp-'logo's.tbxnet.com/tvn.png"
    }, {
        'description': "Cabo Telecom",
        'slug': "cabo",
        'logo': "https://sp-'logo's.tbxnet.com/cabo.png"
    }, {
        'description': "Multiplay Telecom",
        'slug': "multiplay",
        'logo': "https://sp-'logo's.tbxnet.com/multiplay.png"
    }, {
        'description': "Sky Brasil",
        'slug': "sky_br",
        'logo': "https://sp-'logo's.tbxnet.com/sky_br.png"
    }, {
        'description': "Algar Telecom",
        'slug': "algar",
        'logo': "https://sp-'logo's.tbxnet.com/algar.png"
    }, {
        'description': "Oi",
        'slug': "oitv",
        'logo': "https://sp-'logo's.tbxnet.com/oitv.png"
    }, {
        'description': "Claro Net Tv",
        'slug': "net",
        'logo': "https://sp-'logo's.tbxnet.com/net.png"
    }
]


proxy = None  # control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


def get_device_id():
    device_id = control.setting('tntplay_device_id')
    if not device_id:
        device_id = generate_device_id()
        control.log('New TNT Play Device ID: %s' % device_id)
        control.setSetting('tntplay_device_id', device_id)

    return device_id


def generate_device_id():
    import uuid
    import hashlib

    return 'TNTGO_LATAM_BR_%s' % str(hashlib.sha256(uuid.uuid4().hex.encode()).hexdigest())


def logout(platform='PCTV'):
    cookie = control.setting('tntplay_token')
    return tnt_logout(cookie, platform)


def tnt_logout(token, platform='PCTV'):

    if not token:
        return

    headers = {
        'Accept': 'application/json',
        'cookie': 'avs_cookie=' + token,
        'User-Agent': 'Tnt/2.2.13.1908061505 CFNetwork/1107.1 Darwin/19.0.0'
    }
    url = 'https://api.tntgo.tv/AVS/besc?action=Logout&channel={platform}&logoutDevice=Y'.format(platform=platform)
    result = requests.get(url, headers=headers).json()

    return result


def get_token(force=False):

    cookie = control.setting('tntplay_token')

    if cookie and not force:
        return cookie

    if not cookie:
        cookie = login()

    cookie = refresh_token(cookie)

    control.setSetting('tntplay_token', cookie)

    return cookie


def login():
    username = control.setting('tntplay_account')
    password = control.setting('tntplay_password')
    country = control.setting('tntplay_country') or 'BR'
    idp_id = control.setting('tntplay_provider')

    identity_provider = next((idp.get('slug') for idp in TNT_PROVIDERS if idp['description'] == idp_id), None)

    return tnt_login(username, password, identity_provider, country)


def refresh_token(token):
    headers = {
        'Accept': 'application/json',
        'cookie': 'avs_cookie=' + token,
        'User-Agent': 'Tnt/2.2.13.1908061505 CFNetwork/1107.1 Darwin/19.0.0'
    }

    device_id = get_device_id()
    url = 'https://apac.ti-platform.com/AGL/1.0/R/ENG/IPHONE/TNTGO_LATAM_BR/USER/REFRESH?deviceId={device_id}&filter_brand=space%2Ctnts%2Ctnt'.format(device_id=device_id)

    control.log('TNT PLAY GET %s' % url)
    control.log(headers)

    response = requests.get(url, headers=headers, proxies=proxy)

    response.raise_for_status()

    result = response.json()

    if not result:
        raise Exception('Failed to authenticate')

    if result['resultCode'] != 'OK':
        control.log(result['message'])
        control.log(result)
        control.log('TNT PLAY: TRYING TO LOGIN...')

        auth_token = login()
    else:
        auth_token = result['resultObj']['avs_cookie']

    return auth_token


def tnt_login(username, password, identity_provider, country='BR'):

    idp_func_name = '%s_login' % identity_provider

    if idp_func_name not in globals():
        raise Exception(control.lang(34129))

    # start tnt login
    device_id = get_device_id()

    session = requests.session()

    start_url = 'https://sp.tbxnet.com/v2/auth/tnt_br/login.html?return=https%3A%2F%2Fauth.ti-platform.com%2Fsite%2FAuth-Toolbox-Proto-Webview.html&country={country}&idp={idp}'.format(country=country, idp=identity_provider)

    response = session.get(start_url, proxies=proxy)

    response.raise_for_status()

    # idp provider login
    response = globals()[idp_func_name](session, response, username, password)

    # continue tnt login
    p = urlparse.urlparse(response.url)
    qs = urlparse.parse_qs(p.query)

    if not qs or 'toolbox_user_token' not in qs:
        raise Exception('Failed to login: %s' % response.url)

    toolbox_user_token = qs.get('toolbox_user_token')[0]

    login_url = 'https://apac.ti-platform.com/AGL/1.0/a/eng/PCTV/TNTGO_LATAM_BR/USER/LOGIN_TOOLBOX/'
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Tnt/2.2.13.1908061505 CFNetwork/1107.1 Darwin/19.0.0'
    }
    post_data = {
        "cp_id": "tnt_br",
        "deviceid": device_id,
        "toolbox_user_token": toolbox_user_token
    }

    response = session.post(login_url, data=post_data, headers=headers, proxies=proxy)

    response.raise_for_status()

    response = response.json()

    if response['resultCode'] != 'OK':
        control.log('LOGIN ERROR')

        control.log(response)
        raise Exception(response['message'])

    return response['resultObj']['avs_cookie']


def oitv_login(session, response, username, password):

    html = BeautifulSoup(response.text)

    form = html.find('form')

    if not form:
        raise Exception('Failed to login: %s' % response.url)

    fields = form.findAll('input')

    form_data = dict((field.get('name'), field.get('value')) for field in fields)
    post_url = urlparse.urljoin(response.url, form['action'])

    control.log('[TNT] - POST %s' % post_url)

    response = session.post(post_url, data=form_data, proxies=proxy)

    response.raise_for_status()

    html = BeautifulSoup(response.text)

    if not html:
        raise Exception('Failed to login: %s' % response.url)

    form = html.find('form')

    if not form:
        raise Exception('Failed to login: %s' % response.url)

    fields = form.findAll('input')
    form_data = dict((field.get('name'), field.get('value')) for field in fields)

    form_data['Ecom_User_ID'] = username
    form_data['Ecom_Password'] = password

    post_url = form['action']

    control.log('[TNT] - POST %s' % post_url)

    response = session.post(post_url, data=form_data, proxies=proxy)

    response.raise_for_status()

    url = re.findall(r"window.location.href='([^']+)';", response.text)[0]

    control.log('[TNT] - GET %s' % url)

    response = session.get(url)

    html = BeautifulSoup(response.text)

    error = html.find("div", {"class": "data-invalid-text"})
    if error:
        control.log(response.text)
        msg = error.text.encode('utf8')
        raise Exception(msg)

    form = html.find('form')
    fields = form.findAll('input')
    form_data = dict((field.get('name'), field.get('value')) for field in fields)
    post_url = form['action']

    control.log('[TNT] - POST %s' % post_url)

    response = session.post(post_url, data=form_data, proxies=proxy)

    response.raise_for_status()

    return response


def claro_login(session, response, username, password):
    return net_login(session, response, username, password)


def net_login(session, response, username, password):

    p = urlparse.urlparse(response.url)
    qs = urlparse.parse_qs(p.query)

    html = BeautifulSoup(response.text)

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

    response = session.post(post_url, data=form_data, proxies=proxy)

    response.raise_for_status()

    p = urlparse.urlparse(response.url)
    qs = urlparse.parse_qs(p.query)

    if 'error' in qs and 'error_description' in qs:
        raise Exception(qs.get('error_description')[0])

    return response
