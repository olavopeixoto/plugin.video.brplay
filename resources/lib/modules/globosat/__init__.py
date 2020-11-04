from resources.lib.modules import cache
from resources.lib.modules import control
import requests
import urllib
import auth_helper


def request_query(query, variables, force_refresh=False, retry=3):
    tenant = 'globosat-play'

    token = auth_helper.get_globosat_token()

    url = 'https://products-jarvis.globo.com/graphql?query={query}&variables={variables}'.format(query=query, variables=urllib.quote_plus(variables))
    headers = {
        'authorization': token,
        'x-tenant-id': tenant,
        'x-platform-id': 'web',
        'x-device-id': 'desktop',
        'x-client-version': '1.5.1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    control.log('{} - GET {}'.format(tenant, url))

    response = cache.get(requests.get, 1, url, headers=headers, force_refresh=force_refresh, table='globosat')

    if response.status_code >= 500 and retry > 0:
        return request_query(query, variables, True, retry - 1)

    response.raise_for_status()

    json_response = response.json()

    control.log(json_response)

    return json_response
