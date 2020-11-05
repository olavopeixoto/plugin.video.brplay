import requests
from resources.lib.modules import control
from resources.lib.modules import cache
import os
from auth import gettoken, get_default_profile
from private_data import get_device_id
import urllib
from collections import OrderedDict
import player
import json
import traceback

FANART = os.path.join(control.artPath(), 'fanart_oi.jpg')
LOGO = os.path.join(control.artPath(), 'logo_oiplay.png')
FAVORITES = os.path.join(control.artPath(), 'favorites.png')


PLAYER_HANDLER = player.__name__


def get_channels():

    return [{
        'handler': __name__,
        'method': 'get_main_menu',
        'label': 'Oi Play',
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }]


def get_main_menu_url():

    catalog, version = get_catalog()
    qs = OrderedDict({
        'catalogid': catalog,
        'versionId': version,
        'maxRating': 18,
        'useragent': 'web'
    })
    return 'https://apim.oi.net.br/app/oiplay/ummex/v1/menu?{qs}'.format(qs=urllib.urlencode(qs))


def get_main_menu():
    url = get_main_menu_url()
    menu = request_cached(url)

    for item in menu:
        if item.get('itemType') in ['Home', 'Categories'] and item.get('title') not in ['Pra Alugar']:

            yield {
                'handler': __name__,
                'method': 'get_home',
                'label': item.get('title'),
                'id': item.get('id'),
                'art': {
                    'thumb': LOGO,
                    'fanart': FANART
                }
            }


def get_home(id):
    url = get_main_menu_url()
    menu = request_cached(url)

    for item in menu:
        if item.get('id') == id:
            for content in item.get('contentLists', []):
                if content.get('listType') not in ['LiveChannels', 'Applications']:
                    method = 'get_list' if content.get('listType') != 'Bookmarks' else 'get_bookmarks'
                    yield {
                        'handler': __name__,
                        'method': method,
                        'label': content.get('title'),
                        'menu_id': id,
                        'id': content.get('id'),
                        'art': {
                            'thumb': LOGO,
                            'fanart': FANART
                        }
                    }

            for child in item.get('childItems', []):
                if child.get('title') not in ['Ao Vivo']:
                    yield {
                        'handler': __name__,
                        'method': 'open_menu',
                        'label': child.get('title'),
                        'id': child.get('id'),
                        'art': {
                            'thumb': LOGO,
                            'fanart': FANART
                        }
                    }


def open_menu(id):
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/menu/{id}?maxRating=18'.format(id=id)
    response = request_cached(url)

    if response:
        hosts = get_subscribed_host_ids()
        for item in response:
            #any(container in source["url"] for source in response['resource']['sources']):
            if not item.get('items'):
                continue

            has_item = False
            for sub_item in item.get('items'):
                provider = next((cp for cp in sub_item.get('contentProviders', []) if cp.get('hostId') in hosts), {})
                if provider:
                    has_item = True
                    break

            if not has_item:
                continue

            yield {
                'handler': __name__,
                'method': 'open_menu_item',
                'label': item.get('title'),
                'menu_id': id,
                'id': item.get('id'),
                'art': {
                    'thumb': LOGO,
                    'fanart': FANART
                }
            }


def open_menu_item(menu_id, id):
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/menu/{id}?maxRating=18'.format(id=menu_id)
    response = request_cached(url)
    if response:
        hosts = get_subscribed_host_ids()
        for menu in response:
            if menu.get('id') == id:

                for item in menu.get('items', []) or []:

                    provider = next((cp for cp in item.get('contentProviders', []) if cp.get('hostId') in hosts), {})
                    if not provider:
                        continue

                    yield {
                        'handler': __name__,
                        'method': 'get_content',
                        'id': item.get('tmsId'),
                        'label': item.get('title'),
                        'title': item.get('title'),
                        'tvshowtitle': item.get('seriesTitle'),
                        'plot': item.get('synopsis'),
                        'genre': item.get('genres'),
                        'year': item.get('releaseYear'),
                        'episode': item.get('episodeNumber'),
                        'season': item.get('seasonNumber'),
                        'mpaa': item.get('rating'),
                        'duration': item.get('durationInSeconds', 0),
                        'setCast': [{
                            'name': cast.get('name'),
                            'thumbnail': cast.get('photoUrl'),
                        } for cast in item.get('castMembers', [])],
                        'directors': item.get('directors'),
                        'playType': item.get('playType'),
                        'adult': item.get('isAdult'),
                        'mediatype': 'movie' if item.get('itemType') == 'Movie' else 'tvshow' if item.get('itemType') == 'Serie' else 'video',
                        'art': {
                            'thumb': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Thumbnail'), LOGO),
                            'fanart': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Backdrop'), FANART),
                        }
                    }


