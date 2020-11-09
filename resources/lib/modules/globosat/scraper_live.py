# -*- coding: utf-8 -*-

import datetime
import time
from resources.lib.modules import control
from resources.lib.modules.globosat import request_query
from . import get_authorized_services
from . import auth_helper
import player

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

    query = 'query%20getAllBroadcasts%28%24logoScale%3A%20BroadcastChannelTrimmedLogoScales%20%3D%20X56%29%20%7B%0A%20%20broadcasts%20%7B%0A%20%20%20%20mediaId%0A%20%20%20%20mutedMediaId%0A%20%20%20%20promotionalMediaId%0A%20%20%20%20promotionalText%0A%20%20%20%20geofencing%0A%20%20%20%20geoblocked%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20color%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20text%3A%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20trimmedLogo%28scale%3A%20%24logoScale%29%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%7D%0A%20%20%20%20epgCurrentSlots%20%7B%0A%20%20%20%20%20%20composite%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%0A%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20media%20%7B%0A%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    variables = '{{"date":"{date}"}}'.format(date=today_str)
    response = request_query(query, variables, use_cache=False)

    authorized_services = []
    if control.setting('globosat_ignore_channel_authorization') != 'true':
        service_ids = [broadcast['media']['serviceId'] for broadcast in response['data']['broadcasts']]
        authorized_services = get_authorized_services(service_ids)

    for broadcast in response['data']['broadcasts']:
        if 'epgCurrentSlots' not in broadcast or not broadcast['epgCurrentSlots']:
            continue

        service_id = broadcast['media']['serviceId']

        if control.setting('globosat_ignore_channel_authorization') != 'true' and (service_id not in authorized_services or not auth_helper.is_available_for(broadcast.get('media', {}).get('availableFor'))):
            continue

        geofencing = broadcast.get('geofencing', False)
        media_id = broadcast.get('mediaId')

        if geofencing:
            affiliate = get_globosat_affiliate()
            if affiliate:
                code, latitude, longitude = control.get_coordinates(affiliate)
                broadcast = get_epg_with_coordinates(media_id, latitude, longitude)

        program = next(iter(broadcast.get('epgCurrentSlots')), {}) or {}

        live_text = u' (' + control.lang(32004) + u')' if program['liveBroadcast'] else u''

        program_detail = u': ' + program['metadata'] if program['metadata'] else u''

        program_name = program['name'] + program_detail if program['metadata'] and not program['metadata'].startswith(program['name']) else program['metadata'] if program['metadata'] else program['name']

        channel_name = broadcast['channel']['name']

        label = u"[B]%s[/B][I] - %s[/I]%s" % (channel_name, program_name, live_text)

        fanart = FANART_URL.format(media_id=broadcast['mediaId'])
        thumb = SNAPSHOT_URL.format(transmission=THUMBS[str(broadcast['channel']['id'])]) + '/?v=' + str(int(time.time())) if str(broadcast['channel']['id']) in THUMBS else THUMB_URL.format(media_id=broadcast['mediaId'])

        program_date = datetime.datetime.utcfromtimestamp(program['startTime'])
        end_time = datetime.datetime.utcfromtimestamp(program['endTime'])

        duration = (end_time - program_date).total_seconds()

        title = program.get('title', {}) or {}

        thumb = (title.get('cover', {}) or {}).get('landscape', thumb) or thumb

        program_time_desc = datetime.datetime.strftime(program_date, '%H:%M') + ' - ' + datetime.datetime.strftime(end_time, '%H:%M')
        description = '%s | %s' % (program_time_desc, program.get('description'))

        tags = [program_time_desc]

        if program.get('liveBroadcast', False):
            tags.append(control.lang(32004))

        tags.extend(program.get('tags', []) or [])

        yield {
            'handler': PLAYER_HANDLER,
            'method': 'playlive',
            'id': media_id,
            'IsPlayable': True,
            'livefeed': True,
            'live': program['liveBroadcast'],
            'channel_id': broadcast['channel']['id'],
            'service_id': service_id,
            'program_id': title.get('originProgramId'),
            'studio': 'Canais Globo',
            'label': label,
            'title': label,
            'year': title.get('releaseYear'),
            'country': title.get('countries', []),
            'genre': title.get('genresNames', []),
            'cast': title.get('castNames', []),
            'director': title.get('directorsNames', []),
            'writer': title.get('screenwritersNames', []),
            'credits': title.get('artDirectorsNames', []),
            'mpaa': program.get('contentRating'),
            # 'title': program.get('metadata', program.get('name', '')),
            'tvshowtitle': program['name'] if program_name else None,
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
    query = 'query%20Epg%28%24mediaId%3A%20ID%21%2C%20%24coordinates%3A%20CoordinatesData%29%20%7B%0A%20%20broadcast%28mediaId%3A%20%24mediaId%2C%20coordinates%3A%20%24coordinates%29%20%7B%0A%20%20%20%20...EpgFragment%0A%20%20%7D%0A%7D%0Afragment%20EpgFragment%20on%20Broadcast%20%7B%0A%20%20mediaId%0A%20%20withoutDVRMediaId%0A%20%20imageOnAir%28scale%3A%20X1080%29%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20slug%0A%20%20%7D%0A%20%20affiliateSignal%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20dtvChannel%0A%20%20%20%20%20%20dtvHDID%0A%20%20%20%20%20%20dtvID%0A%20%20%20%20%7D%0A%20%20epgCurrentSlots%28limit%3A%202%29%20%7B%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20programId%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20alternativeTime%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20format%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directors%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20cast%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20genres%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20structure%20%7B%0A%20%20%20%20%20%20%20%20%20%20...seasonedStructureFragment%0A%20%20%20%20%20%20%20%20%20%20...filmPlaybackStructureFragment%0A%20%20%20%20%20%20%20%20%20%20...episodeListStructureFragment%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20seasonedStructureFragment%20on%20SeasonedStructure%20%7B%0A%20%20seasons%20%7B%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20number%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20totalEpisodes%0A%20%20%20%20%20%20episodes%28page%3A%201%2C%20perPage%3A%204%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20number%0A%20%20%20%20%20%20%20%20%20%20seasonNumber%0A%20%20%20%20%20%20%20%20%20%20seasonId%0A%20%20%20%20%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20filmPlaybackStructureFragment%20on%20FilmPlaybackStructure%20%7B%0A%20%20videoPlayback%20%7B%0A%20%20%20%20id%0A%20%20%20%20availableFor%0A%20%20%20%20headline%0A%20%20%20%20description%0A%20%20%20%20thumb%0A%20%20%20%20duration%0A%20%20%7D%0A%7D%0Afragment%20episodeListStructureFragment%20on%20EpisodeListStructure%20%7B%0A%20%20episodes%28page%3A%201%2C%20perPage%3A%204%29%20%7B%0A%20%20%20%20page%0A%20%20%20%20hasNextPage%0A%20%20%20%20nextPage%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20number%0A%20%20%20%20%20%20seasonNumber%0A%20%20%20%20%20%20seasonId%0A%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    variables = '{{"mediaId":"{media_id}","coordinates":{{"lat":"{lat}", "long": "{long}"}}}}'.format(media_id=media_id, lat=latitude, long=longitude)
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
