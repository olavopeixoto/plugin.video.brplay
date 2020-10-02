import json
import requests
from resources.lib.beatifulsoup import BeautifulSoup
import urlparse
import resources.lib.modules.control as control

REFRESH_CODE_URL = 'https://apac.ti-platform.com/AGL/1.0/R/ENG/IPHONE/TNTGO_LATAM_BR/USER/REFRESH?deviceId=%s&filter_brand=space%2Ctnts%2Ctnt'


def get_token(force=False):
    cookie = control.setting('tntplay_token')

    if cookie and not force:
        return cookie

    username = control.setting('tntplay_account')
    password = control.setting('tntplay_password')

    if not cookie:
        cookie = login(username, password)

    headers = {
        'Accept': 'application/json',
        'cookie': 'avs_cookie=' + cookie,
        'User-Agent': 'Tnt/2.2.13.1908061505 CFNetwork/1107.1 Darwin/19.0.0'
    }

    result = json.loads(requests.get(REFRESH_CODE_URL, headers=headers).content)

    if not result:
        raise Exception('Failed to authenticate')

    if result['resultCode'] != 'OK':
        print(result['message'])
        print(result)
        print('TNT PLAY: TRYING TO LOGIN...')
        cookie = login(username, password)
    else:
        cookie = result['resultObj']['avs_cookie']

    control.setSetting('tntplay_token', cookie)

    return cookie


def login(username, password):

    device_id = get_device_id()

    session = requests.session()

    country = control.setting('tntplay_country') or 'BR'
    identity_provider = control.setting('tntplay_provider') or 'oitv'

    start_url = 'https://sp.tbxnet.com/v2/auth/tnt_br/login.html?return=https%3A%2F%2Fauth.ti-platform.com%2Fsite%2FAuth-Toolbox-Proto-Webview.html&country={country}&idp={idp}'.format(country=country, idp=identity_provider)
    response = session.get(start_url)

    html = BeautifulSoup(response.content)

    form = html.find('form')
    fields = form.findAll('input')
    form_data = dict((field.get('name'), field.get('value')) for field in fields)
    post_url = urlparse.urljoin(response.url, form['action'])

    response = session.post(post_url, data=form_data)

    html = BeautifulSoup(response.content)

    form = html.find('form')
    fields = form.findAll('input')
    form_data = dict((field.get('name'), field.get('value')) for field in fields)

    form_data['Ecom_User_ID'] = username
    form_data['Ecom_Password'] = password

    post_url = form['action']

    response = session.post(post_url, data=form_data)

    html = BeautifulSoup(response.content)

    form = html.find('form')
    fields = form.findAll('input')
    form_data = dict((field.get('name'), field.get('value')) for field in fields)
    post_url = form['action']

    response = session.post(post_url, data=form_data)

    p = urlparse.urlparse(response.url)
    qs = urlparse.parse_qs(p.query)

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

    response = session.post(login_url, data=post_data, headers=headers).json()

    if response['resultCode'] != 'OK':
        print('LOGIN ERROR')
        print(response)
        raise Exception(response['message'])

    return response['resultObj']['avs_cookie']


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

    return 'TNTGO_LATAM_BR_%s' % str(hashlib.sha256(uuid.uuid4().hex).hexdigest())
