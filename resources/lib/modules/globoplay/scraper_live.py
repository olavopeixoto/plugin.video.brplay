# -*- coding: utf-8 -*-

from resources.lib.modules import control, cache, util, workers
import requests
from . import player
import datetime
import re
from sqlite3 import dbapi2 as database
import time
import os
from urllib.parse import quote_plus
import traceback
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from . import get_authorized_services, request_query, auth_helper

GLOBO_LOGO = 'http://s3.glbimg.com/v1/AUTH_180b9dd048d9434295d27c4b6dadc248/media_kit/42/f3/a1511ca14eeeca2e054c45b56e07.png'
GLOBO_FANART = os.path.join(control.artPath(), 'globo.jpg')

GLOBOPLAY_APIKEY = '35978230038e762dd8e21281776ab3c9'

LOGO_BBB = 'https://s.glbimg.com/pc/gm/media/dc0a6987403a05813a7194cd0fdb05be/2014/12/1/7e69a2767aebc18453c523637722733d.png'
FANART_BBB = 'http://s01.video.glbimg.com/x1080/244881.jpg'

PLAYER_HANDLER = player.__name__


GLOBO_LIVE_MEDIA_ID = 4452349
GLOBO_LIVE_SUBSCRIBER_MEDIA_ID = 6120663  # DVR
GLOBO_US_LIVE_MEDIA_ID = 7832875
GLOBO_US_LIVE_SUBSCRIBER_MEDIA_ID = 7832875

SNAPSHOT_URL = 'https://live-thumbs.video.globo.com/{transmission}/snapshot'

THUMBS = {
    '1688': 'spo124ha',
    '1689': 'spo224ha',
    '1690': 'spo324ha',
    '1676': 'gnews24ha',
    '1678': 'gnt24ha',
    '1679': 'msw24ha',
    '1675': 'viva24ha',
    '1683': 'maisgsat24ha',
    '1681': 'gloob24ha',
    '1682': 'gloobinho24ha',
    '1674': 'off24ha',
    '1680': 'bis24ha',
    '1684': 'mpix24ha',
    '1663': 'bra24ha',
    '1686': 'univ24ha',
    '1685': 'syfy24ha',
    '1687': 'stduniv24ha',
    '3041': 'cbt24ha',
    '2858': 'pfc124ha',
}


def get_globo_live_id():
    return GLOBO_LIVE_SUBSCRIBER_MEDIA_ID


def get_live_channels():

    affiliate_id = control.setting('globo_affiliate')

    affiliates = control.get_affiliates_by_id(int(affiliate_id))

    live = []

    show_globo_internacional = control.setting('show_globo_international') == 'true'

    if len(affiliates) == 1 and not show_globo_internacional and not is_globoplay_mais_canais_available():
        affiliate = __get_affiliate_live_channels(affiliates[0])
        live.extend(affiliate)
    else:
        threads = [workers.Thread(__get_affiliate_live_channels, affiliate) for affiliate in affiliates]
        if is_globoplay_mais_canais_available():
            threads.append(workers.Thread(get_mais_canais))
        if show_globo_internacional:
            threads.append(workers.Thread(get_globo_americas))
        [i.start() for i in threads]
        [i.join() for i in threads]
        [live.extend(i.get_result()) for i in threads]

    seen = []
    filtered_channels = filter(lambda x: seen.append(x['affiliate_code'] if 'affiliate_code' in x else '$FOO$') is None if 'affiliate_code' not in x or x['affiliate_code'] not in seen else False, live)

    if not control.globoplay_ignore_channel_authorization():
        service_ids = [channel.get('service_id') for channel in filtered_channels]
        authorized_service_ids = get_authorized_services(service_ids)
        filtered_channels = [channel for channel in filtered_channels if not channel.get('service_id') or (channel.get('service_id') in authorized_service_ids)]

    return filtered_channels


