"""
XBMCLocalProxy 0.1
Copyright 2011 Torben Gerkensmeyer

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

import base64
import re
import time
import urllib
import sys
import traceback
import socket
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urllib import *


class MyHandler(BaseHTTPRequestHandler):
    """
    Serves a HEAD request
    """

    def do_HEAD(s):
        print "XBMCLocalProxy: Serving HEAD request..."
        s.answer_request(0)

    """
    Serves a GET request.
    """

    def do_GET(s):
        print "XBMCLocalProxy: Serving GET request..."
        s.answer_request(1)

    def answer_request(s, sendData):
        try:
            request_path = s.path[1:]
            request_path = re.sub(r"\?.*", "", request_path)
            if request_path == "stop":
                sys.exit()
            elif request_path == "version":
                s.send_response(200)
                s.end_headers()
                s.wfile.write("Proxy: Running\r\n")
                s.wfile.write("Version: 0.1")
            elif request_path[0:12] == "withheaders/":
                (realpath, sep, additionalheaders) = request_path[12:].partition("/")
                fURL = base64.b64decode(realpath)
                additionalhString = base64.b64decode(additionalheaders)
                s.serveFile(fURL, additionalhString, sendData)
            else:
                s.send_response(403)
        except:
            traceback.print_exc()
            s.wfile.close()
            return
        try:
            s.wfile.close()
        except:
            pass

    """
    Sends the requested file and add additional headers.
    """

    def serveFile(s, fURL, additionalhstring, sendData):
        additionalh = s.decodeHeaderString(additionalhstring)
        opener = FancyURLopener()
        opener.addheaders = []
        d = {}
        sheaders = s.decodeHeaderString("".join(s.headers.headers))
        for key in sheaders:
            d[key] = sheaders[key]
            if (key != "Host"): opener.addheader(key, sheaders[key])
        for key in additionalh:
            d[key] = additionalh[key]
            opener.addheader(key, additionalh[key])
        response = opener.open(fURL)
        s.send_response(response.code)
        print "XBMCLocalProxy: Sending headers..."
        headers = response.info()
        for key in headers:
            try:
                val = headers[key]
                s.send_header(key, val)
            except Exception, e:
                print e
                pass
        s.end_headers()

        if (sendData):
            print "XBMCLocalProxy: Sending data..."
            fileout = s.wfile
            try:
                buf = "INIT"
                try:
                    while (buf != None and len(buf) > 0):
                        buf = response.read(8 * 1024)
                        fileout.write(buf)
                        fileout.flush()
                    response.close()
                    fileout.close()
                    print time.asctime(), "Closing connection"
                except socket.error, e:
                    print time.asctime(), "Client Closed the connection."
                    try:
                        response.close()
                        fileout.close()
                    except Exception, e:
                        return
                except Exception, e:
                    traceback.print_exc(file=sys.stdout)
                    response.close()
                    fileout.close()
            except:
                traceback.print_exc()
                s.wfile.close()
                return
        try:
            s.wfile.close()
        except:
            pass

    def decodeHeaderString(self, hs):
        di = {}
        hss = hs.replace("\r", "").split("\n")
        for line in hss:
            u = line.split(": ")
            try:
                di[u[0]] = u[1]
            except:
                pass
        return di


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


HOST_NAME = '127.0.0.1'
PORT_NUMBER = 64653

if __name__ == '__main__':
    socket.setdefaulttimeout(10)
    server_class = ThreadedHTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print "XBMCLocalProxy Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    while (True):
        httpd.handle_request()
    httpd.server_close()
    print "XBMCLocalProxy Stops %s:%s" % (HOST_NAME, PORT_NUMBER)