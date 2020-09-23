# -*- coding: utf-8 -*-

from resources.lib.modules import control
import os
import time
from resources.lib.modules import client
from resources.lib.modules import util
import datetime

SEXYHOT_LOGO = os.path.join(control.artPath(), 'logo_sexyhot.png')
SEXYHOT_FANART = os.path.join(control.artPath(), 'fanart_sexyhot.png')

FANART_URL = 'http://s01.video.glbimg.com/x720/{media_id}.jpg'
# THUMB_URL = 'https://s04.video.glbimg.com/x720/{media_id}.jpg'
THUMB_URL = 'https://live-thumbs.video.globo.com/sexy24ha/snapshot/'


def get_broadcast():

    url = 'https://products-jarvis.globo.com/graphql?query=query%20getBroadcast%28%24mediaId%3A%20ID%21%2C%20%24coordinates%3A%20CoordinatesData%2C%20%24logoScale%3A%20BroadcastChannelTrimmedLogoScales%20%3D%20X56%29%20%7B%0A%20%20broadcast%28mediaId%3A%20%24mediaId%2C%20coordinates%3A%20%24coordinates%29%20%7B%0A%20%20%20%20mediaId%0A%20%20%20%20mutedMediaId%0A%20%20%20%20promotionalMediaId%0A%20%20%20%20promotionalText%0A%20%20%20%20geoblocked%0A%20%20%20%20geofencing%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20trimmedLogo%28scale%3A%20%24logoScale%29%0A%20%20%20%20%20%20slug%0A%20%20%20%20%7D%0A%20%20%20%20imageOnAir%3A%20imageOnAir%28scale%3A%20X720%29%0A%20%20%20%20epgCurrentSlots%28limit%3A%203%29%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%7D%0A%20%20%20%20media%20%7B%0A%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D&operationName=getBroadcast&variables=%7B%22logoScale%22%3A%22X42%22%2C%22mediaId%22%3A%226988462%22%7D'
    headers = {
        'x-client-version': '0.4.3',
        'x-device-id': 'desktop',
        'x-platform-id': 'web',
        'x-tenant-id': 'sexy-hot'
    }
    response = client.request(url, headers=headers)

    channels = []

    broadcast = response['data']['broadcast']

    program = broadcast['epgCurrentSlots'][0]

    live_text = ' (' + control.lang(32004) + ')' if program['liveBroadcast'] else ''
    name = "[B]" + broadcast['channel']['name'] + "[/B]" + (
        '[I] - ' + (program['name'] or '') + '[/I]' if program['name'] else '') + live_text

    fanart = broadcast['imageOnAir']  # FANART_URL.format(media_id=broadcast['mediaId']) + '?v=' + str(int(time.time()))
    thumb = THUMB_URL + '?v=' + str(int(time.time()))  # THUMB_URL.format(media_id=broadcast['mediaId']) + '?v=' + str(int(time.time()))

    program_date = datetime.datetime.fromtimestamp(program['startTime'])
    endTime = datetime.datetime.fromtimestamp(program['endTime'])
    duration = (endTime - program_date).total_seconds()

    program_name = program['name'] + (u': ' + program['metadata'] if program['metadata'] else u'')

    item = {
        'slug': broadcast['channel']['slug'],
        'studio': broadcast['channel']['name'],
        'name': name,
        'title': program_name,
        'tvshowtitle': program['name'] if program_name else None,
        'sorttitle': broadcast['channel']['name'],
        'logo': broadcast['channel']['logo'],
        'fanart': fanart,
        'thumb': thumb,
        'live': program['liveBroadcast'],
        'playable': 'true',
        'plot': program['description'] or '' if not control.isFTV else ' ',
        'plotoutline': datetime.datetime.strftime(program_date, '%H:%M') + ' - ' + datetime.datetime.strftime(
            program_date + datetime.timedelta(seconds=duration), '%H:%M'),
        'id': broadcast['mediaId'],
        'channel_id': 2065,
        'duration': int(duration),
        'dateadded': datetime.datetime.strftime(program_date, '%Y-%m-%d %H:%M:%S'),
        'brplayprovider': 'globosat',
        'livefeed': 'true',
        'clearlogo': broadcast['channel']['logo'],
        'clearart': None,
        'banner': None,
    }

    channels.append(item)

    return channels
