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
    bandwidth_setting_temp = control.setting('bandwidth')

    # In settings.xml - bandwidth
    # Adaptive = '0'
    # Auto = '1'
    # Manual = '2'
    # Max = '3'
    # Medium = '4'
    # Low = '5'

    if bandwidth_setting_temp == '0':
        bandwidth_setting = 'Adaptive'
    elif bandwidth_setting_temp == '1':
        bandwidth_setting = 'Auto'
    elif bandwidth_setting_temp == '2':
        bandwidth_setting = 'Manual'
    elif bandwidth_setting_temp == '3':
        bandwidth_setting = 'Max'
    elif bandwidth_setting_temp == '4':
        bandwidth_setting = 'Medium'
    else:
        bandwidth_setting = 'Low'

    max_bandwidth = 99999999999999

    if bandwidth_setting == 'Max':
        return max_bandwidth

    if bandwidth_setting == 'Medium':
        return 1264000

    if bandwidth_setting == 'Low':
        return 264000

    configured_limit = control.getBandwidthLimit()
    return configured_limit if configured_limit > 0 else max_bandwidth


def pick_bandwidth(url):

    bandwidth_setting_temp = control.setting('bandwidth')

    # In settings.xml - bandwidth
    # Auto = '0'
    # Adaptive = '1'
    # Manual = '2'
    # Max = '3'
    # Medium = '4'
    # Low = '5'
    if bandwidth_setting_temp == "1":
        bandwidth_setting = "Adaptive"
    elif bandwidth_setting_temp == "2":
        bandwidth_setting = "Manual"
    elif bandwidth_setting_temp == "3":
        bandwidth_setting = "Max"
    elif bandwidth_setting_temp == "4":
        bandwidth_setting = "Medium"
    elif bandwidth_setting_temp == "5":
        bandwidth_setting = "Low"
    else:
        bandwidth_setting = "Auto"

    if bandwidth_setting == 'Auto':
        cookie_jar = cookielib.MozillaCookieJar(control.cookieFile, None, None)
        cookie_jar.clear()
        cookie_jar.save(control.cookieFile, None, None)
        return url, None, None

    if bandwidth_setting == 'Adaptive':

        proxy = control.proxy_url
        maxbandwidth = get_max_bandwidth()
        url_resolver = hlsProxy()

        player_type_temp = control.setting('proxy_type')

        if player_type_temp == "0":
            player_type = "Downloader"
        else:
            player_type = "Redirect"

        player = HLSDownloader if player_type == 'Downloader' else HLSWriter

        if player_type == 'Redirect':
            player.DOWNLOAD_IN_BACKGROUND = False
        elif player_type != 'Downloader':
            player.DOWNLOAD_IN_BACKGROUND = True

        url, mime_type = url_resolver.resolve(url, proxy=proxy, maxbitrate=maxbandwidth, player=player)

        return url, mime_type, url_resolver.stopEvent

    playlist, cookies = m3u8.load(url)

    if playlist is None:
        return None, None, None

    bandwidth_options = []
    for index, playlist_item in enumerate(playlist.playlists):
        bandwidth_options.append({
            'index': index,
            'bandwidth': str(playlist.playlists[index].stream_info.bandwidth)
        })
    bandwidth_options = sorted(bandwidth_options, key=lambda k: int(k['bandwidth']))

    if bandwidth_setting == 'Manual':
        options = []
        options = options + [b['bandwidth'] for b in bandwidth_options]
        dialog = xbmcgui.Dialog()
        bandwidth = dialog.select(control.lang(34010).encode('utf-8'), options)
    else:
        if bandwidth_setting == 'Max':
            bandwidth = len(bandwidth_options) - 1
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