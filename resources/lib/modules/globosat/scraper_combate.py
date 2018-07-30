# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import workers
import re
import json

try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    OrderedDict = None

COMBATE_VIDEOS = 'https://globosatplay.globo.com/combate/videos/%s/%s.json'
COMBATE_EVENTS = 'https://globosatplay.globo.com/combate/%s/eventos/%s.json'
COMBATE_FIGHTERS_LIST = 'https://globosatplay.globo.com/combate/lutadores/?letra=%s'
COMBATE_FIGHTERS_DETAILS = 'https://globosatplay.globo.com/combate/lutadores/%s/videos/todos/%s.json'
COMBATE_LATEST_SLUG = 'ultimos'

artPath = control.artPath()

THUMB_URL = 'https://s04.video.glbimg.com/x720/%s.jpg'


def get_combate_categories():
    return [{
            'title': 'UFC',
            'slug': 'ufc',
        },
        {
            'title': 'Striking',
            'slug': 'striking'
        },
        {
            'title': 'Grappling',
            'slug': 'grappling'
        },
        {
            'title': 'Outros',
            'slug': 'outros'
        },
        {
            'title': 'Lutadores',
            'slug': 'lutadores'
        }
    ]


def get_latest_events(slug):
    headers = {'Accept-Encoding': 'gzip'}
    events = client.request(COMBATE_EVENTS % (slug, COMBATE_LATEST_SLUG), headers=headers)

    videos = []

    for event in events:
        title = event['titulo']
        if not title.__contains__(':'):
            title = title + ' - ' + event['lutador_principal'] + ' x ' + event['lutador_desafiante']
        first = True
        for video in event['videos']:
            videos.append({
                'title': title if first else event['titulo'],
                'id': video['id'],
                'thumb': THUMB_URL % video['id'],  # event['videos'][0]['thumb'],
                'fanart': THUMB_URL % video['id'],
                'plot': event['descricao']
            })
            first = False

    return videos


def get_featured():
    url = 'http://api-tracks.globosat.tv/v1/combate/'

    headers = {
        'Accept-Encoding': 'gzip',
        'Authorization': 'Token dfe2d9096105524042f9b98a86fb07543a125abb'
    }

    events = client.request(url, headers=headers)

    videos = []

    for event in events:
        videos.append({
            'title': event['titulo_video'],
            'id': event['recurso']['id'],
            'thumb': event['imagem_url_x720'],
            'fanart': event['imagem_url_x720'],
            'plot': event['descricao'],
            'duration': float(event['duracao_original']) / 1000.0
        })

    return videos


def get_previous_events():
    url = 'http://api.fights.globosat.tv/api/previous_events'

    headers = {
        'Accept-Encoding': 'gzip'
    }

    events = client.request(url, headers=headers)

    videos = []

    for event in events:
        videos.append({
            'title': event['nome'],
            'date': event['data'],
            'slug': event['slug'],
            'plot': 'Evento realizado em ' + event['data'],
            'thumb': event['cards']['principal']['lutas'][0]['video']['url_thumbnail'] if len(event['cards']['principal']['lutas']) > 0 else THUMB_URL % event['video_id'],
            'fanart': THUMB_URL % event['video_id'],
            'url': 'get_previous_events_videos',
            'order': '*'
        })

    return videos


def get_previous_events_videos(slug):
    url = 'http://api.fights.globosat.tv/api/previous_events'

    headers = {
        'Accept-Encoding': 'gzip'
    }

    events = client.request(url, headers=headers)

    videos = []

    event = next(e for e in events if e['slug'] == slug)

    if event:
        cards = event['cards'].keys()
        for card in cards:
            if card in event['cards'] and event['cards'][card] and 'lutas' in event['cards'][card] and event['cards'][card]['lutas']:
                for luta in event['cards'][card]['lutas']:
                    video = luta['video']
                    videos.append({
                        'title': video['titulo'],
                        'id': video['video_id'],
                        'thumb': video['url_thumbnail'],
                        'fanart': video['url_thumbnail'],
                        'plot': video['descricao'],
                        'duration': sum(int(x) * 60 ** i for i, x in
                                enumerate(reversed(video['duracao'].split(':')))) if video['duracao'] else 0
                    })

        return videos

    return None


