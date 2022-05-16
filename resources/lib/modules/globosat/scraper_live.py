# -*- coding: utf-8 -*-

import datetime
import time
from resources.lib.modules import control
from resources.lib.modules.globosat import request_query, request_url
from . import get_authorized_services
from . import auth_helper
from . import player

FANART_URL = 'http://s01.video.glbimg.com/x1080/{media_id}.jpg'
THUMB_URL = 'https://s04.video.glbimg.com/x1080/{media_id}.jpg'

SNAPSHOT_URL = 'https://live-thumbs.video.globo.com/{transmission}/snapshot'

THUMBS = {
    '2024': 'spo424ha',
    '1996': 'spo124ha',
    '2001': 'spo224ha',
    '2002': 'spo324ha',
    '1987': 'gnews24ha',
    '1986': 'gnt24ha',
    '1991': 'msw24ha',
    '1982': 'viva24ha',
    '1981': 'maisgsat24ha',
    '1989': 'gloob24ha',
    '2046': 'gloobinho24ha',
    '1992': 'off24ha',
    '1983': 'bis24ha',
    '2079': 'mpix24ha',
    '1984': 'bra24ha',
    '1997': 'univ24ha',
    '2000': 'syfy24ha',
    '2023': 'stduniv24ha',
    '2006': 'sexy24ha',
    '1960': 'cbt24ha',
    # '936': 'pfc124ha',
    # '1995': 'pfc1'
}

PLAYER_HANDLER = player.__name__


