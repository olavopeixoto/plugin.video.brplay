# -*- coding: utf-8 -*-

import re
import sys
from urllib.parse import urlparse
import traceback
from resources.lib.modules.globo_util import get_signed_hashes
import requests
from resources.lib.modules import control
from resources.lib.modules import hlshelper
from resources.lib.hlsproxy.simpleproxy import MediaProxy
from resources.lib.modules.globoplay import resourceshelper
from resources.lib.modules.globosat import auth_helper

import xbmc
import threading


HISTORY_URL_API = 'https://api.vod.globosat.tv/globosatplay/watch_history.json?token=%s'
PLAYER_SLUG = 'android'
PLAYER_VERSION = '3.24.0'
GLOBOSAT_API_AUTHORIZATION = 'token b4b4fb9581bcc0352173c23d81a26518455cc521'


class Player(xbmc.Player):
    def __init__(self):
        super(xbmc.Player, self).__init__()
        self.stopPlayingEvent = None
        self.url = None
        self.isLive = False
        self.token = None
        self.video_id = None
        self.offset = 0.0

    def playlive(self, id, meta):

        meta = meta or {}

        control.log("Globosat Play - play_stream: id=%s | meta=%s" % (id, meta))

        if id is None: return

        self.isLive = meta.get('livefeed', False)

        # cdn = control.setting('globosat_cdn')
        # if cdn:
        #     cdn = cdn.lower() if cdn.lower() != 'auto' else None
        #
        # if meta.get('geofencing') and meta.get('lat') and meta.get('long'):
        #     control.log('Selecting Geo Fencing Video - lat: %s | long: %s' % (meta.get('lat'), meta.get('long')))
        #     info = resourceshelper.get_geofence_video_info(id, meta.get('lat'), meta.get('long'), auth_helper.get_credentials(), cdn)
        # elif not meta.get('router', True) or cdn:
        #     control.log('Selecting video using Playlist')
        #     info = resourceshelper.get_video_info(id, cdn=cdn)
        # else:
        #     control.log('Selecting video using Router')
        #     info = resourceshelper.get_video_router(id, self.isLive, cdn)
        #     if not info:
        #         info = resourceshelper.get_video_info(id, cdn=cdn)

        control.log('Selecting video using session api')
        info = resourceshelper.get_video_session(id, auth_helper.get_credentials().get('GLBID'), meta.get('lat'), meta.get('long'))

        control.log("INFO: %s" % repr(info))

        if not info or info is None or 'channel' not in info:
            return

        encrypted = 'encrypted' in info and info['encrypted']

        if encrypted and not control.is_inputstream_available():
            control.okDialog(control.lang(31200), control.lang(34103))
            return

        url = info['url']

        if info.get('query_string_template'):
            try:
                hash_token = info.get('hash_token')
                user = info.get('user')

                if not hash_token:
                    control.log('Signing resource: %s' % info.get('resource_id'))
                    hash_token, user, credentials = self.sign_resource(info['provider_id'], info['resource_id'], id, info['player'], info['version'], cdn)
            except Exception as ex:
                control.log(traceback.format_exc(), control.LOGERROR)
                control.log("PLAYER ERROR: %s" % repr(ex))
                return

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

        self.offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0

        parsed_url = urlparse(url)
        if parsed_url.path.endswith(".m3u8"):
            self.url, mime_type, stop_event, cookies = hlshelper.pick_bandwidth(url)
        elif parsed_url.path.endswith(".mpd") and not self.isLive:
            # proxy_handler = MediaProxy()
            # self.url = proxy_handler.resolve(url)
            # stop_event = proxy_handler.stop_event
            self.url = url
            stop_event = None
            mime_type = None
            cookies = None
        else:
            self.url = url
            mime_type, stop_event, cookies = 'video/mp4', None, None

        if self.url is None:
            if stop_event:
                control.log("Setting stop event for proxy player")
                stop_event.set()
            control.infoDialog(control.lang(34100), icon='ERROR')
            return

        control.log("Resolved URL: %s" % repr(self.url))
        control.log("Parsed URL: %s" % repr(parsed_url))

        if control.supports_offscreen:
            item = control.item(path=self.url, offscreen=True)
        else:
            item = control.item(path=self.url)
        item.setArt(meta.get('art', {}))
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='Video', infoLabels=control.filter_info_labels(meta))

        item.setContentLookup(False)

        if parsed_url.path.endswith(".mpd"):
            mime_type = 'application/dash+xml'
            item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            if self.isLive:
                item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')

        elif parsed_url.path.endswith(".ism/manifest"):
            mime_type = 'application/vnd.ms-sstr+xml'
            item.setProperty('inputstream.adaptive.manifest_type', 'ism')

        else:
            item.setProperty('inputstream.adaptive.manifest_type', 'hls')

        if encrypted:
            control.log("DRM: %s" % info['drm_scheme'])
            licence_url = info['protection_url']
            item.setProperty('inputstream.adaptive.license_type', info['drm_scheme'])
            if info['drm_scheme'] == 'com.widevine.alpha' or info['drm_scheme'] == 'com.microsoft.playready':
                item.setProperty('inputstream.adaptive.license_key', licence_url + "||R{SSM}|")

        if mime_type:
            item.setMimeType(mime_type)
            control.log("MIME TYPE: %s" % repr(mime_type))

        if not cookies and control.is_inputstream_available():
            item.setProperty('inputstream', 'inputstream.adaptive')
            # reqCookies = client.request(url=self.url,output='cookiejar',headRequest=True)
            # cookie_string = "; ".join([str(x) + "=" + str(y) for x, y in reqCookies.items()])
            # item.setProperty('inputstream.adaptive.stream_headers', 'cookie=%s' % cookie_string)
            # control.log("COOKIE STRING: %s" % cookie_string)

        if 'subtitles' in info and info['subtitles'] and len(info['subtitles']) > 0:
            control.log("FOUND SUBTITLES: %s" % repr([sub['url'] for sub in info['subtitles']]))
            item.setSubtitles([sub['url'] for sub in info['subtitles']])

        control.resolve(int(sys.argv[1]), True, item)

        self.stopPlayingEvent = threading.Event()
        self.stopPlayingEvent.clear()

        self.token = auth_helper.get_globosat_token()

        self.video_id = info['id'] if 'id' in info else None

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
                    current_time = self.getTime()
                    if current_time - last_time > 5 or (last_time == 0 and current_time > 1):
                        last_time = current_time
                        self.save_video_progress(self.token, self.video_id, current_time)
            control.sleep(1000)

        if stop_event:
            control.log("Setting stop event for proxy player")
            stop_event.set()

        control.log("Done playing. Quitting...")

    def onPlayBackStarted(self):
        # Will be called when xbmc starts playing a file
        control.log("Playback has started!")
        # if self.offset > 0: self.seekTime(float(self.offset))

    def onPlayBackEnded(self):
        # Will be called when xbmc stops playing a file
        control.log("setting event in onPlayBackEnded ")

        # if self.stopPlayingEvent:
        #     self.stopPlayingEvent.set()

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        control.log("setting event in onPlayBackStopped")

        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def sign_resource(self, provider_id, resource_id, video_id, player, version, cdn=None):
        proxy = control.proxy_url
        proxy = None if proxy is None or proxy == '' else {
            'http': proxy,
            'https': proxy,
        }

        credentials = auth_helper.get_globosat_cookie(provider_id)

        hash_url = 'https://security.video.globo.com/videos/%s/hash?resource_id=%s&version=%s&player=%s' % (video_id, resource_id, PLAYER_VERSION, PLAYER_SLUG)
        if cdn:
            hash_url = hash_url + '&cdn=' + cdn
        control.log('GET %s' % hash_url)
        response = requests.get(hash_url, cookies=credentials, headers={"Accept-Encoding": "gzip"}, proxies=proxy)
        response.raise_for_status()

        hash_json = response.json()

        control.log(hash_json)

        if not hash_json or hash_json is None or 'message' in hash_json and hash_json['message']:
            message = hash_json['message'] if hash_json and 'message' in hash_json else control.lang(34102)
            message = str(hash_json['http_status_code']) + u'|' + message if hash_json and 'http_status_code' in hash_json else message
            control.infoDialog(message=message, sound=True, icon='ERROR')
            raise Exception(message)

        hash_token = get_signed_hashes(hash_json['hash']) if 'hash' in hash_json else hash_json['token']
        user = hash_json["user"] if 'user' in hash_json else None
        return hash_token, user, credentials

    def save_video_progress(self, token, video_id, watched_seconds):

        try:
            if self.isLive:
                return

            post_data = {
                'watched_seconds': int(round(watched_seconds)),
                'id': video_id
            }

            url = HISTORY_URL_API % token
            headers = {
                "Accept-Encoding": "gzip",
                "Content-Type": "application/x-www-form-urlencoded",
                "version": "2",
                "Authorization": GLOBOSAT_API_AUTHORIZATION
            }

            response = requests.post(url, headers=headers, data=post_data)

            response.raise_for_status()

        except Exception as ex:
            control.log(traceback.format_exc(), control.LOGERROR)
            control.log("ERROR SAVING VIDEO PROGRESS (GLOBOSAT PLAY): %s" % repr(ex))
