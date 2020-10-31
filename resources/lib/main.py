# -*- coding: utf-8 -*-

import json
import traceback


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
        indexer.create_directory(navigator.root())

    elif action == 'settings':
        from resources.lib.indexers import navigator
        navigator.open_settings()

    elif action == 'clear':
        from resources.lib.indexers import navigator
        navigator.clear_cache()

    elif action == 'clearAuth':
        from resources.lib.indexers import navigator
        navigator.clear_credentials()

    elif action == 'login':
        from resources.lib.indexers import navigator
        navigator.cache_auth()

    elif action == 'refresh':
        from resources.lib.modules import control
        control.refresh()

    elif action == 'searchMenu':
        from resources.lib.indexers import navigator
        navigator.search_menu()

    elif action == 'image':
        return 'https://globosatplay.globo.com/_next/static/images/canaisglobo-e3e629829ab01851d983aeaec3377807.png'

    # Generic Tree

    elif action == 'generic':
        from resources.lib.indexers import indexer
        indexer.handle_route(meta_json)
