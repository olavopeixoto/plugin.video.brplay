# -*- coding: utf-8 -*-

import os
from resources.lib.modules import control
from resources.lib.modules.sexyhotplay import request_query
from resources.lib.modules.globosat import player

artPath = control.artPath()
LOGO = os.path.join(artPath, 'logo_sexyhot.png')
FANART = os.path.join(artPath, 'fanart_sexyhot.png')
NEXT_ICON = os.path.join(control.artPath(), 'next.png')

PLAYER_HANDLER = player.__name__


def get_channels():

    return [{
        'handler': __name__,
        'method': 'get_categories',
        'label': 'Sexyhot',
        'art': {
            'thumb': LOGO,
            'fanart': FANART,
        }
    }]


def get_categories():

    yield {
        'handler': __name__,
        'method': 'get_home',
        'label': control.lang(34135).encode('utf-8'),
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }

    yield {
        'handler': __name__,
        'method': 'get_videos',
        'label': u'+ Vídeos',
        'slug': 'mais-videos',
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }

    yield {
        'handler': __name__,
        'method': 'get_videos',
        'label': u'Originais',
        'plot': u'O Sexy Hot Produções é o nosso selo de filmes próprios e exclusivos de alta qualidade.',
        'slug': 'originais',
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }

    yield {
        'handler': __name__,
        'method': 'get_genres',
        'id': '4828a3a4-1c97-4e27-86b5-3e8a872152f1',
        'label': u'Categorias',
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }

    yield {
        'handler': __name__,
        'method': 'get_genres',
        'id': 'b9d07874-d4fc-491b-979e-6c9d2fb11bff',
        'label': u'Porn Stars',
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }

    yield {
        'handler': __name__,
        'method': 'get_videos',
        'label': u'Filmes',
        'slug': 'filmes',
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }

    yield {
        'handler': __name__,
        'method': 'get_videos',
        'label': u'Séries',
        'plot': 'Confira todas as séries do Sexy Hot.',
        'slug': 'series',
        'art': {
            'thumb': LOGO,
            'fanart': FANART
        }
    }


def get_home():
    query = 'query%20getPage%28%24id%3A%20ID%21%2C%20%24subscriptionType%3A%20SubscriptionType%2C%20%24type%3A%20PageType%29%20%7B%0A%20%20page%28id%3A%20%24id%2C%20filter%3A%20%7BsubscriptionType%3A%20%24subscriptionType%2C%20type%3A%20%24type%7D%29%20%7B%0A%20%20%20%20...pageCollection%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0Afragment%20pageCollection%20on%20Page%20%7B%0A%20%20name%0A%20%20identifier%0A%20%20origemId%0A%20%20productId%0A%20%20premiumHighlight%20%7B%0A%20%20%20%20headline%0A%20%20%20%20fallbackHeadline%0A%20%20%20%20buttonText%0A%20%20%20%20callText%0A%20%20%20%20highlightId%0A%20%20%20%20highlight%20%7B%0A%20%20%20%20%20%20...highlightOffer%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20fallbackCallText%0A%20%20%20%20fallbackHighlightId%0A%20%20%20%20fallbackHighlight%20%7B%0A%20%20%20%20%20%20...highlightOffer%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20offerItems%20%7B%0A%20%20%20%20...%20on%20PageOffer%20%7B%0A%20%20%20%20%20%20title%0A%20%20%20%20%20%20componentType%0A%20%20%20%20%20%20playlistEnabled%0A%20%20%20%20%20%20navigation%20%7B%0A%20%20%20%20%20%20%20%20...%20on%20URLNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20url%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20...%20on%20CategoriesPageNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20identifier%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20offerId%0A%20%20%20%20%20%20genericOffer%20%7B%0A%20%20%20%20%20%20%20%20...%20on%20Offer%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20userBased%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20...%20on%20RecommendedOffer%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20PageHighlight%20%7B%0A%20%20%20%20%20%20callText%0A%20%20%20%20%20%20componentType%0A%20%20%20%20%20%20headline%0A%20%20%20%20%20%20highlightId%0A%20%20%20%20%20%20fallbackCallText%0A%20%20%20%20%20%20fallbackHeadline%0A%20%20%20%20%20%20fallbackHighlightId%0A%20%20%20%20%20%20leftAligned%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20__typename%0A%7D%0Afragment%20highlightOffer%20on%20Highlight%20%7B%0A%20%20id%0A%20%20contentType%0A%20%20contentId%0A%20%20contentItem%20%7B%0A%20%20%20%20...%20on%20Video%20%7B%0A%20%20%20%20%20%20availableFor%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20kind%0A%20%20%20%20%20%20broadcast%20%7B%0A%20%20%20%20%20%20%20%20mediaId%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20title%20%7B%0A%20%20%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20subset%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20Title%20%7B%0A%20%20%20%20%20%20titleId%0A%20%20%20%20%20%20slug%0A%20%20%20%20%20%20type%0A%20%20%20%20%20%20headline%0A%20%20%20%20%20%20originProgramId%0A%20%20%20%20%20%20subset%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20headlineText%0A%20%20headlineImage%0A%20%20highlightImage%20%7B%0A%20%20%20%20mobile%0A%20%20%20%20web%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20offerImage%20%7B%0A%20%20%20%20mobile%0A%20%20%20%20web%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20__typename%0A%7D%0A'
    variables = '{"id":"explore"}'
    response = request_query(query, variables) or {}

    for item in response.get('data', {}).get('page', {}).get('offerItems', []):
        if item.get('componentType', None) == 'TAKEOVER':
            continue

        yield {
            'handler': __name__,
            'method': 'get_offer',
            'label': item.get('callText', item.get('headline', item.get('title', ''))),
            'id': item.get('offerId', item.get('highlightId', None)),
            'component_type': item.get('componentType', None),
            'art': {
                'thumb': LOGO,
                'fanart': FANART
            }
        }


