import sys, urllib, os, json
from resources.lib.modules import control
from resources.lib.modules import cache

artPath = control.artPath()
NEXT_ICON = os.path.join(control.artPath(), 'next.png')

class indexer:
    def __init__(self):
        pass

    def get_vod(self):
        import scraper_vod as scraper
        vod = scraper.getChannels()

        for item in vod:
            item["brplayprovider"] = "sexyhot"

        return vod

    def get_categories(self):

        import scraper_vod as scraper

        list = cache.get(scraper.get_categories, 1)

        self.channel_directory(list)

        return list

    def get_videos(self, url):

        import scraper_vod as scraper
        videos, next_page_url = cache.get(scraper.get_videos, 1, url)

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        for video in videos:
            meta = video

            sysmeta = urllib.quote_plus(json.dumps(meta))
            isFolder = False
            brplayprovider = 'sexyhot'
            id_sexyhot = video['id_sexyhot']
            title = video['title']

            action_url = '%s?action=playvod&provider=%s&id_sexyhot=%s&isFolder=%s&meta=%s' % (
            sysaddon, brplayprovider, id_sexyhot, isFolder, sysmeta)

            item = control.item(label=title)

            art = {
                'poster': video['poster'],
                'fanart': video['fanart'],
            }

            item.setArt(art)
            item.setProperty('IsPlayable', 'true')
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=action_url, listitem=item, isFolder=isFolder)

        if next_page_url:
            sysurl = urllib.quote_plus(next_page_url)

            action_url = '%s?action=getVideos&provider=sexyhot&url=%s' % (sysaddon, sysurl)

            title = 'More Videos'
            item = control.item(label=title)
            art = {
                'logo': os.path.join(artPath, 'logo_sexyhot.png'),
                'thumb': NEXT_ICON,
                'fanart': os.path.join(artPath, 'fanart_sexyhot.png'),
            }
            item.setArt(art)
            item.setProperty('IsPlayable', 'false')
            item.setInfo(type='video', infoLabels={'title': title})

            control.addItem(handle=syshandle, url=action_url, listitem=item, isFolder=True)

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'movies')
        control.directory(syshandle, cacheToDisc=False)

    def channel_directory(self, items):
        if items is None or len(items) == 0: control.idle(); sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])
        fanart = os.path.join(artPath, 'fanart_sexyhot.png')
        logo = os.path.join(artPath, 'logo_sexyhot.png')

        refreshMenu = control.lang(32072).encode('utf-8')

        cm = []
        cm.append((refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon))

        for index, item in enumerate(items):
            label = item['name']
            sysurl = urllib.quote_plus(item['url'])

            url = '%s?action=getVideos&provider=sexyhot&url=%s' % (sysaddon, sysurl)

            item = control.item(label=label)

            item.setArt({
                'logo': logo,
                # 'thumb': logo,
                'fanart': fanart,
            })
            item.addContextMenuItems(cm)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', fanart)
            item.setInfo(type='video', infoLabels={'title': label})
            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=False)
