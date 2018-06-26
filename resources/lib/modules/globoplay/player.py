# -*- coding: utf-8 -*-

import json
import re
import sys
import urllib
import xbmc
import auth_helper
from urlparse import urlparse
from resources.lib.modules import hlshelper
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules.util import get_signed_hashes
from resources.lib.modules.globoplay import resourceshelper
import threading

HISTORY_URL = 'https://api.user.video.globo.com/watch_history/'
PLAYER_SLUG = 'android'
PLAYER_VERSION = '1.1.24'


class Player(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self)
        self.sources = []
        self.offset = 0.0
        self.isLive = False
        self.m3u8 = None
        self.cookies = None
        self.url = None
        self.item = None
        self.stopPlayingEvent = None
        self.credentials = None
        self.program_id = None
        self.video_id = None

    def onPlayBackStopped(self):
        control.log("PLAYBACK STOPPED")

        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def onPlayBackEnded(self):
        control.log("PLAYBACK ENDED")

        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def onPlayBackStarted(self):
        control.log("PLAYBACK STARTED")
        # if self.offset > 0: self.seekTime(float(self.offset))

    def play_stream(self, id, meta, children_id=None):

        if id is None: return

        try:
            meta = json.loads(meta)
        except:
            meta = {
                "playcount": 0,
                "overlay": 6,
                "mediatype": "video",
                "aired": None
            }

        self.isLive = False

        if 'livefeed' in meta and meta['livefeed'] == 'true':
            control.log("PLAY LIVE!")
            self.isLive = True
            info = self.__getLiveVideoInfo(id, meta['affiliate'] if 'affiliate' in meta else None)
            if info is None:
                return

            item, self.url, stopEvent = self.__get_list_item(meta, info)
        else:
            info = resourceshelper.get_video_info(id, children_id)
            if info is None:
                return

            if 'resource_id' not in info:
                control.log("PLAY CHILDREN!")
                items=[]
                xbmc.PlayList(1).clear()
                first=True
                for i in info:
                    hash, user, self.credentials = self.sign_resource(i['resource_id'], i['id'], i['player'], i['version'])
                    i['hash'] = hash
                    i['user'] = user
                    item, url, stopEvent = self.__get_list_item(meta, i, False)
                    if first:
                        self.url = url
                        first=False
                    items.append(item)
                    control.log("PLAYLIST ITEM URL: %s" % url)
                    xbmc.PlayList(1).add(url, item)
                item = items[0]
            else:
                control.log("PLAY SINGLE RESOURCE!")
                hash, user, self.credentials = self.sign_resource(info['resource_id'], info["id"], info['player'], info['version'], meta['anonymous'] if 'anonymous' in meta else False)
                info['hash'] = hash
                info['user'] = user
                item, self.url, stopEvent = self.__get_list_item(meta, info)

        self.offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0
        self.isLive = 'live' in meta and meta['live']

        syshandle = int(sys.argv[1])
        control.resolve(syshandle, True, item)

        self.stopPlayingEvent = threading.Event()
        self.stopPlayingEvent.clear()

        self.program_id = info['program_id'] if 'program_id' in info else None
        self.video_id = id

        first_run = True
        last_time = 0.0
        while not self.stopPlayingEvent.isSet():
            if control.monitor.abortRequested():
                control.log("Abort requested")
                break
            if self.isPlaying():
                if first_run:
                    self.showSubtitles(False)
                    first_run = False

                if not self.isLive:
                    total_time = self.getTotalTime()
                    current_time = self.getTime()
                    if current_time - last_time > 5 or (last_time == 0 and current_time > 1):
                        last_time = current_time
                        percentage_watched = current_time / total_time if total_time > 0 else 1.0 / 1000000.0
                        self.save_video_progress(self.credentials, self.program_id, self.video_id, current_time * 1000, fully_watched=0.9 < percentage_watched <= 1)
            control.sleep(500)

        if stopEvent:
            control.log("Setting stop event for proxy player")
            stopEvent.set()

        control.log("Done playing. Quitting...")

    def __get_list_item(self, meta, info, pick_bandwidth=True):
        hash = info['hash']
        user = info['user']

        title = info['title']  # or meta['title'] if 'title' in meta else None

        query_string = re.sub(r'{{(\w*)}}', r'%(\1)s', info['query_string_template'])

        query_string = query_string % {
            'hash': hash,
            'key': 'app',
            'openClosed': 'F' if info['subscriber_only'] else 'A',
            'user': user if info['subscriber_only'] else ''
        }

        url = '?'.join([info['url'], query_string])

        control.log("live media url: %s" % url)

        meta.update({
            "genre": info["category"],
            "plot": info["title"],
            "plotoutline": info["title"],
            "title": title
        })

        poster = meta['poster'] if 'poster' in meta else control.addonPoster()
        thumb = meta['thumb'] if 'thumb' in meta else info["thumbUri"]

        parsed_url = urlparse(url)
        if parsed_url.path.endswith(".m3u8"):
            if pick_bandwidth:
                url, mime_type, stopEvent, cookies = hlshelper.pick_bandwidth(url)
            else:
                mime_type, stopEvent, cookies = None, None, None
        else:
            # self.url = url
            mime_type, stopEvent, cookies = 'video/mp4', None, None

        if url is None:
            if stopEvent:
                control.log("Setting stop event for proxy player")
                stopEvent.set()
            control.infoDialog(message=control.lang(34100).encode('utf-8'), icon='ERROR')
            return None, None, None

        control.log("Resolved URL: %s" % repr(url))

        item = control.item(path=url)
        item.setInfo(type='video', infoLabels=meta)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'tvshow.poster': poster, 'season.poster': poster})
        item.setProperty('IsPlayable', 'true')

        item.setContentLookup(False)

        if parsed_url.path.endswith(".mpd"):
            mime_type = 'application/dash+xml'
            if not control.disable_inputstream_adaptive:
                control.log("Using inputstream.adaptive MPD")
                item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                item.setProperty('inputstreamaddon', 'inputstream.adaptive')

        if mime_type:
            item.setMimeType(mime_type)
        elif not cookies:
            item.setMimeType('application/vnd.apple.mpegurl')
            if not control.disable_inputstream_adaptive:
                control.log("Using inputstream.adaptive HLS")
                item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                item.setProperty('inputstreamaddon', 'inputstream.adaptive')

        # if self.offset > 0:
        #     duration = float(meta['duration']) if 'duration' in meta else 0
        #     if duration > 0:
        #         item.setProperty('StartPercent', str((self.offset / duration) * 100))

        # if self.offset > 0:
        #     item.setProperty('resumetime', str(self.offset))
        #     duration = float(meta['duration']) if 'duration' in meta else self.offset
        #     duration = duration * 1000.0
        #     item.setProperty('totaltime', str(duration))

        if 'subtitles' in info and info['subtitles'] and len(info['subtitles']) > 0:
            item.setSubtitles([sub['url'] for sub in info['subtitles']])

        return item, url, stopEvent

    def __getLiveVideoInfo(self, id, geolocation):

        credentials = auth_helper.get_credentials()

        if credentials is None:
            return None

        affiliate_temp = control.setting('globo_affiliate')

        # In settings.xml - globo_affiliate
        # 0 = All
        # 1 = Rio de Janeiro
        # 2 = Sao Paulo
        # 3 = Brasilia
        # 4 = Belo Horizonte
        # 5 = Recife
        if affiliate_temp == "0":
            affiliate = "All"
        elif affiliate_temp == "2":
            affiliate = "Sao Paulo"
        elif affiliate_temp == "3":
            affiliate = "Brasilia"
        elif affiliate_temp == "4":
            affiliate = "Belo Horizonte"
        elif affiliate_temp == "5":
            affiliate = "Recife"
        else:
            affiliate = "Rio de Janeiro"

        if affiliate == "All" and geolocation != None:
            pass
        elif affiliate == "Sao Paulo":
            geolocation = 'lat=-23.5505&long=-46.6333'
        elif affiliate == 'Brasilia':
            geolocation = 'lat=-15.7942&long=-47.8825'
        elif affiliate == 'Belo Horizonte':
            geolocation = 'lat=-19.9245&long=-43.9352'
        elif affiliate == "Recife":
            geolocation = 'lat=-8.0476&long=-34.8770'
        else:  # Rio de Janeiro
            geolocation = 'lat=-22.900&long=-43.172'

        post_data = "%s&player=%s&version=%s" % (geolocation, PLAYER_SLUG, PLAYER_VERSION)

        # 4452349
        hashUrl = 'http://security.video.globo.com/videos/%s/hash' % id
        hashJson = client.request(hashUrl, error=True, cookie=credentials, mobile=True, headers={
            "Accept-Encoding": "gzip",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Globo Play/0 (iPhone)"
        }, post=post_data)

        hash = get_signed_hashes(hashJson['hash'])[0]

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
            "player": PLAYER_SLUG,
            "url": hashJson["url"],
            "query_string_template": "h={{hash}}&k={{key}}&a={{openClosed}}&u={{user}}",
            "thumbUri": hashJson["thumbUri"],
            "hash": hash,
            "user": hashJson["user"],
            "credentials": credentials,
            "encrypted": False
        }

    def sign_resource(self, resource_id, video_id, player, version, anonymous=False):
        proxy = control.proxy_url
        proxy = None if proxy is None or proxy == '' else {
            'http': proxy,
            'https': proxy,
        }

        if not anonymous:
            # authenticate
            credentials = auth_helper.get_credentials()
        else:
            credentials = None

        hashUrl = 'https://security.video.globo.com/videos/%s/hash?resource_id=%s&version=%s&player=%s' % (video_id, resource_id, PLAYER_VERSION, PLAYER_SLUG)
        hashJson = client.request(hashUrl, cookie=credentials, mobile=False, headers={"Accept-Encoding": "gzip"}, proxy=proxy)

        if not hashJson or 'hash' not in hashJson:
            control.infoDialog(message=control.lang(34101).encode('utf-8'), sound=True, icon='ERROR')
            control.idle()
            sys.exit()
            return None

        hash = get_signed_hashes(hashJson['hash'])[0]

        return hash, hashJson['user'] if 'user' in hashJson else None, credentials

    def save_video_progress(self, credentials, program_id, video_id, milliseconds_watched, fully_watched=False):

        try:
            post_data = {
                'resource_id': video_id,
                'milliseconds_watched': int(round(milliseconds_watched)),
                'program_id': program_id,
                'fully_watched': fully_watched
            }

            control.log("--- SAVE WATCH HISTORY --- %s" % repr(post_data))

            post_data = urllib.urlencode(post_data)

            client.request(HISTORY_URL, error=True, cookie=credentials, mobile=True, headers={
                "Accept-Encoding": "gzip",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Globo Play/0 (iPhone)"
            }, post=post_data)

            # import xbmcgui
            # WINDOW = xbmcgui.Window(12006)
            # WINDOW.setProperty("InfoLabelName", "the new value")

        except Exception as ex:
            control.log("ERROR SAVING VIDEO PROGRESS (GLOBO PLAY): %s" % repr(ex))