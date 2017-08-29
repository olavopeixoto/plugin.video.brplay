# -*- coding: utf-8 -*-

import json
import re
import sys
import urllib

import auth
from resources.lib.modules import util
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import hlshelper

import xbmc
import threading
import scraper_live

HISTORY_URL_API = 'https://api.vod.globosat.tv/globosatplay/watch_history.json?token=%s'


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

        if 'encrypted' in info and info['encrypted'] == 'true':
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

        self.url, mime_type, stopEvent = hlshelper.pick_bandwidth(url)

        if self.url is None:
            control.infoDialog(control.lang(34100).encode('utf-8'), icon='ERROR')
            return

        control.log("Resolved URL: %s" % repr(self.url))

        item = control.item(path=self.url)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'tvshow.poster': poster, 'season.poster': poster})
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='Video', infoLabels=meta)

        if mime_type:
            item.setMimeType(mime_type)

        item.setContentLookup(False)

        control.resolve(int(sys.argv[1]), True, item)

        self.stopPlayingEvent = threading.Event()
        self.stopPlayingEvent.clear()

        provider = control.setting('globosat_provider').lower().replace(' ', '_')
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

        if not username or not password or username == '' or password == '':
            return []

        authenticator = getattr(auth, provider)()
        self.token, sessionKey = authenticator.get_token(username, password)

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
        if self.offset > 0: self.seekTime(float(self.offset))

    def onPlayBackEnded(self):
        # Will be called when xbmc stops playing a file
        control.log("setting event in onPlayBackEnded ")

        if not self.isLive: self.save_video_progress(self.token, self.video_id, self.getTime())

        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        control.log("setting event in onPlayBackStopped ")

        if not self.isLive:
            self.save_video_progress(self.token, self.video_id, self.getTime())

        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

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

        for node in playlist_json['resources']:
            if any("ios" in s for s in node['players']):
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

        hash_url = 'https://security.video.globo.com/videos/%s/hash?resource_id=%s&version=1.1.23&player=ios' % (video_id, resource_id)
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
            "player": "ios",
            "url": resource["url"],
            "query_string_template": resource["query_string_template"],
            "thumbUri": resource["thumbUri"] if 'thumbUri' in resource else None,
            "hash": hash_json["hash"],
            "user": hash_json["user"] if 'user' in hash_json else None,
            "encrypted": resource['encrypted'] if 'encrypted' in resource else 'false',
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