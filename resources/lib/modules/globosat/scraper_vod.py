# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules.globosat import auth_helper
import urllib
import requests

GLOBOSAT_API_AUTHORIZATION = 'token b4b4fb9581bcc0352173c23d81a26518455cc521'
GLOBOSAT_SEARCH = 'https://globosatplay.globo.com/busca/pagina/%s.json?q=%s'
GLOBOSAT_FEATURED = 'https://api.vod.globosat.tv/globosatplay/featured.json'
GLOBOSAT_TRACKS = 'https://api.vod.globosat.tv/globosatplay/tracks.json'
GLOBOSAT_TRACKS_ITEM = 'https://api.vod.globosat.tv/globosatplay/tracks/%s.json'

GLOBOSAT_BASE_FAVORITES = 'https://api.vod.globosat.tv/globosatplay/watch_favorite.json?token=%s'
GLOBOSAT_FAVORITES = GLOBOSAT_BASE_FAVORITES + '&page=%s&per_page=%s'
GLOBOSAT_DEL_FAVORITES = GLOBOSAT_BASE_FAVORITES + '&id=%s'

GLOBOSAT_BASE_WATCH_LATER = 'https://api.vod.globosat.tv/globosatplay/watch_later.json?token=%s'
GLOBOSAT_WATCH_LATER = GLOBOSAT_BASE_WATCH_LATER + '&page=%s&per_page=%s'
GLOBOSAT_DEL_WATCH_LATER = GLOBOSAT_BASE_WATCH_LATER + '&id=%s'

GLOBOSAT_WATCH_HISTORY = 'https://api.vod.globosat.tv/globosatplay/watch_history.json?token=%s&page=%s&per_page=%s'

artPath = control.artPath()


def get_authorized_channels():
    token = auth_helper.get_globosat_token()

    if not token:
        return []

    client_id = "85014160-e953-4ddb-bbce-c8271e4fde74"
    channels_url = "https://gsatmulti.globo.com/oauth/sso/login/?chave=%s&token=%s" % (client_id, token)

    channels = []

    pkgs_response = client.request(channels_url, headers={"Accept-Encoding": "gzip"})

    control.log("-- PACKAGES: %s" % repr(pkgs_response))

    pkgs = pkgs_response['pacotes']

    channel_ids = []
    for pkg in pkgs:
        for channel in pkg['canais']:
            if channel['slug'] == 'telecine-zone':
                continue

            elif channel['id_globo_videos'] not in channel_ids:
                channel_ids.append(channel['id_globo_videos'])
                channels.append({
                    "id": channel['id_globo_videos'],
                    # "channel_id": channel['id_globo_videos'],
                    "id_cms": channel['id_cms'],
                    "logo": channel['logo_fundo_claro'],
                    "name": channel['nome'],
                    "slug": channel['slug'],
                    "adult": channel['slug'] == 'sexyhot',
                    "vod": "vod" in channel['acls'],
                    "live": "live" in channel['acls']
                })

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


def search(term, page=1):
    try:
        page = int(page)
    except:
        page = 1

    videos = []
    headers = {'Accept-Encoding': 'gzip'}
    data = client.request(GLOBOSAT_SEARCH % (page, term), headers=headers)
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
            'fanart': item['program']['background_image_tv_cropped'] if 'program' in item and item['program'] else item['background_image'],
            'mediatype': 'episode',
            'brplayprovider': 'globosat',
            'milliseconds_watched': int(item['watched_seconds']) * 1000
        }

        videos.append(video)

    return videos
