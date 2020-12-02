import requests
import datetime
import pytz
import traceback
from . import player, get_authorization
from resources.lib.modules import control, util

PLAYER_HANDLER = player.__name__

SBT_LOGO = 'https://www.sbt.com.br/assets/images/logo-sbt.png'


def get_live_channels():
    headers = {
        'Authorization': get_authorization(),
        'Origin': 'https://www.sbt.com.br',
        'Accept-Encoding': 'gzip, deflate, br'
    }

    br_timezone = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(tz=br_timezone)

    if control.setting('sbt_ignore_dst') == 'true':
        now = now - br_timezone.localize(datetime.datetime.utcnow()).dst()

    url = 'https://content.sbt.com.br/api/programschedule?livegrade={date}&operation=le&orderby=startdate&limit=1'.format(date=now.strftime('%Y-%m-%dT%H:%M:%S'))

    control.log('GET %s' % url)

    programs = (requests.get(url, headers=headers, verify=False).json() or {}).get('results', [])

    control.log(programs)

    program = next(iter(programs), {}) or {}

    try:
        start_time = util.strptime_workaround(program.get('startdate'), '%Y-%m-%dT%H:%M:%S')
        start_time = br_timezone.localize(start_time)
        start_time = start_time.astimezone(pytz.UTC)
        start_time = start_time + util.get_utc_delta()
    except:
        control.log(traceback.format_exc(), control.LOGERROR)
        start_time = datetime.datetime.now()

    plot = program.get('description')
    plot = '%s - | %s' % (datetime.datetime.strftime(start_time, '%H:%M'), plot)
    program_name = program.get('title')
    channel_name = 'SBT'

    label = u"[B]%s[/B][I] - %s[/I]" % (channel_name, program_name)

    thumb = program.get('thumbnail')

    tags = []

    yield {
        'handler': PLAYER_HANDLER,
        'method': 'playlive',
        'IsPlayable': True,
        'livefeed': True,
        'studio': channel_name,
        'label': label,
        'title': label,
        'genre': program.get('gender'),
        # 'title': program.get('metadata', program.get('name', '')),
        'tvshowtitle': program_name,
        'sorttitle': program_name,
        'tag': tags,
        'plot': plot,
        'duration': int(0),
        'dateadded': datetime.datetime.strftime(start_time, '%Y-%m-%d %H:%M:%S'),
        'mediatype': 'episode',
        'art': {
            'icon': SBT_LOGO,
            'clearlogo': SBT_LOGO,
            'fanart': thumb,
            'thumb': thumb,
            'tvshow.poster': thumb,
        }
    }


def get_programmes():

    page_range = [0, 1, 2]

    headers = {
        'Authorization': get_authorization(),
        'Origin': 'https://www.sbt.com.br',
        'Accept-Encoding': 'gzip, deflate, br'
    }

    results = []

    br_timezone = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(tz=br_timezone)

    for i in page_range:
        date = now + datetime.timedelta(days=i)

        url = 'http://content.sbt.com.br/api/programgrade?datagrade={}&limit=200'.format(date.strftime('%Y-%m-%d'))

        print('GET ' + url)

        response = requests.get(url, headers=headers, verify=False).json()

        results.extend(response['results'])

    programmes = []

    for result in results:

        start_time = util.strptime_workaround(result['startdate'], '%Y-%m-%dT%H:%M:%S')

        start_time = pytz.timezone('America/Sao_Paulo').localize(start_time)

        start_time = start_time.astimezone(pytz.UTC)

        start_time_string = datetime.datetime.strftime(start_time, '%Y%m%d%H%M%S +0000')

        title = result['title']

        rating = result['classification'].strip()

        desc = result['description'] + u' ({})'.format(rating)

        programme = {
            'channel': id,
            'start': start_time_string,
            'title': [(title, u'pt')],
            'icon': [{'src': result['thumbnail']}],
            'desc': [(desc, u'pt')],
            'category': [(result['gender'], u'pt')]
        }

        programmes.append(programme)

    programmes = sorted(programmes, key=lambda x: (x['channel'], x['start']))

    size = len(programmes)

    for i in range(0, size - 1):
        if programmes[i]['channel'] == programmes[i + 1]['channel']:
            programmes[i]['stop'] = programmes[i + 1]['start']

    return programmes