def get_live_channels():

    today_str = datetime.datetime.utcnow().strftime('%Y-%m-%d')

    affiliate_code = 'null'
    affiliate = get_globosat_affiliate()
    latitude = None
    longitude = None
    if affiliate:
        affiliate_code, latitude, longitude = control.get_coordinates(affiliate)
        if not affiliate_code:
            affiliate_code, affiliate_name = get_affiliate_code_by_coordinates(latitude, longitude)

    query = 'query%20getAllBroadcasts%28%24affiliateCode%3A%20String%2C%20%24logoScale%3A%20BroadcastChannelTrimmedLogoScales%20%3D%20X56%2C%20%24imageOnAirScale%3A%20BroadcastImageOnAirScales%20%3D%20X1080%29%20%7B%0A%20%20broadcasts%28filtersInput%3A%20%7BaffiliateCode%3A%20%24affiliateCode%7D%29%20%7B%20%0A%20%20%20%20mediaId%0A%20%20%20%20mutedMediaId%0A%20%20%20%20promotionalMediaId%0A%20%20%20%20promotionalText%0A%20%20%20%20geofencing%0A%20%20%20%20geoblocked%0A%20%20%20%20imageOnAir%28scale%3A%20%24imageOnAirScale%29%0A%20%20%20%20assets%20%7B%0A%20%20%20%20%20%20thumbUrl%0A%20%20%20%20%20%20previewUrl%0A%20%20%20%20%20%20teaserUrl%0A%20%20%20%20%7D%0A%20%20%20%20categories%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20position%0A%20%20%20%20%7D%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20color%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20text%3A%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20trimmedLogo%28scale%3A%20%24logoScale%29%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%7D%0A%20%20%20%20epgCurrentSlots%20%7B%0A%20%20%20%20%20%20composite%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%0A%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20media%20%7B%0A%20%20%20%20%20%20liveThumbnail%0A%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20headline%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    variables = '{{"date":"{date}","affiliateCode":"{affiliate}"}}'.format(date=today_str, affiliate=affiliate_code)
    response = request_query(query, variables, use_cache=False)

    authorized_services = []
    globosat_ignore_channel_authorization = control.setting('globosat_ignore_channel_authorization') == 'true'

    if not globosat_ignore_channel_authorization:
        service_ids = [broadcast['media']['serviceId'] for broadcast in response['data']['broadcasts']]
        authorized_services = get_authorized_services(service_ids)

    now = str(int(time.time()))

    for broadcast in response['data']['broadcasts']:
        # if 'epgCurrentSlots' not in broadcast or not broadcast['epgCurrentSlots']:
        #     continue

        service_id = broadcast['media']['serviceId']

        if not globosat_ignore_channel_authorization and (service_id not in authorized_services or not auth_helper.is_available_for(broadcast.get('media', {}).get('availableFor'))):
            continue

        media_id = broadcast.get('mediaId')

        program = next(iter(broadcast.get('epgCurrentSlots')), {}) or {}

        live_text = u' (' + control.lang(32004) + u')' if program.get('liveBroadcast') else u''

        program_detail = u': ' + program.get('metadata') if program.get('metadata') else u''

        program_name = program.get('name', '') or broadcast.get('media', {}).get('headline') or ''

        program_name = program_name + program_detail if program.get('metadata') and not program.get('metadata', '').startswith(program_name) else program.get('metadata') if program.get('metadata') else program_name

        channel_name = broadcast['channel']['name']

        label = u"[B]%s[/B][I] - %s[/I]%s" % (channel_name, program_name, live_text)

        fanart = FANART_URL.format(media_id=broadcast['mediaId'])
        fanart = broadcast.get('imageOnAir', fanart) or fanart

        thumb = SNAPSHOT_URL.format(transmission=THUMBS[str(broadcast['channel']['id'])]) if str(broadcast['channel']['id']) in THUMBS else THUMB_URL.format(media_id=broadcast['mediaId'])
        thumb = '%s?v=%s' % (broadcast.get('assets', {}).get('thumbUrl') or thumb, now)

        program_date = datetime.datetime.utcfromtimestamp(program.get('startTime')) if program else datetime.datetime.utcnow()
        end_time = datetime.datetime.utcfromtimestamp(program.get('endTime')) if program else datetime.datetime.utcnow()

        duration = (end_time - program_date).total_seconds() if program else 0

        title = program.get('title', {}) or {}

        thumb = (title.get('cover', {}) or {}).get('landscape', thumb) or thumb

        program_time_desc = datetime.datetime.strftime(program_date, '%H:%M') + ' - ' + datetime.datetime.strftime(end_time, '%H:%M')
        description = '%s | %s' % (program_time_desc, program.get('description'))

        tags = [program_time_desc]

        if program.get('liveBroadcast', False):
            tags.append(control.lang(32004))

        tags.extend(program.get('tags', []) or [])

        categories = next((category.get('name') for category in broadcast.get('categories', [])), [])

        geofencing = broadcast.get('geofencing', False)

        yield {
            'handler': PLAYER_HANDLER,
            'method': player.Player.playlive.__name__,
            'id': media_id,
            'IsPlayable': True,
            'livefeed': True,
            'geofencing': geofencing,
            'lat': latitude,
            'long': longitude,
            'live': program.get('liveBroadcast', False),
            'channel_id': broadcast['channel']['id'],
            'service_id': service_id,
            'program_id': title.get('originProgramId'),
            'channelname': channel_name,
            'studio': 'Canais Globo',
            'label': label,
            'title': label,
            'year': title.get('releaseYear'),
            'country': title.get('countries', []) or [],
            'genre': title.get('genresNames', []) or categories,
            'cast': title.get('castNames', []) or [],
            'director': title.get('directorsNames', []) or [],
            'writer': title.get('screenwritersNames', []) or [],
            'credits': title.get('artDirectorsNames', []) or [],
            'mpaa': program.get('contentRating'),
            # 'title': program.get('metadata', program.get('name', '')),
            'tvshowtitle': program.get('name') if program_name else None,
            'sorttitle': program_name,
            'tag': tags,
            'plot': description,
            'duration': int(duration),
            'dateadded': datetime.datetime.strftime(program_date, '%Y-%m-%d %H:%M:%S'),
            'mediatype': 'episode',
            'art': {
                'icon': broadcast['channel']['logo'],
                'clearlogo': broadcast['channel']['logo'],
                'fanart': (title.get('cover', {}) or {}).get('landscape', fanart) or fanart,
                'thumb': thumb,
                'tvshow.poster': (title.get('poster', {}) or {}).get('web', thumb),
            }
        }


