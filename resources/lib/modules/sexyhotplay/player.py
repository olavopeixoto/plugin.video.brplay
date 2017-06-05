# -*- coding: utf-8 -*-

import json
import re
import sys
import urllib

import auth
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules.util import get_signed_hashes


class player:
    def __init__(self):
        self.retry = 0

    def playVod(self, id, meta):

        self.retry = 0

        control.log("PLAY SEXYHOT - ID: %s" % id)

        if id == None: return
        try:
            id = self.__getGloboId(id)

            control.log('globo_midia_id: %s' % str(id))

            info = self.__getVideoInfo(id)

            title = info['title']

            signed_hashes = get_signed_hashes(info['hash'])

            query_string = re.sub(r'{{(\w*)}}', r'%(\1)s', info['query_string_template'])

            query_string = query_string % {
                'hash': signed_hashes[0],
                'key': 'html5'
            }

            url = '?'.join([info['url'], query_string])

            control.log("live media url: %s" % url)

            try: meta = json.loads(meta)
            except: meta = {
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

            item = control.item(path=url)
            item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'tvshow.poster': poster, 'season.poster': poster})
            item.setProperty('IsPlayable', 'true')
            item.setInfo(type='Video', infoLabels=meta)

            control.resolve(int(sys.argv[1]), id != None, item)
        except:
            pass



    def __getGloboId(self, id):
        provider = control.setting('globosat_provider').lower().replace(' ', '_')
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

        authenticator = getattr(auth, provider)()
        token, sessionKey = authenticator.get_token(username, password, select_profile=False)

        url = "http://sexyhotplay.com.br/vod/ajax/playback/"

        json_response = client.request(url, error=True, post=urllib.urlencode({
            'url': 'https://api.vod.globosat.tv/sexyhotplay',
            'midiaId': id,
            'sessionKey': sessionKey
        }), headers={
            "Content-Type":"application/x-www-form-urlencoded",
            'Accept-Encoding': 'gzip'
        })

        if 'autorizado' in json_response and json_response['autorizado'] == False:
            if self.retry == 0:
                self.retry = self.retry + 1
                authenticator.clearCredentials()
                return self.__getGloboId(id)
            else:
                control.infoDialog(control.lang(31200).encode('utf-8'), heading=u'Não Autorizado: %s' % json_response['motivo'], sound=True, icon='ERROR')
                control.idle()
                sys.exit()
                return None

        return json_response['videos']['globovideos']['original']



    def __getVideoInfo(self, id):

        proxy = control.setting('proxy_url')
        proxy = None if proxy == None or proxy == '' else {
            'http': proxy,
            'https': proxy,
        }

        playlistUrl = 'http://api.globovideos.com/videos/%s/playlist'
        playlistJson = client.request(playlistUrl % id, headers={"Accept-Encoding": "gzip"})

        if not 'videos' in playlistJson or len(playlistJson['videos']) == 0:
            return control.infoDialog(control.lang(31200).encode('utf-8'), heading=str('Video Info Not Found'), sound=True, icon='ERROR')
            # raise Exception("Player version not found.")

        playlistJson = playlistJson['videos'][0]

        for node in playlistJson['resources']:
            if any("ios" in s for s in node['players']):
                resource = node
                break

        if resource == None:
            return control.infoDialog(control.lang(31200).encode('utf-8'), heading=str('Video Resource Not Found'), sound=True, icon='ERROR')

        resource_id = resource['_id']

        provider = control.setting('globosat_provider').lower().replace(' ', '_')
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

        #authenticate
        authenticator = getattr(auth, provider)()
        credentials = authenticator.authenticate(playlistJson["provider_id"], username, password, False)

        hashUrl = 'https://security.video.globo.com/videos/%s/hash?resource_id=%s&version=1.1.23&player=ios' % (id, resource_id)

        control.log("HASH URL: %s" % hashUrl)

        hashJson = client.request(hashUrl, cookie=credentials, mobile=True, headers={"Accept-Encoding": "gzip"}, proxy=proxy)

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
            "thumbUri": None, #resource["thumbUri"],
            "hash": hashJson["hash"]
        }