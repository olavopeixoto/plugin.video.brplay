from resources.lib.modules import control
from resources.lib.modules.globo_util import get_signed_hashes
import requests

PLAYER_VERSION = '1.1.24'
DEVICE_ID = "NmExZjhkODljZWE5YTZkZWQ3MTIzNmJhNzg3NQ=="
DEVICE_ID_KEY = "{{deviceId}}"


def get_video_router(video_id, is_live=False, cdn=None):

    proxy = control.proxy_url
    proxy = None if proxy is None or proxy == '' else {
        'http': proxy,
        'https': proxy,
    }

    cdn = cdn or 'globo'

    version = PLAYER_VERSION

    enable_4k = control.is_4k_enabled
    enable_hdr = control.setting('enable_hdr') == 'true'
    prefer_dash = control.setting('prefer_dash') == 'true'

    players_preference = []

    if enable_4k:
        if enable_hdr:
            players_preference.extend([
                'tvos_4k',
                'androidtv_hdr',
                'roku_4k_hdr',
                'webos_4k_hdr'
            ])
        else:
            players_preference.extend([
                'androidtv_sdr'
            ])

    players_preference.extend([
        'androidtv',
        'android',
        'android_native',

    ])

    container = '.mpd' if prefer_dash else None  # '.m3u8'

    selected_player = None

    response = None
    for player in players_preference:
        playlist_url = 'https://router.video.globo.com/cdn?video_id={video_id}&player_type={player}&video_type={video_type}&content_protection=widevine&quality=max&cdn={cdn}'
        final_url = playlist_url.format(video_id=video_id, player=player, video_type='Live' if is_live else 'Video', cdn=cdn)
        control.log('[Globoplay Player] - GET %s' % final_url)
        response = requests.get(final_url, headers={"Accept-Encoding": "gzip"}, proxies=proxy).json()
        control.log(response)
        if response and 'resource' in response:
            if container is None or any(container in source["url"] for source in response['resource']['sources']):
                selected_player = player
                break

    if not response:
        raise Exception("Couldn't find resource")

    resource = response['resource']
    encrypted = resource['drm_protection_enabled']

    if encrypted and resource['content_protection']['type'] != 'widevine':
        control.infoDialog(message='DRM not supported: %s' % resource['content_protection']['type'], sound=True, icon='ERROR')
        return None

    drm_scheme = 'com.widevine.alpha' if encrypted else None
    server_url = resource['content_protection']['server'] if encrypted else None

    source = resource['sources'][0]

    subtitles = []
    if 'subtitles' in source and source['subtitles']:
        for language in source['subtitles']:
            subtitle = source['subtitles'][language]
            subtitles.append({
                'language': subtitle['language'],
                'url': subtitle['url']
            })

    result = {
        "resource_id": resource['_id'],
        "id": video_id,
        "title": None,
        "program": None,
        "program_id": None,
        "provider_id": None,
        "channel": None,
        "channel_id": None,
        "category": None,
        "subscriber_only": True,
        "exhibited_at": None,
        "player": selected_player,
        "version": version,
        "url": source["url"],
        "query_string_template": source['auth_param_templates']["query_string"],
        "thumbUri": None,
        "encrypted": encrypted,
        "drm_scheme": drm_scheme,
        "protection_url": server_url.replace(DEVICE_ID_KEY, DEVICE_ID) if encrypted else None,
        'cdn': source['cdn'],
        'subtitles': subtitles
    }

    control.log(result)

    return result


def get_video_info(video_id, children_id=None, cdn=None):
    playlist_url = 'http://api.globovideos.com/videos/%s/playlist'
    playlist_json = requests.get(playlist_url % video_id, headers={"Accept-Encoding": "gzip"}).json()

    if not playlist_json or playlist_json is None or 'videos' not in playlist_json or len(playlist_json['videos']) == 0:
        message = (playlist_json or {}).get('message') or control.lang(34101)
        control.infoDialog(message=message, sound=True, icon='ERROR')
        return None

    control.log(playlist_json)

    playlist_json = playlist_json['videos'][0]

    play_children = control.setting('play_children') == 'true' or children_id is not None

    if play_children and 'children' in playlist_json and len(playlist_json['children']) > 0 and 'cuepoints' in playlist_json and len(playlist_json['cuepoints']) > 0:
        # resources = next((children for children in playlist_json['children'] if children['id]']==children_id), playlist_json['children'][0])
        return [_select_resource(children['id'], children['resources'], playlist_json, children['title'], cdn=cdn) for children in playlist_json['children']]
    else:
        return _select_resource(video_id, playlist_json['resources'], playlist_json, cdn=cdn)


