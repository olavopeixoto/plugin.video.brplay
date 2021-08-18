import requests
import datetime
import traceback
from .auth import login
from .auth import PLATFORM
from . import player
import resources.lib.modules.control as control

PLAYER_HANDLER = player.__name__

proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


def get_live_channels():

    try:
        credentials = login()
        return get_live_channels_user_only(credentials)

    except Exception as ex:
        control.log(traceback.format_exc(), control.LOGERROR)
        control.okDialog(u'Now Online', str(ex))
        return []
        # return get_live_channels_all()


def get_live_channels_user_only(credentials):
    avs_cookie = credentials['cookies']['avs_cookie']
    login_info = credentials['cookies']['LoginInfo']

    cookies = {
        'avs_cookie': avs_cookie,
        'LoginInfo': login_info
    }

    header = {}

    if PLATFORM == 'PCTV':
        header['x-xsrf-token'] = credentials['headers']['X-Xsrf-Token']

    url = 'https://www.nowonline.com.br/avsclient/1.1/epg/livechannels?channel={platform}&channelIds=&numberOfSchedules=2&includes=images&onlyUserContent=Y'.format(
        platform=PLATFORM)
    response = requests.get(url, headers=header, cookies=cookies, proxies=proxy).json()

    control.log(response)

    for channel in (response.get('response', {}) or {}).get('liveChannels', []) or []:
        yield hydrate_channel(channel)


def get_live_channels_all():
    url = 'https://www.nowonline.com.br/avsclient/epg/livechannels?channel={platform}&channelIds=&numberOfSchedules=2&includes=images'.format(platform=PLATFORM)

    control.log('GET %s' % url)

    response = requests.get(url).json()

    control.log(response)

    for channel in response.get('response', []):
        yield hydrate_channel(channel)


def hydrate_channel(channel):
    epg = next(iter(channel.get('schedules', [])), {})

    id = channel.get('id')
    channel_name = channel.get('name') or channel.get('title', '')
    title = epg.get('title', '') or channel_name
    description = epg.get('description')
    duration = epg.get('duration', 0)
    season = epg.get('seasonNumber')
    episode = epg.get('episodeNumber')
    date = datetime.datetime.utcfromtimestamp(epg.get('startTime', 0))
    end_time = datetime.datetime.utcfromtimestamp(epg.get('endTime', 0))
    genre = channel.get('type')
    rating = epg.get('ageRating')

    logo = channel.get('logo')

    # thumb = epg.get('images', {}).get('coverLandscape')
    # fanart = epg.get('images', {}).get('coverLandscape')
    poster = epg.get('images', {}).get('coverPortrait')
    # banner = epg.get('images', {}).get('banner')
    thumb = epg.get('images', {}).get('banner')
    fanart = thumb

    name_title = u'%s: T%s E%s' % (title, season, episode) if season else title

    label = u"[B]%s[/B][I] - %s[/I]" % (channel_name, name_title)

    program_time_desc = datetime.datetime.strftime(date, '%H:%M') + ' - ' + datetime.datetime.strftime(end_time, '%H:%M')

    tags = [program_time_desc]

    description = '%s | %s' % (program_time_desc, description)

    return {
        'handler': PLAYER_HANDLER,
        'method': 'playlive',
        'id': id,
        'IsPlayable': True,
        'livefeed': True,
        'label': label,
        'title': label,
        'studio': 'Now Online',
        'tag': tags,
        # 'title': title,
        'tvshowtitle': title,
        'sorttitle': name_title,
        'channel_id': id,
        'dateadded': datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'),
        'plot': description,
        'duration': duration,
        'adult': False,
        'genre': genre,
        'rating': rating,
        'episode': episode,
        'season': season,
        'art': {
            'thumb': thumb,
            'clearlogo': logo,
            'tvshow.poster': poster or thumb,
            'fanart': fanart
        }
    }