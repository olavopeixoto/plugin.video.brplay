import requests
import uuid
from resources.lib.modules import control
import json


PLATFORM = 'PCTV'  # PCTV | IPHONEH | ANDROIDTABLETH | ANDROIDMOBILEH

proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


def validate_login(credentials, do_request=True):

    if not credentials:
        return False

    current_platform = credentials.get('platform')
    if not current_platform or current_platform != PLATFORM:
        return False

    if not do_request:
        return True

    header = {
        'referer': 'https://www.nowonline.com.br/',
    }

    if PLATFORM == 'PCTV':
        xsrf = credentials['headers']['X-Xsrf-Token']
        header['x-xsrf-token'] = xsrf
        header['User_Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36'
        url = 'https://www.nowonline.com.br/AGL/1.1/R/ENG/{platform}/ALL/NET/USER/SESSIONS'.format(platform=PLATFORM)
    else:
        device_id = credentials['deviceId']
        header['User_Agent'] = 'NETNow/10.10.06 (br.com.netcombo.now.iphone; build:4; iOS 14.0.1) Alamofire/4.5.1'
        url = 'https://www.nowonline.com.br/AGL/1.1/R/ENG/{platform}/ALL/NET/USER/SESSIONS?accountDeviceIdType=DEVICEID&accountDeviceId={deviceId}'.format(platform=PLATFORM, deviceId=device_id)

    avs_cookie = credentials['cookies']['avs_cookie']
    login_info = credentials['cookies']['LoginInfo']

    cookies = {
        'avs_cookie': avs_cookie,
        'LoginInfo': login_info
    }

    control.log('GET %s' % url)
    control.log(header)
    control.log(cookies)

    response = requests.get(url, headers=header, cookies=cookies, proxies=proxy)

    control.log('Login Validation:')
    control.log(response.text)

    # {"resultCode":"KO","errorDescription":"ACN_3000","message":"400 - \"{\\\"error\\\": \\\"invalid_grant\\\", \\\"error_description\\\": \\\"Refresh token doesn't exist or it's expired\\\"}\"","resultObj":"","systemTime":1603476452213}

    return response.status_code == 200 and str(response.json().get('resultCode', '')) == 'OK'


def login(validate=True):

    credentials = control.setting('nowonline_credentials')

    if credentials:
        control.log('Found credentials cached')
        result = json.loads(credentials)
        if validate_login(result, validate):
            return result

        control.log('Validation failed, trying to login...')

    username = control.setting('nowonline_account')
    password = control.setting('nowonline_password')

    url = 'https://www.nowonline.com.br/AGL/1.1/R/ENG/{platform}/ALL/NET/USER/SESSIONS'.format(platform=PLATFORM)

    header = {
        'referer': 'https://www.nowonline.com.br/'
    }

    data = {
        "credentials":
            {
                "username": username,
                "password": password,
                "type": "net"
            }
    }

    device_id = None

    if PLATFORM != 'PCTV':
        device_id = control.setting('nowonline_device_id')
        if not device_id:
            device_id = str(uuid.uuid4()).upper()
            control.setSetting('nowonline_device_id', device_id)

        data['deviceInfo'] = {
            "deviceId": device_id,
            "deviceIdType": "DEVICEID"
        }

    control.log('GET %s' % url)

    response = requests.post(url, json=data, headers=header, proxies=proxy)

    response.raise_for_status()

    # response_data = response.json()
    avs_cookie = response.cookies.get('avs_cookie')
    avs_user_info = response.cookies.get('avs_user_info')
    dt_cookie = response.cookies.get('dtCookie')
    login_info = response.cookies.get('LoginInfo')
    session_id = response.cookies.get('sessionId')
    x_xsrf_token = response.headers.get('X-Xsrf-Token')

    credentials = {
        'platform': PLATFORM,
        'cookies': {
            'avs_cookie': avs_cookie,
            'avs_user_info': avs_user_info,
            'dtCookie': dt_cookie,
            'LoginInfo': login_info,
            'sessionId': session_id,
        },
        'headers': {
            'X-Xsrf-Token': x_xsrf_token
        }
    }

    if PLATFORM != 'PCTV':
        credentials['deviceId'] = device_id

    control.log(credentials)

    control.setSetting('nowonline_credentials', json.dumps(credentials))

    return credentials


def get_request_data(validate=False):
    credentials = login(validate)

    avs_cookie = credentials['cookies']['avs_cookie']
    avs_user_info = credentials['cookies']['avs_user_info']
    login_info = credentials['cookies']['LoginInfo']
    xsrf = credentials['headers']['X-Xsrf-Token']

    headers = {
        'referer': 'https://www.nowonline.com.br/'
    }

    if PLATFORM == 'PCTV':
        headers['x-xsrf-token'] = xsrf

    cookies = {
        'avs_cookie': avs_cookie,
        'LoginInfo': login_info,
        'avs_user_info': avs_user_info
    }

    return headers, cookies
