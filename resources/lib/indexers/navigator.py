# -*- coding: utf-8 -*-

import os
import vod
import live
from resources.lib.modules import control, cache

artPath = control.artPath()
addonFanart = control.addonFanart()


def root():

    if control.is_live_available():
        handler = live.__name__
        method = 'get_channels'
        yield add_directory_item(handler, method, 32001, 'live.png')

    if control.is_vod_available():
        handler = vod.__name__
        method = 'get_vod_channels_directory'
        yield add_directory_item(handler, method, 32002, 'ondemand.png')

    if not control.is_live_available() and not control.is_vod_available():
        handler = __name__
        method = 'open_settings'
        yield add_directory_item(handler, method, 32005, 'tools.png')


def open_settings():
    control.openSettings('globoplay_username')
    control.refresh()


def search_menu():

    t = control.lang(32010).encode('utf-8')
    k = control.keyboard('', t)
    k.doModal()
    q = k.getText()

    if not k.isConfirmed():
        return

    search(q)


def search(query, page=1):
    vod.search(query, page)


def clear_cache():
    control.idle()

    yes = control.yesnoDialog(control.lang(32056).encode('utf-8'), '', '')

    if not yes:
        return

    cache.delete_file()

    control.infoDialog(control.lang(32057).encode('utf-8'), sound=True, icon='INFO')


def clear_credentials():
    control.idle()

    yes = control.yesnoDialog(control.lang(32056).encode('utf-8'), '', '')

    if not yes:
        return

    control.clear_credentials()

    control.infoDialog(control.lang(32057).encode('utf-8'), sound=True, icon='INFO')


def add_directory_item(handler, method, lang, thumb_file_name):

    return {
        'handler': handler,
        'method': method,
        'label': control.lang(lang).encode('utf-8'),
        'art': {
            'thumb': os.path.join(artPath, thumb_file_name) if artPath else None,
            'fanart': addonFanart
        }
    }
