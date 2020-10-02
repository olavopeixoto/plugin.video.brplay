# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import util
from resources.lib.modules import workers
from resources.lib.modules import cache
import datetime
import re
from sqlite3 import dbapi2 as database
import time
import os
from scraper_vod import GLOBOPLAY_CONFIGURATION
import urllib

GLOBO_LOGO = 'http://s3.glbimg.com/v1/AUTH_180b9dd048d9434295d27c4b6dadc248/media_kit/42/f3/a1511ca14eeeca2e054c45b56e07.png'
GLOBO_FANART = os.path.join(control.artPath(), 'globo.jpg')

GLOBOPLAY_APIKEY = '35978230038e762dd8e21281776ab3c9'

LOGO_BBB = 'https://s.glbimg.com/pc/gm/media/dc0a6987403a05813a7194cd0fdb05be/2014/12/1/7e69a2767aebc18453c523637722733d.png'
FANART_BBB = 'http://s01.video.glbimg.com/x720/244881.jpg'


def get_globo_live_id():
    return 4452349


def get_live_channels():

    affiliate_temp = control.setting('globo_affiliate')

    affiliates = control.get_affiliates_by_id(int(affiliate_temp))

    live = []

    if control.setting('show_multicam') == 'true':
        config = cache.get(client.request, 1, GLOBOPLAY_CONFIGURATION)

        # multicams = config['multicamLabel']
        multicam = config['growth']['menu'] if 'growth' in config and 'menu' in config['growth'] and 'is_enabled' in config['growth']['menu'] and config['growth']['menu']['is_enabled'] else None

        if multicam:
            title = multicam['label_item']
            live.append({
                'slug': 'multicam',
                'name': '[B]' + title + '[/B]',
                'studio': 'Big Brother Brasil',
                'title': title,
                'tvshowtitle': '',
                'sorttitle': title,
                'logo': LOGO_BBB,
                'clearlogo': LOGO_BBB,
                'fanart': FANART_BBB,
                'thumb': FANART_BBB,
                'playable': 'false',
                'plot': None,
                'id': multicam['link_program_id'],
                'channel_id': config['channel_id'],
                'duration': None,
                'isFolder': 'true',
                'brplayprovider': 'multicam'
            })

    show_globo_internacional = control.setting('show_globo_international') == 'true'

    if len(affiliates) == 1 and not show_globo_internacional:
        affiliate = __get_affiliate_live_channels(affiliates[0])
        live.append(affiliate)
    else:
        threads = [workers.Thread(__append_result, __get_affiliate_live_channels, live, affiliate) for affiliate in affiliates]
        if show_globo_internacional:
            threads.append(workers.Thread(__append_result, get_globo_americas, live))
        [i.start() for i in threads]
        [i.join() for i in threads]

    seen = []
    return filter(lambda x: seen.append(x['affiliate_code'] if 'affiliate_code' in x else '$FOO$') is None if 'affiliate_code' not in x or x['affiliate_code'] not in seen else False, live)


def __append_result(fn, item_list, *args):
    item = fn(*args)
    if item:
        if isinstance(item, list):
            item_list.extend(item)
        else:
            item_list.append(item)


