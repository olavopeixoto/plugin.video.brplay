# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules.globoplay import request_query, get_headers, get_image_scaler, get_authorized_services
from . import auth_helper
from . import player
import requests
import os
from resources.lib.modules.globosat import pfc
from resources.lib.modules.globosat.pfc import PREMIERE_LOGO, PREMIERE_FANART

GLOBO_LOGO_WHITE = 'https://s2.glbimg.com/1D3_vIjzzFrXkfMVFmEcMqq7gQk=/285x285/https://s2.glbimg.com/nItvOm5LGvf7xhO-zkUsoeFbVMY=/filters:fill(transparent,false)/https://i.s3.glbimg.com/v1/AUTH_c3c606ff68e7478091d1ca496f9c5625/internal_photos/bs/2020/V/q/33CD65RVK44W5BSLbx1g/rede-globo.png'
GLOBO_FANART = os.path.join(control.artPath(), 'globoplay_bg_fhd.png')
GLOBOPLAY_THUMB = os.path.join(control.artPath(), 'globoplay.png')

THUMB_URL = 'http://s01.video.glbimg.com/x1080/%s.jpg'

PLAYER_HANDLER = player.__name__

PAGE_SIZE = 100


def get_globoplay_channels():

    yield {
        'handler': __name__,
        'method': 'get_categories',
        "id": 196,
        "service_id": 4654,
        "adult": False,
        'art': {
            'thumb': GLOBO_LOGO_WHITE,
            'fanart': GLOBO_FANART
        },
        "label": 'Globo'
    }

    if control.is_globoplay_mais_canais_ao_vivo_available():
        if control.globoplay_ignore_channel_authorization() or auth_helper.is_service_allowed(auth_helper.CADUN_SERVICES.GSAT_CHANNELS):
            query = 'query%20getChannelsList%28%24page%3A%20Int%2C%20%24perPage%3A%20Int%29%20%7B%0A%20%20broadcastChannels%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%2C%20filtersInput%3A%20%7Bfilter%3A%20WITH_PAGES%7D%29%20%7B%0A%20%20%20%20page%0A%20%20%20%20perPage%0A%20%20%20%20hasNextPage%0A%20%20%20%20nextPage%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20pageIdentifier%0A%20%20%20%20%20%20payTvServiceId%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20logo%28format%3A%20PNG%29%0A%20%20%20%20%20%20color%0A%20%20%20%20%20%20requireUserTeam%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A'
            variables = '{"page":1, "perPage": 200}'

            query_response = request_query(query, variables)

            resources = query_response['data']['broadcastChannels']['resources']

            for broadcast in resources:
                if str(broadcast.get('id')) in ['196', '1995']:
                    continue

                yield {
                        'handler': __name__,
                        'method': 'get_page',
                        "id": broadcast.get('pageIdentifier'),
                        "type": 'CHANNELS',
                        "adult": False,
                        'art': {
                            'thumb': broadcast['logo'],
                            'fanart': GLOBO_FANART
                        },
                        'slug': broadcast['pageIdentifier'],
                        "label": broadcast['name']
                    }

        if control.globoplay_ignore_channel_authorization() or auth_helper.is_service_allowed(auth_helper.CADUN_SERVICES.PREMIERE):
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


def get_categories(page=1, per_page=PAGE_SIZE):
    home = 'home-assinante' if auth_helper.is_subscribed() else 'home-free' if auth_helper.is_logged_in() else 'home-anonimo'

    yield {
        'handler': __name__,
        'method': 'get_page',
        'id': home,
        'type': None,
        'label': control.lang(34135).encode('utf-8'),
        'art': {
            'thumb': GLOBOPLAY_THUMB,
            'fanart': GLOBO_FANART
        }
    }

    query = 'query%20getCategories%28%24page%3A%20Int%2C%20%24perPage%3A%20Int%29%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20categories%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20__typename%20hasNextPage%20nextPage%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20__typename%20name%20background%20navigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20__typename...on%20MenuSlugNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D...on%20MenuPageNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20identifier%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D'
    variables = '{{"page":{page},"perPage":{per_page}}}'.format(page=page, per_page=per_page)
    resources = request_query(query, variables).get('data', {}).get('categories', {}).get('resources', [])

    for resource in resources:
        yield {
            'handler': __name__,
            'method': 'get_page' if resource.get('navigation', {}).get('identifier') else 'get_affiliate_states',
            'id': resource.get('navigation', {}).get('identifier', ''),
            'label': resource.get('name', ''),
            'art': {
                'thumb': resource.get('background'),
                'fanart': resource.get('background', GLOBO_FANART)
            }
        }


def get_globoplay_home():
    home = 'home-assinante' if auth_helper.is_subscribed() else 'home-free' if auth_helper.is_logged_in() else 'home-anonimo'

    return get_page(home, type=None)


