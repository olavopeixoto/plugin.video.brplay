# -*- coding: utf-8 -*-

from resources.lib.modules import control, cache, util, workers
import requests
from . import player
import datetime
import time
import os
from . import get_authorized_services, request_query, auth_helper, get_tenant

GLOBO_LOGO = 'http://s3.glbimg.com/v1/AUTH_180b9dd048d9434295d27c4b6dadc248/media_kit/42/f3/a1511ca14eeeca2e054c45b56e07.png'
GLOBO_FANART = os.path.join(control.artPath(), 'globo.jpg')

GLOBOPLAY_APIKEY = '35978230038e762dd8e21281776ab3c9'

LOGO_BBB = 'https://s.glbimg.com/pc/gm/media/dc0a6987403a05813a7194cd0fdb05be/2014/12/1/7e69a2767aebc18453c523637722733d.png'
FANART_BBB = 'http://s01.video.glbimg.com/x1080/244881.jpg'

PLAYER_HANDLER = player.__name__
PLAYSTREAM_METHOD = player.Player.play_stream.__name__


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
    '2333': 'glbeua',
    '4446': 'glbeua',
    '4452': 'glbpt'
}


def get_globo_live_id():
    return GLOBO_LIVE_SUBSCRIBER_MEDIA_ID if auth_helper.is_subscribed() else GLOBO_LIVE_MEDIA_ID


def get_live_channels():

    affiliate_id = control.setting('globo_affiliate')

    affiliates = control.get_affiliates_by_id(int(affiliate_id))

    live = []

    if get_tenant() == auth_helper.TENANTS.GLOBO_PLAY:
        if len(affiliates) == 1 and not is_globoplay_mais_canais_available():
            affiliate = __get_affiliate_live_channels(affiliates[0])
            live.extend(affiliate)
        else:
            threads = [workers.Thread(__get_affiliate_live_channels, affiliate) for affiliate in affiliates]
            if is_globoplay_mais_canais_available():
                threads.append(workers.Thread(get_epg_broadcast_list))
            [i.start() for i in threads]
            [i.join() for i in threads]
            [live.extend(i.get_result() or []) for i in threads]
    else:
        live.extend(get_epg_broadcast_list())

    seen = []
    filtered_channels = list(filter(lambda x: seen.append(x['affiliate_code'] if 'affiliate_code' in x else '$FOO$') is None if 'affiliate_code' not in x or x['affiliate_code'] not in seen else False, live))

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

    return get_broadcast_with_coordinates(live_globo_id, latitude, longitude, code)


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