def get_offer_id(slug):
    query = 'query%20getPageOffers(%24id%3A%20ID!%2C%20%24filter%3A%20PageType)%20%7B%0A%20%20page%3A%20page(id%3A%20%24id%2C%20filter%3A%20%7Btype%3A%20%24filter%7D)%20%7B%0A%20%20%20%20origemId%0A%20%20%20%20productId%0A%20%20%20%20offerItems%20%7B%0A%20%20%20%20%20%20...%20on%20PageOffer%20%7B%0A%20%20%20%20%20%20%20%20offerId%0A%20%20%20%20%20%20%20%20title%0A%20%20%20%20%20%20%20%20navigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20...%20on%20URLNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20url%0A%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20...%20on%20CategoriesPageNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20identifier%0A%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20componentType%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20...%20on%20PageHighlight%20%7B%0A%20%20%20%20%20%20%20%20highlightId%0A%20%20%20%20%20%20%20%20headline%0A%20%20%20%20%20%20%20%20callText%0A%20%20%20%20%20%20%20%20leftAligned%0A%20%20%20%20%20%20%20%20componentType%0A%20%20%20%20%20%20%20%20fallbackHighlightId%0A%20%20%20%20%20%20%20%20fallbackHeadline%0A%20%20%20%20%20%20%20%20fallbackCallText%0A%20%20%20%20%20%20%20%20highlight%20%7B%0A%20%20%20%20%20%20%20%20%20%20...OfferHighlightFragment%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A%0Afragment%20OfferHighlightFragment%20on%20Highlight%20%7B%0A%20%20contentId%0A%20%20contentType%0A%20%20headlineText%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20highlightImage%20%7B%0A%20%20%20%20web%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20offerImage%20%7B%0A%20%20%20%20web%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20contentItem%20%7B%0A%20%20%20%20...OfferTitleFragment%0A%20%20%20%20...OfferVideoFragment%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20__typename%0A%7D%0A%0Afragment%20OfferVideoFragment%20on%20Video%20%7B%0A%20%20id%0A%20%20availableFor%0A%20%20headline%0A%20%20kind%0A%20%20thumb%0A%20%20title%20%7B%0A%20%20%20%20titleId%0A%20%20%20%20headline%0A%20%20%20%20slug%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20__typename%0A%7D%0A%0Afragment%20OfferTitleFragment%20on%20Title%20%7B%0A%20%20titleId%0A%20%20headline%0A%20%20poster%20%7B%0A%20%20%20%20web%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20__typename%0A%7D%0A'
    variables = '{{"id":"{slug}","filter":"CATEGORIES"}}'.format(slug=slug)
    response = request_query(query, variables) or {}
    data = response.get('data', {}) or {}
    page_data = data.get('page', {}) or {}
    item = next((item for item in page_data.get('offerItems', [])), {})

    return item.get('offerId', None), item.get('componentType', None)


