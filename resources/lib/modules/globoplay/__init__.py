# -*- coding: utf-8 -*-

from resources.lib.modules import control, cache, workers
import requests
from urllib.parse import quote_plus
from . import auth_helper


def request_query(query, variables, force_refresh=False, timeout_hour=1, retry=3):
    proxy = get_proxy()

    url = 'https://cloud-jarvis.globo.com/graphql?query={query}&variables={variables}'.format(query=query, variables=quote_plus(variables))
    headers = get_headers()

    control.log('{} - GET {}'.format('Globoplay', url))
    response = cache.get(requests.get, timeout_hour, url, headers=headers, proxies=proxy, force_refresh=force_refresh, table='globoplay')

    if response.status_code >= 500 and retry > 0:
        return request_query(query, variables, True, timeout_hour=timeout_hour, retry=retry - 1)

    response.raise_for_status()

    json_response = response.json()

    control.log(json_response)

    if 'errors' in json_response and json_response['errors'] and retry > 0:
        return request_query(query, variables, force_refresh=True, timeout_hour=timeout_hour, retry=retry-1)

    return json_response


def get_tenant():
    tenant_id = int(control.setting('globoplay_tenant') or -1)

    if tenant_id == 1:
        return auth_helper.TENANTS.GLOBO_PLAY
    if tenant_id == 2:
        return auth_helper.TENANTS.GLOBO_PLAY_BETA
    if tenant_id == 3:
        return auth_helper.TENANTS.GLOBO_PLAY_US
    if tenant_id == 4:
        return auth_helper.TENANTS.GLOBO_PLAY_PT
    if tenant_id == 5:
        return auth_helper.TENANTS.GLOBO_PLAY_EU

    # Default Auto
    return discover_tenant()


def get_proxy():
    tenant = get_tenant()
    proxy = control.proxy_url
    proxy = None if proxy is None or proxy == '' or (tenant != auth_helper.TENANTS.GLOBO_PLAY and tenant != auth_helper.TENANTS.GLOBO_PLAY_BETA) else {
        'http': proxy,
        'https': proxy,
    }

    return proxy


def get_headers():
    token, user_id = auth_helper.get_token_and_user_id()

    return {
        'accept': '*/*',
        'authorization': token,
        'content-type': 'application/json',
        'Referer': 'https://globoplay.globo.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'x-tenant-id': get_tenant(),
        'x-client-version': '3.543.1',
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

    # if not auth_helper.is_logged_in():
    #     auth_helper.get_credentials()

    ids_set = set(service_ids)

    if len(ids_set) == 1:
        return [service_id for index, service_id in enumerate(ids_set) if auth_helper.is_service_allowed(service_id)]
    else:
        threads = [workers.Thread(auth_helper.is_service_allowed, service_id) for service_id in ids_set]
        [t.start() for t in threads]
        [t.join() for t in threads]
        [t.kill() for t in threads]
        return [service_id for index, service_id in enumerate(ids_set) if threads[index].get_result()]


def discover_tenant():
    import re
    response = requests.get('https://globoplay.globo.com/')
    response.raise_for_status()

    match = re.search(r'tenant: "([^"]+)",', response.text)

    tenant = match.group(1)

    return tenant
