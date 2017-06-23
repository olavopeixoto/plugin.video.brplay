import xbmcgui

from resources.lib.modules import control
import urllib, resources.lib.modules.m3u8 as m3u8

# try:
#     import http.cookiejar as cookielib
# except:
#     import cookielib

def pickBandwidth(url):

    bandwidth_setting = control.setting('bandwidth')

    if bandwidth_setting == 'Auto':
       return url

    #Auto|Manual|Max|Medium|Low

    playlist, cookies = m3u8.load(url)

    bandwidth_options = []
    for index, playlist_item in enumerate(playlist.playlists):
        bandwidth_options.append({
            'index': index,
            'bandwidth': str(playlist.playlists[index].stream_info.bandwidth)
        })
    bandwidth_options = sorted(bandwidth_options, key=lambda k: int(k['bandwidth']))

    if bandwidth_setting == 'Manual':
        options = ['Auto'] if control.isJarvis else []
        options = options + [b['bandwidth'] for b in bandwidth_options]
        dialog = xbmcgui.Dialog()
        bandwidth = dialog.select("Pick the desired bandwidth:", options)
        if control.isJarvis:
            if bandwidth == 0:
                return url
            bandwidth = bandwidth - 1
    else:
        if bandwidth_setting == 'Max':
            bandwidth = len(bandwidth_options)
        elif bandwidth_setting == 'Medium':
            bandwidth = len(bandwidth_options) - 2
        elif bandwidth_setting == 'Low':
            bandwidth = 1

    cookies_str = urllib.urlencode(cookies.get_dict()).replace('&', '; ') + ';'
    url = '%s|Cookie=%s' % (playlist.playlists[bandwidth].absolute_uri, cookies_str)
    control.log("FINAL URL: %s" % url)

    # if control.isJarvis:
    #     cookie_jar = cookielib.MozillaCookieJar(control.cookieFile, None, None)
    #     cookie_jar.clear()
    #     for cookie in cookies:
    #         cookie_jar.set_cookie(cookie)
    #     cookie_jar.save(control.cookieFile, None, None)

    return url