# -*- coding: utf-8 -*-

# from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules.globosat import auth_helper
import urllib
import requests
import os

GLOBOSAT_API_AUTHORIZATION = 'token b4b4fb9581bcc0352173c23d81a26518455cc521'
GLOBOSAT_SEARCH = 'https://globosatplay.globo.com/busca/pagina/%s.json?q=%s'
GLOBOSAT_FEATURED = 'https://api.vod.globosat.tv/globosatplay/featured.json'
GLOBOSAT_TRACKS = 'https://api.vod.globosat.tv/globosatplay/tracks.json'
GLOBOSAT_TRACKS_ITEM = 'https://api.vod.globosat.tv/globosatplay/tracks/%s.json'

GLOBOSAT_CHANNELS = 'https://api-vod.globosat.tv/globosatplay/channels.json'
GLOBOSAT_CARDS = 'https://api-vod.globosat.tv/globosatplay/cards.json?&channel_id_globo_videos=%s&page=%s'
GLOBOSAT_PROGRAMS = 'https://api-vod.globosat.tv/globosatplay/programs.json?&id_globo_videos=%s&page=%s'
GLOBOSAT_EPISODES_SEASON = 'https://api-vod.globosat.tv/globosatplay/episodes.json?program_id=%s&season_id=%s&page=%s'
GLOBOSAT_EPISODES = 'https://api-vod.globosat.tv/globosatplay/episodes.json?&program_id=%s&page=%s'

GLOBOSAT_BASE_FAVORITES = 'https://api.vod.globosat.tv/globosatplay/watch_favorite.json?token=%s'
GLOBOSAT_FAVORITES = GLOBOSAT_BASE_FAVORITES + '&page=%s&per_page=%s'
GLOBOSAT_DEL_FAVORITES = GLOBOSAT_BASE_FAVORITES + '&id=%s'

GLOBOSAT_BASE_WATCH_LATER = 'https://api.vod.globosat.tv/globosatplay/watch_later.json?token=%s'
GLOBOSAT_WATCH_LATER = GLOBOSAT_BASE_WATCH_LATER + '&page=%s&per_page=%s'
GLOBOSAT_DEL_WATCH_LATER = GLOBOSAT_BASE_WATCH_LATER + '&id=%s'

GLOBOSAT_WATCH_HISTORY = 'https://api.vod.globosat.tv/globosatplay/watch_history.json?token=%s&page=%s&per_page=%s'

artPath = control.artPath()
PREMIERE_LOGO = os.path.join(artPath, 'logo_premiere.png')
PREMIERE_FANART = os.path.join(artPath, 'fanart_premiere_720.jpg')

PREMIERE_MATCHES_JSON = 'https://api-soccer.globo.com/v1/premiere/matches?order=asc&page='


CHANNEL_MAP = {
    1995: 936,
    2065: 692,
    2006: 692
}