def get_genres(id, page=1):
    query = 'query%20allCategoriesQuery(%24page%3A%20Int%2C%20%24perPage%3A%20Int%2C%20%24parentCategoryId%3A%20ID)%20%7B%0A%20%20categories(page%3A%20%24page%2C%20perPage%3A%20%24perPage%2C%20parentCategoryId%3A%20%24parentCategoryId)%20%7B%0A%20%20%20%20page%0A%20%20%20%20hasNextPage%0A%20%20%20%20nextPage%0A%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20background%0A%20%20%20%20%20%20navigation%20%7B%0A%20%20%20%20%20%20%20%20...%20on%20MenuSlugNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20...%20on%20MenuPageNavigation%20%7B%0A%20%20%20%20%20%20%20%20%20%20identifier%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A'
    variables = '{{"page":{page},"perPage":200,"parentCategoryId":"{id}"}}'.format(page=page, id=id)
    response = request_query(query, variables) or {}

    categories = response.get('data', {}).get('categories', {})

    resources = categories.get('resources', [])

    for resource in resources:

        yield {
            'handler': __name__,
            'method': 'get_videos',
            'label': resource.get('name', ''),
            'slug': resource.get('navigation', {}).get('identifier', None),
            'art': {
                'thumb': resource.get('background', LOGO),
                'fanart': FANART
            }
        }

    if categories.get('hasNextPage', False):

        yield {
                'handler': __name__,
                'method': 'get_genres',
                'page': categories.get('nextPage'),
                'id': id,
                'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page),
                'art': {
                    'poster': NEXT_ICON,
                    'fanart': FANART
                },
                'properties': {
                    'SpecialSort': 'bottom'
                }
            }


def get_videos(slug):

    id, component_type = get_offer_id(slug)

    if not id or not component_type:
        return

    return get_offer(id, component_type)


def get_offer(id, component_type):

    if component_type == 'THUMB':
        return get_thumb_offer(id)

    if component_type == 'CONTINUEWATCHING':
        return get_continue_watching()

    if component_type == 'OFFERHIGHLIGHT':
        return get_offer_highlight(id)

    # Default = POSTER
    return get_poster_offer(id)


