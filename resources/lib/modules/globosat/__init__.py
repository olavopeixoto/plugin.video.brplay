from resources.lib.modules import control, cache, workers
import requests
from urllib.parse import quote_plus
from . import auth_helper


def request_query(query, variables, force_refresh=False, retry=3, use_cache=True):
    domain = control.setting('globo_api_domain')

    url = 'https://{domain}/graphql?query={query}&variables={variables}'.format(domain=domain, query=query, variables=quote_plus(variables))
    return request_url(url, force_refresh, retry, use_cache)


def request_url(url, force_refresh=False, retry=3, use_cache=True):
    tenant = 'globosat-play'

    token = auth_helper.get_globosat_token()

    headers = {
        'authorization': token,
        'x-tenant-id': tenant,
        'x-platform-id': 'web',
        'x-device-id': 'desktop',
        'x-client-version': '1.17.0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
    }

    control.log('{} - GET {}'.format(tenant, url))

    if use_cache:
        response = cache.get(requests.get, 1, url, headers=headers, force_refresh=force_refresh, table='globosat')
    else:
        response = requests.get(url, headers=headers)

    if response.status_code >= 500 and retry > 0:
        return request_url(url, True, retry - 1)

    response.raise_for_status()

    json_response = response.json()

    control.log(json_response)

    return json_response


def get_authorized_services(service_ids):
    if not service_ids:
        return []

    if control.setting('globosat_ignore_channel_authorization') == 'true':
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
        return [service_id for index, service_id in enumerate(ids_set) if threads[index].get_result()]
