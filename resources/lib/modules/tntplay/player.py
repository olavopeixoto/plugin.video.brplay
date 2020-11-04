# -*- coding: utf-8 -*-

import json
import sys
from urlparse import urlparse
import urllib
import resources.lib.modules.control as control
from resources.lib.modules import hlshelper
import requests
import xbmc
from auth import get_token, get_device_id, logout
import traceback

LANGUAGE = control.lang(34125).encode('utf-8')

proxy = None #control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}

vod_platform = 'PCTV_DASH' if control.prefer_dash else 'PCTV'


class Player(xbmc.Player):
    def __init__(self):
        super(xbmc.Player, self).__init__()
        self.stopPlayingEvent = None
        self.url = None
        self.isLive = False
        self.token = None
        self.video_id = None
        self.offset = 0.0

    def playlive(self, id, meta, encrypted=False):

        meta = meta or {}

        control.log("TNT Play - play_stream: id=%s | meta=%s" % (id, meta))

        if id is None: return

        try:
            url = self.geturl(id, encrypted=encrypted)
        except Exception as ex:
            control.log(traceback.format_exc(), control.LOGERROR)
            control.okDialog(u'TNT Play', str(ex))
            return

        if encrypted and not control.is_inputstream_available():
            control.okDialog(u'TNT Play', control.lang(34103).encode('utf-8'))
            return

        control.log("live media url: %s" % url)

        self.offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0

        self.isLive = not encrypted

        parsed_url = urlparse(url)

        if ".m3u8" in parsed_url.path:
            self.url, mime_type, stopEvent, cookies = hlshelper.pick_bandwidth(url)
        else:
            self.url = url
            mime_type, stopEvent, cookies = None, None, None

        if self.url is None:
            if stopEvent:
                control.log("Setting stop event for proxy player")
                stopEvent.set()
            control.infoDialog(control.lang(34100).encode('utf-8'), icon='ERROR')
            return

        control.log("Resolved URL: %s" % repr(self.url))
        control.log("Parsed URL: %s" % repr(parsed_url))

        item = control.item(path=self.url)
        item.setArt(meta.get('art', {}))
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='Video', infoLabels=control.filter_info_labels(meta))

        item.setContentLookup(False)

        manifest_type = 'hls' if parsed_url.path.endswith(".m3u8") else 'mpd'

        if encrypted:
            control.log("DRM: com.widevine.alpha")
            licence_url = 'https://widevine.license.istreamplanet.com/widevine/api/license/7837c2c6-8fe4-4db0-9900-1bd66c21ffa3'
            item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            item.setProperty('inputstream.adaptive.manifest_type', manifest_type)

            cookie = get_token()
            retry = 1
            token = ''
            while retry >= 0:
                retry = retry - 1

                headers = {
                    'Accept': 'application/json',
                    'cookie': 'avs_cookie=' + cookie,
                    'User-Agent': 'Tnt/2.2.13.1908061505 CFNetwork/1107.1 Darwin/19.0.0'
                }
                drm_url = 'https://api.tntgo.tv/AGL/1.0/A/{lang}/{platform}/TNTGO_LATAM_BR/CONTENT/GETDRMTOKEN/{id}'.format(lang=LANGUAGE, platform=vod_platform, id=id)

                control.log('TNT DRM GET %s' % drm_url)
                control.log(headers)

                drm_response = requests.get(drm_url, headers=headers, proxies=proxy).json() or {}

                control.log(drm_response)

                if drm_response.get('resultCode', 'KO') == u'OK':
                    token = drm_response.get('resultObj')
                    break

                if drm_response.get('message', '') == 'Token not valid':
                    cookie = get_token(True)
                else:
                    logout()
                    control.infoDialog(drm_response.get('message', u'DRM ERROR'), icon='ERROR')
                    return

            headers = {
                'user-agent': 'Tnt/2.2.13.1908061505 CFNetwork/1107.1 Darwin/19.0.0',
                'x-isp-token': token,
                'Origin': 'https://www.tntgo.tv',
                'content-type': 'application/octet-stream'
            }

            license_key = '%s|%s|R{SSM}|' % (licence_url, urllib.urlencode(headers))
            item.setProperty('inputstream.adaptive.license_key', license_key)
            stream_headers = {
                'user-agent': 'Tnt/2.2.13.1908061505 CFNetwork/1107.1 Darwin/19.0.0',
                'Origin': 'https://www.tntgo.tv'
            }
            item.setProperty('inputstream.adaptive.stream_headers', urllib.urlencode(stream_headers))
        else:
            item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            # mime_type = 'application/vnd.apple.mpegurl'
            # item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')

        if mime_type:
            item.setMimeType(mime_type)
            control.log("MIME TYPE: %s" % repr(mime_type))

        if not cookies and control.is_inputstream_available():
            item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            item.setProperty('inputstream', 'inputstream.adaptive')  # Kodi 19

        control.resolve(int(sys.argv[1]), True, item)

        control.log("Done playing. Quitting...")

    def geturl(self, content_id, cookie=None, encrypted=False):

        device_id = get_device_id()

        platform = 'PCTV' if not encrypted else vod_platform  # 'PCTV_DASH'

        url = 'https://apac.ti-platform.com/AGL/1.0/R/%s/%s/TNTGO_LATAM_BR/CONTENT/CDN/?id=%s&type=VOD&asJson=Y&accountDeviceId=%s' % (LANGUAGE, platform, content_id, device_id)

        retry = True if not cookie else False

        cookie = cookie or get_token()

        headers = {
            'Accept': 'application/json',
            'cookie': 'avs_cookie=' + cookie,
            'User-Agent': 'Tnt/2.2.13.1908061505 CFNetwork/1107.1 Darwin/19.0.0'
        }

        control.log('TNT GET ' + url)
        control.log(headers)

        result = requests.get(url, headers=headers, proxies=proxy).json() or {}

        control.log(result)

        if 'message' in result and result['message'] == u'Token not valid' and retry:
            cookie = get_token(True)
            return self.geturl(content_id, cookie, encrypted)

        if result.get('resultCode', u'KO') == u'KO':
            logout()
            raise Exception('%s: %s' % (result.get('message', u'STREAM URL ERROR'), result.get('errorDescription', u'UNKNOWN')))

        return result.get('resultObj', {}).get('src')
