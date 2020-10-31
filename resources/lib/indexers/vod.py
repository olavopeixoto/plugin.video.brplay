# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules.globosat import scraper_vod as globosat
from resources.lib.modules.sexyhotplay import scraper_vod as sexyhot
from resources.lib.modules.globoplay import scraper_vod as globoplay
from resources.lib.modules.tntplay import scraper_vod as tnt_vod
from resources.lib.modules.netnow import scraper_vod as netnow
from resources.lib.modules.telecine import scraper_vod as telecine


def get_vod_channels_directory():
    from resources.lib.indexers import indexer

    channels = []

    if control.is_globosat_available():
        channels.extend(globosat.get_authorized_channels())
        if control.show_adult_content:
            channels.extend(sexyhot.get_channels())

    if control.is_globoplay_available():
        channels.extend(globoplay.get_globoplay_channels())

    if control.is_tntplay_available():
        channels.extend(tnt_vod.get_channels())

    if control.is_nowonline_available():
        channels.extend(netnow.get_channels())

    if control.is_telecine_available():
        channels.extend(telecine.get_channels())

    channels = sorted(channels, key=lambda k: k.get('label', ''))

    if not control.show_adult_content:
        channels = [channel for channel in channels if not channel.get("adult", False)]

    indexer.create_directory(channels)
