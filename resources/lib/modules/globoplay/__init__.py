# -*- coding: utf-8 -*-

from resources.lib.modules import control, cache, workers
import requests
import urllib
import auth_helper


def request_query(query, variables, force_refresh=False, retry=3):
    url = 'https://products-jarvis.globo.com/graphql?query={query}&variables={variables}'.format(query=query, variables=urllib.quote_plus(variables))
    headers = get_headers()

    control.log('{} - GET {}'.format('Globoplay', url))
    response = cache.get(requests.get, 1, url, headers=headers, force_refresh=force_refresh, table='globoplay')

    if response.status_code >= 500 and retry > 0:
        return request_query(query, variables, True, retry - 1)

    response.raise_for_status()

    json_response = response.json()

    control.log(json_response)

    if 'errors' in json_response and json_response['errors'] and retry > 0:
        return request_query(query, variables, force_refresh=True, retry=retry-1)

    return json_response


def get_headers():
    token, user_id = auth_helper.get_token_and_user_id()
    return {
        'accept': '*/*',
        'authorization': token,
        'content-type': 'application/json',
        'Referer': 'https://globoplay.globo.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'x-tenant-id': 'globo-play',
        'x-client-version': '3.395.1',
        'x-device-id': 'desktop',
        'x-platform-id': 'web',
        'x-user-id': user_id
    }


def get_image_scaler():
    if control.is_4k_images_enabled:
        return 'X2160'

    return 'X1080'


def get_authorized_services(service_ids):
    if not service_ids:
        return []

    if control.globoplay_ignore_channel_authorization():
        return service_ids

    if len(service_ids) == 1:
        return [service_id for index, service_id in enumerate(service_ids) if auth_helper.is_service_allowed(service_id)]
    else:
        threads = [workers.Thread(auth_helper.is_service_allowed, service_id) for service_id in service_ids]
        [t.start() for t in threads]
        [t.join() for t in threads]
        [t.kill() for t in threads]
        return [service_id for index, service_id in enumerate(service_ids) if threads[index].get_result()]
