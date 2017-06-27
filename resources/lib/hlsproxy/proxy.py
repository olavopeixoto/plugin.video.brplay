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

import hashlib
import re
import socket
import sys
import traceback
import urllib
import urlparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn

import xbmc

g_stopEvent=None
g_downloader=None
g_currentprocessor=None
MIME_TYPE = 'video/MP2T'

HOST_NAME = '127.0.0.1'
PORT_NUMBER = 55444

class ProxyHandler(BaseHTTPRequestHandler):
    """
   Serves a HEAD request
   """
    def do_HEAD(self):
        print "XBMCLocalProxy: Serving HEAD request..."
        #
        self.send_response(200)
        #self.send_header("Accept-Ranges","bytes")
        self.send_header("Content-Type", MIME_TYPE)
        self.end_headers()
        #s.answer_request(False)

    """
    Serves a GET request.
    """
    def do_GET(s):
        print "XBMCLocalProxy: Serving GET request..."
        s.answer_request(True)
 
    def answer_request(self, sendData):
        global g_stopEvent
        global g_downloader
        global g_currentprocessor

        try:
            #Pull apart request path
            request_path=self.path[1:] 
            querystring=request_path            
            request_path=re.sub(r"\?.*","",request_path)
            
            #If a request to stop is sent, shut down the proxy

            if request_path.lower()=="stop":# all special web interfaces here
                sys.exit()
                return
            if request_path.lower()=="favicon.ico":
                print 'dont have no icon here, may be in future'
                self.wfile.close()
                return
            if request_path.lower()=="sendvideopart":
                print 'sendvideopart'
                #sendvideoparthere
                self.send_response(200)
                self.send_header("Content-Type", MIME_TYPE)
                self.end_headers()
                init_done=True
                videourl=self.decode_videoparturl(querystring.split('?')[1])
                g_currentprocessor.sendVideoPart(videourl,self.wfile)
                return

            init_done=False
            (url,proxy,use_proxy_for_chunks,maxbitrate)=self.decode_url(request_path)

            from hlsdownloader import HLSDownloader
            downloader=HLSDownloader()
            if not downloader.init(self.wfile, url, proxy, use_proxy_for_chunks, g_stopEvent, maxbitrate):
                print 'cannot init'
                raise Exception('HLS.url failed to play\nServer down? check Url.')

            self.send_response(200)
            self.send_header("Content-Type", MIME_TYPE)
            self.end_headers()

            init_done=True
            srange,framgementToSend=(None,None)

            if sendData:
                downloader.keep_sending_video(self.wfile, srange, framgementToSend)
                #self.wfile.close()
                #runningthread=thread.start_new_thread(downloader.download,(self.wfile,url,proxy,use_proxy_for_chunks,))
                print 'srange,framgementToSend',srange,framgementToSend
                #runningthread=thread.start_new_thread(downloader.keep_sending_video,(self.wfile,srange,framgementToSend,))
                
                #xbmc.sleep(500)
                #while not downloader.status=="finished":
                #    xbmc.sleep(200);

        except Exception as inst:
            #Print out a stack trace
            traceback.print_exc()
            #g_stopEvent.set()
            if not init_done:
                xbmc.executebuiltin("XBMC.Notification(BRPlayProxy,%s,4000,'')" % inst.message)
                self.send_error(404)
            #print 'sending 404'
            #self.send_error(404)
            #Close output stream file
            #self.wfile.close()
            print 'closed'
            
        #Close output stream file
        #self.wfile.close()
        self.finish()
        return 
   
    def generate_ETag(self, url):
        md=hashlib.md5()
        md.update(url)
        return md.hexdigest()
        
    def get_range_request(self, hrange, file_size):
        if hrange==None:
            srange=0
            erange=None
        else:
            try:
                #Get the byte value from the request string.
                hrange=str(hrange)
                splitRange=hrange.split("=")[1].split("-")
                srange=int(splitRange[0])
                erange = splitRange[1]
                if erange=="":
                    erange=int(file_size)-1
                #Build range string
                
            except:
                # Failure to build range string? Create a 0- range.
                srange=0
                erange=int(file_size-1);
        return (srange, erange)

    def decode_videoparturl(self, url):
        print 'in params',url
        params=urlparse.parse_qs(url)
        received_url = params['url'][0].replace('\r','')
        return received_url
        
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


"""
Sends the requested file and add additional headers.
"""
class Server(HTTPServer):
    """HTTPServer class with timeout."""
 
    def get_request(self):
        """Get the request and client address from the socket."""
        self.socket.settimeout(5.0)
        result = None
        while result is None:
            try:
                result = self.socket.accept()
            except socket.timeout:
                pass
        result[0].settimeout(1000)
        return result


class ThreadedHTTPServer(ThreadingMixIn, Server):
    """Handle requests in a separate thread."""
 

class hlsProxy():

    def __init__(self):
        pass

    def start(self,stopEvent,port=PORT_NUMBER):
        global PORT_NUMBER
        global HOST_NAME
        global g_stopEvent
        print 'port',port,'HOST_NAME',HOST_NAME
        g_stopEvent = stopEvent
        socket.setdefaulttimeout(10)
        server_class = ThreadedHTTPServer
        #MyHandler.protocol_version = "HTTP/1.1"
        ProxyHandler.protocol_version = "HTTP/1.1"

        try:
            httpd = server_class((HOST_NAME, port), ProxyHandler)

            print "XBMCLocalProxy Starts - %s:%s" % (HOST_NAME, port)
            while(True and not stopEvent.isSet()):
                httpd.handle_request()
        finally:
            if httpd:
                httpd.server_close()

        print "XBMCLocalProxy Stops %s:%s" % (HOST_NAME, port)

    def prepare_url(self,url, proxy=None, use_proxy_for_chunks=True, port=PORT_NUMBER, maxbitrate=0):
        global PORT_NUMBER
        newurl=urllib.urlencode({'url': url,'proxy':proxy,'use_proxy_for_chunks':use_proxy_for_chunks,'maxbitrate':maxbitrate})
        link = 'http://'+HOST_NAME+(':%s/' % str(port)) + newurl
        return (link) #make a url that caller then call load into player


class MyPlayer(xbmc.Player):
    def __init__ (self):
        xbmc.Player.__init__(self)

    def play(self, url, listitem):
        print 'Now im playing... %s' % url
        self.stopPlaying.clear()
        xbmc.Player( ).play(url, listitem)
        
    def onPlayBackEnded( self ):
        # Will be called when xbmc stops playing a file
        print "seting event in onPlayBackEnded " 
        self.stopPlaying.set();
        print "stop Event is SET"

    def onPlayBackStopped( self ):
        # Will be called when user stops xbmc playing a file
        print "seting event in onPlayBackStopped " 
        self.stopPlaying.set();
        print "stop Event is SET"