def __get_affiliate_live_channels(affiliate):
    control.log('__get_affiliate_live_channels: %s' % affiliate)
    live_globo_id = get_globo_live_id()

    code, latitude, longitude = control.get_coordinates(affiliate)

    if code is None and latitude is not None:
        result = get_affiliate_by_coordinates(latitude, longitude)
        code = result['code'] if result and 'code' in result else None

    if code is None:
        control.log('No affiliate code for: %s' % affiliate)
        return []

    live_program = __get_live_program(code)

    program_description = get_program_description(live_program.get('program_id_epg'), live_program.get('program_id'), code)

    control.log("globo live (%s) program_description: %s" % (code, repr(program_description)))

    item = {}

    item.update(program_description)

    item.pop('datetimeutc', None)

    title = program_description['title'] if 'title' in program_description else live_program.get('title')
    safe_tvshowtitle = program_description['tvshowtitle'] if 'tvshowtitle' in program_description and program_description['tvshowtitle'] else ''
    safe_subtitle = program_description['subtitle'] if 'subtitle' in program_description and program_description['subtitle'] and not safe_tvshowtitle.startswith(program_description['subtitle']) else ''
    subtitle_txt = (" / " if safe_tvshowtitle and safe_subtitle else '') + safe_subtitle
    tvshowtitle = " - " + safe_tvshowtitle + subtitle_txt if safe_tvshowtitle or subtitle_txt else ''

    program_name = '%s%s' % (title, tvshowtitle)
    item.update({
        'handler': PLAYER_HANDLER,
        'method': 'play_stream',
        'lat': latitude,
        'long': longitude,
        'affiliate_code': code,
        'IsPlayable': True,
        'id': live_globo_id,
        'program_id': live_program.get('program_id'),
        'service_id': 4654,
        'channel_id': 196,
        'live': True,
        'livefeed': True,
        'label': '[B]Globo %s[/B][I] - %s[/I]' % (re.sub(r'\d+', '', code), program_name),
        'title': '[B]Globo %s[/B][I] - %s[/I]' % (re.sub(r'\d+', '', code), program_name),
        'tvshowtitle': safe_tvshowtitle + subtitle_txt,
        'sorttitle': program_name,
        'studio': 'Globoplay',
    })

    art = item.get('art', {}) or {}
    if not art:
        item['art'] = art

    if not art.get('thumb'):
        # thumb = 'https://live-thumbs.video.globo.com/globo-rj/snapshot/' + str(int(time.time()))
        art['thumb'] = live_program.get('thumb')

    if not art.get('fanart'):
        art['fanart'] = live_program.get('fanart')

    if not art.get('poster'):
        art['tvshow.poster'] = live_program.get('poster')

    art['clearlogo'] = GLOBO_LOGO
    art['icon'] = GLOBO_LOGO

    return [item]


def __get_live_program(affiliate='RJ'):
    headers = {'Accept-Encoding': 'gzip'}
    url = 'https://api.globoplay.com.br/v1/live/%s?api_key=%s' % (affiliate, GLOBOPLAY_APIKEY)

    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        control.log('GET %s' % url)

        response = session.get(url, headers=headers).json()

        control.log(response)

        if not response or 'live' not in response:
            return {}

        live = response['live']

        return {
            'id': live['id_dvr'],
            'poster': live['poster'],
            'thumb': live['poster_safe_area'],
            'fanart': live['background_image'],
            'program_id': live['program_id'],
            'program_id_epg': live['program_id_epg'],
            'title': live['program_name']
        }
    except:
        control.log('ERROR __get_live_program: %s' % affiliate)
        control.log(traceback.format_exc(), control.LOGERROR)

    return {}


def get_program_description(program_id_epg, program_id, affiliate='RJ'):

    utc_timezone = control.get_current_brasilia_utc_offset()

    today = datetime.datetime.utcnow() - datetime.timedelta(hours=(5-utc_timezone))  # GMT-3 epg timezone - Schedule starts at 5am = GMT-8
    today = today if not today is None else datetime.datetime.utcnow() - datetime.timedelta(hours=(5-utc_timezone))  # GMT-3 - Schedule starts at 5am = GMT-8
    today_string = datetime.datetime.strftime(today, '%Y-%m-%d')

    day_schedule = __get_or_add_full_day_schedule_cache(today_string, affiliate, 24)

    return next(iter(sorted((slot for slot in day_schedule if ((slot['id_programa'] == program_id_epg and slot['id_programa'] is not None) or (slot['id_webmedia'] == program_id and slot['id_webmedia'] is not None)) and slot['datetimeutc'] < datetime.datetime.utcnow()), key=lambda x: x['datetimeutc'], reverse=True)), {})