def get_next_events_videos(slug):
    url = 'http://api.fights.globosat.tv/api/next_events'

    headers = {
        'Accept-Encoding': 'gzip'
    }

    events = client.request(url, headers=headers)

    videos = []

    event = next(e for e in events if e['slug'] == slug)

    if event:
        cards = event['cards'].keys()
        for card in cards:
            if card in event['cards'] and event['cards'][card] and 'lutas' in event['cards'][card] and event['cards'][card]['lutas']:
                for luta in event['cards'][card]['lutas']:
                    lutadores = luta['lutadores']
                    principal = lutadores['principal']
                    desafiante = lutadores['desafiante']
                    video = luta['video']
                    thumb = video['url_thumbnail'] if video and 'url_thumbnail' in video and video['url_thumbnail'] else principal['url_foto_cintura']
                    videos.append({
                        'title': event['nome'] + ' - ' + principal['nome'] + ' x ' + desafiante['nome'],
                        'id': video['video_id'] if video and 'video_id' in video else None,
                        'plot': 'Luta entre ' + principal['nome'] + ' x ' + desafiante['nome'] + u', válida pelo ' + event['nome'] + ', em ' + event['data'],
                        'thumb': thumb,
                        'fanart': thumb
                    })

        return videos

    return None


def get_next_events():
    url = 'http://api.fights.globosat.tv/api/next_events'

    headers = {
        'Accept-Encoding': 'gzip'
    }

    events = client.request(url, headers=headers)

    videos = []

    for event in events:
        videos.append({
            'title': event['nome'] + ' - ' + event['data'] + ' ' + event['hora'],
            'date': event['data'],
            'slug': event['slug'],
            'plot': 'Data do evento: ' + event['data'],
            'thumb': event['cards']['principal']['lutas'][0]['video']['url_thumbnail'] if len(event['cards']['principal']['lutas']) > 0 and event['cards']['principal']['lutas'][0]['video'] else THUMB_URL % event['video_id'],
            'fanart': THUMB_URL % event['video_id'],
            'url': 'get_next_events_videos',
            'order': '*'
        })

    return videos


def __append_result(fn, list, size_meter, *args):
        list_return = fn(*args)
        size_meter[0] = len(list_return) if list_return and size_meter[0] > 0 else 0
        if list_return and len(list_return) > 0:
            list += list_return


def get_ufc_submenu():

    return [{
        'title': u'Destaques',
        'slug': 'featured_ufc',
        'url': None,
        'order': '*'
    },{
        'title': u'Eventos Anteriores',
        'slug': 'previous_ufc',
        'url': None,
        'order': '*'
    },{
        'title': u'Próximos Eventos',
        'slug': 'next_ufc',
        'url': None,
        'order': '*'
    },{
        'title': u'Últimos',
        'slug': 'ultimos_ufc',
        'url': None,
        'order': '*'
    },{
        'title': u'Todos',
        'slug': 'todos_ufc',
        'url': None,
        'order': '*'
    }]


def open_ufc_submenu(slug):
    if slug == 'todos_ufc':
        return get_all_events('ufc')
    elif slug == 'featured_ufc':
        return get_featured()
    elif slug == 'previous_ufc':
        return get_previous_events()
    elif slug == 'next_ufc':
        return get_next_events()
    elif slug == 'ultimos_ufc':
        return get_latest_events('ufc')

    return []


