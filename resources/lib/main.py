# -*- coding: utf-8 -*-

import json
import traceback
import sys
from resources.lib.indexers import navigator, indexer
from resources.lib.modules import control


def run(params):
    params = params or {}

    control.log('[BRplay] - PARAMS: %s' % params)

    # Parameters
    action = params.get('action')

    meta = params.get('meta')

    try:
        meta_json = json.loads(meta) if meta else None
    except:
        control.log(traceback.format_exc(), control.LOGERROR)
        meta_json = {}

    # Actions
    if not action:
        syshandle = int(sys.argv[1])
        indexer.create_directory(navigator.root(), cache_to_disk=False)
        control.category(handle=syshandle, category=control.addonInfo('name'))

    elif action == navigator.open_settings.__name__:
        navigator.open_settings()

    elif action == 'clear':
        navigator.clear_cache()

    elif action == 'clearAuth':
        navigator.clear_credentials()

    elif action == 'refresh':
        control.refresh()

    # Generic Tree

    elif action == 'generic':
        indexer.handle_route(meta_json)
