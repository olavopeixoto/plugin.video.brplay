# -*- coding: utf-8 -*-

import datetime
import json
import sys
import urllib

import resources.lib.modules.util as util
from resources.lib.modules import control
from resources.lib.modules import workers
from resources.lib.modules.globoplay import indexer as globoplay
from resources.lib.modules.globoplay import scraper_live as globoplay_live
from resources.lib.modules.globosat import indexer as globosat
from resources.lib.modules.sexyhotplay import indexer as sexyhotplay
from resources.lib.modules.oiplay import scraper_live as oiplay


class Live:
    def __init__(self):
        self.systime = (datetime.datetime.utcnow()).strftime('%Y%m%d%H%M%S%f')

    def get_channels(self):

        live = []

        threads = []

        if control.is_globoplay_available():
            threads.append(workers.Thread(self.append_result, globoplay.Indexer().get_live_channels, live))

        if control.is_globosat_available():
            threads.append(workers.Thread(self.append_result, globosat.Indexer().get_live, live))
            if control.show_adult_content:
                threads.append(workers.Thread(self.append_result, sexyhotplay.Indexer().get_live_channels, live))

        if control.is_oiplay_available():
            threads.append(workers.Thread(self.append_result, oiplay.get_live_channels, live))

        [i.start() for i in threads]
        [i.join() for i in threads]

        # live.append({
        #     'slug': 'bandnews',
        #     'name': 'Bandnews',
        #     'title': 'Bandnews',
        #     'sorttitle': 'Bandnews',
        #     'logo': os.path.join(control.artPath(), 'logo_bandnews.png'),
        #     # 'clearlogo': os.path.join(control.artPath(), 'logo_bandnews.png'),
        #     'color': None,
        #     'fanart': os.path.join(control.artPath(), 'fanart_bandnews.jpg'),
        #     'thumb': None,
        #     'playable': 'true',
        #     'plot': None,
        #     'id': -1,
        #     'channel_id': -1,
        #     'duration': None,
        #     'url': 'http://evcv.mm.uol.com.br:1935/band/bandnews/playlist.m3u8'
        # })

        # live = sorted(live, key=lambda k: k['sorttitle'])
        # live = sorted(live, key=lambda k: '1' if 'isFolder' in k and k['isFolder'] == 'true' else '0')
        # live = sorted(live, key=lambda k: k['dateadded'] if 'dateadded' in k else None, reverse=True)

        # shuffle(live)

        self.channel_directory(live)

        return live

    def append_result(self, fn, list, *args):
        list += fn(*args)

    def get_subitems_pfc(self, meta):
        live = globosat.Indexer().get_pfc(meta)

        self.channel_directory(live)

        return live

    def get_subitems_bbb(self, program_id):
        live = globoplay_live.get_multicam(program_id)

        self.channel_directory(live)

        return live

    def channel_directory(self, items):
        if items is None or len(items) == 0:
            control.idle()
            sys.exit()

        sysaddon = sys.argv[0]

        syshandle = int(sys.argv[1])

        try:
            isOld = False
            control.item().getArt('type')
        except:
            isOld = True

        refreshMenu = control.lang(32072).encode('utf-8')

        list_items = []

        for order, channel in enumerate(items):
            label = channel['name']
            meta = channel
            meta.update({'mediatype': channel['mediatype'] if 'mediatype' in channel else 'tvshow'})  # string - "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            meta.update({'playcount': 0, 'overlay': 6})
            meta.update({'duration': channel['duration']}) if 'duration' in channel else None
            meta.update({'title': channel['title']}) if 'title' in channel else None
            meta.update({'tagline': channel['tagline']}) if 'tagline' in channel else None
            meta.update({'year': channel['year']}) if 'year' in channel else None

            meta.update({'sorttitle': meta['title']})
            meta.update({'title': meta['name']})

            sysmeta = urllib.quote_plus(json.dumps(meta))
            id_globo_videos = channel['id']
            brplayprovider = channel['brplayprovider'] if 'brplayprovider' in channel else None
            isFolder = channel['isFolder'] == 'true' if 'isFolder' in channel else False
            isPlayable = channel['playable'] == 'true' if 'playable' in channel else False

            url = channel['url'] if 'url' in channel else '%s?action=playlive&provider=%s&id_globo_videos=%s&isFolder=%s&meta=%s&t=%s' % (sysaddon, brplayprovider, id_globo_videos, isFolder, sysmeta, self.systime)

            cm = [(refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon)]

            if isOld is True:
                cm.append((control.lang2(19033).encode('utf-8'), 'Action(Info)'))

            item = control.item(label=label)

            fanart = channel['fanart']

            art = {'icon': channel['logo'], 'fanart': fanart}

            if 'poster' in channel:
                art.update({'poster': channel['poster']})
            if 'banner' in channel:
                art.update({'banner': channel['banner']})
            if 'clearart' in channel:
                art.update({'clearart': channel['clearart']})
            if 'clearlogo' in channel:
                art.update({'clearlogo': channel['clearlogo']})
            if 'landscape' in channel:
                art.update({'landscape': channel['landscape']})
            if 'thumb' in channel:
                art.update({'thumb': channel['thumb']})

            item.setArt(art)

            if 'logo' in channel and 'logo2' in channel:
                item.setProperty('Logo1', channel['logo'])
                item.setProperty('Logo2', channel['logo2'])
                item.setProperty('Initials1', channel['initials1'])
                item.setProperty('Initials2', channel['initials2'])

            if 'live' in channel:
                item.setProperty('Live', str(channel['live']))

            if 'gamedetails' in channel:
                item.setProperty('GameDetails', channel['gamedetails'])

            item.setProperty('Fanart_Image', fanart)

            if 'hd' not in channel or channel['hd'] == True:
                video_info = {'aspect': 1.78, 'width': 1280, 'height': 720}
            else:
                video_info = {'aspect': 1.78, 'width': 720, 'height': 480}

            item.addStreamInfo('video', video_info)

            item.addContextMenuItems(cm)
            item.setProperty('IsPlayable', 'false' if isFolder or not isPlayable else 'true')
            item.setInfo(type='video', infoLabels=meta)

            item.setContentLookup(False)

            if 'duration' in channel and channel['duration'] is not None:
                duration = float(meta['duration'])
                startdate = util.strptime_workaround(channel['dateadded'], '%Y-%m-%d %H:%M:%S') if 'dateadded' in channel else None
                offset = float(util.get_total_seconds(datetime.datetime.now() - startdate)) if startdate else 0
                item.setProperty('Progress', str((offset / duration) * 100) if duration else str(0))
                item.setProperty('totaltime', str(duration))

            # if not isFolder:
            #     item.setMimeType("application/vnd.apple.mpegurl")

            list_items.append((url, item, isFolder))

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_VIDEO_SORT_TITLE)
        control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_DATEADDED)
        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.addItems(syshandle, list_items)
        control.category(handle=syshandle, category=control.lang(32001).encode('utf-8'))

        content = 'LiveTV' if control.isJarvis else 'tvshows'

        control.content(syshandle, content)
        control.directory(syshandle, cacheToDisc=False)