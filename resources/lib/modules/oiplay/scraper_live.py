from resources.lib.modules import client
from resources.lib.modules import workers
from resources.lib.modules import util
import datetime


def get_live_channels():
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/lists/651acd5c-236d-47d1-9e57-584a233ab76a?limit=200&orderby=titleAsc&page=1&useragent=androidtv'
    response = client.request(url)

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
    response = client.request(url)

    now = response['schedules'][0]
    program = now['program']

    title = program['seriesTitle']
    studio = response['title']

    thumb = None
    fanart = None
    if 'programImages' in program and len(program['programImages']) > 0:
        thumb = next(image['url'] for image in program['programImages'] if image['type'] == 'Thumbnail')
        fanart = next(image['url'] for image in program['programImages'] if image['type'] == 'Backdrop') or thumb
        thumb = thumb or fanart

    logo = response['positiveLogoUrl']

    cast = [c['name'] for c in program['castMembers']]

    date = util.strptime(now['startTimeUtc'], '%Y-%m-%dT%H:%M:%SZ') + util.get_utc_delta()

    return {
        'slug': response['callLetter'],
        'name': "[B]" + studio + "[/B][I] - " + title + "[/I]",
        'studio': studio,
        'title': title,
        'tvshowtitle': title,
        'sorttitle': studio,
        'thumb': thumb,
        'logo': logo,
        'clearlogo': logo,
        'clearart': logo,
        'banner': None,
        'color': None,
        'fanart': fanart,
        'id': response['prgSvcId'],
        'channel_id': response['prgSvcId'],
        'brplayprovider': 'oiplay',
        'playable': 'true',
        'livefeed': 'true',
        'dateadded': datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'),
        'plot': program['synopsis'],
        'duration': now['durationSeconds'],
        'adult': program['isAdult'],
        'cast': cast,
        'director': program['directors'],
        'genre': program['genres'],
        'rating': program['rating'],
        'year': program['releaseYear'],
        "mediatype": 'episode' if program['episodeNumber'] else 'video'
    }


def get_epg(start, end, channel_map):
    start_time = datetime.datetime.strftime(start, '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.datetime.strftime(end, '%Y-%m-%dT%H:%M:%SZ')
    url = 'https://apim.oi.net.br/app/oiplay/ummex/v1/epg?starttime={starttime}&endtime={endtime}&liveSubscriberGroup={channelmap}'.format(starttime=start_time, endtime=end_time, channelmap=channel_map)
    epg = client.request(url)
    return epg
