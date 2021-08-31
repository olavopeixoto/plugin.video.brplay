# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules.globosat import player, get_authorized_services
import os
import time
import requests
import datetime

SEXYHOT_LOGO = os.path.join(control.artPath(), 'logo_sexyhot.png')
SEXYHOT_FANART = os.path.join(control.artPath(), 'fanart_sexyhot.png')

FANART_URL = 'http://s01.video.glbimg.com/x1080/{media_id}.jpg'
THUMB_URL_MEDIA = 'https://s04.video.glbimg.com/x720/{media_id}.jpg'
THUMB_URL = 'https://live-thumbs.video.globo.com/sexy24ha/snapshot/'


PLAYER_HANDLER = player.__name__


def get_broadcast():

    url = 'https://products-jarvis.globo.com/graphql?query=query%20getBroadcast%28%24mediaId%3A%20ID%21%2C%20%24coordinates%3A%20CoordinatesData%2C%20%24logoScale%3A%20BroadcastChannelTrimmedLogoScales%20%3D%20X56%29%20%7B%0A%20%20broadcast%28mediaId%3A%20%24mediaId%2C%20coordinates%3A%20%24coordinates%29%20%7B%0A%20%20%20%20mediaId%0A%20%20%20%20mutedMediaId%0A%20%20%20%20promotionalMediaId%0A%20%20%20%20promotionalText%0A%20%20%20%20geofencing%0A%20%20%20%20geoblocked%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20color%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20text%3A%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20trimmedLogo%28scale%3A%20%24logoScale%29%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%7D%0A%20%20%20%20imageOnAir%3A%20imageOnAir%28scale%3A%20X720%29%0A%20%20%20%20epgCurrentSlots%28limit%3A%202%29%20%7B%0A%20%20%20%20%20%20composite%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20media%20%7B%0A%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D&operationName=getBroadcast&variables=%7B%22logoScale%22%3A%22X42%22%2C%22mediaId%22%3A%226988462%22%7D'
    headers = {
        'x-tenant-id': 'sexy-hot',
        'x-platform-id': 'web',
        'x-device-id': 'desktop',
        'x-client-version': '0.4.3',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }
    response = requests.get(url, headers=headers).json()

    broadcast = response['data']['broadcast']

    program = broadcast['epgCurrentSlots'][0]

    program_name = program['name'] + (u': ' + program['metadata'] if program['metadata'] else u'')

    live_text = ' (' + control.lang(32004) + ')' if program['liveBroadcast'] else ''
    label = "[B]" + broadcast['channel']['name'] + "[/B]" + ('[I] - ' + program_name + '[/I]' if program_name else '') + live_text

    fanart = broadcast['imageOnAir']  # FANART_URL.format(media_id=broadcast['mediaId']) + '?v=' + str(int(time.time()))
    thumb = THUMB_URL + '?v=' + str(int(time.time()))
    # thumb = THUMB_URL_MEDIA.format(media_id=broadcast['mediaId']) + '?v=' + str(int(time.time()))

    program_date = datetime.datetime.fromtimestamp(program['startTime'])
    end_time = datetime.datetime.fromtimestamp(program['endTime'])
    duration = (end_time - program_date).total_seconds()

    title = program.get('title', {}) or {}

    service_id = broadcast.get('media', {}).get('serviceId')

    program_time_desc = datetime.datetime.strftime(program_date, '%H:%M') + ' - ' + datetime.datetime.strftime(end_time, '%H:%M')
    description = '%s | %s' % (program_time_desc, program.get('description'))

    tags = [program_time_desc]

    if program.get('liveBroadcast', False):
        tags.append(control.lang(32004))

    tags.extend(program.get('tags', []) or [])

    item = {
        'handler': PLAYER_HANDLER,
        'method': player.Player.playlive.__name__,
        'id': broadcast['mediaId'],
        'IsPlayable': True,
        'channel_id': 2065,
        'service_id': service_id,
        'livefeed': True,
        'live': program['liveBroadcast'],
        'studio': 'Sexyhot Play',
        'label': label,
        'title': label,
        # 'title': program.get('metadata', program.get('name', '')),
        # 'tvshowtitle': program['name'] if program_name else None,
        'sorttitle': program_name,
        'plot': description,
        # 'plotoutline': datetime.datetime.strftime(program_date, '%H:%M') + ' - ' + datetime.datetime.strftime(program_date + datetime.timedelta(seconds=duration), '%H:%M'),
        'tag': tags,
        'duration': int(duration),
        'dateadded': datetime.datetime.strftime(program_date, '%Y-%m-%d %H:%M:%S'),
        'adult': True,
        'year': title.get('releaseYear'),
        'country': title.get('countries', []),
        'genre': title.get('genresNames', []),
        'cast': title.get('castNames', []),
        'director': title.get('directorsNames', []),
        'writer': title.get('screenwritersNames', []),
        'credits': title.get('artDirectorsNames', []),
        'mpaa': program.get('contentRating'),
        'art': {
            'fanart': (title.get('cover', {}) or {}).get('landscape', fanart) or fanart,
            'thumb': (title.get('cover', {}) or {}).get('landscape', thumb) or thumb,
            'tvshow.poster': (title.get('poster', {}) or {}).get('web'),
            'clearlogo': broadcast['channel']['logo']
        }
    }

    if service_id not in get_authorized_services([service_id]):
        return

    yield item
