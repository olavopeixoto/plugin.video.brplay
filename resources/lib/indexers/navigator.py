# -*- coding: utf-8 -*-

import os
from . import vod
from . import live
from resources.lib.modules import control, cache

artPath = control.artPath()
addonFanart = control.addonFanart()


def root():
    if control.is_live_available():
        handler = live.__name__
        method = live.get_channels.__name__
        yield add_directory_item(handler, method, 32001, 'live.png')

    if control.is_vod_available():
        handler = vod.__name__
        method = vod.get_vod_channels_directory.__name__
        yield add_directory_item(handler, method, 32002, 'ondemand.png')

    if not control.is_live_available() and not control.is_vod_available():
        handler = __name__
        method = open_settings.__name__
        yield add_directory_item(handler, method, 32005, 'tools.png')

    if control.is_globosat_available() or control.is_globoplay_available() or control.is_oiplay_available() or control.is_nowonline_available() or control.is_tntplay_available():
        handler = __name__
        method = search.__name__
        yield add_directory_item(handler, method, 32010, 'search.png')


def open_settings():
    control.openSettings('globoplay_username')
    control.refresh()


def search(query=None, page=1):
    if not query:
        query = control.dialog.input(control.lang2(24121))

    return vod.search(query, page)


def clear_cache():
    control.idle()

    yes = control.yesnoDialog(control.lang(32056))

    if not yes:
        return

    cache.delete_file()

    control.infoDialog(control.lang(32057), sound=True, icon='INFO')


def clear_credentials():
    control.idle()

    yes = control.yesnoDialog(control.lang(32056))

    if not yes:
        return

    control.clear_credentials()

    control.infoDialog(control.lang(32057), sound=True, icon='INFO')


def add_directory_item(handler, method, lang, thumb_file_name):

    return {
        'handler': handler,
        'method': method,
        'label': control.lang(lang),
        'art': {
            'thumb': os.path.join(artPath, thumb_file_name) if artPath else None,
            'fanart': addonFanart
        }
    }
