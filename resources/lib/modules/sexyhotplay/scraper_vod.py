import os
import urllib
import datetime
from resources.lib.modules import util
from resources.lib.modules import control
from resources.lib.modules import client

artPath = control.artPath()


def getChannels():

    channels = [{
        'slug': 'sexyhot',
        'name': 'Sexyhot',
        'logo': os.path.join(artPath, 'logo_sexyhot.png'),
        'fanart': os.path.join(artPath, 'fanart_sexyhot.png'),
        'playable': 'false',
        'plot': None,
        'id': None,
        'isFolder': 'true'
    }]

    return channels


def get_categories():

    results = []
    return results


def get_videos(page=1):
    page_size = 24
    variables = '{{"id":"7e679166-caa2-457c-a5f3-56ff7ca79a69","page":{page},"perPage":{pagesize}}}'
    query = '''query getOffer($id: ID!, $page: Int, $perPage: Int) {
  genericOffer(id: $id) {
    ... on Offer {
      id
      contentType
      items: paginatedItems(page: $page, perPage: $perPage) {
        page
        nextPage
        perPage
        hasNextPage
        resources {
          ...VideoFragment
          ...TitleFragment
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}
fragment VideoFragment on Video {
  id
  availableFor
  headline
  kind
  duration
  formattedDuration
  thumb
  liveThumbnail
  preview
  originalContent
  exhibitedAt
  title {
    titleId
    headline
    slug
    __typename
  }
  channel {
    id
    name
    slug
    __typename
  }
  __typename
}
fragment TitleFragment on Title {
  titleId
  headline
  slug
  poster {
    web
    __typename
  }
  channel {
    id
    name
    slug
    __typename
  }
  __typename
}'''
    # url = 'https://products-jarvis.globo.com/graphql?operationName=getOffer&variables={var}&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22ed91671dc38a0f931c33239fd7b299d9035ea25177c212eb05fd512ab69ee134%22%7D%7D'
    url = 'https://products-jarvis.globo.com/graphql?query={query}&variables={var}'
    headers = {
        'x-tenant-id': 'sexy-hot',
        'x-platform-id': 'web',
        'x-device-id': 'desktop',
        'x-client-version': '0.4.3',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
        'accept-encoding': 'gzip'
    }

    result = client.request(url.format(query=urllib.quote_plus(query), var=urllib.quote_plus(variables.format(page=page, pagesize=page_size))), headers=headers)

    videos = []

    for video in result['data']['genericOffer']['items']['resources']:
        date = util.strptime(video['exhibitedAt'], '%Y-%m-%dT%H:%M:%SZ') + util.get_utc_delta()
        videos.append({
            'id_sexyhot': video['id'],
            'mediatype': 'movie' if video['kind'] == 'film' else 'episode' if video['kind'] in ['serie', 'episode'] else 'video',
            'overlay': 6,
            'duration': int(video['duration'])/1000,
            'title': video['headline'],
            'plot': '',
            'thumb': video['thumb'],
            'poster': video['thumb'],
            'fanart': os.path.join(artPath, 'fanart_sexyhot.png'),
            'dateadded': datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S')
        })

    next_page = result['data']['genericOffer']['items']['nextPage'] if result['data']['genericOffer']['items']['hasNextPage'] else None

    return videos, next_page
