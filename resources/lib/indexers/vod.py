# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules.globosat import scraper_vod as globosat
from resources.lib.modules.sexyhotplay import scraper_vod as sexyhot
from resources.lib.modules.globoplay import scraper_vod as globoplay
from resources.lib.modules.tntplay import scraper_vod as tnt_vod
from resources.lib.modules.netnow import scraper_vod as netnow
from resources.lib.modules.telecine import scraper_vod as telecine
from resources.lib.modules.oiplay import scraper_vod as oiplay
from resources.lib.modules import workers
from itertools import cycle, islice, chain
import random


def get_vod_channels_directory():

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

    if control.is_oiplay_available():
        channels.extend(oiplay.get_channels())

    if not control.show_adult_content:
        channels = [channel for channel in channels if not channel.get("adult", False)]

    for channel in channels:
        channel.update({
            'sort': control.SORT_METHOD_LABEL
        })

        yield channel


def search(query, page=1):
    if not query:
        yield control.run_plugin_url()
        return

    print('[BRplay] - search: %s | %s' % (query, page))
    threads = []

    if control.is_globoplay_available():
        threads.append(workers.Thread(convert_to_list, globoplay.search, query, page))

    if control.is_globosat_available():
        threads.append(workers.Thread(convert_to_list, globosat.search, query, page))

    if control.is_telecine_available():
        threads.append(workers.Thread(convert_to_list, telecine.search, query, page))

    if control.is_oiplay_available():
        threads.append(workers.Thread(convert_to_list, oiplay.search, query, page))

    if control.is_nowonline_available():
        threads.append(workers.Thread(convert_to_list, netnow.search, query, page))

    [i.start() for i in threads]
    [i.join() for i in threads]

    random.shuffle(threads)

    all_results = (thread.get_result() for thread in threads)

    control.log(all_results)

    combined = list(roundrobin(*all_results))
    # combined = chain(*all_results)

    has_next_page = False

    if not combined:
        control.okDialog(line1=control.lang(34141).encode('utf-8'), heading=control.lang(32010).encode('utf-8'))
        yield control.run_plugin_url()
        return

    rank = 1
    for result in combined:
        if result.get('page'):
            has_next_page = True
            continue

        result.update({
            'sort': [(control.SORT_METHOD_UNSORTED, '%U'), control.SORT_METHOD_STUDIO],
            # 'sort': [(control.SORT_METHOD_TRACKNUM, '%U'), control.SORT_METHOD_STUDIO, (control.SORT_METHOD_LABEL_IGNORE_FOLDERS, '%U')],
            'tracknumber': rank,
            'sorttitle': '%04d' % (rank,),
            'content': 'episodes',
            'mediatype': 'video'
        })

        rank += 1

        yield result

    if has_next_page:
        yield {
            'handler': __name__,
            'method': 'search',
            'query': query,
            'page': page+1,
            'label': '%s (%s)' % (control.lang(34136).encode('utf-8'), page+1),
            'art': {
                'poster': control.addonNext(),
                'fanart': control.addonFanart()
            },
            'properties': {
                'SpecialSort': 'bottom'
            }
        }


def convert_to_list(generator, *params):
    return list(generator(*params))


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))
