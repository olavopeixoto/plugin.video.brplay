# -*- coding: utf-8 -*-

import re
import sys
import xbmc
from . import auth_helper
import requests
from urllib.parse import urlparse
from resources.lib.modules import hlshelper
from resources.lib.hlsproxy.simpleproxy import MediaProxy
from resources.lib.modules import control
from resources.lib.modules.globo_util import get_signed_hashes
from resources.lib.modules.globoplay import resourceshelper
import threading
import traceback

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
        self.stop_playing_event = None
        self.credentials = None
        self.program_id = None
        self.video_id = None

    def onPlayBackStopped(self):
        control.log("PLAYBACK STOPPED")

        if self.stop_playing_event:
            self.stop_playing_event.set()

    def onPlayBackEnded(self):
        control.log("PLAYBACK ENDED")

        if self.stop_playing_event:
            self.stop_playing_event.set()

    def onPlayBackStarted(self):
        control.log("PLAYBACK STARTED")
        # if self.offset > 0: self.seekTime(float(self.offset))

    def play_stream(self, id, meta, children_id=None):

        meta = meta or {}

        control.log("GloboPlay - play_stream: id=%s | children_id=%s | meta=%s" % (id, children_id, meta))

        if id is None:
            return

        self.isLive = meta.get('livefeed', False)
        stop_event = None

        cdn = control.setting('globo_cdn')
        if cdn:
            cdn = cdn.lower() if cdn.lower() != 'auto' else None

        if self.isLive and meta.get('lat') and meta.get('long'):
            control.log("PLAY LIVE!")

            latitude = meta.get('lat')
            longitude = meta.get('long')

            if not latitude or not longitude:
                code, latitude, longitude = control.get_coordinates(control.get_affiliates_by_id(-1))

            info = self.__getLiveVideoInfo(id, latitude, longitude, cdn)

            if info is None:
                return

            item, self.url, stop_event = self.__get_list_item(meta, info)

        else:
            if not meta.get('router', True) or cdn:
                info = resourceshelper.get_video_info(id, children_id, cdn)
            else:
                info = resourceshelper.get_video_router(id, self.isLive, cdn)
                if not info:
                    info = resourceshelper.get_video_info(id, children_id, cdn)

            if info is None:
                return

            if 'resource_id' not in info:
                control.log("PLAY CHILDREN!")
                items = []
                xbmc.PlayList(1).clear()
                first = True
                for i in info:
                    hash_token, user, self.credentials = self.sign_resource(i['resource_id'], i['id'], i['player'], i['version'], cdn=i['cdn'])
                    i['hash'] = hash_token
                    i['user'] = user
                    item, url, stop_event = self.__get_list_item(meta, i, False)
                    if first:
                        self.url = url
                        first = False
                    items.append(item)
                    control.log("PLAYLIST ITEM URL: %s" % url)
                    xbmc.PlayList(1).add(url, item)
                item = items[0]
            else:
                control.log("PLAY SINGLE RESOURCE!")
                hash_token, user, self.credentials = self.sign_resource(info['resource_id'], info["id"], info['player'], info['version'], meta['anonymous'] if 'anonymous' in meta else False, cdn=info['cdn'])
                info['hash'] = hash_token
                info['user'] = user
                item, self.url, stop_event = self.__get_list_item(meta, info)

        self.offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0

        self.stop_playing_event = threading.Event()
        self.stop_playing_event.clear()

        self.program_id = info['program_id'] if 'program_id' in info else meta.get('program_id')
        self.video_id = id

        syshandle = int(sys.argv[1])
        control.resolve(syshandle, True, item)

        first_run = True
        last_time = 0.0
        while not self.stop_playing_event.isSet():
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

        if stop_event:
            control.log("Setting stop event for proxy player")
            stop_event.set()

        control.log("Done playing. Quitting...")

    def __get_list_item(self, meta, info, pick_bandwidth=True):
        hash_token = info['hash']
        user = info['user']

        query_string = re.sub(r'{{(\w*)}}', r'%(\1)s', info['query_string_template'])

        query_string = query_string % {
            'hash': hash_token,
            'key': 'app',
            'openClosed': 'F' if info['subscriber_only'] and user else 'A',
            'user': user if info['subscriber_only'] and user else '',
            'token': hash_token
        }

        url = '?'.join([info['url'], query_string])

        control.log("live media url: %s" % url)

        parsed_url = urlparse(url)
        if parsed_url.path.endswith(".m3u8"):
            if pick_bandwidth:
                url, mime_type, stop_event, cookies = hlshelper.pick_bandwidth(url)
            else:
                mime_type, stop_event, cookies = None, None, None

        elif parsed_url.path.endswith(".mpd"):
            proxy_handler = MediaProxy()
            url = proxy_handler.resolve(url)
            stop_event = proxy_handler.stop_event
            mime_type = None
            cookies = None

        else:
            mime_type, stop_event, cookies = 'video/mp4', None, None

        if url is None:
            if stop_event:
                control.log("Setting stop event for proxy player")
                stop_event.set()
            control.infoDialog(message=control.lang(34100), icon='ERROR')
            return None, None, None

        control.log("Resolved URL: %s" % repr(url))

        if control.supports_offscreen:
            item = control.item(path=url, offscreen=True)
        else:
            item = control.item(path=url)

        item.setInfo(type='video', infoLabels=control.filter_info_labels(meta))
        item.setArt(meta.get('art', {}))
        item.setProperty('IsPlayable', 'true')

        item.setContentLookup(False)

        user_agent = 'User-Agent=Globo Play/0 (iPhone)'

        if parsed_url.path.endswith(".mpd"):
            mime_type = 'application/dash+xml'
            if control.enable_inputstream_adaptive:
                control.log("Using inputstream.adaptive MPD")
                item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                item.setProperty('inputstream.adaptive.stream_headers', user_agent)
                item.setProperty('inputstream', 'inputstream.adaptive')

        if mime_type:
            item.setMimeType(mime_type)
        elif not cookies:
            item.setMimeType('application/vnd.apple.mpegurl')
            if control.enable_inputstream_adaptive:
                control.log("Using inputstream.adaptive HLS")
                item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                item.setProperty('inputstream.adaptive.stream_headers', user_agent)
                item.setProperty('inputstream', 'inputstream.adaptive')

        encrypted = info.get('encrypted', False)

        if encrypted and not control.is_inputstream_available():
            control.okDialog(control.lang(31200), control.lang(34103))
            return

        if encrypted:
            control.log("DRM: %s" % info['drm_scheme'])
            licence_url = info['protection_url']
            item.setProperty('inputstream.adaptive.license_type', info['drm_scheme'])
            if info['drm_scheme'] == 'com.widevine.alpha' or info['drm_scheme'] == 'com.microsoft.playready':
                item.setProperty('inputstream.adaptive.license_key', licence_url + "||R{SSM}|")

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

        return item, url, stop_event

    def __getLiveVideoInfo(self, id, latitude, longitude, cdn=None):

        proxy = control.proxy_url
        proxy = None if proxy is None or proxy == '' else {
            'http': proxy,
            'https': proxy,
        }

        credentials = auth_helper.get_credentials()

        if credentials is None:
            return None

        post_data = {
            'player': PLAYER_SLUG,
            'version': PLAYER_VERSION,
            'lat': latitude,
            'long': longitude
        }

        if cdn:
            post_data['cdn'] = cdn

        # 4452349
        hash_url = 'http://security.video.globo.com/videos/%s/hash' % id
        control.log('POST %s' % hash_url)
        control.log(post_data)
        response = requests.post(hash_url, cookies=credentials, headers={
                                                                "Accept-Encoding": "gzip",
                                                                "Content-Type": "application/x-www-form-urlencoded",
                                                                "User-Agent": "Globo Play/0 (iPhone)"
                                                            }, data=post_data, proxies=proxy)

        response.raise_for_status()

        hash_json = response.json()

        control.log(hash_json)

        hash_token = get_signed_hashes(hash_json['hash']) if 'hash' in hash_json else hash_json['token']
        querystring_template = hash_json.get('query_string_template') or "h={{hash}}&k={{key}}&a={{openClosed}}&u={{user}}"

        return {
            "id": "-1",
            "title": hash_json["name"],
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
            "url": hash_json["url"],
            "query_string_template": querystring_template,
            "thumbUri": hash_json["thumbUri"],
            "hash": hash_token,
            "user": hash_json["user"],
            "credentials": credentials,
            "encrypted": False
        }

    def sign_resource(self, resource_id, video_id, player, version, anonymous=False, cdn=None):
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

        hash_url = 'https://security.video.globo.com/videos/%s/hash?resource_id=%s&version=%s&player=%s' % (video_id, resource_id, PLAYER_VERSION, PLAYER_SLUG)
        if cdn:
            hash_url = hash_url + '&cdn=' + cdn

        control.log('GET %s' % hash_url)
        response = requests.get(hash_url, cookies=credentials, headers={"Accept-Encoding": "gzip"}, proxies=proxy)

        response.raise_for_status()

        hash_json = response.json()

        if not hash_json or ('hash' not in hash_json and 'token' not in hash_json):
            message = (hash_json or {}).get('message') or control.lang(34101)
            control.log(hash_json or message, control.LOGERROR)
            control.infoDialog(message=message, sound=True, icon='ERROR')
            control.idle()
            sys.exit()

        hash_token = get_signed_hashes(hash_json['hash']) if 'hash' in hash_json else hash_json['token']

        return hash_token, hash_json.get('user'), credentials

    def save_video_progress(self, credentials, program_id, video_id, milliseconds_watched, fully_watched=False):

        try:
            post_data = {
                'resource_id': video_id,
                'milliseconds_watched': int(round(milliseconds_watched)),
                'program_id': program_id,
                'fully_watched': fully_watched
            }

            control.log("--- SAVE WATCH HISTORY --- %s" % repr(post_data))
            control.log('POST %s' % HISTORY_URL)
            response = requests.post(HISTORY_URL, cookies=credentials, headers={
                                                                "Accept-Encoding": "gzip",
                                                                "Content-Type": "application/x-www-form-urlencoded",
                                                                "User-Agent": "Globo Play/0 (iPhone)"
                                                            }, data=post_data)

            response.raise_for_status()

            # import xbmcgui
            # WINDOW = xbmcgui.Window(12006)
            # WINDOW.setProperty("InfoLabelName", "the new value")

        except Exception as ex:
            control.log(traceback.format_exc(), control.LOGERROR)
            control.log("ERROR SAVING VIDEO PROGRESS (GLOBO PLAY): %s" % repr(ex))
