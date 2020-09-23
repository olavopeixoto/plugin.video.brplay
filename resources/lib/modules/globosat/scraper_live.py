# -*- coding: utf-8 -*-

import os, datetime, time, urllib
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import util
from resources.lib.modules import workers
from resources.lib.modules import cache
from resources.lib.modules import kodi_util
import re
import json

GLOBOSAT_URL = 'http://globosatplay.globo.com'
GLOBOSAT_API_URL = 'http://api.vod.globosat.tv/globosatplay'
GLOBOSAT_API_AUTHORIZATION = 'token b4b4fb9581bcc0352173c23d81a26518455cc521'
GLOBOSAT_API_CHANNELS = GLOBOSAT_API_URL + '/channels.json?page=%d'
COMBATE_SIMULCAST_URL = 'https://api-simulcast.globosat.tv/v1/combateplay'
GLOBOSAT_SIMULCAST_URL = 'https://api-simulcast.globosat.tv/v1/globosatplay'
PREMIERE_MATCHES_JSON = 'https://api-soccer.globo.com/v1/premiere/matches?order=asc&page='
PREMIERE_NEXT_MATCHES_JSON = 'https://api-soccer.globo.com/v1/premiere/matches?status=not_started&order=asc&page='
INFO_URL = 'http://api.globovideos.com/videos/%s/playlist'
PREMIERE_24H_SIMULCAST = 'https://api-simulcast.globosat.tv/v1/premiereplay/'

GET_GRAPHQL_ALL_BROADCASTS_VARIABLES = '{{"logoScale":"X42","date":"{date}"}}'
GET_GRAPHQL_ALL_BROADCASTS_PERSISTED = 'https://products-jarvis.globo.com/graphql?operationName=getAllBroadcasts&variables={variables}&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%223ed5d9a9bca84fd2cda18fc0e59a2fb626fb5bbe7205a507af3392e66809528b%22%7D%7D'
GET_GRAPHQL_ALL_BROADCASTS = 'https://products-jarvis.globo.com/graphql?query=query%20getAllBroadcasts%28%24logoScale%3A%20BroadcastChannelTrimmedLogoScales%20%3D%20X56%29%20%7B%0A%20%20broadcasts%20%7B%0A%20%20%20%20mediaId%0A%20%20%20%20mutedMediaId%0A%20%20%20%20promotionalMediaId%0A%20%20%20%20promotionalText%0A%20%20%20%20geofencing%0A%20%20%20%20geoblocked%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20color%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20text%3A%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20trimmedLogo%28scale%3A%20%24logoScale%29%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20epgCurrentSlots%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20composite%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20media%20%7B%0A%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A&operationName=getAllBroadcasts&variables={variables}'

GLOBOSAT_TRANSMISSIONS = GLOBOSAT_API_URL + '/transmissions.json?page=%s'
GLOBOSAT_LIVE_JSON = GLOBOSAT_URL + '/xhr/transmissoes/ao-vivo.json'

artPath = control.artPath()

COMBATE_LOGO = os.path.join(artPath, 'logo_combate.png')
PREMIERE_LOGO = os.path.join(artPath, 'logo_premiere.png')
PREMIERE_FANART = os.path.join(artPath, 'fanart_premiere_720.jpg')  # https://s02.video.glbimg.com/x720/2752761.jpg

FANART_URL = 'http://s01.video.glbimg.com/x720/{media_id}.jpg'
THUMB_URL = 'https://s04.video.glbimg.com/x720/{media_id}.jpg'

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
    '2006': 'sexy24ha'
}


