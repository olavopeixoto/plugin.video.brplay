# -*- coding: utf-8 -*-

import importlib
import sys
from urllib.parse import quote_plus
import json
import operator
from .allowkwargs import allow_kwargs
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


def create_directory(items, current=None, cache_to_disk=True):
    if current is None:
        current = {}

    succeeded = True
    custom_title = None

    try:
        media_types = {}
        content = None
        sort_methods = set()

        item_count = 0

        for data in items:
            label = data.get('label', '')

            if control.supports_offscreen:
                item = control.item(label=label, offscreen=True)
            else:
                item = control.item(label=label)

            art = data.get('art', {}) or {}
            item.setArt(art)

            properties = data.get('properties', {}) or {}
            item.setProperties(properties)

            item.setInfo(type='video', infoLabels=control.filter_info_labels(data))

            cm = [(control.lang(32072), 'RunPlugin(%s?action=refresh)' % sysaddon),
                  (control.lang(33501), 'RunPlugin(%s?action=clear)' % sysaddon)]

            for menu in data.get('context_menu', []) or []:
                cm.append(menu)

            item.addContextMenuItems(cm)

            meta_string = quote_plus(json.dumps(data))
            url = data.get('url', None) or '%s?action=generic&meta=%s' % (sysaddon, meta_string)

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
                item.setCast(data.get('setCast', []))

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=is_folder)

            item_count = item_count + 1

        control.log('Added %s item%s' % (item_count, 's' if item_count > 1 else ''))

        for sort in sort_methods:
            if isinstance(sort, tuple):
                control.addSortMethod(syshandle, sort[0], sort[1], sort[2] if len(sort) > 2 else None)
            else:
                control.addSortMethod(syshandle, sort)

        category = custom_title or current.get('label', None)
        if category:
            control.category(handle=syshandle, category=category)

        # content: files, songs, artists, albums, movies, tvshows, episodes, musicvideos
        if not content and media_types:
            media_type = max(media_types.items(), key=operator.itemgetter(1))[0]

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
        control.directory(syshandle, succeeded=succeeded, updateListing=False, cacheToDisc=cache_to_disk)


# https://romanvm.github.io/Kodistubs/_autosummary/xbmcplugin.html#xbmcplugin.addSortMethod

# /* LabelFormatter
#  * ==============
#  *
#  * The purpose of this class is to parse a mask string of the form
#  *
#  *  [%N. ][%T] - [%A][ (%Y)]
#  *
#  * and provide methods to format up a CFileItem's label(s).
#  *
#  * The %N/%A/%B masks are replaced with the corresponding metadata (if available).
#  *
#  * Square brackets are treated as a metadata block.  Anything inside the block other
#  * than the metadata mask is treated as either a prefix or postfix to the metadata. This
#  * information is only included in the formatted string when the metadata is non-empty.
#  *
#  * Any metadata tags not enclosed with square brackets are treated as if it were immediately
#  * enclosed - i.e. with no prefix or postfix.
#  *
#  * The special characters %, [, and ] can be produced using %%, %[, and %] respectively.
#  *
#  * Any static text outside of the metadata blocks is only shown if the blocks on either side
#  * (or just one side in the case of an end) are both non-empty.
#  *
#  * Examples (using the above expression):
#  *
#  *   Track  Title  Artist  Year     Resulting Label
#  *   -----  -----  ------  ----     ---------------
#  *     10    "40"    U2    1983     10. "40" - U2 (1983)
#  *           "40"    U2    1983     "40" - U2 (1983)
#  *     10            U2    1983     10. U2 (1983)
#  *     10    "40"          1983     "40" (1983)
#  *     10    "40"    U2             10. "40" - U2
#  *     10    "40"                   10. "40"
#  *
#  * Available metadata masks:
#  *
#  *  %A - Artist
#  *  %B - Album
#  *  %C - Programs count
#  *  %D - Duration
#  *  %E - episode number
#  *  %F - FileName
#  *  %G - Genre
#  *  %H - season*100+episode
#  *  %I - Size
#  *  %J - Date
#  *  %K - Movie/Game title
#  *  %L - existing Label
#  *  %M - number of episodes
#  *  %N - Track Number
#  *  %O - mpaa rating
#  *  %P - production code
#  *  %Q - file time
#  *  %R - Movie rating
#  *  %S - Disc Number
#  *  %T - Title
#  *  %U - studio
#  *  %V - Playcount
#  *  %W - Listeners
#  *  %X - Bitrate
#  *  %Y - Year
#  *  %Z - tvshow title
#  *  %a - Date Added
#  *  %b - Total number of discs
#  *  %c - Relevance - Used for actors' appearances
#  *  %d - Date and Time
#  *  %e - Original release date
#  *  %f - bpm
#  *  %p - Last Played
#  *  %r - User Rating
#  *  *t - Date Taken (suitable for Pictures)
#  */
