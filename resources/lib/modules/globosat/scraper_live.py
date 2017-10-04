# -*- coding: utf-8 -*-

import os, datetime, time
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import util

GLOBOSAT_URL = 'http://globosatplay.globo.com'
GLOBOSAT_API_URL = 'http://api.vod.globosat.tv/globosatplay'
GLOBOSAT_API_AUTHORIZATION = 'token b4b4fb9581bcc0352173c23d81a26518455cc521'
GLOBOSAT_API_CHANNELS = GLOBOSAT_API_URL + '/channels.json?page=%d'
COMBATE_SIMULCAST_URL = 'http://api.simulcast.globosat.tv/combate'
GLOBOSAT_SIMULCAST_URL = 'http://api.simulcast.globosat.tv/globosatplay'
PREMIERE_LIVE_JSON = GLOBOSAT_URL + '/premierefc/ao-vivo/add-on/jogos-ao-vivo/520142353f8adb4c90000008.json'
PREMIERE_UPCOMING_JSON = GLOBOSAT_URL + '/premierefc/ao-vivo/add-on/proximos-jogos/520142353f8adb4c90000006.json'
INFO_URL = 'http://api.globovideos.com/videos/%s/playlist'
PREMIERE_24H_SIMULCAST = 'https://api-simulcast.globosat.tv/v1/premiereplay/'

artPath = control.artPath()

COMBATE_LOGO = os.path.join(artPath, 'logo_combate.png')
PREMIERE_LOGO = os.path.join(artPath, 'logo_premiere.png')
PREMIERE_FANART = os.path.join(artPath, 'fanart_premiere_720.jpg')


def get_basic_live_channels():

    live = []

    page = 1
    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}
    channel_info = client.request(GLOBOSAT_API_CHANNELS % page, headers=headers)
    results = channel_info['results']
    # loop through pages
    while channel_info['next'] is not None:
        page += 1
        channel_info = client.request(GLOBOSAT_API_CHANNELS % page, headers=headers)
        results.update(channel_info['results'])

    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}
    channel_info = client.request(GLOBOSAT_SIMULCAST_URL, headers=headers)
    simulcast_results = channel_info['results']

    for result in results:
        if len(result['transmissions']) == 0: pass

        for transmission in result['transmissions']:
            simulcast_result = next((result for result in simulcast_results if result['id_midia_live_play'] == transmission['items'][0]['id_globo_videos']), None)
            simulcast_data = __get_simulcast_data(simulcast_result) if not simulcast_result is None else {}

            item = {
                    'slug': result['slug'],
                    'name': transmission['title'],
                    'studio': transmission['title'],
                    'title': transmission['title'],
                    'thumb': 'https://live-thumbs.video.globo.com/univ24ha/snapshot/?v=' + str(int(time.time())),
                    'plot': None,
                    'duration': None,
                    'brplayprovider': 'globosat',
                    'playable': 'true'
                    }

            item.update(simulcast_data)

            item.update({
                    'sorttitle': transmission['title'],
                    'logo': result['color_logo'],
                    'clearlogo': result['color_logo'],
                    'clearart': result['white_logo'],
                    'banner': result['white_horizontal_logo'],
                    'color': result['color'],
                    'fanart': transmission['items'][0]['image'],
                    'id': transmission['items'][0]['id_globo_videos'],
                    'channel_id': transmission['id_channel'],
                    'brplayprovider': 'globosat',
                    'thumb': item['thumb'] if 'thumb' in item and item['thumb'] is not None else None,
                    'livefeed': 'true'
                    })

            live.append(item)

    return live

def get_combate_live_channels():

    #COMBATE
    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}
    channel_info = client.request(COMBATE_SIMULCAST_URL, headers=headers)
    results = channel_info['results']

    live = []

    for result in results:
        channel = __get_simulcast_data(result)
        channel.update({
            'logo': COMBATE_LOGO,
            'clearlogo': COMBATE_LOGO
        })
        live.append(channel)

    return live


