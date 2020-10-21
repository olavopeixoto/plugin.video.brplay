from resources.lib.modules import client
import datetime
from auth import PLATFORM


def get_live_channels():
    url = 'https://www.nowonline.com.br/avsclient/epg/livechannels?channel={platform}&channelIds=&numberOfSchedules=2&includes=images'.format(platform=PLATFORM)
    response = client.request(url)

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
            'slug': id,
            'name': u"[B]" + channel_name + u"[/B][I] - " + name_title + u"[/I]",
            'studio': channel_name,
            'title': title,
            'tvshowtitle': title,
            'sorttitle': channel_name,
            'thumb': thumb,
            'logo': logo,
            'clearlogo': logo,
            'clearart': logo,
            'banner': None,
            # 'poster': poster,
            'color': None,
            'fanart': fanart,
            'id': id,
            'channel_id': id,
            'brplayprovider': 'nowonline',
            'playable': 'true',
            'livefeed': 'true',
            'dateadded': datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'),
            'plot': description,
            'duration': duration,
            'adult': False,
            'cast': [],
            'director': [],
            'genre': genre,
            'rating': rating,
            'year': None,
            'episode': episode,
            'season': season,
            "mediatype": 'episode' if episode else 'video'
        }
