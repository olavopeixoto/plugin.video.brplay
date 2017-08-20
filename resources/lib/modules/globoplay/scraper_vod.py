# -*- coding: utf-8 -*-

import auth
import resources.lib.modules.util as util
from resources.lib.modules import client
from resources.lib.modules import control

GLOBO_LOGO = 'http://s3.glbimg.com/v1/AUTH_180b9dd048d9434295d27c4b6dadc248/media_kit/42/f3/a1511ca14eeeca2e054c45b56e07.png'
GLOBO_FANART = 'https://s02.video.glbimg.com/x720/4452349.jpg'

GLOBOPLAY_URL = 'https://api.globoplay.com.br'
GLOBOPLAY_APIKEY = '4c3f033123840f740508ec49e89e5142'
GLOBOPLAY_CATEGORIAS = GLOBOPLAY_URL + '/v1/categories/?api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_DAYS = GLOBOPLAY_URL + '/v1/programs/%d/videos/days?api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_VIDEOS = GLOBOPLAY_URL + '/v1/programs/%d/videos?day=%s&order=asc&page=%d&per_page=%s&api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_VIDEOS_RANGE = GLOBOPLAY_URL + '/v1/programs/%d/videos?start=%s&end=%s&order=desc&per_page=%s&api_key=' + GLOBOPLAY_APIKEY

GLOBOPLAY_HIGHLIGHTS = GLOBOPLAY_URL + '/v2/highlights?api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_FAVORITES = 'http://api.user.video.globo.com/favorites?page=%s&per_page=%s'
GLOBOPLAY_WATCHHISTORY_BYPROGRAM = 'https://api.user.video.globo.com/watch_history/last_by_program?library_id=560d2da572696f10df000000&preload_metadata=true&limit=%s'
GLOBOPLAY_CONTINUEWATCHING_BYPROGRAM = 'https://api.user.video.globo.com/watch_history/last_by_program?library_id=560d2da572696f10df000000&preload_metadata=true&fully_watched=false&limit=%s'
GLOBOPLAY_MOST_WATCHED_VIDEOS = 'https://api.globoplay.com.br/v1/trilhos/mais-vistos?api_key=' + GLOBOPLAY_APIKEY

GLOBOPLAY_SEARCH = 'https://api.globoplay.com.br/v1/search?page=%s&q=%s&api_key=' + GLOBOPLAY_APIKEY

THUMB_URL = 'http://s01.video.glbimg.com/x720/%s.jpg'


def get_globoplay_channels():

    channels = []

    channels.append({
            'slug': 'globo',
            'name': 'Globo',
            'logo': GLOBO_LOGO,
            'clearlogo': GLOBO_LOGO,
            'fanart': GLOBO_FANART,
            'playable': 'false',
            'plot': None,
            'id': 196,
        })

    return channels


def get_extra_sections():

    extras = [{
        'id': '-highlights-',
        'title': control.lang(34011).encode('utf-8')
    },{
        'id': '-mostwatched-',
        'title': control.lang(34012).encode('utf-8')
    },{
        'id': '-continue-',
        'title': control.lang(34013).encode('utf-8')
    },{
        'id': '-favorites-',
        'title': control.lang(34014).encode('utf-8')
    },{
        'id': '-history-',
        'title': control.lang(34015).encode('utf-8')
    }]

    return extras


def get_globo_extra_episodes(category, page=1):
    if category == '-highlights-':
        return get_highlights()
    elif category == '-favorites-':
        return get_favorites(page)
    elif category == '-history-':
        return get_watch_history()
    elif category == '-continue-':
        return get_continue_watching()
    elif category == '-mostwatched-':
        return get_most_watched_videos()

    return [], None, 0


def get_highlights():
    videos = []
    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_HIGHLIGHTS, headers=headers)
    for item in data['highlights']:
        video = {
            'id': item['videoId'],
            'title': item['programName'],
            # 'tvshowtitle': item['program']['title'],
            'plot': item['description'],
            'duration': sum(int(x) * 60 ** i for i, x in
                            enumerate(reversed(item['duration'].split(':')))) if item['duration'] else 0,
            'thumb': item['thumb'],
            'fanart': item['thumb'],
            'clearlogo': GLOBO_LOGO,
            'mediatype': 'episode'
        }

        videos.append(video)

    return videos, None, 1


