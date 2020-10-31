# -*- coding: utf-8 -*-

from resources.lib.modules import cache
from resources.lib.modules import control
import requests
import urllib
import auth_helper


def request_query(query, variables, force_refresh=False, retry=3):
    url = 'https://products-jarvis.globo.com/graphql?query={query}&variables={variables}'.format(query=query, variables=urllib.quote_plus(variables))
    headers = get_headers()

    print('{} - GET {}'.format('Globoplay', url))
    response = cache.get(requests.get, 1, url, headers=headers, force_refresh=force_refresh, table='globoplay')

    if response.status_code >= 500 and retry > 0:
        return request_query(query, variables, True, retry - 1)

    response.raise_for_status()

    json_response = response.json()

    control.log(json_response)

    return json_response


def get_headers():
    return {
        'accept': '*/*',
        'authorization': auth_helper.get_token(),
        'content-type': 'application/json',
        'Referer': 'https://globoplay.globo.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
        'x-tenant-id': 'globo-play',
        'x-client-version': '3.330.0',
        'x-device-id': 'desktop',
        'x-platform-id': 'web',
        'x-user-id': auth_helper.get_user_id()
    }


def get_image_scaler():
    if control.is_4k_images_enabled:
        return 'X2160'

    return 'X1080'
