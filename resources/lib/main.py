# -*- coding: utf-8 -*-

import json
import traceback
import sys


def run(params):
    from resources.lib.modules import control

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
        from resources.lib.indexers import navigator, indexer
        syshandle = int(sys.argv[1])
        indexer.create_directory(navigator.root(), cache_to_disk=False)
        control.category(handle=syshandle, category=control.addonInfo('name'))

    elif action == 'settings':
        from resources.lib.indexers import navigator
        navigator.open_settings()

    elif action == 'clear':
        from resources.lib.indexers import navigator
        navigator.clear_cache()

    elif action == 'clearAuth':
        from resources.lib.indexers import navigator
        navigator.clear_credentials()

    elif action == 'refresh':
        from resources.lib.modules import control
        control.refresh()

    # Generic Tree

    elif action == 'generic':
        from resources.lib.indexers import indexer
        indexer.handle_route(meta_json)
