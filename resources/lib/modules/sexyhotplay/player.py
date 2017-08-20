# -*- coding: utf-8 -*-

import json
import re
import sys
import urllib
import threading
import auth
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules.util import get_signed_hashes
from resources.lib.modules import hlshelper

import xbmc


class Player(xbmc.Player):
    def __init__(self):
        super(xbmc.Player, self).__init__()
        self.stopPlayingEvent = None
        self.retry = 0

    def play_vod(self, id, meta):

        self.retry = 0

        control.log("PLAY SEXYHOT - ID: %s" % id)

        if id is None:
            return

        id = self.__get_globo_id(id)

        control.log('globo_midia_id: %s' % str(id))

        if id is None:
            return

        info = self.__get_video_info(id)

        if info is None:
            return

        title = info['title']

        signed_hashes = get_signed_hashes(info['hash'])

        query_string = re.sub(r'{{(\w*)}}', r'%(\1)s', info['query_string_template'])

        query_string = query_string % {
            'hash': signed_hashes[0],
            'key': 'html5'
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
                "thumb": None,
                "mediatype": "video"
            }

        meta.update({
            "genre": info["category"],
        });

        poster = meta['poster'] if 'poster' in meta else control.addonPoster()
        thumb = meta['thumb'] if 'thumb' in meta else info["thumbUri"]

        url, mime_type, stopEvent = hlshelper.pick_bandwidth(url)
        control.log("Resolved URL: %s" % repr(url))

        item = control.item(path=url)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'tvshow.poster': poster, 'season.poster': poster})
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='Video', infoLabels=meta)

        if mime_type:
            item.setMimeType(mime_type)

        item.setContentLookup(False)

        control.resolve(int(sys.argv[1]), id != None, item)

        self.stopPlayingEvent = threading.Event()
        self.stopPlayingEvent.clear()

        while not self.stopPlayingEvent.isSet():
            if control.monitor.abortRequested():
                control.log("Abort requested")
                break
            control.sleep(500)

        if stopEvent:
            control.log("Setting stop event for proxy player")
            stopEvent.set()

    def onPlayBackStarted(self):
        # Will be called when xbmc starts playing a file
        control.log("Playback has started!")

    def onPlayBackEnded(self):
        # Will be called when xbmc stops playing a file
        control.log("setting event in onPlayBackEnded ")
        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        control.log("setting event in onPlayBackStopped ")
        if self.stopPlayingEvent:
            self.stopPlayingEvent.set()

    def __get_globo_id(self, id):
        provider = control.setting('globosat_provider').lower().replace(' ', '_')
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

        authenticator = getattr(auth, provider)()
        token, sessionKey = authenticator.get_token(username, password, select_profile=False)

        if not sessionKey:
            return None

        url = "http://sexyhotplay.com.br/vod/ajax/playback/"

        json_response = client.request(url, error=True, post=urllib.urlencode({
            'url': 'https://api.vod.globosat.tv/sexyhotplay',
            'midiaId': id,
            'sessionKey': sessionKey
        }), headers={
            "Content-Type": "application/x-www-form-urlencoded",
            'Accept-Encoding': 'gzip'
        })

        if 'autorizado' in json_response and json_response['autorizado'] == False:
            if self.retry == 0:
                self.retry = self.retry + 1
                authenticator.clearCredentials()
                return self.__get_globo_id(id)
            else:
                control.infoDialog(message=u'%s: %s' % (control.lang(34104).encode('utf-8'), json_response['motivo']), sound=True, icon='ERROR')
                control.idle()
                sys.exit()
                return None

        return json_response['videos']['globovideos']['original']

    def __get_video_info(self, id):

        playlistUrl = 'http://api.globovideos.com/videos/%s/playlist'
        playlistJson = client.request(playlistUrl % id, headers={"Accept-Encoding": "gzip"})

        if not 'videos' in playlistJson or len(playlistJson['videos']) == 0:
            control.infoDialog(message=control.lang(34101).encode('utf-8'), sound=True, icon='ERROR')
            return None

        playlistJson = playlistJson['videos'][0]

        for node in playlistJson['resources']:
            if any("ios" in s for s in node['players']):
                resource = node
                break

        if resource == None:
            control.infoDialog(message=control.lang(34102).encode('utf-8'), sound=True, icon='ERROR')
            return None

        resource_id = resource['_id']

        provider = control.setting('globosat_provider').lower().replace(' ', '_')
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

        # authenticate
        authenticator = getattr(auth, provider)()
        credentials = authenticator.authenticate(playlistJson["provider_id"], username, password, False)

        hashUrl = 'https://security.video.globo.com/videos/%s/hash?resource_id=%s&version=1.1.23&player=ios' % (
        id, resource_id)

        control.log("HASH URL: %s" % hashUrl)

        hashJson = client.request(hashUrl, cookie=credentials, mobile=True, headers={"Accept-Encoding": "gzip"})

        control.log("HASH JSON: %s" % repr(hashJson))

        if 'http_status_code' in hashJson and hashJson['http_status_code'] == 403:
            control.infoDialog(message=str('%s: %s' % (control.lang(34105).encode('utf-8'), hashJson['message'])), sound=True, icon='ERROR')
            return None

        return {
            "id": playlistJson["id"],
            "title": playlistJson["title"],
            "program": playlistJson["program"],
            "program_id": playlistJson["program_id"],
            "provider_id": playlistJson["provider_id"],
            "channel": playlistJson["channel"],
            "channel_id": playlistJson["channel_id"],
            "category": playlistJson["category"],
            "subscriber_only": playlistJson["subscriber_only"],
            "exhibited_at": playlistJson["exhibited_at"],
            "player": "ios",
            "url": resource["url"],
            "query_string_template": resource["query_string_template"],
            "thumbUri": None,  # resource["thumbUri"],
            "hash": hashJson["hash"]
        }
