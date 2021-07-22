# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import workers
from resources.lib.modules.globoplay import scraper_live as globoplay
from resources.lib.modules.globosat import scraper_live as globosat
from resources.lib.modules.sexyhotplay import scraper_live as sexyhotplay
from resources.lib.modules.oiplay import scraper_live as oiplay
from resources.lib.modules.tntplay import scraper_live as tntplay
from resources.lib.modules.netnow import scraper_live as netnow
from resources.lib.modules.sbt import scraper_live as sbt
from resources.lib.modules.pluto import scraper_live as pluto


def get_channels():
    live = []

    threads = []

    if control.is_globoplay_available():
        threads.append(workers.Thread(globoplay.get_live_channels))

    if control.is_globosat_available():
        threads.append(workers.Thread(globosat.get_live_channels))
        if control.show_adult_content:
            threads.append(workers.Thread(sexyhotplay.get_broadcast))

    if control.is_oiplay_available():
        threads.append(workers.Thread(oiplay.get_live_channels))

    if control.is_tntplay_available():
        threads.append(workers.Thread(tntplay.get_live_channels))

    if control.is_nowonline_available():
        threads.append(workers.Thread(netnow.get_live_channels))

    if control.is_sbt_available():
        threads.append(workers.Thread(sbt.get_live_channels))

    if control.is_pluto_available():
        threads.append(workers.Thread(pluto.get_live_channels))

    [i.start() for i in threads]
    [i.join() for i in threads]

    [live.extend(i.get_result()) for i in threads if i.get_result()]

    control.log(live)

    for channel in live:
        channel.update({
            'sort': [control.SORT_METHOD_DATEADDED, (control.SORT_METHOD_LABEL_IGNORE_FOLDERS, '%U'), (control.SORT_METHOD_VIDEO_SORT_TITLE, '%U'), (control.SORT_METHOD_STUDIO, '%L')],
            'overlay': 4,
            'playcount': 0,
            'content': 'tvshows',    # 'content': 'tvshows',  # content: files, songs, artists, albums, movies, tvshows, episodes, musicvideos
            'mediatype': 'episode',  # 'mediatype': "video", "movie", "tvshow", "season", "episode" or "musicvideo"
        })
        if channel.get('cast') is None:
            channel['cast'] = []
        properties = channel.get('properties', {})
        if not properties:
            channel['properties'] = properties
        properties.update({
            'ResumeTime': 0.0
        })

    return live
