# -*- coding: utf-8 -*-

import auth
import urllib
import resources.lib.modules.util as util
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import workers

GLOBO_LOGO = 'http://s3.glbimg.com/v1/AUTH_180b9dd048d9434295d27c4b6dadc248/media_kit/42/f3/a1511ca14eeeca2e054c45b56e07.png'
GLOBO_FANART = 'https://s02.video.glbimg.com/x720/4452349.jpg'

GLOBOPLAY_URL = 'https://api.globoplay.com.br'
GLOBOPLAY_APIKEY = '4c3f033123840f740508ec49e89e5142'  # '35978230038e762dd8e21281776ab3c9'
GLOBOPLAY_CATEGORIES = GLOBOPLAY_URL + '/v3/categories/?api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_DAYS = GLOBOPLAY_URL + '/v1/programs/%d/videos/days?api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_VIDEOS = GLOBOPLAY_URL + '/v1/programs/%d/videos?day=%s&order=asc&page=%d&per_page=%s&api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_VIDEOS_RANGE = GLOBOPLAY_URL + '/v1/programs/%d/videos?start=%s&end=%s&order=%s&per_page=%s&api_key=' + GLOBOPLAY_APIKEY

GLOBOPLAY_HIGHLIGHTS = GLOBOPLAY_URL + '/v2/highlights?api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_FAVORITES = 'http://api.user.video.globo.com/favorites?page=%s&per_page=%s'
GLOBOPLAY_WATCHHISTORY_BYPROGRAM = 'https://api.user.video.globo.com/watch_history/?preload_metadata=true&per_page=%s'
GLOBOPLAY_CONTINUEWATCHING_BYPROGRAM = 'https://api.user.video.globo.com/watch_history/?preload_metadata=true&fully_watched=false&per_page=%s'
GLOBOPLAY_MOST_WATCHED_VIDEOS = GLOBOPLAY_URL + '/v1/trilhos/mais-vistos?api_key=' + GLOBOPLAY_APIKEY

GLOBOPLAY_SEARCH = GLOBOPLAY_URL + '/v1/search?page=%s&q=%s&api_key=' + GLOBOPLAY_APIKEY

GLOBOPLAY_STATES = GLOBOPLAY_URL + '/v1/states?api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_REGIONS = GLOBOPLAY_URL + '/v1/regions/search?&query=%s&api_key=' + GLOBOPLAY_APIKEY
GLOBOPLAY_PROGRAMS_BY_REGION = GLOBOPLAY_URL + '/v1/categories/region/%s?api_key=' + GLOBOPLAY_APIKEY

GLOBOPLAY_PROGRAM_INFO = GLOBOPLAY_URL + '/v1/programs/%s/info?api_key=' + GLOBOPLAY_APIKEY

GLOBOPLAY_CONFIGURATION = GLOBOPLAY_URL + '/v1/configurations?api_key=' + GLOBOPLAY_APIKEY

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
            'adult': False
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
    categories_json = client.request(GLOBOPLAY_CATEGORIES, headers=headers)['categories']
    categories = [json['title'].capitalize() for json in categories_json]

    programs = [{'category': json['title'].capitalize(), 'programs': [{
                            'id': j['id'],
                            'name': j['title'],
                            'poster': j['assets']['poster_web'] if control.is_4k_images_enabled and 'poster_web' in j['assets'] else j['assets']['poster_mobile'] if 'poster_mobile' in j['assets'] else j['assets']['poster_tv'] if 'poster_tv' in j['assets'] else None,
                            'fanart': j['assets']['tvos_background_4k'] if control.is_4k_images_enabled and 'tvos_background_4k' in j['assets'] else j['assets']['background_tv'],
                            'clearlogo': GLOBO_LOGO,
                            'kind': 'movies' if j['type'] == 'filmes' else (j['type'] or 'default'),
                            'plot': j['description'] if 'description' in j else '',
                            'brplayprovider': 'globoplay'
                        } for j in json['programs']], 'subcategories': [{'category': j['title'].capitalize(), 'programs': [{
                            'id': p['id'],
                            'name': p['title'],
                            'poster': p['assets']['poster_web'] if control.is_4k_images_enabled and 'poster_web' in p['assets'] else p['assets']['poster_mobile'] if 'poster_mobile' in p['assets'] else p['assets']['poster_tv'] if 'poster_tv' in p['assets'] else None,
                            'fanart': p['assets']['tvos_background_4k'] if control.is_4k_images_enabled and 'tvos_background_4k' in p['assets'] else p['assets']['background_tv'],
                            'clearlogo': GLOBO_LOGO,
                            'kind': 'movies' if p['type'] == 'filmes' else (p['type'] or 'default'),
                            'plot': p['description'] if 'description' in j else '',
                            'brplayprovider': 'globoplay'
                        } for p in j['programs']]} for j in json['subcategories']]} for json in categories_json]

    return (categories, programs)


