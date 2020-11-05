import requests
import datetime
from auth import PLATFORM
import player

PLAYER_HANDLER = player.__name__


def get_live_channels():
    url = 'https://www.nowonline.com.br/avsclient/epg/livechannels?channel={platform}&channelIds=&numberOfSchedules=2&includes=images'.format(platform=PLATFORM)
    response = requests.get(url).json()

    for channel in response.get('response', []):

        epg = channel.get('schedules')[0]

        id = channel.get('id')
        channel_name = channel.get('name')
        title = epg.get('title')
        description = epg.get('description')
        duration = epg.get('duration', 0)
        season = epg.get('seasonNumber')
        episode = epg.get('episodeNumber')
        date = datetime.datetime.utcfromtimestamp(epg.get('startTime', 0))
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

        yield {
            'handler': PLAYER_HANDLER,
            'method': 'playlive',
            'id': id,
            'IsPlayable': True,
            'livefeed': True,
            'label': u"[B]" + channel_name + u"[/B][I] - " + name_title + u"[/I]",
            'title': u"[B]" + channel_name + u"[/B][I] - " + name_title + u"[/I]",
            'studio': 'Now Online',
            # 'title': title,
            # 'tvshowtitle': title,
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
