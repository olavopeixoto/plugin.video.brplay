# -*- coding: utf-8 -*-

import re,urllib,json,urlparse,base64,random

from resources.lib.modules import client
from resources.lib.modules import control


class trailer:
    def __init__(self):
        self.base_link = 'http://www.youtube.com'
        self.key_link = random.choice(['QUl6YVN5RDd2aFpDLTYta2habTVuYlVyLTZ0Q0JRQnZWcnFkeHNz', 'QUl6YVN5Q2RiNEFNenZpVG0yaHJhSFY3MXo2Nl9HNXBhM2ZvVXd3'])
        self.key_link = '&key=%s' % base64.urlsafe_b64decode(self.key_link)
        self.search_link = 'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=5&q=%s'
        self.youtube_search = 'https://www.googleapis.com/youtube/v3/search?q='
        self.youtube_watch = 'http://www.youtube.com/watch?v=%s'


    def play(self, name, url=None):
        try:
            url = self.worker(name, url)
            if url == None: return

            title = control.infoLabel('listitem.title')
            if title == '': title = control.infoLabel('listitem.label')
            icon = control.infoLabel('listitem.icon')

            item = control.item(path=url, iconImage=icon, thumbnailImage=icon)
            try: item.setArt({'icon': icon})
            except: pass
            item.setInfo(type='Video', infoLabels = {'title': title})
            control.player.play(url, item)
        except:
            pass

    def worker(self, name, url):
        try:
            if url.startswith(self.base_link):
                url = self.resolve(url)
                if url == None: raise Exception()
                return url
            elif not url.startswith('http://'):
                url = self.youtube_watch % url
                url = self.resolve(url)
                if url == None: raise Exception()
                return url
            else:
                raise Exception()
        except:
            query = name + ' trailer'
            query = self.youtube_search + query
            url = self.search(query)
            if url == None: return
            return url


    def search(self, url):
        try:
            query = urlparse.parse_qs(urlparse.urlparse(url).query)['q'][0]

            apiLang = control.apiLanguage()['youtube']

            if apiLang != 'en':
                query += ' %s' % control.apiLanguage(True)['youtube']
                url += "&relevanceLanguage=%s" % apiLang

            url = self.search_link % urllib.quote_plus(query) + self.key_link

            result = client.request(url)

            items = json.loads(result)['items']
            items = [(i['id']['videoId']) for i in items]

            for url in items:
                url = self.resolve(url)
                if not url is None: return url
        except:
            return


    def resolve(self, url):
        try:
            id = url.split('?v=')[-1].split('/')[-1].split('?')[0].split('&')[0]
            result = client.request('http://www.youtube.com/watch?v=%s' % id)

            message = client.parseDOM(result, 'div', attrs = {'id': 'unavailable-submessage'})
            message = ''.join(message)

            alert = client.parseDOM(result, 'div', attrs = {'id': 'watch7-notification-area'})

            if len(alert) > 0: raise Exception()
            if re.search('[a-zA-Z]', message): raise Exception()

            url = 'plugin://plugin.video.youtube/play/?video_id=%s' % id
            return url
        except:
            return

