# -*- coding: utf-8 -*-

import requests
import sys
from urlparse import urlparse
import threading
from auth import gettoken
from auth import get_default_profile
from private_data import get_device_id
import resources.lib.modules.control as control
from resources.lib.modules import hlshelper
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

        meta = meta or {}

        control.log("Oi Play - play_stream: id=%s | meta=%s" % (id, meta))

        if id is None: return

        provider = meta.get('provider')
        self.isLive = meta.get('livefeed', False)

        data = self.individualize(self.isLive, id, provider)

        if not data or 'individualization' not in data:
            error_message = '%s: %s' % (data.get('reason'), data.get('detail')) if data and data.get('reason') else control.lang(34100).encode('utf-8')
            control.infoDialog(error_message, icon='ERROR')
            return

        encrypted = 'drm' in data and 'licenseUrl' in data['drm']

        if encrypted and not control.is_inputstream_available():
            control.okDialog(u'Oi Play', control.lang(34103).encode('utf-8'))
            return

        url = data['individualization']['url']

        # info = data.get('token', {}).get('cmsChannelItem') or data.get('token', {}).get('cmsContentItem')

        control.log("live media url: %s" % url)

        self.offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0

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

        if control.supports_offscreen:
            item = control.item(path=self.url, offscreen=True)
        else:
            item = control.item(path=self.url)
        item.setArt(meta.get('art', {}))
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
            # licence_url = data['drm']['licenseUrl'] + '&token=' + data['drm']['jwtToken']
            if data.get('drm', {}).get('jwtToken'):
                licence_url = '%s&token=%s' % (data.get('drm', {}).get('licenseUrl'), data.get('drm', {}).get('jwtToken'))
            else:
                licence_url = data.get('drm', {}).get('licenseUrl')
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

    def individualize(self, is_live, content_id, provider, format='mpd'):

        token, account = gettoken()
        device_id = get_device_id()
        profile = get_default_profile(account, device_id, token)

        useragent = 'ios' if format == 'm3u8' else 'web'

        if is_live:
            url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/media/accounts/%s/profiles/%s/live/%s/individualize?deviceId=%s&tablet=false&useragent=%s' % (account, profile, content_id, device_id, 'ios' if format == 'm3u8' else 'web')
        else:
            url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/media/accounts/{account}/profiles/{profile}/content/{content}/{provider}/individualize?deviceId={deviceId}&tablet=false&useragent={useragent}'.format(account=account, profile=profile, content=content_id, provider=provider.encode('utf-8'), deviceId=device_id, useragent=useragent)

        headers = {
            'Accept': 'application/json',
            'X-Forwarded-For': '189.1.125.97',
            'User-Agent': 'OiPlay-Store/5.1.1 (iPhone; iOS 13.3.1; Scale/3.00)' if format == 'm3u8' else 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Authorization': 'Bearer ' + token
        }

        control.log('OIPLAY GET ' + url)
        control.log(headers)

        try:
            individualize = requests.get(url, headers=headers).json()

            control.log(individualize)

            control.log(individualize.get('individualization', {}).get('url'))

            return individualize
        except:

            control.log('RETRYING...')

            token, account_id = gettoken(force_new=True)

            headers['Authorization'] = 'Bearer ' + token

            control.log('OIPLAY GET ' + url)
            control.log(headers)

            individualize = requests.get(url, headers=headers).json()

            control.log(individualize)

            return individualize
