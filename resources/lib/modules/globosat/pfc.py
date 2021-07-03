# -*- coding: utf-8 -*-

from resources.lib.modules import kodi_util
from resources.lib.modules import util
from resources.lib.modules import workers
from resources.lib.modules import control
import datetime
import requests
import os


artPath = control.artPath()
PREMIERE_LOGO = os.path.join(artPath, 'logo_premiere.png')
PREMIERE_FANART = os.path.join(artPath, 'fanart_premiere_720.jpg')

PREMIERE_NEXT_MATCHES_JSON = 'https://api-soccer.globo.com/v1/premiere/matches?status=not_started&order=asc&page='


def get_premiere_cards():
    return [{
            'handler': __name__,
            'method': 'get_premiere_games',
            'title': u'\u2063Veja a Programação',
            'label': u'[B]\u2063Próximos Jogos[/B]',
            'plot': 'Veja os jogos programados',
            'art': {
                'thumb': PREMIERE_FANART,
                'fanart': PREMIERE_FANART,
                'clearlogo': PREMIERE_LOGO,
            }
        }]


def get_premiere_games():
    headers = {'Accept-Encoding': 'gzip'}

    page = 1
    result = requests.get(PREMIERE_NEXT_MATCHES_JSON + str(page), headers=headers).json()
    next_games = result['results']
    pages = result['pagination']['pages']

    if pages > 1:
        threads = []
        for page in range(2, pages + 1):
            threads.append(workers.Thread(requests.get, PREMIERE_NEXT_MATCHES_JSON + str(page), headers))

        [i.start() for i in threads]
        [i.join() for i in threads]
        [next_games.extend(i.get_result().json().get('results', []) or []) for i in threads]

    for game in next_games:
        utc_timezone = control.get_current_brasilia_utc_offset()
        parsed_date = util.strptime_workaround(game['datetime'], format='%Y-%m-%dT%H:%M:%S') + datetime.timedelta(hours=(-utc_timezone))
        date_string = kodi_util.format_datetimeshort(parsed_date)

        label = game['home']['name'] + u' x ' + game['away']['name']

        medias = game.get('medias', []) or []

        media_desc = '\n\n' + '\n\n'.join([u'Transmissão %s\n%s' % (media.get('title'), media.get('description')) for media in medias])

        plot = game['phase'] + u' d' + get_artigo(game['championship']) + u' ' + game['championship'] + u'\nDisputado n' + get_artigo(game['stadium']) + u' ' + game['stadium'] + u'. ' + date_string + media_desc

        name = (date_string + u' - ') + label

        # thumb = merge_logos(game['home']['logo_60x60_url'], game['away']['logo_60x60_url'], str(game['id']) + '.png')
        # thumb = PREMIERE_FANART

        yield {
            'label': name,
            'plot': plot,
            'tvshowtitle': game['championship'],
            'IsPlayable': False,
            'setCast': [{
                    'name': game['home']['name'],
                    'role': 'Mandante',
                    'thumbnail': game['home']['logo_60x60_url'],
                    'order': 0
                }, {
                    'name': game['away']['name'],
                    'role': 'Visitante',
                    'thumbnail': game['away']['logo_60x60_url'],
                    'order': 1
                }],
            'art': {
                'thumb': game['home']['logo_60x60_url'],
                'fanart': PREMIERE_FANART
            }
        }


def merge_logos(logo1, logo2, filename):
    from PIL import Image
    from io import BytesIO

    file_path = os.path.join(control.tempPath, filename)

    control.log(file_path)

    if os.path.isfile(file_path):
        return file_path

    images = map(Image.open, [BytesIO(requests.get(logo1).content), BytesIO(requests.get(logo2).content)])
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGBA', (total_width, max_height))

    x_offset = 0
    for im in images:
        height_offset = (max_height - im.size[1]) / 2
        new_im.paste(im, (x_offset, height_offset))
        x_offset += im.size[0]

    new_im.save(file_path)

    return file_path


def get_artigo(word):

    test = word.split(' ')[0] if word else u''

    if test.endswith('a'):
        return u'a'

    if test.endswith('as'):
        return u'as'

    if test.endswith('os'):
        return u'os'

    return u'o'
