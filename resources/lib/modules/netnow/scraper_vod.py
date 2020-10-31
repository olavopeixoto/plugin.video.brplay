# -*- coding: utf-8 -*-
from auth import PLATFORM
from auth import get_request_data
import requests
import resources.lib.modules.control as control
from resources.lib.modules import cache
from resources.lib.modules import workers
import player

PLAYER_HANDLER = player.__name__


proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


class CATEGORIES:
    INICIO = u'INÍCIO'
    ESPECIAIS = u'ESPECIAIS E PROMOÇÕES'
    TV = u'PROGRAMAS DE TV'
    FILMES = u'FILMES'
    SERIES = u'SÉRIES'
    KIDS = u'KIDS'
    CLARO = u'CLARO VIDEO'
    CLUBE = u'NOW CLUBE'


CATEGORY_SLUG = {
    CATEGORIES.INICIO: 'home',
    CATEGORIES.ESPECIAIS: 'home-especiais-e-promocoes',
    CATEGORIES.TV: 'home-programas-de-tv',
    CATEGORIES.FILMES: 'home-cinema',
    CATEGORIES.SERIES: 'home-series',
    CATEGORIES.KIDS: 'home-kids',
    CATEGORIES.CLARO: 'home-clarovideo',
    CATEGORIES.CLUBE: 'home-now-clube'
}

CATEGORIES_HIDE = [
    'live',
    'categories',  # TODO
    'tv_channels'  # TODO
]

FANART = 'https://t2.tudocdn.net/391136'
THUMB = 'https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcScaBeflBdP6AdV246I7YtH6j9r997X39OeHg&usqp=CAU'


def get_channels():
    return [{
        'handler': __name__,
        'method': 'get_channel_categories',
        "label": 'Now Online',
        "adult": False,
        'art': {
            'thumb': THUMB,
            'fanart': FANART
        }
    }]


def get_channel_categories():
    categories = [
        CATEGORIES.INICIO,
        CATEGORIES.ESPECIAIS,
        CATEGORIES.TV,
        CATEGORIES.FILMES,
        CATEGORIES.SERIES,
        CATEGORIES.KIDS,
        CATEGORIES.CLARO,
        CATEGORIES.CLUBE,
    ]

    for category in categories:
        yield {
            'handler': __name__,
            'method': 'get_page',
            'category': category,
            'label': category,
            'art': {
                'thumb': THUMB,
                'fanart': FANART
            }
        }


def _get_page(category, validate=False):
    url = None

    slug = CATEGORY_SLUG.get(category, None)
    if slug:
        url = 'https://www.nowonline.com.br/avsclient/usercontent/categories/{slug}?channel={platform}'.format(platform=PLATFORM, slug=slug)

    if not url:
        control.log('NO CONTENT AVAILABLE FOR CATEGORY: %s' % category)
        return {}

    return request_logged_in(url, validate=validate)


def get_page(category):

    response = _get_page(category)

    response = response.get('response', {}) or {}

    if not response:
        response = _get_page(category, validate=True)
        response = response.get('response', {}) or {}
        if not response:
            return

    for item in response.get('categories', []):
        if item.get('type', '') not in CATEGORIES_HIDE:
            yield {
                'handler': __name__,
                'method': 'get_content',
                'category': category,
                'subcategory': item.get('title', '').encode('utf-8'),
                'label': item.get('title', '').encode('utf-8'),
                'art': {
                    'thumb': THUMB,
                    'fanart': FANART
                }
            }


def get_content(category, subcategory):

    response = _get_page(category)

    item = next((item for item in response.get('response', {}).get('categories', []) if item.get('title', '') == subcategory), {})

    if not item.get('contents', []):
        if item.get('type', None) == 'continue_watching':
            url = 'https://www.nowonline.com.br/AGL/1.0/R/ENG/{platform}/ALL/NET/USER/BOOKMARKS'.format(platform=PLATFORM)
            response = request_logged_in(url, False)
            contents = [result.get('content', {}) for result in response.get('resultObj', []) if result.get('content', {})]
        else:
            id = item.get('id', -1)
            url = 'https://www.nowonline.com.br/avsclient/categories/{id}/contents?offset=1&channel={platform}&limit=30'.format(platform=PLATFORM, id=id)
            response = request_logged_in(url)
            contents = response.get('response', {}).get('contents', [])
    else:
        contents = item.get('contents', [])

    threads = [{
                'thread': workers.Thread(_get_content, content.get('id', -1)),
                'id': content.get('id', -1)
                } for content in contents if content.get('type', '') in ['tvshow', 'movie', 'episode']]

    [i['thread'].start() for i in threads]
    [i['thread'].join() for i in threads]

    return [_hydrate_content(next((next(iter(t['thread'].get_result().get('response', [])), {}) for t in threads if t['id'] == content.get('id', -1)), content)) for content in contents]


