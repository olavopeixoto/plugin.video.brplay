# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import client
from BeautifulSoup import BeautifulSoup as bs
from resources.lib.modules import workers
import re

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
            'title': 'Pride',
            'slug': 'pride'
        },
        {
            'title': 'Meca',
            'slug': 'meca'
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


def __append_result(fn, list, size_meter, *args):
        list_return = fn(*args)
        size_meter[0] = len(list_return) if list_return and size_meter[0] > 0 else 0
        if list_return and len(list_return) > 0:
            list += list_return


def get_all_events(slug):

    preload_size = 20

    events = []

    start = 1
    end = 1
    size_meter = [1]

    while size_meter[0] > 0:
        start = end
        end = start + preload_size - 1
        threads = [workers.Thread(__append_result, get_events_by_page, events, size_meter, slug, i) for i in range(start, end)]
        [i.start() for i in threads]
        [i.join() for i in threads]

    return [{
        'title': u'Últimos',
        'url': None,
        'order': '*'
    }] + sorted(events, key=lambda k: k['order'], reverse=True)


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
    soup = bs(html)

    cards = soup.find('div', attrs={'class': 'cards'})

    inner_html = cards.renderContents()

    card_list = inner_html.split('<div class="pauta"></div>')

    videos = []

    tvshowtitle = soup.find('meta', attrs={'property': 'og:title'})['content']

    for card in card_list:
        card_bs = bs(card)

        link = card_bs.find('a')
        paragraph = card_bs.find('p', attrs={'class': 'right'})

        video_id = link.find('span', attrs={'class': 'card combate '})['data-video-id']
        first_fighter = paragraph.find('span', attrs={'class': re.compile(r'\bfirst\b')}).renderContents()
        second_fighter = paragraph.find('span', attrs={'class': re.compile(r'\blast\b')}).renderContents()
        description = paragraph.find('span', attrs={'class': 'description'}).renderContents()

        videos.append({
            'id': video_id,
            'title': first_fighter + ' x ' + second_fighter,
            'tvshowtitle': tvshowtitle,
            'plot': description,
            'fanart': THUMB_URL % video_id,
            'thumb': THUMB_URL % video_id,
        })

    return videos