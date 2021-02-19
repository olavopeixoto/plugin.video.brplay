# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules.globosat import request_query
import time
import player
import pfc
from pfc import PREMIERE_LOGO, PREMIERE_FANART


FANART = 'https://canaisglobo.globo.com/_next/static/images/canaisglobo-e3e629829ab01851d983aeaec3377807.png'


CHANNEL_MAP = {
    1995: 936,
    2065: 692,
    2006: 692
}

PLAYER_HANDLER = player.__name__


def get_authorized_channels():
    query = 'query%20getChannelsList%28%24page%3A%20Int%2C%20%24perPage%3A%20Int%29%20%7B%0A%20%20broadcastChannels%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%2C%20filtersInput%3A%20%7Bfilter%3A%20WITH_PAGES%7D%29%20%7B%0A%20%20%20%20page%0A%20%20%20%20perPage%0A%20%20%20%20hasNextPage%0A%20%20%20%20nextPage%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20pageIdentifier%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20trimmedLogo%0A%20%20%20%20%20%20color%0A%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%20%20pageIdentifier%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A'
    variables = '{"page":1,"perPage":100}'

    query_response = request_query(query, variables)

    resources = query_response['data']['broadcastChannels']['resources']

    for broadcast in resources:
        if broadcast['pageIdentifier'] == 'premiere':
            continue

        yield {
                'handler': __name__,
                'method': 'get_channel_programs',
                "id": broadcast['id'],
                "adult": broadcast['id'] in [2065, 2006],
                'art': {
                    'thumb': broadcast['trimmedLogo'],
                    'fanart': FANART
                },
                'slug': broadcast['pageIdentifier'],
                "label": broadcast['name']
            }

    yield {
        'handler': pfc.__name__,
        'method': 'get_premiere_cards',
        "id": 1995,
        "adult": False,
        'art': {
            'thumb': PREMIERE_LOGO,
            'fanart': PREMIERE_FANART
        },
        "label": 'Premiere'
    }


def get_channel_programs(slug, art=None):
    if art is None:
        art = {}

    variables = '{{"id":"{id}","filter":"HOME"}}'.format(id=slug)
    query = 'query%20getPageOffers%28%24id%3A%20ID%21%2C%20%24filter%3A%20PageType%29%20%7B%0A%20%20page%3A%20page%28id%3A%20%24id%2C%20filter%3A%20%7Btype%3A%20%24filter%7D%29%20%7B%0A%20%20%20%20offerItems%20%7B%0A%20%20%20%20%20%20...%20on%20PageOffer%20%7B%0A%20%20%20%20%20%20%20%20offerId%0A%20%20%20%20%20%20%20%20title%0A%20%20%20%20%20%20%20%20navigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20...%20on%20URLNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20url%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20...%20on%20CategoriesPageNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20identifier%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20componentType%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    offers = request_query(query, variables).get('data', {}).get('page', {}).get('offerItems', [])

    for offer in offers:
        if not offer:
            continue

        if offer.get('componentType') == 'TAKEOVER':
            continue

        yield {
            'handler': __name__,
            'method': 'get_offer',
            'id': offer.get('offerId'),
            'component_type': offer.get('componentType'),
            'label': offer.get('title', ''),
            'art': {
                'thumb': art.get('thumb'),
                'fanart': FANART
            }
        }


def get_offer(id, component_type):
    # if component_type == 'THUMB':
    #     return get_thumb_offer(id)
    #
    # if component_type == 'CONTINUEWATCHING':
    #     return get_continue_watching()
    #
    # if component_type == 'OFFERHIGHLIGHT':
    #     return get_offer_highlight(id)
    #
    # if component_type == 'CATEGORYBACKGROUND':
    #     return get_category_offer(id)

    if component_type == 'BROADCASTTHUMB':
        return get_broadcastthumb_offer(id)

    # Default
    return get_generic_offer(id)