def get_authorized_channels(retry=1):
    token = auth_helper.get_globosat_token()

    if not token:
        return []

    channels_url = "https://gsatmulti.globo.com/apis/user/%s/" % token

    channels = []

    pkgs_response = client.request(channels_url, headers={"Accept-Encoding": "gzip"})

    if not pkgs_response or 'provider_accounts' not in pkgs_response:
        if retry > 0:
            retry = retry - 1
            control.clear_globosat_credentials()
            return get_authorized_channels(retry)
        else:
            return channels

    # control.log("-- PACKAGES: %s" % repr(pkgs_response))

    pkgs = pkgs_response['provider_accounts']

    channel_ids = []
    for pkg in pkgs:
        for channel in pkg['channels']:
            if channel['id_globo_videos'] not in channel_ids:
                channel_ids.append(channel['id_globo_videos'])
                channels.append({
                    "id": channel['id_globo_videos'],
                    "service_id": channel['service_id'],
                    "name": channel['name'],
                    "adult": channel['id_globo_videos'] in [2065,2006],
                    'slug': '',
                    'logo': '',
                    'color': '',
                })

    broadcasts_url = 'https://products-jarvis.globo.com/graphql?query=query%20getChannelsList%28%24page%3A%20Int%2C%20%24perPage%3A%20Int%29%20%7B%0A%20%20broadcastChannels%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20page%0A%20%20%20%20perPage%0A%20%20%20%20hasNextPage%0A%20%20%20%20nextPage%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20color%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&operationName=getChannelsList&variables=%7B%22page%22%3A1%2C%22perPage%22%3A200%7D'
    query_response = client.request(broadcasts_url, headers={
        "Accept-Encoding": "gzip",
        "x-tenant-id": "globosat-play",
        'x-platform-id': 'web',
        'x-device-id': 'desktop',
        'x-client-version': '0.4.3',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    })

    resources = []
    resources.extend(query_response['data']['broadcastChannels']['resources'])

    query_response = client.request(broadcasts_url, headers={
        "Accept-Encoding": "gzip",
        "x-tenant-id": "sexy-hot",
        'x-platform-id': 'web',
        'x-device-id': 'desktop',
        'x-client-version': '0.4.3',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    })

    resources.extend(query_response['data']['broadcastChannels']['resources'])

    for broadcast in resources:
        channel = next((channel for channel in channels if int(broadcast['id']) == int(channel['id']) and int(channel['id']) > 0 or (CHANNEL_MAP.get(int(channel['id']), -1) == int(broadcast['id']))), None)
        if channel:
            channel.update({
                'slug': broadcast['slug'],
                'logo': broadcast['logo'],
                'color': broadcast['color'],
                "name": broadcast['name']
            })

    # result = list(filter(lambda x: 'slug' in x, channels))
    return channels


def get_channel_programs(channel_id):
    base_url = 'https://api.vod.globosat.tv/globosatplay/cards.json?channel_id=%s&page=%s'
    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}

    page = 1
    url = base_url % (channel_id, page)
    result = client.request(url, headers=headers)

    next = result['next'] if 'next' in result else None
    programs_result = result['results'] or []

    while next:
        page = page + 1
        url = base_url % (channel_id, page)
        result = client.request(url, headers=headers)
        next = result['next'] if 'next' in result else None
        programs_result = programs_result + result['results']

    programs = []

    for program in programs_result:
        programs.append({
            'id': program['id_globo_videos'],
            'title': program['title'],
            'name': program['title'],
            'fanart': program['background_image_tv_cropped'],
            'poster': program['image'],
            'plot': program['description'],
            'kind': program['kind'] if 'kind' in program else None
        })

    return programs


def get_channel_cards(channel_id_globo_videos):

    if str(channel_id_globo_videos) == str(1995):
        return get_premiere_cards()

    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}

    page = 1
    url = GLOBOSAT_CARDS % (channel_id_globo_videos, page)
    result = client.request(url, headers=headers)

    next = result['next'] if 'next' in result else None
    programs_result = result['results'] or []

    while next:
        page = page + 1
        url = GLOBOSAT_CARDS % (channel_id_globo_videos, page)
        result = client.request(url, headers=headers)
        next = result['next'] if 'next' in result else None
        programs_result = programs_result + result['results']

    programs = []

    for program in programs_result:
        programs.append({
            'id': program['id'],
            'id_globo_videos': program['id_globo_videos'],
            'title': program['title'],
            'name': program['title'],
            'fanart': program['background_image_tv_cropped'],
            'poster': program['image'],
            'plot': program['description'],
            'kind': program['kind'] if 'kind' in program else None
        })

    return programs


def get_premiere_cards():
    return [{
            'id': 1995,
            'id_globo_videos': None,
            'title': u'\u2063Veja a Programação',
            'name': u'[B]\u2063Próximos Jogos[/B]',
            'fanart': PREMIERE_FANART,
            'poster': None,
            'plot': 'Veja os jogos programados',
            'kind': None,
            'brplayprovider': 'premierefc',
            'studio': 'Premiere FC',
            'tvshowtitle': u'Próximos Jogos',
            'sorttitle': 'Premiere FC',
            'clearlogo': PREMIERE_LOGO,
            'thumb': PREMIERE_FANART,
            'playable': 'false',
            'channel_id': 1995,
            'duration': None,
            'isFolder': 'true',
        }]