def _select_resource(video_id, resources, metadata, title_override=None, cdn=None):
    resource = None
    encrypted = False
    player = 'android'
    drm_scheme = None

    enable_4k = control.is_4k_enabled
    enable_hdr = control.setting('enable_hdr') == 'true'
    prefer_dash = control.setting('prefer_dash') == 'true'
    prefer_smoothstreaming = control.setting('prefer_smoothstreaming') == 'true'
    prefer_playready = control.setting('prefer_playready') == 'true'

    if prefer_smoothstreaming:
        for node in resources:
            if 'players' in node and 'encrypted' in node and node['encrypted'] and any('smoothstreaming' in s for s in node['players']) and any('playready' in s for s in node['content_protection']):
                encrypted = True
                resource = node
                player = 'android_native'
                drm_scheme = 'com.microsoft.playready'
                server_url = resource['content_protection']['playready']['server']
                break

    if prefer_playready and not resource:
        try_player = 'androidtv_hdr' if enable_hdr else 'androidtv_sdr' if enable_4k else 'androidtv'
        for node in resources:
            if 'players' in node and 'encrypted' in node and node['encrypted'] and any(try_player in s for s in node['players']) and any('playready' in s for s in node['content_protection']):
                encrypted = True
                resource = node
                player = try_player
                drm_scheme = 'com.microsoft.playready'
                server_url = resource['content_protection']['playready']['server']
                break
        if not resource:
            for node in resources:
                if 'players' in node and 'encrypted' in node and node['encrypted'] and any('android_native' in s for s in node['players']) and any('playready' in s for s in node['content_protection']):
                    encrypted = True
                    resource = node
                    player = 'android_native'
                    drm_scheme = 'com.microsoft.playready'
                    server_url = resource['content_protection']['playready']['server']
                    break

    if not resource:
        for node in resources:
            if 'players' in node and 'encrypted' in node and node['encrypted'] and any('android_native' in s for s in node['players']) and any('widevine' in s for s in node['content_protection']):
                encrypted = True
                resource = node
                player = 'android_native'
                drm_scheme = 'com.widevine.alpha'
                server_url = resource['content_protection']['widevine']['server']
                break

    if not resource and enable_4k and prefer_dash:
        for node in resources:
            if 'players' in node and any('tv_4k_dash' in s for s in node['players']):
                resource = node
                player = 'tv_4k_dash'
                break

    if not resource and prefer_dash:
        for node in resources:
            if 'players' in node and any('tv_dash' in s for s in node['players']):
                resource = node
                player = 'tv_dash'
                break

    if not resource and enable_4k and (not prefer_dash or not control.is_inputstream_available()):
        for node in resources:
            if 'players' in node and any('tvos_4k' in s for s in node['players']) and '2160' in node['_id'] and not node.get('encrypted', False):
                resource = node
                player = 'tvos_4k'
                break

    if not resource and enable_4k and enable_hdr:
        for node in resources:
            # if 'players' in node and 'height' in node and node['height'] == 2160 and any('androidtv_hdr' in s for s in node['players']):
            if 'players' in node and any('androidtv_hdr' in s for s in node['players']):
                resource = node
                player = 'androidtv_hdr'
                break

    if not resource and enable_4k:
        for node in resources:
            # if 'players' in node and 'height' in node and node['height'] == 2160 and any('androidtv_sdr' in s for s in node['players']):
            if 'players' in node and any('androidtv_sdr' in s for s in node['players']):
                resource = node
                player = 'androidtv_sdr'
                break

    #Prefer MP4 when available
    if not resource:
        for node in resources:
            if 'players' in node and 'height' in node and node['height'] == 720 and any('desktop' in s for s in node['players']):
                resource = node
                player = 'android'
                break

    if not resource:
        for node in resources:
            if 'players' in node and any('androidtv' in s for s in node['players']):
                resource = node
                player = 'androidtv'
                break

    if not resource:
        for node in resources:
            if 'players' in node and any('android' in s for s in node['players']):
                resource = node
                player = 'android'
                break

    if (resource or None) is None:
        control.infoDialog(message=control.lang(34102), sound=True, icon='ERROR')
        return None

    control.log('Selected resource for video %s: %s' % (video_id, resource['_id']))

    subtitles = []
    for subtitle in resources:
        if 'type' in subtitle and subtitle['type'] == 'subtitle':
            control.log('Found Subtitle: %s' % subtitle['url'])
            subtitles.append({
                'language': subtitle['language'],
                'url': subtitle['url']
            })

    cdn_data = resource['cdns'][cdn] if cdn in resource['cdns'] else None
    if cdn_data:
        domain = cdn_data['domain']
        query_string_template = cdn_data['query_string_template']
        path = resource['paths']['max']
        url = domain + path
    else:
        query_string_template = resource["query_string_template"]
        url = resource["url"]
        cdn = 'globo'

    result = {
        "resource_id": resource['_id'],
        "id": video_id,
        "title": title_override or metadata["title"],
        "program": metadata["program"],
        "program_id": metadata["program_id"],
        "provider_id": metadata["provider_id"],
        "channel": metadata["channel"],
        "channel_id": metadata["channel_id"],
        "category": metadata["category"],
        "subscriber_only": metadata["subscriber_only"],
        "exhibited_at": metadata["exhibited_at"],
        "player": player,
        "version": PLAYER_VERSION,
        "url": url,
        "cdn": cdn,
        "query_string_template": query_string_template,
        "thumbUri": resource["thumbUri"] if 'thumbUri' in resource else None,
        "encrypted": encrypted,
        "drm_scheme": drm_scheme,
        "protection_url": server_url.replace(DEVICE_ID_KEY, DEVICE_ID) if encrypted else None,
        'subtitles': subtitles
    }

    control.log(result)

    return result


