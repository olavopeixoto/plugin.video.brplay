from resources.lib.modules import workers
from resources.lib.modules import cache


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

        authorized_channels = [channel for channel in self.get_authorized_channels() if channel["live"]]

        live = [channel for channel in live if self.is_in(channel, authorized_channels)]

        return live

    def is_in(self, live, channels):
        for channel in channels:
            if channel['id'] == live['channel_id']:
                return True

        return False

    def __append_result(self, fn, list, *args):
        list += fn(*args)

    def get_channel_programs(self, channel_id):
        import scraper_vod as scraper

        programs = scraper.get_channel_programs(channel_id)

        for item in programs:
            item["brplayprovider"] = "globosat"

        return programs

    def get_authorized_channels(self):
        import scraper_vod as scraper

        channels = cache.get(scraper.get_authorized_channels, 360, table="auth_channels")

        return channels

    def get_vod(self):
        vod = self.get_authorized_channels()

        vod = [channel for channel in vod if channel["vod"] and not channel["slug"].startswith("sportv-") and not channel["slug"].startswith("big-brother-brasil")]

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