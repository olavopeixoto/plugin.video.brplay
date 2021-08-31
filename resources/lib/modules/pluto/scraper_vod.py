import requests
import uuid
from resources.lib.modules import control
from resources.lib.modules import cache


LOGO = 'https://is4-ssl.mzstatic.com/image/thumb/Purple114/v4/a8/8c/b1/a88cb1bc-14f1-7b33-c43a-07f3b19bb7d8/AppIcon-1x_U007emarketing-5-0-85-220.png/1200x630bb.png'
# LOGO = 'https://www.cordcuttersnews.com/wp-content/uploads/2019/11/PlutoTV_Logo_Transparent_1200x670.png'
# LOGO = 'https://d2suv5gemfchwa.cloudfront.net/assets/images/logos/apps/transparent/padded/pluto_tv_new.png'
FANART = 'https://static.wixstatic.com/media/3a4b66_bc8636cb769449b0ad87454171c9cef8~mv2.png/v1/fill/w_1280,h_720,al_c/3a4b66_bc8636cb769449b0ad87454171c9cef8~mv2.png'
# FANART = 'https://variety.com/wp-content/uploads/2020/02/pluto-tv.png'


proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


def get_channels():
    return [{
        'handler': __name__,
        'method': get_main_menu.__name__,
        'label': 'Pluto TV',
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }]


def get_main_menu():
    url = 'https://api.pluto.tv/v3/vod/categories?includeItems=false&deviceType=web&sid=1&deviceId=1'
    response = request_json(url)

    for genre in response.get('categories', []):
        yield {
            'handler': __name__,
            'method': open_category.__name__,
            'id': genre.get('_id'),
            'label': genre.get('name'),
            'art': {
                'icon': LOGO,
                'thumb': LOGO,
                'fanart': FANART
            },
            # 'sort': control.SORT_METHOD_LABEL
        }


def open_category(id):
    sid = control.setting('pluto_sid')
    if not sid:
        sid = str(uuid.uuid4())
        control.setSetting('pluto_sid', sid)
    did = control.setting('pluto_did')
    if not did:
        did = str(uuid.uuid4())
        control.setSetting('pluto_did', did)

    url = 'https://api.pluto.tv/v3/vod/categories?includeItems=true&deviceType=web&sid=%s&deviceId=%s' % (sid, did)
    response = request_json(url)

    category = next((c for c in response.get('categories', []) if c.get('_id') == id), {})

    for item in category.get('items', []):

        thumb = next((c.get('url') for c in item.get('covers', []) if c.get('aspectRatio') == '16:9'), None) or FANART
        poster = next((c.get('url') for c in item.get('covers', []) if c.get('aspectRatio') == '347:500'), None)

        if item.get('type') == 'movie':
            url = next((url.get('url') for url in item.get('stitched', {}).get('urls') if url.get('type') == 'hls'), '')
            url = url.replace('deviceType=&', 'deviceType=web&').replace('deviceMake=&', 'deviceMake=Chrome&').replace('deviceModel=&', 'deviceModel=Chrome&').replace('appName=&', 'appName=web&')

            yield {
                'url': url,
                'IsPlayable': True,
                'label': item.get('name'),
                'plot': item.get('description'),
                'duration': item.get('allotment'),
                'rating': item.get('rating'),
                'genre': item.get('genre'),
                'mediatype': 'movie',  # 'mediatype': "video", "movie", "tvshow", "season", "episode" or "musicvideo"
                'art': {
                    'thumb': thumb,
                    'poster': poster,
                    'fanart': thumb
                }
            }

        else:
            yield {
                'handler': __name__,
                'method': get_series.__name__,
                'id': item.get('_id'),
                'label': item.get('name'),
                'tvshowtitle': item.get('name'),
                'plot': item.get('description'),
                'rating': item.get('rating'),
                'genre': item.get('genre'),
                'mediatype': 'tvshow',  # 'mediatype': "video", "movie", "tvshow", "season", "episode" or "musicvideo"
                'art': {
                    'thumb': thumb,
                    'poster': poster,
                    'fanart': thumb
                }
            }


def get_series(id):
    sid = control.setting('pluto_sid')
    if not sid:
        sid = str(uuid.uuid4())
        control.setSetting('pluto_sid', sid)

    url = 'https://api.pluto.tv/v3/vod/series/{series_id}/seasons?includeItems=true&deviceType=web&sid={sid}'.format(series_id=id, sid=sid)
    response = request_json(url)

    seasons = response.get('seasons', [])

    if len(seasons) == 1:
        return get_season(id, seasons[0]['number'])

    return hydrate_seasons(response, seasons)


def hydrate_seasons(response, seasons):
    thumb = response.get('featuredImage', {}).get('path')
    poster = next((c.get('url') for c in response.get('covers', []) if c.get('aspectRatio') == '347:500'), None)

    for season in seasons:
        yield {
            'handler': __name__,
            'method': get_season.__name__,
            'id': response.get('_id'),
            'label': '%s %s' % (control.lang(34137), season.get('number')),
            'tvshowtitle': response.get('name'),
            'plot': response.get('description'),
            'rating': response.get('rating'),
            'genre': response.get('genre'),
            'season': season.get('number'),
            'mediatype': 'season',  # 'mediatype': "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            'art': {
                'thumb': thumb,
                'poster': poster,
                'fanart': thumb
            }
        }


def get_season(id, season):
    sid = control.setting('pluto_sid')
    if not sid:
        sid = str(uuid.uuid4())
        control.setSetting('pluto_sid', sid)

    url = 'https://api.pluto.tv/v3/vod/series/{series_id}/seasons?includeItems=true&deviceType=web&sid={sid}'.format(series_id=id, sid=sid)
    response = request_json(url)

    fanart = response.get('featuredImage', {}).get('path')
    poster = next((c.get('url') for c in response.get('covers', []) if c.get('aspectRatio') == '347:500'), None)

    season_episodes = next((s for s in response.get('seasons', []) if s.get('number') == season), {})

    for episode in season_episodes.get('episodes', []):
        url = next((url.get('url') for url in episode.get('stitched', {}).get('urls') if url.get('type') == 'hls'), '')
        url = url.replace('deviceType=&', 'deviceType=web&').replace('deviceMake=&', 'deviceMake=Chrome&').replace('deviceModel=&', 'deviceModel=Chrome&').replace('appName=&', 'appName=web&')

        thumb = next((c.get('url') for c in episode.get('covers', []) if c.get('aspectRatio') == '16:9'), None)

        yield {
            'url': url,
            'IsPlayable': True,
            'tvshowtitle': response.get('name'),
            'label': episode.get('name'),
            'title': episode.get('name'),
            'plot': episode.get('description'),
            'rating': episode.get('rating'),
            'genre': episode.get('genre'),
            'duration': episode.get('allotment'),
            'episode': episode.get('number'),
            'season': episode.get('season'),
            'mediatype': 'episode',  # 'mediatype': "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            'art': {
                'thumb': thumb,
                'poster': poster,
                'fanart': fanart
            }
        }


def request_json(url):
    return cache.get(requests.get, 4, url, proxies=proxy, table='pluto').json()