def get_premiere_live_channels():

    live = []

    offline = False
    headers = {'Accept-Encoding': 'gzip'}
    live_games = client.request(PREMIERE_LIVE_JSON, headers=headers)['jogos']
    if len(live_games) == 0:
        offline = True
        live_games = client.request(PREMIERE_UPCOMING_JSON, headers=headers)['jogos']

    if not live_games:
        return []

    tvshowtitle = u'Live' if not offline else u'Próximos Jogos'

    if len(live_games) == 1:
        return [__get_game_data(live_games[0], {
            'slug': 'premiere-fc',
            'studio': 'Premiere FC',
            'sorttitle': 'Premiere FC',
            'logo': PREMIERE_LOGO,
            'clearlogo': PREMIERE_LOGO,
            'fanart': PREMIERE_FANART,
            'thumb': PREMIERE_FANART,
            'channel_id': 1995
        }, offline)]

    if len(live_games) > 1:
        title = '%s jogos programados' % len(live_games)
        extra_games_str = ' + ' + str(len(live_games) - 1) + ' jogos'
    else:
        title = ''
        extra_games_str = ''

    #PREMIERE
    live.append({
        'slug': 'premiere-fc',
        'name': 'Assista Agora' if not offline else u'Próximos Jogos',
        'studio': 'Premiere FC',
        'title': 'Ao Vivo' if not offline else u'Veja a Programação',
        'tvshowtitle': tvshowtitle,
        'sorttitle': 'Premiere FC',
        'logo': PREMIERE_LOGO,
        'clearlogo': PREMIERE_LOGO,
        'fanart': PREMIERE_FANART,
        'thumb': PREMIERE_FANART,
        'playable': 'false',
        'plot': title,
        'id': None,
        'channel_id': 1995,
        'duration': None,
        'isFolder': 'true',
        'logo': live_games[0]['time_mandante']['escudo'],
        'logo2': live_games[0]['time_visitante']['escudo'],
        'initials1': live_games[0]['time_mandante']['sigla'],
        'initials2': live_games[0]['time_visitante']['sigla'],
        'gamedetails': live_games[0]['campeonato'] + extra_games_str,
    })

    return live


def get_premiere_live_24h_channels():

    live = []

    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}
    live_channels = client.request(PREMIERE_24H_SIMULCAST, headers=headers)

    studio = 'Premiere Clubes'

    control.log("-- PREMIERE CLUBES SIMULCAST: %s" % repr(live_channels))

    for channel_data in live_channels:
        program_date = util.strptime_workaround(channel_data['starts_at'][0:19]) + datetime.timedelta(hours=3) + util.get_utc_delta() if channel_data and 'starts_at' in channel_data and channel_data['starts_at'] is not None else datetime.datetime.now()
        live_text = ' (' + control.lang(32004) + ')' if channel_data['live'] else ''
        title = studio + ('[I] - ' + (channel_data['name'] or '') + '[/I]' if channel_data['name'] else '') + live_text

        live.append({
            'slug': 'premiere-fc',
            'name': title,
            'studio': studio,
            'title': channel_data['description'],
            'tvshowtitle': channel_data['name'],
            'sorttitle': studio,
            'logo': PREMIERE_LOGO,
            'clearlogo': PREMIERE_LOGO,
            'fanart': channel_data['image_url'],
            'thumb': channel_data['snapshot_url'] + '?v=' + str(int(time.time())),
            'playable': 'true',
            'plot': channel_data['description'],
            'id': int(channel_data['media_globovideos_id']),
            'channel_id': int(channel_data['channel_globovideos_id']),
            'duration': int(channel_data['duration'] or 0) / 1000,
            'isFolder': 'false',
            'live': channel_data['live'],
            'livefeed': 'true',
            'brplayprovider': 'globosat',
            'dateadded': datetime.datetime.strftime(program_date, '%Y-%m-%d %H:%M:%S'),
        })

    return live