def get_page(id, art=None, type='CATEGORIES'):
    if art is None:
        art = {}

    type_str = ''
    if type:
        type_str = ',"type":"{type}"'.format(type=type)

    query = 'query%20getPage%28%24id%3A%20ID%21%2C%20%24subscriptionType%3A%20SubscriptionType%2C%20%24type%3A%20PageType%29%20%7B%0A%20%20page%28id%3A%20%24id%2C%20filter%3A%20%7BsubscriptionType%3A%20%24subscriptionType%2C%20type%3A%20%24type%7D%29%20%7B%0A%20%20%20%20...pageCollection%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0Afragment%20pageCollection%20on%20Page%20%7B%0A%20%20name%0A%20%20identifier%0A%20%20origemId%0A%20%20productId%0A%20%20premiumHighlight%20%7B%0A%20%20%20%20headline%0A%20%20%20%20fallbackHeadline%0A%20%20%20%20buttonText%0A%20%20%20%20callText%0A%20%20%20%20highlightId%0A%20%20%20%20highlight%20%7B%0A%20%20%20%20%20%20...highlightOffer%0A%20%20%20%20%7D%0A%20%20%20%20fallbackCallText%0A%20%20%20%20fallbackHighlightId%0A%20%20%20%20fallbackHighlight%20%7B%0A%20%20%20%20%20%20...highlightOffer%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20offerItems%20%7B%0A%20%20%20%20...%20on%20PageOffer%20%7B%0A%20%20%20%20%20%20title%0A%20%20%20%20%20%20componentType%0A%20%20%20%20%20%20playlistEnabled%0A%20%20%20%20%20%20navigation%20%7B%0A%20%20%20%20%20%20%20%20...%20on%20URLNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20url%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20...%20on%20CategoriesPageNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20identifier%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20offerId%0A%20%20%20%20%20%20genericOffer%20%7B%0A%20%20%20%20%20%20%20%20...%20on%20Offer%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20userBased%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20...%20on%20RecommendedOffer%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20PageHighlight%20%7B%0A%20%20%20%20%20%20callText%0A%20%20%20%20%20%20componentType%0A%20%20%20%20%20%20headline%0A%20%20%20%20%20%20highlightId%0A%20%20%20%20%20%20fallbackCallText%0A%20%20%20%20%20%20fallbackHeadline%0A%20%20%20%20%20%20fallbackHighlightId%0A%20%20%20%20%20%20leftAligned%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20highlightOffer%20on%20Highlight%20%7B%0A%20%20id%0A%20%20contentType%0A%20%20contentId%0A%20%20contentItem%20%7B%0A%20%20%20%20...%20on%20Video%20%7B%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20kind%0A%20%20%20%20%20%20broadcast%20%7B%0A%20%20%20%20%20%20%20%20mediaId%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20subset%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20Title%20%7B%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20type%0A%20%20%20%20%20%20headline%0A%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20subset%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20headlineText%0A%20%20headlineImage%0A%20%20highlightImage%20%7B%0A%20%20%20%20mobile%0A%20%20%20%20web%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20offerImage%20%7B%0A%20%20%20%20mobile%0A%20%20%20%20web%0A%20%20%7D%0A%7D'
    variables = '{{"id":"{id}"{type}}}'.format(id=id, type=type_str)
    page = request_query(query, variables).get('data', {}).get('page', {})

    if not page:
        return

    offers = list(filter(lambda x: filter_offers(x), page.get('offerItems', []) or []))
    premium = page.get('premiumHighlight', {}) or {}

    valid_premium = is_valid_highlight(premium)
    is_valid_premium = valid_premium[0]

    if len(offers) == 1 and not is_valid_premium:
        item = offers[0]
        return get_offer(item.get('offerId'), item.get('componentType'))

    return get_page_offers(offers, valid_premium, art, type)


def filter_offers(item):
    title = (item.get('title') or '').lower()
    headline = (item.get('headline') or '').lower()

    if item.get('componentType') in ['CHANNELSLOGO', 'TAKEOVER', 'SIMULCAST'] or title in ['assista ao vivo', 'categorias'] or headline.startswith('agora n') or title.startswith('agora n'):
        return False

    return True


def is_valid_highlight(premium):
    # content_type = "VIDEO", "SIMULCAST", "BACKGROUND"

    ignored_content_types = ['BACKGROUND', 'SIMULCAST']

    label = None
    plot = None
    highlight = {}
    if premium:
        highlight = premium.get('highlight', {}) or {}
        content_type = highlight.get('contentType')

        label = premium.get('headline')
        plot = premium.get('callText')

        if content_type in ignored_content_types:
            highlight = premium.get('fallbackHighlight', {}) or {}
            content_type = highlight.get('contentType')
            label = premium.get('fallbackHeadline')
            plot = premium.get('fallbackCallText')

        if highlight and content_type and content_type not in ignored_content_types:
            return True, highlight, label, plot

    return False, highlight, label, plot


def get_page_offers(offers, premium, art=None, type=None):
    is_valid_premium, highlight, label, plot = premium

    logo = art.get('thumb', GLOBO_LOGO_WHITE) if type == 'CHANNELS' else GLOBO_LOGO_WHITE

    if is_valid_premium:
        title_id = ((highlight.get('contentItem', {}) or {}).get('title', {}) or {}).get('titleId') or (highlight.get('contentItem', {}) or {}).get('titleId')
        yield {
            'handler': __name__,
            'method': 'get_title' if title_id else 'get_offer',
            'label': label or highlight.get('headlineText'),
            'id': title_id or highlight.get('contentId'),
            'availableFor': (highlight.get('contentItem', {}) or {}).get('availableFor'),
            'plot': plot,
            'component_type': 'OFFERHIGHLIGHT',  # 'PREMIUMHIGHLIGHT',
            'art': {
                'thumb': highlight.get('headlineImage') or (highlight.get('offerImage', {}) or {}).get('web') or logo,
                'fanart': (highlight.get('highlightImage', {}) or {}).get('web', art.get('fanart', GLOBO_FANART))
            }
        }

    for item in offers:
        yield {
                'handler': __name__,
                'method': 'get_offer',
                'label': item.get('title', item.get('headline', '')),
                'plot': item.get('callText'),
                'id': item.get('offerId') or item.get('highlightId'),
                'component_type': item.get('componentType'),
                'art': {
                    'thumb': logo,
                    'fanart': art.get('fanart', GLOBO_FANART)
                }
            }


