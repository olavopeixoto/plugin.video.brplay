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

    results = []
    return results


def get_videos(page=1):

    url = 'https://sexyhot.globo.com/api/v1/videos?page=' + str(page)

    result = client.request(url)

    videos = []

    for video in result['videos']:
        videos.append({
            'id_sexyhot': video['idGloboVideo'],
            'mediatype': 'movie' if video['type'] == 'film' else 'episode' if type == 'serie' else 'video',
            'overlay': 6,
            'duration': int(video['unformatted_duration'])/1000,
            'title': video['title'],
            'plot': video['description'],
            'cast': [actor['name'] for actor in video['cast']],
            'tag': [tag for tag in video['tags']],
            'thumb': video['thumb'],
            'poster': video['card_url'] if video['type'] == 'film' else video['thumb'],
            'fanart': os.path.join(artPath, 'fanart_sexyhot.png'),
            'episode': video['episode'],
            'year': video['year']
        })

    next_page = result['pagination']['page'] + 1 if result['pagination']['page'] < result['pagination']['totalPages'] else None

    return videos, next_page