def get_program_dates(program_id):

    headers = {'Accept-Encoding': 'gzip'}
    days = client.request(GLOBOPLAY_DAYS % int(program_id), headers=headers)

    days_result = days['days'] if days and 'days' in days else []

    return days_result, days['position'] == 'last' if days and 'position' in days else True


def get_globo_partial_episodes(program_id, page=1, bingewatch=False):

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


def get_globo_episodes(program_id, page=1, bingewatch=False):

    videos = []
    video_page_size = 300
    full_calendar_threshold = 15

    days, last = get_program_dates(program_id)

    if not days or len(days) == 0:
        return videos, page, len(days), None

    page = int(page)

    if page < 1:
        page = 1

    if page > len(days):
        page = len(days)

    if len(days) - page + 1 < full_calendar_threshold:
        sevenDays = len(days)
    else:
        sevenDays = page + 6 if len(days) > page + 6 else len(days)

    if not last:
        days.reverse()
        order = 'asc'
        firstday = days[page - 1]
        lastday = days[sevenDays - 1]
    else:
        order = 'desc'
        firstday = days[sevenDays-1]
        lastday = days[page-1]

    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_VIDEOS_RANGE % (int(program_id), firstday, lastday, order, video_page_size), headers=headers)

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
            'mediatype': 'episode',
            'bingewatch': not last  # bingewatch
        }

        if not item["full_episode"]:
            exerpts.append(video)
            continue

        videos.append(video)

    if len(videos) == 0:
        videos = exerpts

    page = sevenDays+1 if sevenDays+1 < len(days) else None

    return videos, page, len(days), days if sevenDays+1 < len(days) else None


def get_globo_episodes_by_date(program_id, date, bingewatch=False):

    videos = []
    video_page_size = 300

    order = 'asc' if bingewatch else 'desc'

    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_VIDEOS_RANGE % (int(program_id), date, date, order, video_page_size), headers=headers)

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


def get_states():

    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_STATES, headers=headers)

    if not data or not 'states' in data:
        return []

    return data['states']


def get_regions(state):

    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_REGIONS % urllib.quote_plus(state), headers=headers)

    if not data or not 'regions' in data:
        return []

    # {
    #     "affiliate_code": "RES",
    #     "affiliate_name": "TV Rio Sul",
    #     "region_group_name": "Sul e Costa Verde",
    #     "state_acronym": "RJ",
    #     "state_name": "Rio de Janeiro"
    # }

    return data['regions']


def get_programs_by_region(region):

    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOPLAY_PROGRAMS_BY_REGION % region, headers=headers)

    if not data or not 'categories' in data:
        return []

    programs = []

    for item in data['categories']:
        for program in item['programs']:
            assets = program['assets']
            programs.append({
                'id': program['id'],
                'title': program['title'],
                'plot': program['description'],
                'poster': assets['poster_web'] if control.is_4k_images_enabled and 'poster_web' in assets else assets['poster_mobile'] if 'poster_mobile' in assets else assets['poster_tv'] if 'poster_tv' in assets else None,
                'fanart': assets['tvos_background_4k'] if control.is_4k_images_enabled and 'tvos_background_4k' in assets else assets['background_tv'],
                'brplayprovider': 'globoplay'
            })

    return programs


def get_4k():

    headers = {'Accept-Encoding': 'gzip'}
    config = client.request(GLOBOPLAY_CONFIGURATION, headers=headers)

    if not config or 'features' not in config or 'videos4k' not in config['features']:
        return []

    video_ids = config['features']['videos4k']

    if not video_ids or len(video_ids) == 0:
        return []

    threads = []
    programs = []

    for id in video_ids:
        threads.append(workers.Thread(__add_search_results, __get_program_info, programs, id))

    [i.start() for i in threads]
    [i.join() for i in threads]

    return programs


def __add_search_results(fn, list, *args):
    result = fn(*args)
    list.append(result)


def __get_program_info(id):
    headers = {'Accept-Encoding': 'gzip'}
    program = client.request(GLOBOPLAY_PROGRAM_INFO % id, headers=headers)

    assets = program['assets']
    return {
                'id': program['id'],
                'title': program['title'],
                'plot': program['description'],
                'poster': assets['poster_web'] if control.is_4k_images_enabled and 'poster_web' in assets else assets['poster_mobile'] if 'poster_mobile' in assets else assets['poster_tv'] if 'poster_tv' in assets else None,
                'fanart': assets['tvos_background_4k'] if control.is_4k_images_enabled and 'tvos_background_4k' in assets else assets['background_tv'],
                'brplayprovider': 'globoplay'
            }