def get_premiere_games(meta):

    live = []
    offline = False

    headers = {'Accept-Encoding': 'gzip'}
    live_games = client.request(PREMIERE_LIVE_JSON, headers=headers)['jogos']
    if len(live_games) == 0:
        offline=True
        live_games = client.request(PREMIERE_UPCOMING_JSON, headers=headers)['jogos']

    for game in live_games:
        livemeta = meta.copy()
        #offlineText = u' (' + game['data'] + u')' if offline else u''
        #tvshowtitle = game['campeonato'] + u': ' + game['time_mandante']['nome'] + u' x ' + game['time_visitante']['nome'] + u' (' + game['estadio'] + u')'
        #plot =  game['campeonato'] + u': ' + game['time_mandante']['nome'] + u' x ' + game['time_visitante']['nome'] + u' (' + game['estadio'] + u')' + u'. ' + game['data']
        live.append(__get_game_data(game, livemeta, offline))

    return live

def __get_game_data(game, meta, offline):
    meta.update({
        'name': game['time_mandante']['nome'] + u' x ' + game['time_visitante']['nome'],
        'label2': game['time_mandante']['nome'] + u' x ' + game['time_visitante']['nome'],
        'playable': 'true' if game['id_midia'] != None else 'false',
        'plot': game['estadio'],
        'plotoutline': game['data'],
        'id': game['id_midia'],
        'logo': game['time_mandante']['escudo'],
        'logo2': game['time_visitante']['escudo'],
        'initials1': game['time_mandante']['sigla'],
        'initials2': game['time_visitante']['sigla'],
        'isFolder': 'false',
        'mediatype': 'episode',
        'tvshowtitle': game['time_mandante']['sigla'] + u' x ' + game['time_visitante']['sigla'],
        'title': game['campeonato'],
        'brplayprovider': 'globosat',
        'gamedetails': None,
        'livefeed': str(offline).lower()
    })
    return meta

def __get_simulcast_data(result):

    live_text = ' (' + control.lang(32004) + ')' if result['live'] else ''
    program_date = util.strptime_workaround(result['day'], '%d/%m/%Y %H:%M') + datetime.timedelta(hours=3) + util.get_utc_delta() if not result['day'] is None else datetime.datetime.now()
    # program_local_date_string = datetime.datetime.strftime(program_date, '%d/%m/%Y %H:%M')
    # duration_str = (' - ' + str(result['duration'] or 0) + ' minutos') if (result['duration'] or 0) > 0 else ''
    title = result['channel']['title'] + ('[I] - ' + (result['title'] or '') + '[/I]' if result['title'] else '') + live_text


    return {
        'slug': result['channel']['title'].lower(),
        'studio': result['channel']['title'],
        'name': title,
        'title': result['subtitle'],
        'tvshowtitle': result['title'] if result['title'] else None,
        'sorttitle': result['channel']['title'],
        # 'logo': None,
        # 'color': None,
        'fanart': result['thumb_cms'],
        'thumb': result['channel']['url_snapshot'] + '?v=' + str(int(time.time())),
        'live': result['live'],
        'playable': 'true',
        'plot': ' ', #(result['title'] or '') + ' - ' + (result['subtitle'] or ''), #program_local_date_string + duration_str + '\n' + (result['title'] or '') + '\n' + (result['subtitle'] or ''),
        'plotoutline': datetime.datetime.strftime(program_date, '%H:%M') + ' - ' + (datetime.datetime.strftime(program_date + datetime.timedelta(minutes=(result['duration'] or 0)), '%H:%M') if (result['duration'] or 0) > 0 else 'N/A'),
        # 'programTitle': result['subtitle'],
        'id': result['id_midia_live_play'],
        'channel_id': result['channel']['id_globo_videos'],
        'duration': int(result['duration'] or 0) * 60,
        # 'tagline': result['subtitle'],
        # 'date': datetime.datetime.strftime(program_date, '%d.%m.%Y'),
        # 'aired': datetime.datetime.strftime(program_date, '%Y-%m-%d'),
        'dateadded': datetime.datetime.strftime(program_date, '%Y-%m-%d %H:%M:%S'),
        # 'StartTime': datetime.datetime.strftime(program_date, '%H:%M:%S'),
        # 'EndTime': datetime.datetime.strftime(program_date + datetime.timedelta(minutes=(result['duration'] or 0)), '%H:%M:%S'),
        'brplayprovider': 'globosat'
    }