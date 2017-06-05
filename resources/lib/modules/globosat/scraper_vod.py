# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import client
import auth

GLOBOSAT_API_URL = 'https://api.vod.globosat.tv/globosatplay'
GLOBOSAT_API_AUTHORIZATION = 'token b4b4fb9581bcc0352173c23d81a26518455cc521'
GLOBOSAT_API_CHANNELS = GLOBOSAT_API_URL + '/channels.json?page=%d'
GLOBOSAT_SEARCH = 'https://globosatplay.globo.com/busca/pagina/%s.json?q=%s'

artPath = control.artPath()

def get_authorized_channels():

    provider = control.setting('globosat_provider').lower().replace(' ', '_')
    username = control.setting('globosat_username')
    password = control.setting('globosat_password')

    authenticator = getattr(auth, provider)()
    token, sessionKey = authenticator.get_token(username, password)

    client_id = "85014160-e953-4ddb-bbce-c8271e4fde74"
    channels_url = "https://gsatmulti.globo.com/oauth/sso/login/?chave=%s&token=%s" % (client_id, token)

    channels = []

    pkgs = client.request(channels_url, headers={"Accept-Encoding": "gzip"})['pacotes']

    channel_ids = []
    for pkg in pkgs:
        for channel in pkg['canais']:
            if control.setting('show_adult') == 'false' and channel['slug'] == 'sexyhot':
                continue

            if channel['id_cms'] == 0 and channel['slug'] != 'combate' and channel['slug'] != 'sexyhot' or channel['slug'] == 'telecine-zone' :
                continue

            elif "vod" in channel['acls'] and channel['id_globo_videos'] not in channel_ids:
                channel_ids.append(channel['id_globo_videos'])
                channels.append({
                    "id": channel['id_globo_videos'],
                    # "channel_id": channel['id_globo_videos'],
                    "id_cms": channel['id_cms'],
                    "logo": channel['logo_fundo_claro'],
                    "name": channel['nome'],
                    "slug": channel['slug']
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