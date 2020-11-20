import requests
import re
import json
import urllib
import control

proxy = control.proxy_url
proxy = None if proxy is None or proxy == '' else {
    'http': proxy,
    'https': proxy,
}


def geturl(url):

    control.log('YouTube: %s' % url)

    if url.startswith('https://www.youtube.com/embed/live_stream?channel='):
        video_id = get_video_id(url)
        # return get_manifest_url(video_id)
        return get_manifest_url_v2(video_id)

    r = re.search(r'https?://www.youtube.com/embed/([^/|^?]+)', url)
    if r:
        video_id = r.group(1)
        return get_manifest_url_v2(video_id)

    if url and not url.startswith('http'):
        url = 'https://www.youtube.com/channel/{channel}/live'.format(channel=url)

    # https://www.youtube.com/channel/UCoMdktPbSTixAyNGwb-UYkQ/live
    if url.startswith('https://www.youtube.com/channel/'):
        if not url.endswith('/live'):
            url = url + '/live'
        channel = re.search(r'https://www.youtube.com/channel/(.*?)/live', url).group(1)
        video_id = get_video_id('https://www.youtube.com/embed/live_stream?channel=' + channel)

        manifest_url = get_manifest_url(video_id)

        return manifest_url

    webpage = requests.get(url, proxies=proxy).content
    mobj = re.search(r';ytplayer.config = ({.*?});', webpage)
    player_config = json.loads(mobj.group(1))

    player_response_string = player_config['args']['player_response']

    player_response = json.loads(player_response_string)

    return player_response['streamingData']['hlsManifestUrl']


# https://www.youtube.com/embed/live_stream?channel=UCuiLR4p6wQ3xLEm15pEn1Xw
# url = 'https://www.youtube.com/embed/live_stream?channel=' + channel
def get_video_id(url):

    webpage = requests.get(url, proxies=proxy).content

    return re.search(r'\"video_id\":\"(.*?)\"', webpage).group(1)


def get_manifest_url(video_id):

    url = 'https://www.youtube.com/get_video_info?video_id=' + video_id
    result = requests.get(url, proxies=proxy).content
    result = urllib.unquote_plus(result)

    result = re.search(r'\"hlsManifestUrl\":\"(.*?)\"', result)

    if not result:
        control.log('NO hlsManifestUrl', control.LOGERROR)

    return result.group(1) if result else None


def get_manifest_url_v2(video_id):

    url = 'https://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1&bpctr=9999999999' % video_id
    result = requests.get(url, proxies=proxy).content

    # print result

    result = re.search(r';ytplayer\.config\s*=\s*({.+?});ytplayer', result)

    if not result:
        control.log('NO Config', control.LOGERROR)
        return None

    config = result.group(1)

    config_json = json.loads(config)

    player_response = json.loads(config_json['args']['player_response'])

    return player_response['streamingData']['hlsManifestUrl']


def get_manifest_url_by_url(url):

    result = requests.get(url, proxies=proxy).content
    result = urllib.unquote_plus(result)

    result = re.search(r'\"hlsManifestUrl\":\"(.*?)\"', result)

    if not result:
        control.log('NO hlsManifestUrl', control.LOGERROR)

    return result.group(1) if result else None
