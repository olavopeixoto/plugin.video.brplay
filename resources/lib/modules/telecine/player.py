# -*- coding: utf-8 -*-

import json
import sys
import requests
import urllib
from resources.lib.modules import control
from resources.lib.modules.telecine import get_headers
from auth import get_device_id
import traceback

import xbmc

proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


class Player(xbmc.Player):
    def __init__(self):
        super(xbmc.Player, self).__init__()

    def playlive(self, path, meta):

        control.log("Telecine Play - play_stream: path=%s | meta=%s" % (path, meta))

        if path is None:
            return

        if not control.is_inputstream_available():
            control.okDialog('Telecine Play', control.lang(34103).encode('utf-8'))
            return

        try:
            url, license_url = self.get_stream(path)
        except:
            control.log(traceback.format_exc(), control.LOGERROR)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            control.okDialog('Telecine Play', str(exc_value))
            return

        if '.mpd' not in url:
            response = requests.get(url, proxies=proxy)
            url = response.url

        control.log("media url: %s" % url)
        control.log("license url: %s" % license_url)

        try:
            meta = json.loads(meta)
        except:
            meta = {
                "playcount": 0,
                "overlay": 6,
                "mediatype": "video",
            }

        if control.supports_offscreen:
            item = control.item(path=url, offscreen=True)
        else:
            item = control.item(path=url)

        art = meta.get('art', {}) or {}
        item.setArt(art)

        properties = meta.get('properties', {}) or {}
        item.setProperties(properties)

        item.setProperty('IsPlayable', 'true')

        item.setInfo(type='Video', infoLabels=control.filter_info_labels(meta))

        item.setContentLookup(False)

        item.setMimeType('application/dash+xml')
        item.setProperty('inputstream.adaptive.manifest_type', 'mpd')

        if license_url:
            headers = {
                'user-agent': 'Telecine_iOS/2.5.10 (br.com.telecineplay; build:37; iOS 14.1.0) Alamofire/5.2.2',
                'x-device': 'Mobile-iOS',
                'x-version': '2.5.10',
                'content-type': 'application/octet-stream'
            }

            item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            item.setProperty('inputstream.adaptive.license_key', "%s|%s|R{SSM}|" % (license_url, urllib.urlencode(headers)))

        item.setProperty('inputstreamaddon', 'inputstream.adaptive')

        # if 'subtitles' in info and info['subtitles'] and len(info['subtitles']) > 0:
        #     control.log("FOUND SUBTITLES: %s" % repr([sub['url'] for sub in info['subtitles']]))
        #     item.setSubtitles([sub['url'] for sub in info['subtitles']])

        syshandle = int(sys.argv[1])

        control.resolve(syshandle, True, item)

        control.log("Done playing. Quitting...")

    def get_stream(self, path, retry=3):

        device_id = get_device_id()

        url = 'https://bff.telecinecloud.com/api/v1/videos?deviceId={device_id}&path={path}'.format(device_id=device_id, path=path)

        control.log('[Telecine player] - GET %s' % url)
        result = requests.get(url, headers=get_headers())

        if result.status_code == 504 and retry > 0:  # handles server timeout
            return self.get_stream(path, retry - 1)

        result.raise_for_status()

        result = result.json()

        control.log('[Telecine player] - %s' % result)

        return result.get('videoSourceMpegDash'), result.get('widevineLicenseUrl')
