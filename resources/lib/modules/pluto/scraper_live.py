import requests
import datetime
import uuid
from resources.lib.modules import control, util, cache


proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


def get_live_channels():

    start_date = datetime.datetime.utcnow()
    stop_date = start_date + datetime.timedelta(hours=6)

    url = 'https://api.pluto.tv/v2/channels?start=' + start_date.strftime('%Y-%m-%dT%H:00:00.000Z') + '&stop=' + stop_date.strftime('%Y-%m-%dT%H:00:00.000Z')

    response = cache.get(requests.get, 4, url, proxies=proxy, table='pluto').json()

    now_str = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')

    for channel in response:

        if 'timelines' not in channel:
            continue

        program = next(p for p in channel['timelines'] if p['start'] <= now_str < p['stop'])

        is_live = program.get('liveBroadcast', False)
        live_text = u' (' + control.lang(32004) + u')' if is_live else u''

        title = program.get('title')
        sub_title = program.get('episode', {}).get('name')
        thumb = program.get('episode', {}).get('series', {}).get('featuredImage', {}).get('path') or program.get('episode', {}).get('poster', {}).get('path') or None
        fanart = thumb
        logo = channel['colorLogoPNG']['path']

        program_name = title + (u': ' + sub_title if sub_title else u'')

        duration_milliseconds = int(program['episode']['duration'])
        start_time = util.strptime_workaround(program['start'], '%Y-%m-%dT%H:%M:%S.%fZ')
        stop_time = start_time + datetime.timedelta(milliseconds=duration_milliseconds)

        program_time_desc = datetime.datetime.strftime(start_time, '%H:%M') + ' - ' + datetime.datetime.strftime(stop_time, '%H:%M')
        tags = [program_time_desc]

        description = '%s | %s' % (program_time_desc, program.get('episode', {}).get('description'))

        studio = channel['name']

        label = u"[B]%s[/B][I] - %s[/I]%s" % (studio, program_name, live_text)

        genres = [program.get('episode', {}).get('genre').upper(),
                    program.get('episode', {}).get('subGenre').upper(),
                    program.get('episode', {}).get('series', {}).get('type').upper()]

        sid = control.setting('pluto_sid')
        if not sid:
            sid = str(uuid.uuid4())
            control.setSetting('pluto_sid', sid)
        did = control.setting('pluto_did')
        if not did:
            did = str(uuid.uuid4())
            control.setSetting('pluto_did', did)

        video_url = u'https://service-stitcher.clusters.pluto.tv/stitch/hls/channel/{channel}/master.m3u8?deviceType=web&deviceMake=Chrome&deviceModel=Chrome&sid={sid}&deviceId={did}&deviceVersion=74.0.3729.131&appVersion=2.5.1-f9a6096b469cfe5e4f1cc92cc697e8500e57891c&deviceDNT=0&userId=&advertisingId=&deviceLat=38.8177&deviceLon=-77.1527&app_name=&appName=&buildVersion=&appStoreUrl=&architecture='.format(channel=channel['_id'], sid=sid, did=did)
        # video_url = channel.get('stitched', {}).get('urls', [])[0].get('url')

        yield {
            'url': video_url,
            'IsPlayable': True,
            'label': label,
            'title': label,
            'studio': 'Pluto TV',
            'tvshowtitle': title,
            'sorttitle': program_name,
            'dateadded': datetime.datetime.strftime(start_time, '%Y-%m-%d %H:%M:%S'),
            'plot': description,
            'tag': tags,
            'duration': duration_milliseconds / 1000,
            'adult': False,
            'genre': genres,
            'year': program.get('episode', {}).get('clip', {}).get('originalReleaseDate', '')[0:4],
            'rating': program.get('episode', {}).get('rating'),
            'episode': program.get('episode', {}).get('number'),
            'art': {
                'icon': logo,
                'thumb': thumb,
                'tvshow.poster': thumb,
                'clearlogo': logo,
                'fanart': fanart
            }
        }
