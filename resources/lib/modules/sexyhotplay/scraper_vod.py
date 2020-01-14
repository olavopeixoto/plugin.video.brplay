import os,re
from resources.lib.modules import control
from resources.lib.modules import client

artPath = control.artPath()


def getChannels():

    channels = [{
        'slug': 'sexyhot',
        'name': 'Sexyhot',
        'logo': os.path.join(artPath, 'logo_sexyhot.png'),
        'fanart': os.path.join(artPath, 'fanart_sexyhot.png'),
        'playable': 'false',
        'plot': None,
        'id': None,
        'isFolder': 'true'
    }]

    return channels


def get_categories():

    # url = "http://sexyhotplay.com.br/categorias/"
    # html = client.request(url, headers={'Cookie': 'disclaimer-sexyhotplay=1;'})
    #
    # soup = bs(html)
    # div = soup.find('div', attrs={'class': 'colunas-3-15'})
    #
    # links = div.findAll('a', attrs={'class': 'link'}, recursive=True)

    results = []
    # for link in links:
    #     label = link.find('strong').string
    #     url = 'http://sexyhotplay.com.br' + link['href']
    #     results.append({
    #         'name': label,
    #         # 'clearlogo': os.path.join(artPath, 'logo_sexyhot.png'),
    #         'url': url
    #     })

    return results


def get_videos(page=1):

    url = 'https://sexyhot.globo.com/api/v1/videos?page=' + str(page)

    result = client.request(url)

    videos = []

    for video in result['videos']:
        videos.append({
            'id_sexyhot': video['idGloboVideo'],
            'mediatype': 'movie',
            'overlay': 6,
            'duration': int(video['unformatted_duration']),
            'title': video['title'],
            'plot': video['description'],
            'cast': [actor['name'] for actor in video['cast']],
            'poster': video['thumb'],
            'fanart': os.path.join(artPath, 'fanart_sexyhot.png')
        })

    next_page = result['pagination']['page'] + 1 if result['pagination']['page'] < result['pagination']['totalPages'] else None

    return videos, next_page