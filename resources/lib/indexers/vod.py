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
from resources.lib.modules import util

GLOBO_FANART = scraper_vod.GLOBO_FANART

CALENDAR_ICON = os.path.join(control.artPath(), 'calendar.png')
NEXT_ICON = os.path.join(control.artPath(), 'next.png')
REPLAY_ICON = os.path.join(control.artPath(), 'returning-tvshows.png')
REPLAY_ICON_POSTER = os.path.join(control.artPath(), 'returning-tvshows-poster.png')

# DRM_CHANNELS = ['megapix', 'megapix-2', 'telecine']
DRM_CHANNELS = [1990, 2079, 1966]
# BLACKLIST_CHANNELS = ['multishow-2', 'telecine', 'sexy-hot', 'globonews-2', 'megapix', 'telecine-zone', 'big-brother-brasil-1', 'big-brother-brasil-2']
BLACKLIST_CHANNELS = [2060, 1966, 1966, 2069, 1990, 2013, 2012, 2058, 2002, 2001, 2006]


class Vod:
    def __init__(self):
        self.systime = (datetime.datetime.utcnow()).strftime('%Y%m%d%H%M%S%f')

    def get_vod_channels_directory(self):

        channels = self.get_vod_channels()

        self.channel_directory(channels)

    def get_vod_channels(self):

        channels = cache.get(self.__get_vod_channels, 360, table="channels")

        channels = [channel for channel in channels if channel['id'] not in BLACKLIST_CHANNELS]

        if not control.show_adult_content:
            channels = [channel for channel in channels if not channel["adult"]]

        if not control.is_inputstream_available():
            channels = [channel for channel in channels if channel['id'] not in DRM_CHANNELS]

        return channels

    def __get_vod_channels(self):

        channels = []

        if control.is_globosat_available():
            channels += globosat.Indexer().get_vod()

        if control.is_globoplay_available():
            channels += globoplay.Indexer().get_vod()

        channels = sorted(channels, key=lambda k: k['name'])

        return channels

    def get_channel_programs(self, channel_id):
        programs = cache.get(globosat.Indexer().get_channel_programs, 1, channel_id)
        self.programs_directory(programs)

    def get_channel_categories(self, slug='globo'):
        if slug == 'combate':
            categories = cache.get(scraper_combate.get_combate_categories, 1)
            self.category_combate_directory(categories)
        else:
            categories = globoplay.Indexer().get_channel_categories()
            extras = globoplay.Indexer().get_extra_categories()
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

        control.category(handle=syshandle, category=control.lang(32080).encode('utf-8'))

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=False)

    def get_track(self, id, kind='episode'):
        from resources.lib.modules.globosat import scraper_vod
        videos = cache.get(scraper_vod.get_track_list, 1, id)

        if kind == 'programs' or kind == 'movies':
            self.programs_directory(videos, kind=kind)
        else:
            self.episodes_directory(videos, provider='globosat')

    def get_featured(self):
        from resources.lib.modules.globosat import scraper_vod
        featured = cache.get(scraper_vod.get_featured, 1)
        self.episodes_directory(featured, provider='globosat')

    def get_favorites(self):
        from resources.lib.modules.globosat import scraper_vod
        favorites = scraper_vod.get_favorites()
        syshandle = int(sys.argv[1])
        control.category(handle=syshandle, category=control.lang(32090).encode('utf-8'))
        self.episodes_directory(favorites, provider='globosat', is_favorite=True)

    def add_favorites(self, video_id):
        from resources.lib.modules.globosat import scraper_vod
        scraper_vod.add_favorites(video_id)

        control.infoDialog(control.lang(32057).encode('utf-8'), sound=True, icon='INFO')

    def del_favorites(self, video_id):
        from resources.lib.modules.globosat import scraper_vod
        scraper_vod.del_favorites(video_id)

        control.refresh()
        control.infoDialog(control.lang(32057).encode('utf-8'), sound=True, icon='INFO')

    def get_watch_later(self):
        from resources.lib.modules.globosat import scraper_vod
        favorites = scraper_vod.get_watch_later()
        syshandle = int(sys.argv[1])
        control.category(handle=syshandle, category=control.lang(32095).encode('utf-8'))
        self.episodes_directory(favorites, provider='globosat', is_watchlater=True)

    def add_watch_later(self, video_id):
        from resources.lib.modules.globosat import scraper_vod
        scraper_vod.add_watch_later(video_id)

        control.infoDialog(control.lang(32057).encode('utf-8'), sound=True, icon='INFO')

    def del_watch_later(self, video_id):
        from resources.lib.modules.globosat import scraper_vod
        scraper_vod.del_watch_later(video_id)

        control.refresh()
        control.infoDialog(control.lang(32057).encode('utf-8'), sound=True, icon='INFO')

    def get_watch_history(self):
        from resources.lib.modules.globosat import scraper_vod
        watch_history = scraper_vod.get_watch_history()
        syshandle = int(sys.argv[1])
        control.category(handle=syshandle, category=control.lang(32096).encode('utf-8'))
        self.episodes_directory(watch_history, provider='globosat')

    def get_programs_by_category(self, category):
        programs = cache.get(globoplay.Indexer().get_category_programs, 1, category)
        subcategories = cache.get(globoplay.Indexer().get_category_subcategories, 1, category)
        self.programs_directory(programs, subcategories, category)

    def get_programs_by_subcategory(self, category, subcategory):
        subcategories = cache.get(globoplay.Indexer().get_category_programs, 1, category, subcategory)
        self.programs_directory(subcategories)

    def get_states(self):
        states = cache.get(globoplay.Indexer().get_states, 1)
        self.state_directory(states)

    def get_4k(self):
        programs = cache.get(globoplay.Indexer().get_4k, 1)
        self.programs_directory(programs)

    def get_regions(self, state):
        regions = cache.get(globoplay.Indexer().get_regions, 1, state)
        self.region_directory(regions)

    def get_programs_by_region(self, region):
        programs = cache.get(globoplay.Indexer().get_programs_by_region, 1, region)
        self.programs_directory(programs)

    def get_event_videos(self, category, url):
        if url is None or url == 'None':
            events = cache.get(scraper_combate.open_ufc_submenu, 1, category)
            self.episodes_directory(events, category, provider='globosat')
        else:
            if url in dir(scraper_combate):
                events = cache.get(getattr(scraper_combate, url), 1, category)
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

            return

        if category == 'ufc':
            events = scraper_combate.get_ufc_submenu()

        else:
            events = cache.get(scraper_combate.get_all_events, 1, category)

        for event in events:
            label = event['title']
            event_url = urllib.quote_plus(event['url']) if event['url'] else None
            slug = event['slug'] if 'slug' in event else category

            meta = {
                'mediatype': 'video',
                'overlay': 6,
                'title': label
            }

            url = '%s?action=openevent&url=%s&provider=%s&category=%s' % (sysaddon, event_url, 'combate', slug)

            item = control.item(label=label)

            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=False)

    def get_videos_by_category(self, category, page=1, poster=None):
        episodes, next_page, total_pages = globoplay.Indexer().get_videos_by_category(category, page)
        self.episodes_directory(episodes, category, next_page, total_pages, 'openextra', poster=poster)

    def get_videos_by_program(self, program_id, id_globo_videos, page=1, poster=None, provider=None, bingewatch=False, fanart=None):
        episodes, nextpage, total_pages, days = cache.get(globoplay.Indexer().get_videos_by_program, 1, program_id, page, bingewatch)
        self.episodes_directory(episodes, program_id, nextpage, total_pages, days=days, poster=poster, provider=provider, fanart=fanart)

    def get_seasons_by_program(self, id_globo_videos):
        if not util.is_number(id_globo_videos):
            control.infoDialog('[%s] %s' % (self.__class__.__name__, 'NO VIDEO ID'), 'ERROR')
            return

        card = cache.get(globosat.Indexer().get_seasons_by_program, 1, id_globo_videos)

        if 'seasons' in card and card['seasons'] and len(card['seasons']) > 0:
            self.seasons_directory(card)
        else:
            self.get_episodes_by_program(card['id'])

    def get_episodes_by_program(self, id_program, id_season=None):
        episodes = cache.get(globosat.Indexer().get_episodes_by_program, 1, id_program, id_season)
        self.episodes_directory(episodes)

    def get_videos_by_program_date(self, program_id, date, poster=None, provider=None, bingewatch=False, fanart=None):
        episodes = cache.get(globoplay.Indexer().get_videos_by_program_date, 1, program_id, date, bingewatch)
        self.episodes_directory(episodes, program_id, poster=poster, provider=provider, fanart=fanart)

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

        if days is None or len(days) == 0:
            control.idle() ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        for day in days:
            label = day
            meta = {}
            meta.update({'mediatype': 'video'})
            meta.update({'overlay': 6})
            meta.update({'title': label})
            meta.update({'date': day})

            url = '%s?action=openvideos&provider=%s&program_id=%s&date=%s' % (sysaddon, provider, program_id, day)

            item = control.item(label=label)

            art = {'poster': poster}
            item.setArt(art)

            # item.setProperty('Fanart_Image', GLOBO_FANART)

            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_DATE)

        control.content(syshandle, 'episodes')
        control.directory(syshandle, cacheToDisc=False)

    def search(self, q, page=1):

        results = []

        threads = []

        if control.is_globoplay_available():
            threads.append(workers.Thread(self.add_search_results, globoplay.Indexer().search, results, q, page))

        if control.is_globosat_available():
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
                'thumb': result['thumb'],
                'fanart': result['fanart'],
                'mediatype': result['mediatype']
            }
            if 'duration' in result:
                meta.update({'duration': result['duration']})

            meta.update({'mediatype': 'video'})
            meta.update({'overlay': 6})
            meta.update({'title': label})
            meta.update({'live': False})

            if 'tvshowtitle' in result:
                meta.update({'tvshowtitle': result['tvshowtitle']})

            sysmeta = urllib.quote_plus(json.dumps(meta))

            provider = result['brplayprovider'] if 'brplayprovider' in result else 'globoplay'

            item = control.item(label=label)

            fanart = meta['fanart'] if 'fanart' in meta else GLOBO_FANART

            clearlogo = meta['clearlogo'] if 'clearlogo' in meta else None

            art = {'thumb': result['thumb'], 'fanart': fanart, 'clearlogo': clearlogo}

            isFolder = False

            if 'IsPlayable' not in result or result['IsPlayable']:
                url = '%s?action=playvod&provider=%s&id_globo_videos=%s&meta=%s' % (sysaddon, provider, result['id'], sysmeta)
                item.setProperty('IsPlayable', "true")
                isFolder = False
            else:
                item.setProperty('IsPlayable', "false")
                isFolder = True

                is_bingewatch = result['mediatype'] == 'tvshow'

                if result['brplayprovider'] == 'globoplay':
                    url = '%s?action=openvideos&provider=%s&program_id=%s&id_globo_videos=%s&poster=%s&bingewatch=%s&fanart=%s' % (sysaddon, result['brplayprovider'], result['id'], result['id'], result['thumb'], is_bingewatch, fanart)
                else:
                    url = '%s?action=openvideos&provider=%s&id_globo_videos=%s' % (sysaddon, result['brplayprovider'], result['id'])

            item.setProperty('Fanart_Image', fanart)

            if 'duration' in meta:
                duration = float(meta['duration']) if 'duration' in meta else 0
                duration = duration * 1000.0
                item.setProperty('totaltime', str(duration))

            item.setArt(art)
            item.setInfo(type='video', infoLabels=meta)

            cm = [(refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon)]
            item.addContextMenuItems(cm)

            # item.setMimeType("application/vnd.apple.mpegurl")

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

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

    def add_results(self, fn, list, *args):
        results = fn(*args)
        list += results

    def episodes_directory(self, items, program_id=None, next_page=None, total_pages=None, next_action='openvideos', days=[], poster=None, provider=None, is_favorite=False, is_watchlater=False, fanart=None):
        if items is None or len(items) == 0:
            control.idle()
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        # 32072 = "Refresh" 
        refreshMenu = control.lang(32072).encode('utf-8')
        addFavorite = control.lang(32073).encode('utf-8')
        removeFavorite = control.lang(32074).encode('utf-8')
        addWatchLater = control.lang(32075).encode('utf-8')
        removeWatchLater = control.lang(32076).encode('utf-8')

        content = 'videos'
        sort = True

        if days:
            # 34005 = "By Date"
            label = control.lang(34005).encode('utf-8')
            meta = {}
            meta.update({'mediatype': 'video'})
            meta.update({'overlay': 6})
            meta.update({'title': label})

            url = '%s?action=showdates&provider=%s&program_id=%s&category=%s' % (sysaddon, provider, program_id, program_id)

            item = control.item(label=label)

            local_fanart = fanart if fanart is not None else meta['fanart'] if 'fanart' in meta else GLOBO_FANART

            item.setProperty('Fanart_Image', local_fanart)

            art = {'icon': CALENDAR_ICON, 'thumb': CALENDAR_ICON, 'fanart': local_fanart}

            if poster:
                art.update({'poster': poster})

            # item.setProperty('Fanart_Image', GLOBO_FANART)

            item.setArt(art)
            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        for video in items:

            if 'url' in video:

                content = 'files'
                sort = False

                label = video['title']
                event_url = urllib.quote_plus(video['url']) if video['url'] else None
                slug = video['slug'] if 'slug' in video else program_id

                meta = {
                    'mediatype': 'video',
                    'overlay': 6,
                    'title': label
                }

                meta.update(video)

                url = '%s?action=openevent&url=%s&provider=%s&category=%s' % (sysaddon, event_url, 'combate', slug)

                item = control.item(label=label)

                if 'thumb' in meta and 'fanart' in meta:
                    art = {'thumb': meta['thumb'], 'fanart': meta['fanart']}
                    item.setArt(art)

                item.setProperty('IsPlayable', "false")
                item.setInfo(type='video', infoLabels=meta)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

            else:
                # label = video['label'] if 'label' in video else video['title']
                label = video['title']
                meta = video
                meta.update({'overlay': 6})

                if 'live' not in meta:
                    meta.update({'live': False})

                sysmeta = urllib.quote_plus(json.dumps(meta))

                provider = provider or video['brplayprovider'] if 'brplayprovider' in video else provider

                action = 'playvod' if not meta['live'] else 'playlive'

                url = '%s?action=%s&provider=%s&id_globo_videos=%s&meta=%s' % (sysaddon, action, provider, video['id'], sysmeta)

                item = control.item(label=label)

                local_fanart = fanart if fanart is not None else meta['fanart'] if 'fanart' in meta else GLOBO_FANART

                clearlogo = meta['clearlogo'] if 'clearlogo' in meta else None

                poster = meta['poster'] if 'poster' in meta else poster

                art = {'thumb': meta['thumb'], 'poster': poster, 'fanart': local_fanart, 'clearlogo': clearlogo}

                item.setProperty('Fanart_Image', local_fanart)

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

                if 'date' not in meta:
                    sort = False

                item.setArt(art)
                item.setProperty('IsPlayable', "true")
                item.setInfo(type='video', infoLabels = meta)

                cm = [(refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon)]
                if provider == 'globosat':
                    if is_favorite:
                        cm.append((removeFavorite, 'RunPlugin(%s?action=delFavorites&id_globo_videos=%s)' % (sysaddon,video['id'])))
                    else:
                        cm.append((addFavorite, 'RunPlugin(%s?action=addFavorites&id_globo_videos=%s)' % (sysaddon,video['id'])))
                    if is_watchlater:
                        cm.append((removeWatchLater, 'RunPlugin(%s?action=delwatchlater&id_globo_videos=%s)' % (sysaddon,video['id'])))
                    else:
                        cm.append((addWatchLater, 'RunPlugin(%s?action=addwatchlater&id_globo_videos=%s)' % (sysaddon,video['id'])))
                item.addContextMenuItems(cm)

                # item.setMimeType("application/vnd.apple.mpegurl")

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)

        if next_page:
            if 'bingewatch' in meta and meta['bingewatch']:
                label = control.lang(34007).encode('utf-8')
            else:
                # 34006 = "Older Videos"
                label = control.lang(34006).encode('utf-8')

            meta = {}
            meta.update({'mediatype': 'video'})
            meta.update({'overlay': 6})
            meta.update({'title': label})

            url = '%s?action=%s&provider=%s&program_id=%s&category=%s&page=%s' % (sysaddon, next_action, provider, program_id, program_id, next_page)

            item = control.item(label=label)

            local_fanart = fanart if fanart is not None else meta['fanart'] if 'fanart' in meta else GLOBO_FANART

            item.setProperty('Fanart_Image', local_fanart)

            art = {'icon': NEXT_ICON, 'thumb': NEXT_ICON, 'poster': poster, 'fanart': local_fanart}

            # item.setProperty('Fanart_Image', GLOBO_FANART)

            item.setArt(art)
            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        if not next_page and next_action == 'openvideos' and sort:
            control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_DATE)
        else:
            control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_UNSORTED)

        control.content(syshandle, content)
        control.directory(syshandle, cacheToDisc=False)

    def seasons_directory(self, card):
        if card is None:
            control.idle()
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        # 32072 = "Refresh"
        refreshMenu = control.lang(32072).encode('utf-8')

        content = 'videos'

        seasons = card['seasons']

        for season in seasons:

            # label = video['label'] if 'label' in video else video['title']
            label = season['title']

            meta = card
            meta.update({'overlay': 6})
            meta.update({'mediatype': 'season'})  # string - "video", "movie", "tvshow", "season", "episode" or "musicvideo"

            # sysmeta = urllib.quote_plus(json.dumps(meta))

            provider = card['brplayprovider'] if 'brplayprovider' in card else 'globosat'

            action = 'openepisodes'

            url = '%s?action=%s&provider=%s&program_id=%s&season_id=%s' % (sysaddon, action, provider, card['id'], season['id'])

            item = control.item(label=label)

            local_fanart = meta['fanart'] if 'fanart' in meta else GLOBO_FANART

            poster = meta['poster'] if 'poster' in meta else None

            logo = meta['logo'] if 'logo' in meta else None

            art = {'thumb': local_fanart, 'poster': poster, 'fanart': local_fanart, 'clear_logo': logo}

            item.setProperty('Fanart_Image', local_fanart)

            item.setArt(art)
            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels={
                'year': season['year'],
                'season': season['number'],
                'overlay': 4,
                'mediatype': 'season',
                'plot': season['description'] or card['plot'],
                'plotoutline': season['description'] or card['plot'],
                'episode': season['episodes_number'],
                'season': card['season']
            })

            cm = [(refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon)]

            item.addContextMenuItems(cm)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_UNSORTED)

        control.content(syshandle, content)
        control.directory(syshandle, cacheToDisc=False)

    def programs_directory(self, items, folders=[], category=None, kind=None):
        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        # 32072 = "Refresh" 
        refreshMenu = control.lang(32072).encode('utf-8')

        has_playable_item = False

        for index, program in enumerate(items):

            label = program['name'] if 'name' in program else program['title'] if 'title' in program else ''

            media_kind = kind if kind is not None else program['kind'] if 'kind' in program else None

            is_music_video = media_kind == 'shows'
            is_movie = media_kind == 'movies'

            is_playable = is_music_video or is_movie

            is_bingewatch = media_kind == 'bingewatch'

            id_globo_videos = program['id_globo_videos'] if 'id_globo_videos' in program and program['id_globo_videos'] else None

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
                id_globo_videos = id_globo_videos or program['id']
                url = '%s?action=playvod&provider=%s&id_globo_videos=%s&meta=%s' % (sysaddon, program['brplayprovider'], id_globo_videos, sysmeta)
            else:
                if program['brplayprovider'] == 'globoplay':
                    url = '%s?action=openvideos&provider=%s&program_id=%s&id_globo_videos=%s&poster=%s&bingewatch=%s&fanart=%s' % (sysaddon, program['brplayprovider'], program['id'], id_globo_videos, thumb, is_bingewatch, fanart)
                else:
                    url = '%s?action=openvideos&provider=%s&id_globo_videos=%s' % (sysaddon, program['brplayprovider'], id_globo_videos)

            cm = [(refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon)]
            item.addContextMenuItems(cm)

            item.setArt(art)
            item.setProperty('IsPlayable', 'true' if is_playable else 'false')
            item.setInfo(type='video', infoLabels=meta)

            # if is_playable:
            #     item.setMimeType("application/vnd.apple.mpegurl")
            #     has_playable_item = True

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=not is_playable)

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_VIDEO_SORT_TITLE)
        #
        # if has_playable_item:
        #     control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL)
        # else:
        #     control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        for subcategory in folders:
            label = subcategory
            meta = {}
            meta.update({'title': subcategory})

            url = '%s?action=opencategory&provider=%s&category=%s&subcategory=%s' % (sysaddon, 'globoplay', urllib.quote_plus(category), urllib.quote_plus(subcategory))

            item = control.item(label=label)

            fanart = GLOBO_FANART

            art = {'fanart': fanart}

            if str(subcategory).lower() == 'replay':
                art.update({'thumb': REPLAY_ICON})
                art.update({'poster': REPLAY_ICON_POSTER})

            item.setArt(art)

            item.setProperty('Fanart_Image', fanart)

            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            cm = [(refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon)]
            item.addContextMenuItems(cm)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        control.content(syshandle, 'tvshows')
        control.directory(syshandle, cacheToDisc=False)

    def category_directory(self, items, extras, provider='globoplay'):
        if items is None or len(items) == 0:
            control.idle()
            sys.exit()

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

            cm = [(refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon)]
            item.addContextMenuItems(cm)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        # 4K Content
        if control.is_4k_enabled:
            label = control.lang(34107).encode('utf-8')
            meta = {}
            meta.update({'title': label})

            url = '%s?action=open4k&provider=%s' % (sysaddon, provider)

            item = control.item(label=label)

            fanart = GLOBO_FANART

            art = {'fanart': fanart}
            item.setArt(art)

            item.setProperty('Fanart_Image', fanart)

            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            cm = []
            cm.append((refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon))
            item.addContextMenuItems(cm)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        # Programas Locais
        label = control.lang(34106).encode('utf-8')
        meta = {}
        meta.update({'title': label})

        url = '%s?action=openlocal&provider=%s' % (sysaddon, provider)

        item = control.item(label=label)

        fanart = GLOBO_FANART

        art = {'fanart': fanart}
        item.setArt(art)

        item.setProperty('Fanart_Image', fanart)

        item.setProperty('IsPlayable', "false")
        item.setInfo(type='video', infoLabels=meta)

        cm = [(refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon)]
        item.addContextMenuItems(cm)

        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=False)

    def channel_directory(self, items):
        if items is None or len(items) == 0:
            control.idle()
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        #addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
        #addonFanart, settingFanart = control.addonFanart(), control.setting('fanart')

        try:
            isOld = False
            control.item().getArt('type')
        except:
            isOld = True

        # isPlayable = 'true' #if not 'plugin' in control.infoLabel('Container.PluginName') else 'false'

        #playbackMenu = control.lang(32063).encode('utf-8') if control.setting('hosts.mode') == '2' else control.lang(32064).encode('utf-8')

        #queueMenu = control.lang(32065).encode('utf-8')

        # 32072 = "Refresh" 
        refreshMenu = control.lang(32072).encode('utf-8')

        for i in items:
            # try:
            label = i['name']
            meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
            meta.update({'mediatype': 'video'})  # string - "video", "movie", "tvshow", "season", "episode" or "musicvideo"
            meta.update({'playcount': 0, 'overlay': 6})
            meta.update({'duration': i['duration']}) if 'duration' in i else None
            meta.update({'title': i['title']}) if 'title' in i else None
            meta.update({'tagline': i['tagline']}) if 'tagline' in i else None
            # meta.update({'aired': i['datetime']}) if 'datetime' in i else None
            # meta.update({'dateadded': i['datetime']}) if 'datetime' in i else None

            #"StartTime", "EndTime", "ChannelNumber" and "ChannelName"

            sysmeta = urllib.quote_plus(json.dumps(meta))
            id_globo_videos = i['id']
            id_cms = i['id_cms'] if 'id_cms' in i and i['id_cms'] is not None else ''
            slug = i['slug'] if 'slug' in i and i['slug'] is not None else ''
            brplayprovider = i['brplayprovider']

            url = '%s?action=openchannel&provider=%s&id_globo_videos=%s&id_cms=%s&slug=%s&meta=%s&t=%s' % (sysaddon, str(brplayprovider), id_globo_videos, id_cms, urllib.quote_plus(slug), sysmeta, self.systime)

            cm = [(refreshMenu, 'RunPlugin(%s?action=refresh)' % sysaddon)]

            #cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))

            if isOld is True:
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
            # elif not addonFanart is None:
            #     item.setProperty('Fanart_Image', addonFanart)

            if 'fanart' in i:
                item.setProperty('Fanart_Image', i['fanart'])
            else:
                item.setProperty('Fanart_Image', control.addonFanart())

            item.setArt(art)
            item.addContextMenuItems(cm)
            item.setProperty('IsPlayable', "false")
            item.setInfo(type='video', infoLabels=meta)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
            # except:
            #     pass

        control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.category(handle=syshandle, category=control.lang(32002).encode('utf-8'))

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=False)

    def category_combate_directory(self, items):
        if items is None or len(items) == 0: control.idle() ; sys.exit()

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

    def state_directory(self, items, provider='globoplay'):
        if items is None or len(items) == 0:
            control.idle() ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        # 32072 = "Refresh"
        refreshMenu = control.lang(32072).encode('utf-8')

        for state in items:
            label = state
            meta = {}
            meta.update({'title': state})

            url = '%s?action=openlocal&provider=%s&state=%s' % (sysaddon, provider, state)

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

    def region_directory(self, items, provider='globoplay'):
        if items is None or len(items) == 0:
            control.idle() ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        # 32072 = "Refresh"
        refreshMenu = control.lang(32072).encode('utf-8')

        for region in items:
            label = region['region_group_name'] + " (%s)" % region['affiliate_name']
            meta = {}
            meta.update({'title': label})

            url = '%s?action=openlocal&provider=%s&region=%s' % (sysaddon, provider, region['affiliate_code'])

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
