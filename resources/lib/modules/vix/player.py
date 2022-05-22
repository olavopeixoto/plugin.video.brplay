# -*- coding: utf-8 -*-

import sys
import uuid
import base64
import json
import datetime
from resources.lib.modules import control
import requests
from urllib.parse import urlparse

import xbmc
import threading

proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


class Player(xbmc.Player):
    def __init__(self):
        super(xbmc.Player, self).__init__()
        self.stopPlayingEvent = None
        self.url = None
        self.isLive = False
        self.token = None
        self.video_id = None
        self.offset = 0.0

    def playlive(self, media_key, season, episode, meta):

        meta = meta or {}

        control.log("VIX - play_stream | meta=%s" % meta)

        self.isLive = True

        url = self.get_url(media_key, season, episode)

        control.log("live media url: %s" % url)

        if not url:
            control.infoDialog(control.lang(34100), icon='ERROR')
            return

        self.url = url
        stop_event = None

        if self.url is None:
            if stop_event:
                control.log("Setting stop event for proxy player")
                stop_event.set()
            control.infoDialog(control.lang(34100), icon='ERROR')
            return

        parsed_url = urlparse(url)

        control.log("Resolved URL: %s" % repr(self.url))
        control.log("Parsed URL: %s" % repr(parsed_url))

        if control.supports_offscreen:
            item = control.item(path=self.url, offscreen=True)
        else:
            item = control.item(path=self.url)
        item.setArt(meta.get('art', {}))
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='Video', infoLabels=control.filter_info_labels(meta))

        # item.setContentLookup(False)

        # if parsed_url.path.endswith(".mpd"):
        #     mime_type = 'application/dash+xml'
        #     item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        #     if self.isLive:
        #         item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
        #
        # else:
        #     mime_type = 'application/vnd.apple.mpegurl'
        #     item.setProperty('inputstream.adaptive.manifest_type', 'hls')
        #
        # if mime_type:
        #     item.setMimeType(mime_type)
        #     control.log("MIME TYPE: %s" % repr(mime_type))
        #
        # if control.is_inputstream_available():
        #     item.setProperty('inputstream', 'inputstream.adaptive')

        control.resolve(int(sys.argv[1]), True, item)

        self.stopPlayingEvent = threading.Event()
        self.stopPlayingEvent.clear()

        while not self.stopPlayingEvent.isSet():
            control.monitor.waitForAbort(1)
            if control.monitor.abortRequested():
                control.log("Abort requested")
                break

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

        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        control.log("setting event in onPlayBackStopped")

        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def get_url(self, media_id, season, episode):

        uid, jwt = self.login()

        headers = {
            'Authorization': 'Bearer %s' % jwt,
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br'
        }

        url = 'https://api-edge.prod.gcp.vix.services/api/catalog/watch/%s/%s/%s' % (media_id, season, episode)

        control.log('GET STREAM URL: %s' % url)

        response = requests.get(url, headers=headers, proxies=proxy, verify=False).json()

        stream_url = (response.get('data', {}) or {}).get('playKey')

        return stream_url

    def login(self):
        uid = control.setting('vix_id')
        jwt = control.setting('vix_jwt')

        if uid and jwt:
            token = jwt.split('.')[1]
            padded = token + "=" * divmod(len(token), 4)[1]
            jwt_decoded = json.loads(base64.urlsafe_b64decode(padded))
            timestamp = jwt_decoded.get('exp')
            exp = datetime.datetime.fromtimestamp(timestamp)
            if exp > datetime.datetime.utcnow():
                control.log('VIX - JWT from cache')
                return uid, jwt

            control.log('VIX - JWT expired (%s)' % timestamp)

        guest_id = str(uuid.uuid4())
        url = 'https://api-edge.prod.gcp.vix.services/api/members/login-guest'
        data = {
            "guestId": guest_id
        }

        control.log('VIX Login - %s' % guest_id)

        response = requests.post(url, data=data)

        response.raise_for_status()

        response_json = response.json()

        control.log(response_json)

        uid = (response_json.get('data', {}) or {}).get('id')
        jwt = (response_json.get('meta', {}) or {}).get('jwt')

        control.log('id: %s' % uid)
        control.log('jwt: %s' % jwt)

        control.setSetting('vix_id', uid)
        control.setSetting('vix_jwt', jwt)

        return uid, jwt
