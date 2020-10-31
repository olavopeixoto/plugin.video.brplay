# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules import workers
from resources.lib.modules.globoplay import scraper_live as globoplay
from resources.lib.modules.globosat import scraper_live as globosat
from resources.lib.modules.sexyhotplay import scraper_live as sexyhotplay
from resources.lib.modules.oiplay import scraper_live as oiplay
from resources.lib.modules.tntplay import scraper_live as tntplay
from resources.lib.modules.netnow import scraper_live as netnow


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

    [i.start() for i in threads]
    [i.join() for i in threads]

    [live.extend(i.get_result()) for i in threads if i.get_result()]

    control.log(live)

    live = sorted(live, key=lambda k: k['sorttitle'])
    live = sorted(live, key=lambda k: k['dateadded'] if 'dateadded' in k else None, reverse=True)

    return live