def __get_or_add_full_day_schedule_cache(date_str, affiliate, timeout):

    control.makeFile(control.dataPath)
    dbcon = database.connect(control.cacheFile)

    response = None

    try:
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT response, added FROM globoplay_schedule WHERE date_str = ? AND affiliate = ?", (date_str, affiliate))
        match = dbcur.fetchone()

        response = eval(match[0])

        t1 = int(match[1])
        t2 = int(time.time())
        update = (abs(t2 - t1) / 3600) >= int(timeout)
        if update is False:
            control.log("Returning globoplay_schedule cached response for affiliate %s and date_str %s" % (affiliate, date_str))
            return response
    except Exception as ex:
        control.log(traceback.format_exc(), control.LOGERROR)
        control.log("CACHE ERROR: %s" % repr(ex))

    control.log("Fetching FullDaySchedule for %s: %s" % (affiliate, date_str))

    r = __get_full_day_schedule(date_str, affiliate)

    if (r is None or r == []) and response is not None:
        return response
    elif r is None or r == []:
        return []

    r_str = repr(r)
    t = int(time.time())
    dbcur.execute("CREATE TABLE IF NOT EXISTS globoplay_schedule (""date_str TEXT, ""affiliate TEXT, ""response TEXT, ""added TEXT, ""UNIQUE(date_str, affiliate)"");")
    dbcur.execute("DELETE FROM globoplay_schedule WHERE affiliate = '%s'" % affiliate)
    dbcur.execute("INSERT INTO globoplay_schedule Values (?, ?, ?, ?)", (date_str, affiliate, r_str, t))
    dbcon.commit()

    return r