def get_favorites(page=1, per_page=10):
    videos = []

    username = control.setting('globoplay_username')
    password = control.setting('globoplay_password')

    # authenticate
    credentials = auth.auth().authenticate(username, password)
    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_FAVORITES % (page, per_page), cookie=credentials, headers=headers)

    if not data or not 'data' in data:
        return [], None, 0

    for item in data['data']:
        video = {
            'id': item['resource_id'],
            'title': item['metadata']['title'],
            'tvshowtitle': item['metadata']['program']['title'],
            'plot': item['metadata']['description'],
            'duration': int(item['metadata']['duration'])/1000 if item['metadata']['duration'] else 0,
            'thumb': THUMB_URL % item['resource_id'],
            'fanart': THUMB_URL % item['resource_id'],
            'date': item['metadata']['exhibited_at'],
            'mediatype': 'episode',
            'season': item['metadata']['season'] if 'season' in item['metadata'] else None,
            'episode': item['metadata']['episode'] if 'episode' in item['metadata'] else None,
            'year': item['metadata']['year'] if 'year' in item['metadata'] else None,
            'originaltitle': item['metadata']['original_title'] if 'original_title' in item['metadata'] else None
        }

        videos.append(video)

    pager = data['pager']

    return videos, pager['next_page'], pager['total_pages']


def get_watch_history():
    videos = []

    limit = 15

    username = control.setting('globoplay_username')
    password = control.setting('globoplay_password')

    # authenticate
    credentials = auth.auth().authenticate(username, password)

    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_WATCHHISTORY_BYPROGRAM % limit, cookie=credentials, headers=headers)

    if not data or not 'data' in data:
        return [], None, 0

    for item in data['data']:
        video = {
            'id': item['resource_id'],
            'title': item['metadata']['title'],
            'tvshowtitle': item['metadata']['program']['title'],
            'plot': item['metadata']['description'],
            'duration': int(item['metadata']['duration'])/1000 if item['metadata']['duration'] else 0,
            'thumb': THUMB_URL % item['resource_id'],
            'fanart': THUMB_URL % item['resource_id'],
            'clearlogo': GLOBO_LOGO,
            'aired': item['metadata']['exhibited_at'][:10],
            'mediatype': 'episode',
            'season': item['metadata']['season'] if 'season' in item['metadata'] else None,
            'episode': item['metadata']['episode'] if 'episode' in item['metadata'] else None,
            'year': item['metadata']['year'] if 'year' in item['metadata'] else None,
            'originaltitle': item['metadata']['original_title'] if 'original_title' in item['metadata'] else None,
            'lastplayed': item['updated_at'][:19].replace('T', ' '),
            'playcount': '1'
        }

        if 'fully_watched' not in item or not item['fully_watched']:
            video.update({'milliseconds_watched': item['milliseconds_watched']})

        videos.append(video)

    return videos, None, 1


def get_continue_watching():
    videos = []

    limit = 15

    username = control.setting('globoplay_username')
    password = control.setting('globoplay_password')

    # authenticate
    credentials = auth.auth().authenticate(username, password)

    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_CONTINUEWATCHING_BYPROGRAM % limit, cookie=credentials, headers=headers)

    if not data or not 'data' in data:
        return [], None, 0

    for item in data['data']:
        video = {
            'id': item['resource_id'],
            'title': item['metadata']['title'],
            'tvshowtitle': item['metadata']['program']['title'],
            'plot': item['metadata']['description'],
            'duration': int(item['metadata']['duration'])/1000 if item['metadata']['duration'] else 0,
            'thumb': THUMB_URL % item['resource_id'],
            'fanart': THUMB_URL % item['resource_id'],
            'aired': item['metadata']['exhibited_at'][:10],
            'mediatype': 'episode',
            'season': item['metadata']['season'] if 'season' in item['metadata'] else None,
            'episode': item['metadata']['episode'] if 'episode' in item['metadata'] else None,
            'year': item['metadata']['year'] if 'year' in item['metadata'] else None,
            'originaltitle': item['metadata']['original_title'] if 'original_title' in item['metadata'] else None,
            'milliseconds_watched': item['milliseconds_watched'],
            'lastplayed': item['updated_at'][:19].replace('T', ' '),
            'playcount': '1'
        }

        videos.append(video)

    return videos, None, 1


def get_most_watched_videos():

    videos = []

    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_MOST_WATCHED_VIDEOS, headers=headers)

    if not data or not 'videos' in data:
        return [], None, 0

    for item in data['videos']:
        video = {
            'id': item['id'],
            'title': item['title'],
            'tvshowtitle': item['title'],
            'plot': item['description'],
            'duration': sum(int(x) * 60 ** i for i, x in
                                    enumerate(reversed(item['duration'].split(':')))) if item['duration'] else 0,
            'thumb': THUMB_URL % item['id'],
            'fanart': THUMB_URL % item['id'],
            'aired': item['exhibited'],
            'mediatype': 'episode',
            'genre': item['subset']
        }

        videos.append(video)

    return videos, None, 1


def get_globo_programs():
    headers = {'Accept-Encoding': 'gzip'}
    categories_json = client.request(GLOBOPLAY_CATEGORIAS, headers=headers)['categories']
    categories = [json['title'].capitalize() for json in categories_json]

    programs = [{'category': json['title'].capitalize(), 'programs': [{
                            'id': j['id'],
                            'name': j['name'],
                            'thumb': j['thumb'],
                            # 'fanart': j['thumb'],
                            'fanart': control.addonFanart(),
                            'clearlogo': GLOBO_LOGO,
                            'kind': 'movies' if j['type'] == 'filmes' else 'default',
                            'brplayprovider': 'globoplay'
                        } for j in json['programs']]} for json in categories_json]

    return (categories, programs)


