from resources.lib.modules import control
from resources.lib.modules import client

PLAYER_VERSION = '1.1.24'


def get_video_info(video_id, children_id=None):
    playlist_url = 'http://api.globovideos.com/videos/%s/playlist'
    playlist_json = client.request(playlist_url % video_id, headers={"Accept-Encoding": "gzip"})

    if not playlist_json or playlist_json is None or 'videos' not in playlist_json or len(playlist_json['videos']) == 0:
        control.infoDialog(message=control.lang(34101).encode('utf-8'), sound=True, icon='ERROR')
        return None

    playlist_json = playlist_json['videos'][0]

    play_children = control.setting('play_children') == 'true' or children_id is not None

    if play_children and 'children' in playlist_json and len(playlist_json['children']) > 0 and 'cuepoints' in playlist_json and len(playlist_json['cuepoints']) > 0:
        # resources = next((children for children in playlist_json['children'] if children['id]']==children_id), playlist_json['children'][0])
        return [_select_resource(children['id'], children['resources'], playlist_json, children['title']) for children in playlist_json['children']]
    else:
        return _select_resource(video_id, playlist_json['resources'], playlist_json)


def _select_resource(video_id, resources, metadata, title_override=None):
    resource = None
    encrypted = False
    player = 'android'

    enable_4k = control.is_4k_enabled
    enable_hdr = control.setting('enable_hdr') == 'true'
    prefer_dash = control.setting('prefer_dash') == 'true'

    for node in resources:
        if 'players' in node and 'encrypted' in node and node['encrypted'] and any('android_native' in s for s in node['players']) and any('widevine' in s for s in node['content_protection']):
            encrypted = True
            resource = node
            player = 'android_native'
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

    if not resource and enable_4k and enable_hdr:
        for node in resources:
            if 'players' in node and 'height' in node and node['height'] == 2160 and any('androidtv_hdr' in s for s in node['players']):
                resource = node
                player = 'androidtv_hdr'
                break

    if not resource and enable_4k:
        for node in resources:
            if 'players' in node and 'height' in node and node['height'] == 2160 and any('androidtv_sdr' in s for s in node['players']):
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
            if 'players' in node and any('android' in s for s in node['players']):
                resource = node
                player = 'android'
                break

    if (resource or None) is None:
        control.infoDialog(message=control.lang(34102).encode('utf-8'), sound=True, icon='ERROR')
        return None

    subtitles = []
    for subtitle in resources:
        if 'type' in subtitle and subtitle['type'] == 'subtitle':
            subtitles.append({
                'language': subtitle['language'],
                'url': subtitle['url']
            })

    return {
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
        "url": resource["url"],
        "query_string_template": resource["query_string_template"],
        "thumbUri": resource["thumbUri"] if 'thumbUri' in resource else None,
        "encrypted": encrypted,
        "protection_url": resource['content_protection']['widevine']['server'].replace('{{deviceId}}', 'NmExZjhkODljZWE5YTZkZWQ3MTIzNmJhNzg3NQ==') if encrypted else None,
        "protection_type": 'widevine' if encrypted else None,
        'subtitles': subtitles
    }