def __get_full_day_schedule(today, affiliate='RJ'):

    # utc_timezone = control.get_current_brasilia_utc_offset()

    url = "https://api.globoplay.com.br/v1/epg/%s/praca/%s?api_key=%s" % (today, affiliate, GLOBOPLAY_APIKEY)
    headers = {'Accept-Encoding': 'gzip'}

    slots = (requests.get(url, headers=headers).json() or {}).get('gradeProgramacao', {}).get('slots', [])

    result = []

    if not slots:
        return result

    for index, slot in enumerate(slots):
        cast = None
        castandrole = None
        if 'elenco' in slot:
            try:
                cast_raw = slot['elenco'].split('||')
                cast = [c.strip() for c in cast_raw[0].split(',')] if cast_raw is not None and len(cast_raw) > 0 else None
                if cast_raw is not None and len(cast_raw) > 1 and cast_raw[1].strip().startswith('Elenco de dublagem:'):
                    castandrole_raw = cast_raw[1].strip().split('Elenco de dublagem:')
                    if len(castandrole_raw) > 1: #Dubladores e seus personagens
                        castandrole_raw = castandrole_raw[1].split('Outras Vozes:')
                        castandrole = [(c.strip().split(':')[1].strip(), c.strip().split(':')[0].strip()) for c in castandrole_raw[0].split('/')] if len(castandrole_raw[0].split('/')) > 0 else None
                        if len(castandrole_raw) > 1: #Outros dubladores sem papel definido
                            castandrole = [(c.strip(), 'Outros') for c in castandrole_raw[1].split('/')]
            except Exception as ex:
                control.log("ERROR POPULATING CAST: %s" % repr(ex))
                pass

        # program_datetime_utc = util.strptime_workaround(slot['data_exibicao_e_horario']) + datetime.timedelta(hours=(-utc_timezone))
        # program_datetime = program_datetime_utc + util.get_utc_delta()
        program_datetime = datetime.datetime.utcfromtimestamp(slot.get('start_time'))
        program_datetime_utc = program_datetime

        # program_local_date_string = datetime.datetime.strftime(program_datetime, '%d/%m/%Y %H:%M')

        title = slot['nome_programa'] if 'nome_programa' in slot else None
        if "tipo_programa" in slot and slot["tipo_programa"] == "confronto":
            showtitle = slot['confronto']['titulo_confronto'] + ' - ' + slot['confronto']['participantes'][0]['nome'] + ' X ' + slot['confronto']['participantes'][1]['nome']
        else:
            showtitle = None

        # next_start = slots[index+1]['data_exibicao_e_horario'] if index+1 < len(slots) else None
        # next_start = (util.strptime_workaround(next_start) + datetime.timedelta(hours=(-utc_timezone)) + util.get_utc_delta()) if next_start else datetime.datetime.now()
        next_start = datetime.datetime.utcfromtimestamp(slots[index+1].get('start_time')) if index+1 < len(slots) else datetime.datetime.utcnow()

        program_time_desc = datetime.datetime.strftime(program_datetime, '%H:%M') + ' - ' + datetime.datetime.strftime(next_start, '%H:%M')
        tags = [program_time_desc]
        if slot.get('closed_caption'):
            tags.append(slot.get('closed_caption'))
        if slot.get('facebook'):
            tags.append(slot.get('facebook'))
        if slot.get('twitter'):
            tags.append(slot.get('twitter'))

        description = '%s | %s' % (program_time_desc, slot.get('resumo', showtitle) or showtitle)

        item = {
            "tagline": slot['chamada'] if 'chamada' in slot else slot['nome_programa'],
            # "closed_caption": slot['closed_caption'] if 'closed_caption' in slot else None,
            # "facebook": slot['facebook'] if 'facebook' in slot else None,
            # "twitter": slot['twitter'] if 'twitter' in slot else None,
            # "hd": slot['hd'] if 'hd' in slot else True,
            # "id": slot['id_programa'],
            "id_programa": slot['id_programa'],
            "id_webmedia": slot['id_webmedia'],
            "subtitle": slot['resumo'] if slot['nome_programa'] == 'Futebol' else None,
            "title": title,
            'tvshowtitle': showtitle,
            "plot": description,
            # "plotoutline": datetime.datetime.strftime(program_datetime, '%H:%M') + ' - ' + datetime.datetime.strftime(next_start, '%H:%M'),
            "genre": slot['tipo_programa'],
            "tag": tags,
            "datetimeutc": program_datetime_utc,
            "dateadded": datetime.datetime.strftime(program_datetime, '%Y-%m-%d %H:%M:%S'),
            # 'StartTime': datetime.datetime.strftime(program_datetime, '%H:%M:%S'),
            # 'EndTime': datetime.datetime.strftime(next_start, '%H:%M:%S'),
            'duration': util.get_total_seconds(next_start - program_datetime),
            'art': {
                # "fanart": 'https://s02.video.glbimg.com/x720/%s.jpg' % get_globo_live_id(),
                "thumb": slot['imagem'],
                # "icon": slot['logo'] if 'logo' in slot else None,
                "clearlogo": slot['logo'] if 'logo' in slot else None,
                "poster": slot['poster'] if 'poster' in slot else None,
            }
        }

        if slot['tipo_programa'] == 'filme':
            item.update({
                "originaltitle": slot['titulo_original'] if 'titulo_original' in slot else None,
                'genre': slot['genero'] if 'genero' in slot else None,
                'year': slot['ano'] if 'ano' in slot else None,
                'director': slot['direcao'] if 'direcao' in slot else None
            })
            if cast:
                item.update({
                    'cast': cast
                })
            if castandrole:
                item.update({
                    'castandrole': castandrole,
                })

        result.append(item)

    return result


def get_affiliate_by_coordinates(latitude, longitude):

    url = 'https://api.globoplay.com.br/v1/affiliates/{lat},{long}?api_key={apikey}'.format(lat=latitude, long=longitude, apikey=GLOBOPLAY_APIKEY)

    result = cache.get(requests.get, 720, url, table='globoplay').json()

    # {
    #     "channelNumber": 29,
    #     "code": "RJ",
    #     "groupCode": "TVG",
    #     "groupName": "REDE GLOBO",
    #     "name": "GLOBO RIO",
    #     "serviceIDHD": "48352",
    #     "serviceIDOneSeg": "48376",
    #     "state": "RJ"
    # }

    return result


