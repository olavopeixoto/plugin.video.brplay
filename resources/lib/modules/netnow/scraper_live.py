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
        channel_name = channel.get('name', None)
        title = epg.get('title', None)
        description = epg.get('description', None)
        duration = epg.get('duration', 0)
        season = epg.get('seasonNumber', None) or None
        episode = epg.get('episodeNumber', None) or None
        date = datetime.datetime.utcfromtimestamp(epg.get('startTime', 0))
        genre = channel.get('type', None)
        rating = epg.get('ageRating', None)

        logo = channel.get('logo', None)

        # thumb = epg.get('images', {}).get('coverLandscape', None)
        # fanart = epg.get('images', {}).get('coverLandscape', None)
        # poster = epg.get('images', {}).get('coverPortrait', None)
        # banner = epg.get('images', {}).get('banner', None)
        thumb = epg.get('images', {}).get('banner', None)
        fanart = thumb

        name_title = u'%s: T%s E%s' % (title, season, episode) if season else title

        yield {
            'handler': PLAYER_HANDLER,
            'method': 'playlive',
            'id': id,
            'IsPlayable': True,
            'livefeed': True,
            'label': u"[B]" + channel_name + u"[/B][I] - " + name_title + u"[/I]",
            'studio': channel_name,
            'title': title,
            'tvshowtitle': title,
            'sorttitle': channel_name,
            'channel_id': id,
            'dateadded': datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'),
            'plot': description,
            'duration': duration,
            'adult': False,
            'genre': genre,
            'rating': rating,
            'episode': episode,
            'season': season,
            "mediatype": 'tvshow',
            'art': {
                'thumb': thumb,
                'clearlogo': logo,
                # 'poster': poster,
                'fanart': fanart
            }
        }