def __get_affiliate_live_channels(affiliate):
    liveglobo = get_globo_live_id()

    code, latitude, longitude = control.get_coordinates(affiliate)

    if code is None and latitude is not None:
        result = get_affiliate_by_coordinates(latitude, longitude)
        code = result['code'] if result and 'code' in result else None

    if code is None:
        return None

    live_program = __get_live_program(code)

    if not live_program:
        return None

    geo_position = 'lat=%s&long=%s' % (latitude, longitude)

    program_description = get_program_description(live_program['program_id_epg'], live_program['program_id'], code)

    control.log("globo live (%s) program_description: %s" % (code, repr(program_description)))

    item = {
        'plot': None,
        'duration': None,
        'affiliate': geo_position,
        'brplayprovider': 'globoplay',
        'affiliate_code': code,
        'logo': None,
        'thumb': live_program['thumb'],
        'poster': live_program['poster'],
        'fanart': live_program['fanart']
    }

    item.update(program_description)

    item.pop('datetimeutc', None)

    title = program_description['title'] if 'title' in program_description else live_program['title']
    # subtitle = program_description['subtitle'] if 'subtitle' in program_description else live_program['title']

    safe_tvshowtitle = program_description['tvshowtitle'] if 'tvshowtitle' in program_description and program_description['tvshowtitle'] else ''
    safe_subtitle = program_description['subtitle'] if 'subtitle' in program_description and program_description['subtitle'] and not safe_tvshowtitle.startswith(program_description['subtitle']) else ''
    subtitle_txt = (" / " if safe_tvshowtitle and safe_subtitle else '') + safe_subtitle
    tvshowtitle = " (" + safe_tvshowtitle + subtitle_txt + ")" if safe_tvshowtitle or subtitle_txt else ''

    item.update({
        'slug': 'globo',
        'name': ('[B]' if not control.isFTV else '') + 'Globo ' + re.sub(r'\d+','',code) + ('[/B]' if not control.isFTV else '') + '[I] - ' + title + (tvshowtitle if not control.isFTV else '') + '[/I]',
        'title': title, #subtitle,  # 'Globo ' + re.sub(r'\d+','',code) + '[I] - ' + program_description['title'] + '[/I]',
        'sorttitle': 'Globo ' + re.sub(r'\d+','',code),
        'clearlogo': GLOBO_LOGO,
        # 'tagline': program_description['title'],
        'studio': 'Rede Globo - ' + affiliate,
        # 'logo': GLOBO_LOGO,
        'playable': 'true',
        'id': liveglobo,
        'channel_id': 196,
        'live': True,
        'livefeed': 'true'
    })

    if control.isFTV:
        item.update({'tvshowtitle': title})

    if 'fanart' not in item or not item['fanart']:
        item.update({'fanart': GLOBO_FANART})

    # if 'poster' not in item or not item['poster']:
    #     item.update({'poster': live_program['poster']})

    if 'thumb' not in item or not item['thumb']:
        item.update({'thumb': live_program['poster']})

    return item


def __get_live_program(affiliate='RJ'):
    headers = {'Accept-Encoding': 'gzip'}
    url = 'https://api.globoplay.com.br/v1/live/%s?api_key=%s' % (affiliate, GLOBOPLAY_APIKEY)

    response = client.request(url, headers=headers)

    if not response or 'live' not in response:
        return None

    live = response['live']

    return {
        'poster': live['poster'],
        'thumb': live['poster_safe_area'],
        'fanart': live['background_image'],
        'program_id': live['program_id'],
        'program_id_epg': live['program_id_epg'],
        'title': live['program_name']
    }


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

        response = eval(match[0].encode('utf-8'))

        t1 = int(match[1])
        t2 = int(time.time())
        update = (abs(t2 - t1) / 3600) >= int(timeout)
        if update is False:
            control.log("Returning globoplay_schedule cached response for affiliate %s and date_str %s" % (affiliate, date_str))
            return response
    except Exception as ex:
        control.log("CACHE ERROR: %s" % repr(ex))
        pass

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

    utc_timezone = control.get_current_brasilia_utc_offset()

    url = "https://api.globoplay.com.br/v1/epg/%s/praca/%s?api_key=%s" % (today, affiliate, GLOBOPLAY_APIKEY)
    headers = {'Accept-Encoding': 'gzip'}

    slots = client.request(url, headers=headers)['gradeProgramacao']['slots']

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

        program_datetime_utc = util.strptime_workaround(slot['data_exibicao_e_horario']) + datetime.timedelta(hours=(-utc_timezone))
        program_datetime = program_datetime_utc + util.get_utc_delta()

        # program_local_date_string = datetime.datetime.strftime(program_datetime, '%d/%m/%Y %H:%M')

        title = slot['nome_programa'] if 'nome_programa' in slot else None
        if "tipo_programa" in slot and slot["tipo_programa"] == "confronto":
            showtitle = slot['confronto']['titulo_confronto'] + ' - ' + slot['confronto']['participantes'][0]['nome'] + ' X ' + slot['confronto']['participantes'][1]['nome']
        else:
            showtitle = slot['nome_programa'] if 'nome_programa' in slot and control.isFTV else None

        next_start = slots[index+1]['data_exibicao_e_horario'] if index+1 < len(slots) else None
        next_start = (util.strptime_workaround(next_start) + datetime.timedelta(hours=(-utc_timezone)) + util.get_utc_delta()) if next_start else datetime.datetime.now()

        item = {
            "tagline": slot['chamada'] if 'chamada' in slot else slot['nome_programa'],
            "closed_caption": slot['closed_caption'] if 'closed_caption' in slot else None,
            "facebook": slot['facebook'] if 'facebook' in slot else None,
            "twitter": slot['twitter'] if 'twitter' in slot else None,
            "hd": slot['hd'] if 'hd' in slot else True,
            "id": slot['id_programa'],
            "id_programa": slot['id_programa'],
            "id_webmedia": slot['id_webmedia'],
            # "fanart": 'https://s02.video.glbimg.com/x720/%s.jpg' % get_globo_live_id(),
            "thumb": slot['imagem'],
            "logo": slot['logo'] if 'logo' in slot else None,
            "clearlogo": slot['logo'] if 'logo' in slot else None,
            "poster": slot['poster'] if 'poster' in slot else None,
            "subtitle": slot['resumo'] if slot['nome_programa'] == 'Futebol' else None,
            "title": title,
            "plot": slot['resumo'] if 'resumo' in slot else showtitle, #program_local_date_string + ' - ' + (slot['resumo'] if 'resumo' in slot else showtitle.replace(' - ', '\n') if showtitle and len(showtitle) > 0 else slot['nome_programa']),
            "plotoutline": datetime.datetime.strftime(program_datetime, '%H:%M') + ' - ' + datetime.datetime.strftime(next_start, '%H:%M'),
            "mediatype": 'episode' if showtitle and len(showtitle) > 0 else 'video',
            "genre": slot['tipo_programa'],
            "datetimeutc": program_datetime_utc,
            "dateadded": datetime.datetime.strftime(program_datetime, '%Y-%m-%d %H:%M:%S'),
            # 'StartTime': datetime.datetime.strftime(program_datetime, '%H:%M:%S'),
            # 'EndTime': datetime.datetime.strftime(next_start, '%H:%M:%S'),
            'duration': util.get_total_seconds(next_start - program_datetime)
        }

        # if showtitle and len(showtitle) > 0:
        item.update({
            'tvshowtitle': showtitle
        })

        if slot["tipo_programa"] == "confronto":
            item.update({
                'logo': slot['confronto']['participantes'][0]['imagem'],
                'logo2': slot['confronto']['participantes'][1]['imagem'],
                'initials1': slot['confronto']['participantes'][0]['nome'][:3].upper(),
                'initials2': slot['confronto']['participantes'][1]['nome'][:3].upper()
            })

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