def get_card_seasons(id_globo_videos):
    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}

    page = 1
    url = GLOBOSAT_PROGRAMS % (id_globo_videos, page)
    result = client.request(url, headers=headers)

    next = result['next'] if 'next' in result else None
    programs_response = result['results'] or []

    while next:
        page = page + 1
        url = GLOBOSAT_PROGRAMS % (id_globo_videos, page)
        result = client.request(url, headers=headers)
        next = result['next'] if 'next' in result else None
        programs_response = programs_response + result['results']

    card_data = programs_response[0] if programs_response and len(programs_response) > 0 else None
    seasons_response = card_data['seasons'] if card_data and 'seasons' in card_data else []

    if not card_data:
        return {
            'id': None,
            'title': None,
            'name': None,
            'fanart': None,
            'poster': None,
            'plot': None,
            'kind': None
        }

    seasons = []

    card = {
        'id': card_data['id'],
        'id_globo_videos': card_data['id_globo_videos'],
        'title': card_data['title'],
        'name': card_data['title'],
        'fanart': card_data['background_image_tv_cropped'],
        'poster': card_data['poster_image'],
        'logo': card_data['logo_image'],
        'plot': card_data['description'],
        'kind': card_data['kind'] if 'kind' in seasons else None,
        'season': len(seasons_response),
    }

    for season in seasons_response:
        seasons.append({
            'id': season['id'],
            'title': season['title'],
            'description': season['description'],
            'episodes_number': season['episodes_number'],
            'number': season['number'],
            'year': season['year']
        })

    card['seasons'] = seasons

    return card


def get_card_episodes(program_id, season_id=None):
    headers = {'Authorization': GLOBOSAT_API_AUTHORIZATION, 'Accept-Encoding': 'gzip'}

    page = 1
    url = GLOBOSAT_EPISODES_SEASON % (program_id, season_id, page) if season_id else GLOBOSAT_EPISODES % (program_id, page)
    result = client.request(url, headers=headers)

    next = result['next'] if 'next' in result else None
    programs_result = result['results'] or []

    while next:
        page = page + 1
        url = GLOBOSAT_EPISODES_SEASON % (program_id, season_id, page) if season_id else GLOBOSAT_EPISODES % (program_id, page)
        result = client.request(url, headers=headers)
        next = result['next'] if 'next' in result else None
        programs_result = programs_result + result['results']

    episodes = []

    for episode in programs_result:

        if episode['number'] and 'season' in episode and episode['season'] and 'number' in episode['season']:
            title = 'S%sE%s - %s' % (episode['season']['number'], episode['number'], episode['title'])
        else:
            title = episode['title']

        if 'program' in episode and episode['program']:
            tvshowtitle = episode['program']['title']
        else:
            tvshowtitle = title

        data = {
            'id': episode['id_globo_videos'],
            'id_globo_videos': episode['id_globo_videos'],
            'title': title,
            'name': episode['title'],
            'fanart': episode['background_image_tv_cropped'],
            'thumb': episode['thumb_image'],
            'poster': episode['image'],
            'plot': episode['description'],
            'plotoutline': episode['description'],
            'kind': episode['kind'] if 'kind' in episode else None,
            'duration': episode['duration_in_milliseconds'] / 1000.0,
            'brplayprovider': 'globosat',
            'tvshowtitle': tvshowtitle,
            # 'episode': episode['number'],
            # 'season': episode['season']['number'] if 'season' in episode and episode['season'] and 'number' in episode['season'] else None,
            'country': episode['country'],
            'genre': episode['categories'],
            'tag': episode['tags'],
            'mpaa': episode['content_rating'],
            'mediatype': 'episode'
        }

        if 'director' in episode and episode['director'] and len(episode['director']) > 0:
            data['director'] = [director['name'] for director in episode['director']]

        if 'cast' in episode and episode['cast'] and len(episode['cast']) > 0:
            data['cast'] = [director['name'] for director in episode['cast']]

        episodes.append(data)

    return episodes


