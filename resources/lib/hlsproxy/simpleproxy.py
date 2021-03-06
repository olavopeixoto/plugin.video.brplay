# -*- coding: utf-8 -*-

import re
import socket
import os
from urllib.parse import quote_plus, unquote_plus, urlparse, urljoin
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
import requests
from resources.lib.modules import control

HOST_NAME = '127.0.0.1'
PROXY_PORT = 55444
PROXY_URL_FORMAT = 'http://%s:%s/proxy.%%s?url=%%s' % (HOST_NAME, PROXY_PORT)

session = requests.Session()
BASE_URL = None


def log(msg):
    # pass
    control.log(msg)


class RequestHandler(BaseHTTPRequestHandler):
    proxy = None

    def __init__(self, request, client_address, server):
        self.proxy = None if not RequestHandler.proxy else {
            'http': RequestHandler.proxy,
            'https': RequestHandler.proxy,
        }
        self.uri_search = re.compile(r'URI="([^"]+)"')
        self.https_match = re.compile(r'https?://')
        self.base_url_match = re.compile(r'<BaseURL>([^<]+)</BaseURL>')
        self.proxy_match = re.compile(r'(/proxy(?:\.(\w+))?)\?url=(.*)')
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    """
    Serves a HEAD request
    """
    def do_HEAD(self):
        log("Simple Proxy: HEAD %s" % self.path)
        self.send_response(200)
        self.send_header("Content-Type", 'application/vnd.apple.mpegurl')  # todo: dynamic mime type
        self.end_headers()

    """
    Serves a GET request.
    """
    def do_GET(self):
        global BASE_URL

        log("Simple Proxy: GET %s" % self.path)

        match = self.proxy_match.search(self.path)

        if match:
            # extension = match.group(2)
            media_url = unquote_plus(match.group(3))
        else:
            media_url = urljoin(BASE_URL, self.path[1:])

        headers = dict((k.lower(), v) for k, v in self.headers.items())

        if 'host' in headers:
            del headers['host']
        if 'cookie' in headers:
            del headers['cookie']
        if 'origin' in headers:
            del headers['origin']

        log('GET %s' % media_url)
        log(headers)

        response = session.get(media_url, headers=headers, proxies=self.proxy)

        log('RESPONSE: %s' % response.status_code)

        log(response.headers)

        self.send_response(response.status_code)

        self.send_header('Content-Type', response.headers['Content-Type'])

        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')

        if response.text:
            content = response.text
            if response.url.split('?')[0].endswith('.m3u8') and 200 <= response.status_code < 300:
                # print 'M3U8 CONTENT'
                line_buffer = []
                for line in content.splitlines():
                    res = self.uri_search.search(line)
                    if res:
                        content_url = res.group(1)
                        new_url = content_url

                        if not self.https_match.match(new_url):
                            new_url = urljoin(response.url, new_url)

                        path = urlparse(new_url).path
                        ext = os.path.splitext(path)[1] or 'm3u8'
                        ext = ext.replace('.', '')

                        # new_url = proxy_url.format(url=urllib.quote_plus(new_url))
                        new_url = PROXY_URL_FORMAT % (ext, quote_plus(new_url))

                        content_url = line.replace(content_url, new_url)
                        line_buffer.append(content_url)
                        # print content_url

                    elif line != "" and not line.startswith('#'):
                        line = urljoin(response.url, line)
                        # content_url = proxy_url.format(url=urllib.quote_plus(line))

                        path = urlparse(line).path
                        ext = os.path.splitext(path)[1] or 'm3u8'
                        ext = ext.replace('.', '')

                        content_url = PROXY_URL_FORMAT % (ext, quote_plus(line))
                        line_buffer.append(content_url)
                        # print content_url
                    else:
                        line_buffer.append(line)
                        # print line

                content = '\n'.join(line_buffer)

                log('CONTENT: %s' % content)

                content = content.encode('utf-8')

            elif '.mpd' in response.url.split('?')[0] and 200 <= response.status_code < 300:
                BASE_URL = response.url

                result = self.base_url_match.search(response.text)

                if result:
                    base_url = result.group(1)

                    new_url = urljoin(response.url, base_url)

                    path = urlparse(new_url).path
                    ext = os.path.splitext(path)[1] or 'mpd'
                    ext = ext.replace('.', '')

                    new_base_url = PROXY_URL_FORMAT % (ext, quote_plus(new_url))
                    content = self.base_url_match.sub(r'<BaseURL>' + new_base_url + r'</BaseURL>', response.text)

                log('CONTENT: %s' % content)

                content = content.encode('utf-8')

            else:
                log('CONTENT: binary')
                content = response.content

            self.send_header('Content-Length', str(len(content)))
            self.end_headers()

            self.wfile.write(content)
            self.wfile.flush()

            # print 'CLOSE FILE'
            # self.wfile.close()

        else:
            self.end_headers()


class Server(HTTPServer):
    def __init__(self, server_address, request_handler_class, stop_event):
        self.stop_event = stop_event
        HTTPServer.__init__(self, server_address, request_handler_class)

    """
    Sends the requested file and add additional headers.
    """
    """HTTPServer class with timeout."""
    def get_request(self):
        log("Server(HTTPServer): Serving GET request...")

        """Get the request and client address from the socket."""
        self.socket.settimeout(5.0)
        result = None
        while result is None:
            try:
                if self.stop_event.isSet():
                    return None

                result = self.socket.accept()
            except socket.timeout:
                pass
        result[0].settimeout(5000)
        return result


class ThreadedHTTPServer(ThreadingMixIn, Server, object):

    def __init__(self, server_address, request_handler_class, stop_event):
        super(ThreadedHTTPServer, self).__init__(server_address, request_handler_class, stop_event)

    """Handle requests in a separate thread."""
    daemon_threads = True

    # def handle_error(self, request, client_address):
    #     # suppress socket/ssl related errors
    #     cls, e = sys.exc_info()[:2]
    #     if cls is socket.error or cls is ssl.SSLError:
    #         pass
    #     else:
    #         return Server.handle_error(self, request, client_address)


class MediaProxy:

    @property
    def stop_event(self):
        return self.stopPlaying

    def __init__(self, proxy=None):
        log('MediaProxy Init | proxy: %s' % proxy)
        self.host_name = HOST_NAME
        self.port = PROXY_PORT

        self.stopPlaying = threading.Event()
        self.stopPlaying.clear()

        t = threading.Thread(target=self.__start, args=(self.stopPlaying, proxy,))
        t.daemon = True
        t.start()

    def __start(self, stop_event, proxy):
        log('MediaProxy Start')
        socket.setdefaulttimeout(10)

        RequestHandler.protocol_version = "HTTP/1.1"
        RequestHandler.proxy = proxy

        httpd = None
        try:
            ThreadedHTTPServer.daemon_threads = True
            httpd = ThreadedHTTPServer((self.host_name, self.port, ), RequestHandler, stop_event)

            log("Simple Proxy Started - %s:%s" % (self.host_name, self.port))

            while not stop_event.isSet():
                httpd.handle_request()
        finally:
            try:
                if httpd:
                    httpd.server_close()
            finally:
                log("Simple Proxy Stopped %s:%s" % (self.host_name, self.port))

    def resolve(self, url):

        log('MediaProxy resolve: %s' % url)

        path = urlparse(url).path
        extension = os.path.splitext(path)[1] or 'm3u8'
        extension = extension.replace('.', '')

        link = PROXY_URL_FORMAT % (extension, quote_plus(url))

        return link  # make a url that caller then call load into player
