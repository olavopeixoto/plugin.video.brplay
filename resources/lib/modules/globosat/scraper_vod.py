# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import kodi_util
from resources.lib.modules import util
import datetime
import requests
import os
import player
from resources.lib.modules import workers
from resources.lib.modules.globosat import request_query

artPath = control.artPath()
PREMIERE_LOGO = os.path.join(artPath, 'logo_premiere.png')
PREMIERE_FANART = os.path.join(artPath, 'fanart_premiere_720.jpg')

PREMIERE_NEXT_MATCHES_JSON = 'https://api-soccer.globo.com/v1/premiere/matches?status=not_started&order=asc&page='

FANART = 'https://globosatplay.globo.com/_next/static/images/canaisglobo-e3e629829ab01851d983aeaec3377807.png'
NEXT_ICON = os.path.join(control.artPath(), 'next.png')

CHANNEL_MAP = {
    1995: 936,
    2065: 692,
    2006: 692
}

PLAYER_HANDLER = player.__name__


def get_authorized_channels():
    query = 'query%20getChannelsList(%24page%3A%20Int%2C%20%24perPage%3A%20Int)%20%7B%0A%20%20broadcastChannels(page%3A%20%24page%2C%20perPage%3A%20%24perPage%2C%20filtersInput%3A%20%7Bfilter%3A%20WITH_PAGES%7D)%20%7B%0A%20%20%20%20page%0A%20%20%20%20perPage%0A%20%20%20%20hasNextPage%0A%20%20%20%20nextPage%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20pageIdentifier%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20logo(format%3A%20PNG)%0A%20%20%20%20%20%20color%0A%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%20%20pageIdentifier%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A'
    variables = '{"page":1,"perPage":100}'

    query_response = request_query(query, variables)

    resources = query_response['data']['broadcastChannels']['resources']

    for broadcast in resources:
        yield {
                'handler': __name__,
                'method': 'get_channel_programs',
                "id": broadcast['id'],
                "adult": broadcast['id'] in [2065, 2006],
                'art': {
                    'thumb': broadcast['logo'],
                    'fanart': FANART
                },
                'slug': broadcast['pageIdentifier'],
                "label": broadcast['name']
            }

    yield {
        'handler': __name__,
        'method': 'get_premiere_cards',
        "id": 1995,
        "adult": False,
        'art': {
            'thumb': PREMIERE_LOGO,
            'fanart': PREMIERE_FANART
        },
        "label": 'Premiere'
    }


def get_channel_programs(slug, art={}):
    variables = '{{"id":"{id}","filter":"HOME"}}'.format(id=slug)
    query = 'query%20getPageOffers%28%24id%3A%20ID%21%2C%20%24filter%3A%20PageType%29%20%7B%0A%20%20page%3A%20page%28id%3A%20%24id%2C%20filter%3A%20%7Btype%3A%20%24filter%7D%29%20%7B%0A%20%20%20%20offerItems%20%7B%0A%20%20%20%20%20%20...%20on%20PageOffer%20%7B%0A%20%20%20%20%20%20%20%20offerId%0A%20%20%20%20%20%20%20%20title%0A%20%20%20%20%20%20%20%20navigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20...%20on%20URLNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20url%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20...%20on%20CategoriesPageNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20identifier%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20componentType%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    offers = request_query(query, variables).get('data', {}).get('page', {}).get('offerItems', [])

    for offer in offers:
        if not offer:
            continue

        if offer.get('componentType', None) == 'TAKEOVER':
            continue

        yield {
            'handler': __name__,
            'method': 'get_offer',
            'id': offer.get('offerId', None),
            'label': offer.get('title', ''),
            'art': {
                'thumb': art.get('thumb', None),
                'fanart': FANART
            }
        }


