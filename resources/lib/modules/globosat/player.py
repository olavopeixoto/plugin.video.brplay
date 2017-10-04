# -*- coding: utf-8 -*-

import json
import re
import sys
import urllib
from urlparse import urlparse

import auth
import auth_helper
from resources.lib.modules import util
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import hlshelper

import xbmc
import threading
import scraper_live

HISTORY_URL_API = 'https://api.vod.globosat.tv/globosatplay/watch_history.json?token=%s'
PLAYER_SLUG = 'android'
PLAYER_VERSION = '1.1.24'

# "urn:uuid:1077efec-c0b2-4d02-ace3-3c1e52e2fb4b": "org.w3.clearkey",
# "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed": "com.widevine.alpha",
# "urn:uuid:9a04f079-9840-4286-ab92-e65be0885f95": "com.microsoft.playready",
# "urn:uuid:f239e769-efa3-4850-9c16-a903c6932efb": "com.adobe.primetime"

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

        if id is None: return

        info = self.__get_video_info(id)

        if not info or 'channel' not in info:
            return

        encrypted = 'encrypted' in info and info['encrypted']

        if encrypted and not control.is_inputstream_available():
            control.infoDialog(message=control.lang(34103).encode('utf-8'), icon='Wr')
            return

        title = info['channel']

        signed_hashes = util.get_signed_hashes(info['hash'])

        query_string = re.sub(r'{{(\w*)}}', r'%(\1)s', info['query_string_template'])

        query_string = query_string % {
            'hash': signed_hashes[0],
            'key': 'app',
            'openClosed': 'F' if info['subscriber_only'] else 'A',
            'user': info['user'] if info['subscriber_only'] else ''
        }

        url = '?'.join([info['url'], query_string])

        control.log("live media url: %s" % url)

        try:
            meta = json.loads(meta)
        except:
            meta = {
                "playcount": 0,
                "overlay": 6,
                "title": title,
                "thumb": info["thumbUri"],
                "mediatype": "video",
                "aired": info["exhibited_at"]
            }

        meta.update({
            "genre": info["category"],
            "plot": info["title"],
            "plotoutline": info["title"]
        })

        poster = meta['poster'] if 'poster' in meta else control.addonPoster()
        thumb = meta['thumb'] if 'thumb' in meta else info["thumbUri"]

        self.offset = float(meta['milliseconds_watched']) / 1000.0 if 'milliseconds_watched' in meta else 0

        self.isLive = 'livefeed' in meta and meta['livefeed'] == 'true'

        parsed_url = urlparse(url)
        if parsed_url.path.endswith(".m3u8"):
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

        item = control.item(path=self.url)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'tvshow.poster': poster, 'season.poster': poster})
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='Video', infoLabels=meta)

        item.setContentLookup(False)

        if encrypted:
            licence_url = info['protection_url']

            mime_type = 'application/dash+xml'
            item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            # item.setProperty('inputstream.adaptive.manifest_type', 'ism')
            item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha') # 'com.microsoft.playready'
            item.setProperty('inputstream.adaptive.license_key', licence_url + "||R{SSM}|")
            # item.setProperty('inputstream.adaptive.license_data', licence_url)

        if mime_type:
            item.setMimeType(mime_type)
        elif not cookies:
            item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            item.setProperty('inputstreamaddon', 'inputstream.adaptive')

        control.resolve(int(sys.argv[1]), True, item)

        self.stopPlayingEvent = threading.Event()
        self.stopPlayingEvent.clear()

        self.token = auth_helper.get_globosat_token()

        self.video_id = info['id'] if 'id' in info else None

        last_time = 0.0
        while not self.stopPlayingEvent.isSet():
            if control.monitor.abortRequested():
                control.log("Abort requested")
                break
            if self.isPlaying() and not self.isLive:
                current_time = self.getTime()
                if current_time - last_time > 5 or (last_time == 0 and current_time > 1):
                    last_time = current_time
                    self.save_video_progress(self.token, self.video_id, current_time)
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

        # if self.stopPlayingEvent:
        #     self.stopPlayingEvent.set()

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        control.log("setting event in onPlayBackStopped ")

        # if self.stopPlayingEvent:
        #     self.stopPlayingEvent.set()

    def __get_video_info(self, video_id):

        proxy = control.proxy_url
        proxy = None if proxy is None or proxy == '' else {
            'http': proxy,
            'https': proxy,
        }

        playlist_url = 'http://api.globovideos.com/videos/%s/playlist'
        playlist_json = client.request(playlist_url % video_id, headers={"Accept-Encoding": "gzip"})

        if 'videos' not in playlist_json or len(playlist_json['videos']) == 0:
            control.infoDialog(message=control.lang(34101).encode('utf-8'), sound=True, icon='ERROR')
            return None
            # raise Exception("Player version not found.")

        playlist_json = playlist_json['videos'][0]

        resource = None
        encrypted = False

        for node in playlist_json['resources']:
            if 'encrypted' in node and node['encrypted'] and any('android_native' in s for s in node['players']) and any('widevine' in s for s in node['content_protection']):
                encrypted = True
                resource = node
                break

        if not resource:
            for node in playlist_json['resources']:
                if 'height' in node and node['height'] == 720 and any('desktop' in s for s in node['players']):
                    resource = node
                    break

        if not resource:
            for node in playlist_json['resources']:
                if any(PLAYER_SLUG in s for s in node['players']):
                    resource = node
                    break

        if (resource or None) is None:
            control.infoDialog(message=control.lang(34102).encode('utf-8'), sound=True, icon='ERROR')
            return None

        resource_id = resource['_id']

        provider = control.setting('globosat_provider').lower().replace(' ', '_')
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

        # authenticate
        authenticator = getattr(auth, provider)()
        credentials = authenticator.authenticate(playlist_json["provider_id"], username, password)

        hash_url = 'https://security.video.globo.com/videos/%s/hash?resource_id=%s&version=%s&player=%s' % (video_id, resource_id, PLAYER_VERSION, PLAYER_SLUG)
        hash_json = client.request(hash_url, cookie=credentials, mobile=True, headers={"Accept-Encoding": "gzip"}, proxy=proxy)

        if not hash_json or 'message' in hash_json and hash_json['message']:
            control.infoDialog(message=control.lang(34102).encode('utf-8'), sound=True, icon='ERROR')
            return None

        return {
            "id": playlist_json["id"],
            "title": playlist_json["title"],
            "program": playlist_json["program"],
            "program_id": playlist_json["program_id"],
            "provider_id": playlist_json["provider_id"],
            "channel": playlist_json["channel"],
            "channel_id": playlist_json["channel_id"],
            "category": playlist_json["category"],
            "subscriber_only": playlist_json["subscriber_only"],
            "exhibited_at": playlist_json["exhibited_at"],
            "player": PLAYER_SLUG,
            "url": resource["url"],
            "query_string_template": resource["query_string_template"],
            "thumbUri": resource["thumbUri"] if 'thumbUri' in resource else None,
            "hash": hash_json["hash"],
            "user": hash_json["user"] if 'user' in hash_json else None,
            "encrypted": encrypted,
            "protection_url": resource['content_protection']['widevine']['server'].replace('{{deviceId}}', 'NmExZjhkODljZWE5YTZkZWQ3MTIzNmJhNzg3NQ==') if encrypted else None,
            "protection_type": 'widevine' if encrypted else None,
            "credentials": credentials
        }

    def save_video_progress(self, token, video_id, watched_seconds):

        post_data = {
            'watched_seconds': int(round((watched_seconds))),
            'id': video_id
        }

        url = HISTORY_URL_API % token
        headers = {
            "Accept-Encoding": "gzip",
            "Content-Type": "application/x-www-form-urlencoded",
            "version": "2",
            "Authorization": scraper_live.GLOBOSAT_API_AUTHORIZATION
        }

        post_data = urllib.urlencode(post_data)

        client.request(url, error=True, mobile=True, headers=headers, post=post_data)