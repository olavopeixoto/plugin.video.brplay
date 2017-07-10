# -*- coding: utf-8 -*-

"""
XBMCLocalProxy 0.1
Copyright 2011 Torben Gerkensmeyer
 
Modified for HLS format by brplayer
 
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
 
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import re
import socket
import traceback
import urllib
import urlparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn

import xbmc
import xbmcgui

import thread
import threading
# from resources.lib.modules import workers

# from hlsdownloader import HLSDownloader
# from hlswriter import HLSWriter as HLSDownloader
# from legacyhlsdownloader import HLSDownloader

g_stopEvent=None
VIDEO_MIME_TYPE = 'video/MP2T'
PLAYLIST_MIME_TYPE = 'application/vnd.apple.mpegurl'

HOST_NAME = '127.0.0.1'
PORT_NUMBER = 55444


def log(msg):
    # pass
    xbmc.log(msg, level=xbmc.LOGNOTICE)


class ProxyHandler(BaseHTTPRequestHandler):

    downloader = None

    """
    Serves a HEAD request
    """
    def do_HEAD(self):
        print "XBMCLocalProxy: Serving HEAD request..."
        self.send_response(200)
        self.send_header("Content-Type", PLAYLIST_MIME_TYPE)
        self.end_headers()

    """
    Serves a GET request.
    """
    def do_GET(self):
        print "XBMCLocalProxy: Serving GET request..."
        global g_stopEvent

        try:
            #Pull apart request path
            request_path=self.path[1:]
            path_and_query=request_path
            path_and_query_list = path_and_query.split('?')
            querystring = path_and_query_list[1] if len(path_and_query_list) > 1 else ''
            request_path=re.sub(r"\?.*","",request_path)

            init_done=False

            log("GET REQUEST: %s" % self.path)

            if request_path.lower() == "brplay":
                (url, proxy, use_proxy_for_chunks, maxbitrate) = self.decode_url(querystring)

                if not self.downloader.init(self.wfile, url, proxy, use_proxy_for_chunks, g_stopEvent, maxbitrate):
                    print 'cannot init'
                    raise Exception('HLS.url failed to play\nServer down? check Url.')

                log("GET REQUEST Content-Type: %s" % self.downloader.MAIN_MIME_TYPE)

                self.send_response(200)
                self.send_header("Content-Type", self.downloader.MAIN_MIME_TYPE)
                self.end_headers()

                init_done=True

                self.downloader.keep_sending_video(self.wfile)

            else:
                is_playlist = request_path.endswith('.m3u8')
                is_media = request_path.endswith('.ts')
                self.send_response(200)
                mime_type = PLAYLIST_MIME_TYPE if is_playlist else VIDEO_MIME_TYPE if is_media else 'application/octet-stream'
                log("GET REQUEST Content-Type: %s" % mime_type)
                self.send_header("Content-Type", mime_type)
                self.end_headers()
                init_done = True
                if is_playlist:
                    log("GET REQUEST MEDIA PLAYLIST")
                    base_uri = 'http://%s:%s' % (HOST_NAME, PORT_NUMBER)
                    self.downloader.download_segment_playlist(path_and_query, base_uri, self.wfile)
                elif is_media:
                    log("GET REQUEST MEDIA DATA")
                    self.downloader.download_segment_media(path_and_query, self.wfile)
                else:
                    log("GET REQUEST BINARY DATA")
                    self.downloader.download_binary(path_and_query, self.wfile)

        except Exception as inst:
            #Print out a stack trace
            traceback.print_exc()
            if not init_done:
                xbmc.executebuiltin("XBMC.Notification(BRPlayProxy,%s,4000,'')" % inst.message)
                self.send_error(404)
            print 'closed'
        finally:
            log("REQUEST COMPLETED")
            try:
                self.finish()
                log("REQUEST FINISHED CALLED SUCCESSFULLY")
            except Exception, e:
                xbmc.log("PROXYHANDLER ERROR: %s " % e.message, level=xbmc.LOGERROR)

    def decode_url(self, url):
        print 'in params',url
        params=urlparse.parse_qs(url)
        print 'params',params
        received_url = params['url'][0].replace('\r','')
        print 'received_url',received_url

        use_proxy_for_chunks = False
        proxy=None
        try:
            proxy = params['proxy'][0]
            use_proxy_for_chunks =  params['use_proxy_for_chunks'][0]
        except: pass
        
        maxbitrate=0
        try:
            maxbitrate = int(params['maxbitrate'][0])
        except: pass

        if proxy=='None' or proxy=='':
            proxy=None
        if use_proxy_for_chunks=='False':
            use_proxy_for_chunks=False
        
        return (received_url,proxy,use_proxy_for_chunks,maxbitrate)

    def decode_videoparturl(self, url):
        print 'in params', url
        params = urlparse.parse_qs(url)
        received_url = params['url'][0].replace('\r', '')
        return received_url


"""
Sends the requested file and add additional headers.
"""
class Server(HTTPServer):
    """HTTPServer class with timeout."""
 
    def get_request(self):
        print "Server(HTTPServer): Serving GET request..."
        global g_stopEvent

        """Get the request and client address from the socket."""
        self.socket.settimeout(5.0)
        result = None
        while result is None:
            try:
                if g_stopEvent and g_stopEvent.isSet():
                    return None

                result = self.socket.accept()
            except socket.timeout:
                pass
        result[0].settimeout(1000)
        return result


class ThreadedHTTPServer(ThreadingMixIn, Server):
    """Handle requests in a separate thread."""
    # def __init__(self):
    #     ThreadingMixIn.daemon_threads = True


class hlsProxy():

    @property
    def stopEvent(self):
        return self.stopPlaying

    def __init__(self):
        self.stopPlaying = None
        pass

    def __start(self, stopEvent, player, port=PORT_NUMBER):
        global PORT_NUMBER
        global HOST_NAME
        global g_stopEvent

        g_stopEvent = stopEvent

        socket.setdefaulttimeout(10)

        ProxyHandler.protocol_version = "HTTP/1.1"
        ProxyHandler.downloader = player()

        httpd = None
        try:
            ThreadedHTTPServer.daemon_threads = True
            httpd = ThreadedHTTPServer((HOST_NAME, port), ProxyHandler)

            log("XBMCLocalProxy Starts - %s:%s" % (HOST_NAME, port))
            while not stopEvent.isSet():
                httpd.handle_request()
        finally:
            try:
                if httpd:
                    httpd.server_close()
                    httpd.shutdown()
            finally:
                log("XBMCLocalProxy Stops %s:%s" % (HOST_NAME, port))

    def __prepare_url(self, url, proxy=None, use_proxy_for_chunks=True, port=PORT_NUMBER, maxbitrate=0):
        global PORT_NUMBER
        newurl=urllib.urlencode({'url': url,'proxy': proxy,'use_proxy_for_chunks': use_proxy_for_chunks,'maxbitrate': maxbitrate})
        link = 'http://%s:%s/brplay?%s' % (HOST_NAME, str(port), newurl)
        return (link) #make a url that caller then call load into player

    def resolve(self, url, proxy=None, use_proxy_for_chunks=True, maxbitrate=0, player=None):

        self.stopPlaying=threading.Event()
        progress = xbmcgui.DialogProgress()

        progress.create('Starting local proxy')
        progress.update(20, "", 'Loading local proxy', "")

        self.stopPlaying.clear()
        thread.start_new_thread(self.__start, (self.stopPlaying, player,))

        url_to_play = self.__prepare_url(url, proxy, use_proxy_for_chunks, maxbitrate=maxbitrate)

        xbmc.sleep(500)

        progress.update(100, "", "", "")
        progress.close()

        return url_to_play, player.MAIN_MIME_TYPE