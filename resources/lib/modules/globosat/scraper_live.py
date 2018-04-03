# -*- coding: utf-8 -*-

import os, datetime, time
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import util
from resources.lib.modules import workers
from resources.lib.modules import cache
import re
import json
import csv

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

GLOBOSAT_TRANSMISSIONS = GLOBOSAT_API_URL + '/transmissions.json?page=%s'
GLOBOSAT_LIVE_JSON = GLOBOSAT_URL + '/xhr/transmissoes/ao-vivo.json'

#UNIVERSAL CHANNEL
#https://api.globovideos.com/videos/5497510/playlist

artPath = control.artPath()

COMBATE_LOGO = os.path.join(artPath, 'logo_combate.png')
PREMIERE_LOGO = os.path.join(artPath, 'logo_premiere.png')
PREMIERE_FANART = os.path.join(artPath, 'fanart_premiere_720.jpg')  # https://s02.video.glbimg.com/x720/2752761.jpg


def get_basic_live_channels():
    # return get_basic_live_channels_from_simulcast_only() + get_sportv4_live()
    return get_basic_live_channels_from_api() + get_sportv4_live()
    # return get_transmissions_live_channels_from_json() + get_sportv4_live()


def get_basic_live_channels_from_simulcast_only():
    live = []
    simulcast_results = []

    __get_globosat_simulcast(simulcast_results)

    for simulcast_result in simulcast_results:

        simulcast_data = __get_simulcast_data(simulcast_result) if not simulcast_result is None else {}

        item = {
            'plot': None,
            'duration': None,
            'brplayprovider': 'globosat',
            'playable': 'true',
            'livefeed': 'true'
        }

        item.update(simulcast_data)

        live.append(item)

    return live


def get_transmissions_live_channels_from_json():
    transmissions = []

    threads = [
        workers.Thread(__get_transmissions_page, transmissions, 1),
        workers.Thread(__get_transmissions_page, transmissions, 2)
    ]
    [i.start() for i in threads]
    [i.join() for i in threads]

    channels = []

    for transmission in transmissions:
        updated_at = util.strptime_workaround(transmission['updated_at'], '%Y-%m-%dT%H:%M:%SZ')

        if updated_at > datetime.datetime.utcnow() - datetime.timedelta(hours=24):
            if transmission['status'] == "ativa":
                for item in transmission['items']:

                    title = transmission['title']
                    if item['title'] != str(item['id_globo_videos']):
                        title = title + item['title']
                    channel = {
                        'slug': str(item['id_globo_videos']),
                        'name': title,
                        'studio': transmission['title'],
                        'title': title,
                        'plot': None,
                        'duration': None,
                        'sorttitle': title,
                        'thumb': item['image'],
                        'logo': None,
                        'clearlogo': None,
                        'clearart': None,
                        'banner': None,
                        'color': None,
                        'fanart': None,
                        'id': item['id_globo_videos'],
                        'channel_id': transmission['id_channel'],
                        'brplayprovider': 'globosat',
                        'playable': 'true',
                        'livefeed': 'true',
                        # 'dateadded': datetime.datetime.strftime(updated_at, '%Y-%m-%d %H:%M:%S')
                    }

                    channels.append(channel)

    return channels


def get_sportv4_live():

    title = 'E-SporTV'
    logo = 'https://s.glbimg.com/pc/gm/media/dc0a6987403a05813a7194cd0fdb05be/2014/11/14/74c21fae4de1e884063ff2329950b9b4.png' #os.path.join(control.artPath(), 'sportv4.png'),
    id = 5125939

    return [{
                'slug': 'sportv4',
                'name': "[B]" + title + "[/B]",
                'studio': title,
                'title': title,
                'sorttitle': title,
                'thumb': 'https://live-thumbs.video.globo.com/spo424ha/snapshot/?v=' + str(int(time.time())),
                'logo': logo,
                'clearlogo': logo,
                'clearart': logo,
                'banner': None,
                'color': None,
                'fanart': 'https://s03.video.glbimg.com/x720/%s.jpg' % id,
                'id': id,
                'channel_id': 2024,
                'brplayprovider': 'globosat',
                'playable': 'true',
                'livefeed': 'true',
                'dateadded': None,
                'plot': None,
                'duration': None,
            }]