def search(term, page=1):
    try:
        page = int(page)
    except:
        page = 1

    videos = []
    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOSAT_SEARCH % (page, urllib.quote_plus(term)), headers=headers)
    total = data['total']
    next_page = page + 1 if len(data['videos']) < total else None

    for item in data['videos']:
        video = {
            'id': item['id'],
            'label': item['canal'] + ' - ' + item['programa'] + ' - ' + item['titulo'],
            'title': item['titulo'],
            'tvshowtitle': item['programa'],
            'studio': item['canal'],
            'plot': item['descricao'],
            'duration': sum(int(x) * 60 ** i for i, x in
                            enumerate(reversed(item['duracao'].split(':')))) if item['duracao'] else 0,
            'thumb': item['thumb_large'],
            'fanart': item['thumb_large'],
            'mediatype': 'episode',
            'brplayprovider': 'globosat'
        }

        videos.append(video)

    return videos, next_page, total


def get_featured(channel_id=None):
    headers = {
        'Accept-Encoding': 'gzip',
        'Authorization': GLOBOSAT_API_AUTHORIZATION
    }
    channel_filter = '?channel_id=%s' % channel_id if channel_id else ''
    featured_list = client.request(GLOBOSAT_FEATURED + channel_filter, headers=headers)

    results = featured_list['results']

    while featured_list['next'] is not None:
        featured_list = client.request(featured_list['next'], headers=headers)
        results += featured_list['results']

    videos = []

    for item in results:

        media = item['media']

        if media:
            video = {
                'id': item['id_globo_videos'],
                'label': media['channel']['title'] + ' - ' + item['title'] + ' - ' + media['title'],
                'title': media['title'],
                'tvshowtitle': item['title'],
                'studio': media['channel']['title'],
                'plot': media['description'],
                'tagline': item['subtitle'],
                'duration': float(media['duration_in_milliseconds']) / 1000.0,
                'logo': media['program']['logo_image'] if 'program' in media and media['program'] else item['channel'][
                    'color_logo'],
                'clearlogo': media['program']['logo_image'] if 'program' in media and media['program'] else
                item['channel']['color_logo'],
                'poster': media['program']['poster_image'] if 'program' in media and media['program'] else media[
                    'card_image'],
                'thumb': media['thumb_image'],
                'fanart': media['background_image_tv_cropped'] if 'program' in media and media['program'] else media[
                    'background_image'],
                'mediatype': 'episode',
                'brplayprovider': 'globosat'
            }
        else:
            video = {
                'id': item['id_globo_videos'],
                'label': item['channel']['title'] + ' - ' + item['title'],
                'title': item['title'],
                'tvshowtitle': item['title'],
                'studio': item['channel']['title'],
                'plot': item['subtitle'],
                # 'tagline': item['subtitle'],
                # 'duration': float(media['duration_in_milliseconds']) / 1000.0,
                # 'logo': media['program']['logo_image'],
                # 'clearlogo': media['program']['logo_image'],
                # 'poster': media['program']['poster_image'],
                'thumb': item['background_image'],
                'fanart': item['background_image'],
                'mediatype': 'episode',
                'brplayprovider': 'globosat'
            }

        videos.append(video)

    return videos


def get_tracks(channel_id=None):
    headers = {
        'Accept-Encoding': 'gzip',
        'Authorization': GLOBOSAT_API_AUTHORIZATION
    }
    channel_filter = '?channel_id=%s' % channel_id if channel_id else ''
    tracks_response = client.request(GLOBOSAT_TRACKS + channel_filter, headers=headers)

    results = tracks_response['results']

    tracks = []

    for item in results:
        video = {
            'id': item['id'],
            'label': item['title'],
            'title': item['title'],
            'kind': item['kind']
        }

        tracks.append(video)

    return tracks


