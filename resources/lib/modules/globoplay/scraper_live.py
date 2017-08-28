# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import util
from resources.lib.modules import workers
import datetime,re
from sqlite3 import dbapi2 as database
import time

GLOBO_LOGO = 'http://s3.glbimg.com/v1/AUTH_180b9dd048d9434295d27c4b6dadc248/media_kit/42/f3/a1511ca14eeeca2e054c45b56e07.png'
GLOBO_FANART = control.addonFanart()

GLOBOPLAY_APIKEY = '35978230038e762dd8e21281776ab3c9'


def get_globo_live_id():
    return 4452349


def get_live_channels():

    affiliate_temp = control.setting('globo_affiliate')

    # In settings.xml - globo_affiliate
    # 0 = All
    # 1 = Rio de Janeiro
    # 2 = Sao Paulo
    # 3 = Brasilia
    # 4 = Belo Horizonte
    # 5 = Recife

    if affiliate_temp == '0':
        affiliate = 'All'
    elif affiliate_temp == '2':
        affiliate = 'Sao Paulo'
    elif affiliate_temp == '3':
        affiliate = 'Brasilia'
    elif affiliate_temp == '4':
        affiliate = 'Belo Horizonte'
    elif affiliate_temp == '5':
        affiliate = 'Recife'
    # elif affiliate_temp == '6':
    #     affiliate = 'Salvador'
    # elif affiliate_temp == '7':
    #     affiliate = 'Fortaleza'
    # elif affiliate_temp == '8':
    #     affiliate = 'Aracaju'
    # elif affiliate_temp == '9':
    #     affiliate = 'Maceio'
    # elif affiliate_temp == '10':
    #     affiliate = 'Cuiaba'
    # elif affiliate_temp == '11':
    #     affiliate = 'Porto Alegre'
    # elif affiliate_temp == '12':
    #     affiliate = 'Florianopolis'
    # elif affiliate_temp == '13':
    #     affiliate = 'Curitiba'
    # elif affiliate_temp == '14':
    #     affiliate = 'Vitoria'
    # elif affiliate_temp == '15':
    #     affiliate = 'Goiania'
    # elif affiliate_temp == '16':
    #     affiliate = 'Campo Grande'
    # elif affiliate_temp == '17':
    #     affiliate = 'Manaus'
    # elif affiliate_temp == '18':
    #     affiliate = 'Belem'
    # elif affiliate_temp == '19':
    #     affiliate = 'Macapa'
    # elif affiliate_temp == '20':
    #     affiliate = 'Palmas'
    # elif affiliate_temp == '21':
    #     affiliate = 'Rio Branco'
    # elif affiliate_temp == '22':
    #     affiliate = 'Teresina'
    # elif affiliate_temp == '23':
    #     affiliate = 'Sao Luis'
    # elif affiliate_temp == '24':
    #     affiliate = 'Joao Pessoa'
    # elif affiliate_temp == '25':
    #     affiliate = 'Natal'
    else:
        affiliate = 'Rio de Janeiro'

    if affiliate == "All":
        # affiliates = ['Rio de Janeiro','Sao Paulo','Brasilia','Belo Horizonte','Recife','Salvador','Fortaleza','Aracaju','Maceio','Cuiaba','Porto Alegre','Florianopolis','Curitiba','Vitoria','Goiania','Campo Grande','Manaus','Belem','Macapa','Palmas','Rio Branco','Teresina','Sao Luis','Joao Pessoa','Natal']
        affiliates = ['Rio de Janeiro','Sao Paulo','Brasilia','Belo Horizonte','Recife']
    else:
        affiliates = [affiliate]

    live = []
    threads = [workers.Thread(__append_result, __get_affiliate_live_channels, live, affiliate) for affiliate in affiliates]
    [i.start() for i in threads]
    [i.join() for i in threads]

    return live


def __append_result(fn, list, *args):
        item = fn(*args)
        if item:
            list.append(item)