def get_offer(id, component_type):
    if component_type == 'THUMB':
        return get_thumb_offer(id)

    if component_type == 'CONTINUEWATCHING':
        return get_continue_watching()

    if component_type == 'OFFERHIGHLIGHT':
        return get_offer_highlight(id)

    if component_type == 'CATEGORYBACKGROUND':
        return get_category_offer(id)

    # Default = POSTER
    return get_poster_offer(id)


def get_thumb_offer(id, page=1, per_page=PAGE_SIZE):
    query = 'query%20getOfferThumbById%28%24id%3A%20ID%21%2C%20%24page%3A%20Int%2C%20%24perPage%3A%20Int%2C%20%24context%3A%20RecommendedOfferContextInput%29%20%7B%0A%20%20genericOffer%28id%3A%20%24id%29%20%7B%0A%20%20%20%20...%20on%20Offer%20%7B%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20userBased%0A%20%20%20%20%20%20paginatedItems%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...videoFragment%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20RecommendedOffer%20%7B%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20items%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%2C%20context%3A%20%24context%29%20%7B%0A%20%20%20%20%20%20%20%20customTitle%0A%20%20%20%20%20%20%20%20abExperiment%20%7B%0A%20%20%20%20%20%20%20%20%20%20experiment%0A%20%20%20%20%20%20%20%20%20%20alternative%0A%20%20%20%20%20%20%20%20%20%20trackId%0A%20%20%20%20%20%20%20%20%20%20convertUrl%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...videoFragment%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A%0Afragment%20videoFragment%20on%20Video%20%7B%0A%20%20id%0A%20%20kind%0A%20%20headline%0A%20%20description%0A%20%20liveThumbnail%0A%20%20thumb%0A%20%20broadcast%20%7B%0A%20%20%20%20mediaId%0A%20%20%20%20trimmedLogo%28scale%3A%20X56%29%0A%20%20%20%20imageOnAir%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20payTvServiceId%0A%20%20%20%20%20%20trimmedLogo%28scale%3A%20X56%29%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20title%20%7B%0A%20%20%20%20titleId%0A%20%20%20%20originProgramId%0A%20%20%20%20headline%0A%20%20%20%20description%0A%20%20%20%20slug%0A%20%20%20%20releaseYear%0A%20%20%20%20contentRating%0A%20%20%20%20contentRatingCriteria%0A%20%20%20%20type%0A%20%20%20%20format%0A%20%20%20%20countries%0A%20%20%20%20directors%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%7D%0A%20%20%20%20cast%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%7D%0A%20%20%20%20genres%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%7D%0A%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20availableFor%0A%20%20serviceId%0A%20%20duration%0A%7D'
    variables = '{{"id":"{id}","page":{page},"perPage":{per_page}}}'.format(id=id, page=page, per_page=per_page)
    generic_offer = request_query(query, variables).get('data', {}).get('genericOffer', {})
    items = generic_offer.get('paginatedItems', generic_offer.get('items', {})) or {}

    custom_title = items.get('customTitle')

    resources = items.get('resources', []) or []

    if not control.globoplay_ignore_channel_authorization():
        service_ids = [item.get('serviceId') for item in resources]
        authorized_ids = get_authorized_services(service_ids)
        resources = [item for item in resources if item.get('serviceId') in authorized_ids and auth_helper.is_available_for(item.get('availableFor'))]

    for item in filter(__filter_plus, resources):
        yield {
                'handler': PLAYER_HANDLER,
                'method': 'play_stream',
                'IsPlayable': True,
                'custom_title': custom_title,
                'tagline': custom_title,
                'id': item.get('id'),
                'program_id': item.get('originProgramId', ''),
                'label': '%s: %s' % (item.get('title', {}).get('headline', ''), item.get('headline', '')),
                'title': item.get('headline', ''),
                'originaltitle': item.get('originalHeadline', ''),
                'tvshowtitle': item.get('title', {}).get('headline'),
                'duration': (item.get('duration', 0) or 0) / 1000,
                'year': item.get('title', {}).get('releaseYear', ''),
                'country': item.get('countries', []),
                'genre': item.get('genresNames', []),
                'cast': item.get('castNames', []),
                'director': item.get('directorsNames', []),
                'writer': item.get('screenwritersNames', []),
                'credits': item.get('artDirectorsNames', []),
                'mpaa': (item.get('title', {}) or {}).get('contentRating', ''),
                'plot': item.get('description', ''),
                'mediatype': 'video',
                # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
                'art': {
                    'thumb': item.get('thumb', GLOBOPLAY_THUMB),
                    'fanart': item.get('title', {}).get('cover', {}).get('web', GLOBO_FANART),
                    # 'poster': ((item.get('title', {}) or {}).get('poster', {}) or {}).get('web'),
                    'icon': ((item.get('title', {}) or {}).get('logo', {}) or {}).get('web'),
                }
            }

    if items.get('hasNextPage', False):
        yield {
            'handler': __name__,
            'method': 'get_thumb_offer',
            'id': id,
            'page': items.get('nextPage'),
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
            'art': {
                'poster': control.addonNext(),
                'fanart': GLOBO_FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def __filter_plus(item):
    if not item:
        return False

    if not control.is_globoplay_mais_canais_ao_vivo_available() or (not control.globoplay_ignore_channel_authorization() and not auth_helper.is_service_allowed(auth_helper.CADUN_SERVICES.GSAT_CHANNELS)):
        service_id = (item.get('channel', {}) or {}).get('payTvServiceId', '') or item.get('payTvServiceId', '') or ((item.get('broadcast', {}) or {}).get('channel', {}) or {}).get('payTvServiceId', '')
        return not service_id

    return True


def get_poster_offer(id, page=1, per_page=PAGE_SIZE):
    control.log('get_poster_offer: %s | page: %s' % (id, page))

    query = 'query%20getOffer%28%24id%3A%20ID%21%2C%20%24page%3A%20Int%2C%20%24perPage%3A%20Int%2C%20%24context%3A%20RecommendedOfferContextInput%29%20%7B%0A%20%20genericOffer%28id%3A%20%24id%29%20%7B%0A%20%20%20%20...%20on%20Offer%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20userBased%0A%20%20%20%20%20%20paginatedItems%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...titleHome%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20RecommendedOffer%20%7B%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20items%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%2C%20context%3A%20%24context%29%20%7B%0A%20%20%20%20%20%20%20%20customTitle%0A%20%20%20%20%20%20%20%20abExperiment%20%7B%0A%20%20%20%20%20%20%20%20%20%20experiment%0A%20%20%20%20%20%20%20%20%20%20alternative%0A%20%20%20%20%20%20%20%20%20%20trackId%0A%20%20%20%20%20%20%20%20%20%20convertUrl%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...titleHome%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20titleHome%20on%20Title%20%7B%0A%20%20originVideoId%0A%20%20titleId%0A%20%20type%0A%20%20originProgramId%0A%20%20headline%0A%20%20originalHeadline%0A%20%20description%0A%20%20slug%0A%20%20contentRating%0A%20%20contentRatingCriteria%0A%20%20releaseYear%0A%20%20format%0A%20%20countries%0A%20%20genresNames%0A%20%20directorsNames%0A%20%20artDirectorsNames%0A%20%20authorsNames%0A%20%20castNames%0A%20%20screenwritersNames%0A%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20poster%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20slug%0A%20%20%7D%0A%7D'
    variables = '{{"id":"{id}","page":{page},"perPage":{perPage}}}'.format(id=id, page=page, perPage=per_page)

    generic_offer = request_query(query, variables).get('data', {}).get('genericOffer', {}) or {}
    items = generic_offer.get('paginatedItems', generic_offer.get('items', {})) or {}

    custom_title = items.get('customTitle')

    for resource in items.get('resources', []) or []:
        playable = True if resource.get('originVideoId') else False
        yield {
            'handler': PLAYER_HANDLER if playable else __name__,
            'method': 'play_stream' if playable else 'get_title',
            'id': resource.get('originVideoId', resource.get('titleId')) or resource.get('titleId'),
            'program_id': resource.get('originProgramId'),
            'IsPlayable': playable,
            'custom_title': custom_title,
            'tagline': custom_title,
            # 'type': resource.get('type'),
            'label': resource.get('headline', ''),
            'title': resource.get('headline', ''),
            'originaltitle': resource.get('originalHeadline', ''),
            'studio': resource.get('channel', {}).get('name'),
            'year': resource.get('releaseYear', ''),
            'country': resource.get('countries', []),
            'genre': resource.get('genresNames', []),
            'cast': resource.get('castNames', []),
            'director': resource.get('directorsNames', []),
            'writer': resource.get('screenwritersNames', []),
            'credits': resource.get('artDirectorsNames', []),
            'tag': resource.get('contentRatingCriteria'),
            'mpaa': resource.get('contentRating', ''),
            'plot': resource.get('description', ''),
            'mediatype': 'movie' if resource.get('type', '') == 'MOVIE' else 'tvshow',
            # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            'art': {
                'poster': resource.get('poster', {}).get('web'),
                'clearlogo': resource.get('logo', {}).get('web'),
                'fanart': resource.get('cover', {}).get('web', GLOBO_FANART)
            }
        }

    if items.get('hasNextPage', False):
        yield {
            'handler': __name__,
            'method': 'get_poster_offer',
            'id': id,
            'page': items.get('nextPage'),
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
            'art': {
                'poster': control.addonNext(),
                'fanart': GLOBO_FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_title(id, season=None, page=1, per_page=PAGE_SIZE):
    if not id:
        return

    control.log('get_title: %s | page %s' % (id, page))
    variables = '{{"titleId":"{id}", "episodeTitlePage": {page}, "episodeTitlePerPage": {per_page}, "userIsLoggedIn": true}}'.format(id=id, page=page, per_page=per_page)
    query = 'query%20getTitleFavorited%28%24titleId%3A%20String%2C%20%24episodeTitlePage%3A%20Int%2C%20%24episodeTitlePerPage%3A%20Int%2C%20%24userIsLoggedIn%3A%20Boolean%21%29%20%7B%0A%20%20title%28titleId%3A%20%24titleId%29%20%7B%0A%20%20%20%20...titleFragment%0A%20%20%20%20...continueWatchingTitleFragment%0A%20%20%20%20favorited%0A%20%20%7D%0A%7D%0Afragment%20titleFragment%20on%20Title%20%7B%0A%20%20titleId%0A%20%20slug%0A%20%20headline%0A%20%20originalHeadline%0A%20%20description%0A%20%20originVideoId%0A%20%20originProgramId%0A%20%20type%0A%20%20format%0A%20%20contentRating%0A%20%20contentRatingCriteria%0A%20%20releaseYear%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20slug%0A%20%20%7D%0A%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20poster%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20countries%0A%20%20genresNames%0A%20%20directorsNames%0A%20%20artDirectorsNames%0A%20%20authorsNames%0A%20%20castNames%0A%20%20screenwritersNames%0A%20%20extras%20%7B%0A%20%20%20%20%20%20editorialOffers%20%7B%0A%20%20%20%20%20%20%20%20...%20on%20PageOffer%20%7B%0A%20%20%20%20%20%20%20%20%20%20offerId%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20structure%20%7B%0A%20%20%20%20%20%20...seasonedStructureFragment%0A%20%20%20%20%20%20...filmPlaybackStructureFragment%0A%20%20%20%20%20%20...episodeListStructureFragment%0A%20%20%20%20%7D%0A%7D%0Afragment%20seasonedStructureFragment%20on%20SeasonedStructure%20%7B%0A%20%20seasons%20%7B%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20number%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20totalEpisodes%0A%20%20%20%20%20%20episodes%28page%3A%20%24episodeTitlePage%2C%20perPage%3A%20%24episodeTitlePerPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20number%0A%20%20%20%20%20%20%20%20%20%20seasonNumber%0A%20%20%20%20%20%20%20%20%20%20seasonId%0A%20%20%20%20%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20%20%20exhibitedAt%0A%20%20%20%20%20%20%20%20%20%20%20%20encrypted%0A%20%20%20%20%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20seasonsWithExcerpts%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20number%0A%20%20%20%20%20%20%20%20%20%20totalEpisodes%0A%20%20%20%20%20%20%20%20%7D%0A%7D%0Afragment%20filmPlaybackStructureFragment%20on%20FilmPlaybackStructure%20%7B%0A%20%20videoPlayback%20%7B%0A%20%20%20%20id%0A%20%20%20%20exhibitedAt%0A%20%20%20%20encrypted%0A%20%20%20%20availableFor%0A%20%20%20%20headline%0A%20%20%20%20description%0A%20%20%20%20thumb%0A%20%20%20%20duration%0A%20%20%7D%0A%7D%0Afragment%20episodeListStructureFragment%20on%20EpisodeListStructure%20%7B%0A%20%20episodes%28page%3A%20%24episodeTitlePage%2C%20perPage%3A%20%24episodeTitlePerPage%29%20%7B%0A%20%20%20%20page%0A%20%20%20%20hasNextPage%0A%20%20%20%20nextPage%0A%20%20%20%20total%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20number%0A%20%20%20%20%20%20seasonNumber%0A%20%20%20%20%20%20seasonId%0A%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20exhibitedAt%0A%20%20%20%20%20%20%20%20encrypted%0A%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20excerpts%28page%3A%20%24episodeTitlePage%2C%20perPage%3A%20%24episodeTitlePerPage%29%20%7B%0A%20%20%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20%20%20total%0A%20%20%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20%20%20exhibitedAt%0A%20%20%20%20%20%20%20%20%20%20%20%20encrypted%0A%20%20%20%20%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%7D%0Afragment%20continueWatchingTitleFragment%20on%20Title%20%7B%0A%20%20structure%20%7B%0A%20%20%20%20...%20on%20SeasonedStructure%20%7B%0A%20%20%20%20%20%20continueWatching%20%40include%28if%3A%20%24userIsLoggedIn%29%20%7B%0A%20%20%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20%20%20...continueWatchingVideoFragment%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20FilmPlaybackStructure%20%7B%0A%20%20%20%20%20%20continueWatching%20%40include%28if%3A%20%24userIsLoggedIn%29%20%7B%0A%20%20%20%20%20%20%20%20...continueWatchingVideoFragment%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20EpisodeListStructure%20%7B%0A%20%20%20%20%20%20continueWatching%20%40include%28if%3A%20%24userIsLoggedIn%29%20%7B%0A%20%20%20%20%20%20%20%20video%20%7B%0A%20%20%20%20%20%20%20%20%20%20...continueWatchingVideoFragment%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20continueWatchingVideoFragment%20on%20Video%20%7B%0A%20%20id%0A%20%20headline%0A%20%20description%0A%20%20watchedProgress%0A%20%20duration%0A%20%20contentRating%0A%20%20contentRatingCriteria%0A%7D'
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
            'method': 'play_stream',
            'id': video.get('id', ''),
            'program_id': title.get('originProgramId'),
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
            'context_menu': [('Adicionar a minha lista', control.run_plugin_url({'action': 'addFavorites'}))] if not is_favorite else [('Remover da minha lista', control.run_plugin_url({'action': 'addFavorites'}))],
            'art': {
                'clearlogo': title.get('logo', {}).get('web'),
                'poster': title.get('poster', {}).get('web'),
                'fanart': title.get('cover', {}).get('landscape', GLOBO_FANART)
            }
        }

    elif 'episodes' in structure:
        episodes = structure.get('episodes', {})
        page = episodes.get('nextPage', 0) if episodes.get('hasNextPage', False) else 0

        resources = episodes.get('resources', []) or []

        if not resources:
            excerpts = structure.get('excerpts', {}) or {}
            page = excerpts.get('nextPage', 0) if excerpts.get('hasNextPage', False) else 0
            resources = excerpts.get('resources', []) or []

        for resource in resources:
            video = resource.get('video', resource)

            yield {
                'handler': PLAYER_HANDLER,
                'method': 'play_stream',
                'IsPlayable': True,
                'id': video.get('id'),
                'program_id': title.get('originProgramId'),
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
                    'fanart': title.get('cover', {}).get('landscape', GLOBO_FANART),
                    'tvshow.poster': title.get('poster', {}).get('web'),
                },
                'sort': control.SORT_METHOD_EPISODE if resource.get('number') and resource.get('seasonNumber') else None
            }

    elif 'seasons' in structure:

        seasons = structure.get('seasons', {}).get('resources', [])
        if len(seasons) == 1 or season:

            season_resource = next((s for s in structure.get('seasons', {}).get('resources', []) if s.get('number', 0) == season), seasons[0])

            if not season_resource:
                return

            for episode in season_resource.get('episodes', {}).get('resources', []):
                video = episode.get('video', {})
                yield {
                        'handler': PLAYER_HANDLER,
                        'method': 'play_stream',
                        'IsPlayable': True,
                        'id': video.get('id'),
                        'program_id': title.get('originProgramId'),
                        'label': video.get('headline', ''),
                        'title': video.get('headline', ''),
                        'originaltitle': video.get('originalHeadline', ''),
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
                        'dateadded': video.get('exhibitedAt', '').replace('Z', '').replace('T', ' '),
                        'aired': (video.get('exhibitedAt', '') or '').split('T')[0],
                        'sort': control.SORT_METHOD_EPISODE,
                        'art': {
                            'thumb': video.get('thumb'),
                            'fanart': title.get('cover', {}).get('landscape', GLOBO_FANART),
                            'tvshow.poster': title.get('poster', {}).get('web'),
                        }
                    }
        else:
            for season in structure.get('seasons', {}).get('resources', []):
                yield {
                    'handler': __name__,
                    'method': 'get_title',
                    'id': id,
                    'label': '%s %s' % (control.lang(34137).encode('utf-8'), season.get('number', 0)),
                    'season': season.get('number', 0),
                    'title': title.get('headline'),
                    'tvshowtitle': title.get('headline'),
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
                    'mediatype': 'season',
                    'art': {
                        'clearlogo': title.get('logo', {}).get('web'),
                        'poster': title.get('poster', {}).get('web'),
                        'fanart': title.get('cover', {}).get('landscape', GLOBO_FANART)
                    }
                }

    else:
        control.log('[globoplay] - unsupported structure: %s' % structure)

    if page > 0:
        yield {
            'handler': __name__,
            'method': 'get_title',
            'id': id,
            'page': page,
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
            'art': {
                'poster': control.addonNext(),
                'fanart': GLOBO_FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_continue_watching(page=1, per_page=PAGE_SIZE):
    query = 'query%20getContinueWatching%28%24page%3A%20Int%2C%20%24perPage%3A%20Int%29%20%7B%0A%20%20user%20%7B%0A%20%20%20%20myLastWatchedVideos%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20kind%0A%20%20%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20%20%20thumb%0A%20%20%20%20%20%20%20%20duration%0A%20%20%20%20%20%20%20%20formattedDuration%0A%20%20%20%20%20%20%20%20watchedProgress%0A%20%20%20%20%20%20%20%20serviceId%0A%20%20%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20%20%20format%0A%20%20%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20%20%20directors%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20cast%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20genres%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    variables = '{{"page":{page},"perPage":{per_page}}}'.format(page=page, per_page=per_page)
    result = request_query(query, variables) or {}

    data = result.get('data', {}) or {}
    user = data.get('user', {}) or {}
    my_last_watched_videos = user.get('myLastWatchedVideos', {}) or {}
    resources = my_last_watched_videos.get('resources', []) or []

    for resource in resources:
        title = resource.get('title', {}) or {}
        yield {
                'handler': PLAYER_HANDLER,
                'method': 'play_stream',
                'id': resource.get('id'),
                'program_id': title.get('originProgramId'),
                'type': (resource.get('title', {}) or {}).get('type'),
                'label': resource.get('headline', ''),
                'title': resource.get('headline', ''),
                'tvshowtitle': title.get('headline', ''),
                'duration': resource.get('duration', 0) / 1000,
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
                'plot': resource.get('description', ''),
                'mediatype': 'episode' if resource.get('kind', '') == 'episode' else 'movie' if title.get('type', '') == 'MOVIE' else 'tvshow',
                # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
                'art': {
                    'thumb': resource.get('thumb'),
                    # 'poster': title.get('poster', {}) or {}).get('web'),
                    'clearicon': (title.get('logo', {}) or {}).get('web'),
                    'fanart': (title.get('cover', {}) or {}).get('web', GLOBO_FANART),
                },
                'properties': {
                    'resumetime': str(resource.get('watchedProgress', 0) / 1000)
                }
            }


def get_offer_highlight(id):
    query = 'query%20getHighlight%28%24id%3A%20ID%21%2C%20%24fallbackHighlightId%3A%20ID%20%3D%20%22%22%2C%20%24shouldFetchFallback%3A%20Boolean%20%3D%20false%29%20%7B%0A%20%20highlight%3A%20highlight%28id%3A%20%24id%29%20%7B%0A%20%20%20%20...highlightOffer%0A%20%20%7D%0A%20%20fallbackHighlight%3A%20highlight%28id%3A%20%24fallbackHighlightId%29%20%40include%28if%3A%20%24shouldFetchFallback%29%20%7B%0A%20%20%20%20...highlightOffer%0A%20%20%7D%0A%7D%0Afragment%20highlightOffer%20on%20Highlight%20%7B%0A%20%20id%0A%20%20contentType%0A%20%20contentId%0A%20%20contentItem%20%7B%0A%20%20%20%20...%20on%20Video%20%7B%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20kind%0A%20%20%20%20%20%20broadcast%20%7B%0A%20%20%20%20%20%20%20%20mediaId%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20originalHeadline%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20originVideoId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20format%0A%20%20%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20subset%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20Title%20%7B%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20originalHeadline%0A%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20originVideoId%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20format%0A%20%20%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20subset%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20headlineText%0A%20%20headlineImage%0A%20%20highlightImage%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20offerImage%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%7D'
    variables = '{{"fallbackHighlightId":null,"shouldFetchFallback":false,"id":"{id}"}}'.format(id=id)
    item = ((request_query(query, variables).get('data', {}) or {}).get('highlight', {}) or {}).get('contentItem', {}) or {}

    title = item.get('title', item) or item

    playable = True if title.get('originVideoId') else False
    yield {
        'handler': PLAYER_HANDLER if playable else __name__,
        'method': 'play_stream' if playable else 'get_title',
        'id': title.get('originVideoId', title.get('titleId')) or title.get('titleId'),
        'program_id': title.get('originProgramId'),
        'IsPlayable': playable,
        # 'type': resource.get('type'),
        'label': title.get('headline', ''),
        'title': title.get('headline', ''),
        'studio': title.get('channel', {}).get('name'),
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
            'fanart': title.get('cover', {}).get('web', GLOBO_FANART)
        }
    }


def get_affiliate_states(art=None):
    if art is None:
        art = {}

    query = 'query%20getAffiliateStates%20%7B%0A%20%20%20%20%20%20affiliate%20%7B%0A%20%20%20%20%20%20%20%20affiliateStates%20%7B%0A%20%20%20%20%20%20%20%20%20%20acronym%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20regions%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D'
    variables = '{}'
    states = request_query(query, variables).get('data', {}).get('affiliate', {}).get('affiliateStates', [])

    for state in states:
        yield {
            'handler': __name__,
            'method': 'get_regions',
            'label': '%s (%s)' % (state.get('name', ''), state.get('acronym', '')),
            'acronym': state.get('acronym', ''),
            'art': {
                'thumb': GLOBO_LOGO_WHITE,
                'fanart': art.get('fanart', GLOBO_FANART)
            }
        }


def get_regions(acronym, art=None):
    if art is None:
        art = {}

    query = 'query%20getAffiliateStates%20%7B%0A%20%20%20%20%20%20affiliate%20%7B%0A%20%20%20%20%20%20%20%20affiliateStates%20%7B%0A%20%20%20%20%20%20%20%20%20%20acronym%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20regions%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20affiliateName%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D'
    variables = '{}'
    states = request_query(query, variables).get('data', {}).get('affiliate', {}).get('affiliateStates', [])

    for state in states:
        if state.get('acronym', '') == acronym:
            regions = state.get('regions', [])
            if len(regions) == 1:
                region = regions[0]
                label = '%s (%s)' % (region.get('name', ''), region.get('affiliateName', '')) if region.get('affiliateName', '') else region.get('name', '')
                return get_affiliate_region(region.get('slug'), region.get('affiliateName', region.get('name', '')))
            else:
                return _iterate_regions(regions, art)


def _iterate_regions(regions, art):

    for region in regions:
        label = '%s (%s)' % (region.get('name', ''), region.get('affiliateName', '')) if region.get('affiliateName', '') else region.get('name', '')
        yield {
            'handler': __name__,
            'method': 'get_affiliate_region',
            'label': label,
            'affiliate_name': region.get('affiliateName', region.get('name')),
            'slug': region.get('slug', ''),
            'art': {
                'thumb': GLOBO_LOGO_WHITE,
                'fanart': art.get('fanart', GLOBO_FANART)
            }
        }


def get_affiliate_region(slug, affiliate_name=None, page=1, per_page=PAGE_SIZE):
    query = 'query%20getAffiliateRegion%28%24regionSlug%3A%20String%21%2C%20%24page%3A%20Int%21%2C%20%24perPage%3A%20Int%21%29%20%7B%0A%20%20affiliate%20%7B%0A%20%20%20%20affiliateRegion%28regionSlug%3A%20%24regionSlug%29%20%7B%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20affiliateName%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20state%20%7B%0A%20%20%20%20%20%20%20%20acronym%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20titles%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20%20%20originalHeadline%0A%20%20%20%20%20%20%20%20%20%20description%0A%20%20%20%20%20%20%20%20%20%20originVideoId%0A%20%20%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20%20%20format%0A%20%20%20%20%20%20%20%20%20%20contentRating%0A%20%20%20%20%20%20%20%20%20%20contentRatingCriteria%0A%20%20%20%20%20%20%20%20%20%20releaseYear%0A%20%20%20%20%20%20%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20web%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20countries%0A%20%20%20%20%20%20%20%20%20%20genresNames%0A%20%20%20%20%20%20%20%20%20%20directorsNames%0A%20%20%20%20%20%20%20%20%20%20artDirectorsNames%0A%20%20%20%20%20%20%20%20%20%20authorsNames%0A%20%20%20%20%20%20%20%20%20%20castNames%0A%20%20%20%20%20%20%20%20%20%20screenwritersNames%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    variables = '{{"regionSlug":"{slug}","page":{page},"perPage":{per_page}}}'.format(slug=slug, page=page, per_page=per_page)
    affiliate_region = request_query(query, variables).get('data', {}).get('affiliate', {}).get('affiliateRegion', {}) or {}

    resources = (affiliate_region.get('titles', {}) or {}).get('resources', [])
    for title in resources:
        playable = True if title.get('originVideoId') else False
        yield {
                'handler': PLAYER_HANDLER if playable else __name__,
                'method': 'play_stream' if playable else 'get_title',
                'id': title.get('originVideoId', title.get('titleId')) or title.get('titleId'),
                'program_id': title.get('originProgramId'),
                'IsPlayable': playable,
                'custom_title': affiliate_name,
                'label': title.get('headline', ''),
                'title': title.get('headline', ''),
                'studio': title.get('channel', {}).get('name'),
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
                    'fanart': title.get('cover', {}).get('landscape', GLOBO_FANART)
                }
            }


# CATEGORYBACKGROUND
def get_category_offer(id, page=1, per_page=PAGE_SIZE):
    query = 'query%20getOfferCategoryById%28%24id%3A%20ID%21%2C%20%24page%3A%20Int%2C%20%24perPage%3A%20Int%29%20%7B%0A%20%20genericOffer%28id%3A%20%24id%29%20%7B%0A%20%20%20%20...%20on%20Offer%20%7B%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20userBased%0A%20%20%20%20%20%20paginatedItems%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...%20on%20Category%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20background%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%20%20navigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20...%20on%20MenuSlugNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20...%20on%20MenuPageNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20identifier%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D'
    variables = '{{"id":"{id}","page":{page},"perPage":{per_page}}}'.format(id=id, page=page, per_page=per_page)
    page = request_query(query, variables).get('data', {}).get('genericOffer', {}).get('paginatedItems', {})

    for resource in page.get('resources', []):
        yield {
                'handler': __name__,
                'method': 'get_page' if resource.get('navigation', {}).get('identifier') else 'get_affiliate_states',
                'id': resource.get('navigation', {}).get('identifier', ''),
                'label': resource.get('name', ''),
                'art': {
                    'thumb': resource.get('background'),
                    'fanart': resource.get('background')
                }
            }

    if page.get('hasNextPage', False):
        yield {
            'handler': __name__,
            'method': 'get_category_offer',
            'id': id,
            'page': page.get('nextPage'),
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
            'art': {
                'poster': control.addonNext(),
                'fanart': GLOBO_FANART
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

    provider = u'Globoplay'

    for title in titles.get('resources', []):
        playable = True if title.get('originVideoId') else False
        yield {
                'handler': PLAYER_HANDLER if playable else __name__,
                'method': 'play_stream' if playable else 'get_title',
                'id': title.get('originVideoId', title.get('titleId')) or title.get('titleId'),
                'program_id': title.get('originProgramId'),
                'IsPlayable': playable,
                'label': title.get('headline', ''),
                'title': title.get('headline', ''),
                'studio': provider, #title.get('channel', {}).get('name', provider),
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
                    'thumb': title.get('poster', {}).get('web'),
                    'tvshow.poster': title.get('poster', {}).get('web'),
                    'clearlogo': title.get('logo', {}).get('web'),
                    'fanart': title.get('cover', {}).get('web', GLOBO_FANART)
                }
            }

    videos = response.get('videos', {})

    for video in videos.get('resources', []):
        title = video.get('title', {})
        yield {
                'handler': PLAYER_HANDLER,
                'method': 'play_stream',
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
                'aired': (video.get('exhibitedAt', '') or '').split('T')[0],
                'mediatype': 'episode',
                # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
                'art': {
                    'thumb': video.get('thumb', GLOBO_FANART) or GLOBO_FANART,
                    'tvshow.poster': title.get('poster', {}).get('web'),
                    'clearlogo': (title.get('logo', {}) or {}).get('web'),
                    'fanart': (title.get('cover', {}) or {}).get('web', GLOBO_FANART)
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
                'fanart': GLOBO_FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def add_to_my_list(id):
    url = 'https://jarvis.globo.com/graphql'
    post = {
            "operationName": "addTitleToMyList",
            "variables": {
                "titleId": id
            },
            "query": "mutation addTitleToMyList($titleId: ID) { addTitleToMyList(input: {titleId: $titleId}) }"
        }

    return requests.post(url, json=post, headers=get_headers())


def remove_from_my_list(id):
    url = 'https://jarvis.globo.com/graphql'
    post = {
            "operationName": "deleteTitleFromMyList",
            "variables": {
                "titleId": id
            },
            "query": "mutation deleteTitleFromMyList($titleId: ID) { deleteTitleFromMyList(input: {titleId: $titleId}) }"
        }

    return requests.post(url, json=post, headers=get_headers())


def get_similar_offer(id, group, format):
    query = 'querygetSuggestByGroupAndFormatAndTitleId($group:SuggestGroups,$format:TitleFormat,$titleId:ID){user{suggest{bestFit(group:$group,relatedInfoInput:{format:$format,titleId:$titleId}){resource{...onOffer{idofferType:contentType}...onRecommendedOffer{idofferType:contentType}}}}}}'
    # variables = '{{"group":"TITLE_SCREEN","format":"LONG","titleId":"n1QzXpvMmS"}}'
    variables = '{{"group":"{group}","format":"{format}","titleId":"{id}"}}'.format(id=id, group=group, format=format)

    response = request_query(query, variables)

    resource = ((((response.get('data', {}) or {}).get('user', {}) or {}).get('suggest', {}) or {}).get('bestFit', {}) or {}).get('resource', {}) or {}

    return get_offer(resource.get('id'), resource.get('offerType'))
