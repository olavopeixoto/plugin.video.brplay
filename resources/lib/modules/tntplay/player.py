# -*- coding: utf-8 -*-

import json
import sys
from urlparse import urlparse
import threading
import resources.lib.modules.control as control
from resources.lib.modules import hlshelper
import requests
import xbmc
from auth import get_token, get_device_id


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

        try:
            url = self.geturl(id)
        except Exception as ex:
            control.okDialog(control.lang(31200), str(ex))
            return

        encrypted = False  # 'drm' in data and 'licenseUrl' in data['drm']

        if encrypted:
            print('DRM Video!')

        if encrypted and not control.is_inputstream_available():
            control.okDialog(control.lang(31200), control.lang(34103).encode('utf-8'))
            return

        # url = data['individualization']['url']

        # url = url.replace('https://', 'http://')  # hack

        # info = data['token']['cmsChannelItem']

        # title = info['title']

        control.log("live media url: %s" % url)

        try:
            meta = json.loads(meta)
        except:
            meta = {
                "playcount": 0,
                "overlay": 6,
                # "title": title,
                # "thumb": info['positiveLogoUrl'],
                # "mediatype": "video",
                # "aired": None,
                # "genre": info["categoryName"],
                # "plot": title,
                # "plotoutline": title
            }

        poster = meta['poster'] if 'poster' in meta else None
        thumb = meta['thumb'] if 'thumb' in meta else None

        self.offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0

        self.isLive = True  # info['isLive']

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
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster})
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='Video', infoLabels=control.filter_info_labels(meta))

        item.setContentLookup(False)

        # if ".mpd" in parsed_url.path:
        #     mime_type = 'application/dash+xml'
        #     item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        #     if self.isLive:
        #         item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
        #
        # else:
        item.setProperty('inputstream.adaptive.manifest_type', 'hls')

        if encrypted:
            control.log("DRM: com.widevine.alpha")
            # licence_url = data['drm']['licenseUrl'] + '&token=' + data['drm']['jwtToken']
            # item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            # item.setProperty('inputstream.adaptive.license_key', licence_url + "||R{SSM}|")

        # if mime_type:
        #     item.setMimeType(mime_type)
        #     control.log("MIME TYPE: %s" % repr(mime_type))

        if not cookies and control.is_inputstream_available():
            item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            item.setProperty('inputstream', 'inputstream.adaptive')  # Kodi 19

        control.resolve(int(sys.argv[1]), True, item)

        control.log("Done playing. Quitting...")

    def geturl(self, channel, cookie=None):

        device_id = get_device_id()

        url = 'https://apac.ti-platform.com/AGL/1.0/R/ENG/PCTV/TNTGO_LATAM_BR/CONTENT/CDN/?id=%s&type=VOD&asJson=Y&accountDeviceId=%s' % (channel, device_id)

        retry = True if not cookie else False

        cookie = cookie or get_token()

        headers = {
            'Accept': 'application/json',
            'cookie': 'avs_cookie=' + cookie,
            'User-Agent': 'Tnt/2.2.13.1908061505 CFNetwork/1107.1 Darwin/19.0.0'
        }

        control.log('TNT GET ' + url)
        control.log(headers)

        result = json.loads(requests.get(url, headers=headers).content)

        control.log(result)

        if 'message' in result and result['message'] == 'Token not valid' and retry:
            cookie = get_token(True)
            return self.geturl(channel, cookie)

        if result.get('resultCode', u'KO') == u'KO':
            raise Exception('%s: %s' % (result.get('message', u'ERROR'), result.get('errorDescription', u'UNKNOWN')))

        return result['resultObj']['src']
