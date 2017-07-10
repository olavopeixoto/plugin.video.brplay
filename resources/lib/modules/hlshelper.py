import xbmcgui,xbmc

from resources.lib.modules import control
import urllib, resources.lib.modules.m3u8 as m3u8
from resources.lib.hlsproxy.proxy import hlsProxy

try:
    import http.cookiejar as cookielib
except:
    import cookielib

from resources.lib.hlsproxy.hlsdownloader import HLSDownloader
from resources.lib.hlsproxy.hlswriter import HLSWriter

def get_max_bandwidth():
    bandwidth_setting = control.setting('bandwidth')

    max_bandwidth = 99999999999999

    if bandwidth_setting == 'Max':
        return max_bandwidth

    if bandwidth_setting == 'Medium':
        return 1264000

    if bandwidth_setting == 'Low':
        return 264000

    configured_limit = control.getBandwidthLimit()
    return configured_limit if configured_limit > 0 else max_bandwidth


def pickBandwidth(url):

    bandwidth_setting = control.setting('bandwidth')

    if bandwidth_setting == 'Auto':
        cookie_jar = cookielib.MozillaCookieJar(control.cookieFile, None, None)
        cookie_jar.clear()
        cookie_jar.save(control.cookieFile, None, None)
        return url, None, None

    if bandwidth_setting == 'Adaptive':
        proxy = control.setting('proxy_url')
        maxbandwidth = get_max_bandwidth()
        url_resolver = hlsProxy()
        player_type = control.setting('proxy_type')
        player = HLSDownloader if player_type == 'Downloader' else HLSWriter
        url, mime_type = url_resolver.resolve(url, proxy=proxy, use_proxy_for_chunks=True, maxbitrate=maxbandwidth, player=player)
        return url, mime_type, url_resolver.stopEvent

    #Adaptive|Auto|Manual|Max|Medium|Low

    playlist, cookies = m3u8.load(url)

    bandwidth_options = []
    for index, playlist_item in enumerate(playlist.playlists):
        # xbmc.log("BANDWIDTH: %s | URL: %s" % (str(playlist.playlists[index].stream_info.bandwidth), playlist.playlists[index].absolute_uri), level=xbmc.LOGNOTICE)
        bandwidth_options.append({
            'index': index,
            'bandwidth': str(playlist.playlists[index].stream_info.bandwidth)
        })
    bandwidth_options = sorted(bandwidth_options, key=lambda k: int(k['bandwidth']))

    if bandwidth_setting == 'Manual':
        options = []
        options = options + [b['bandwidth'] for b in bandwidth_options]
        dialog = xbmcgui.Dialog()
        bandwidth = dialog.select("Pick the desired bandwidth:", options)
    else:
        if bandwidth_setting == 'Max':
            bandwidth = len(bandwidth_options)
        elif bandwidth_setting == 'Medium':
            bandwidth = len(bandwidth_options) - 2
        elif bandwidth_setting == 'Low':
            bandwidth = 1

    cookies_str = urllib.urlencode(cookies.get_dict()).replace('&', '; ') + ';'
    url = '%s|Cookie=%s' % (playlist.playlists[bandwidth_options[bandwidth]['index']].absolute_uri, cookies_str)
    xbmc.log("FINAL URL: %s" % url, level=xbmc.LOGNOTICE)

    cookie_jar = cookielib.MozillaCookieJar(control.cookieFile, None, None)
    cookie_jar.clear()
    for cookie in cookies:
        cookie_jar.set_cookie(cookie)
    cookie_jar.save(control.cookieFile, None, None)

    return url, None, None