def get_broadcast_with_coordinates(media_id, latitude, longitude, affiliate_code, date=None):
    if not date:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=control.get_current_brasilia_utc_offset())
        date = now.strftime('%Y-%m-%d')
    variables = '{{"date":"{date}","mediaId":"{media_id}","coordinates":{{"lat":"{lat}", "long": "{long}"}}}}'.format(media_id=media_id, lat=latitude, long=longitude, date=date)
    query = 'query%20Epg%28%24mediaId%3A%20ID%21%2C%20%24coordinates%3A%20CoordinatesData%2C%20%24date%3A%20Date%21%29%20%7B%0A%20%20broadcast%28mediaId%3A%20%24mediaId%2C%20coordinates%3A%20%24coordinates%29%20%7B%0A%20%20%20%20...EpgFragment%0A%20%20%7D%0A%7D%0Afragment%20EpgFragment%20on%20Broadcast%20%7B%0A%20%20mediaId%0A%20%20imageOnAir%28scale%3A%20X1080%29%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20slug%0A%20%20%7D%0A%20%20affiliateSignal%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20dtvChannel%0A%20%20%20%20%20%20dtvHDID%0A%20%20%20%20%20%20dtvID%0A%20%20%20%20%7D%0A%20%20media%20%7B%0A%20%20%20%20serviceId%0A%20%20%20%20headline%0A%20%20%20%20thumb%28size%3A%20720%29%0A%20%20%20%20availableFor%0A%20%20%20%20title%20%7B%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20headline%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20epgByDate%28date%3A%20%24date%29%20%7B%0A%20%20%20%20entries%20%7B%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20programId%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20alternativeTime%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20title%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%20%20portrait%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    response = request_query(query, variables, timeout_hour=24)
    broadcast = (response.get('data', {}) or {}).get('broadcast', {}) or {}

    utc_now = int(datetime.datetime.now().timestamp())

    if broadcast['epgByDate']['entries'] and utc_now >= max(int(epg['endTime']) for epg in broadcast['epgByDate']['entries']):
        date = (strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        yield from get_broadcast_with_coordinates(media_id, latitude, longitude, affiliate_code, date)
        return

    epg = next((epg for epg in broadcast['epgByDate']['entries'] if int(epg['startTime']) <= utc_now < int(epg['endTime'])), {})
    control.log('EPG: %s' % epg)

    channel = broadcast.get('channel', {}) or {}

    logo = channel.get('logo')
    channel_name = '%s %s' % (channel.get('name', ''), affiliate_code)
    fanart = broadcast.get('imageOnAir')
    channel_id = channel.get('id', 0)
    service_id = broadcast.get('media', {}).get('serviceId', 0)

    duration = epg.get('durationInMinutes', 0) * 60

    title_obj = epg.get('title', {}) or {}

    title = '%s: %s' % (epg.get('name', ''), epg.get('metadata')) if epg.get('metadata') else epg.get('name', '')
    description = title_obj.get('description') or epg.get('description', '')
    fanart = (title_obj.get('cover', {}) or {}).get('landscape', fanart) or fanart
    poster = (title_obj.get('poster', {}) or {}).get('web')
    thumb = SNAPSHOT_URL.format(transmission='globo-' + str(affiliate_code).lower()) + '?=' + str(int(time.time()))

    label = '[B]' + channel_name + '[/B]' + ('[I] - ' + title + '[/I]' if title else '')

    program_datetime = datetime.datetime.utcfromtimestamp(epg.get('startTime', 0)) + util.get_utc_delta()
    next_start = datetime.datetime.utcfromtimestamp(epg.get('endTime', 0)) + util.get_utc_delta()

    plotoutline = datetime.datetime.strftime(program_datetime, '%H:%M') + ' - ' + datetime.datetime.strftime(next_start, '%H:%M')

    description = '%s | %s' % (plotoutline, description)

    yield {
        'handler': PLAYER_HANDLER,
        'method': PLAYSTREAM_METHOD,
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
        'country': title_obj.get('countries', []) or [],
        'genre': title_obj.get('genresNames', []) or [],
        'cast': title_obj.get('castNames', []) or [],
        'director': title_obj.get('directorsNames', []) or [],
        'writer': title_obj.get('screenwritersNames', []) or [],
        'credits': title_obj.get('artDirectorsNames', []) or [],
        'mpaa': epg.get('contentRating'),
        "art": {
            'icon': logo,
            'clearlogo': logo,
            'thumb': thumb,
            'fanart': fanart,
            'tvshow.poster': poster
        }
    }


def is_globoplay_mais_canais_available():
    if not control.is_globoplay_mais_canais_ao_vivo_available():
        return False

    return control.globoplay_ignore_channel_authorization() or auth_helper.is_service_allowed(auth_helper.CADUN_SERVICES.GSAT_CHANNELS)


def get_epg_broadcast_list(date=None):
    if not date:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=control.get_current_brasilia_utc_offset())
        date = now.strftime('%Y-%m-%d')
    control.log('get_epg_broadcast_list(%s)' % date)
    variables = '{{"date":"{}"}}'.format(date)
    query = 'query%20getEpgBroadcastList%28%24date%3A%20Date%21%29%20%7B%0A%20%20broadcasts%20%7B%0A%20%20%20%20...broadcastFragment%0A%20%20%7D%0A%7D%0Afragment%20broadcastFragment%20on%20Broadcast%20%7B%0A%20%20mediaId%0A%20%20media%20%7B%0A%20%20%20%20serviceId%0A%20%20%20%20liveThumbnail%0A%20%20%20%20headline%0A%20%20%20%20thumb%28size%3A%20720%29%0A%20%20%20%20availableFor%0A%20%20%20%20title%20%7B%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20headline%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20imageOnAir%28scale%3A%20X1080%29%0A%20%20transmissionId%0A%20%20geofencing%0A%20%20geoblocked%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20color%0A%20%20%20%20name%0A%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%7D%0A%20%20epgByDate%28date%3A%20%24date%29%20%7B%0A%20%20%20%20entries%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20metadata%0A%20%20%20%20%20%20description%0A%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20tags%0A%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20alternativeTime%0A%20%20%20%20%20%20title%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%20%20portrait%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    response = request_query(query, variables)
    broadcasts = response['data']['broadcasts']

    utc_now = int(datetime.datetime.now().timestamp())

    correct_date = False
    has_epg = False
    for broadcast in broadcasts:
        max_end_time = max((int(epg['endTime']) for epg in broadcast['epgByDate']['entries']), default=-1)
        control.log('MAX EPG [%s] %s END TIME: %s [%s]' % (broadcast.get('channel', {}).get('name'), date, max_end_time, utc_now))
        has_epg = has_epg or max_end_time > 0
        if utc_now < max_end_time > 0:
            correct_date = True
            break

    if has_epg and not correct_date:
        date = (strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        yield from get_epg_broadcast_list(date)
        return

    for broadcast in broadcasts:
        channel = broadcast.get('channel', {}) or {}
        service_id = broadcast.get('media', {}).get('serviceId', 0)

        if channel.get('id') == '196' and get_tenant() == auth_helper.TENANTS.GLOBO_PLAY:
            control.log('Channel 196 ignored. Tenant: ' + get_tenant())
            continue

        if not control.globoplay_ignore_channel_authorization():
            if not auth_helper.is_service_allowed(service_id):
                continue

        if not control.is_globoplay_mais_canais_ao_vivo_available():
            if service_id == auth_helper.CADUN_SERVICES.GSAT_CHANNELS:
                continue

        media_id = str(broadcast.get('mediaId', 0))

        epg = next((epg for epg in broadcast['epgByDate']['entries'] if int(epg['startTime']) <= utc_now < int(epg['endTime'])), {})

        control.log('EPG: %s' % epg)

        logo = channel.get('logo')

        if channel.get('id') == '196':
            tenant = get_tenant().replace('globo-play', '').replace('-', '').upper()
            channel_name = '%s %s' % (channel.get('name', ''), tenant)
        else:
            channel_name = (broadcast.get('media', {}) or {}).get('headline', '').replace('Agora no ', '').replace(
                'Agora na ', '').strip()  # channel.get('name', '')

        fanart = broadcast.get('imageOnAir')
        channel_id = channel.get('id', 0)

        duration = epg.get('durationInMinutes', 0) * 60

        title_obj = epg.get('title', {}) or {}

        title = '%s: %s' % (epg.get('name', ''), epg.get('metadata')) if epg.get('metadata') else epg.get('name', '')
        description = title_obj.get('description') or epg.get('description', '')
        fanart = (title_obj.get('cover', {}) or {}).get('landscape', fanart) or fanart
        poster = (title_obj.get('poster', {}) or {}).get('web')
        thumb = broadcast.get('media', {}).get('liveThumbnail', fanart) + '?=' + str(int(time.time()))

        # if not title:
        #     transmission_id = broadcast.get('transmissionId')
        #     search_date = strptime(date, '%Y-%m-%d')
        #     start_time = search_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        #     end_time = search_date.replace(hour=23, minute=59, second=0, microsecond=0).timestamp()
        #     alternative_epg = get_epg_by_transmission(transmission_id, int(start_time), int(end_time))
        #     control.log(alternative_epg)
        #     alt_epg = next((epg for epg in alternative_epg if int(epg['start_time']) <= utc_now < int(epg['end_time'])), {})
        #     control.log(alt_epg)
        #     title = alt_epg.get('program', '')
        #     control.log(title)

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
            'method': PLAYSTREAM_METHOD,
            'IsPlayable': True,
            'id': media_id,
            'channel_id': channel_id,
            'service_id': service_id,
            'live': epg.get('liveBroadcast', False) or False,
            'livefeed': True,
            'label': label,
            'title': title,
            # 'title': title,
            'tvshowtitle': title,
            'plot': description,
            # 'plotoutline': plotoutline,
            # "tagline": plotoutline,
            'tag': tags,
            'duration': duration,
            "dateadded": datetime.datetime.strftime(program_datetime, '%Y-%m-%d %H:%M:%S'),
            'sorttitle': title,
            'studio': auth_helper.get_service_name(service_id),
            'year': title_obj.get('releaseYear'),
            'country': title_obj.get('countries', []) or [],
            'genre': title_obj.get('genresNames', []) or [],
            'cast': title_obj.get('castNames', []) or [],
            'director': title_obj.get('directorsNames', []) or [],
            'writer': title_obj.get('screenwritersNames', []) or [],
            'credits': title_obj.get('artDirectorsNames', []) or [],
            'mpaa': epg.get('contentRating'),
            "art": {
                'icon': logo,
                'clearlogo': logo,
                'thumb': thumb,
                'fanart': fanart,
                'tvshow.poster': poster
            }
        }


def get_epg_by_transmission(transmission_id, start_time, end_time):
    url = 'https://epg-api.video.globo.com/v2/programs?transmission_id={transmission_id}&start_time={start_time}&end_time={end_time}'.format(transmission_id=transmission_id, start_time=start_time ,end_time=end_time)
    hours_cache = int((int(end_time) - int(datetime.datetime.now().timestamp())) / 60 / 60)

    control.log('{} - GET {}'.format('Globoplay', url))

    response = cache.get(requests.get, hours_cache, url, table='globoplay')

    if response.status_code != 200:
        return []

    json_response = response.json()

    control.log(json_response)

    return json_response.get('programs', []) or []


def strptime(string_date, format):
    try:
        res = datetime.datetime.strptime(string_date, format)
    except TypeError:
        res = datetime.datetime(*(time.strptime(string_date, format)[0:6]))

    return res
