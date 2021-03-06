# -*- coding: utf-8 -*-

import requests
from resources.lib.modules import control, cache
from . import player
from urllib.parse import quote_plus

PLAYER_HANDLER = player.__name__


CONFIG_URL = 'https://cdn.ti-platform.com/config_TNT.json'

CHANNEL_MAP = {
    'TNTLA_BR': 'TNT',
    'TNTSLA_BR': 'TNT Series',
    'SPACELA_BR': 'Space',
}

CHANNEL_SLUG_MAP = {
    'TNTLA_BR': 'tnt',
    'TNTSLA_BR': 'tnts',
    'SPACELA_BR': 'space',
}

LOGO_MAP = {
    'TNTLA_BR': 'https://turner-latam-prod.akamaized.net/PROD-LATAM/live-channels/tnt.png',
    'TNTSLA_BR': 'https://turner-latam-prod.akamaized.net/PROD-LATAM/live-channels/tnts-pt.png',
    'SPACELA_BR': 'https://turner-latam-prod.akamaized.net/PROD-LATAM/live-channels/space.png',
}

IMAGE_TYPE = {
        "BUNDLE": [],
        "EPISODE": [
            "VIDEOSCREENSHOT"
        ],
        "GROUP_OF_BUNDLES": [
            "CHARACTER",
            "FEATURED10x3",
            "FEATURED16x9",
            "LOGO"
        ]
    }

IMAGE_URL = "https://turner-latam-prod.akamaized.net/PROD-LATAM/{pictureUrl}/{pictureUrl}_{imageType}.jpg"

# FANART = 'https://www.sportfacts.org/wp-content/uploads/2017/04/Watch-TNT-Online.jpg'
FANART = 'https://i.vimeocdn.com/video/529460829_1280x720.jpg'

PLATFORM = 'PCTV_DASH'
LANGUAGE = control.lang(34125)  # 'ENG'  # 'POR'

FEATURED = control.lang(32080).upper()
ALL_GENRES = control.lang(34126).upper()

SERIES = control.lang(34127).upper()
MOVIES = control.lang(34128).upper()


def get_channels():

    return [{
                'handler': __name__,
                'method': 'get_channel_categories',
                'label': 'TNT',
                'art': {
                    'thumb': LOGO_MAP['TNTLA_BR'],
                    'fanart': FANART
                }
            }]


def get_channel_categories():

    yield {
        'handler': __name__,
        'method': 'get_genres',
        'label': MOVIES,
        'category': MOVIES,
        'art': {
            'thumb': LOGO_MAP['TNTLA_BR'],
            'fanart': FANART
        }
    }

    yield {
        'handler': __name__,
        'method': 'get_genres',
        'label': SERIES,
        'category': SERIES,
        'art': {
            'thumb': LOGO_MAP['TNTLA_BR'],
            'fanart': FANART
        }
    }


def get_genres(category):

    media_type = 'movie%2Celemental' if category == MOVIES else 'series'

    url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/{platform}/TNTGO_LATAM_BR/CONTENT/FACET?objectSubtype={type}&facet=genres&filter_brand=tnts%2Ctnt%2Cspace'.format(platform=PLATFORM, type=media_type, lang=LANGUAGE)
    result = cache.get(requests.get, 24, url, table='tntplay').json().get('resultObj', {}).get('facets', []) or []

    yield {
        'handler': __name__,
        'method': 'get_content',
        'label': FEATURED,
        'category': category,
        'genre': FEATURED,
        'properties': {
            'SpecialSort': 'top'
        },
        'art': {
            'thumb': LOGO_MAP['TNTLA_BR'],
            'fanart': FANART
        }
    }

    yield {
        'handler': __name__,
        'method': 'get_content',
        'label': ALL_GENRES,
        'category': category,
        'genre': ALL_GENRES,
        'properties': {
            'SpecialSort': 'top'
        },
        'art': {
            'thumb': LOGO_MAP['TNTLA_BR'],
            'fanart': FANART
        }
    }

    for facet in result:
        yield {
                'handler': __name__,
                'method': 'get_content',
                'label': facet.get('key').upper(),
                'category': category,
                'genre': facet.get('key').upper(),
                'art': {
                    'thumb': LOGO_MAP['TNTLA_BR'],
                    'fanart': FANART
                }
            }