def getAllBroadcasts():

    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    variables = GET_GRAPHQL_ALL_BROADCASTS_VARIABLES.format(date=today_str)
    url = GET_GRAPHQL_ALL_BROADCASTS.format(variables=urllib.quote_plus(variables))

    headers = {
        'x-tenant-id': 'globosat-play',
        'x-platform-id': 'web',
        'x-device-id': 'desktop',
        'x-client-version': '0.10.0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
        'accept-encoding': 'gzip'
    }

    response = client.request(url, headers=headers)

    channels = []

    for broadcast in response['data']['broadcasts']:
        if 'epgCurrentSlots' not in broadcast or not broadcast['epgCurrentSlots']:
            continue

        program = broadcast['epgCurrentSlots'][0]

        live_text = u' (' + control.lang(32004) + u')' if program['liveBroadcast'] else u''

        program_detail = u': ' + program['metadata'] if program['metadata'] else u''

        program_name = program['name'] + program_detail if program['metadata'] and not program['metadata'].startswith(program['name']) else program['metadata'] if program['metadata'] else program['name']

        name = u"[B]" + broadcast['channel']['name'] + u"[/B]" + u'[I] - ' + program_name + u'[/I]' + live_text

        fanart = FANART_URL.format(media_id=broadcast['mediaId'])
        thumb = SNAPSHOT_URL.format(transmission=THUMBS[str(broadcast['channel']['id'])]) + '/?v=' + str(int(time.time())) if str(broadcast['channel']['id']) in THUMBS else THUMB_URL.format(media_id=broadcast['mediaId'])

        program_date = datetime.datetime.fromtimestamp(program['startTime'])
        endTime = datetime.datetime.fromtimestamp(program['endTime'])
        duration = (endTime - program_date).total_seconds()

        program_name = program['name'] + program_detail

        item = {
            'slug': broadcast['channel']['slug'],
            'studio': broadcast['channel']['name'],
            'name': name,
            'title': program_name,
            'tvshowtitle': program['name'] if program_name else None,
            'sorttitle': broadcast['channel']['name'],
            'logo': broadcast['channel']['logo'],
            'color': broadcast['channel']['color'],
            'fanart': fanart,
            'thumb': thumb,
            'live': program['liveBroadcast'],
            'playable': 'true',
            'plot': program['description'] or '' if not control.isFTV else ' ',
            'plotoutline': datetime.datetime.strftime(program_date, '%H:%M') + ' - ' + datetime.datetime.strftime(program_date + datetime.timedelta(seconds=duration), '%H:%M'),
            'id': broadcast['mediaId'],
            'channel_id': broadcast['channel']['id'],
            'duration': int(duration),
            'dateadded': datetime.datetime.strftime(program_date, '%Y-%m-%d %H:%M:%S'),
            'brplayprovider': 'globosat',
            'livefeed': 'true',
            'clearlogo': broadcast['channel']['logo'],
            'clearart': None,
            'banner': None,
            'isFree': broadcast['media']['availableFor'] == 'ANONYMOUS'
        }

        channels.append(item)

    return channels


def get_basic_live_channels():
    return get_basic_live_channels_from_simulcast_only() # + get_sportv4_live()
    # return get_basic_live_channels_from_api()  # + get_sportv4_live()
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
            'livefeed': 'true',
            'thumb': None,
            'clearlogo': None,
            'clearart': None,
            'banner': None,
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
            'name': '[B]' + title + '[/B]',
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
            simulcast_result = next((result for result in simulcast_results if str(result['media_globovideos_id']) == str(transmission['items'][0]['id_globo_videos'])), None)
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
                    'fanart': item['fanart'] if 'fanart' in item and item['fanart'] is not None else transmission['items'][0]['image'],
                    'id': transmission['items'][0]['id_globo_videos'],
                    'channel_id': transmission['id_channel'],
                    'brplayprovider': 'globosat',
                    'thumb': item['thumb'] if 'thumb' in item and item['thumb'] is not None else 'https://s03.video.glbimg.com/x720/%s.jpg' % transmission['items'][0]['id_globo_videos'],
                    'livefeed': 'true'
                    })

            live.append(item)

            channel_id_list.append(int(item['channel_id']))

    for simulcast_result in simulcast_results:
        if simulcast_result is None or int(simulcast_result['channel']['globovideos_id']) in channel_id_list:
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

    if affiliate:
        code, latitude, longitude = control.get_coordinates(affiliate)
        url = GLOBOSAT_SIMULCAST_URL + '?latitude=%s&longitude=%s' % (latitude, longitude)
    else:
        url = GLOBOSAT_SIMULCAST_URL

    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}
    channel_info = client.request(url, headers=headers)
    simulcast_results += channel_info


def get_combate_live_channels():

    #COMBATE
    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip', 'User-Agent': 'CombatePlay/108 CFNetwork/978.0.7 Darwin/18.5.0'}
    results = client.request(COMBATE_SIMULCAST_URL, headers=headers)

    live = []

    for result in results:
        channel = __get_simulcast_data(result)
        channel.update({
            'logo': COMBATE_LOGO,
            'clearlogo': COMBATE_LOGO
        })
        live.append(channel)

    return live


