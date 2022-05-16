import requests
import re
from resources.lib.modules import control


def get_authorization():
    token = control.setting('sbt_token')

    if token:
        return token

    control.log('SBT - Getting new auth token')

    main_url = 'https://www.sbt.com.br/'
    response = requests.get(main_url)

    response.raise_for_status()

    match = re.search(r'src="(main-[^"]+\.js)"', response.text)

    # src="main-es2015.e60433d0eb7853f03969.js"
    module_name = match.group(1)

    control.log('SBT MODULE NAME: %s' % module_name)

    url = 'https://www.sbt.com.br/' + module_name

    response = requests.get(url, verify=False)

    r = re.search(r'setHeaders:\s*{Authorization:"(.+?)"', response.text)

    token = r.group(1)

    control.setSetting('sbt_token', token)

    control.log(token)

    return token
