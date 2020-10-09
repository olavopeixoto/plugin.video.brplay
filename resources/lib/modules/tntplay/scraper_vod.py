# -*- coding: utf-8 -*-

import requests
import resources.lib.modules.control as control


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
    'TNTLA_BR': 'https://turner-latam-prod.akamaized.net/PROD-LATAM/live-channels/tnt_left.png',
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

# FANART = 'https://i.pinimg.com/originals/9d/c5/ba/9dc5ba36de7ad6e987c74e5ff4981925.jpg'
FANART = 'https://www.sportfacts.org/wp-content/uploads/2017/04/Watch-TNT-Online.jpg'

PLATFORM = 'PCTV_DASH'
LANGUAGE = control.lang(34125).encode('utf-8')  # 'ENG'  # 'POR'

FEATURED = control.lang(32080).upper().encode('utf-8')
ALL_GENRES = control.lang(34126).upper().encode('utf-8')

SERIES = control.lang(34127).upper().encode('utf-8')
MOVIES = control.lang(34128).upper().encode('utf-8')


def get_channels():

    # channels = []
    #
    # for channel_id in CHANNEL_MAP:
    #     logo = LOGO_MAP[channel_id]
    #     name = CHANNEL_MAP[channel_id]
    #     slug = CHANNEL_SLUG_MAP[channel_id]
    #
    #     channel = {
    #         "id": channel_id,
    #         "service_id": -1,
    #         "name": name,
    #         "adult": False,
    #         'slug': slug,
    #         'logo': logo,
    #         'brplayprovider': 'tntplay',
    #         # 'color': '#FFFFFF'
    #     }
    #
    #     channels.append(channel)
    #
    # return channels

    return [{
                "id": 'TNTLA_BR',
                "service_id": -1,
                "name": 'TNT',
                "adult": False,
                'slug': 'tnt',
                'logo': LOGO_MAP['TNTLA_BR'],
                'brplayprovider': 'tntplay',
                # 'color': '#FFFFFF'
            }]


def get_channel_categories(channel):

    return [SERIES, MOVIES]


def get_genres(category):

    type = 'movie%2Celemental' if category == MOVIES else 'series'

    url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/{platform}/TNTGO_LATAM_BR/CONTENT/FACET?objectSubtype={type}&facet=genres&filter_brand=tnts%2Ctnt%2Cspace'.format(platform=PLATFORM, type=type, lang=LANGUAGE)
    result = requests.get(url).json().get('resultObj', {}).get('facets', []) or []

    genres = [FEATURED, ALL_GENRES]

    genres.extend(sorted([facet.get('key').upper().encode('utf-8') for facet in result]))

    return genres


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

    result = requests.get(url).json().get('resultObj', {}).get('containers', []) or []

    for item in result:
        metadata = item.get('metadata', {})

        # episode_poster = '%s_%s' % (metadata.get('pictureUrl').split('_')[0], metadata['emfAttributes']['TopLevelEntityId'])
        poster = IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType='POSTER')
        fanart = FANART  # IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType=fanart_image_type)

        program = {
                    'id': item.get('id'),
                    'name': metadata.get('title', ''),
                    'poster': poster,
                    'fanart': fanart,
                    'clearlogo': None,
                    'kind': 'movies' if metadata.get('contentSubtype', '') == 'MOVIE' else 'tvshow',
                    'plot': metadata.get('longDescription', ''),
                    'plotoutline': metadata.get('shortDescription', ''),
                    'genre': metadata.get('genres', None),
                    'year': metadata.get('year', None),
                    'country': metadata.get('country', None),
                    'director': metadata.get('directors', []),
                    'cast': metadata.get('actors', []),
                    'episode': metadata.get('episodeNumber', None),
                    'season': metadata.get('season', None),
                    'encrypted': metadata.get('isEncrypted', True),
                    'brplayprovider': 'tntplay'
                }

        yield program


