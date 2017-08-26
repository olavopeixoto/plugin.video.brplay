# -*- coding: utf-8 -*-

import datetime
import json
import os
import sys
import urllib

from resources.lib.modules.globoplay import scraper_vod
from resources.lib.modules.globosat import indexer as globosat
from resources.lib.modules import control
from resources.lib.modules.globoplay import indexer as globoplay
from resources.lib.modules.globosat import scraper_combate
from resources.lib.modules import cache
from resources.lib.modules import workers

GLOBO_FANART = scraper_vod.GLOBO_FANART

CALENDAR_ICON = os.path.join(control.artPath(), 'calendar.png')
NEXT_ICON = os.path.join(control.artPath(), 'next.png')

class Vod:
    def __init__(self):
        self.systime = (datetime.datetime.utcnow()).strftime('%Y%m%d%H%M%S%f')

    def get_vod_channels(self):

        channels = cache.get(self.__get_vod_channels, 360, table="channels")

        if not control.show_adult_content:
            channels = [channel for channel in channels if not channel["adult"]]

        self.channel_directory(channels)

        return channels

    def __get_vod_channels(self):

        channels = []

        if self.__isGlobosatAvailable():
            channels += globosat.Indexer().get_vod()

        if self.__isGloboplayAvailable():
             channels += globoplay.Indexer().get_vod()

        channels = sorted(channels, key=lambda k: k['name'])

        return channels

    def __isGlobosatAvailable(self):
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

        return username and password and username.strip() != '' and password.strip() != ''

    def __isGloboplayAvailable(self):
        username = control.setting('globoplay_username')
        password = control.setting('globoplay_password')

        return username and password and username.strip() != '' and password.strip() != ''

    def get_channel_programs(self, channel_id):
        programs = cache.get(globosat.Indexer().get_channel_programs, 1, channel_id)
        self.programs_directory(programs)

    def get_channel_categories(self, slug='globo'):
        if slug == 'combate':
            categories = cache.get(scraper_combate.get_combate_categories, 1)
            self.category_combate_directory(categories)
        else:
            categories = cache.get(globoplay.Indexer().get_channel_categories, 1)
            extras = cache.get(globoplay.Indexer().get_extra_categories, 1)
            self.category_directory(categories, extras)

    def get_extras(self):
        from resources.lib.modules.globosat import scraper_vod
        tracks = cache.get(scraper_vod.get_tracks, 1)

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])
        provider = 'globosat'

        url = '%s?action=openfeatured&provider=%s' % (sysaddon, provider)

        label = 'Destaques'

        item = control.item(label=label)

        item.setProperty('IsPlayable', "false")
        item.setInfo(type='video', infoLabels={'title': label})

        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        for track in tracks:
            url = '%s?action=openextra&provider=%s&id=%s&kind=%s' % (sysaddon, provider, track['id'], track['kind'])

            label = track['title']

            item = control.item(label=label)

            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels={'title': label})

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=False)

    def get_track(self, id, kind='episode'):
        from resources.lib.modules.globosat import scraper_vod
        videos = cache.get(scraper_vod.get_track_list, 1, id)

        if kind == 'programs':
            self.programs_directory(videos)
        else:
            self.episodes_directory(videos, provider='globosat')

    def get_featured(self):
        from resources.lib.modules.globosat import scraper_vod
        featured = cache.get(scraper_vod.get_featured, 1)
        self.episodes_directory(featured, provider='globosat')

    def get_programs_by_categories(self, category):
        categories = cache.get(globoplay.Indexer().get_category_programs, 1, category)
        self.programs_directory(categories)

    def get_event_videos(self, category, url):
        if url is None or url == 'None':
            events = cache.get(scraper_combate.get_latest_events, 1, category)
            self.episodes_directory(events, category, provider='globosat')
        else:
            events = cache.get(scraper_combate.scrape_videos_from_page, 1, url)
            self.episodes_directory(events, category, provider='globosat')

    def get_events_by_categories(self, category):
        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        if category == 'lutadores':
            import string
            letters = list(string.ascii_uppercase)

            for letter in letters:

                url = '%s?action=openfighters&letter=%s' % (sysaddon, letter)

                item = control.item(label=letter)

                item.setProperty('IsPlayable', "false")
                item.setInfo(type='video', infoLabels={'title': letter})

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

            control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

            control.content(syshandle, 'files')
            control.directory(syshandle, cacheToDisc=False)

        else:
            # events = scraper_combate.get_latest_events(category)
            # self.episodes_directory(events, category, provider='globosat')

            events = cache.get(scraper_combate.get_all_events, 1, category)

            for event in events:
                label = event['title']
                event_url = urllib.quote_plus(event['url']) if event['url'] else None

                meta = {
                    'mediatype': 'video',
                    'overlay': 6,
                    'title': label
                }

                url = '%s?action=openevent&url=%s&provider=%s&category=%s' % (sysaddon, event_url, 'combate', category)

                item = control.item(label=label)

                item.setProperty('IsPlayable', "false")
                item.setInfo(type='video', infoLabels=meta)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

            control.content(syshandle, 'files')
            control.directory(syshandle, cacheToDisc=False)

    def get_videos_by_category(self, category, page=1, poster=None):
        episodes, next_page, total_pages = globoplay.Indexer().get_videos_by_category(category, page)
        self.episodes_directory(episodes, category, next_page, total_pages, 'openextra', poster=poster)

    def get_videos_by_program(self, program_id, page=1, poster=None, provider=None):
        episodes, nextpage, total_pages, days = cache.get(globoplay.Indexer().get_videos_by_program, 1, program_id, page)
        self.episodes_directory(episodes, program_id, nextpage, total_pages, days=days, poster=poster, provider=provider)

    def get_videos_by_program_date(self, program_id, date, poster=None, provider=None):
        episodes = cache.get(globoplay.Indexer().get_videos_by_program_date, 1, program_id, date)
        self.episodes_directory(episodes, program_id, poster=poster, provider=provider)

    def get_fighters(self, letter):
        fighters = cache.get(globosat.Indexer().get_fighters, 1, letter)

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        for fighter in fighters:

            label = fighter['title']
            slug = fighter['slug']
            thumb = fighter['thumb'] if 'thumb' in fighter else None

            meta = {
                'mediatype': 'episode',
                'overlay': 6,
                'title': label,
                'slug': slug,
                'url': fighter['url']
            }

            url = '%s?action=openfighter&slug=%s' % (sysaddon, slug)

            item = control.item(label=label)

            art = {'icon': thumb, 'thumb': thumb, 'fanart': thumb, 'poster': thumb, 'banner': thumb, 'landscape': thumb }

            item.setProperty('Fanart_Image', thumb)

            item.setArt(art)
            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        control.content(syshandle, 'episodes')
        control.directory(syshandle, cacheToDisc=False)

    def get_fighter_videos(self, slug, page):
        videos, next_page, total_pages = cache.get(globosat.Indexer().get_fighter_videos, 1, slug, page)
        self.episodes_directory(videos, next_page=next_page, total_pages=total_pages, next_action='openfighter&slug=%s' % slug, provider='globosat')

    def get_program_dates(self, program_id, poster=None, provider='globoplay'):
        days = globoplay.Indexer().get_program_dates(program_id)

        if days == None or len(days) == 0: control.idle() ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        for day in days:
            label = day
            meta = {}
            meta.update({'mediatype': 'video'})
            meta.update({'overlay': 6})
            meta.update({'title': label})

            url = '%s?action=openvideos&provider=%s&program_id=%s&date=%s' % (sysaddon, provider, program_id, day)

            item = control.item(label=label)

            art = {'poster': poster}
            item.setArt(art)

            # item.setProperty('Fanart_Image', GLOBO_FANART)

            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        control.content(syshandle, 'episodes')
        control.directory(syshandle, cacheToDisc=False)

    def search(self, q, page=1):

        results = []

        threads = []

        if self.__isGloboplayAvailable():
            threads.append(workers.Thread(self.add_search_results, globoplay.Indexer().search, results, q, page))

        if self.__isGlobosatAvailable():
            threads.append(workers.Thread(self.add_search_results, globosat.Indexer().search, results, q, page))

        [i.start() for i in threads]
        [i.join() for i in threads]

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])
        refreshMenu = control.lang(32072).encode('utf-8')

        results = sorted(results, key=lambda k:k['brplayprovider'] if 'brplayprovider' in k else '')

        for result in results:
            label = result['label']

            meta = {
                'id': result['id'],
                'title': result['title'],
                'plot': result['plot'],
                'duration': result['duration'],
                'thumb': result['thumb'],
                'fanart': result['fanart'],
                'mediatype': 'episode'
            }
            meta.update({'mediatype': 'video'})
            meta.update({'overlay': 6})
            meta.update({'title': label})
            meta.update({'live': False})

            if 'tvshowtitle' in result:
                meta.update({'tvshowtitle': result['tvshowtitle']})

            sysmeta = urllib.quote_plus(json.dumps(meta))

            provider = result['brplayprovider'] if 'brplayprovider' in result else 'globoplay'

            url = '%s?action=playvod&provider=%s&id_globo_videos=%s&meta=%s' % (sysaddon, provider, result['id'], sysmeta)

            item = control.item(label=label)

            fanart = meta['fanart'] if 'fanart' in meta else GLOBO_FANART

            clearlogo = meta['clearlogo'] if 'clearlogo' in meta else None

            art = {'thumb': result['thumb'], 'fanart': fanart, 'clearlogo': clearlogo}

            item.setProperty('Fanart_Image', fanart)

            if 'duration' in meta:
                duration = float(meta['duration']) if 'duration' in meta else 0
                duration = duration * 1000.0
                item.setProperty('totaltime', str(duration))

            item.setArt(art)
            item.setProperty('IsPlayable', "true")
            item.setInfo(type='video', infoLabels=meta)

            cm = []
            cm.append((refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon))
            item.addContextMenuItems(cm)

            item.setMimeType("application/vnd.apple.mpegurl")

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)

        # if next_page:
        # label = 'Next Page (%s/%s)' % (nextpage, total_pages)

        # 34004 = "More Videos"
        label = control.lang(34004).encode('utf-8')

        meta = {}
        meta.update({'mediatype': 'video'})
        meta.update({'overlay': 6})
        meta.update({'title': label})

        url = '%s?action=search&q=%s&provider=%s&page=%s' % (sysaddon, q, 'globoplay', int(page)+1)

        item = control.item(label=label)

        art = {'icon': NEXT_ICON, 'thumb': NEXT_ICON}

        # item.setProperty('Fanart_Image', GLOBO_FANART)

        item.setArt(art)
        item.setProperty('IsPlayable', "false")
        item.setInfo(type='video', infoLabels=meta)

        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        control.content(syshandle, 'episodes')
        control.directory(syshandle, cacheToDisc=True)

    def add_search_results(self, fn, list, *args):
        results, next_page, total = fn(*args)
        list += results

    def episodes_directory(self, items, program_id=None, next_page=None, total_pages=None, next_action='openvideos', days=[], poster=None, provider=None):
        if items == None or len(items) == 0: control.idle() ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        # 32072 = "Refresh" 
        refreshMenu = control.lang(32072).encode('utf-8')

        if days:
            # 34005 = "By Date"
            label = control.lang(34005).encode('utf-8')
            meta = {}
            meta.update({'mediatype': 'video'})
            meta.update({'overlay': 6})
            meta.update({'title': label})

            url = '%s?action=showdates&provider=%s&program_id=%s&category=%s' % (sysaddon, provider, program_id, program_id)

            item = control.item(label=label)

            art = {'icon': CALENDAR_ICON, 'thumb': CALENDAR_ICON}

            if poster:
                art.update({'poster': poster})

            # item.setProperty('Fanart_Image', GLOBO_FANART)

            item.setArt(art)
            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        for video in items:
                # label = video['label'] if 'label' in video else video['title']
                label = video['title']
                meta = video
                meta.update({'overlay': 6})
                meta.update({'live': False})

                sysmeta = urllib.quote_plus(json.dumps(meta))

                provider = provider or video['brplayprovider'] if 'brplayprovider' in video else provider

                url = '%s?action=playvod&provider=%s&id_globo_videos=%s&meta=%s' % (sysaddon, provider, video['id'], sysmeta)

                item = control.item(label=label)

                fanart = meta['fanart'] if 'fanart' in meta else GLOBO_FANART

                clearlogo = meta['clearlogo'] if 'clearlogo' in meta else None

                poster = meta['poster'] if 'poster' in meta else poster

                art = {'thumb': meta['thumb'], 'poster': poster, 'fanart': fanart, 'clearlogo': clearlogo}

                item.setProperty('Fanart_Image', fanart)

                offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0

                if 'duration' in meta:
                    duration = float(meta['duration']) if 'duration' in meta else offset
                    duration = duration * 1000.0
                    item.setProperty('totaltime', str(duration))

                if offset > 0:
                    item.setProperty('resumetime', str(offset))
                    meta.update({
                        'playcount': 1
                    })
                else:
                    item.setProperty('resumetime', str(0))
                    meta.update({
                        'playcount': 0
                    })

                item.setArt(art)
                item.setProperty('IsPlayable', "true")
                item.setInfo(type='video', infoLabels = meta)

                cm = []
                cm.append((refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon))
                item.addContextMenuItems(cm)

                item.setMimeType("application/vnd.apple.mpegurl")

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)

        if next_page:
            # label = 'Next Page (%s/%s)' % (nextpage, total_pages)

            # 34006 = "Older Videos"
            label = control.lang(34006).encode('utf-8')
            
            meta = {}
            meta.update({'mediatype': 'video'})
            meta.update({'overlay': 6})
            meta.update({'title': label})

            url = '%s?action=%s&provider=%s&program_id=%s&category=%s&page=%s' % (sysaddon, next_action, 'globoplay', program_id, program_id, next_page)

            item = control.item(label=label)

            art = {'icon': NEXT_ICON, 'thumb': NEXT_ICON, 'poster': poster}

            # item.setProperty('Fanart_Image', GLOBO_FANART)

            item.setArt(art)
            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'episodes')
        control.directory(syshandle, cacheToDisc=False)


    def programs_directory(self, items):
        if items == None or len(items) == 0: control.idle() ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        # 32072 = "Refresh" 
        refreshMenu = control.lang(32072).encode('utf-8')

        has_playable_item = False

        for index, program in enumerate(items):

                label = program['name'] if 'name' in program else program['title'] if 'title' in program else ''

                is_music_video = 'kind' in program and program['kind'] == 'shows'
                is_movie = 'kind' in program and program['kind'] == 'movies'

                is_playable = is_music_video or is_movie

                meta = program
                meta.update({
                    'mediatype': 'musicvideo' if is_music_video else 'movie' if is_movie else 'tvshow',
                    'overlay': 6,
                    'title': label,
                    'sorttitle': "%03d" % (index,)
                })

                item = control.item(label=label)

                poster = program['poster'] if 'poster' in program else None

                thumb = program['thumb'] if 'thumb' in program else None

                fanart = program['fanart'] if 'fanart' in program else GLOBO_FANART

                clearlogo = program['clearlogo'] if 'clearlogo' in program else None

                art = {'fanart': fanart, 'clearlogo': clearlogo}

                if poster:
                    art.update({'poster': poster})

                if thumb:
                    art.update({'thumb': thumb})

                item.setProperty('Fanart_Image', fanart)

                if is_playable:
                    sysmeta = urllib.quote_plus(json.dumps(meta))
                    url = '%s?action=playvod&provider=%s&id_globo_videos=%s&meta=%s' % (sysaddon, program['brplayprovider'], program['id'], sysmeta)
                else:
                    url = '%s?action=openvideos&provider=%s&program_id=%s&poster=%s' % (sysaddon, program['brplayprovider'], program['id'], thumb)

                cm = []
                cm.append((refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon))
                item.addContextMenuItems(cm)

                item.setArt(art)
                item.setProperty('IsPlayable', 'true' if is_playable else 'false')
                item.setInfo(type='video', infoLabels = meta)

                if is_playable:
                    item.setMimeType("application/vnd.apple.mpegurl")
                    has_playable_item = True

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=not is_playable)

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_VIDEO_SORT_TITLE)
        #
        # if has_playable_item:
        #     control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL)
        # else:
        #     control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'tvshows')
        control.directory(syshandle, cacheToDisc=False)

    def category_directory(self, items, extras, provider='globoplay'):
        if items == None or len(items) == 0: control.idle() ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        # 32072 = "Refresh" 
        refreshMenu = control.lang(32072).encode('utf-8')

        for extra in extras:
            id = extra['id']
            label = extra['title']
            meta = {}
            meta.update({'title': label})

            url = '%s?action=openextra&provider=%s&category=%s' % (sysaddon, provider, id)

            item = control.item(label=label)

            # art = {}
            # art.update({'icon': GLOBO_LOGO, 'thumb': GLOBO_LOGO})
            # item.setArt(art)

            item.setProperty('Fanart_Image', GLOBO_FANART)

            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        for title in items:
            label = title
            meta = {}
            meta.update({'title': title})

            url = '%s?action=opencategory&provider=%s&category=%s' % (sysaddon, provider, title)

            item = control.item(label=label)

            fanart = GLOBO_FANART

            art = {'fanart': fanart}
            item.setArt(art)

            item.setProperty('Fanart_Image', fanart)

            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels = meta)

            cm = []
            cm.append((refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon))
            item.addContextMenuItems(cm)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=False)


    def channel_directory(self, items):
        if items == None or len(items) == 0: control.idle() ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        #addonPoster, addonBanner = control.addonPoster(), control.addonBanner()

        #addonFanart, settingFanart = control.addonFanart(), control.setting('fanart')

        try: isOld = False ; control.item().getArt('type')
        except: isOld = True

        # isPlayable = 'true' #if not 'plugin' in control.infoLabel('Container.PluginName') else 'false'

        #playbackMenu = control.lang(32063).encode('utf-8') if control.setting('hosts.mode') == '2' else control.lang(32064).encode('utf-8')

        #queueMenu = control.lang(32065).encode('utf-8')

        # 32072 = "Refresh" 
        refreshMenu = control.lang(32072).encode('utf-8')

        for i in items:
            # try:
                label = i['name']
                meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
                meta.update({'mediatype': 'video'}) #string - "video", "movie", "tvshow", "season", "episode" or "musicvideo"
                meta.update({'playcount': 0, 'overlay': 6})
                meta.update({'duration': i['duration']}) if 'duration' in i else None
                meta.update({'title': i['title']}) if 'title' in i else None
                meta.update({'tagline': i['tagline']}) if 'tagline' in i else None
                # meta.update({'aired': i['datetime']}) if 'datetime' in i else None
                # meta.update({'dateadded': i['datetime']}) if 'datetime' in i else None

                #"StartTime", "EndTime", "ChannelNumber" and "ChannelName"

                sysmeta = urllib.quote_plus(json.dumps(meta))
                id_globo_videos = i['id']
                id_cms = i['id_cms'] if 'id_cms' in i else None
                slug = i['slug'] if 'slug' in i else None
                brplayprovider = i['brplayprovider']

                url = '%s?action=openchannel&provider=%s&id_globo_videos=%s&id_cms=%s&slug=%s&meta=%s&t=%s' % (sysaddon, brplayprovider, id_globo_videos, id_cms, slug, sysmeta, self.systime)

                cm = []

                #cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))

                cm.append((refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon))

                if isOld == True:
                    cm.append((control.lang2(19033).encode('utf-8'), 'Action(Info)'))

                item = control.item(label=label)

                art = {}

                # if 'poster2' in i and not i['poster2'] == '0':
                #     art.update({'icon': i['poster2'], 'thumb': i['poster2'], 'poster': i['poster2']})
                # elif 'poster' in i and not i['poster'] == '0':
                #     art.update({'icon': i['poster'], 'thumb': i['poster'], 'poster': i['poster']})
                # else:
                #     art.update({'icon': addonPoster, 'thumb': addonPoster, 'poster': addonPoster})

                art.update({'icon': i['logo'], 'thumb': i['logo'], 'poster': i['logo']})

                #art.update({'banner': addonBanner})

                # if settingFanart == 'true' and 'fanart' in i and not i['fanart'] == '0':
                #     item.setProperty('Fanart_Image', i['fanart'])
                # elif not addonFanart == None:
                #     item.setProperty('Fanart_Image', addonFanart)

                if 'fanart' in i:
                    item.setProperty('Fanart_Image', i['fanart'])
                else:
                    item.setProperty('Fanart_Image', control.addonFanart())

                item.setArt(art)
                item.addContextMenuItems(cm)
                item.setProperty('IsPlayable', "false")
                item.setInfo(type='video', infoLabels = meta)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
            # except:
            #     pass

        control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=False)


    def category_combate_directory(self, items):
        if items == None or len(items) == 0: control.idle() ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        # 32072 = "Refresh" 
        refreshMenu = control.lang(32072).encode('utf-8')

        for item in items:
            title = item['title']
            label = title
            slug = item['slug']
            meta = {}
            meta.update({'title': title})

            url = '%s?action=opencategory&provider=%s&category=%s' % (sysaddon, 'combate', slug)

            item = control.item(label=label)

            # art = {'icon': GLOBO_LOGO, 'thumb': GLOBO_LOGO, 'fanart': fanart}
            # item.setArt(art)

            # item.setProperty('Fanart_Image', fanart)

            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels = meta)

            cm = []
            cm.append((refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon))
            item.addContextMenuItems(cm)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=False)