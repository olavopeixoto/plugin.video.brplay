# -*- coding: UTF-8 -*-

from resources.lib.modules.globosat.auth import claro as globosat_claro
from resources.lib.modules.globosat.auth import globosat_guest as globosat_globosat_guest
from resources.lib.modules.globosat.auth import net as globosat_net
from resources.lib.modules.globosat.auth import sky as globosat_sky
from resources.lib.modules.globosat.auth import tv_oi as globosat_tv_oi
from resources.lib.modules.globosat.auth import vivo as globosat_vivo


class net(globosat_net):
    OAUTH_URL = 'http://sexyhotplay.com.br/vod/auth/authorize/'
    GLOBOSAT_CREDENTIALS = 'sexyhot_credentials'
    PROVIDER_ID = 131

class tv_oi(globosat_tv_oi):
    OAUTH_URL = 'http://sexyhotplay.com.br/vod/auth/authorize/'
    GLOBOSAT_CREDENTIALS = 'sexyhot_credentials'
    PROVIDER_ID = 132

class sky(globosat_sky):
    OAUTH_URL = 'http://sexyhotplay.com.br/vod/auth/authorize/'
    GLOBOSAT_CREDENTIALS = 'sexyhot_credentials'
    PROVIDER_ID = 88

class vivo(globosat_vivo):
    OAUTH_URL = 'http://sexyhotplay.com.br/vod/auth/authorize/'
    GLOBOSAT_CREDENTIALS = 'sexyhot_credentials'
    PROVIDER_ID = 155

class claro(globosat_claro):
    OAUTH_URL = 'http://sexyhotplay.com.br/vod/auth/authorize/'
    GLOBOSAT_CREDENTIALS = 'sexyhot_credentials'
    PROVIDER_ID = 173

class globosat_guest(globosat_globosat_guest):
    OAUTH_URL = 'http://sexyhotplay.com.br/vod/auth/authorize/'
    GLOBOSAT_CREDENTIALS = 'sexyhot_credentials'
    PROVIDER_ID = 43