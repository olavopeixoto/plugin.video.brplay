# -*- coding: utf-8 -*-

from resources.lib.modules import cache


class Indexer:

    def get_live_channels(self):

        import scraper_live as scraper

        live = scraper.get_live_channels()

        return live

    def get_vod(self):

        import scraper_vod as scraper
        vod = scraper.get_globoplay_channels()

        for item in vod:
            item["brplayprovider"] = "globoplay"

        return vod

    def get_channel_categories(self):

        import scraper_vod as scraper
        categories, programs = cache.get(scraper.get_globo_programs, 1)

        return categories

    def get_extra_categories(self):

        import scraper_vod as scraper
        categories = cache.get(scraper.get_extra_sections, 1)

        return categories

    def get_category_programs(self, category, subcategory=None):

        import scraper_vod as scraper
        categories, category_programs = cache.get(scraper.get_globo_programs, 1)

        if type(category) != unicode:
            category = unicode(category, 'UTF-8')

        category_data = next(category_program for category_program in category_programs if category_program['category'] == category)

        if subcategory is not None:
            return next(category_program for category_program in category_data['subcategories'] if category_program['category'] == subcategory)['programs']
        else:
            return category_data['programs']

    def get_category_subcategories(self, category):

        import scraper_vod as scraper
        categories, category_programs = cache.get(scraper.get_globo_programs, 1)

        if type(category) != unicode:
            category = unicode(category, 'UTF-8')

        subcategories = next(category_program for category_program in category_programs if category_program['category'] == category)['subcategories']

        return [subcategory['category'] for subcategory in subcategories]

    def get_videos_by_category(self, category, page=1):

        import scraper_vod as scraper
        episodes, next_page, total_pages = scraper.get_globo_extra_episodes(category, page)

        for episode in episodes:
            episode['brplayprovider'] = 'globoplay'

        return episodes, next_page, total_pages

    def get_videos_by_program(self, program_id, page=1, bingewatch=False):

        import scraper_vod as scraper
        from resources.lib.modules import control

        episodes, nextpage, total_pages, days = scraper.get_globo_episodes(program_id, page, bingewatch) if control.setting("globo_play_full_videos") == 'true' else scraper.get_globo_partial_episodes(program_id, page, bingewatch)

        for episode in episodes:
            episode['brplayprovider'] = 'globoplay'

        return episodes, nextpage, total_pages, days

    def get_videos_by_program_date(self, program_id, date, bingewatch=False):

        import scraper_vod as scraper

        episodes = scraper.get_globo_episodes_by_date(program_id, date, bingewatch)

        for episode in episodes:
            episode['brplayprovider'] = 'globoplay'

        return episodes

    def get_program_dates(self, program_id):

        import scraper_vod as scraper

        days, last = scraper.get_program_dates(program_id)

        return days

    def search(self, q, page=1):

        import scraper_vod as scraper

        return scraper.search(q, page)

    def get_states(self):

        import scraper_vod as scraper

        return cache.get(scraper.get_states, 1)

    def get_regions(self, state):

        import scraper_vod as scraper

        return cache.get(scraper.get_regions, 1, state)

    def get_programs_by_region(self, region):

        import scraper_vod as scraper

        return cache.get(scraper.get_programs_by_region, 1, region)

    def get_4k(self):

        import scraper_vod as scraper

        return cache.get(scraper.get_4k, 1)