def get_content(category, genre):
    if category == MOVIES:
        if genre == FEATURED:
            url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/IPHONE/TNTGO_LATAM_BR/TRAY/NAME/FEATURED_MOVIES?orderBy=year&sortOrder=desc&filter_objectSubtype=MOVIE&filter_propertyName=TNTGO_LATAM_BR&filter_brand=tnts%2Ctnt%2Cspace'.format(platform=PLATFORM, lang=LANGUAGE)
        else:
            filter_genres = ''
            if genre != ALL_GENRES:
                filter_genres = '&filter_genres=%s' % genre.lower()
            url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/IPHONE/TNTGO_LATAM_BR/TRAY/SEARCH/VOD?orderBy=year&sortOrder=desc&filter_objectSubtype=MOVIE&filter_propertyName=TNTGO_LATAM_BR&from=0&to=99&filter_brand=space%2Ctnts%2Ctnt{filter}'.format(platform=PLATFORM, filter=filter_genres, lang=LANGUAGE)

    else:
        if genre == FEATURED:
            url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/IPHONE/TNTGO_LATAM_BR/TRAY/NAME/FEATURED_SHOWS?orderBy=year&sortOrder=desc&filter_objectSubtype=series&filter_propertyName=TNTGO_LATAM_BR&filter_brand=tnts%2Ctnt%2Cspace'.format(platform=PLATFORM, lang=LANGUAGE)
        else:
            filter_genres = ''
            if genre != ALL_GENRES:
                filter_genres = '&filter_genres=%s' % genre.lower()
            url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/IPHONE/TNTGO_LATAM_BR/TRAY/SEARCH/VOD?orderBy=year&sortOrder=desc&filter_objectSubtype=SERIES&filter_propertyName=TNTGO_LATAM_BR&from=0&to=99&filter_brand=space%2Ctnts%2Ctnt{filter}'.format(platform=PLATFORM, filter=filter_genres, lang=LANGUAGE)

    return request_content(url)


def request_content(url):
    result = cache.get(requests.get, 24, url, table='tntplay').json().get('resultObj', {}).get('containers', []) or []

    for item in result:
        metadata = item.get('metadata', {})

        # episode_poster = '%s_%s' % (metadata.get('pictureUrl').split('_')[0], metadata['emfAttributes']['TopLevelEntityId'])
        poster = IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType='POSTER')
        fanart = FANART  # IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType=fanart_image_type)

        playable = metadata.get('contentSubtype', '') == 'MOVIE'

        program = {
            'handler': PLAYER_HANDLER if playable else __name__,
            'method': 'playlive' if playable else 'get_seasons',
            'IsPlayable': playable,
            'id': item.get('id'),
            'label': metadata.get('title', ''),
            'plot': metadata.get('longDescription', ''),
            'plotoutline': metadata.get('shortDescription', ''),
            'genre': metadata.get('genres'),
            'year': metadata.get('year'),
            'country': metadata.get('country'),
            'director': metadata.get('directors', []),
            'cast': metadata.get('actors', []),
            'episode': metadata.get('episodeNumber'),
            'season': metadata.get('season'),
            'encrypted': metadata.get('isEncrypted'),
            'mediatype': 'movie' if metadata.get('contentSubtype', '') == 'MOVIE' else 'tvshow',
            # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            'art': {
                'poster': poster,
                'fanart': fanart
            }
        }

        yield program


def get_seasons(id):
    url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/IPHONE/TNTGO_LATAM_BR/CONTENT/DETAIL/GOB/{id}?filter_brand=space%2Ctnt%2Ctnts'.format(lang=LANGUAGE, id=id)

    control.log('TNT SEASONS GET %s' % url)

    items = cache.get(requests.get, 24, url, table='tntplay').json().get('resultObj', {}).get('containers', [])

    control.log(items)

    if len(items) > 0:
        item = items[0]
    else:
        return

    seasons = item.get('contentObjects', [])

    if len(seasons) == 1:
        obj = seasons[0]
        obj_meta = obj.get('metadata', {}) or {}
        return get_episodes(obj_meta.get('contentId'))
    else:
        metadata = item.get('metadata', {})

        show_poster = IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType='POSTER')
        show_fanart = FANART  # IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType=fanart_image_type)
        tvshow_name = metadata.get('title', '')

        return _get_seasons_internal(seasons, tvshow_name, show_poster, show_fanart)