def get_track_list(id):
    videos = []

    headers = {
        'Accept-Encoding': 'gzip',
        'Authorization': GLOBOSAT_API_AUTHORIZATION
    }
    track_list = client.request(GLOBOSAT_TRACKS_ITEM % id, headers=headers)

    results = track_list['results'] if track_list and 'results' in track_list else None

    if results is None:
        return videos

    while (track_list['next'] if track_list and 'next' in track_list else None) is not None:
        track_list = client.request(track_list['next'], headers=headers)
        results += track_list['results']

    for item in results:
        media = item['media']
        if media:
            video = {
                'id': item['id_globo_videos'],
                'id_globo_videos': item['id_globo_videos'],
                'label': media['channel']['title'] + ' - ' + media['title'],
                'title': media['title'],
                'tvshowtitle': media['program']['title'] if 'program' in media and media['program'] else None,
                'studio': media['channel']['title'],
                'plot': media['description'],
                'tagline': media['subtitle'],
                'duration': float(media['duration_in_milliseconds']) / 1000.0,
                'logo': media['program']['logo_image'] if 'program' in media and media['program'] else media['channel'][
                    'color_logo'],
                'clearlogo': media['program']['logo_image'] if 'program' in media and media['program'] else
                media['channel']['color_logo'],
                'poster': media['program']['poster_image'] if 'program' in media and media['program'] else media[
                    'card_image'],
                'thumb': media['thumb_image'],
                'fanart': media['background_image_tv_cropped'],
                'mediatype': 'episode',
                'brplayprovider': 'globosat'
            }
        else:
            program = item['program']
            video = {
                'id': item['id_globo_videos'],
                'id_globo_videos': item['id_globo_videos'],
                'label': program['title'],
                'title': program['title'],
                'tvshowtitle': program['title'],
                'studio': program['channel']['title'],
                'plot': program['description'],
                'tagline': None,
                'logo': program['logo_image'],
                'clearlogo': program['logo_image'],
                'poster': program['poster_image'],
                'thumb': None,
                'fanart': program['background_image_tv_cropped'],
                'mediatype': 'tvshow',
                'isplayable': False,
                'brplayprovider': 'globosat'
            }
        videos.append(video)

    return videos


def get_favorites(page=1):
    headers = {
        'Accept-Encoding': 'gzip',
        'Authorization': GLOBOSAT_API_AUTHORIZATION,
        'Version': 2
    }

    token = auth_helper.get_globosat_token()

    favorites_list = client.request(GLOBOSAT_FAVORITES % (token, page, 50), headers=headers)

    results = favorites_list['data']

    while favorites_list['next'] is not None:
        favorites_list = client.request(favorites_list['next'], headers=headers)
        results += favorites_list['data']

    videos = []

    for item in results:

        video = {
            'id': item['id_globo_videos'],
            'label': item['channel']['title'] + (' - ' + item['program']['title'] if 'program' in item and item['program'] else '') + ' - ' + item['title'],
            'title': item['title'],
            'tvshowtitle': item['program']['title'] if 'program' in item and item['program'] else item['title'],
            'studio': item['channel']['title'],
            'plot': item['description'],
            'tagline': item['subtitle'],
            'duration': float(item['duration_in_milliseconds']) / 1000.0,
            'logo': item['program']['logo_image'] if 'program' in item and item['program'] else item['channel'][
                'color_logo'],
            'clearlogo': item['program']['logo_image'] if 'program' in item and item['program'] else
            item['channel']['color_logo'],
            'poster': item['program']['poster_image'] if 'program' in item and item['program'] else item[
                'card_image'],
            'thumb': item['thumb_image'],
            'fanart': item['program']['background_image_tv_cropped'] if 'program' in item and item['program'] else item[
                'background_image_tv_cropped'],
            'mediatype': 'episode',
            'brplayprovider': 'globosat'
        }

        videos.append(video)

    return videos


def add_favorites(video_id):
    post_data = {
        'id': video_id
    }

    token = auth_helper.get_globosat_token()

    url = GLOBOSAT_BASE_FAVORITES % token
    headers = {
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "version": "2",
        "Authorization": GLOBOSAT_API_AUTHORIZATION
    }

    post_data = urllib.urlencode(post_data)

    client.request(url, headers=headers, post=post_data)


def del_favorites(video_id):

    token = auth_helper.get_globosat_token()

    url = GLOBOSAT_DEL_FAVORITES % (token, video_id)
    headers = {
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "version": "2",
        "Authorization": GLOBOSAT_API_AUTHORIZATION
    }

    requests.delete(url=url, headers=headers)


