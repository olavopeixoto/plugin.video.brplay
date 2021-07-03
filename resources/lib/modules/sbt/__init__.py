import requests
import re
from resources.lib.modules import control


def get_authorization():
    token = control.setting('sbt_token')

    if token:
        return token

    control.log('SBT - Getting new auth token')

    url = 'https://www.sbt.com.br/main.js'

    response = requests.get(url, verify=False)

    r = re.search(r'setHeaders:\s*{Authorization:"(.+?)"', response.content)

    token = r.group(1)

    control.setSetting('sbt_token', token)

    control.log(token)

    return token
