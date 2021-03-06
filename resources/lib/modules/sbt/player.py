# -*- coding: utf-8 -*-

import sys
from resources.lib.modules import control, ytlive
from . import get_authorization
import re
import requests
from urllib.parse import urlparse
from resources.lib.hlsproxy.simpleproxy import MediaProxy

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

    def playlive(self, meta):

        meta = meta or {}

        control.log("SBT - play_stream | meta=%s" % meta)

        self.isLive = True

        url = self.get_url()

        control.log("live media url: %s" % url)

        if not url:
            control.infoDialog(control.lang(34100), icon='ERROR')
            return

        if control.proxy_url:
            http_proxy = MediaProxy(control.proxy_url)
            self.url = http_proxy.resolve(url)
            stop_event = http_proxy.stop_event
        else:
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

        item.setContentLookup(False)

        if parsed_url.path.endswith(".mpd"):
            mime_type = 'application/dash+xml'
            item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            if self.isLive:
                item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')

        else:
            mime_type = 'application/vnd.apple.mpegurl'
            item.setProperty('inputstream.adaptive.manifest_type', 'hls')

        if mime_type:
            item.setMimeType(mime_type)
            control.log("MIME TYPE: %s" % repr(mime_type))

        if control.is_inputstream_available():
            item.setProperty('inputstream', 'inputstream.adaptive')

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

    def get_url(self):

        headers = {
            'Authorization': get_authorization(),
            'Origin': 'https://www.sbt.com.br',
            'Accept-Encoding': 'gzip, deflate, br'
        }

        url = 'http://content.sbt.com.br/api/medias?limit=1&idsite=207&idsitearea=1562&idplaylist=6307'

        response = requests.get(url, headers=headers, proxies=proxy, verify=False).json()

        description = response['results'][0]['description']

        r = re.search(r'src="(.+?)"', description)

        url_cache = r.group(1)

        stream_url = ytlive.geturl(url_cache)

        return stream_url