def get_seasons(id):
    url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/IPHONE/TNTGO_LATAM_BR/CONTENT/DETAIL/GOB/{id}?filter_brand=space%2Ctnt%2Ctnts'.format(lang=LANGUAGE, id=id)

    control.log('TNT SEASONS GET %s' % url)

    items = requests.get(url).json().get('resultObj', {}).get('containers', [])

    control.log(items)

    if len(items) > 0:
        item = items[0]
    else:
        return None

    metadata = item.get('metadata', {})

    show_poster = IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType='POSTER')
    show_fanart = FANART  # IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType=fanart_image_type)
    tvshow_name = metadata.get('title', '')

    program = {
        'id': item.get('id'),
        'name': metadata.get('title', ''),
        'poster': show_poster,
        'fanart': show_fanart,
        'clearlogo': None,
        'kind': 'season',
        'plot': metadata.get('longDescription', ''),
        'plotoutline': metadata.get('shortDescription', ''),
        'genre': metadata.get('genres', None),
        'year': metadata.get('year', None),
        'country': metadata.get('country', None),
        'director': metadata.get('directors', []),
        'cast': metadata.get('actors', []),
        'episode': metadata.get('episodeNumber', None),
        'season': metadata.get('season', None),
        'encrypted': metadata.get('isEncrypted', True),
        'brplayprovider': 'tntplay',
        'seasons': []
    }

    seasons = item.get('contentObjects', [])

    for obj in seasons:

        obj_meta = obj.get('metadata', {}) or {}
        picture_url = obj_meta.get('pictureUrl', None) or None
        poster = IMAGE_URL.format(pictureUrl=picture_url, imageType='POSTER') if picture_url else show_poster

        season = {
            'kind': 'season',
            'id': obj_meta.get('contentId'),
            'title': obj_meta.get('title', ''),
            'tvshowtitle': tvshow_name,
            'plot': obj_meta.get('longDescription', ''),
            'plotoutline': obj_meta.get('shortDescription', ''),
            'poster': poster,
            'fanart': show_fanart,
            'genre': obj_meta.get('genres', None),
            'year': obj_meta.get('year', None),
            'country': obj_meta.get('country', None),
            'director': obj_meta.get('directors', []),
            'cast': obj_meta.get('actors', []),
            'episode': obj_meta.get('episodeNumber', None),
            'season': obj_meta.get('season', None),
            'mpaa': obj_meta.get('pcVodLabel', None),
        }

        program['seasons'].append(season)

    return program


def get_episodes(id):
    url = 'https://apac.ti-platform.com/AGL/1.0/R/{lang}/IPHONE/TNTGO_LATAM_BR/CONTENT/DETAIL/BUNDLE/{id}?filter_brand=space%2Ctnt%2Ctnts'.format(lang=LANGUAGE, id=id)

    control.log('TNT EPISODES GET %s' % url)

    items = requests.get(url).json().get('resultObj', {}).get('containers', [])

    control.log(items)

    if len(items) > 0:
        item = items[0]
    else:
        raise StopIteration

    metadata = item.get('metadata', {})

    show_poster = IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType='POSTER')
    show_fanart = FANART  # IMAGE_URL.format(pictureUrl=metadata.get('pictureUrl'), imageType=fanart_image_type)
    tvshow_name = metadata.get('title', '')

    program = {
        'id': item.get('id'),
        'name': metadata.get('title', ''),
        'poster': show_poster,
        'fanart': show_fanart,
        'clearlogo': None,
        'kind': 'season',
        'plot': metadata.get('longDescription', ''),
        'plotoutline': metadata.get('shortDescription', ''),
        'genre': metadata.get('genres', None),
        'year': metadata.get('year', None),
        'country': metadata.get('country', None),
        'director': metadata.get('directors', []),
        'cast': metadata.get('actors', []),
        'episode': metadata.get('episodeNumber', None),
        'season': metadata.get('season', None),
        'encrypted': metadata.get('isEncrypted', True),
        'brplayprovider': 'tntplay',
    }

    episodes = item.get('contentObjects', [])

    for obj in episodes:

        obj_meta = obj.get('metadata', {}) or {}
        picture_url = obj_meta.get('pictureUrl', None) or None
        thumb = IMAGE_URL.format(pictureUrl=picture_url, imageType='VIDSCREENSHOT') if picture_url else show_poster

        poster_url = '%s_%s' % (picture_url.split('_')[0], obj_meta.get('emfAttributes', {}).get('TopLevelEntityId', ''))
        poster = IMAGE_URL.format(pictureUrl=poster_url, imageType='POSTER')

        season = {
            'kind': 'episode',
            'id': obj_meta.get('contentId'),
            'title': obj_meta.get('title', ''),
            'tvshowtitle': tvshow_name,
            'plot': obj_meta.get('longDescription', ''),
            'plotoutline': obj_meta.get('shortDescription', ''),
            'thumb': thumb,
            'poster': poster,
            'genre': obj_meta.get('genres', None),
            'year': obj_meta.get('year', None),
            'country': obj_meta.get('country', None),
            'director': obj_meta.get('directors', []),
            'cast': obj_meta.get('actors', []),
            'episode': obj_meta.get('episodeNumber', None),
            'season': obj_meta.get('season', None),
            'mpaa': obj_meta.get('pcVodLabel', None),
            'duration': obj_meta.get('duration', None),
            'brplayprovider': 'tntplay'
        }

        yield dict(program, **season)