def get_globoplay_broadcasts(media_id, latitude, longitude):

    variables = quote_plus('{{"mediaId":"{media_id}","coordinates":{"lat":"{lat}", "long": "{long}"}}}'.format(media_id=media_id, lat=latitude, long=longitude))
    query = 'query%20Epg%28%24mediaId%3A%20ID%21%2C%20%24coordinates%3A%20CoordinatesData%29%20%7B%0A%20%20broadcast%28mediaId%3A%20%24mediaId%2C%20coordinates%3A%20%24coordinates%29%20%7B%0A%20%20%20%20...broadcastFragment%0A%20%20%7D%0A%7D%0Afragment%20broadcastFragment%20on%20Broadcast%20%7B%0A%20%20%20%20%20%20mediaId%0A%20%20%20%20%20%20transmissionId%0A%20%20%20%20%20%20logo%0A%20%20%20%20%20%20imageOnAir%28scale%3A%20X1080%29%0A%20%20%20%20%20%20withoutDVRMediaId%0A%20%20%20%20%20%20promotionalMediaId%0A%20%20%20%20%20%20salesPageCallToAction%0A%20%20%20%20%20%20promotionalText%0A%20%20%20%20%20%20geofencing%0A%20%20%20%20%20%20geoblocked%0A%20%20%20%20%20%20ignoreAdvertisements%0A%20%20%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20color%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%20%20%20%20payTvServiceId%0A%20%20%20%20%20%20%20%20payTvUsersMessage%0A%20%20%20%20%20%20%20%20payTvExternalLink%0A%20%20%20%20%20%20%20%20payTvExternalLinkLabel%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20affiliateSignal%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20dtvChannel%0A%20%20%20%20%20%20dtvHDID%0A%20%20%20%20%20%20dtvID%0A%20%20%20%20%7D%0A%20%20%20%20%20%20epgCurrentSlots%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20tags%0A%20%20%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20%20%20title%7B%0A%20%20%20%20%20%20%20%20%20%20poster%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20landscape%0A%20%20%20%20%20%20%20%20%20%20%20%20portrait%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20%20%20format%0A%20%20%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20%20%20directors%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20cast%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20genres%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20media%20%7B%0A%20%20%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20thumb%28size%3A%20720%29%0A%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20subscriptionService%20%7B%0A%20%20%20%20%20%20%20%20%20%20faq%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20url%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20default%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20salesPage%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20identifier%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20default%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D'
    response = request_query(query, variables)
    broadcasts = (response.get('data', {}) or {}).get('broadcasts', []) or []

    utc_now = int(control.to_timestamp(datetime.datetime.utcnow()))

    result = []
    for broadcast in broadcasts:
        media_id = str(broadcast.get('mediaId', 0))

        epg = next((epg for epg in broadcast['epgByDate']['entries'] if int(epg['startTime']) <= utc_now < int(epg['endTime'])), {})

        control.log('EPG: %s' % epg)

        channel = broadcast.get('channel', {}) or {}

        logo = channel.get('logo')
        channel_name = channel.get('name', '').replace('TV Globo', 'Globo')  # broadcast.get('media', {}).get('headline', '')
        fanart = broadcast.get('imageOnAir')
        channel_id = channel.get('id', 0)
        service_id = broadcast.get('media', {}).get('serviceId', 0)

        duration = epg.get('durationInMinutes', 0) * 60

        title_obj = epg.get('title', {}) or {}

        title = epg.get('name', '')
        description = title_obj.get('description') or epg.get('description', '')
        fanart = title_obj.get('cover', {}).get('landscape', fanart) or fanart
        poster = title_obj.get('poster', {}).get('web')

        label = '[B]' + channel_name + '[/B]' + ('[I] - ' + title + '[/I]' if title else '')

        program_datetime = datetime.datetime.utcfromtimestamp(epg.get('startTime', 0)) + util.get_utc_delta()
        next_start = datetime.datetime.utcfromtimestamp(epg.get('endTime', 0)) + util.get_utc_delta()

        plotoutline = datetime.datetime.strftime(program_datetime, '%H:%M') + ' - ' + datetime.datetime.strftime(next_start, '%H:%M')

        if not description or len(description) < 3:
            description = '%s | %s' % (title, plotoutline) if title else plotoutline

        result.append({
            'handler': PLAYER_HANDLER,
            'method': 'play_stream',
            'IsPlayable': True,
            'id': media_id,
            'channel_id': channel_id,
            'service_id': service_id,
            'live': epg.get('liveBroadcast', False) or False,
            'livefeed': True,
            'label': label,
            'title': label,
            # 'title': title,
            'tvshowtitle': title,
            'plot': description,
            # 'plotoutline': plotoutline,
            "tagline": plotoutline,
            'duration': duration,
            "dateadded": datetime.datetime.strftime(program_datetime, '%Y-%m-%d %H:%M:%S'),
            'sorttitle': title,
            'studio': 'Globoplay',
            'year': title_obj.get('releaseYear'),
            'country': title_obj.get('countries', []),
            'genre': title_obj.get('genresNames', []),
            'cast': title_obj.get('castNames', []),
            'director': title_obj.get('directorsNames', []),
            'writer': title_obj.get('screenwritersNames', []),
            'credits': title_obj.get('artDirectorsNames', []),
            'mpaa': epg.get('contentRating'),
            "art": {
                'icon': logo,
                'clearlogo': logo,
                'thumb': fanart,
                'fanart': fanart,
                'tvshow.poster': poster
            }
        })

    return result


