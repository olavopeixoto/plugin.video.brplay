# -*- coding: utf-8 -*-

import datetime
import time
from resources.lib.modules import control
from resources.lib.modules.globosat import request_query
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
    '936': 'pfc124ha'
}

PLAYER_HANDLER = player.__name__


def get_live_channels():

    today_str = datetime.datetime.now().strftime('%Y-%m-%d')

    query = 'query%20getAllBroadcasts%28%24logoScale%3A%20BroadcastChannelTrimmedLogoScales%20%3D%20X56%29%20%7B%0A%20%20broadcasts%20%7B%0A%20%20%20%20mediaId%0A%20%20%20%20mutedMediaId%0A%20%20%20%20promotionalMediaId%0A%20%20%20%20promotionalText%0A%20%20%20%20geofencing%0A%20%20%20%20geoblocked%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20color%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20text%3A%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20trimmedLogo%28scale%3A%20%24logoScale%29%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%7D%0A%20%20%20%20epgCurrentSlots%20%7B%0A%20%20%20%20%20%20composite%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%0A%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20media%20%7B%0A%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    variables = '{{"logoScale":"X42","date":"{date}"}}'.format(date=today_str)
    response = request_query(query, variables)

    channels = []

    for broadcast in response['data']['broadcasts']:
        if 'epgCurrentSlots' not in broadcast or not broadcast['epgCurrentSlots']:
            continue

        program = broadcast['epgCurrentSlots'][0]

        live_text = u' (' + control.lang(32004) + u')' if program['liveBroadcast'] else u''

        program_detail = u': ' + program['metadata'] if program['metadata'] else u''

        program_name = program['name'] + program_detail if program['metadata'] and not program['metadata'].startswith(program['name']) else program['metadata'] if program['metadata'] else program['name']

        channel_name = broadcast['channel']['name']

        label = u"[B]%s[/B][I] - %s[/I]%s" % (channel_name, program_name, live_text)

        fanart = FANART_URL.format(media_id=broadcast['mediaId'])
        thumb = SNAPSHOT_URL.format(transmission=THUMBS[str(broadcast['channel']['id'])]) + '/?v=' + str(int(time.time())) if str(broadcast['channel']['id']) in THUMBS else THUMB_URL.format(media_id=broadcast['mediaId'])

        program_date = datetime.datetime.fromtimestamp(program['startTime'])
        end_time = datetime.datetime.fromtimestamp(program['endTime'])
        duration = (end_time - program_date).total_seconds()

        # program_name = program['name'] + program_detail

        title = program.get('title', {}) or {}

        thumb = (title.get('cover', {}) or {}).get('landscape', thumb) or thumb

        item = {
            'handler': PLAYER_HANDLER,
            'method': 'playlive',
            'id': broadcast['mediaId'],
            'IsPlayable': True,
            'livefeed': True,
            'live': program['liveBroadcast'],
            'channel_id': broadcast['channel']['id'],
            'service_id': broadcast['media']['serviceId'],
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
            # 'tvshowtitle': program['name'] if program_name else None,
            'sorttitle': program_name,
            'tag': program.get('tags', []),
            'plot': program['description'] or '' if not control.isFTV else ' ',
            # 'plotoutline': datetime.datetime.strftime(program_date, '%H:%M') + ' - ' + datetime.datetime.strftime(end_time, '%H:%M'),
            'duration': int(duration),
            'dateadded': datetime.datetime.strftime(program_date, '%Y-%m-%d %H:%M:%S'),
            # 'isFree': broadcast['media']['availableFor'] == 'ANONYMOUS',
            'mediatype': 'episode',
            'art': {
                'icon': broadcast['channel']['logo'],
                'clearlogo': broadcast['channel']['logo'],
                'fanart': (title.get('cover', {}) or {}).get('landscape', fanart) or fanart,
                'thumb': thumb,
                'tvshow.poster': (title.get('poster', {}) or {}).get('web', thumb),
            }
        }

        channels.append(item)

    return channels