def get_program_dates(program_id):

    headers = {'Accept-Encoding': 'gzip'}
    days = client.request(GLOBOPLAY_DAYS % int(program_id), headers=headers)

    days = days['days'] if days and 'days' in days else []

    return days


def get_globo_partial_episodes(program_id, page=1):

    videos = []
    headers = {'Accept-Encoding': 'gzip'}
    days = client.request(GLOBOPLAY_DAYS % int(program_id), headers=headers)['days']
    video_page_size = 100
    size_videos = 100
    page_num = 1

    while size_videos >= video_page_size:
        try:
            data = client.request(GLOBOPLAY_VIDEOS % (int(program_id), days[page-1], page_num, size_videos))
            size_videos = len(data['videos'])
            for item in data['videos']:
                video = {
                    'id': item['id'],
                    'title': item['title'],
                    'tvshowtitle': item['program']['title'],
                    'plot': item['description'],
                    'duration': sum(int(x) * 60 ** i for i, x in
                                    enumerate(reversed(item['duration'].split(':')))) if item['duration'] else 0,
                    'date': util.time_format(item['exhibited'], '%Y-%m-%d'),
                    'genre': item['subset'],
                    'thumb': THUMB_URL % item['id'],
                    'fanart': GLOBO_FANART,
                    'mediatype': 'episode'
                }
                videos.append(video)
            page_num += 1
        except:
            break
    page = (page+1 if page < len(days) else None)

    return videos, page, len(days), days if page < len(days) else None


def get_globo_episodes(program_id, page=1):

    videos = []
    video_page_size = 300
    full_calendar_threshold = 15

    days = get_program_dates(program_id)

    page = int(page)

    if page < 1:
        page = 1

    if page > len(days):
        page = len(days)

    if len(days) - page + 1 < full_calendar_threshold:
        sevenDays = len(days)
    else:
        sevenDays = page+6 if len(days) > page+6 else len(days)

    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_VIDEOS_RANGE % (int(program_id), days[sevenDays-1], days[page-1], video_page_size), headers=headers)

    exerpts = []

    for item in data['videos']:

        video = {
            'id': item['id'],
            'title': item['title'],
            'tvshowtitle': item['program']['title'],
            'plot': item['description'],
            'duration': sum(int(x) * 60 ** i for i, x in
                            enumerate(reversed(item['duration'].split(':')))) if item['duration'] else 0,
            'date': util.time_format(item['exhibited'], '%Y-%m-%d'),
            'genre': item['subset'],
            'thumb': THUMB_URL % item['id'],
            'fanart': GLOBO_FANART,
            'mediatype': 'episode'
        }

        if not item["full_episode"]:
            exerpts.append(video)
            continue

        videos.append(video)

    if len(videos) == 0:
        videos = exerpts

    page = sevenDays+1 if sevenDays+1 < len(days) else None

    return videos, page, len(days), days if sevenDays+1 < len(days) else None


def get_globo_episodes_by_date(program_id, date):

    videos = []
    video_page_size = 300
    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_VIDEOS_RANGE % (int(program_id), date, date, video_page_size), headers=headers)

    for item in data['videos']:
        video = {
            'id': item['id'],
            'title': item['title'],
            'tvshowtitle': item['program']['title'],
            'plot': item['description'],
            'duration': sum(int(x) * 60 ** i for i, x in
                            enumerate(reversed(item['duration'].split(':')))) if item['duration'] else 0,
            'date': util.time_format(item['exhibited'], '%Y-%m-%d'),
            'genre': item['subset'],
            'thumb': THUMB_URL % item['id'],
            'fanart': GLOBO_FANART,
            'mediatype': 'episode'
        }

        videos.append(video)

    return videos


def search(term, page=1):
    try:
        page = int(page)
    except:
        page = 1

    videos = []
    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_SEARCH % (page, term), headers=headers)

    if not data:
        return [], None, 0

    total = data['total']
    next_page = page + 1 if data['has_next'] else None

    for item in data['videos']:
        video = {
            'id': item['id'],
            'label': 'Globo - ' + item['title'],
            'title': item['title'],
            'plot': item['description'],
            'duration': sum(int(x) * 60 ** i for i, x in
                            enumerate(reversed(item['duration'].split(':')))) if item['duration'] else 0,
            'thumb': THUMB_URL % item['id'],
            'fanart': GLOBO_FANART,
            'mediatype': 'episode',
            'brplayprovider': 'globoplay'
        }

        videos.append(video)

    return videos, next_page, total