def get_globo_americas():

    is_globosat_available = control.is_globosat_available()

    headers = {
        "Accept-Encoding": "gzip",
        "User-Agent": "Globo Play/0 (iPhone)",
        "x-tenant-id": "globo-play-us",
        'x-platform-id': 'web',
        'x-device-id': 'desktop',
        'x-client-version': '0.4.3'
    }

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=control.get_current_brasilia_utc_offset())
    date = now.strftime('%Y-%m-%d')
    variables = quote_plus('{{"date":"{}"}}'.format(date))
    query = 'query%20getEpgBroadcastList%28%24date%3A%20Date%21%29%20%7B%0A%20%20broadcasts%20%7B%0A%20%20%20%20...broadcastFragment%0A%20%20%7D%0A%7D%0Afragment%20broadcastFragment%20on%20Broadcast%20%7B%0A%20%20mediaId%0A%20%20media%20%7B%0A%20%20%20%20serviceId%0A%20%20%20%20headline%0A%20%20%20%20thumb%28size%3A%20720%29%0A%20%20%20%20availableFor%0A%20%20%20%20title%20%7B%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20headline%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20imageOnAir%28scale%3A%20X1080%29%0A%20%20transmissionId%0A%20%20geofencing%0A%20%20geoblocked%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20color%0A%20%20%20%20name%0A%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%7D%0A%20%20epgByDate%28date%3A%20%24date%29%20%7B%0A%20%20%20%20entries%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20alternativeTime%0A%20%20%20%20%20%20title%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%20%20portrait%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    url = 'https://jarvis.globo.com/graphql?query={query}&variables={variables}'.format(query=query, variables=variables)
    control.log('GLOBOPLAY US - GET %s' % url)
    response = cache.get(requests.get, 24, url, headers=headers, table='globoplay').json()
    control.log(response)
    broadcasts = response['data']['broadcasts']

    utc_now = int(control.to_timestamp(datetime.datetime.utcnow()))

    # thumb_usa = 'https://live-thumbs.video.globo.com/glbeua/snapshot/' + str(int(time.time()))

    result = []
    for broadcast in broadcasts:
        media_id = str(broadcast.get('mediaId', 0))

        if is_globosat_available and media_id != str(GLOBO_US_LIVE_SUBSCRIBER_MEDIA_ID):
            continue

        epg = next((epg for epg in broadcast['epgByDate']['entries'] if int(epg['startTime']) <= utc_now < int(epg['endTime'])), {})

        control.log('EPG: %s' % epg)

        channel = broadcast.get('channel', {}) or {}

        logo = channel.get('logo')
        channel_name = channel.get('name', '').replace('TV Globo', 'Globo') + ' USA'  # broadcast.get('media', {}).get('headline', '')
        fanart = broadcast.get('imageOnAir')
        channel_id = channel.get('id', 0)
        service_id = broadcast.get('media', {}).get('serviceId', 0)
        # channel_slug = '%s-americas' % channel.get('name', '').lower().replace(' ', '')

        duration = epg.get('durationInMinutes', 0) * 60

        title_obj = epg.get('title', {}) or {}

        title = epg.get('name', '')
        description = title_obj.get('description') or epg.get('description', '')
        fanart = title_obj.get('cover', {}).get('landscape', fanart) or fanart
        poster = title_obj.get('poster', {}).get('web')

        label = '[B]' + channel_name + '[/B]' + ('[I] - ' + title + '[/I]' if title else '')

        program_datetime = datetime.datetime.utcfromtimestamp(epg.get('startTime', 0)) + util.get_utc_delta()
        next_start = datetime.datetime.utcfromtimestamp(epg.get('endTime', 0)) + util.get_utc_delta()

        plotoutline = datetime.datetime.strftime(program_datetime, '%H:%M') + ' - ' + datetime.datetime.strftime(next_start, '%H:%M')

        description = '%s | %s' % (plotoutline, description)

        tags = [plotoutline]

        if epg.get('liveBroadcast', False):
            tags.append(control.lang(32004))

        tags.extend(epg.get('tags', []) or [])

        result.append({
            'handler': PLAYER_HANDLER,
            'method': 'play_stream',
            'IsPlayable': True,
            'id': media_id,
            'channel_id': channel_id,
            'service_id': service_id,
            'live': epg.get('liveBroadcast', False) or False,
            'livefeed': True,
            'label': label,
            'title': label,
            # 'title': title,
            'tvshowtitle': title,
            'plot': description,
            # 'plotoutline': plotoutline,
            # "tagline": plotoutline,
            'tag': tags,
            'duration': duration,
            "dateadded": datetime.datetime.strftime(program_datetime, '%Y-%m-%d %H:%M:%S'),
            'sorttitle': title,
            'studio': 'Globoplay Americas',
            'year': title_obj.get('releaseYear'),
            'country': title_obj.get('countries', []),
            'genre': title_obj.get('genresNames', []),
            'cast': title_obj.get('castNames', []),
            'director': title_obj.get('directorsNames', []),
            'writer': title_obj.get('screenwritersNames', []),
            'credits': title_obj.get('artDirectorsNames', []),
            'mpaa': epg.get('contentRating'),
            "art": {
                'icon': logo,
                'clearlogo': logo,
                'thumb': fanart,
                'fanart': fanart,
                'tvshow.poster': poster
            }
        })

    return result


