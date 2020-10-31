# -*- coding: utf-8 -*-

from auth import get_auth_token
from resources.lib.modules import control
from resources.lib.modules import cache
import requests


def get_headers():
    return {
        'authorization': 'Bearer %s' % get_auth_token(),
        'user-agent': 'Telecine_iOS/2.5.10 (br.com.telecineplay; build:37; iOS 14.1.0) Alamofire/5.2.2',
        'x-device': 'Mobile-iOS',
        'x-version': '2.5.10'
    }


def get_cached(url, proxies=None, force_refresh=False, retry=3):
    control.log('[Telecine] - GET %s' % url)

    response = cache.get(requests.get, 1, url, headers=get_headers(), proxies=proxies, force_refresh=force_refresh, table="telecine")

    if response.status_code >= 500 and retry > 0:
        return get_cached(url, proxies, True, retry-1)

    response.raise_for_status()

    json_response = response.json()

    control.log('[Telecine] - ' % json_response)

    return json_response
