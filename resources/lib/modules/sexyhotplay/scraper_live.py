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
THUMB_URL = 'https://s04.video.glbimg.com/x720/{media_id}.jpg'


def get_broadcast():

    url = 'https://products-jarvis.globo.com/graphql?operationName=getBroadcast&variables=%7B%22mediaId%22%3A%226988462%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22ad75b8bcda1b9b447d5efaeee7229c3c0e278508527d735194a01cf6b1e2b1bb%22%7D%7D'
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

    fanart = FANART_URL.format(media_id=broadcast['mediaId']) + '?v=' + str(int(time.time()))
    thumb = THUMB_URL.format(media_id=broadcast['mediaId']) + '?v=' + str(int(time.time()))

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