def is_globoplay_mais_canais_available():
    if not control.is_globoplay_mais_canais_ao_vivo_available():
        return False

    return control.globoplay_ignore_channel_authorization() or auth_helper.is_service_allowed(auth_helper.CADUN_SERVICES.GSAT_CHANNELS)


def get_mais_canais():

    query = 'query%20getBroadcastList%20%7B%0A%20%20%20%20%20%20broadcasts%20%7B%0A%20%20%20%20%20%20%20%20...broadcastFragment%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20fragment%20broadcastFragment%20on%20Broadcast%20%7B%0A%20%20%20%20%20%20mediaId%0A%20%20%20%20%20%20transmissionId%0A%20%20%20%20%20%20logo%0A%20%20%20%20%20%20imageOnAir%28scale%3A%20X1080%29%0A%20%20%20%20%20%20withoutDVRMediaId%0A%20%20%20%20%20%20promotionalMediaId%0A%20%20%20%20%20%20salesPageCallToAction%0A%20%20%20%20%20%20promotionalText%0A%20%20%20%20%20%20geofencing%0A%20%20%20%20%20%20geoblocked%0A%20%20%20%20%20%20ignoreAdvertisements%0A%20%20%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20color%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%20%20%20%20payTvServiceId%0A%20%20%20%20%20%20%20%20payTvUsersMessage%0A%20%20%20%20%20%20%20%20payTvExternalLink%0A%20%20%20%20%20%20%20%20payTvExternalLinkLabel%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20epgCurrentSlots%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20tags%0A%20%20%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20%20%20title%7B%0A%20%20%20%20%20%20%20%20%20%20poster%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20landscape%0A%20%20%20%20%20%20%20%20%20%20%20%20portrait%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20%20%20format%0A%20%20%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20%20%20directors%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20cast%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20genres%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20media%20%7B%0A%20%20%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20thumb%28size%3A%20720%29%0A%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20subscriptionService%20%7B%0A%20%20%20%20%20%20%20%20%20%20faq%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20url%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20default%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20salesPage%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20identifier%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20default%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D'
    variables = '{}'

    response = request_query(query, variables, force_refresh=True) or {}

    for broadcast in response.get('data', {}).get('broadcasts', []) or []:
        channel = broadcast.get('channel', {}) or {}

        if channel.get('id') == '196':
            continue

        media_id = str(broadcast.get('mediaId', 0))

        epg = next((epg for epg in broadcast.get('epgCurrentSlots', [])), {})

        control.log('EPG: %s' % epg)

        logo = channel.get('logo')
        channel_name = broadcast.get('media', {}).get('headline', '').replace('Agora no ', '').replace('Agora na ', '').strip()  #channel.get('name', '')
        fanart = broadcast.get('imageOnAir')
        channel_id = channel.get('id', 0)
        service_id = broadcast.get('media', {}).get('serviceId', 0)
        # channel_slug = '%s-americas' % channel.get('name', '').lower().replace(' ', '')

        duration = epg.get('durationInMinutes', 0) * 60

        title_obj = epg.get('title', {}) or {}

        title = epg.get('name', '')
        description = title_obj.get('description') or epg.get('description', '')
        fanart = title_obj.get('cover', {}).get('landscape', fanart) or fanart
        poster = title_obj.get('poster', {}).get('web')
        thumb = THUMBS.get(str(broadcast.get('transmissionId')))
        thumb = (SNAPSHOT_URL.format(transmission=thumb) + '?=' + str(int(time.time()))) if thumb else fanart

        label = '[B]' + channel_name + '[/B]' + ('[I] - ' + title + '[/I]' if title else '')

        program_datetime = datetime.datetime.utcfromtimestamp(epg.get('startTime', 0)) + util.get_utc_delta()
        next_start = datetime.datetime.utcfromtimestamp(epg.get('endTime', 0)) + util.get_utc_delta()

        plotoutline = datetime.datetime.strftime(program_datetime, '%H:%M') + ' - ' + datetime.datetime.strftime(next_start, '%H:%M')

        description = '%s | %s' % (plotoutline, description)

        tags = [plotoutline]

        if epg.get('liveBroadcast', False):
            tags.append(control.lang(32004))

        tags.extend(epg.get('tags', []) or [])

        yield {
            'handler': PLAYER_HANDLER,
            'method': 'play_stream',
            'IsPlayable': True,
            'id': media_id,
            'channel_id': channel_id,
            'service_id': service_id,
            'live': epg.get('liveBroadcast', False) or False,
            'livefeed': True,
            'label': label,
            'title': label,
            # 'title': title,
            'tvshowtitle': title,
            'plot': description,
            # 'plotoutline': plotoutline,
            # "tagline": plotoutline,
            'tag': tags,
            'duration': duration,
            "dateadded": datetime.datetime.strftime(program_datetime, '%Y-%m-%d %H:%M:%S'),
            'sorttitle': title,
            'studio': 'Globoplay',
            'year': title_obj.get('releaseYear'),
            'country': title_obj.get('countries', []),
            'genre': title_obj.get('genresNames', []),
            'cast': title_obj.get('castNames', []),
            'director': title_obj.get('directorsNames', []),
            'writer': title_obj.get('screenwritersNames', []),
            'credits': title_obj.get('artDirectorsNames', []),
            'mpaa': epg.get('contentRating'),
            "art": {
                'icon': logo,
                'clearlogo': logo,
                'thumb': thumb,
                'fanart': fanart,
                'tvshow.poster': poster
            }
        }