def get_premiere_live_games():

    live = []
    all_games = []

    headers = {'Accept-Encoding': 'gzip'}
    page = 1
    has_more = True
    while has_more:
        result = client.request(PREMIERE_MATCHES_JSON + str(page), headers=headers, error=True)
        all_games += result['results']
        has_more = result['pagination']['has_next'] or not result or 'pagination' not in result or 'has_next' not in result['pagination']
        if has_more:
            page = page + 1

    if not all_games:
        return []

    live_games = list(filter(lambda x: x['status'] == 'live', all_games))
    offline_games = list(filter(lambda x: x['status'] != 'live' and x['status'] != 'ended', all_games))

    for game in live_games:
        live_game = __get_game_data(game, {
            'slug': 'premiere-fc',
            'studio': 'Premiere FC',
            'sorttitle': 'Premiere FC',
            'logo': PREMIERE_LOGO,
            'clearlogo': PREMIERE_LOGO,
            'fanart': PREMIERE_FANART,
            'thumb': PREMIERE_FANART,
            'channel_id': 1995
        }, False)
        live_game.update({
            'name': '[B]Premiere FC[/B] - ' + live_game['name'],
            'title': u'\u2063' + live_game['title']
        })
        live.append(live_game)

    if len(offline_games) > 0:
        if len(offline_games) > 1:
            plural = 's' if len(offline_games) > 1 else ''
            title = '%s jogo%s programado%s' % (len(offline_games), plural, plural)
            extra_plural = 's' if len(offline_games) - 1 > 1 else ''
            extra_games_str = ' + ' + str(len(offline_games) - 1) + ' jogo' + extra_plural
        else:
            title = ''
            extra_games_str = ''

        #PREMIERE
        # live.append({
        #     'slug': 'premiere-fc',
        #     'name': u'[B]\u2063Próximos Jogos[/B]',
        #     'studio': 'Premiere FC',
        #     'title': u'\u2063Veja a Programação',
        #     'tvshowtitle': u'Próximos Jogos',
        #     'sorttitle': 'Premiere FC',
        #     'clearlogo': PREMIERE_LOGO,
        #     'fanart': PREMIERE_FANART,
        #     'thumb': PREMIERE_FANART,
        #     'playable': 'false',
        #     'plot': title,
        #     'id': None,
        #     'channel_id': 1995,
        #     'duration': None,
        #     'isFolder': 'true',
        #     'logo': offline_games[0]['home']['logo_60x60_url'],
        #     'logo2': offline_games[0]['away']['logo_60x60_url'],
        #     'initials1': offline_games[0]['home']['abbreviation'],
        #     'initials2': offline_games[0]['away']['abbreviation'],
        #     'gamedetails': offline_games[0]['championship'] + extra_games_str,
        #     'brplayprovider': 'premierefc'
        # })

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
        live_text = ' (' + control.lang(32004) + ')' if channel_data['live'] is True or channel_data['live'] == 'true' else ''
        studio = channel_data['channel']['title']
        label = '[B]' + studio + '[/B]' + ('[I] - ' + channel_data['name'] + '[/I]' if channel_data['name'] else '') + live_text

        live_channel = {
            'slug': 'premiere-fc',
            'name': label,
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


def __append_result(fn, list, *args):
    list += fn(*args)['results']


def get_premiere_games(meta={}):
    meta = meta or {}
    live = []
    live_games = []

    headers = {'Accept-Encoding': 'gzip'}

    page = 1
    result = client.request(PREMIERE_NEXT_MATCHES_JSON + str(page), headers=headers)
    live_games += result['results']
    pages = result['pagination']['pages']

    if pages > 1:
        threads = []
        for page in range(2, pages + 1):
            print ('PFC URL: ' + PREMIERE_NEXT_MATCHES_JSON + str(page))
            threads.append(workers.Thread(__append_result, client.request, live_games, PREMIERE_NEXT_MATCHES_JSON + str(page), True, True, False, None, None, headers, False, False, None, None, None, '', '30', False))

        [i.start() for i in threads]
        [i.join() for i in threads]

    for game in live_games:
        livemeta = meta.copy()
        live.append(__get_game_data(game, livemeta, live_games))

    return live


def __get_game_data(game, meta, offline):

    utc_timezone = control.get_current_brasilia_utc_offset()
    parsed_date = util.strptime_workaround(game['datetime'], format='%Y-%m-%dT%H:%M:%S') + datetime.timedelta(hours=(-utc_timezone))
    date_string = kodi_util.format_datetimeshort(parsed_date)

    # plot = game['championship'] + u': ' + game['home']['name'] + u' x ' + game['away']['name'] + u' (' + game['stadium'] + u')' + u'. ' + date_string
    label = game['home']['name'] + u' x ' + game['away']['name']
    media_desc = '\n' + game['medias'][0]['description'] if 'medias' in game and game['medias'] and len(game['medias']) > 0 and game['medias'][0]['description'] else ''
    plot = game['phase'] + u' d' + get_artigo(game['championship']) + u' ' + game['championship'] + u'. Disputado n' + get_artigo(game['stadium']) + u' ' + game['stadium'] + u'. ' + date_string + media_desc

    name = ((date_string + u' - ') if offline else u'') + label if not control.isFTV else label
    meta.update({
        'name': name,
        'label2': label,
        'playable': 'true' if 'medias' in game and game['medias'] and len(game['medias']) > 0 and 'id' in game['medias'][0] else 'false',
        'plot': game['stadium'] if control.isFTV else plot,
        'plotoutline': date_string,
        'id': game['medias'][0]['id'] if game['medias'] and len(game['medias']) > 0 and 'id' in game['medias'][0] else None,
        'logo': game['home']['logo_60x60_url'],
        'logo2': game['away']['logo_60x60_url'],
        'initials1': game['home']['abbreviation'],
        'initials2': game['away']['abbreviation'],
        'isFolder': 'false',
        'mediatype': 'episode',
        'tvshowtitle': game['home']['abbreviation'] + u' x ' + game['away']['abbreviation'],
        'title': game['championship'],
        'brplayprovider': 'globosat',
        'gamedetails': None,
        'livefeed': game['status'] == 'live',
    })
    return meta


def get_artigo(word):

    test = word.split(' ')[0] if word else u''

    if test.endswith('a'):
        return u'a'

    if test.endswith('as'):
        return u'as'

    if test.endswith('os'):
        return u'os'

    return u'o'


def __get_simulcast_data(result):

    utc_timezone = control.get_current_brasilia_utc_offset()

    live_text = ' (' + control.lang(32004) + ')' if result['live'] else ''
    program_date = util.strptime_workaround(result['starts_at'][:-6]) + datetime.timedelta(hours=-utc_timezone) + util.get_utc_delta() if not result['starts_at'] is None else datetime.datetime.now()
    # program_local_date_string = datetime.datetime.strftime(program_date, '%d/%m/%Y %H:%M')
    # duration_str = (' - ' + str(result['duration'] or 0) + ' minutos') if (result['duration'] or 0) > 0 else ''

    name = "[B]" + result['channel']['title'] + "[/B]" + ('[I] - ' + (result['name'] or '') + '[/I]' if result['name'] else '') + live_text

    return {
        'slug': result['channel']['title'].lower(),
        'studio': result['channel']['title'],
        'name': name,
        'title': result['name'],
        'tvshowtitle': result['name'] if result['name'] else None,
        'sorttitle': result['channel']['title'],
        'logo': result['channel']['default_logo'],
        'color': result['channel']['color'],
        'fanart': result['image_url'],
        'thumb': result['snapshot_url'] + '?v=' + str(int(time.time())),
        'live': result['live'],
        'playable': 'true',
        'plot': result['description'] or '' if not control.isFTV else ' ', #(result['title'] or '') + ' - ' + (result['subtitle'] or ''), #program_local_date_string + duration_str + '\n' + (result['title'] or '') + '\n' + (result['subtitle'] or ''),
        'plotoutline': datetime.datetime.strftime(program_date, '%H:%M') + ' - ' + (datetime.datetime.strftime(program_date + datetime.timedelta(minutes=(int(result['duration'] or 0) / 1000 / 60)), '%H:%M') if (result['duration'] or 0) > 0 else 'N/A'),
        # 'programTitle': result['subtitle'],
        'id': result['media_globovideos_id'],
        'channel_id': result['channel']['globovideos_id'],
        'duration': int(result['duration'] or 0) / 1000,
        # 'tagline': result['subtitle'],
        # 'date': datetime.datetime.strftime(program_date, '%d.%m.%Y'),
        # 'aired': datetime.datetime.strftime(program_date, '%Y-%m-%d'),
        'dateadded': datetime.datetime.strftime(program_date, '%Y-%m-%d %H:%M:%S'),
        # 'StartTime': datetime.datetime.strftime(program_date, '%H:%M:%S'),
        # 'EndTime': datetime.datetime.strftime(program_date + datetime.timedelta(minutes=(result['duration'] or 0)), '%H:%M:%S'),
        'brplayprovider': 'globosat',
        'livefeed': 'true',
        'clearlogo': result['channel']['white_logo'],
        'clearart': None,
        'banner': None,
    }