def get_thumb_offer(id, page=1, per_page=200):
    query = 'query%20getOfferThumbById%28%24id%3A%20ID%21%2C%20%24page%3A%20Int%2C%20%24perPage%3A%20Int%2C%20%24context%3A%20RecommendedOfferContextInput%29%20%7B%0A%20%20genericOffer%28id%3A%20%24id%29%20%7B%0A%20%20%20%20...%20on%20Offer%20%7B%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20userBased%0A%20%20%20%20%20%20paginatedItems%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...videoFragment%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20RecommendedOffer%20%7B%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20items%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%2C%20context%3A%20%24context%29%20%7B%0A%20%20%20%20%20%20%20%20customTitle%0A%20%20%20%20%20%20%20%20abExperiment%20%7B%0A%20%20%20%20%20%20%20%20%20%20experiment%0A%20%20%20%20%20%20%20%20%20%20alternative%0A%20%20%20%20%20%20%20%20%20%20trackId%0A%20%20%20%20%20%20%20%20%20%20convertUrl%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...videoFragment%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A%0Afragment%20videoFragment%20on%20Video%20%7B%0A%20%20id%0A%20%20kind%0A%20%20headline%0A%20%20description%0A%20%20liveThumbnail%0A%20%20thumb%0A%20%20broadcast%20%7B%0A%20%20%20%20mediaId%0A%20%20%20%20trimmedLogo%28scale%3A%20X56%29%0A%20%20%20%20imageOnAir%0A%20%20%20%20channel%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20payTvServiceId%0A%20%20%20%20%20%20trimmedLogo%28scale%3A%20X56%29%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20title%20%7B%0A%20%20%20%20titleId%0A%20%20%20%20originProgramId%0A%20%20%20%20headline%0A%20%20%20%20description%0A%20%20%20%20slug%0A%20%20%20%20releaseYear%0A%20%20%20%20contentRating%0A%20%20%20%20contentRatingCriteria%0A%20%20%20%20type%0A%20%20%20%20format%0A%20%20%20%20countries%0A%20%20%20%20directors%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%7D%0A%20%20%20%20cast%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%7D%0A%20%20%20%20genres%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%7D%0A%20%20%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20poster%20%7B%0A%20%20%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%20%20logo%20%7B%0A%20%20%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20%7D%0A%20%20availableFor%0A%20%20serviceId%0A%20%20duration%0A%7D'
    variables = '{{"id":"{id}","page":{page},"perPage":{per_page}}}'.format(id=id, page=page, per_page=per_page)
    generic_offer = request_query(query, variables).get('data', {}).get('genericOffer', {})
    items = generic_offer.get('paginatedItems', generic_offer.get('items', {})) or {}

    custom_title = items.get('customTitle', None)

    for item in items.get('resources', []):
        yield {
                'handler': PLAYER_HANDLER,
                'method': 'playlive',
                'IsPlayable': True,
                'custom_title': custom_title,
                'tagline': custom_title,
                'id': str(item.get('id', '')),
                'label': '%s: %s' % (item.get('title', {}).get('headline', ''), item.get('headline', '')),
                'title': item.get('headline', ''),
                'originaltitle': item.get('originalHeadline', ''),
                'tvshowtitle': item.get('title', {}).get('headline', None),
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
                    'thumb': item.get('thumb', LOGO),
                    'fanart': item.get('title', {}).get('cover', {}).get('web', FANART),
                    # 'poster': ((item.get('title', {}) or {}).get('poster', {}) or {}).get('web', None),
                    'icon': ((item.get('title', {}) or {}).get('logo', {}) or {}).get('web', None),
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
                'poster': NEXT_ICON,
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_poster_offer(id, page=1, per_page=40):
    control.log('get_poster_offer: %s | page: %s' % (id, page))

    query = 'query%20getOffer%28%24id%3A%20ID%21%2C%20%24page%3A%20Int%2C%20%24perPage%3A%20Int%2C%20%24context%3A%20RecommendedOfferContextInput%29%20%7B%0A%20%20genericOffer%28id%3A%20%24id%29%20%7B%0A%20%20%20%20...%20on%20Offer%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20userBased%0A%20%20%20%20%20%20paginatedItems%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%29%20%7B%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...titleHome%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20...%20on%20RecommendedOffer%20%7B%0A%20%20%20%20%20%20contentType%0A%20%20%20%20%20%20items%28page%3A%20%24page%2C%20perPage%3A%20%24perPage%2C%20context%3A%20%24context%29%20%7B%0A%20%20%20%20%20%20%20%20customTitle%0A%20%20%20%20%20%20%20%20abExperiment%20%7B%0A%20%20%20%20%20%20%20%20%20%20experiment%0A%20%20%20%20%20%20%20%20%20%20alternative%0A%20%20%20%20%20%20%20%20%20%20trackId%0A%20%20%20%20%20%20%20%20%20%20convertUrl%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20resources%20%7B%0A%20%20%20%20%20%20%20%20%20%20...titleHome%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20page%0A%20%20%20%20%20%20%20%20perPage%0A%20%20%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20%20%20nextPage%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0Afragment%20titleHome%20on%20Title%20%7B%0A%20%20originVideoId%0A%20%20titleId%0A%20%20type%0A%20%20originProgramId%0A%20%20headline%0A%20%20originalHeadline%0A%20%20description%0A%20%20slug%0A%20%20contentRating%0A%20%20contentRatingCriteria%0A%20%20releaseYear%0A%20%20format%0A%20%20countries%0A%20%20genresNames%0A%20%20directorsNames%0A%20%20artDirectorsNames%0A%20%20authorsNames%0A%20%20castNames%0A%20%20screenwritersNames%0A%20%20cover%20%7B%0A%20%20%20%20%20%20landscape%28scale%3A%20X1080%29%0A%20%20%20%20%20%20web%0A%20%20%20%20%7D%0A%20%20poster%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20logo%20%7B%0A%20%20%20%20web%0A%20%20%7D%0A%20%20channel%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20slug%0A%20%20%7D%0A%7D'
    variables = '{{"id":"{id}","page":{page},"perPage":{perPage}}}'.format(id=id, page=page, perPage=per_page)

    generic_offer = request_query(query, variables).get('data', {}).get('genericOffer', {}) or {}
    items = generic_offer.get('paginatedItems', generic_offer.get('items', {})) or {}

    custom_title = items.get('customTitle', None)

    for resource in items.get('resources', []) or []:
        playable = True if resource.get('originVideoId', None) else False
        yield {
            'handler': PLAYER_HANDLER if playable else __name__,
            'method': 'playlive' if playable else 'get_title',
            'id': resource.get('originVideoId', resource.get('titleId', None)) or resource.get('titleId', None),
            'IsPlayable': playable,
            'custom_title': custom_title,
            'tagline': custom_title,
            # 'type': resource.get('type', None),
            'label': resource.get('headline', ''),
            'title': resource.get('headline', ''),
            'originaltitle': resource.get('originalHeadline', ''),
            'studio': resource.get('channel', {}).get('name', None),
            'year': resource.get('releaseYear', ''),
            'country': resource.get('countries', []),
            'genre': resource.get('genresNames', []),
            'cast': resource.get('castNames', []),
            'director': resource.get('directorsNames', []),
            'writer': resource.get('screenwritersNames', []),
            'credits': resource.get('artDirectorsNames', []),
            'tag': resource.get('contentRatingCriteria', None),
            'mpaa': resource.get('contentRating', ''),
            'plot': resource.get('description', ''),
            'mediatype': 'movie' if resource.get('type', '') == 'MOVIE' else 'tvshow',
            # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            'art': {
                'poster': (resource.get('poster', {}) or {}).get('web', None),
                'clearlogo': (resource.get('logo', {}) or {}).get('web', None),
                'fanart': (resource.get('cover', {}) or {}).get('web', FANART)
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
                'poster': NEXT_ICON,
                'fanart': FANART
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def get_title(id, season=None, page=1):
    if not id:
        return

    control.log('get_title: %s | page %s' % (id, page))
    variables = '{{"titleId":"{id}", "episodeTitlePage": {page}, "userIsLoggedIn": true}}'.format(id=id, page=page)
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
            'context_menu': [('Adicionar a minha lista', control.run_plugin_url({'action': 'addFavorites'}))] if not is_favorite else [('Remover da minha lista', control.run_plugin_url({'action': 'addFavorites'}))],
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
                'art': {
                    'thumb': video.get('thumb', None),
                    'fanart': title.get('cover', {}).get('landscape', FANART)
                },
                'sort': control.SORT_METHOD_EPISODE if resource.get('number', None) and resource.get('seasonNumber', None) else None
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
                        'method': 'playlive',
                        'IsPlayable': True,
                        'id': video.get('id'),
                        'label': video.get('headline', ''),
                        'title': video.get('headline', ''),
                        'originaltitle': video.get('originalHeadline', ''),
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
                        'dateadded': video.get('exhibitedAt', '').replace('Z', '').replace('T', ' '),
                        'sort': control.SORT_METHOD_EPISODE,
                        'art': {
                            'thumb': video.get('thumb', None),
                            'fanart': title.get('cover', {}).get('landscape', FANART)
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
                    'title': title.get('headline', None),
                    'tvshowtitle': title.get('headline', None),
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


def get_continue_watching(page=1, per_page=40):
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
                'method': 'playlive',
                'id': str(resource.get('id', '')),
                'type': (resource.get('title', {}) or {}).get('type', None),
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
                'tag': title.get('contentRatingCriteria', None),
                'mpaa': title.get('contentRating', ''),
                'plot': resource.get('description', ''),
                'mediatype': 'episode' if resource.get('kind', '') == 'episode' else 'movie' if title.get('type', '') == 'MOVIE' else 'tvshow',
                # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
                'art': {
                    'thumb': resource.get('thumb', None),
                    # 'poster': title.get('poster', {}) or {}).get('web', None),
                    'clearicon': (title.get('logo', {}) or {}).get('web', None),
                    'fanart': (title.get('cover', {}) or {}).get('web', FANART),
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

    if not title:
        return

    playable = True if title.get('originVideoId', None) else False
    yield {
        'handler': PLAYER_HANDLER if playable else __name__,
        'method': 'playlive' if playable else 'get_title',
        'id': title.get('originVideoId', title.get('titleId', None)) or title.get('titleId', None),
        'IsPlayable': playable,
        # 'type': resource.get('type', None),
        'label': title.get('headline', ''),
        'title': title.get('headline', ''),
        'studio': title.get('channel', {}).get('name', None),
        'year': title.get('releaseYear', ''),
        'originaltitle': title.get('originalHeadline', ''),
        'country': title.get('countries', []),
        'genre': title.get('genresNames', []),
        'cast': title.get('castNames', []),
        'director': title.get('directorsNames', []),
        'writer': title.get('screenwritersNames', []),
        'credits': title.get('artDirectorsNames', []),
        'tag': title.get('contentRatingCriteria', None),
        'mpaa': title.get('contentRating', ''),
        'plot': title.get('description', ''),
        'mediatype': 'movie' if title.get('type', '') == 'MOVIE' else 'tvshow',
        # "video", "movie", "tvshow", "season", "episode" or "musicvideo"
        'art': {
            'poster': title.get('poster', {}).get('web', None),
            'clearlogo': title.get('logo', {}).get('web', None),
            'fanart': title.get('cover', {}).get('web', FANART)
        }
    }