def __get_affiliate_live_channels(affiliate):
    liveglobo = get_globo_live_id()

    if affiliate == "Sao Paulo":
        code, geo_position = "SP1", 'lat=-23.5505&long=-46.6333'
    elif affiliate == "Brasilia":
        code, geo_position = "DF", 'lat=-15.7942&long=-47.8825'
    elif affiliate == "Belo Horizonte":
        code, geo_position = "BH", 'lat=-19.9245&long=-43.9352'
    elif affiliate == "Recife":
        code, geo_position = "PE1", 'lat=-8.0476&long=-34.8770'

    # elif affiliate == "Salvador":
    #     code, geo_position = "SAL", 'lat=-12.9722&long=-38.5014'
    # elif affiliate == "Fortaleza":
    #     code, geo_position = "CE1", 'lat=-3.7319&long=-38.5267'
    # elif affiliate == "Aracaju":
    #     code, geo_position = "SER", 'lat=-10.9472&long=-37.0731'
    # elif affiliate == "Maceio":
    #     code, geo_position = "MAC", 'lat=-9.6498&long=-35.7089'
    # elif affiliate == "Cuiaba":
    #     code, geo_position = "MT", 'lat=-15.6014&long=-56.0979'
    # elif affiliate == "Porto Alegre":
    #     code, geo_position = "RS1", 'lat=-30.0347&long=-51.2177'
    # elif affiliate == "Florianopolis":
    #     code, geo_position = "SC1", 'lat=-27.5949&long=-48.5482'
    # elif affiliate == "Curitiba":
    #     code, geo_position = "CUR", 'lat=-25.4244&long=-49.2654'
    # elif affiliate == "Vitoria":
    #     code, geo_position = "VIT", 'lat=-20.2976&long=-40.2958'
    # elif affiliate == "Goiania":
    #     code, geo_position = "GO01", 'lat=-16.6869&long=-49.2648'
    # elif affiliate == "Campo Grande":
    #     code, geo_position = "MS1", 'lat=-20.4697&long=-54.6201'
    # elif affiliate == "Manaus":
    #     code, geo_position = "MAN", 'lat=-3.1190&long=-60.0217'
    # elif affiliate == "Belem":
    #     code, geo_position = "BEL", 'lat=-1.4558&long=-48.4902'
    # elif affiliate == "Macapa":
    #     code, geo_position = "AMP", 'lat=-0.0356&long=-51.0705'
    # elif affiliate == "Palmas":
    #     code, geo_position = "PAL", 'lat=-10.2491&long=-48.3243'
    # elif affiliate == "Rio Branco":
    #     code, geo_position = "ACR", 'lat=-9.9754&long=-67.8249'
    # elif affiliate == "Teresina":
    #     code, geo_position = "TER", 'lat=-5.0920&long=-42.8038'
    # elif affiliate == "Sao Luis":
    #     code, geo_position = "MA1", 'lat=-2.5391&long=-44.2829'
    # elif affiliate == "Joao Pessoa":
    #     code, geo_position = "JP", 'lat=-7.1195&long=-34.8450'
    # elif affiliate == "Natal":
    #     code, geo_position = "NAT", 'lat=-5.7793&long=-35.2009'
    else:
        code, geo_position = "RJ", 'lat=-22.900&long=-43.172'

    live_program = __get_live_program(code)

    if not live_program:
        return None

    program_description = get_program_description(live_program['program_id_epg'], live_program['program_id'], code)

    control.log("program_description: %s" % repr(program_description))

    item = {
        'plot': None,
        'duration': None,
        'affiliate': geo_position,
        'brplayprovider': 'globoplay',
        'affiliate_code': code,
        'logo': None
    }

    item.update(program_description)

    item.pop('datetimeutc', None)

    title = program_description['title'] if 'title' in program_description else 'N/A'
    subtitle = program_description['subtitle'] if 'subtitle' in program_description else 'N/A'

    item.update({
        'slug': 'globo',
        'name': 'Globo ' + re.sub(r'\d+','',code) + '[I] - ' + title + '[/I]',
        'title': subtitle, #'Globo ' + re.sub(r'\d+','',code) + '[I] - ' + program_description['title'] + '[/I]',
        'tvshowtitle': title,
        'sorttitle': 'Globo ' + re.sub(r'\d+','',code),
        'clearlogo': GLOBO_LOGO,
        # 'tagline': program_description['title'],
        'studio': 'Rede Globo - ' + affiliate,
        # 'logo': GLOBO_LOGO,
        'playable': 'true',
        'id': liveglobo,
        'channel_id': 196,
        'live': True,
        'fanart': GLOBO_FANART
    })

    return item


def __get_live_program(affiliate='RJ'):
    headers = {'Accept-Encoding': 'gzip'}
    url = 'https://api.globoplay.com.br/v1/live/%s?api_key=%s' % (affiliate, GLOBOPLAY_APIKEY)

    response = client.request(url, headers=headers)

    if not 'live' in response:
        return None

    live = response['live']

    return {
        'poster': live['poster'],
        'program_id': live['program_id'],
        'program_id_epg': live['program_id_epg'],
        'title': live['program_name']
    }


def get_program_description(program_id_epg, program_id, affiliate='RJ'):

    today = datetime.datetime.utcnow() - datetime.timedelta(hours=8)  # GMT-3 epg timezone - Schedule starts at 5am = GMT-8
    today = today if not today is None else datetime.datetime.utcnow() - datetime.timedelta(hours=8)  # GMT-3 - Schedule starts at 5am = GMT-8
    today_string = datetime.datetime.strftime(today, '%Y-%m-%d')

    day_schedule = __get_or_add_full_day_schedule_cache(today_string, affiliate, 24)

    return next(iter(sorted((slot for slot in day_schedule if ((slot['id_programa'] == program_id_epg and slot['id_programa'] is not None) or (slot['id_webmedia'] == program_id and slot['id_webmedia'] is not None)) and slot['datetimeutc'] < datetime.datetime.utcnow()), key=lambda x: x['datetimeutc'], reverse=True)), {})


