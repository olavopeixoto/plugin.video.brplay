import requests
from . import player
from resources.lib.modules import control
from resources.lib.modules import cache

LOGO = 'https://www.vixbrasiltv.com/tv/static/images/VIX_logos-01-min.f8b0d34.png'
LOGO2 = 'https://lh4.googleusercontent.com/qL_tD1g6eNEGy0dE-8VuVXl61SKI7P410TaFCzpJE5NnDCLRwGpWxpcV_ByXSwgXGVyhPNbm2PC9Oi_p-9-AKJbw9ZZybN1ZHo4Byh9mfrmBh67SChMdN8OP1zjNRPWaLg=w3997'
FANART = ''

PLAYER_HANDLER = player.__name__

proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


def get_channels():

    return [{
        'handler': __name__,
        'method': get_main_menu.__name__,
        'lang': get_language(),
        'label': 'VIX TV',
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }]


def get_main_menu(channel='Brazil', lang='pt'):

    yield {
        'handler': __name__,
        'method': get_home_highlights.__name__,
        'channel': channel,
        'lang': lang,
        'label': control.lang(34132),
        'art': {
            'icon': LOGO,
            'thumb': LOGO,
            'fanart': FANART
        }
    }

    if channel == 'Brazil':
        yield {
            'handler': __name__,
            'method': get_categories.__name__,
            'channel': channel,
            'lang': lang,
            'label': control.lang(34170),
            'art': {
                'icon': LOGO,
                'thumb': LOGO,
                'fanart': FANART
            }
        }

    yield from get_carousel(channel=channel, lang=lang)


