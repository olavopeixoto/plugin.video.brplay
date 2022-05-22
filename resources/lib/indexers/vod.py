# -*- coding: utf-8 -*-

from resources.lib.modules import control
from resources.lib.modules.globosat import scraper_vod as globosat
from resources.lib.modules.globoplay import scraper_vod as globoplay
from resources.lib.modules.tntplay import scraper_vod as tnt_vod
from resources.lib.modules.netnow import scraper_vod as netnow
from resources.lib.modules.oiplay import scraper_vod as oiplay
from resources.lib.modules.pluto import scraper_vod as pluto
from resources.lib.modules.vix import scraper_vod as vix
from resources.lib.modules import workers
from itertools import cycle, islice, chain


def get_vod_channels_directory():

    channels = []

    if control.is_globoplay_available():
        channels.extend(globoplay.get_globoplay_channels())

    if control.is_globosat_available():
        channels.extend(globosat.get_authorized_channels())

    if control.is_tntplay_available():
        channels.extend(tnt_vod.get_channels())

    if control.is_nowonline_available():
        channels.extend(netnow.get_channels())

    if control.is_oiplay_available():
        channels.extend(oiplay.get_channels())

    if control.is_pluto_available():
        channels.extend(pluto.get_channels())

    if control.is_vix_available():
        channels.extend(vix.get_channels())

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

    if control.is_oiplay_available():
        threads.append(workers.Thread(convert_to_list, oiplay.search, query, page))

    if control.is_nowonline_available():
        threads.append(workers.Thread(convert_to_list, netnow.search, query, page))

    if control.is_tntplay_available():
        threads.append(workers.Thread(convert_to_list, tnt_vod.search, query, page))

    [i.start() for i in threads]
    [i.join() for i in threads]

    all_results = (thread.get_result() for thread in threads)

    all_results = list(filter(lambda x: x, all_results))

    # combined = list(roundrobin(*all_results))
    combined = chain(*all_results)

    has_next_page = False

    if not combined:
        control.okDialog(line1=control.lang(34141), heading=control.lang(32010))
        yield control.run_plugin_url()
        return

    for result in combined:
        if result.get('page'):
            has_next_page = True
            continue

        result.update({
            'sort': [(control.SORT_METHOD_TRACKNUM, '%T', '%U')],
            'tracknumber': levenshtein_distance(str(query).lower(), str(result.get('title')).lower()),
        })

        yield result

    if has_next_page:
        yield {
            'handler': __name__,
            'method': search.__name__,
            'query': query,
            'page': page+1,
            'label': '%s (%s)' % (control.lang(34136), page+1),
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
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))


def levenshtein_distance(str1, str2):
    from difflib import ndiff
    counter = {"+": 0, "-": 0}
    distance = 0
    for edit_code, *_ in ndiff(str1, str2):
        if edit_code == " ":
            distance += max(counter.values())
            counter = {"+": 0, "-": 0}
        else:
            counter[edit_code] += 1
    distance += max(counter.values())
    return distance