def get_universal_live():

    studio = 'Universal Channel'
    logo = 'https://s.glbimg.com/pc/gm/media/dc0a6987403a05813a7194cd0fdb05be/2014/11/14/2eac19898a33a0fcbfbe9fa3265f70e5.png'
    id = 5497510

    program = __get_universal_epg()
    title = program['title'] or studio
    plot = program['plot']
    dateadded = program['dateadded']
    duration = program['duration']
    tvshowtitle = program['tvshowtitle']
    episode = program['episode']
    originaltitle = program['original_title']
    year = program['year']
    director = program['director']

    label = "[B]" + studio + '[/B][I] - ' + tvshowtitle + ((' Ep. ' + episode) if episode else '') + (' / ' if tvshowtitle else '') + title  + '[/I]'

    return [{
                'slug': 'universal-channel',
                'name': label,
                'studio': studio,
                'title': title,
                'sorttitle': studio,
                'tvshowtitle': tvshowtitle,
                "originaltitle": originaltitle,
                'year': year,
                'director': director,
                'thumb': 'https://live-thumbs.video.globo.com/univ24ha/snapshot/?v=' + str(int(time.time())),
                'logo': logo,
                'clearlogo': logo,
                'clearart': logo,
                'banner': None,
                'color': None,
                'fanart': 'https://s03.video.glbimg.com/x720/5497510.jpg',
                'id': id,
                'channel_id': 1997,
                'brplayprovider': 'globosat',
                'playable': 'true',
                'livefeed': 'true',
                'dateadded': dateadded,  # datetime.datetime.strftime(updated_at, '%Y-%m-%d %H:%M:%S'),
                'plot': plot,
                'duration': duration
            }]


def __get_universal_epg():
    utc_timezone = control.get_current_brasilia_utc_offset()
    utc_now = datetime.datetime.today().utcnow()
    now = utc_now + datetime.timedelta(hours=utc_timezone)
    epg_url = 'http://ancine.grade.globosat.tv/programada/01253766000140_UniversalChannel%s.csv' % datetime.datetime.strftime(now, '%Y%m%d')  # '20180205'
    epg_csv = cache.get(client.request, 2, epg_url)

    epg_data = csv.reader(epg_csv.splitlines(), delimiter='\\', quotechar='"')

    for program in list(epg_data):
        p_date = program[0]
        p_start = program[1]
        p_end = program[2]
        original_title = program[3]
        director = program[4]
        title = program[5]
        tvshow = program[6]
        episode = program[7]
        country = program[8]
        year = program[9]
        rating = program[10]
        plot = program[11]

        start_time = util.strptime_workaround(p_date + ' ' + p_start, '%Y%m%d %H:%M') - datetime.timedelta(hours=(utc_timezone))
        end_time = util.strptime_workaround(p_date + ' ' + p_end, '%Y%m%d %H:%M') - datetime.timedelta(hours=(utc_timezone))

        start_hour = p_start.split(':')[0]
        end_hour = p_end.split(':')[0]
        if int(end_hour) < int(start_hour):
            end_time = end_time + datetime.timedelta(days=1)

        if end_time > utc_now > start_time:

            studio = 'Universal Channel'

            return {
                'original_title': original_title,
                'director': director,
                'title': title,
                'tvshowtitle': tvshow,
                'episode': episode,
                'country': country,
                'year': year,
                'rating': rating,
                'plot': plot,
                'duration': util.get_total_seconds(end_time - start_time),
                "dateadded": datetime.datetime.strftime(start_time + util.get_utc_delta(), '%Y-%m-%d %H:%M:%S'),
                "plotoutline": datetime.datetime.strftime(start_time + util.get_utc_delta(), '%H:%M') + ' - ' + datetime.datetime.strftime(end_time + util.get_utc_delta(), '%H:%M'),
            }

    return {
                'original_title': None,
                'director': None,
                'title': None,
                'tvshowtitle': None,
                'episode': None,
                'country': None,
                'year': None,
                'rating': None,
                'plot': None,
                'duration': None,
                "dateadded": None
            }

def __get_transmissions_page(results, page=1):
    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}
    transmissions = client.request(GLOBOSAT_TRANSMISSIONS % page, headers=headers)
    if transmissions and 'results' in transmissions:
        results += transmissions['results']

    # loop through pages
    # while channel_info['next'] is not None:
    #     page += 1
    #     channel_info = client.request(GLOBOSAT_TRANSMISSIONS % page, headers=headers)
    #     results += channel_info['results']


