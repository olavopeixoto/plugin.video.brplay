import re

from resources.lib.modules import client
from resources.lib.modules import control


class schedule:

    def __init__(self):
        pass

    def get_schedule(self):

        # In Settings.xml - globo_affiliate
        # "0" = All
        # "1" = Rio de Janeiro
        # "2" = Sao Paulo
        # "3" = Brasilia
        # "4" = Belo Horizonte
        # "5" = Recife

        if control.setting("globo_affiliate") == "2":
            affiliate_slug = "sao-paulo"
        elif control.setting("globo_affiliate") == "3":
            affiliate_slug = "distrito-federal"
        elif control.setting("globo_affiliate") == "4":
            affiliate_slug = "belo-horizonte"
        elif control.setting("globo_affiliate") == "5":
            affiliate_slug = "recife"
        else:
            affiliate_slug = "rio-de-janeiro"

        schedule_url = "https://globoplay.globo.com/v/xhr/views/schedule.json?affiliate_slug=%s" % affiliate_slug

        slots = client.request(schedule_url, headers={'Accept-Encoding': 'gzip'})['schedule']['slots']

        result = []

        for slot in slots:
            result.append({
                "title": slot['title'],
                "description": slot['description'],
                "begins_at": slot['begins_at'],
                "ends_at": slot['ends_at'],
                "id": re.match('/v/(\d+)/', slot['video_url']).group(1) if slot['video_url'] != None else None,
                "channel_id": 196,
                "program_id": re.match('/[^/]+/p/(\d+)/', slot['program_url']).group(1) if slot['program_url'] != None else None,
                "live_poster": slot['live_poster'],
                "thumbnail": slot['thumbnail'],
                "thumbnail_hd": slot['thumbnail_hd']
            })

        return result