def get_home_item(menu_id, id):
    url = get_main_menu_url()
    menu = request_cached(url)

    for menu_item in menu:
        if menu_item.get('id') == menu_id:
            for content in menu_item.get('contentLists', []):
                if content.get('id') == id:
                    for item in content.get('items'):
                        yield {
                            'handler': __name__,
                            'method': 'get_home_item',
                            'tmdId': item.get('tmsId'),
                            'id': item.get('id'),
                            'label': item.get('title'),
                            'title': item.get('title'),
                            'tvshowtitle': item.get('seriesTitle'),
                            'plot': item.get('synopsis'),
                            'genre': item.get('genres'),
                            'year': item.get('releaseYear'),
                            'episode': item.get('episodeNumber'),
                            'season': item.get('seasonNumber'),
                            'mpaa': item.get('rating'),
                            'duration': item.get('durationInSeconds', 0),
                            'playType': item.get('playType'),
                            'mediatype': 'movie' if item.get('itemType') == 'Movie' else 'tvshow' if item.get('itemType') == 'Serie' else 'video',
                            'art': {
                                'thumb': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Thumbnail'), LOGO),
                                'fanart': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Backdrop'), FANART),
                            }
                        }


def get_list(id, page=1, page_size=50):

    qs = {
        'limit': page_size,
        'maxRating': 18,
        'offerids': urllib.quote_plus(','.join(get_offers())),
        'orderby': 'titleAsc',  # DateDesc
        'page': page
    }

    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/lists/{id}?{query}'.format(id=id, query=urllib.urlencode(qs))
    response = request_cached(url)

    hosts = get_subscribed_host_ids()

    for item in response.get('items', []):
        provider = next((cp for cp in item.get('contentProviders', []) if cp.get('hostId') in hosts), {})
        if not provider:
            continue

        yield {
            'handler': __name__,
            'method': 'get_content',
            'id': item.get('tmsId'),
            'label': item.get('title'),
            'title': item.get('title'),
            'tvshowtitle': item.get('seriesTitle'),
            'plot': item.get('synopsis'),
            'genre': item.get('genres'),
            'year': item.get('releaseYear'),
            'episode': item.get('episodeNumber'),
            'season': item.get('seasonNumber'),
            'mpaa': item.get('rating'),
            'duration': item.get('durationInSeconds', 0),
            'setCast': [{
                            'name': cast.get('name'),
                            'thumbnail': cast.get('photoUrl'),
                        } for cast in item.get('castMembers', [])],
            'directors': item.get('directors'),
            'playType': item.get('playType'),
            'adult': item.get('isAdult'),
            'mediatype': 'movie' if item.get('itemType') == 'Movie' else 'tvshow' if item.get('itemType') == 'Serie' else 'video',
            'art': {
                'thumb': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Thumbnail'), LOGO),
                'fanart': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Backdrop'), FANART),
            }
        }

    if len(response.get('items', [])) >= page_size:
        yield {
            'handler': __name__,
            'method': 'get_list',
            'id': id,
            'page': page + 1,
            'label': control.lang(34136).encode('utf-8'),
            'art': {
                'poster': control.addonNext(),
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_content(id):

    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/programs/' + id
    item = request_cached(url) or {}

    if item:
        hosts = get_subscribed_host_ids()
        provider = next((cp for cp in item.get('contentProviders', []) if cp.get('hostId') in hosts), {})
        playable = True if provider and item.get('itemType') != 'Serie' else False
        provider_id = provider.get('hostId')

        fanart = next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Backdrop'), FANART)

        liked = is_content_liked(id)

        cm = []
        if liked is True or liked is None:
            cm_label = control.lang(34146).encode('utf-8') if liked is True else control.lang(34144).encode('utf-8')
            cm.append((cm_label, control.run_plugin_url({
                'action': 'generic',
                'meta': json.dumps({
                    'handler': __name__,
                    'method': 'like_content',
                    'id': item.get('tmsId'),
                    'like': True
                })
            })))
        if liked is False or liked is None:
            cm_label = control.lang(34145).encode('utf-8') if liked is False else control.lang(34143).encode('utf-8')
            cm.append((cm_label, control.run_plugin_url({
                'action': 'generic',
                'meta': json.dumps({
                    'handler': __name__,
                    'method': 'like_content',
                    'id': item.get('tmsId'),
                    'like': False
                })
            })))

        handler = __name__ if item.get('itemType') == 'Serie' else PLAYER_HANDLER
        method = 'get_seasons' if item.get('itemType') == 'Serie' else 'playlive'

        yield {
            'handler': handler,
            'method': method,
            'IsPlayable': playable,
            'id': item.get('tmsId'),
            'provider': provider_id,
            'serie': item.get('seriesId'),
            'studio': provider.get('name'),
            'label': item.get('title'),
            'title': item.get('title'),
            'tvshowtitle': item.get('seriesTitle'),
            'plot': item.get('synopsis'),
            'tagline': item.get('ratingWarning'),
            'genre': item.get('genres'),
            'year': item.get('releaseYear'),
            'episode': item.get('episodeNumber'),
            'season': item.get('seasonNumber'),
            'mpaa': item.get('rating'),
            'duration': item.get('durationInSeconds', 0),
            'setCast': [{
                'name': cast.get('name'),
                'thumbnail': cast.get('photoUrl'),
            } for cast in item.get('castMembers', [])],
            'directors': item.get('directors'),
            'playType': item.get('playType'),
            'adult': item.get('isAdult'),
            'context_menu': cm,
            'mediatype': 'movie' if item.get('itemType') == 'Movie' else 'tvshow' if item.get('itemType') == 'Serie' else 'episode' if item.get('itemType') == 'SerieEpisode' else 'video',
            'art': {
                'thumb': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Thumbnail'), LOGO),
                'fanart': fanart
            },
            'properties': {
                'liked': liked is True,
                'disliked': liked is False
            }
        }

        yield {
            'handler': __name__,
            'method': 'get_content_recommendations',
            'id': id,
            'label': control.lang(34142).encode('utf-8'),
            'art': {
                'poster': FAVORITES,
                'fanart': fanart
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_seasons(serie, art=None):
    art = art or {}

    offer_ids = get_offers()
    params = {
        'offerids': ','.join(offer_ids)
    }
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/series/{serie}/seasons?{qs}'.format(serie=serie, qs=urllib.urlencode(params))
    response = request_cached(url)

    if response and len(response) == 1:
        item = response[0]
        return get_episodes(serie, item.get('seasonId'), art)

    return _get_seasons(response, serie, art)


def _get_seasons(seasons, serie, art):

    for item in seasons:
        yield {
            'handler': __name__,
            'method': 'get_episodes',
            'label': '%s %s' % (control.lang(34137).encode('utf-8'), item.get('title')),
            'serie': serie,
            'season': item.get('seasonId'),
            'mediatype': 'season',
            'art': art
        }


def get_episodes(serie, season, art=None):
    art = art or {}

    offer_ids = get_offers()
    params = {
        'offerids': ','.join(offer_ids)
    }
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/series/{serie}/seasons/{season}/episodes?{qs}'.format(serie=serie, season=season, qs=urllib.urlencode(params))
    response = request_cached(url)

    hosts = get_subscribed_host_ids()

    for item in response:
        provider = next((cp for cp in item.get('contentProviders', []) if cp.get('hostId') in hosts), {})
        provider_id = provider.get('hostId')

        fanart = art.get('fanart') or next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Backdrop'), FANART)

        yield {
            'handler': __name__,
            'method': 'get_content',
            'id': item.get('tmsId'),
            'provider': provider_id,
            'studio': provider.get('name'),
            'label': item.get('title'),
            'title': item.get('title'),
            'tvshowtitle': item.get('seriesTitle'),
            'plot': item.get('synopsis'),
            'tagline': item.get('ratingWarning'),
            'genre': item.get('genres'),
            'year': item.get('releaseYear'),
            'episode': item.get('episodeNumber'),
            'season': item.get('seasonNumber'),
            'mpaa': item.get('rating'),
            'duration': item.get('durationInSeconds', 0),
            'setCast': [{
                'name': cast.get('name'),
                'thumbnail': cast.get('photoUrl'),
            } for cast in item.get('castMembers', [])],
            'directors': item.get('directors'),
            'adult': item.get('isAdult'),
            'mediatype': 'episode',
            'sort': control.SORT_METHOD_EPISODE,
            'art': {
                'thumb': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Thumbnail'), LOGO),
                'fanart': fanart
            }
        }


def get_content_recommendations(id):
    token, account = gettoken()
    device_id = get_device_id()
    profile = get_default_profile(account, device_id, token)

    url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/media/accounts/{account}/profiles/{profile}/recommendations/content/{id}/list'.format(account=account, profile=profile, id=id)
    response = request_cached(url) or []

    for item in response:
        yield {
            'handler': __name__,
            'method': 'get_content',
            'id': item.get('tmsId'),
            'label': item.get('title'),
            'title': item.get('title'),
            'tvshowtitle': item.get('seriesTitle'),
            'plot': item.get('synopsis'),
            'genre': item.get('genres'),
            'year': item.get('releaseYear'),
            'episode': item.get('episodeNumber'),
            'season': item.get('seasonNumber'),
            'mpaa': item.get('rating'),
            'duration': item.get('durationInSeconds', 0),
            'setCast': [{
                'name': cast.get('name'),
                'thumbnail': cast.get('photoUrl'),
            } for cast in item.get('castMembers', [])],
            'directors': item.get('directors'),
            'playType': item.get('playType'),
            'adult': item.get('isAdult'),
            'mediatype': 'movie' if item.get('itemType') == 'Movie' else 'tvshow' if item.get('itemType') == 'Serie' else 'video',
            'art': {
                'thumb': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Thumbnail'), LOGO),
                'fanart': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Backdrop'), FANART),
            }
        }


def is_content_liked(id):
    token, account = gettoken()
    device_id = get_device_id()
    profile = get_default_profile(account, device_id, token)

    url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/users/accounts/{account}/profiles/{profile}/likes/{id}/get'.format(account=account, profile=profile, id=id)
    response = request_cached(url, force_refresh=True) or {}

    return True if response.get('name') == 'Like' else False if response.get('name') == 'Dislike' else None


def get_bookmarks():
    token, account = gettoken()
    device_id = get_device_id()
    profile = get_default_profile(account, device_id, token)

    url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/media/accounts/{account}/profiles/{profile}/bookmarks/list'.format(account=account, profile=profile)

    response = request_cached(url, force_refresh=True) or []

    for bookmark in response:
        item = bookmark.get('cmsContentItem', {})
        yield {
            'handler': __name__,
            'method': 'get_content',
            'id': item.get('tmsId'),
            'label': item.get('title'),
            'title': item.get('title'),
            'tvshowtitle': item.get('seriesTitle'),
            'plot': item.get('synopsis'),
            'genre': item.get('genres'),
            'year': item.get('releaseYear'),
            'episode': item.get('episodeNumber'),
            'season': item.get('seasonNumber'),
            'mpaa': item.get('rating'),
            'duration': item.get('durationInSeconds', 0),
            'setCast': [{
                            'name': cast.get('name'),
                            'thumbnail': cast.get('photoUrl'),
                        } for cast in item.get('castMembers', [])],
            'directors': item.get('directors'),
            'playType': item.get('playType'),
            'adult': item.get('isAdult'),
            'mediatype': 'movie' if item.get('itemType') == 'Movie' else 'tvshow' if item.get('itemType') == 'Serie' else 'video',
            'art': {
                'thumb': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Thumbnail'), LOGO),
                'fanart': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Backdrop'), FANART),
            },
            'properties': {
                'resumetime': str(bookmark.get('bookmarkPosition', 0) / 1000)
            }
        }


def like_content(id, like=True):
    token, account = gettoken()
    device_id = get_device_id()
    profile = get_default_profile(account, device_id, token)

    operation = 'like' if like else 'dislike'
    url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/users/accounts/{account}/profiles/{profile}/likes/{operation}'.format(account=account, profile=profile, operation=operation)
    headers = {
        'Authorization': 'Bearer %s' % token,
        'Accept': 'application/json',
        'X-Forwarded-For': '189.1.125.97',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
    }
    data = {
        'tmsId': id
    }
    control.log('POST %s' % url)
    control.log(data)
    response = requests.post(url, json=data, headers=headers)
    control.log(response.status_code)
    control.log(response.content)

    response = response.json()
    return True if response.get('name') == 'Like' else False if response.get('name') == 'Dislike' else None


def search(term, page=1, limit=20):
    params = {
        'q': term,
        'orderby': 'DateDescending',
        'page': page,
        'limit': limit,
        'offerids': urllib.quote_plus(','.join(get_offers())),
        'maxRating': 18
    }
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/search?%s' % urllib.urlencode(params)

    try:
        response = request_cached(url) or []
    except:
        control.log(traceback.format_exc(), control.LOGERROR)
        response = []

    hosts = get_subscribed_host_ids()

    for item in response:
        provider = next((cp for cp in item.get('contentProviders', []) if cp.get('hostId') in hosts), {})
        if not provider:
            continue

        yield {
            'handler': __name__,
            'method': 'get_content',
            'id': item.get('tmsId'),
            'studio': u'Oi Play',
            'label': item.get('title'),
            'title': item.get('title'),
            'tvshowtitle': item.get('seriesTitle'),
            'plot': item.get('synopsis'),
            'genre': item.get('genres'),
            'year': item.get('releaseYear'),
            'episode': item.get('episodeNumber'),
            'season': item.get('seasonNumber'),
            'mpaa': item.get('rating'),
            'duration': item.get('durationInSeconds', 0),
            'setCast': [{
                            'name': cast.get('name'),
                            'thumbnail': cast.get('photoUrl'),
                        } for cast in item.get('castMembers', []) or []],
            'directors': item.get('directors'),
            'playType': item.get('playType'),
            'adult': item.get('isAdult'),
            'mediatype': 'movie' if item.get('itemType') == 'Movie' else 'tvshow' if item.get('itemType') == 'Serie' else 'video',
            'art': {
                'thumb': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Thumbnail'), LOGO),
                'posterr': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Thumbnail'), LOGO),
                'fanart': next((image.get('url') for image in item.get('programImages', []) if image.get('type') == 'Backdrop'), FANART),
            }
        }

    if len(response) >= limit:
        yield {
            'handler': __name__,
            'method': 'search',
            'term': term,
            'page': page + 1,
            'limit': limit,
            'label': control.lang(34136).encode('utf-8'),
            'art': {
                'poster': control.addonNext(),
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_catalog():
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/catalogs'

    response = request_cached(url)

    catalog = next((catalog for catalog in response or []), {})

    return catalog.get('id'), catalog.get('version', {}).get('id')


def get_offers():
    entitlements = get_entitlements()
    return [offer.get('id') for offer in entitlements.get('offers', [])]


def get_subscribed_host_ids():
    entitlements = get_entitlements()

    result = []
    for offer in entitlements.get('offers', []):
        for host in offer.get('hosts', []):
            result.append(host.get('hostId'))

    return result


def get_entitlements():

    token, account = gettoken()

    url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/users/accounts/{account}/entitlements/list'.format(account=account)
    response = request_cached(url)
    return response


def request_cached(url, headers=None, force_refresh=False):
    token, account = gettoken()

    headers = headers or {}

    headers.update({
        'Authorization': 'Bearer %s' % token,
        'Accept': 'application/json',
        'X-Forwarded-For': '189.1.125.97',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
    })

    control.log('GET %s' % url)

    response = cache.get(requests.get, 1, url, headers=headers, force_refresh=force_refresh, table='oiplay')

    response.raise_for_status()

    return response.json()