def get_bbb_channels():
    signals = []

    html = cache.get(client.request, 1, 'https://globosatplay.globo.com/bbb/ao-vivo/')

    if not html:
        return signals

    config_string_matches = re.findall('window.initialState\s*=\s*({.*})', html)

    if not config_string_matches or len(config_string_matches) == 0:
        return signals

    config_string = config_string_matches[0]

    try:
        config_json = json.loads(config_string)
    except Exception as ex:
        control.log("get_bbb_channels ERROR: %s" % ex)
        return signals

    channels = config_json['channels']
    channel = channels['channels'][0]
    for index, signal in enumerate(channels['signals']):
        title = signal['title']
        logo = channel['logotipoXl']
        signals.append({
            'slug': channel['productId'] + str(index),
            'name': title,
            'studio': 'Rede Globo',
            'title': title,
            'sorttitle': title,
            'thumb': signal['thumbUrl'] + '?v=' + str(int(time.time())),
            'logo': logo,
            'clearlogo': logo,
            'clearart': logo,
            'banner': None,
            'color': None,
            'fanart': signal['background'],
            'id': signal['videoId'],
            'channel_id': channel['id'],
            'brplayprovider': 'globosat',
            'playable': 'true',
            'livefeed': 'true',
            'dateadded': None,  # datetime.datetime.strftime(updated_at, '%Y-%m-%d %H:%M:%S'),
            'plot': None,
            'duration': None,
        })

    return signals


def get_basic_live_channels_from_api():

    live = []
    results = []
    simulcast_results = []

    threads = [
        workers.Thread(__get_channels_from_api, results),
        workers.Thread(__get_globosat_simulcast, simulcast_results)
    ]
    [i.start() for i in threads]
    [i.join() for i in threads]

    channel_id_list = []

    for result in results:
        if len(result['transmissions']) == 0:
            pass

        for transmission in result['transmissions']:
            simulcast_result = next((result for result in simulcast_results if result['id_midia_live_play'] == transmission['items'][0]['id_globo_videos']), None)
            simulcast_data = __get_simulcast_data(simulcast_result) if not simulcast_result is None else {}

            item = {
                    'slug': result['slug'],
                    'name': transmission['title'],
                    'studio': transmission['title'],
                    'title': transmission['title'],
                    'thumb': None,
                    'plot': None,
                    'duration': None,
                    'brplayprovider': 'globosat',
                    'playable': 'true'
                    }

            item.update(simulcast_data)

            item.update({
                    'sorttitle': transmission['title'],
                    'logo': result['color_logo'] or result['white_logo'],
                    'clearlogo': result['color_logo'] or result['white_logo'],
                    'clearart': result['white_logo'] or result['color_logo'],
                    'banner': result['white_horizontal_logo'],
                    'color': result['color'],
                    'fanart': transmission['items'][0]['image'],
                    'id': transmission['items'][0]['id_globo_videos'],
                    'channel_id': transmission['id_channel'],
                    'brplayprovider': 'globosat',
                    'thumb': item['thumb'] if 'thumb' in item and item['thumb'] is not None else 'https://s03.video.glbimg.com/x720/%s.jpg' % transmission['items'][0]['id_globo_videos'],
                    'livefeed': 'true'
                    })

            live.append(item)

            channel_id_list.append(int(item['channel_id']))

    for simulcast_result in simulcast_results:
        if simulcast_result is None or int(simulcast_result['channel']['id_globo_videos']) in channel_id_list:
            continue

        simulcast_data = __get_simulcast_data(simulcast_result)

        item = {
                'clearlogo': None,
                'clearart': None,
                'banner': None,
                'livefeed': 'true'
                }

        item.update(simulcast_data)

        live.append(item)

    return live


def __get_channels_from_api(results):
    page = 1
    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}
    channel_info = client.request(GLOBOSAT_API_CHANNELS % page, headers=headers)
    results += channel_info['results']
    # loop through pages
    while channel_info['next'] is not None:
        page += 1
        channel_info = client.request(GLOBOSAT_API_CHANNELS % page, headers=headers)
        results += channel_info['results']


def __get_globosat_simulcast(simulcast_results):
    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}
    channel_info = client.request(GLOBOSAT_SIMULCAST_URL, headers=headers)
    simulcast_results += channel_info['results']


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
        plural = 's' if len(live_games) > 1 else ''
        title = '%s jogo%s programado%s' % (len(live_games), plural, plural)
        extra_plural = 's' if len(live_games) - 1 > 1 else ''
        extra_games_str = ' + ' + str(len(live_games) - 1) + ' jogo' + extra_plural
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
        'brplayprovider': 'premierefc'
    })

    return live


