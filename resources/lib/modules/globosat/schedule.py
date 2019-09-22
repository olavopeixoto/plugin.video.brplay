import datetime
from resources.lib.modules import client
from resources.lib.modules import util
from resources.lib.modules import workers


class schedule:

    def get_schedule(self):

        schedule = []

        threads = [
            workers.Thread(self._get_globosat_schedule, schedule),
            workers.Thread(self._get_combate_schedule, schedule)
        ]
        [i.start() for i in threads]
        [i.join() for i in threads]

        return schedule

    def _get_globosat_schedule(self, schedule):
        globosat_schedule_url = "http://api.simulcast.globosat.tv/globosatplay/?page=%s"
        headers = {
            "User-Agent": "GlobosatPlay/142 CFNetwork/811.4.18 Darwin/16.5.0",
            "Authorization": "Token 59150c4cc6a00f467bf225cf3bf8f44617e27037",
            "Accept-Encoding": "gzip, deflate"
        }

        page = 1
        response = client.request(globosat_schedule_url % page, headers=headers)

        results = response['results']

        while response['next'] != None:
            page += 1
            response = client.request(globosat_schedule_url % page, headers=headers)
            results += response['results']

        for result in results:
            beginsAt = util.strptime_workaround(result['day'], '%d/%m/%Y %H:%M') + util.get_utc_delta()
            schedule.append({
                "name": result['channel']['title'],
                "title": result['title'],
                "description": result['subtitle'],
                "begins_at": beginsAt.isoformat(),
                "ends_at": beginsAt + datetime.timedelta(minutes=result['duration']),
                "id": result['id_midia_live_play'],
                "program_id": None,
                "live_poster": None,
                "thumbnail": result['channel']['url_snapshot'],
                "thumbnail_hd": result['channel']['url_snapshot'],
                "fanart": result['thumb_cms'],
                "color": result['channel']['color']
            })

        return schedule

    def _get_combate_schedule(self, schedule):
        globosat_schedule_url = "http://api.simulcast.globosat.tv/combate/?page=%s"
        headers = {
            "User-Agent": "GlobosatPlay/142 CFNetwork/811.4.18 Darwin/16.5.0",
            "Authorization": "Token 59150c4cc6a00f467bf225cf3bf8f44617e27037",
            "Accept-Encoding": "gzip, deflate"
        }

        page = 1
        response = client.request(globosat_schedule_url % page, headers=headers)

        results = response['results']

        while response['next'] is not None:
            page += 1
            response = client.request(globosat_schedule_url % page, headers=headers)
            results += response['results']

        for result in results:
            beginsAt = util.strptime_workaround(result['day'], '%d/%m/%Y %H:%M') + util.get_utc_delta()
            schedule.append({
                "name": result['channel']['title'],
                "title": result['title'],
                "description": result['subtitle'],
                "begins_at": beginsAt.isoformat(),
                "ends_at": beginsAt + datetime.timedelta(minutes=result['duration']),
                "id": result['id_midia_live_play'],
                "program_id": None,
                "live_poster": None,
                "thumbnail": result['channel']['url_snapshot'],
                "thumbnail_hd": result['channel']['url_snapshot'],
                "fanart": result['thumb_cms'],
                "color": result['channel']['color']
            })

        return schedule
