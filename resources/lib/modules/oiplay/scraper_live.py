import requests
from resources.lib.modules import workers
from resources.lib.modules import util
from resources.lib.modules import cache
import datetime
import player

PLAYER_HANDLER = player.__name__


def get_live_channels():
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/lists/651acd5c-236d-47d1-9e57-584a233ab76a?limit=200&orderby=titleAsc&page=1&useragent=androidtv'
    response = requests.get(url).json()

    channels = []

    threads = [workers.Thread(__merge_channel_data, channel['prgSvcId'], channels) for channel in response['items']]
    [i.start() for i in threads]
    [i.join() for i in threads]

    return channels


def __merge_channel_data(channel, result):
    data = get_channel_epg_now(channel)
    result.append(data)


def get_channel_epg_now(channel):
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/epg/{channel}/beforenowandnext?beforeCount=0&nextCount=0&includeCurrentProgram=true'.format(channel=channel)
    response = requests.get(url).json()

    now = response['schedules'][0]
    program = now['program']

    title = program['seriesTitle']
    series = u" (S" + str(program['seasonNumber']) + u':E' + str(program['episodeNumber']) + u")" if program['programType'] == 'Series' else u''
    episode_title = program['title'] + series if 'title' in program and program['title'] != title else ''
    studio = response['title']

    thumb = None
    fanart = None
    if 'programImages' in program and len(program['programImages']) > 0:
        thumb = next((image['url'] for image in program['programImages'] if image['type'] == 'Thumbnail'), None)
        fanart = next((image['url'] for image in program['programImages'] if image['type'] == 'Backdrop'), thumb) or thumb
        thumb = thumb or fanart

    logo = response['positiveLogoUrl']

    cast = [c['name'] for c in program['castMembers']]

    date = util.strptime(now['startTimeUtc'], '%Y-%m-%dT%H:%M:%SZ') + util.get_utc_delta()
    program_name = title + (u': ' + episode_title if episode_title else u'')
    return {
        'handler': PLAYER_HANDLER,
        'method': 'playlive',
        'id': response['prgSvcId'],
        'IsPlayable': True,
        'livefeed': True,
        'label': u"[B]" + studio + u"[/B][I] - " + program_name + u"[/I]",
        'studio': 'Oi Play',
        # 'title': episode_title,
        # 'tvshowtitle': title,
        'sorttitle': program_name,
        'channel_id': response['prgSvcId'],
        'dateadded': datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'),
        'plot': program['synopsis'],
        'duration': now['durationSeconds'],
        'adult': program['isAdult'],
        'cast': cast,
        'director': program['directors'],
        'genre': program['genres'],
        'rating': program['rating'],
        'year': program['releaseYear'],
        'episode': program['episodeNumber'] if program['episodeNumber'] else None,
        'season': program['seasonNumber'] if program['seasonNumber'] else None,
        'art': {
            'icon': logo,
            'thumb': thumb,
            'tvshow.poster': thumb,
            'clearlogo': logo,
            'fanart': fanart
        }
    }


def get_epg(start, end, channel_map):
    start_time = datetime.datetime.strftime(start, '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.datetime.strftime(end, '%Y-%m-%dT%H:%M:%SZ')
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/epg?starttime={starttime}&endtime={endtime}&liveSubscriberGroup={channelmap}'.format(starttime=start_time, endtime=end_time, channelmap=channel_map)
    epg = cache.get(requests.get, 20, url, table='oiplay').json()
    return epg