def _get_content(id):
    url = 'https://www.nowonline.com.br/avsclient/contents?id={id}&include=images&include=details&include=adult&channel={platform}'.format(platform=PLATFORM, id=id)
    return request_logged_in(url)


def _hydrate_content(content):
    playable = content.get('type', '') == 'movie' or content.get('type', '') == "episode"
    return {
                'handler': PLAYER_HANDLER if playable else __name__,
                'method': 'playlive' if playable else 'get_seasons',
                'IsPlayable': playable,
                'id': content.get('id'),
                'label': content.get('title', ''),
                'title': content.get('title', ''),
                'mediatype': 'movie' if content.get('type', '') == 'movie' else 'episode' if content.get('type', '') == "episode" else 'tvshow',
                'plot': content.get('description', None),
                'plotoutline': content.get('description', None),
                'genre': content.get('genres', []),
                'year': content.get('releaseYear', None),
                'country': content.get('country', None),
                'director': content.get('directors', []),
                'cast': content.get('actors', []),
                'episode': content.get('episodeNumber', None),
                'season': content.get('seasonNumber', None),
                'duration': content.get('duration', None),
                'rating': content.get('averageRating', None),
                'userrating': content.get('userRating', None),
                'mpaa': content.get('ageRating', None),
                'encrypted': True,
                'trailer': content.get('trailerUri', None),
                'art': {
                    'thumb': content.get('images', {}).get('banner', None) if content.get('type', '') != "episode" else content.get('images', {}).get('coverLandscape', None),
                    'poster': content.get('images', {}).get('coverPortrait', None) if content.get('type', '') == 'movie' else None,
                    'fanart': content.get('images', {}).get('banner', None),
                    'clearlogo': content.get('tvChannel', {}).get('logo', None)
                }
            }


def get_seasons(id):

    control.log('get_seasons = %s' % id)

    content = next(iter(_get_content(id).get('response', [])), {})

    program = _hydrate_content(content)

    program['seasons'] = []

    seasons = content.get('seasons', [])

    for season in seasons:
        poster = content.get('images', {}).get('coverPortrait', None) if content.get('type', '') == 'movie' else content.get('images', {}).get('banner', None)

        yield {
            'handler': __name__,
            'method': 'get_episodes',
            'id': id,
            'season_number': season.get('seasonNumber', 0),
            'label': 'Temporada %s' % season.get('seasonNumber', 0),
            'title': 'Temporada %s' % season.get('seasonNumber', 0),
            'tvshowtitle': content.get('title', ''),
            'plot': content.get('description', None),
            'plotoutline': content.get('description', None),
            'genre': content.get('genres', []),
            'year': content.get('releaseYear', None),
            'country': content.get('country', None),
            'director': content.get('directors', []),
            'cast': content.get('actors', []),
            'episode': content.get('episodeNumber', None),
            'season': content.get('seasonNumber', None),
            'mpaa': content.get('ageRating', None),
            'mediatype': 'season',
            'content': 'seasons',
            'art': {
                'poster': poster,
                'fanart': content.get('images', {}).get('banner', None)
            }
        }


def get_episodes(id, season_number=None):
    control.log('get_episodes = %s | %s' % (id, season_number))

    content = next(iter(_get_content(id).get('response', [])), {})

    # program = _hydrate_content(content)

    episodes = next((season.get('episodes', []) for season in content.get('seasons', []) if str(season.get('seasonNumber', 0)) == str(season_number) or season_number is None), [])

    threads = [{
        'thread': workers.Thread(_get_content, content.get('id', -1)),
        'id': content.get('id', -1)
    } for content in episodes if content.get('id', -1) > 0]

    [i['thread'].start() for i in threads]
    [i['thread'].join() for i in threads]

    for eps in episodes:
        yield _hydrate_content(next((next(iter(t['thread'].get_result().get('response', [])), {}) for t in threads if t['id'] == eps.get('id', -1)), eps))


def request_logged_in(url, use_cache=True, validate=False):
    headers, cookies = get_request_data(validate)

    control.log('GET %s' % url)
    if use_cache:
        response = cache.get(requests.get, 1, url, headers=headers, cookies=cookies, table="netnow")
        if response.status_code >= 400:
            cache.clear(table="netnow")
    else:
        response = requests.get(url, headers=headers, cookies=cookies)

    response.raise_for_status()

    result = response.json()

    return result