def get_carousel(channel='Brazil', platform='webdesktop', page=1, lang='pt'):
    # https://api-edge.prod.gcp.vix.services/api/catalog/static/Mobile/carousel/62829fdafbf0c98ef776db0c/webdesktop/BR/pt/1
    # https://api-edge.prod.gcp.vix.services/api/catalog/static/Mobile/carousel/webdesktop/BR/pt/1
    url = 'https://api-edge.prod.gcp.vix.services/api/catalog/static/%s/carousel/%s/BR/%s/%s' % (channel, platform, lang, page)
    response = request_json(url)

    for item in response.get('data', []):
        yield {
            'handler': __name__,
            'method': get_carousel_item.__name__,
            'platform': platform,
            'channel': channel,
            'lang': lang,
            'item_id': item.get('id'),
            'label': item.get('title'),
            'art': {
                'icon': LOGO,
                'thumb': LOGO,
                'fanart': FANART
            },
            # 'sort': control.SORT_METHOD_LABEL
        }

    meta = response.get('meta', {}) or {}

    if (meta.get('totalPages', 0) or 0) > page:
        yield {
            'handler': __name__,
            'method': get_carousel.__name__,
            'label': '%s (%s)' % (control.lang(34136), page),
            'platform': platform,
            'channel': channel,
            'lang': lang,
            'page': page + 1,
            'art': {
                'icon': LOGO,
                'thumb': LOGO,
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_carousel_item(item_id, channel='Brazil', platform='webdesktop', lang='pt', page=1):
    url = 'https://api-edge.prod.gcp.vix.services/api/catalog/static/%s/carousel/%s/%s/BR/%s/%s' % (channel, item_id, platform, lang, page)
    response = request_json(url)

    for item in response.get('data', []) or []:

        show = item.get('show', {}) or {}

        is_playable = not show.get('isEpisodic')
        handler = PLAYER_HANDLER if is_playable else __name__
        method = player.Player.playlive.__name__ if is_playable else get_seasons.__name__

        yield {
            'handler': handler,
            'method': method,
            'IsPlayable': is_playable,
            'channel': channel,
            'platform': platform,
            'lang': lang,
            'media_key': show.get('mediaKey'),
            'label': show.get('title'),
            'title': show.get('title'),
            'plot': show.get('summary'),
            'genre': show.get('genre', '').split(' | '),
            'year': show.get('year'),
            'episode': show.get('episodesTotal'),
            'season': show.get('seasonsTotal'),
            'mpaa': item.get('formattedRating'),
            'duration': show.get('runningTimeSeconds', 0),
            'cast': list(flatten_cast(show.get('cast', []) or [])),
            'writer': list(flatten_cast(show.get('writer', []) or [])),
            'mediatype': 'movie' if show.get('categoryKey') == 'movies' else 'tvshow',  # 'mediatype': "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            'art': {
                'thumb': show.get('posterUrlLandscape'),
                'poster': show.get('posterUrlPortrait'),
                'fanart': show.get('showUrlBackground'),
                'banner': item.get('heroUrlBackground')
            }
        }

    meta = response.get('meta', {}) or {}

    if (meta.get('totalPages', 0) or 0) > page:
        yield {
            'handler': __name__,
            'method': get_carousel_item.__name__,
            'label': '%s (%s)' % (control.lang(34136), page),
            'item_id': item_id,
            'channel': channel,
            'platform': platform,
            'lang': lang,
            'page': page + 1,
            'art': {
                'icon': LOGO,
                'thumb': LOGO,
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_categories(page=1, channel='Brazil', platform='webdesktop', lang='pt'):
    url = 'https://api-edge.prod.gcp.vix.services/api/catalog/static/%s/category/%s/BR/%s/%s' % (channel, platform, lang, page)
    response = request_json(url)
    data = response.get('data', []) or []

    for item in data:
        yield {
            'handler': __name__,
            'method': get_home_category.__name__,
            'channel': item.get('channelPlatform'),
            'platform': platform,
            'lang': lang,
            'item_id': item.get('key'),
            'label': item.get('title'),
            'plot': item.get('description'),
            'art': {
                'icon': LOGO,
                'thumb': item.get('iconSrc') or LOGO,
                'fanart': FANART
            }
        }

    meta = response.get('meta', {}) or {}

    if (meta.get('totalPages', 0) or 0) > page:
        yield {
            'handler': __name__,
            'method': get_categories.__name__,
            'label': '%s (%s)' % (control.lang(34136), page),
            'channel': channel,
            'platform': platform,
            'lang': lang,
            'page': page + 1,
            'art': {
                'icon': LOGO,
                'thumb': LOGO,
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_home_category(item_id, channel, platform='webdesktop', lang='pt'):

    if channel and channel != 'Brazil':
        yield from get_main_menu(channel, lang)

        yield {
            'handler': __name__,
            'method': get_category.__name__,
            'channel': channel,
            'platform': platform,
            'lang': lang,
            'item_id': item_id,
            'label': control.lang(34171),
            'art': {
                'icon': LOGO,
                'thumb': LOGO,
                'fanart': FANART
            }
        }

    else:
        yield from get_category(item_id, channel, 1, platform, lang)


def get_category(item_id, channel, page=1, platform='webdesktop', lang='pt'):

    url = 'https://api-edge.prod.gcp.vix.services/api/catalog/static/Brazil/category/%s/%s/BR/%s/%s' % (item_id, platform, lang, page)
    response = request_json(url)

    for item in response.get('data', []) or []:

        show = item.get('show', {}) or {}

        is_playable = not show.get('isEpisodic')
        handler = PLAYER_HANDLER if is_playable else __name__
        method = player.Player.playlive.__name__ if is_playable else get_seasons.__name__

        yield {
            'handler': handler,
            'method': method,
            'IsPlayable': is_playable,
            'channel': channel,
            'platform': platform,
            'lang': lang,
            'media_key': show.get('mediaKey'),
            'label': show.get('title'),
            'title': show.get('title'),
            'plot': show.get('summary'),
            'genre': show.get('genre', '').split(' | '),
            'year': show.get('year'),
            'episode': show.get('episodesTotal'),
            'season': show.get('seasonsTotal'),
            'mpaa': show.get('formattedRating'),
            'duration': show.get('runningTimeSeconds', 0),
            'cast': list(flatten_cast(show.get('cast', []) or [])),
            'writer': list(flatten_cast(show.get('writer', []) or [])),
            'mediatype': 'movie' if show.get('categoryKey') == 'movies' else 'tvshow',  # 'mediatype': "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            'art': {
                'thumb': show.get('posterUrlLandscape'),
                'poster': show.get('posterUrlPortrait'),
                'fanart': show.get('showUrlBackground'),
                'banner': item.get('heroUrlBackground')
            }
        }

    meta = response.get('meta', {}) or {}

    if (meta.get('totalPages', 0) or 0) > page:
        yield {
            'handler': __name__,
            'method': get_category.__name__,
            'label': '%s (%s)' % (control.lang(34136), page),
            'channel': channel,
            'platform': platform,
            'item_id': item_id,
            'lang': lang,
            'page': page + 1,
            'art': {
                'icon': LOGO,
                'thumb': LOGO,
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_home_highlights(page=1, channel='Brazil', platform='webdesktop', lang='pt'):
    url = 'https://api-edge.prod.gcp.vix.services/api/catalog/static/%s/hero/%s/BR/%s/%s' % (channel, platform, lang, page)
    response = request_json(url)

    for item in response.get('data', []) or []:

        show = item.get('show', {}) or {}

        is_playable = not show.get('isEpisodic')
        handler = PLAYER_HANDLER if is_playable else __name__
        method = player.Player.playlive.__name__ if is_playable else get_seasons.__name__

        yield {
            'handler': handler,
            'method': method,
            'IsPlayable': is_playable,
            'channel': channel,
            'platform': platform,
            'lang': lang,
            'media_key': show.get('mediaKey'),
            'label': show.get('title'),
            'title': show.get('title'),
            'plot': show.get('summary'),
            'genre': show.get('genre', '').split(' | '),
            'year': show.get('year'),
            'episode': show.get('episodesTotal'),
            'season': show.get('seasonsTotal'),
            'mpaa': show.get('formattedRating'),
            'duration': show.get('runningTimeSeconds', 0),
            'cast': list(flatten_cast(show.get('cast', []) or [])),
            'writer': list(flatten_cast(show.get('writer', []) or [])),
            'mediatype': 'movie' if show.get('categoryKey') == 'movies' else 'tvshow',  # 'mediatype': "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            'art': {
                'thumb': show.get('posterUrlLandscape'),
                'poster': show.get('posterUrlPortrait'),
                'fanart': show.get('showUrlBackground'),
                'banner': item.get('heroUrlBackground')
            }
        }

    meta = response.get('meta', {}) or {}

    if (meta.get('totalPages', 0) or 0) > page:
        yield {
            'handler': __name__,
            'method': get_categories.__name__,
            'label': '%s (%s)' % (control.lang(34136), page),
            'channel': channel,
            'platform': platform,
            'lang': lang,
            'page': page + 1,
            'art': {
                'icon': LOGO,
                'thumb': LOGO,
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_seasons(media_key, platform='webdesktop', lang='pt'):
    url = 'https://api-edge.prod.gcp.vix.services/api/catalog/static/show/%s/%s/BR/%s/metadata' % (media_key, platform, lang)
    response = request_json(url)

    data = response.get('data', {}) or {}

    seasons = data.get('seasons', []) or []

    if len(seasons) == 1:
        yield from get_episodes(data.get('mediaKey'), seasons[0].get('id'))
        return

    for season in seasons:
        yield {
            'handler': __name__,
            'method': get_episodes.__name__,
            'platform': platform,
            'lang': lang,
            'media_key': data.get('mediaKey'),
            'label': '%s %s' % (control.lang(34137), season.get('id')),
            'title': data.get('title'),
            'plot': data.get('summary'),
            'genre': data.get('genre', '').split(' | '),
            'year': data.get('year'),
            'mpaa': data.get('formattedRating'),
            'season': season.get('id'),
            'mediatype': 'season',
            'art': {
                'thumb': data.get('posterUrlLandscape'),
                'poster': data.get('posterUrlPortrait'),
                'fanart': data.get('showUrlBackground'),
            }
        }


def get_episodes(media_key, season, platform='webdesktop', lang='pt'):
    url = 'https://api-edge.prod.gcp.vix.services/api/catalog/static/show/%s/%s/BR/%s/metadata' % (media_key, platform, lang)
    response = request_json(url)

    data = response.get('data', {}) or {}

    for episode in data.get('episodes', []) or []:
        if episode.get('season') != season:
            continue

        yield {
            'handler': PLAYER_HANDLER,
            'method': player.Player.playlive.__name__,
            'IsPlayable': True,
            'media_key': episode.get('mediaKey'),
            'label': episode.get('title'),
            'title': episode.get('title'),
            'plot': episode.get('summary'),
            'genre': data.get('genre', '').split(' | '),
            'year': data.get('year'),
            'mpaa': data.get('formattedRating'),
            'season': season,
            'episode': episode.get('number'),
            'mediatype': 'episode',
            'art': {
                'thumb': episode.get('thumbUrlLandscape'),
                'poster': data.get('posterUrlPortrait'),
                'fanart': episode.get('thumbUrlBackground'),
            }
        }


def flatten_cast(cast_matrix):
    for item in cast_matrix:
        for cast in item.split(', '):
            yield cast


def request_json(url):
    control.log('GET %s' % url)
    return cache.get(requests.get, 4, url, proxies=proxy, table='vix').json()


def get_language():
    lang = control.getLanguage().lower()
    control.log('Kodi Language: %s' % lang)
    if lang.startswith('english'):
        control.log('VIX Language: en')
        return 'en'

    control.log('VIX Language: pt')
    return 'pt'