def get_premiere_live_24h_channels():

    live = []

    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}
    live_channels = client.request(PREMIERE_24H_SIMULCAST, headers=headers)

    studio = 'Premiere Clubes'

    # control.log("-- PREMIERE CLUBES SIMULCAST: %s" % repr(live_channels))

    utc_timezone = control.get_current_brasilia_utc_offset()

    for channel_data in live_channels:
        program_date = util.strptime_workaround(channel_data['starts_at'][0:19]) + datetime.timedelta(hours=-utc_timezone) + util.get_utc_delta() if channel_data and 'starts_at' in channel_data and channel_data['starts_at'] is not None else None
        live_text = ' (' + control.lang(32004) + ')' if channel_data['live'] else ''
        studio = channel_data['channel']['title']
        title = studio + ('[I] - ' + channel_data['name'] + '[/I]' if channel_data['name'] else '') + live_text

        live_channel = {
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
            'channel_id': int(channel_data['channel']['globovideos_id']),
            'duration': int(channel_data['duration'] or 0) / 1000,
            'isFolder': 'false',
            'live': channel_data['live'],
            'livefeed': 'true',
            'brplayprovider': 'globosat'
        }

        if program_date is not None:
            live_channel.update({'dateadded': datetime.datetime.strftime(program_date, '%Y-%m-%d %H:%M:%S')})

        live.append(live_channel)

    return live


def get_premiere_games(meta={}, online_only=False):

    live = []
    offline = False

    headers = {'Accept-Encoding': 'gzip'}
    live_games = client.request(PREMIERE_LIVE_JSON, headers=headers)['jogos']
    if len(live_games) == 0 and not online_only:
        offline=True
        live_games = client.request(PREMIERE_UPCOMING_JSON, headers=headers)['jogos']

    for game in live_games:
        livemeta = meta.copy()
        live.append(__get_game_data(game, livemeta, offline))

    return live


def __get_game_data(game, meta, offline):
    # offlineText = u' (' + game['data'] + u')' if offline else u''
    # tvshowtitle = game['campeonato'] + u': ' + game['time_mandante']['nome'] + u' x ' + game['time_visitante']['nome'] + u' (' + game['estadio'] + u')'
    plot =  game['campeonato'] + u': ' + game['time_mandante']['nome'] + u' x ' + game['time_visitante']['nome'] + u' (' + game['estadio'] + u')' + u'. ' + game['data']
    label = game['time_mandante']['nome'] + u' x ' + game['time_visitante']['nome']
    meta.update({
        'name': ((game['data'] + u' - ') if offline else u'') + label if not control.isFTV else label,
        'label2': game['time_mandante']['nome'] + u' x ' + game['time_visitante']['nome'],
        'playable': 'true' if game['id_midia'] is not None else 'false',
        'plot': game['estadio'] if control.isFTV else plot,
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

    utc_timezone = control.get_current_brasilia_utc_offset()

    live_text = ' (' + control.lang(32004) + ')' if result['live'] else ''
    program_date = util.strptime_workaround(result['day'], '%d/%m/%Y %H:%M') + datetime.timedelta(hours=-utc_timezone) + util.get_utc_delta() if not result['day'] is None else datetime.datetime.now()
    # program_local_date_string = datetime.datetime.strftime(program_date, '%d/%m/%Y %H:%M')
    # duration_str = (' - ' + str(result['duration'] or 0) + ' minutos') if (result['duration'] or 0) > 0 else ''

    name = "[B]" + result['channel']['title'] + "[/B]" + ('[I] - ' + (result['title'] or '') + '[/I]' if result['title'] else '') + live_text

    return {
        'slug': result['channel']['title'].lower(),
        'studio': result['channel']['title'],
        'name': name,
        'title': result['subtitle'],
        'tvshowtitle': result['title'] if result['title'] else None,
        'sorttitle': result['channel']['title'],
        'logo': None,
        'color': result['channel']['color'],
        'fanart': result['thumb_cms'],
        'thumb': result['channel']['url_snapshot'] + '?v=' + str(int(time.time())),
        'live': result['live'],
        'playable': 'true',
        'plot': result['subtitle'] or '' if not control.isFTV else ' ', #(result['title'] or '') + ' - ' + (result['subtitle'] or ''), #program_local_date_string + duration_str + '\n' + (result['title'] or '') + '\n' + (result['subtitle'] or ''),
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