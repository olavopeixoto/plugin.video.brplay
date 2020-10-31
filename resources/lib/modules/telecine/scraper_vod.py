# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules.telecine import get_cached
import player
import os

HANDLER = __name__
PLAYER_HANDLER = player.__name__

BASE_URL = 'https://bff.telecinecloud.com/api/v1'

FANART = 'https://t2.tudocdn.net/235304?w=1200'
NEXT_ICON = os.path.join(control.artPath(), 'next.png')


def get_channels():

    return [{
        'handler': HANDLER,
        'method': 'get_channel_categories',
        'label': 'Telecine',
        'id': 1966,
        'art': {
            'thumb': FANART,
            'fanart': FANART,
        }
    }]


def _get_navigation():
    url = BASE_URL + '/navigation'

    response = get_cached(url)

    return response


def get_channel_categories():

    response = _get_navigation()

    yield {
            'handler': HANDLER,
            'method': 'get_page',
            'label': control.lang(34135).encode('utf-8'),
            'path': '/',
            'content': 'files',
            'art': {
                'thumb': FANART,
                'fanart': FANART,
            }
        }

    yield {
        'handler': HANDLER,
        'method': 'get_page',
        'label': control.lang(34134).encode('utf-8'),
        'path': '/account/profile/watched/list',
        'content': 'files',
        'art': {
            'thumb': FANART,
            'fanart': FANART,
        }
    }

    for item in response.get('menu', []):

        if item.get('children', []):
            yield {
                'handler': HANDLER,
                'method': 'get_channel_sub_category',
                'label': item.get('name'),
                'path': item.get('path'),
                'content': 'files',
                'art': {
                    'thumb': FANART,
                    'fanart': FANART,
                }
            }
        else:
            yield {
                'handler': HANDLER,
                'method': 'get_page',
                'label': item.get('name'),
                'path': item.get('path'),
                'content': 'files',
                'art': {
                    'thumb': FANART,
                    'fanart': FANART,
                }
            }


def get_channel_sub_category(label):
    if not label:
        return

    response = _get_navigation()

    children = next((child.get('children', []) for child in response.get('menu', []) if child.get('name', None) == label), {})

    for child in children:
        yield {
                'handler': HANDLER,
                'method': 'get_page',
                'label': child.get('name'),
                'path': child.get('path'),
                'content': 'files',
                'art': {
                    'thumb': FANART,
                    'fanart': FANART,
                }
            }


def get_page(path, absolute=False):

    control.log('get_page: %s' % path)

    if not path:
        return

    if path == '/account/profiles/mylist':
        path = '/account/profile/user-tracks'

    if path.startswith('/account/') or absolute:
        url = path
    else:
        url = '/pages?id=' + path

    use_pagination = control.setting('telecine_use_pagination') == 'true'

    while url:

        response = get_cached(BASE_URL + url)

        template = response.get('template', None)

        control.log('template: %s' % template)

        if not template or template == 'Cinelist':

            entry = next(iter(response.get('entries', [])), response)
            list = entry.get('list', response)

            # image_size = 'poster' if 'poster' in entry.get('template', 'poster').lower() else 'thumb'

            for item in list.get('items', []):

                category = item.get('category', '').split('/')
                has_category = category and len(category) == 3
                genre = category[0] if has_category else None
                subgenre = category[1] if has_category else None
                year = category[2] if has_category else None

                yield {
                    'handler': HANDLER,
                    'method': 'get_film' if item.get('path').startswith('/filme/') else 'get_page',
                    'id': item.get('id'),
                    'path': item.get('path'),
                    'label': item.get('name'),
                    'plot': item.get('mouseOverDescription', response.get('description', None)),
                    'genre': [genre, subgenre],
                    'year': year,
                    'overlay': 5 if item.get('percentWatched', 0) > 0.9 else 4,
                    'mediatype': 'movie' if item.get('originalImageUrl', None) else None,
                    'content': 'files' if not item.get('originalImageUrl', None) else None,
                    'art': {
                        'poster': item.get('originalImageUrl', FANART),
                        'thumb': FANART if not item.get('originalImageUrl', None) else None,
                        'fanart': FANART
                    },
                    'properties': {
                        'playcount': 1 if item.get('percentWatched', 0) > 0.9 else 0
                    }
                }

            url = list.get('paging', {}).get('next', None)

            if url and use_pagination:
                yield {
                    'handler': HANDLER,
                    'method': 'get_page',
                    'absolute': True,
                    'path': list.get('paging', {}).get('next', None),
                    'label': control.lang(34136).encode('utf-8'),
                    'art': {
                        'poster': NEXT_ICON,
                        'fanart': FANART
                    },
                    'properties': {
                        'SpecialSort': 'bottom'
                    }
                }
                url = None

        else:
            fanart = FANART
            for item in response.get('entries', []):

                list_type = item.get('type', None)

                if list_type in ['TextEntry', 'ImageEntry']:
                    fanart = item.get('originalImageUrl', FANART)
                    continue

                image_size = 'poster' if 'poster' in item.get('template', 'poster') else 'thumb'

                if list_type == 'UserEntry':
                    path = item.get('list', {}).get('paging', {}).get('next', None)
                else:
                    path = item.get('list', {}).get('path', None)

                yield {
                    'handler': HANDLER,
                    'method': 'get_page',
                    'path': path,
                    'label': item.get('title', item.get('text', '')) or control.lang(34132).encode('utf-8'),
                    'plot': response.get('description', None),
                    'content': 'files',
                    'art': {
                        image_size: item.get('originalImageUrl', FANART),
                        'fanart': item.get('originalImageUrl', fanart)
                    }
                }

            url = None