def get_multicam(program_id):

    headers = {'Accept-Encoding': 'gzip'}
    url = 'https://api.globoplay.com.br/v1/programs/%s/live?api_key=%s' % (program_id, GLOBOPLAY_APIKEY)
    response = client.request(url, headers=headers)

    if not response or 'erro' in response:
        if response:
            control.log("Multicam Error: %s" % response['erro'])
        return []

    return [{
        'plot': None,
        'duration': None,
        'brplayprovider': 'globoplay',
        'logo': LOGO_BBB,
        'slug': 'multicam_' + channel['description'].replace(' ','_').lower(),
        'name': '[B]' + channel['description'] + '[/B]',
        'title': channel['description'],
        'tvshowtitle': response['title'] if not control.isFTV else '',
        'sorttitle': "%02d" % (i,),
        'clearlogo': LOGO_BBB,
        'studio': response['title'] if control.isFTV else 'Rede Globo',
        'playable': 'true',
        'id': channel['id'],
        'channel_id': 196,
        'live': True,
        'livefeed': 'false',  #force vod hash
        'fanart': FANART_BBB,
        'thumb': channel['thumb'] + '?v=' + str(int(time.time()))
    } for i, channel in enumerate(response['channels'])]


def get_affiliate_by_coordinates(latitude, longitude):

    url = 'https://api.globoplay.com.br/v1/affiliates/{lat},{long}?api_key={apikey}'.format(lat=latitude, long=longitude, apikey=GLOBOPLAY_APIKEY)

    result = client.request(url)

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


