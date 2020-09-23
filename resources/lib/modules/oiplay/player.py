# -*- coding: utf-8 -*-

import json
import sys
from urlparse import urlparse
import threading
from auth import gettoken
from auth import get_default_profile
from private_data import get_user
from private_data import get_password
from private_data import get_device_id
import resources.lib.modules.control as control
from resources.lib.modules import hlshelper
from resources.lib.modules import client
import xbmc


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

        control.log("Oi Play - play_stream: id=%s | meta=%s" % (id, meta))

        if id is None: return

        data = self.individualize(id)

        encrypted = 'drm' in data and 'licenseUrl' in data['drm']

        if encrypted:
            print('DRM Video!')

        if encrypted and not control.is_inputstream_available():
            control.okDialog(control.lang(31200), control.lang(34103).encode('utf-8'))
            return

        url = data['individualization']['url']

        url = url.replace('https://', 'http://')  # hack

        info = data['token']['cmsChannelItem']

        title = info['title']

        control.log("live media url: %s" % url)

        try:
            meta = json.loads(meta)
        except:
            meta = {
                "playcount": 0,
                "overlay": 6,
                "title": title,
                "thumb": info['positiveLogoUrl'],
                "mediatype": "video",
                "aired": None,
                "genre": info["categoryName"],
                "plot": title,
                "plotoutline": title
            }

        # meta.update({
        #     "genre": info["categoryName"],
        #     "plot": title,
        #     "plotoutline": title
        # })

        # poster = meta['poster'] if 'poster' in meta else control.addonPoster()
        thumb = meta['thumb'] if 'thumb' in meta else info['positiveLogoUrl']

        self.offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0

        self.isLive = info['isLive']

        parsed_url = urlparse(url)
        if ".m3u8" in parsed_url.path:
            self.url, mime_type, stopEvent, cookies = hlshelper.pick_bandwidth(url)
        else:
            self.url = url
            mime_type, stopEvent, cookies = 'video/mp4', None, None

        if self.url is None:
            if stopEvent:
                control.log("Setting stop event for proxy player")
                stopEvent.set()
            control.infoDialog(control.lang(34100).encode('utf-8'), icon='ERROR')
            return

        control.log("Resolved URL: %s" % repr(self.url))
        control.log("Parsed URL: %s" % repr(parsed_url))

        item = control.item(path=self.url)
        item.setArt({'icon': thumb, 'thumb': thumb})
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='Video', infoLabels=control.filter_info_labels(meta))

        item.setContentLookup(False)

        if ".mpd" in parsed_url.path:
            mime_type = 'application/dash+xml'
            item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            if self.isLive:
                item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')

        else:
            item.setProperty('inputstream.adaptive.manifest_type', 'hls')

        if encrypted:
            control.log("DRM: com.widevine.alpha")
            licence_url = data['drm']['licenseUrl'] + '&token=' + data['drm']['jwtToken']
            item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            item.setProperty('inputstream.adaptive.license_key', licence_url + "||R{SSM}|")

        if mime_type:
            item.setMimeType(mime_type)
            control.log("MIME TYPE: %s" % repr(mime_type))

        if not cookies and control.is_inputstream_available():
            item.setProperty('inputstreamaddon', 'inputstream.adaptive')

        # if 'subtitles' in info and info['subtitles'] and len(info['subtitles']) > 0:
        #     control.log("FOUND SUBTITLES: %s" % repr([sub['url'] for sub in info['subtitles']]))
        #     item.setSubtitles([sub['url'] for sub in info['subtitles']])

        control.resolve(int(sys.argv[1]), True, item)

        self.stopPlayingEvent = threading.Event()
        self.stopPlayingEvent.clear()

        first_run = True
        # last_time = 0.0
        while not self.stopPlayingEvent.isSet():
            if control.monitor.abortRequested():
                control.log("Abort requested")
                break

            if self.isPlaying():
                if first_run:
                    self.showSubtitles(False)
                    first_run = False
                # if not self.isLive:
                #     current_time = self.getTime()
                #     if current_time - last_time > 5 or (last_time == 0 and current_time > 1):
                #         last_time = current_time
                #         self.save_video_progress(self.token, self.video_id, current_time)
            control.sleep(1000)

        if stopEvent:
            control.log("Setting stop event for proxy player")
            stopEvent.set()

        control.log("Done playing. Quitting...")

    def onPlayBackStarted(self):
        # Will be called when xbmc starts playing a file
        control.log("Playback has started!")
        # if self.offset > 0: self.seekTime(float(self.offset))

    def onPlayBackEnded(self):
        # Will be called when xbmc stops playing a file
        control.log("setting event in onPlayBackEnded ")

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        control.log("setting event in onPlayBackStopped")

        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def individualize(self, channel, format='mpd'):

        account = get_user()
        password = get_password()
        token = gettoken(account, password)

        device_id = get_device_id()
        profile = get_default_profile(account, device_id, token)

        url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/media/accounts/%s/profiles/%s/live/%s/individualize?deviceId=%s&tablet=false&useragent=%s' % (
        account, profile, channel, device_id, 'ios' if format == 'm3u8' else 'web')

        headers = {
            'Accept': 'application/json',
            'X-Forwarded-For': '189.1.125.97',
            'User-Agent': 'OiPlay-Store/5.1.1 (iPhone; iOS 13.3.1; Scale/3.00)' if format == 'm3u8' else 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Authorization': 'Bearer ' + token
        }

        print('OIPLAY GET ' + url)
        print(headers)

        try:
            individualize = client.request(url, headers=headers)

            print(individualize)

            print(individualize['individualization']['url'])

            return individualize
        except:

            print 'RETRYING...'

            headers['Authorization'] = 'Bearer ' + gettoken(account, password, force_new=True)

            print('OIPLAY GET ' + url)
            print(headers)

            individualize = client.request(url, headers=headers)

            print(individualize)

            return individualize