def get_epg_with_coordinates(media_id, latitude, longitude):
    query = 'query%20getAllBroadcasts%28%24affiliateCode%3A%20String%2C%20%24logoScale%3A%20BroadcastChannelTrimmedLogoScales%20%3D%20X56%2C%20%24imageOnAirScale%3A%20BroadcastImageOnAirScales%20%3D%20X1080%29%20%7B%0A%20%20broadcasts%28filtersInput%3A%20%7BaffiliateCode%3A%20%24affiliateCode%7D%29%20%7B%20%0A%20%20%20%20mediaId%0A%20%20%20%20mutedMediaId%0A%20%20%20%20promotionalMediaId%0A%20%20%20%20promotionalText%0A%20%20%20%20geofencing%0A%20%20%20%20geoblocked%0A%20%20%20%20imageOnAir%28scale%3A%20%24imageOnAirScale%29%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20color%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20text%3A%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20trimmedLogo%28scale%3A%20%24logoScale%29%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%7D%0A%20%20%20%20epgCurrentSlots%20%7B%0A%20%20%20%20%20%20composite%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%0A%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20media%20%7B%0A%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    variables = '{{"mediaId":"{media_id}","coordinates":{{"lat":"{lat}","long":"{long}"}}}}'.format(media_id=media_id, lat=latitude, long=longitude)
    response = request_query(query, variables, use_cache=False)

    return (response.get('data', {}) or {}).get('broadcast', {}) or {}


def get_globosat_affiliate():

    geolocation = control.setting('globosat_geofence')

    if geolocation == '0':
        affiliate = None
    elif geolocation == '2':
        affiliate = 'Sao Paulo'
    elif geolocation == '3':
        affiliate = 'Brasilia'
    elif geolocation == '4':
        affiliate = 'Belo Horizonte'
    elif geolocation == '5':
        affiliate = 'Recife'
    elif geolocation == '6':
        affiliate = 'Salvador'
    elif geolocation == '7':
        affiliate = 'Fortaleza'
    elif geolocation == '8':
        affiliate = 'Aracaju'
    elif geolocation == '9':
        affiliate = 'Maceio'
    elif geolocation == '10':
        affiliate = 'Cuiaba'
    elif geolocation == '11':
        affiliate = 'Porto Alegre'
    elif geolocation == '12':
        affiliate = 'Florianopolis'
    elif geolocation == '13':
        affiliate = 'Curitiba'
    elif geolocation == '14':
        affiliate = 'Vitoria'
    elif geolocation == '15':
        affiliate = 'Goiania'
    elif geolocation == '16':
        affiliate = 'Campo Grande'
    elif geolocation == '17':
        affiliate = 'Manaus'
    elif geolocation == '18':
        affiliate = 'Belem'
    elif geolocation == '19':
        affiliate = 'Macapa'
    elif geolocation == '20':
        affiliate = 'Palmas'
    elif geolocation == '21':
        affiliate = 'Rio Branco'
    elif geolocation == '22':
        affiliate = 'Teresina'
    elif geolocation == '23':
        affiliate = 'Sao Luis'
    elif geolocation == '24':
        affiliate = 'Joao Pessoa'
    elif geolocation == '25':
        affiliate = 'Natal'
    elif geolocation == '26':
        affiliate = 'Boa Vista'
    elif geolocation == '27':
        affiliate = 'Porto Velho'
    else:
        affiliate = 'Rio de Janeiro'

    return affiliate


def get_affiliate_code_by_coordinates(latitude, longitude):
    url = 'https://security.video.globo.com/affiliates/info?lat={lat}&long={long}'.format(lat=latitude, long=longitude)
    response = request_url(url, use_cache=False)

    return response.get('code'), response.get('name')