def get_offer(id, page=1):

    control.log('Globosat - GET OFFER: %s | page: %s' % (id, page))

    variables = '{{"id":"{id}","page":{page},"perPage":200}}'.format(id=id, page=page)
    query = 'query%20getOffer%28%24id%3A%20ID%21%2C%20%24page%3A%20Int%2C%20%24perPage%3A%20Int%29%20%7B%0A%20%20genericOffer%28id%3A%20%24id%29%20%7B%0A%20%20%20%20...%20on%20Offer%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20items%3A%20paginatedItems%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...VideoFragment%0A%20%20%20%20%20%20%20%20%20%20...TitleFragment%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20VideoFragment%20on%20Video%20%7B%0A%20%20id%0A%20%20availableFor%0A%20%20headline%0A%20%20description%0A%20%20kind%0A%20%20duration%0A%20%20formattedDuration%0A%20%20thumb%0A%20%20liveThumbnail%0A%20%20title%20%7B%0A%20%20%20%20titleId%0A%20%20%20%20originProgramId%0A%20%20%20%20headline%0A%20%20%20%20description%0A%20%20%20%20slug%0A%20%20%20%20type%0A%20%20%20%20contentRating%0A%20%20%20%20contentRatingCriteria%0A%20%20%20%20releaseYear%0A%20%20%20%20countries%0A%20%20%20%20genresNames%0A%20%20%20%20directorsNames%0A%20%20%20%20artDirectorsNames%0A%20%20%20%20authorsNames%0A%20%20%20%20castNames%0A%20%20%20%20screenwritersNames%0A%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20slug%0A%20%20%7D%0A%7D%0Afragment%20TitleFragment%20on%20Title%20%7B%0A%20%20titleId%0A%20%20originVideoId%0A%20%20originProgramId%0A%20%20slug%0A%20%20headline%0A%20%20originalHeadline%0A%20%20description%0A%20%20type%0A%20%20format%0A%20%20contentRating%0A%20%20contentRatingCriteria%0A%20%20releaseYear%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20slug%0A%20%20%7D%0A%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20poster%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20countries%0A%20%20genresNames%0A%20%20directorsNames%0A%20%20artDirectorsNames%0A%20%20authorsNames%0A%20%20castNames%0A%20%20screenwritersNames%0A%7D'
    generic_offer = request_query(query, variables).get('data', {}).get('genericOffer', {})

    content_type = generic_offer.get('contentType', None)
    items = generic_offer.get('items', {})

    resources = items.get('resources', [])
    for resource in resources:

        if content_type == 'VIDEO':
            title = resource.get('title', {})
            video_id = resource.get('id', None)
        else:
            title = resource
            video_id = title.get('originVideoId', None)

        playable = title.get('type', None) == 'MOVIE' or content_type == 'VIDEO'

        yield {
            'handler': PLAYER_HANDLER if playable else __name__,
            'method': 'playlive' if playable else 'get_title',
            'id': video_id,
            'IsPlayable': playable,
            'title_id': title.get('titleId', None),
            'label': resource.get('headline', title.get('headline', None)),
            'title': resource.get('headline', title.get('headline', None)),
            'tvshowtitle': title.get('headline', None) if title.get('type', None) in ['SERIE', 'TV_PROGRAM'] else None,
            'plot': resource.get('description', title.get('description', None)),
            'year': title.get('releaseYear', None),
            'originaltitle': title.get('originalHeadline', ''),
            'country': title.get('countries', []),
            'genre': title.get('genresNames', []),
            'cast': title.get('castNames', []),
            'director': title.get('directorsNames', []),
            'writer': title.get('screenwritersNames', []),
            'credits': title.get('artDirectorsNames', []),
            'tag': title.get('contentRatingCriteria', None),
            'mpaa': title.get('contentRating', None),
            'studio': title.get('channel', {}).get('name', None),
            'duration': resource.get('duration', 0) / 1000,
            'mediatype': 'episode' if resource.get('kind', None) == 'episode' else 'movie' if title.get('type', None) == 'MOVIE' else 'tvshow',
            'art': {
                'clearlogo': (title.get('logo', {}) or {}).get('web', None),
                'thumb': resource.get('thumb', None),
                'poster': resource.get('poster', {}).get('web', None),
                'fanart': title.get('cover', {}).get('landscape', FANART)
            }
        }

    has_next_page = items.get('hasNextPage', False)
    page = items.get('nextPage', 0)

    if has_next_page:
        yield {
            'handler': __name__,
            'method': 'get_offer',
            'id': id,
            'page': page,
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
            'art': {
                'poster': NEXT_ICON,
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_title(title_id, page=1):
    if not title_id:
        return

    control.log('get_title: %s | page %s' % (title_id, page))
    variables = '{{"titleId":"{id}", "episodeTitlePage": {page}, "userIsLoggedIn": true}}'.format(id=title_id, page=page)
    query = 'query%20getTitleFavorited%28%24titleId%3A%20String%2C%20%24episodeTitlePage%3A%20Int%2C%20%24episodeTitlePerPage%3A%20Int%20%3D%20300%2C%20%24userIsLoggedIn%3A%20Boolean%21%29%20%7B%0A%20%20title%28titleId%3A%20%24titleId%29%20%7B%0A%20%20%20%20...titleFragment%0A%20%20%20%20...continueWatchingTitleFragment%0A%20%20%20%20favorited%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0Afragment%20titleFragment%20on%20Title%20%7B%0A%20%20titleId%0A%20%20slug%0A%20%20headline%0A%20%20originalHeadline%0A%20%20description%0A%20%20originVideoId%0A%20%20originProgramId%0A%20%20type%0A%20%20format%0A%20%20contentRating%0A%20%20contentRatingCriteria%0A%20%20releaseYear%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20slug%0A%20%20%7D%0A%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20poster%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20countries%0A%20%20genresNames%0A%20%20directorsNames%0A%20%20artDirectorsNames%0A%20%20authorsNames%0A%20%20castNames%0A%20%20screenwritersNames%0A%20%20structure%20%7B%0A%20%20%20%20%20%20...seasonedStructureFragment%0A%20%20%20%20%20%20...filmPlaybackStructureFragment%0A%20%20%20%20%20%20...episodeListStructureFragment%0A%20%20%20%20%7D%0A%7D%0Afragment%20seasonedStructureFragment%20on%20SeasonedStructure%20%7B%0A%20%20seasons%20%7B%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20number%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20totalEpisodes%0A%20%20%20%20%20%20episodes%28page%3A%20%24episodeTitlePage%2C%20perPage%3A%20%24episodeTitlePerPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20number%0A%20%20%20%20%20%20%20%20%20%20seasonNumber%0A%20%20%20%20%20%20%20%20%20%20seasonId%0A%20%20%20%20%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20%20%20exhibitedAt%0A%20%20%20%20%20%20%20%20%20%20%20%20encrypted%0A%20%20%20%20%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20filmPlaybackStructureFragment%20on%20FilmPlaybackStructure%20%7B%0A%20%20videoPlayback%20%7B%0A%20%20%20%20id%0A%20%20%20%20exhibitedAt%0A%20%20%20%20encrypted%0A%20%20%20%20availableFor%0A%20%20%20%20headline%0A%20%20%20%20description%0A%20%20%20%20thumb%0A%20%20%20%20duration%0A%20%20%7D%0A%7D%0Afragment%20episodeListStructureFragment%20on%20EpisodeListStructure%20%7B%0A%20%20episodes%28page%3A%20%24episodeTitlePage%2C%20perPage%3A%20%24episodeTitlePerPage%29%20%7B%0A%20%20%20%20page%0A%20%20%20%20hasNextPage%0A%20%20%20%20nextPage%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20number%0A%20%20%20%20%20%20seasonNumber%0A%20%20%20%20%20%20seasonId%0A%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20exhibitedAt%0A%20%20%20%20%20%20%20%20encrypted%0A%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20continueWatchingTitleFragment%20on%20Title%20%7B%0A%20%20structure%20%7B%0A%20%20%20%20...%20on%20SeasonedStructure%20%7B%0A%20%20%20%20%20%20continueWatching%20%40include%28if%3A%20%24userIsLoggedIn%29%20%7B%0A%20%20%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20%20%20...continueWatchingVideoFragment%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20FilmPlaybackStructure%20%7B%0A%20%20%20%20%20%20continueWatching%20%40include%28if%3A%20%24userIsLoggedIn%29%20%7B%0A%20%20%20%20%20%20%20%20...continueWatchingVideoFragment%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20EpisodeListStructure%20%7B%0A%20%20%20%20%20%20continueWatching%20%40include%28if%3A%20%24userIsLoggedIn%29%20%7B%0A%20%20%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20%20%20...continueWatchingVideoFragment%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20__typename%0A%7D%0Afragment%20continueWatchingVideoFragment%20on%20Video%20%7B%0A%20%20id%0A%20%20headline%0A%20%20description%0A%20%20watchedProgress%0A%20%20duration%0A%20%20contentRating%0A%20%20contentRatingCriteria%0A%20%20__typename%0A%7D'
    title = request_query(query, variables)['data']['title']

    if not title.get('structure', {}):
        return

    structure = title['structure']

    page = 0

    is_favorite = title.get('favorited', False)

    if 'videoPlayback' in structure:
        video = title['structure']['videoPlayback']

        yield {
            'handler': PLAYER_HANDLER,
            'method': 'playlive',
            'id': video.get('id', ''),
            'title_id': title.get('titleId', None),
            'label': title.get('headline', ''),
            'title': title.get('headline', None),
            'originaltitle': title.get('originalHeadline', None),
            'plot': title.get('description', None),
            'year': title.get('releaseYear', None),
            'country': title.get('countries', []),
            'genre': title.get('genresNames', []),
            'cast': title.get('castNames', []),
            'director': title.get('directorsNames', []),
            'writer': title.get('screenwritersNames', []),
            'credits': title.get('artDirectorsNames', []),
            'mpaa': title.get('contentRating', None),
            'studio': title.get('channel', {}).get('name', None),
            'mediatype': 'movie',
            'IsPlayable': True,
            'art': {
                'clearlogo': title.get('logo', {}).get('web', None),
                'poster': title.get('poster', {}).get('web', None),
                'fanart': title.get('cover', {}).get('landscape', FANART)
            }
        }

    elif 'episodes' in structure:
        episodes = structure.get('episodes', {})
        page = episodes.get('nextPage', 0) if episodes.get('hasNextPage', False) else 0

        for resource in episodes.get('resources', []):
            video = resource.get('video', {})
            yield {
                'handler': PLAYER_HANDLER,
                'method': 'playlive',
                'IsPlayable': True,
                'id': video.get('id'),
                'label': video.get('headline', ''),
                'title': video.get('headline', ''),
                'originaltitle': title.get('originalHeadline', None),
                'plot': video.get('description', ''),
                'duration': video.get('duration', 0) / 1000,
                'episode': resource.get('number', None),
                'season': resource.get('seasonNumber', None),
                'mediatype': 'episode',
                'tvshowtitle': title.get('headline', None),
                'year': title.get('releaseYear', None),
                'country': title.get('countries', []),
                'genre': title.get('genresNames', []),
                'cast': title.get('castNames', []),
                'director': title.get('directorsNames', []),
                'writer': title.get('screenwritersNames', []),
                'credits': title.get('artDirectorsNames', []),
                'mpaa': title.get('contentRating', None),
                'studio': title.get('channel', {}).get('name', None),
                'aired': (video.get('exhibitedAt', '') or '').split('T')[0],
                'art': {
                    'thumb': video.get('thumb', None),
                    'fanart': title.get('cover', {}).get('landscape', FANART)
                },
                'sort': control.SORT_METHOD_EPISODE if resource.get('number', None) and resource.get('seasonNumber', None) else None
            }

    elif 'seasons' in structure:

        seasons = structure.get('seasons', {}).get('resources', [])
        if len(seasons) == 1:
            season = seasons[0]
            for episode in season.get('episodes', {}).get('resources', []):
                video = episode.get('video', {})
                yield {
                    'handler': PLAYER_HANDLER,
                    'method': 'playlive',
                    'IsPlayable': True,
                    'id': video.get('id'),
                    'label': video.get('headline', ''),
                    'title': video.get('headline', ''),
                    'originaltitle': title.get('originalHeadline', None),
                    'plot': video.get('description', ''),
                    'duration': video.get('duration', 0) / 1000,
                    'episode': episode.get('number', None),
                    'season': episode.get('seasonNumber', None),
                    'mediatype': 'episode',
                    'tvshowtitle': title.get('headline', None),
                    'year': title.get('releaseYear', None),
                    'country': title.get('countries', []),
                    'genre': title.get('genresNames', []),
                    'cast': title.get('castNames', []),
                    'director': title.get('directorsNames', []),
                    'writer': title.get('screenwritersNames', []),
                    'credits': title.get('artDirectorsNames', []),
                    'mpaa': title.get('contentRating', None),
                    'studio': title.get('channel', {}).get('name', None),
                    'aired': (video.get('exhibitedAt', '') or '').split('T')[0],
                    'art': {
                        'thumb': video.get('thumb', None),
                        'fanart': title.get('cover', {}).get('landscape', FANART)
                    },
                    'sort': control.SORT_METHOD_EPISODE
                }
        else:
            for season in structure.get('seasons', {}).get('resources', []):
                yield {
                    'handler': __name__,
                    'method': 'get_episodes',
                    'title_id': title_id,
                    'label': '%s %s' % (control.lang(34137).encode('utf-8'), season.get('number', 0)),
                    'season': season.get('number', 0),
                    'mediatype': 'season',
                    'art': {
                        'clearlogo': title.get('logo', {}).get('web', None),
                        'poster': title.get('poster', {}).get('web', None),
                        'fanart': title.get('cover', {}).get('landscape', FANART)
                    }
                }

    else:
        control.log('@@@@@ globosat - unsupported structure: %s' % structure)

    if page > 0:
        yield {
            'handler': __name__,
            'method': 'get_title',
            'title_id': title_id,
            'page': page,
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
            'art': {
                'poster': NEXT_ICON,
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_episodes(title_id, season, page=1):
    variables = '{{"titleId":"{id}", "episodeTitlePage": {page}}}'.format(id=title_id, page=page)
    query = 'query%20fetchTitleQuery%28%24titleId%3A%20String%2C%20%24episodeTitlePage%3A%20Int%2C%20%24episodeTitlePerPage%3A%20Int%20%3D%20300%29%20%7B%0A%20%20title%28titleId%3A%20%24titleId%29%20%7B%0A%20%20%20%20...titleFragment%0A%20%20%7D%0A%7D%0Afragment%20titleFragment%20on%20Title%20%7B%0A%20%20titleId%0A%20%20slug%0A%20%20headline%0A%20%20description%0A%20%20originProgramId%0A%20%20type%0A%20%20format%0A%20%20contentRating%0A%20%20contentRatingCriteria%0A%20%20releaseYear%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20slug%0A%20%20%7D%0A%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20poster%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20countries%0A%20%20directors%20%7B%0A%20%20%20%20name%0A%20%20%7D%0A%20%20cast%20%7B%0A%20%20%20%20name%0A%20%20%7D%0A%20%20genres%20%7B%0A%20%20%20%20name%0A%20%20%7D%0A%20%20structure%20%7B%0A%20%20%20%20%20%20...seasonedStructureFragment%0A%20%20%20%20%20%20...filmPlaybackStructureFragment%0A%20%20%20%20%20%20...episodeListStructureFragment%0A%20%20%20%20%7D%0A%7D%0Afragment%20seasonedStructureFragment%20on%20SeasonedStructure%20%7B%0A%20%20seasons%20%7B%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20number%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20totalEpisodes%0A%20%20%20%20%20%20episodes%28page%3A%20%24episodeTitlePage%2C%20perPage%3A%20%24episodeTitlePerPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20number%0A%20%20%20%20%20%20%20%20%20%20seasonNumber%0A%20%20%20%20%20%20%20%20%20%20seasonId%0A%20%20%20%20%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20%20%20exhibitedAt%0A%20%20%20%20%20%20%20%20%20%20%20%20encrypted%0A%20%20%20%20%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20filmPlaybackStructureFragment%20on%20FilmPlaybackStructure%20%7B%0A%20%20videoPlayback%20%7B%0A%20%20%20%20id%0A%20%20%20%20exhibitedAt%0A%20%20%20%20encrypted%0A%20%20%20%20availableFor%0A%20%20%20%20headline%0A%20%20%20%20description%0A%20%20%20%20thumb%0A%20%20%20%20duration%0A%20%20%7D%0A%7D%0Afragment%20episodeListStructureFragment%20on%20EpisodeListStructure%20%7B%0A%20%20episodes%28page%3A%20%24episodeTitlePage%2C%20perPage%3A%20%24episodeTitlePerPage%29%20%7B%0A%20%20%20%20page%0A%20%20%20%20hasNextPage%0A%20%20%20%20nextPage%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20number%0A%20%20%20%20%20%20seasonNumber%0A%20%20%20%20%20%20seasonId%0A%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20exhibitedAt%0A%20%20%20%20%20%20%20%20encrypted%0A%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    title = request_query(query, variables)['data']['title']

    if not title.get('structure', {}):
        return

    structure = title['structure']

    if 'seasons' not in structure:
        return

    season_resource = next((s for s in structure.get('seasons', {}).get('resources', []) if s.get('number', 0) == season), {})

    if not season_resource:
        return

    for episode in season_resource.get('episodes', {}).get('resources', []):
        video = episode.get('video', {})
        yield {
            'handler': PLAYER_HANDLER,
            'method': 'playlive',
            'IsPlayable': True,
            'id': video.get('id'),
            'label': video.get('headline', ''),
            'title': video.get('headline', ''),
            'plot': video.get('description', ''),
            'duration': video.get('duration', 0) / 1000,
            'episode': episode.get('number', None),
            'season': episode.get('seasonNumber', None),
            'mediatype': 'episode',
            'tvshowtitle': title.get('headline', None),
            'year': title.get('releaseYear', None),
            'country': [c.get('name') for c in title.get('countries', []) if 'name' in c and c['name']],
            'genre': [c.get('name') for c in title.get('genres', []) if 'name' in c and c['name']],
            'cast': [c.get('name') for c in title.get('cast', []) if 'name' in c and c['name']],
            'director': [c.get('name') for c in title.get('directors', []) if 'name' in c and c['name']],
            'mpaa': title.get('contentRating', None),
            'studio': title.get('channel', {}).get('name', None),
            'dateadded': video.get('exhibitedAt', '').replace('Z', '').replace('T', ' '),
            'aired': (video.get('exhibitedAt', '') or '').split('T')[0],
            'sort': control.SORT_METHOD_EPISODE,
            'art': {
                'thumb': video.get('thumb', None),
                'fanart': title.get('cover', {}).get('landscape', FANART)
            }
        }


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
