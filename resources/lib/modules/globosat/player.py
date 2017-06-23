import json
import re
import sys

import auth
from resources.lib.modules import util
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import hlshelper


class Player:
    def __init__(self):
        pass

    def playlive(self, id, meta):
        if id == None: return
        try:
            info = self.__getVideoInfo(id)

            if info['encrypted'] == 'true':
                control.infoDialog(control.lang(31200).encode('utf-8'), heading=str("Content is DRM encrypted it won't play in Kodi at this moment"), icon='Wr')

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

            try: meta = json.loads(meta)
            except: meta = {
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
            });

            poster = meta['poster'] if 'poster' in meta else control.addonPoster()
            thumb = meta['thumb'] if 'thumb' in meta else info["thumbUri"]

            url = hlshelper.pickBandwidth(url)

            item = control.item(path=url)
            item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'tvshow.poster': poster, 'season.poster': poster})
            item.setProperty('IsPlayable', 'true')
            item.setInfo(type='Video', infoLabels=meta)

            item.setContentLookup(False)

            # cookielib.MozillaCookieJar("mycookies.txt")

            # playlist = client.request(url)

            control.resolve(int(sys.argv[1]), True, item)
        except:
            pass

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

        if (resource or None) == None:
            return control.infoDialog(control.lang(31200).encode('utf-8'), heading=str('Video Resource Not Found'), sound=True, icon='ERROR')

        resource_id = resource['_id']

        provider = control.setting('globosat_provider').lower().replace(' ', '_')
        username = control.setting('globosat_username')
        password = control.setting('globosat_password')

        #authenticate
        authenticator = getattr(auth, provider)()
        credentials = authenticator.authenticate(playlistJson["provider_id"], username, password)

        hashUrl = 'https://security.video.globo.com/videos/%s/hash?resource_id=%s&version=1.1.23&player=ios' % (id, resource_id)
        hashJson = client.request(hashUrl, cookie=credentials, mobile=True, headers={"Accept-Encoding": "gzip"}, proxy=proxy)

        if not hashJson or 'message' in hashJson and hashJson['message']:
            return control.infoDialog(control.lang(31200).encode('utf-8'), heading=hashJson['message'], sound=True, icon='ERROR')

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
            "thumbUri": resource["thumbUri"] if 'thumbUri' in resource else None,
            "hash": hashJson["hash"],
            "user": hashJson["user"] if 'user' in hashJson else None,
            "encrypted": resource['encrypted'] if 'encrypted' in resource else 'false'
        }