def get_globo_americas():

    GLOBO_AMERICAS_ID = 7832875

    is_globosat_available = control.is_globosat_available()

    headers = {
        "Accept-Encoding": "gzip",
        "User-Agent": "Globo Play/0 (iPhone)",
        "x-tenant-id": "globo-play-us"
    }

    now = datetime.datetime.now()
    date = now.strftime('%Y-%m-%d')
    variables = urllib.quote_plus('{{"date":"{}"}}'.format(date))
    query = 'query%20getEpgBroadcastList%28%24date%3A%20Date%21%29%20%7B%0A%20%20broadcasts%20%7B%0A%20%20%20%20...broadcastFragment%0A%20%20%7D%0A%7D%0Afragment%20broadcastFragment%20on%20Broadcast%20%7B%0A%20%20mediaId%0A%20%20media%20%7B%0A%20%20%20%20serviceId%0A%20%20%20%20headline%0A%20%20%20%20thumb%28size%3A%20720%29%0A%20%20%20%20availableFor%0A%20%20%20%20title%20%7B%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20headline%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20imageOnAir%28scale%3A%20X1080%29%0A%20%20transmissionId%0A%20%20geofencing%0A%20%20geoblocked%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20color%0A%20%20%20%20name%0A%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%7D%0A%20%20epgByDate%28date%3A%20%24date%29%20%7B%0A%20%20%20%20entries%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20alternativeTime%0A%20%20%20%20%20%20title%7B%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20poster%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20landscape%0A%20%20%20%20%20%20%20%20%20%20portrait%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20format%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directors%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20cast%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20genres%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    url = 'https://jarvis.globo.com/graphql?query={query}&variables={variables}'.format(query=query, variables=variables)
    response = client.request(url, headers=headers)
    broadcasts = response['data']['broadcasts']

    items = []

    utc_now = control.to_timestamp(datetime.datetime.now())

    for broadcast in broadcasts:
        media_id = str(broadcast.get('mediaId', 0))

        if is_globosat_available and media_id != str(GLOBO_AMERICAS_ID):
            continue

        epg = next((epg for epg in broadcast['epgByDate']['entries'] if epg['startTime'] <= utc_now < epg['endTime']), {})

        channel = broadcast.get('channel', {}) or {}

        logo = channel.get('logo', None)
        channel_name = broadcast.get('media', {}).get('headline', '')
        fanart = broadcast.get('imageOnAir', None)
        channel_id = channel.get('id', 0)
        service_id = broadcast.get('media', {}).get('serviceId', 0)
        channel_slug = '%s-americas' % channel.get('name', '').lower().replace(' ', '')

        duration = epg.get('durationInMinutes', 0) * 60

        title_obj = epg.get('title', {}) or {}

        title = epg.get('name', '')
        description = title_obj.get('description', None) or epg.get('description', '')
        fanart = title_obj.get('cover', {}).get('landscape', fanart) or fanart

        year = title_obj.get('releaseYear', None)
        country = [c.get('name') for c in title_obj.get('countries', []) or [] if 'name' in c and c['name']]
        genres = [c.get('name') for c in title_obj.get('genres', []) or [] if 'name' in c and c['name']]
        cast = [c.get('name') for c in title_obj.get('cast', []) or [] if 'name' in c and c['name']]
        director = [c.get('name') for c in title_obj.get('directors', []) or [] if 'name' in c and c['name']]
        rating = epg.get('contentRating', '')

        name = ('[B]' if not control.isFTV else '') + channel_name + ('[/B]' if not control.isFTV else '') + ('[I] - ' + title + '[/I]' if title else '')

        program_datetime = datetime.datetime.utcfromtimestamp(epg.get('startTime', 0)) + util.get_utc_delta()
        next_start = datetime.datetime.utcfromtimestamp(epg.get('endTime', 0)) + util.get_utc_delta()

        plotoutline = datetime.datetime.strftime(program_datetime, '%H:%M') + ' - ' + datetime.datetime.strftime(next_start, '%H:%M')

        if not description or len(description) < 3:
            description = '%s | %s' % (title, plotoutline) if title else plotoutline

        item = {
            'name': name,
            'title': title,
            'tvshowtitle': title,
            'plot': description,
            'plotoutline': plotoutline,
            "tagline": description,
            'duration': duration,
            "dateadded": datetime.datetime.strftime(program_datetime, '%Y-%m-%d %H:%M:%S'),
            'brplayprovider': 'globoplay',
            'logo': logo,
            'clearlogo': logo,
            'thumb': fanart,
            'poster': None,
            'fanart': fanart,
            'slug': channel_slug,
            'sorttitle': channel_name,
            'studio': channel_name,
            'playable': 'true',
            'id': media_id,
            'channel_id': channel_id,
            'service_id': service_id,
            'live': epg.get('liveBroadcast', False) or False,
            'year': year,
            'country': country,
            'genre': genres,
            'cast': cast,
            'director': director,
            'mpaa': rating,
            'livefeed': 'false',  # force vod player for us channels
            "mediatype": 'video'  # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
        }

        items.append(item)

    return items
