# -*- coding: utf-8 -*-

import json
import sys
import urllib
from auth import login
from auth import PLATFORM
import resources.lib.modules.control as control
import requests
import base64
import traceback


proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


class Player:
    def __init__(self):
        self.stopPlayingEvent = None
        self.url = None
        self.isLive = False

    def playlive(self, id, meta):

        meta = meta or {}

        control.log("Now Online - play_stream: id=%s | meta=%s" % (id, meta))

        if id is None: return

        self.isLive = meta.get('livefeed', False)

        try:
            url, avs_cookie, login_info, xsrf, device_id, sc_id = self.get_cdn(id, self.isLive)
        except Exception as ex:
            control.log(traceback.format_exc(), control.LOGERROR)
            control.okDialog(u'Now Online', ex.message)
            return

        encrypted = True

        if encrypted and not control.is_inputstream_available():
            control.okDialog(u'Now Online', control.lang(34103).encode('utf-8'))
            return

        control.log("live media url: %s" % url)

        thumb = meta['thumb'] if 'thumb' in meta else None

        self.url = url

        item = control.item(path=self.url)
        item.setArt({'icon': thumb, 'thumb': thumb})
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='Video', infoLabels=control.filter_info_labels(meta))

        item.setContentLookup(False)

        item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        # if self.isLive:
        #     item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')

        if encrypted:

            item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')

            licence_url = 'https://proxy.claro01.verspective.net/multirights/widevine?deviceId={deviceId}'.format(deviceId=base64.urlsafe_b64encode(device_id))

            key_headers = {
                'Referer': 'https://www.nowonline.com.br/',
                'Origin': 'https://www.nowonline.com.br',
            }

            video_type = 'LIVE' if self.isLive else 'VOD'

            if not self.isLive:
                url_id = 'https://www.nowonline.com.br/avsclient/contents/product/{id}?channel={platform}'.format(id=id, platform=PLATFORM)
                header = {
                    'referer': 'https://www.nowonline.com.br/',
                }
                if PLATFORM == 'PCTV':
                    header['x-xsrf-token'] = xsrf
                cookies = {
                    'avs_cookie': avs_cookie,
                    'LoginInfo': login_info
                }
                control.log('GET VOD ID: %s' % url_id)
                response = requests.get(url_id, headers=header, cookies=cookies, proxies=proxy).json()
                control.log(response)
                available = response.get('response', {}).get('watch', {}).get('available', False)

                if not available:
                    control.okDialog(u'Now Online', 'Content not available')
                    return

                cp_id = response.get('response', {}).get('cpId', -1)
            else:
                cp_id = id

            if PLATFORM == 'PCTV':
                account_device_id = '|accountDeviceId=1234567' if not self.isLive else ''
                key_headers['privateData'] = 'cookie={avs_cookie}|avs_id={id}|platform={platform}|videoType={videoType}|x-xsrf-token={xsrf}{account_device_id}'.format(avs_cookie=avs_cookie, id=cp_id, xsrf=xsrf, platform=PLATFORM, videoType=video_type, account_device_id=account_device_id)
                user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36'
            else:
                key_headers['privateData'] = 'cookie={avs_cookie}|avs_id={id}|platform={platform}|videoType={videoType}|accountDeviceId={deviceId}||isDownload=Y'.format(avs_cookie=avs_cookie, id=cp_id, deviceId=device_id, platform=PLATFORM, videoType=video_type)
                user_agent = 'NOW/1 CFNetwork/1197 Darwin/20.0.0'

            key_headers['User-Agent'] = user_agent
            key_headers['content-type'] = 'application/octet-stream'

            license_key = '%s|%s|R{SSM}|' % (licence_url, urllib.urlencode(key_headers))
            item.setProperty('inputstream.adaptive.license_key', license_key)
            item.setProperty('inputstream.adaptive.stream_headers', user_agent)

            control.log('license_key: %s' % license_key)

        if control.is_inputstream_available():
            item.setProperty('inputstreamaddon', 'inputstream.adaptive')

        control.resolve(int(sys.argv[1]), True, item)

        control.log("Done playing. Quitting...")

    def get_cdn(self, id, live=True):

        credentials = login()

        avs_cookie = credentials['cookies']['avs_cookie']
        login_info = credentials['cookies']['LoginInfo']
        xsrf = credentials['headers']['X-Xsrf-Token']

        header = {
            'referer': 'https://www.nowonline.com.br/',
        }

        type = 'LIVE' if live else 'VOD'

        device_id = None
        if PLATFORM == 'PCTV':
            header['x-xsrf-token'] = xsrf
            url = 'https://www.nowonline.com.br/avsclient/playback/getcdn?id={id}&type={type}&player=bitmovin&tvChannelId={id}&channel={platform}'.format(id=id, platform=PLATFORM, type=type)
        else:
            device_id = credentials.get('deviceId')
            url = 'https://www.nowonline.com.br/avsclient/playback/getcdn?player=bitmovin&id={id}&channel={platform}&asJson=Y&accountDeviceId={deviceId}&type={type}'.format(id=id, platform=PLATFORM, deviceId=device_id, type=type)

        cookies = {
            'avs_cookie': avs_cookie,
            'LoginInfo': login_info
        }

        control.log('NOW ONLINE GET ' + url)
        control.log(header)
        control.log(cookies)

        response = requests.get(url, headers=header, cookies=cookies, proxies=proxy)

        # response.raise_for_status()

        response = response.json() or {}

        control.log(response)

        src = (response.get('response', {}) or {}).get('src', None) or None
        sc_id = (response.get('response', {}) or {}).get('scId', None) or None

        if not src:
            status = response.get('status', 'Error') or 'Error'
            message = response.get('message', 'Authentication Error') or 'Authentication Error'
            raise Exception('%s: %s' % (status, message))

        if PLATFORM == 'PCTV':
            device_id = self.get_device_id(id, avs_cookie, login_info, xsrf)

        return src, avs_cookie, login_info, xsrf, device_id, sc_id

    def get_device_id(self, id, avs_cookie, login_info, xsrf):
        url = 'https://www.nowonline.com.br/avsclient/usercontent/epg/livechannels?channel={platform}&channelIds={id}&numberOfSchedules=1'.format(id=id, platform=PLATFORM)
        headers = {
            'referer': 'https://www.nowonline.com.br/',
            'x-xsrf-token': xsrf
        }
        cookies = {
            'avs_cookie': avs_cookie,
            'LoginInfo': login_info
        }

        response = requests.get(url, headers=headers, cookies=cookies, proxies=proxy)

        control.log(response.content)

        return response.cookies.get('avs_browser_id')

    def keep_alive(self, avs_cookie, login_info, xsrf, sc_id=None):
        # https://www.nowonline.com.br/avsclient/playback/keepalive?scId=4df59745-4568-4057-9324-7a2c158a04ae&noRefresh=N&channel=PCTV

        url = 'https://www.nowonline.com.br/avsclient/playback/keepalive?noRefresh=N&channel={platform}'.format(platform=PLATFORM)
        headers = {
            'referer': 'https://www.nowonline.com.br/',
            'x-xsrf-token': xsrf
        }
        cookies = {
            'avs_cookie': avs_cookie,
            'LoginInfo': login_info
        }

        control.log('GET %s' % url)

        response = requests.get(url, headers=headers, cookies=cookies, proxies=proxy)

        control.log('Response: %s' % response.status_code)
        control.log(response.content)