def get_all_events(slug):

    preload_size = 20

    events = []

    end = 1
    size_meter = [1]

    while size_meter[0] > 0:
        start = end
        end = start + preload_size - 1
        threads = [workers.Thread(__append_result, get_events_by_page, events, size_meter, slug, i) for i in range(start, end)]
        [i.start() for i in threads]
        [i.join() for i in threads]

    return sorted(events, key=lambda k: k['order'], reverse=True)


def get_events_by_page(slug, page=1):
    headers = {'Accept-Encoding': 'gzip'}
    events = client.request(COMBATE_EVENTS % (slug, page), headers=headers)

    links = []

    if not events or len(events) == 0: return links

    for index, event in enumerate(events):
        links.append({
            'title': event['titulo'],
            'url': 'https://globosatplay.globo.com' + event['uri'],
            'order': "%04d_%06d" % (page,index)
        })

    return links


def get_fighters(letter):
    headers = {'Accept': 'application/json, text/javascript', 'Accept-Encoding': 'gzip', 'X-Requested-With': 'XMLHttpRequest'}
    fighters_response = client.request(COMBATE_FIGHTERS_LIST % letter, headers=headers)

    fighters = []

    for fighter in fighters_response:
        name_split = fighter['nome'].replace(' Spider ', ' ').split(' ')
        last_index = len(name_split) - 1
        first_name_key = name_split[0] + '_' + name_split[1]
        last_name_key = name_split[last_index].upper() + '_' + name_split[last_index-1].upper()
        fighters.append({
            'title': fighter['nome'],
            'url': fighter['url'],
            'slug': fighter['url'].split('/')[-2:][0],
            'thumb': 'http://media.ufc.tv/fighter_images/%s/%s.png' % (first_name_key, last_name_key)
        })

    return fighters


def get_fighter_videos(slug, page=1):
    if not slug: return [], None, 0

    if page is None:
        page = 1

    headers = {'Accept-Encoding': 'gzip'}
    result = client.request(COMBATE_FIGHTERS_DETAILS % (slug, page), headers=headers)

    videos = []

    for video in result['resultado']:
        videos.append({
            "id": video['id'],
            "title": video['titulo'],
            "plot": video['descricao'],
            "duration": sum(int(x) * 60 ** i for i, x in
                            enumerate(reversed(video['duracao'].split(':')))) if video['duracao'] else 0,
            "thumb": video['thumb_large'],
            "fanart": video['thumb_large'],
            "url": video['url']
        })

    total_pages = int(result['total_paginas'])
    next_page = page + 1 if page < total_pages else None

    return videos, next_page, total_pages


def scrape_videos_from_page(url):

    headers = {'Accept-Encoding': 'gzip'}
    html = client.request(url, headers=headers)

    config_string_matches = re.findall('window.initialState\s*=\s*({.*})', html)

    videos = []

    if not config_string_matches or len(config_string_matches) == 0:
        return videos

    config_string = config_string_matches[0]

    try:
        config_json = json.loads(config_string, object_pairs_hook=OrderedDict) if OrderedDict else json.loads(config_string)
    except Exception as ex:
        control.log("combate scrape_videos_from_page ERROR: %s" % ex)
        return videos

    for video in config_json['eventVideos']['videos']:

        # "playlistTitle": "UFC: Bisping x Gastelum",
        # "id": 6313591,
        # "title": "Michael Bisping x Kelvin Gastelum",
        # "description": "Luta entre Michael Bisping x Kelvin Gastelum, válida pelo UFC Bisping x Gastelum - Peso-médio, em 25/11/2017.",
        # "duration": "8 min",
        # "thumbUrl": "https://s04.video.glbimg.com/x216/6313591.jpg",
        # "url": "/combate/v/6313591/",
        # "date": "25 de Nov de 2017"

        videos.append({
            'id': video['id'],
            'title': video['title'],
            'tvshowtitle': video['playlistTitle'],
            'plot': video['description'],
            'fanart': video['thumbUrl'],
            'thumb': video['thumbUrl'],
        })

    return videos