def get_geofence_video_info(video_id, latitude, longitude, credentials, cdn=None):

    if credentials is None:
        return None

    proxy = control.proxy_url
    proxy = None if proxy is None or proxy == '' else {
        'http': proxy,
        'https': proxy,
    }

    version = PLAYER_VERSION

    # enable_4k = control.is_4k_enabled
    # enable_hdr = control.setting('enable_hdr') == 'true'

    players_preference = []

    # if enable_4k:
    #     if enable_hdr:
    #         players_preference.extend([
    #             'androidtv_hdr',
    #         ])
    #     else:
    #         players_preference.extend([
    #             'androidtv_sdr'
    #         ])

    players_preference.extend([
        # 'androidtv',
        'android',
        # 'android_native',

    ])

    selected_player = players_preference[0]

    post_data = {
        'player': selected_player,
        'version': version,
        'lat': latitude,
        'long': longitude,
        'cdn': cdn or 'globo'
    }

    # tz:       00:00
    # player:  ios_native
    # cdn:     globo
    # ts:      1613693205
    # udid:    bbec61e5f3a06ca54624e84accc232b5d49971a6
    # version: 10.25.0
    # lat:     51.49502563476562
    # long:    -0.03278398965019131

    hash_url = 'http://security.video.globo.com/videos/%s/hash' % video_id
    control.log('POST %s' % hash_url)
    control.log(post_data)
    control.log(credentials)
    response = requests.post(hash_url, cookies=credentials, headers={
                                                            "Accept-Encoding": "gzip",
                                                            "Content-Type": "application/x-www-form-urlencoded",
                                                            "User-Agent": "Canais Globo (Globosat Play)/444 (iPhone)"
                                                        }, data=post_data, proxies=proxy)

    response.raise_for_status()

    hash_json = response.json()

    control.log(hash_json)

    return {
        "id": video_id,
        "title": hash_json.get("name"),
        "category": 'Live',
        "subscriber_only": True,
        "channel": None,
        "player": selected_player,
        "url": hash_json.get("url"),
        "query_string_template": hash_json.get('query_string_template') or "h={{hash}}&k={{key}}&a={{openClosed}}&u={{user}}",
        "thumbUri": hash_json.get("thumbUri"),
        "hash_token": get_signed_hashes(hash_json.get('hash')) if 'hash' in hash_json else hash_json.get('token'),
        "user": hash_json.get("user"),
        "credentials": credentials,
        "encrypted": hash_json.get('encrypted', False)
    }
