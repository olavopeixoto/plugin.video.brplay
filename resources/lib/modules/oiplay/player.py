# -*- coding: utf-8 -*-

import requests
import sys
from urllib.parse import urlparse, urlencode
import threading
from .auth import gettoken
from .auth import get_default_profile
from .private_data import get_device_id
import resources.lib.modules.control as control
from resources.lib.modules import hlshelper
import xbmc


class Player(xbmc.Player):
    def __init__(self):
        super(xbmc.Player, self).__init__()
        self.stopPlayingEvent = None
        self.url = None
        self.isLive = False
        self.offset = 0.0
        self.stream_token = None
        self.content_id = None
        self.access_token = None
        self.profile = None
        self.account = None
        self.device_id = None
        self.provider = None
        self.play_time = 0

    def playlive(self, id, meta):

        meta = meta or {}

        control.log("Oi Play - play_stream: id=%s | meta=%s" % (id, meta))

        if id is None: return

        provider = meta.get('provider')
        self.isLive = meta.get('livefeed', False)

        self.content_id = id

        self.provider = provider

        data = self.individualize(self.isLive, id, provider)

        if not data or 'individualization' not in data:
            error_message = '%s: %s' % (data.get('reason'), data.get('detail')) if data and data.get('reason') else control.lang(34100)
            control.infoDialog(error_message, icon='ERROR')
            return

        encrypted = 'drm' in data and 'licenseUrl' in data['drm']

        if encrypted and not control.is_inputstream_available():
            control.okDialog(u'Oi Play', control.lang(34103))
            return

        url = data['individualization']['url']

        self.stream_token = data['token']['token']

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

        if ".mpd" in parsed_url.path:
            mime_type = 'application/dash+xml'
            item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            if self.isLive:
                item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')

        else:
            item.setProperty('inputstream.adaptive.manifest_type', 'hls')

        if encrypted:
            control.log("DRM: com.widevine.alpha")

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
            item.setProperty('inputstream', 'inputstream.adaptive')

        # if 'subtitles' in info and info['subtitles'] and len(info['subtitles']) > 0:
        #     control.log("FOUND SUBTITLES: %s" % repr([sub['url'] for sub in info['subtitles']]))
        #     item.setSubtitles([sub['url'] for sub in info['subtitles']])

        control.resolve(int(sys.argv[1]), True, item)

        self.stopPlayingEvent = threading.Event()
        self.stopPlayingEvent.clear()

        first_run = True
        last_time = 0.0
        while not self.stopPlayingEvent.isSet():
            if control.monitor.abortRequested():
                control.log("Abort requested")
                self.stream_control(4)
                break

            if self.isPlaying():
                self.play_time = int(self.getTime())
                if first_run:
                    self.showSubtitles(False)
                    first_run = False
                current_time = self.getTime()
                if current_time - last_time > 60:
                    last_time = current_time
                    self.stream_control(5)
            control.sleep(1000)

        if stopEvent:
            control.log("Setting stop event for proxy player")
            stopEvent.set()

        control.log("Done playing. Quitting...")

    # Event Types
    # 1 - Load
    # 2 - Start
    # 5 - Continue (Refresh)
    # 4 - Stop
    def stream_control(self, event_type):

        control.log("stream_control: %s" % event_type)

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer %s' % self.access_token,
            'X-Forwarded-For': '177.2.105.143',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
        }

        if self.isLive:
            url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/media/accounts/%s/profiles/%s/live/%s/stream-control?eventTypeId=%s&token=%s' % (self.account, self.profile, self.content_id, event_type, self.stream_token)
        else:
            url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/media/accounts/%s/profiles/%s/content/%s/stream-control?eventTypeId=%s&token=%s&bookmarkPosition=%s' % (
                self.account, self.profile, self.content_id, event_type, self.stream_token, 0 if event_type < 3 else self.play_time)

        control.log(url)

        response = requests.get(url, headers=headers)

        control.log("stream_control response (%s): %s" % (response.status_code, response.content))

    def onPlayBackStarted(self):
        # Will be called when xbmc starts playing a file
        control.log("Playback has started!")
        self.stream_control(2)
        # if self.offset > 0: self.seekTime(float(self.offset))

    def onPlayBackEnded(self):
        # Will be called when xbmc stops playing a file
        control.log("setting event in onPlayBackEnded ")
        self.stream_control(4)

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        control.log("setting event in onPlayBackStopped")
        self.stream_control(4)
        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def individualize(self, is_live, content_id, provider, format='mpd'):

        token, account = gettoken()
        device_id = get_device_id()
        profile = get_default_profile(account, device_id, token)

        self.access_token = token
        self.profile = profile
        self.account = account
        self.device_id = device_id

        useragent = 'ios' if format == 'm3u8' else 'web'

        cep_code = control.setting('oiplay_cepCode')

        if is_live:
            url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/media/accounts/%s/profiles/%s/live/%s/individualize?deviceId=%s&trailer=false&tablet=false&useragent=%s&cepCode=%s' % (account, profile, content_id, device_id, 'ios' if format == 'm3u8' else 'web', cep_code)
        else:
            url = 'https://apim.oi.net.br/app/oiplay/oapi/v1/media/accounts/{account}/profiles/{profile}/content/{content}/{provider}/individualize?deviceId={deviceId}&tablet=false&trailer=false&useragent={useragent}&cep_code={cepCode}'.format(account=account, profile=profile, content=content_id, provider=provider, deviceId=device_id, useragent=useragent, cepCode=cep_code)

        headers = {
            'Accept': 'application/json',
            'X-Forwarded-For': '177.2.105.143',
            'User-Agent': 'OiPlay-Store/5.9.0 (iPhone; iOS 15.6.1; Scale/3.00)' if format == 'm3u8' else 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
            'Authorization': 'Bearer %s' % token,
            'Accept-Encoding': 'gzip, deflate, br'
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
