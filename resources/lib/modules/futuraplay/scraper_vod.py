# -*- coding: utf-8 -*-

from resources.lib.modules import client
from resources.lib.modules import control
from BeautifulSoup import BeautifulSoup as bs
from resources.lib.modules import cache
import re

import urllib
from resources.lib.modules import workers
import resources.lib.modules.util as util

CLEAR_LOGO_WHITE = 'http://static.futuraplay.org/img/futura_tracobranco.png'
CLEAR_LOGO_COLOR = 'http://static.futuraplay.org/img/futura_tracoverde.png'
FUTURA_FANART = 'http://static.futuraplay.org/img/og-image.jpg'
FUTURA_THUMB = 'https://s03.video.glbimg.com/x720/4500346.jpg'

BASE_URL = 'http://www.futuraplay.org'


def get_channels():
    return [{
        'slug': 'futura',
        'name': 'Futura',
        'logo': CLEAR_LOGO_COLOR,
        'clearlogo': CLEAR_LOGO_WHITE,
        'fanart': FUTURA_FANART,
        'thumb': FUTURA_THUMB,
        'playable': 'false',
        'plot': None,
        'id': 1985,
        'adult': False,
        'brplayprovider': 'globoplay'
    }]


def get_menu(slug=None):
    menu = cache.get(__build_menu, 7)

    if slug is not None:
        return __search_slug(menu, slug)

    return menu


def __search_slug(root, slug):
    for item in root:
        if item['slug'] == slug:
            if item['submenu'] is None or len(item['submenu']) == 0:
                return __open_url(item['url'])
            else:
                return item['submenu']

    for item in root:
        result = __search_slug(item['submenu'], slug)
        if result and len(result) > 0:
            return result

    control.log('NO ITEM FOUND!!!')
    return []


def __build_menu():
    headers = {'Accept-Encoding': 'gzip'}
    html = client.request(BASE_URL, headers=headers)

    soup = bs(html)

    div = soup.find('div', attrs={'class': 'mainmenu'})

    nav_menu = div.find('ul')

    return __get_subcategory(nav_menu)


def __get_subcategory(root_node, level=1):
    results = []

    if not root_node:
        return results

    for li in root_node.findAll('li', recursive=False):
        if level == 1 and (not li.has_key('class') or li['class'] != 'child'):
            continue

        link = li.find('a', recursive=False)

        if link is None:
            continue

        category = link.string
        url = link['href']
        slug = url + category.encode("ascii","ignore")
        submenu = li.find('ul')
        results.append({
            'title': category.capitalize(),
            'slug': slug,
            'url': url,
            'submenu': __get_subcategory(submenu, level + 1)
        })

    return results


def __open_url(url):
    headers = {'Accept-Encoding': 'gzip'}
    html = client.request(BASE_URL + url, headers=headers)

    soup = bs(html)

    gallery = soup.findAll('div', attrs={'class': 'thumb-image'})

    control.log('GALLERY: %s' % gallery)

    results = []
    for data in gallery:
        control.log("GALLERY ITEM: %s" % data)
        link = data.find('a')
        results.append({
            'title': link['data-ga-label-title'] if 'data-ga-label-title' in link else link['title'] if 'title' in link else link['href'],
            'id': link['href'],
            'thumb': re.findall('background:url\(([^)]+)', data['style'])[0],
            'brplayprovider': 'futura',
            'IsPlayable': 'true'
        })

    return results