def get_watch_later(page=1):
    headers = {
        'Accept-Encoding': 'gzip',
        'Authorization': GLOBOSAT_API_AUTHORIZATION,
        'Version': 2
    }

    token = auth_helper.get_globosat_token()

    watch_later_list = client.request(GLOBOSAT_WATCH_LATER % (token, page, 50), headers=headers)

    results = watch_later_list['data']

    while watch_later_list['next'] is not None:
        watch_later_list = client.request(GLOBOSAT_WATCH_LATER % (token, watch_later_list['next'], 50), headers=headers)
        results += watch_later_list['data']

    videos = []

    for item in results:

        video = {
            'id': item['id_globo_videos'],
            'label': item['channel']['title'] + (' - ' + item['program']['title'] if 'program' in item and item['program'] else '') + ' - ' + item['title'],
            'title': item['title'],
            'tvshowtitle': item['program']['title'] if 'program' in item and item['program'] else item['title'],
            'studio': item['channel']['title'],
            'plot': item['description'],
            'tagline': None,
            'duration': float(item['duration_in_milliseconds']) / 1000.0,
            'logo': item['program']['logo_image'] if 'program' in item and item['program'] else item['channel']['color_logo'],
            'clearlogo': item['program']['logo_image'] if 'program' in item and item['program'] else item['channel']['color_logo'],
            'poster': item['program']['poster_image'] if 'program' in item and item['program'] else item['card_image'],
            'thumb': item['thumb_image'],
            'fanart': item['program']['background_image_tv_cropped'] if 'program' in item and item['program'] else item['background_image_tv_cropped'],
            'mediatype': 'episode',
            'brplayprovider': 'globosat'
        }

        videos.append(video)

    return videos


def add_watch_later(video_id):
    post_data = {
        'id': video_id
    }

    token = auth_helper.get_globosat_token()

    url = GLOBOSAT_BASE_WATCH_LATER % token
    headers = {
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "version": "2",
        "Authorization": GLOBOSAT_API_AUTHORIZATION
    }

    post_data = urllib.urlencode(post_data)

    client.request(url, headers=headers, post=post_data)


def del_watch_later(video_id):

    token = auth_helper.get_globosat_token()

    url = GLOBOSAT_DEL_WATCH_LATER % (token, video_id)
    headers = {
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "version": "2",
        "Authorization": GLOBOSAT_API_AUTHORIZATION
    }

    requests.delete(url=url, headers=headers)


def get_watch_history(page=1):

    page_size = 50

    headers = {
        'Accept-Encoding': 'gzip',
        'Authorization': GLOBOSAT_API_AUTHORIZATION,
        'Version': 2
    }

    token = auth_helper.get_globosat_token()

    watch_later_list = client.request(GLOBOSAT_WATCH_HISTORY % (token, page, page_size), headers=headers)

    results = watch_later_list['data']

    while watch_later_list['next'] is not None:
        watch_later_list = client.request(GLOBOSAT_WATCH_HISTORY % (token, watch_later_list['next'], page_size), headers=headers)
        results += watch_later_list['data']

    videos = []

    results = sorted(results, key=lambda x: x['watched_date'], reverse=True)

    for item in results:
        channel_title = item['channel']['title'] or ''
        program_title = item['program']['title'] if 'program' in item and item['program'] else ''
        title = item['title'] or 'No Title'
        label = channel_title + (' - ' + program_title) + ' - ' + title
        video = {
            'id': item['id_globo_videos'],
            'label': label,
            'title': item['title'],
            'tvshowtitle': item['program']['title'] if 'program' in item and item['program'] else item['title'],
            'studio': channel_title,
            'plot': item['description'],
            'tagline': None,
            'duration': float(item['duration_in_milliseconds']) / 1000.0,
            'logo': item['program']['logo_image'] if 'program' in item and item['program'] else item['channel']['color_logo'],
            'clearlogo': item['program']['logo_image'] if 'program' in item and item['program'] else item['channel']['color_logo'],
            'poster': item['program']['poster_image'] if 'program' in item and item['program'] else item['card_image'],
            'thumb': item['thumb_image'],
            'fanart': item['program']['background_image_tv_cropped'] if 'program' in item and item['program'] else item['background_image'],
            'mediatype': 'episode',
            'brplayprovider': 'globosat',
            'milliseconds_watched': int(item['watched_seconds']) * 1000
        }

        videos.append(video)

    return videos
