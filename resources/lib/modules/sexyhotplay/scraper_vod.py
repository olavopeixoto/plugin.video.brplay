import os,re
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import util
from BeautifulSoup import BeautifulSoup as bs

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

    url = "http://sexyhotplay.com.br/categorias/"
    html = client.request(url, headers={'Cookie': 'disclaimer-sexyhotplay=1;'})

    soup = bs(html)
    div = soup.find('div', attrs={'class': 'colunas-3-15'})

    links = div.findAll('a', attrs={'class': 'link'}, recursive=True)

    results = []
    for link in links:
        label = link.find('strong').string
        url = 'http://sexyhotplay.com.br' + link['href']
        results.append({
            'name': label,
            # 'clearlogo': os.path.join(artPath, 'logo_sexyhot.png'),
            'url': url
        })

    return results


def get_videos(url):
    from datetime import timedelta
    import time

    html = client.request(url, headers={'Cookie': 'disclaimer-sexyhotplay=1;'})

    soup = bs(html)

    list = soup.find('ul', attrs={'class': 'recipiente-1'})
    items = list.findAll('li', recursive=False)

    next_page = soup.find('a', attrs={'id': 'next-page'})

    if control.setting('sexy_hot_pagination') == 'false':

        oldUrl = url
        while next_page != None and next_page['data-page'] != None and next_page['data-orderby'] != None:

            url = util.add_url_parameters(url, {
                'pagina': int(next_page['data-page']) + 1,
                'ordem': next_page['data-orderby']
            })

            control.log("URL: %s" % url)

            if url == oldUrl:
                break

            oldUrl = url
            html = client.request(url, headers={'Cookie': 'disclaimer-sexyhotplay=1;'})
            soup = bs(html)

            list = soup.find('ul', attrs={'class': 'recipiente-1'})
            items += list.findAll('li', recursive=False)
            next_page = soup.find('a', attrs={'id': 'next-page'})

    videos = []
    for item in items:
        div = item.find('div')

        if div is None:
            continue

        img = item.find('img', attrs={'class': 'imagem'})
        span = item.find('span', attrs={'class': 'chapeu'})

        area = div.find('div', attrs={'class': 'area'})
        link = area.find('a', attrs={'class': 'subtitulo'})

        t = time.strptime(span.string, '%H:%M:%S')
        delta = timedelta(hours=t.tm_hour, minutes=t.tm_min, seconds=t.tm_sec)

        duration = util.get_total_seconds(delta)

        id_sexyhot = re.findall(r'\d+', link['href'])[-1]

        title = link['title']
        title = " ".join([x.capitalize() for x in title.split(" ")])
        plot = area.find('div', attrs={'class': 'informacao'}).string.strip()
        poster = img['src']

        actors_html = area.find('li', attrs={'class': 'metadado'}).findAll('strong')
        actors = [actor.string for actor in actors_html]

        videos.append({
            'id_sexyhot': id_sexyhot,
            'mediatype': 'movie',
            'overlay': 6,
            'duration': duration,
            'title': title,
            # 'tagline': plot,
            'plot': plot,
            'cast': actors,
            'poster': poster,
            'fanart': os.path.join(artPath, 'fanart_sexyhot.png'),
            'url': 'http://sexyhotplay.com.br' + link['href']
            # 'logo': os.path.join(artPath, 'logo_sexyhot.png'),
            # 'thumb': os.path.join(artPath, 'logo_sexyhot.png')
        })

    next_page_url = None
    if control.setting('sexy_hot_pagination') == 'true':
        #More Videos
        if next_page != None and next_page['data-page'] != None and next_page['data-orderby'] != None:

            next_page_url = util.add_url_parameters(url, {
                'pagina': int(next_page['data-page']) + 1,
                'ordem': next_page['data-orderby']
            })

    return videos, next_page_url