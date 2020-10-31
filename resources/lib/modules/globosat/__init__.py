from resources.lib.modules import cache
from resources.lib.modules import control
import requests
import urllib


def request_query(query, variables, tenant='globosat-play'):
    url = 'https://products-jarvis.globo.com/graphql?query={query}&variables={variables}'.format(query=query, variables=urllib.quote_plus(variables))
    headers = {
        'x-tenant-id': tenant,
        'x-platform-id': 'web',
        'x-device-id': 'desktop',
        'x-client-version': '1.5.1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    control.log('{} - GET {}'.format(tenant, url))

    response = cache.get(requests.get, 1, url, headers=headers, table='globosat')

    response.raise_for_status()

    json_response = response.json()

    control.log(json_response)

    return json_response
