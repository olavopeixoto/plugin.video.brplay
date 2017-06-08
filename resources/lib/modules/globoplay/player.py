import json
import re
import sys

import xbmc

import auth
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules.util import get_signed_hashes


class Player(xbmc.Player):
    def __init__(self):
        super(Player, self).__init__()
        self.sources = []
        self.offset = 0.0
        self.isLive = False

    def play(self, id, meta):

        if id == None: return

        try: meta = json.loads(meta)
        except: meta = {
            "playcount": 0,
            "overlay": 6,
            "mediatype": "video",
            "aired": None
        }

        if 'live' in meta and meta['live'] == True:
            info = self.__getLiveVideoInfo(id, meta['affiliate'] if 'affiliate' in meta else None)
        else:
            info = self.__getVideoInfo(id)

        title = meta['title'] if 'title' in meta else info['title']

        signed_hashes = get_signed_hashes(info['hash'])

        query_string = re.sub(r'{{(\w*)}}', r'%(\1)s', info['query_string_template'])

        query_string = query_string % {
            'hash': signed_hashes[0],
            'key': 'app',
            'openClosed': 'F',
            'user': info['user'] if info['subscriber_only'] else ''
        }

        url = '?'.join([info['url'], query_string])

        control.log("live media url: %s" % url)

        meta.update({
            "genre": info["category"],
            "plot": info["title"],
            "plotoutline": info["title"],
            "title": title
        });

        poster = meta['poster'] if 'poster' in meta else control.addonPoster()
        thumb = meta['thumb'] if 'thumb' in meta else info["thumbUri"]

        # playlist, cookies = m3u8.load(url)
        #
        # control.log("PLAYLIST[0].bandwidth: %s" % repr(playlist.playlists[0].stream_info.bandwidth))
        # control.log("PLAYLIST[0].uri: %s" % repr(playlist.playlists[0].absolute_uri))
        # control.log("PLAYLIST[0].cookies: %s" % repr(cookies))
        #
        # cookies_str = urllib.urlencode(cookies.get_dict()).replace('&', '; ') + ';'
        #
        # url = playlist.playlists[0].absolute_uri + '|Cookie=' + urllib.quote(cookies_str)

        # control.log("FINAL URL: %s" % url)

        item = control.item(path=url)

        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'tvshow.poster': poster, 'season.poster': poster})
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='video', infoLabels=meta)

        syshandle = int(sys.argv[1])

        self.offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0

        item.setContentLookup(False)

        # control.player.play(url, item)
        control.resolve(syshandle, True, item)

        self.isLive = 'live' in meta and meta['live'] == True

    #     if self.isLive:
    #         self.keepPlaybackAlive(item, meta)
    #
    # def onPlayBackStarted(self):
    #     control.log('onPlayBackStarted!!!')
    #
    #     # control.execute('Dialog.Close(all,true)')
    #     if self.offset > 0:
    #         control.log('SET SEEKTIME TO: %s' % str(self.offset))
    #         self.seekTime(self.offset)
    #
    # def onPlayBackResumed(self):
    #     control.log('onPlayBackResumed!!!')
    #
    #
    # def keepPlaybackAlive(self, item, meta):
    #     code = meta['affiliate_code'] if 'affiliate_code' in meta else 'RJ'
    #
    #     for i in range(0, 240):
    #         if self.isPlayingVideo(): break
    #         xbmc.sleep(1000)
    #
    #     while self.isPlayingVideo():
    #         control.log("IS PLAYING: TRUE")
    #         live_program = scraper_live.getLiveProgram(code)
    #         program_description = scraper_live.getProgramDescription(live_program['program_id_epg'], live_program['program_id'], code)
    #         meta.update({
    #             'title': 'PLAYING: Globo ' + re.sub(r'\d+','',code) + '[I] - ' + program_description['title'] + '[/I]',
    #             'tvshowtitle': program_description['tvshowtitle'] if 'tvshowtitle' in program_description else None
    #         })
    #         control.log("UPDATING META TO: %s" % repr(meta))
    #         item.setInfo(type='video', infoLabels=meta)
    #         xbmc.sleep(60000)

    def __getVideoInfo(self, id):

        proxy = control.setting('proxy_url')
        proxy = None if proxy == None or proxy == '' else {
            'http': proxy,
            'https': proxy,
        }

        # control.log("VIDEO INFO")

        playlistUrl = 'http://api.globovideos.com/videos/%s/playlist'
        playlistJson = client.request(playlistUrl % id, headers={"Accept-Encoding": "gzip"})

        if not playlistJson or not 'videos' in playlistJson or len(playlistJson['videos']) == 0: #Video Not Available
            control.infoDialog(control.lang(31200).encode('utf-8'), heading=str('Video Info Not Found'), sound=True, icon='ERROR')
            control.idle(); sys.exit()
            return None
            # raise Exception("Player version not found.")

        playlistJson = playlistJson['videos'][0]

        for node in playlistJson['resources']:
            if any("ios" in s for s in node['players']):
                resource = node
                break

        if resource == None:
            control.infoDialog(control.lang(31200).encode('utf-8'), heading=str('Video Resource Not Found'), sound=True, icon='ERROR')
            control.idle()
            sys.exit()
            return None

        resource_id = resource['_id']

        username = control.setting('globoplay_username')
        password = control.setting('globoplay_password')

        #authenticate
        credentials = auth.auth().authenticate(username, password)
        hashUrl = 'http://security.video.globo.com/videos/%s/hash?resource_id=%s&version=1.1.23&player=ios' % (id, resource_id)
        hashJson = client.request(hashUrl, cookie=credentials, mobile=True, headers={"Accept-Encoding": "gzip"}, proxy=proxy)

        return {
            "id": playlistJson["id"],
            "title": playlistJson["title"],
            "duration": int(resource["duration"]),
            "program": playlistJson["program"],
            "program_id": playlistJson["program_id"],
            "provider_id": playlistJson["provider_id"],
            "channel": playlistJson["channel"],
            "channel_id": playlistJson["channel_id"],
            "category": playlistJson["category"],
            "subscriber_only": playlistJson["subscriber_only"],
            "exhibited_at": playlistJson["exhibited_at"],
            "player": "ios",
            "url": resource["url"],
            "query_string_template": resource["query_string_template"],
            "thumbUri": None,
            "hash": hashJson["hash"],
            "user": None
        }

    def __getLiveVideoInfo(self, id, geolocation):

        username = control.setting('globoplay_username')
        password = control.setting('globoplay_password')
        affiliate = control.setting('globo_affiliate')

        if affiliate == "All" and geolocation != None:
            post_data = geolocation + "&player=ios&version=1.1.23"
        elif affiliate == "Sao Paulo":
            post_data = "lat=-23.5505&long=-46.6333&player=ios&version=1.1.23"
        elif affiliate == 'Brasilia':
            post_data = "lat=-15.7942&long=-47.8825&player=ios&version=1.1.23"
        elif affiliate == 'Belo Horizonte':
            post_data = "lat=-19.9245&long=-43.9352&player=ios&version=1.1.23"
        else: #Rio de Janeiro
            post_data = "lat=-22.900&long=-43.172&player=ios&version=1.1.23"

        #authenticateurl
        credentials = auth.auth().authenticate(username, password)

        #4452349
        hashUrl = 'http://security.video.globo.com/videos/%s/hash' % id
        hashJson = client.request(hashUrl, error=True, cookie=credentials, mobile=True, headers={
            "Accept-Encoding": "gzip",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Globo Play/0 (iPhone)"
        }, post=post_data)

        return {
            "id": "-1",
            "title": hashJson["name"],
            # "program": playlistJson["program"],
            # "program_id": playlistJson["program_id"],
            # "provider_id": playlistJson["provider_id"],
            # "channel": playlistJson["channel"],
            # "channel_id": playlistJson["channel_id"],
            "category": 'Live',
            # "subscriber_only": playlistJson["subscriber_only"],
            "subscriber_only": 'true',
            # "exhibited_at": playlistJson["exhibited_at"],
            "player": "ios",
            "url": hashJson["url"],
            "query_string_template": "h={{hash}}&k={{key}}&a={{openClosed}}&u={{user}}",
            "thumbUri": hashJson["thumbUri"],
            "hash": hashJson["hash"],
            "user": hashJson["user"]
        }