def get_film(path, overlay=4):

    if not path:
        return

    url = BASE_URL + '/movies?path=' + path

    item = get_cached(url)

    playable = True if not item.get('comingSoon', False) else False
    label = item.get('title', '') if playable else '%s - %s' % (control.lang(34133).encode('utf-8'), item.get('title', ''))
    film_item = {
        'path': item.get('moviePath'),
        'label': label,
        'title': item.get('title', ''),
        'plot': item.get('description', ''),
        'genre': [g.get('name') for g in item.get('genres', [])],
        'year': item.get('releaseYear', None),
        'userrating': float(item.get('averageUserRating', 0)) * 2,
        'votes': item.get('totalUserRatings', 0),
        'country': item.get('countries', '').split(', '),
        'cast': [c.get('name') for c in item.get('cast', [])],
        'director': item.get('director', {}).get('name', None),
        'mpaa': item.get('classificationCode', '').replace('CLASSIND-', '').replace('LI', 'L'),
        'tag': item.get('advisoryText', '').split(', '),
        'tagline': item.get('classificationTitle', None),
        'duration': int(item.get('length', '0').replace('minutos', '').strip()) * 60,
        'IsPlayable': playable,
        'overlay': overlay or 4,
        'mediatype': 'movie',
        'art': {
                'poster': item.get('posterOriginalImageUrl', None),
                'fanart': item.get('headerOriginalImageUrl', FANART)
            }
    }

    if playable:
        film_item.update({
            'handler': PLAYER_HANDLER,
            'method': 'playlive'
        })

    yield film_item

    for extra in item.get('entries', []):
        yield {
            'handler': HANDLER,
            'method': 'get_film_extra',
            'label': extra.get('title'),
            'path': path,
            'content': 'movies',
            'art': {
                'fanart': item.get('headerOriginalImageUrl', FANART)
            }
        }


def get_film_extra(path, label):

    if not path:
        return

    url = '/movies?path=' + path
    result = get_cached(BASE_URL + url)

    for extra in result.get('entries', []):

        if extra.get('title') == label:

            items = extra.get('list', {}).get('items', [])

            for item in items:

                is_film = item.get('path').startswith('/filme/')

                data = {
                    'handler': HANDLER,
                    'method': 'get_film' if is_film else 'get_page',
                    'path': item.get('path'),
                    'label': item.get('name'),
                    'plot': item.get('mouseOverDescription', '')
                }

                if is_film:
                    category = item.get('category', '').split('/')
                    genre = category[0]
                    subgenre = category[1]
                    year = category[2]

                    data.update({
                        'plot': item.get('mouseOverDescription', ''),
                        'genre': [genre, subgenre],
                        'year': year,
                        'content': 'movies',
                    })

                    data['art'] = {
                        'poster': item.get('originalImageUrl', None),
                        'fanart': result.get('headerOriginalImageUrl', FANART)
                    }

                else:
                    data.update({
                        'handler': PLAYER_HANDLER,
                        'method': 'playlive',
                        'IsPlayable': True
                    })
                    data['art'] = {
                        'thumb': item.get('originalImageUrl', None),
                        'fanart': result.get('headerOriginalImageUrl', FANART)
                    }

                yield data