def __get_or_add_full_day_schedule_cache(date_str, affiliate, timeout):
    control.makeFile(control.dataPath)
    dbcon = database.connect(control.cacheFile)

    try:
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT response, added FROM globoplay_schedule WHERE date_str = ? AND affiliate = ?", (date_str, affiliate))
        match = dbcur.fetchone()

        response = eval(match[0].encode('utf-8'))

        t1 = int(match[1])
        t2 = int(time.time())
        update = (abs(t2 - t1) / 3600) >= int(timeout)
        if update == False:
            control.log("Returning globoplay_schedule cached response for affiliate %s and date_str %s" % (affiliate, date_str))
            return response
    except Exception as ex:
        control.log("CACHE ERROR: %s" % repr(ex))
        pass

    control.log("Fetching FullDaySchedule for %s: %s" % (affiliate, date_str))
    r = __get_full_day_schedule(date_str, affiliate)
    if (r is None or r == []) and not response is None:
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

    url = "https://api.globoplay.com.br/v1/epg/%s/praca/%s?api_key=%s" % (today, affiliate, GLOBOPLAY_APIKEY)
    headers = {'Accept-Encoding': 'gzip'}
    slots = client.request(url, headers=headers)['gradeProgramacao']['slots']

    result = []
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
                        castandrole = [(c.strip().split(':')[1].strip(), c.strip().split(':')[0].strip()) for c in castandrole_raw[0].split('/')]
                        if len(castandrole_raw) > 1: #Outros dubladores sem papel definido
                            castandrole = [(c.strip(), 'Outros') for c in castandrole_raw[1].split('/')]
            except Exception as ex:
                control.log("ERROR POPULATING CAST: %s" % repr(ex))
                pass

        program_datetime_utc = util.strptime_workaround(slot['data_exibicao_e_horario']) + datetime.timedelta(hours=3)
        program_datetime = program_datetime_utc + util.get_utc_delta()

        # program_local_date_string = datetime.datetime.strftime(program_datetime, '%d/%m/%Y %H:%M')

        title = slot['nome_programa'] if 'nome_programa' in slot else None
        if slot["tipo"] == "confronto":
            showtitle = slot['confronto']['titulo_confronto'] + ' - ' + slot['confronto']['participantes'][0]['nome'] + ' X ' + slot['confronto']['participantes'][1]['nome']
        else:
            showtitle = slot['nome'] if 'nome' in slot else None

        next_start = slots[index+1]['data_exibicao_e_horario'] if index+1 < len(slots) else None
        next_start = (util.strptime_workaround(next_start) + datetime.timedelta(hours=3) + util.get_utc_delta()) if next_start else datetime.datetime.now()

        item = {
            "tagline": slot['chamada'] if 'chamada' in slot else slot['nome'],
            "closed_caption": slot['closed_caption'],
            "facebook": slot['facebook'],
            "twitter": slot['twitter'],
            "hd": slot['hd'],
            "id": slot['id'],
            "id_programa": slot['id_programa'],
            "id_webmedia": slot['id_webmedia'],
            "fanart": 'https://s02.video.glbimg.com/x720/%s.jpg' % get_globo_live_id(),
            "thumb": slot['imagem'],
            "logo": slot['logo'],
            "clearlogo": slot['logo'],
            "poster": slot['poster'] if 'poster' in slot else 'None',
            "subtitle": slot['nome'],
            "title": title,
            "plot": slot['resumo'] if 'resumo' in slot else None, #program_local_date_string + ' - ' + (slot['resumo'] if 'resumo' in slot else showtitle.replace(' - ', '\n') if showtitle and len(showtitle) > 0 else slot['nome_programa']),
            "plotoutline": datetime.datetime.strftime(program_datetime, '%H:%M') + ' - ' + datetime.datetime.strftime(next_start, '%H:%M'),
            "mediatype": 'episode' if showtitle and len(showtitle) > 0 else 'video',
            "genre": slot['tipo_programa'],
            "datetimeutc": program_datetime_utc,
            "dateadded": datetime.datetime.strftime(program_datetime, '%Y-%m-%d %H:%M:%S'),
            # 'StartTime': datetime.datetime.strftime(program_datetime, '%H:%M:%S'),
            # 'EndTime': datetime.datetime.strftime(next_start, '%H:%M:%S'),
            'duration': util.get_total_seconds(next_start - program_datetime)
        }

        if showtitle and len(showtitle) > 0:
            item.update({
                'tvshowtitle': showtitle
            })

        if slot['tipo'] == 'filme':
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