def get_generic_offer(id, page=1):

    control.log('Globosat - GET OFFER: %s | page: %s' % (id, page))

    variables = '{{"id":"{id}","page":{page},"perPage":200}}'.format(id=id, page=page)
    query = 'query%20getOffer%28%24id%3A%20ID%21%2C%20%24page%3A%20Int%2C%20%24perPage%3A%20Int%29%20%7B%0A%20%20genericOffer%28id%3A%20%24id%29%20%7B%0A%20%20%20%20...%20on%20Offer%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20items%3A%20paginatedItems%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...VideoFragment%0A%20%20%20%20%20%20%20%20%20%20...TitleFragment%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20VideoFragment%20on%20Video%20%7B%0A%20%20id%0A%20%20availableFor%0A%20%20headline%0A%20%20description%0A%20%20kind%0A%20%20duration%0A%20%20formattedDuration%0A%20%20thumb%0A%20%20liveThumbnail%0A%20%20title%20%7B%0A%20%20%20%20titleId%0A%20%20%20%20originProgramId%0A%20%20%20%20headline%0A%20%20%20%20description%0A%20%20%20%20slug%0A%20%20%20%20type%0A%20%20%20%20contentRating%0A%20%20%20%20contentRatingCriteria%0A%20%20%20%20releaseYear%0A%20%20%20%20countries%0A%20%20%20%20genresNames%0A%20%20%20%20directorsNames%0A%20%20%20%20artDirectorsNames%0A%20%20%20%20authorsNames%0A%20%20%20%20castNames%0A%20%20%20%20screenwritersNames%0A%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20slug%0A%20%20%7D%0A%7D%0Afragment%20TitleFragment%20on%20Title%20%7B%0A%20%20titleId%0A%20%20originVideoId%0A%20%20originProgramId%0A%20%20slug%0A%20%20headline%0A%20%20originalHeadline%0A%20%20description%0A%20%20type%0A%20%20format%0A%20%20contentRating%0A%20%20contentRatingCriteria%0A%20%20releaseYear%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20slug%0A%20%20%7D%0A%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20poster%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20countries%0A%20%20genresNames%0A%20%20directorsNames%0A%20%20artDirectorsNames%0A%20%20authorsNames%0A%20%20castNames%0A%20%20screenwritersNames%0A%7D'
    generic_offer = request_query(query, variables).get('data', {}).get('genericOffer', {})

    content_type = generic_offer.get('contentType')
    items = generic_offer.get('items', {})

    resources = items.get('resources', [])
    for resource in resources:

        if content_type == 'VIDEO':
            title = resource.get('title', {})
            video_id = resource.get('id')
        else:
            title = resource
            video_id = title.get('originVideoId')

        playable = title.get('type') == 'MOVIE' or content_type == 'VIDEO'

        yield {
            'handler': PLAYER_HANDLER if playable else __name__,
            'method': 'playlive' if playable else 'get_title',
            'id': video_id,
            'IsPlayable': playable,
            'title_id': title.get('titleId'),
            'label': resource.get('headline', title.get('headline')),
            'title': resource.get('headline', title.get('headline')),
            'tvshowtitle': title.get('headline') if title.get('type') in ['SERIE', 'TV_PROGRAM'] else None,
            'plot': resource.get('description', title.get('description')),
            'year': title.get('releaseYear'),
            'originaltitle': title.get('originalHeadline', ''),
            'country': title.get('countries', []) or [],
            'genre': title.get('genresNames', []) or [],
            'cast': title.get('castNames', []) or [],
            'director': title.get('directorsNames', []) or [],
            'writer': title.get('screenwritersNames', []) or [],
            'credits': title.get('artDirectorsNames', []) or [],
            'tag': title.get('contentRatingCriteria'),
            'mpaa': title.get('contentRating'),
            'studio': title.get('channel', {}).get('name'),
            'duration': resource.get('duration', 0) / 1000,
            'mediatype': 'episode' if resource.get('kind') == 'episode' else 'movie' if title.get('type') == 'MOVIE' else 'tvshow',
            'art': {
                'clearlogo': (title.get('logo', {}) or {}).get('web'),
                'thumb': resource.get('thumb'),
                'poster': resource.get('poster', {}).get('web') if resource.get('kind') != 'episode' else None,
                'tvshow.poster': title.get('poster', {}).get('web') if resource.get('kind') == 'episode' else None,
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
                'poster': control.addonNext(),
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


# BROADCASTTHUMB
def get_broadcastthumb_offer(id, page=1, per_page=200):
    query = 'query%20getLocalizedOffer%28%24id%3A%20ID%21%2C%20%24affiliateCode%3A%20String%29%20%7B%0A%20%20localizedOffer%28id%3A%20%24id%2C%20affiliateCode%3A%20%24affiliateCode%29%20%7B%0A%20%20%20%20__typename%0A%20%20%20%20...%20on%20LocalizedOffer%20%7B%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20paginatedItems%20%7B%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20...%20on%20Broadcast%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20transmissionId%0A%20%20%20%20%20%20%20%20%20%20%20%20mediaId%0A%20%20%20%20%20%20%20%20%20%20%20%20channelId%0A%20%20%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20%20%20assets%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20previewUrl%28format%3A%20MP4%2C%20scale%3A%20X216%29%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20teaserUrl%28format%3A%20MP4%2C%20scale%3A%20X360%29%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20thumbUrl%28format%3A%20JPEG%2C%20scale%3A%20X360%29%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20media%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20thumb%28size%3A%201080%29%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20liveThumbnail%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20mutedMediaId%0A%20%20%20%20%20%20%20%20%20%20%20%20promotionalMediaId%0A%20%20%20%20%20%20%20%20%20%20%20%20logo%3A%20trimmedLogo%28scale%3A%20X56%29%0A%20%20%20%20%20%20%20%20%20%20%20%20trimmedLogo%0A%20%20%20%20%20%20%20%20%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20logo%3A%20trimmedLogo%28scale%3A%20X56%29%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20pageIdentifier%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20epgCurrentSlots%28limit%3A%201%29%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20startTime%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20endTime%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20programId%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20liveBroadcast%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20durationInMinutes%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20portrait%3A%20portrait%28scale%3A%20X768%29%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20landscape%3A%20landscape%28scale%3A%20X720%29%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20imageOnAir%3A%20imageOnAir%28scale%3A%20X720%29%0A%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    variables = '{{"id":"{id}","affiliateCode":null,"page":{page},"perPage":{per_page}}}'.format(id=id, page=page, per_page=per_page)
    page = request_query(query, variables).get('data', {}).get('localizedOffer', {}).get('paginatedItems', {})

    for item in page.get('resources', []):
        media = item.get('media', {}) or {}
        yield {
            'handler': PLAYER_HANDLER,
            'method': 'playlive',
            'IsPlayable': True,
            'livefeed': True,
            'id': item.get('mediaId'),
            'label': media.get('headline', ''),
            'title': media.get('headline', ''),
            'mediatype': 'video',
            'art': {
                'thumb': '%s?v=%s' % (media.get('liveThumbnail', FANART) or FANART, str(int(time.time()))),
                'fanart': item.get('imageOnAir', FANART),
                'icon': item.get('logo')
            }
        }

    if page.get('hasNextPage', False):
        yield {
            'handler': __name__,
            'method': 'get_broadcastthumb_offer',
            'id': id,
            'page': page.get('nextPage'),
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
            'art': {
                'poster': control.addonNext(),
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
            'title_id': title.get('titleId'),
            'label': title.get('headline', ''),
            'title': title.get('headline'),
            'originaltitle': title.get('originalHeadline'),
            'plot': title.get('description'),
            'year': title.get('releaseYear'),
            'country': title.get('countries', []),
            'genre': title.get('genresNames', []),
            'cast': title.get('castNames', []),
            'director': title.get('directorsNames', []),
            'writer': title.get('screenwritersNames', []),
            'credits': title.get('artDirectorsNames', []),
            'mpaa': title.get('contentRating'),
            'studio': title.get('channel', {}).get('name'),
            'mediatype': 'movie',
            'IsPlayable': True,
            'art': {
                'clearlogo': title.get('logo', {}).get('web'),
                'poster': title.get('poster', {}).get('web'),
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
                'originaltitle': title.get('originalHeadline'),
                'plot': video.get('description', ''),
                'duration': video.get('duration', 0) / 1000,
                'episode': resource.get('number'),
                'season': resource.get('seasonNumber'),
                'mediatype': 'episode',
                'tvshowtitle': title.get('headline'),
                'year': title.get('releaseYear'),
                'country': title.get('countries', []),
                'genre': title.get('genresNames', []),
                'cast': title.get('castNames', []),
                'director': title.get('directorsNames', []),
                'writer': title.get('screenwritersNames', []),
                'credits': title.get('artDirectorsNames', []),
                'mpaa': title.get('contentRating'),
                'studio': title.get('channel', {}).get('name'),
                'aired': (video.get('exhibitedAt', '') or '').split('T')[0],
                'art': {
                    'thumb': video.get('thumb'),
                    'fanart': title.get('cover', {}).get('landscape', FANART),
                    'tvshow.poster': title.get('poster', {}).get('web'),
                },
                'sort': control.SORT_METHOD_EPISODE if resource.get('number') and resource.get('seasonNumber') else None
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
                    'originaltitle': title.get('originalHeadline'),
                    'plot': video.get('description', ''),
                    'duration': video.get('duration', 0) / 1000,
                    'episode': episode.get('number'),
                    'season': episode.get('seasonNumber'),
                    'mediatype': 'episode',
                    'tvshowtitle': title.get('headline'),
                    'year': title.get('releaseYear'),
                    'country': title.get('countries', []),
                    'genre': title.get('genresNames', []),
                    'cast': title.get('castNames', []),
                    'director': title.get('directorsNames', []),
                    'writer': title.get('screenwritersNames', []),
                    'credits': title.get('artDirectorsNames', []),
                    'mpaa': title.get('contentRating'),
                    'studio': title.get('channel', {}).get('name'),
                    'aired': (video.get('exhibitedAt', '') or '').split('T')[0],
                    'art': {
                        'thumb': video.get('thumb'),
                        'fanart': title.get('cover', {}).get('landscape', FANART),
                        'tvshow.poster': title.get('poster', {}).get('web'),
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
                    'sort': [(control.SORT_METHOD_LABEL, '%Y')],
                    'season': season.get('number', 0),
                    'mediatype': 'season',
                    'art': {
                        'clearlogo': title.get('logo', {}).get('web'),
                        'poster': title.get('poster', {}).get('web'),
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
                'poster': control.addonNext(),
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

    episodes = (season_resource.get('episodes', {}) or {})

    for episode in episodes.get('resources', []):
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
            'episode': episode.get('number'),
            'season': episode.get('seasonNumber'),
            'mediatype': 'episode',
            'tvshowtitle': title.get('headline'),
            'year': title.get('releaseYear'),
            'country': [c.get('name') for c in title.get('countries', []) if 'name' in c and c['name']],
            'genre': [c.get('name') for c in title.get('genres', []) if 'name' in c and c['name']],
            'cast': [c.get('name') for c in title.get('cast', []) if 'name' in c and c['name']],
            'director': [c.get('name') for c in title.get('directors', []) if 'name' in c and c['name']],
            'mpaa': title.get('contentRating'),
            'studio': title.get('channel', {}).get('name'),
            'dateadded': video.get('exhibitedAt', '').replace('Z', '').replace('T', ' '),
            'aired': (video.get('exhibitedAt', '') or '').split('T')[0],
            'sort': control.SORT_METHOD_EPISODE,
            'art': {
                'thumb': video.get('thumb'),
                'fanart': title.get('cover', {}).get('landscape', FANART),
                'tvshow.poster': title.get('poster', {}).get('web'),
            }
        }

    page = episodes.get('nextPage', 0) if episodes.get('hasNextPage', False) else 0

    if page > 0:
        yield {
            'handler': __name__,
            'method': 'get_episodes',
            'title_id': title_id,
            'season': season,
            'page': page,
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
            'art': {
                'poster': control.addonNext(),
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def search(term, page=1):
    if not term:
        return

    query = 'query%20search%28%24query%3A%20String%21%2C%20%24page%3A%20Int%29%20%7B%0A%20%20search%20%7B%0A%20%20%20%20titles%28query%3A%20%24query%2C%20page%3A%20%24page%29%20%7B%0A%20%20%20%20%20%20...titlesCollection%0A%20%20%20%20%7D%0A%20%20%20%20videos%28query%3A%20%24query%2C%20page%3A%20%24page%29%20%7B%0A%20%20%20%20%20%20...videosCollection%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20titlesCollection%20on%20TitleCollection%20%7B%0A%20%20page%0A%20%20perPage%0A%20%20hasNextPage%0A%20%20nextPage%0A%20%20total%0A%20%20resources%20%7B%0A%20%20%20%20id%0A%20%20%20%20titleId%0A%20%20%20%20slug%0A%20%20%20%20headline%0A%20%20%20%20originalHeadline%0A%20%20%20%20description%0A%20%20%20%20originVideoId%0A%20%20%20%20originProgramId%0A%20%20%20%20type%0A%20%20%20%20format%0A%20%20%20%20contentRating%0A%20%20%20%20contentRatingCriteria%0A%20%20%20%20releaseYear%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20slug%0A%20%20%20%20%7D%0A%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%7D%0A%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20countries%0A%20%20%20%20genresNames%0A%20%20%20%20directorsNames%0A%20%20%20%20artDirectorsNames%0A%20%20%20%20authorsNames%0A%20%20%20%20castNames%0A%20%20%20%20screenwritersNames%0A%20%20%20%20subset%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%7D%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20slug%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20videosCollection%20on%20VideoCollection%20%7B%0A%20%20page%0A%20%20perPage%0A%20%20hasNextPage%0A%20%20nextPage%0A%20%20total%0A%20%20resources%20%7B%0A%20%20%20%20id%0A%20%20%20%20kind%0A%20%20%20%20headline%0A%20%20%20%20liveThumbnail%0A%20%20%20%20thumb%0A%20%20%20%20title%20%7B%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20originalHeadline%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20originVideoId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20format%0A%20%20%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%7D%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20slug%0A%20%20%20%20%7D%0A%20%20%20%20availableFor%0A%20%20%20%20duration%0A%20%20%20%20formattedDuration%0A%20%20%20%20exhibitedAt%0A%20%20%7D%0A%7D'
    variables = '{{"query":"{term}","page":{page}}}'.format(term=term, page=page)

    response = request_query(query, variables).get('data', {}).get('search', {})

    titles = response.get('titles', {})

    provider = control.lang(31200).encode('utf-8')

    for title in titles.get('resources', []):
        playable = True if title.get('originVideoId') else False
        yield {
                'handler': PLAYER_HANDLER if playable else __name__,
                'method': 'playlive' if playable else 'get_title',
                'title_id': title.get('titleId'),
                'id': title.get('originVideoId'),
                'program_id': title.get('originProgramId'),
                'IsPlayable': playable,
                'label': title.get('headline', ''),
                'title': title.get('headline', ''),
                'studio': title.get('channel', {}).get('name', provider),
                'year': title.get('releaseYear', ''),
                'originaltitle': title.get('originalHeadline', ''),
                'country': title.get('countries', []),
                'genre': title.get('genresNames', []),
                'cast': title.get('castNames', []),
                'director': title.get('directorsNames', []),
                'writer': title.get('screenwritersNames', []),
                'credits': title.get('artDirectorsNames', []),
                'tag': title.get('contentRatingCriteria'),
                'mpaa': title.get('contentRating', ''),
                'plot': title.get('description', ''),
                'mediatype': 'movie' if title.get('type', '') == 'MOVIE' else 'tvshow',
                # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
                'art': {
                    'poster': title.get('poster', {}).get('web'),
                    'clearlogo': title.get('logo', {}).get('web'),
                    'fanart': title.get('cover', {}).get('web', FANART)
                }
            }

    videos = response.get('videos', {}) or {}

    for video in videos.get('resources', []):
        title = video.get('title', {})
        yield {
                'handler': PLAYER_HANDLER,
                'method': 'playlive',
                'id': video.get('id'),
                'program_id': title.get('originProgramId'),
                'IsPlayable': True,
                'label': video.get('headline', ''),
                'title': video.get('headline', ''),
                'tvshowtitle': title.get('headline', ''),
                'studio': (title.get('channel', {}) or {}).get('name', provider),
                'year': title.get('releaseYear', ''),
                'originaltitle': title.get('originalHeadline', ''),
                'country': title.get('countries', []),
                'genre': title.get('genresNames', []),
                'cast': title.get('castNames', []) or [],
                'director': title.get('directorsNames', []),
                'writer': title.get('screenwritersNames', []),
                'credits': title.get('artDirectorsNames', []),
                'tag': title.get('contentRatingCriteria'),
                'mpaa': title.get('contentRating', ''),
                'plot': title.get('description', ''),
                'mediatype': 'episode',
                # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
                'art': {
                    'thumb': video.get('thumb', FANART) or FANART,
                    'tvshow.poster': title.get('poster', {}).get('web'),
                    'clearlogo': (title.get('logo', {}) or {}).get('web'),
                    'fanart': (title.get('cover', {}) or {}).get('web', FANART)
                }
            }

    if videos.get('hasNextPage', False) or titles.get('hasNextPage', False):
        yield {
            'handler': __name__,
            'method': 'search',
            'term': term,
            'page': videos.get('nextPage', titles.get('nextPage')),
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
            'art': {
                'poster': control.addonNext(),
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }
