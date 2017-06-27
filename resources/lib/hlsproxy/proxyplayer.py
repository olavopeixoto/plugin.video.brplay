import thread
import threading
import xbmcgui, xbmc

from resources.lib.hlsproxy.proxy import hlsProxy, MIME_TYPE


class ProxyPlayer():

    def play(self, url, name, proxy=None, use_proxy_for_chunks=False, maxbitrate=0):
        print "URL: " + url
        stopPlaying=threading.Event()
        progress = xbmcgui.DialogProgress()

        hls_proxy=hlsProxy()
        stopPlaying.clear()
        runningthread=thread.start_new_thread(hls_proxy.start,(stopPlaying,))
        progress.create('Starting local proxy')
        stream_delay = 1
        progress.update( 20, "", 'Loading local proxy', "" )
        xbmc.sleep(stream_delay*1000)
        progress.update( 100, "", "", "" )
        url_to_play = hls_proxy.prepare_url(url,proxy,use_proxy_for_chunks,maxbitrate=maxbitrate)

        progress.close()

        return url_to_play, MIME_TYPE