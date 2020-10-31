# -*- coding: utf-8 -*-

import importlib
import sys
import urllib
import json
import operator
from allowkwargs import allow_kwargs
from resources.lib.modules import control
import traceback


class RouteError(Exception):
    pass


MODULES_CACHE = {}


def handle_route(data):
    handler = data.get('handler', None)
    method = data.get('method', None)

    if not handler or not method:
        control.log('No handler available for: %s' % data)
        return

    is_playable = data.get('IsPlayable', False)

    if is_playable:
        return _play_item(handler, method, data)

    result = _run_handler(handler, method, data)

    if result:
        control.log('Iterating items...')
        create_directory(result, data)
    else:
        control.log('No result to display')


def _run_handler(handler, method, kwargs):
    module = _get_module(handler)
    return _run_method(module, method, kwargs)


def _run_method(module, method, kwargs):
    module_name = module.__class__.__name__ if hasattr(module, '__class__') else module.__name__
    control.log('Handling route with: %s.%s' % (module_name, method))

    if hasattr(module, method):
        kwargs['meta'] = kwargs
        return allow_kwargs(getattr(module, method))(**kwargs)


def _play_item(provider, method, data):
    module = _get_module(provider)
    if hasattr(module, 'Player'):
        _run_method(module.Player(), method, data)


def _get_module(full_name):
    if full_name in MODULES_CACHE:
        return MODULES_CACHE[full_name]

    control.log('_get_module: %s' % full_name)

    module = importlib.import_module(full_name)

    MODULES_CACHE[full_name] = module

    return module


def create_directory(items, current=None):
    if current is None:
        current = {}

    sysaddon = sys.argv[0]
    syshandle = int(sys.argv[1])

    succeeded = True
    custom_title = None

    try:
        media_types = {}
        content = None
        sort_methods = set()

        for data in items:
            label = data.get('label', '')

            item = control.item(label=label)

            art = data.get('art', {}) or {}
            item.setArt(art)

            properties = data.get('properties', {}) or {}
            item.setProperties(properties)

            item.setInfo(type='video', infoLabels=control.filter_info_labels(data))

            cm = [(control.lang(32072).encode('utf-8'), 'RunPlugin(%s?action=refresh)' % sysaddon),
                  (control.lang(33501).encode('utf-8'), 'RunPlugin(%s?action=clear)' % sysaddon)]

            for menu in data.get('context_menu', []) or []:
                cm.append(menu)

            item.addContextMenuItems(cm)

            meta_string = urllib.quote_plus(json.dumps(data))
            url = '%s?action=generic&meta=%s' % (sysaddon, meta_string)

            is_playable = data.get('IsPlayable', False)
            is_folder = not is_playable

            if is_playable:
                item.setProperty('IsPlayable', 'true')

            media_type = data.get('mediatype', 'None') or 'None'
            if media_type not in media_types:
                media_types[media_type] = 1
            else:
                media_types[media_type] = media_types[media_type] + 1

            sorts = data.get('sort', [])
            if sorts:
                try:
                    for sort in sorts:
                        sort_methods.add(sort)
                except TypeError:
                    sort_methods.add(sorts)

            if not content and data.get('content', None):
                content = data.get('content', None)

            if not custom_title:
                custom_title = data.get('custom_title', None)

            if data.get('setCast', None):
                item.setCast(data.get('setCast', None))

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=is_folder)

        for sort in sort_methods:
            control.addSortMethod(syshandle, sort)

        control.category(handle=syshandle, category=custom_title or current.get('label', control.lang(32002).encode('utf-8')))

        # content: files, songs, artists, albums, movies, tvshows, episodes, musicvideos
        if not content and media_types:
            media_type = max(media_types.iteritems(), key=operator.itemgetter(1))[0]

            if media_type == 'movie':
                content = 'movies'

            elif media_type == 'tvshow':
                content = 'tvshows'

            elif media_type == 'episode':
                content = 'episodes'

            elif media_type == 'season':
                content = 'tvshows'

            elif media_type == 'musicvideo':
                content = 'musicvideos'

        if content:
            control.content(syshandle, content)

    except Exception:
        control.log(traceback.format_exc(), control.LOGERROR)
        succeeded = False
    finally:
        control.directory(syshandle, succeeded=succeeded, updateListing=False, cacheToDisc=False)