def _get_seasons_internal(seasons, tvshow_name, show_poster, show_fanart):
    for obj in seasons:

        obj_meta = obj.get('metadata', {}) or {}
        # picture_url = obj_meta.get('pictureUrl') or None
        # poster = IMAGE_URL.format(pictureUrl=picture_url, imageType='POSTER') if picture_url else show_poster

        yield {
            'handler': __name__,
            'method': 'get_episodes',
            'mediatype': 'season',
            'id': obj_meta.get('contentId'),
            'label': obj_meta.get('title', ''),
            'title': obj_meta.get('title', ''),
            'tvshowtitle': tvshow_name,
            'plot': obj_meta.get('longDescription', ''),
            'plotoutline': obj_meta.get('shortDescription', ''),
            'genre': obj_meta.get('genres'),
            'year': obj_meta.get('year'),
            'country': obj_meta.get('country'),
            'director': obj_meta.get('directors', []),
            'cast': obj_meta.get('actors', []),
            'episode': obj_meta.get('episodeNumber'),
            'season': obj_meta.get('season'),
            'mpaa': obj_meta.get('pcVodLabel'),
            'art': {
                'poster': show_poster,
                'fanart': show_fanart
            }
        }


def get_episodes(id):
    url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/IPHONE/TNTGO_LATAM_BR/CONTENT/DETAIL/BUNDLE/{id}?filter_brand=space%2Ctnt%2Ctnts'.format(lang=LANGUAGE, id=id)

    control.log('TNT EPISODES GET %s' % url)

    items = cache.get(requests.get, 24, url, table='tntplay').json().get('resultObj', {}).get('containers', [])

    control.log(items)

    if len(items) > 0:
        item = items[0]
    else:
        return

    metadata = item.get('metadata', {})

    show_poster = IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType='POSTER')
    show_fanart = FANART  # IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType=fanart_image_type)
    tvshow_name = metadata.get('title', '')

    episodes = item.get('contentObjects', [])

    for obj in episodes:

        obj_meta = obj.get('metadata', {}) or {}
        picture_url = obj_meta.get('pictureUrl') or None

        thumb_url = '%s_%s' % (picture_url.split('_')[0], obj_meta.get('emfAttributes', {}).get('TopLevelEntityId', ''))

        # thumb = IMAGE_URL.format(pictureUrl=thumb_url, imageType='VIDSCREENSHOT') if picture_url else show_poster
        thumb = IMAGE_URL.format(pictureUrl=thumb_url, imageType='FEATURED_HANDSET') if picture_url else show_poster
        # https://turner-latam-prod.akamaized.net/PROD-LATAM/{pictureUrl}/{pictureUrl}_{imageType}.jpg
        # https://turner-latam-prod.akamaized.net/PROD-LATAM/TNTSERIES_213272714/TNTSERIES_213272714_FEATURED_HANDSET.jpg?imwidth=1125

        poster_url = '%s_%s' % (picture_url.split('_')[0], obj_meta.get('emfAttributes', {}).get('TopLevelEntityId', ''))
        poster = IMAGE_URL.format(pictureUrl=poster_url, imageType='POSTER')

        yield {
            'handler': PLAYER_HANDLER,
            'method': 'playlive',
            'IsPlayable': True,
            'encrypted': metadata.get('isEncrypted', True),
            'mediatype': 'episode',
            'id': obj_meta.get('contentId'),
            'label': obj_meta.get('title', ''),
            'title': obj_meta.get('title', ''),
            'tvshowtitle': tvshow_name,
            'plot': obj_meta.get('longDescription', ''),
            'plotoutline': obj_meta.get('shortDescription', ''),
            'genre': obj_meta.get('genres'),
            'year': obj_meta.get('year'),
            'country': obj_meta.get('country'),
            'director': obj_meta.get('directors', []),
            'cast': obj_meta.get('actors', []),
            'episode': obj_meta.get('episodeNumber'),
            'season': obj_meta.get('season'),
            'mpaa': obj_meta.get('pcVodLabel'),
            'duration': obj_meta.get('duration'),
            'sort': control.SORT_METHOD_EPISODE,
            'art': {
                'thumb': thumb,
                'poster': poster,
                'tvshow.poster': show_poster,
                'fanart': show_fanart
            }
        }


def search(term, page=1):
    # url = 'https://api.tntgo.tv/AGL/1.0/A/POR/PCTV/TNTGO_LATAM_BR/TRAY/SEARCH/VOD?query=Marg%20Helgenberger&filter_objectSubtype=series,movie&from=0&to=99&selectedUserLevel=3'
    url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/IPHONE/TNTGO_LATAM_BR/TRAY/SEARCH/VOD?query={query}&filter_objectSubtype=MOVIE%2CSERIES&filter_propertyName=TNTGO_LATAM_BR&from=0&to=49&filter_brand=tnts%2Ctnt%2Cspace'.format(lang=LANGUAGE, query=quote_plus(term))

    return request_content(url)
