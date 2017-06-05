from resources.lib.modules import workers


class Indexer:
    def __init__(self):
        pass

    def get_live(self):
        import scraper_live as scraper

        live = []

        threads = [
            workers.Thread(self.__append_result, scraper.get_basic_live_channels, live),
            workers.Thread(self.__append_result, scraper.get_combate_live_channels, live),
            workers.Thread(self.__append_result, scraper.get_premiere_live_channels, live)
        ]
        [i.start() for i in threads]
        [i.join() for i in threads]

        return live

    def __append_result(self, fn, list, *args):
        list += fn(*args)

    def get_channel_programs(self, channel_id):
        import scraper_vod as scraper

        programs = scraper.get_channel_programs(channel_id)

        for item in programs:
            item["brplayprovider"] = "globosat"

        return programs

    def get_vod(self):
        import scraper_vod as scraper

        vod = scraper.get_authorized_channels()

        for item in vod:
            item["brplayprovider"] = "globosat" if item['slug'] != 'sexyhot' else 'sexyhot'

        return vod

    def get_pfc(self, meta):
        import scraper_live as scraper
        pfc = scraper.get_premiere_games(meta)

        for item in pfc:
            item["brplayprovider"] = "globosat"

        return pfc

    def get_fighters(self, letter):
        import scraper_combate as scraper
        return scraper.get_fighters(letter)

    def get_fighter_videos(self, slug, page):
        import scraper_combate as scraper
        return scraper.get_fighter_videos(slug, page)

    def search(self, q, page=1):
        import scraper_vod as scraper

        return scraper.search(q, page)