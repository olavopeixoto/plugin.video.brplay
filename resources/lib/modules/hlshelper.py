import xbmcgui,xbmc

from resources.lib.modules import control
import resources.lib.modules.m3u8 as m3u8
from resources.lib.hlsproxy.proxy import HlsProxy

try:
    import http.cookiejar as cookielib
except:
    import cookielib

__url_resolver__ = None


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
    global __url_resolver__

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

    player_type_temp = control.setting('proxy_type')

    if player_type_temp == "0":
        player_type = "Downloader"
    else:
        player_type = "Redirect"

    if bandwidth_setting == 'Manual':
        option_adaptive_downloader = '%s %s' % (control.lang(33102), control.lang(33202))
        option_adaptive_redirect = '%s %s' % (control.lang(33102), control.lang(33203))
        option_auto = control.lang(33103)
        option_manual = control.lang(33104)
        options = [option_auto, option_adaptive_downloader, option_adaptive_redirect, option_manual]
        dialog = xbmcgui.Dialog()
        bandwidth_option = dialog.select(control.lang(34010), options)
        if bandwidth_option < 0:
            return None, None, None, None
        elif bandwidth_option == 0:
            bandwidth_setting = 'Auto'
        elif bandwidth_option == 1:
            bandwidth_setting = 'Adaptive'
            player_type = 'Downloader'
        elif bandwidth_option == 2:
            bandwidth_setting = 'Adaptive'
            player_type = 'Redirect'
        elif bandwidth_option == 3:
            bandwidth_setting = 'Manual'

    if bandwidth_setting == 'Auto':
        if control.isJarvis:
            cookie_jar = cookielib.MozillaCookieJar(control.cookieFile)
            cookie_jar.clear()
            cookie_jar.save(control.cookieFile, False, False)
        return url, None, None, None

    if bandwidth_setting == 'Adaptive':

        proxy = control.proxy_url
        maxbandwidth = get_max_bandwidth()

        if __url_resolver__ is None:
            __url_resolver__ = HlsProxy()

        if player_type == 'Downloader':
            from resources.lib.hlsproxy.hlsdownloader import HLSDownloader
            player = HLSDownloader
        else:
            from resources.lib.hlsproxy.hlswriter import HLSWriter
            player = HLSWriter
            # from resources.lib.hlsproxy.simplewriter import SimpleHLSWriter
            # player = SimpleHLSWriter

        url, mime_type = __url_resolver__.resolve(url, proxy=proxy, maxbitrate=maxbandwidth, player=player)

        return url, mime_type, __url_resolver__.stop_event, None

    playlist, cookies = m3u8.load(url)

    if playlist is None:
        return None, None, None, None

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
        bandwidth = dialog.select(control.lang(34010), options)
        if bandwidth < 0:
            return None, None, None, None
    else:
        if bandwidth_setting == 'Max':
            bandwidth = len(bandwidth_options) - 1
        elif bandwidth_setting == 'Medium':
            bandwidth = len(bandwidth_options) - 2
        elif bandwidth_setting == 'Low':
            bandwidth = 1

    cookies_dict = cookies.get_dict()
    cookies_str = ";".join([str(key)+"="+str(cookies_dict[key]) for key in cookies_dict])

    if control.isJarvis:
        url = playlist.playlists[bandwidth_options[bandwidth]['index']].absolute_uri

        cookie_jar = cookielib.MozillaCookieJar(control.cookieFile)
        cookie_jar.clear()
        for cookie in cookies:
            cookie_jar.set_cookie(cookie)
        cookie_jar.save(control.cookieFile, False, False)
    else:
        url = '%s|Cookie=%s' % (playlist.playlists[bandwidth_options[bandwidth]['index']].absolute_uri, cookies_str)

    control.log("FINAL URL: %s" % url)

    return url, None, None, cookies_str
