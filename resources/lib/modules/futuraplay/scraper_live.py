# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import client
import datetime,re
from resources.lib.modules import cache
from resources.lib.modules import util
import time

CLEAR_LOGO_WHITE = 'http://static.futuraplay.org/img/futura_tracobranco.png'
CLEAR_LOGO_COLOR = 'http://static.futuraplay.org/img/futura_tracoverde.png'
FUTURA_LOGO = 'http://static.futuraplay.org/img/futura_rodape.png'

FUTURA_FANART = 'http://static.futuraplay.org/img/og-image.jpg'
FUTURA_THUMB = 'https://live-thumbs.video.globo.com/futura24ha/snapshot/'  # 'https://s03.video.glbimg.com/x720/4500346.jpg'


def get_live_id():
    return 4500346


def get_live_channels():

    utc_timezone = control.get_current_brasilia_utc_offset()

    today = datetime.datetime.utcnow() + datetime.timedelta(hours=(utc_timezone))
    today_string = datetime.datetime.strftime(today, '%Y-%m-%d')

    url = 'http://www.futuraplay.org/api/programacao/%s/' % today_string

    response = cache.get(client.request, 1, url)

    programs = [slot for slot in response['exibicoes'] if util.strptime_workaround(slot['dia'], '%d/%m/%Y %H:%M') < today]

    program = programs[-1]

    program_datetime = util.strptime_workaround(program['dia'], '%d/%m/%Y %H:%M') - datetime.timedelta(hours=(utc_timezone))

    start_time = util.strptime_workaround(program['hora'], '%H:%M') - datetime.timedelta(hours=(utc_timezone))
    end_time = util.strptime_workaround(program['fim'], '%H:%M:%S') - datetime.timedelta(hours=(utc_timezone))

    return [{
        'slug': 'futura',
        'name': 'Futura ' + '[I] - ' + program['subtitulo'] + '[/I]',
        'title': program['titulo'] if program['titulo'] != program['titulo_serie'] else None,
        "subtitle": program['subtitulo'] if program['subtitulo'] != program['titulo'] else None,
        "plot": program['sinopse'],
        'tvshowtitle': program['titulo_serie'],
        'sorttitle': 'Futura',
        'clearlogo': CLEAR_LOGO_COLOR,
        'fanart': FUTURA_FANART,
        'thumb': FUTURA_THUMB + '?v=' + str(int(time.time())),
        'studio': 'Futura',
        'playable': 'true',
        'id': get_live_id(),
        'channel_id': 1985,
        'live': False, # use vod player
        "mediatype": 'episode',
        'livefeed': 'true' if program['ao_vivo'] is True or program['ao_vivo'] == 'true' else 'false',
        'logo': CLEAR_LOGO_COLOR,
        'duration': int(program['duracao']) * 60,
        "plotoutline": datetime.datetime.strftime(start_time, '%H:%M') + ' - ' + datetime.datetime.strftime(end_time, '%H:%M'),
        "dateadded": datetime.datetime.strftime(program_datetime, '%Y-%m-%d %H:%M:%S'),
        'brplayprovider': 'globoplay',
        'anonymous': True
    }]