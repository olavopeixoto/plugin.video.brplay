# -*- coding: utf-8 -*-

import requests
import datetime
import time
import traceback
from . import player
from .scraper_vod import FANART
from resources.lib.modules import cache, control


POSTER_URL = 'http://i.cdn.turner.com/tntla/images/portal/fixed/cards/{titleId}_424x636{lang}.jpg'

CHANNEL_MAP = {
    'TNTLA_BR': 'TNT',
    'TNTSLA_BR': 'TNT Series',
    'SPACELA_BR': 'Space',
}

LOGO_MAP = {
    'TNTLA_BR': 'https://turner-latam-prod.akamaized.net/PROD-LATAM/live-channels/tnt_left.png',
    'TNTSLA_BR': 'https://turner-latam-prod.akamaized.net/PROD-LATAM/live-channels/tnts-pt.png',
    'SPACELA_BR': 'https://turner-latam-prod.akamaized.net/PROD-LATAM/live-channels/space.png',
}


PLAYER_HANDLER = player.__name__


def get_live_channels():
    # epg_url = 'http://schedule.dmti.cloud/schedule?from=2020-09-24T00:00:00&to=2020-10-01T00:00:00&feed=TNTLA_BR&mapped=true'
    # title_details = 'http://schedule.dmti.cloud/show-detail?id=1600898464519&mapped=true&output=json'
    # url = 'https://apac.ti-platform.com/AGL/1.0/R/PT/PCTV/TNTGO_LATAM_BR/LIVE/CHANNELS'

    channel_ids = '1000036824,1000036827,1000036819'
    language = 'POR'  # 'ENG'

    epg_url = 'https://api.tntgo.tv/AGL/1.0/a/{language}/PCTV/TNTGO_LATAM_BR/CHANNEL/EPG?channelId={channels}&channel=PCTV'.format(language=language, channels=channel_ids)

    control.log('GET %s' % epg_url)
    channels = requests.get(epg_url).json().get('resultObj', {}).get('channelList', [])
    control.log(channels)

    now_timestamp = to_timestamp(datetime.datetime.now())

    control.log('NOW = %s' % now_timestamp)

    results = []
    for channel in channels:

        programmes = channel.get('programList', []) or []
        programme = next((p for p in programmes if p.get('startTime', 0) <= now_timestamp <= p.get('endTime', 0)), {})

        control.log(programme)

        program_details_url = 'http://schedule.dmti.cloud/show-detail?id={id}&mapped=true&output=json'.format(id=programme.get('contentId', ''))

        control.log('GET %s' % program_details_url)

        program_details_response = cache.get(requests.get, 780, program_details_url, table='tntplay')

        control.log(program_details_response.status_code)
        control.log(program_details_response.text)

        try:
            program_details_response = program_details_response.json()
        except:
            control.log(traceback.format_exc(), control.LOGERROR)
            program_details_response = {}

        details_key = next(iter(program_details_response.keys()), None)
        details = program_details_response.get(details_key, {}) or {}

        channel_name = CHANNEL_MAP.get(channel.get('callLetter'), channel.get('channelName', '')) or channel.get('channelName', '')

        title = programme.get('title', '')
        subtitle = programme.get('subtitle', '') if programme.get('subtitle', '') != title else u''
        plot = programme.get('contentDescription', '')
        plot_outline = programme.get('shortDescription', '')

        start_time = datetime.datetime.utcfromtimestamp(programme.get('startTime', 0))
        end_time = datetime.datetime.utcfromtimestamp(programme.get('endTime', 0))

        lang = details.get('lang', '')

        poster_lang = '_pt' if lang == 'pt' else ''

        poster_url = POSTER_URL.format(titleId=details.get('titleId', ''), lang=poster_lang)

        logo = LOGO_MAP.get(channel.get('callLetter'))

        program_name = title + (u': ' + subtitle if subtitle else u'')

        program_time_desc = datetime.datetime.strftime(start_time, '%H:%M') + ' - ' + datetime.datetime.strftime(end_time, '%H:%M')
        plot = '%s | %s' % (program_time_desc, plot)

        tags = [program_time_desc]

        label = u"[B]" + channel_name + u"[/B][I] - " + program_name + u"[/I]"

        results.append({
            'handler': PLAYER_HANDLER,
            'method': player.Player.playlive.__name__,
            'id': channel.get('channelId', ''),
            'IsPlayable': True,
            'livefeed': True,
            'label': label,
            'title': label,
            # 'title': subtitle,
            # 'originaltitle': details.get('originalTitle'),
            'studio': 'TNT Play',
            'tag': tags,
            'tvshowtitle': title,
            'sorttitle': program_name,
            'channel_id': channel.get('channelId', ''),
            'dateadded': datetime.datetime.strftime(start_time, '%Y-%m-%d %H:%M:%S'),
            'plot': plot,
            'plotoutline': plot_outline,
            'duration': programme.get('duration', 0) or 0,
            'adult': False,
            'cast': details.get('actorList', []).split(','),
            'director': details.get('directorList', []).split(','),
            'genre': details.get('genreList'),
            'rating': details.get('rate'),
            'year': details.get('releaseYear'),
            'country': details.get('country'),
            'episode': details.get('episode'),
            'season': details.get('season'),
            'art': {
                'thumb': poster_url,
                'tvshow.poster': poster_url,
                'clearlogo': logo,
                'fanart': FANART,
            }
        })

    return results


def to_timestamp(date):
    return int((time.mktime(date.timetuple()) + date.microsecond / 1000000.0))
