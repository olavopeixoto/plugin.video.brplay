# -*- coding: utf-8 -*-

import os
import sys
import urllib
import vod

from resources.lib.modules import control, cache
# from resources.lib.modules import trakt

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])

artPath = control.artPath()
addonFanart = control.addonFanart()

# traktCredentials = trakt.getTraktCredentialsInfo()
# traktIndicators = trakt.getTraktIndicatorsInfo()


class navigator:
    def root(self):
        if control.is_globosat_available() or control.is_globoplay_available() or control.is_oiplay_available() or control.is_tntplay_available() or control.is_nowonline_available():
            self.add_directory_item(32001, 'liveChannels', 'live.png', 'live.png')
            if control.is_globosat_available() or control.is_globoplay_available() or control.is_tntplay_available() or control.is_nowonline_available():
                self.add_directory_item(32002, 'vodChannels', 'ondemand.png', 'ondemand.png')
        else:
            self.add_directory_item(32005, 'settings', 'tools.png', 'tools.png')

        if control.is_globosat_available():
            self.add_directory_item(32080, 'featured', 'featured.png', 'featured.png')
            self.add_directory_item(32090, 'favorites', 'favorites.png', 'favorites.png')
            self.add_directory_item(32095, 'watchlater', 'userlists.png', 'userlists.png')
            self.add_directory_item(32096, 'watchhistory', 'years.png', 'years.png')

        if control.is_globosat_available() or control.is_globoplay_available():
            self.add_directory_item(32010, 'searchMenu', 'search.png', 'search.png')

        # control.addSortMethod(int(sys.argv[1]), control.SORT_METHOD_LABEL_IGNORE_FOLDERS)

        control.content(syshandle, 'files')

        self.end_directory()

    def openSettings(self):
        control.openSettings('globoplay_username')
        control.refresh()

    def searchMenu(self):

        t = control.lang(32010).encode('utf-8')
        k = control.keyboard('', t)
        k.doModal()
        q = k.getText()

        if not k.isConfirmed():
            return

        self.search(q)

    def search(self, query, page=1):
        vod.Vod().search(query, page)

    def clear_cache(self):
        control.idle()

        yes = control.yesnoDialog(control.lang(32056).encode('utf-8'), '', '')

        if not yes:
            return

        cache.delete_file()

        control.infoDialog(control.lang(32057).encode('utf-8'), sound=True, icon='INFO')

    def clear_credentials(self):
        control.idle()

        yes = control.yesnoDialog(control.lang(32056).encode('utf-8'), '', '')

        if not yes:
            return

        control.clear_credentials()

        control.infoDialog(control.lang(32057).encode('utf-8'), sound=True, icon='INFO')

    def cache_auth(self):
        import resources.lib.modules.globosat.scraper_vod as scraper_vod

        cache.get(scraper_vod.get_authorized_channels, 1)

    def add_directory_item(self, name, query, thumb, icon, queue=False, isAction=True, isFolder=True):
        try: name = control.lang(name).encode('utf-8')
        except: pass
        url = '%s?action=%s' % (sysaddon, query) if isAction else query
        thumb = os.path.join(artPath, thumb) if not artPath is None else icon
        item = control.item(label=name)
        item.setArt({'icon': thumb, 'thumb': thumb})
        if not addonFanart is None: item.setProperty('Fanart_Image', addonFanart)
        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

    def end_directory(self):
        control.content(syshandle, 'addons')
        control.directory(syshandle, cacheToDisc=True)


