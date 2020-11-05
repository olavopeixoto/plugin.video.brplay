# -*- coding: utf-8 -*-

import importlib
import sys
import urllib
import json
import operator
from allowkwargs import allow_kwargs
from resources.lib.modules import control
import traceback
import types


class RouteError(Exception):
    pass


MODULES_CACHE = {}

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])


def handle_route(data):
    handler = data.get('handler', None)
    method = data.get('method', None)

    if not handler or not method:
        control.log('No handler available for: %s' % data)
        return

    is_playable = data.get('IsPlayable', False)

    if is_playable:
        control.log('Playing item...')
        return _play_item(handler, method, data)

    control.log('Discovering directory...')
    result = _run_handler(handler, method, data)

    if result and is_iterable(result):
        control.log('Iterating items...')
        create_directory(result, data)
    else:
        if isinstance(result, str):
            control.log('Executing command: %s' % result)
            control.execute(result)
        elif is_iterable(result):
            control.log('No result to display')
        else:
            control.log('Refreshing container')
            control.refresh()
            return

        control.directory(syshandle)


def _run_handler(handler, method, kwargs):
    module = _get_module(handler)
    return _run_method(module, method, kwargs)


def is_iterable(item):
    if isinstance(item, str):
        return False

    if isinstance(item, bool):
        return False

    if isinstance(item, int):
        return False

    if isinstance(item, dict):
        return False

    if isinstance(item, types.GeneratorType):
        return True

    try:
        iter(item)
        return True
    except TypeError:
        return False


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

    succeeded = True
    custom_title = None

    try:
        media_types = {}
        content = None
        sort_methods = set()

        for data in items:
            label = data.get('label', '')
            label2 = data.get('label2', None)

            item = control.item(label=label, label2=label2)

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
            is_folder = data.get('IsFolder', not is_playable)

            if is_playable:
                item.setProperty('IsPlayable', 'true')
            else:
                item.setProperty('IsPlayable', 'false')

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
            if isinstance(sort, tuple):
                control.addSortMethod(syshandle, sort[0], sort[1])
            else:
                control.addSortMethod(syshandle, sort)

        category = custom_title or current.get('label', None)
        if category:
            control.category(handle=syshandle, category=category)

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

        if content and content != 'default':
            control.content(syshandle, content)

    except:
        control.log(traceback.format_exc(), control.LOGERROR)
        succeeded = False
    finally:
        control.directory(syshandle, succeeded=succeeded, updateListing=False, cacheToDisc=True)
