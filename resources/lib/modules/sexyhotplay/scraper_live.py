# -*- coding: utf-8 -*-

from resources.lib.modules import control
import os
import time
from resources.lib.modules import client
from resources.lib.modules import util
import datetime

SEXYHOT_LOGO = os.path.join(control.artPath(), 'logo_sexyhot.png')
SEXYHOT_FANART = os.path.join(control.artPath(), 'fanart_sexyhot.png')
SEXYHOT_LIVEID = 6988462


def get_sexyhot_live_id():
    return SEXYHOT_LIVEID


def get_live_channels():

    title = 'SexyHOT'

    simulcast = get_simulcast()

    program_title = simulcast['program_title']

    return [{
        'slug': 'sexyhot',
        'name': '[B]' + title + '[/B] ' + '[I] - ' + program_title + '[/I]',
        'title': title,
        "subtitle": program_title,
        'tvshowtitle': program_title,
        "plot": program_title,
        'sorttitle': 'sexyhot',
        'clearlogo': SEXYHOT_LOGO,
        'fanart': SEXYHOT_FANART,
        'thumb': 'https://live-thumbs.video.globo.com/sexy24ha/snapshot/' + '?v=' + str(int(time.time())),
        'studio': 'SexyHOT',
        'playable': 'true',
        'id': get_sexyhot_live_id(),
        'channel_id': 2065,
        'live': True,
        "mediatype": 'episode',
        'livefeed': 'true',
        'logo': SEXYHOT_LOGO,
        'duration': int(simulcast['duration_seconds']),
        'brplayprovider': 'globosat',
        'adult': True,
        "dateadded": datetime.datetime.strftime(simulcast['start_date'], '%Y-%m-%d %H:%M:%S'),
        'anonymous': True
    }]


def get_simulcast():

    url = 'https://sexyhot.globo.com/api/v1/simulcast'

    simulcast = client.request(url)

    program_title = simulcast['nowEvent']['title']
    program_start = simulcast['nowEvent']['date']
    program_stop = simulcast['nextEvent']['date']

    program_start_date = util.strptime_workaround(program_start, '%Y-%m-%dT%H:%M:%S-03:00')
    program_stop_date = util.strptime_workaround(program_stop, '%Y-%m-%dT%H:%M:%S-03:00')

    utc_timezone = control.get_current_brasilia_utc_offset()

    duration = util.get_total_seconds(program_stop_date - program_start_date)

    return {
        'program_title': program_title,
        'duration_seconds': duration,
        'start_date': program_start_date - datetime.timedelta(hours=(utc_timezone))
    }
