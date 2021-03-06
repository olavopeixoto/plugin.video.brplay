# -*- coding: utf-8 -*-

import http.cookiejar as cookielib
import os
import traceback
import urllib.parse as urlparse

import requests
import copy
from resources.lib.modules import control
from resources.lib.modules import m3u8 as m3u8

try:
    import xbmc
    is_standalone = False
except:
    is_standalone = True


class SimpleHLSWriter:

    MAIN_MIME_TYPE = 'application/vnd.apple.mpegurl'

    """
    A downloader for hls manifests
    """
    def __init__(self):
        self.enable_log = control.log_enabled

        self.cookieJar = cookielib.LWPCookieJar()
        self.session = None
        self.clientHeader = None
        self.manifest_playlist = None
        self.original_media_list = None
        self.selected_bandwidth_index = None
        self.use_proxy = False
        self.proxy = None
        self.g_stopEvent = None
        self.maxbitrate = 0
        self.url = None
        self.key = None

    def log(self, msg):
        if self.enable_log:
            if is_standalone:
                print(msg)
            else:
                import threading
                control.log("%s - %s" % (threading.currentThread(), msg))

    def log_error(self, msg):
        if is_standalone:
            print(msg)
        else:
            control.log(msg)

    def init(self, out_stream, url, proxy=None, stopEvent=None, maxbitrate=0):
        try:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            self.session = requests.Session()
            self.session.cookies = self.cookieJar
            self.clientHeader = None
            self.proxy = proxy

            if self.proxy and len(self.proxy) == 0:
                self.proxy = None

            self.use_proxy = False

            if stopEvent:
                stopEvent.clear()

            self.g_stopEvent = stopEvent
            self.maxbitrate = maxbitrate

            if '|' in url:
                sp = url.split('|')
                url = sp[0]
                self.clientHeader = sp[1]
                self.log(self.clientHeader)
                self.clientHeader = urlparse.parse_qsl(self.clientHeader)
                self.log('header received now url and headers are %s | %s' % (url, self.clientHeader))

            self.url = url

            return True
        except:
            traceback.print_exc()

        return False

    def keep_sending_video(self, dest_stream):
        try:
            self.download_main_playlist(self.url, dest_stream, self.g_stopEvent, self.maxbitrate)
        except Exception as e:
            self.log('ERROR SENDING MAIN PLAYLIST: %s' % e.message)
            traceback.print_exc()

    def download_main_playlist(self, url, stream, stop_event=None, max_bitrate=0):
        if stop_event and stop_event.isSet():
            return

        self.log("STARTING MAIN PLAYLIST DOWNLOAD. URI: %s" % url)

        # load main m3u8 playlist
        self.manifest_playlist = self.__load_playlist_from_uri(url)

        playlist = self.manifest_playlist

        playlist_response = playlist.dumps()
        self.log("SENDING MAIN PLAYLIST: %s" % playlist_response)

        self.__send_back(playlist_response, stream)

    def download_segment_playlist(self, uri, base_uri, stream, stop_event=None):

        self.log("STARTING SEGMENT PLAYLIST DOWNLOAD. URI: %s" % uri)

        if stop_event and stop_event.isSet():
            self.log("stop_event received")
            return

        absolute_uri = self.manifest_playlist.base_uri + uri

        self.log("REQUESTED SEGMENT PLAYLIST ABSOLUTE URI: %s" % absolute_uri)

        media_list = self.__load_playlist_from_uri(absolute_uri)

        self.original_media_list = copy.deepcopy(media_list)

        # replace original url with proxy's url so Kodi requests to proxy player instead of media origin
        self.original_media_list.base_uri = base_uri
        for segment in self.original_media_list.segments:
            segment.base_uri = base_uri
            parsed_url = urlparse.urlparse(segment.uri)
            segment.uri = parsed_url.path

        media_playlist_response = self.original_media_list.dumps()

        self.log("SENDING MEDIA PLAYLIST: %s" % media_playlist_response)

        self.__send_back(media_playlist_response, stream)

    def download_binary(self, url, dest_stream):

        self.log('DOWNLOADING BINARY URI: %s' % url)

        while not self.original_media_list or not self.original_media_list.keys:
            xbmc.sleep(100)
            if self.g_stopEvent and self.g_stopEvent.isSet():
                return

        file = url.split('/')[-1]
        keys = filter(lambda k: k.uri.split('/')[-1] == file, self.original_media_list.keys)

        retry = 20

        while len(keys) <= 0 < retry:
            xbmc.sleep(50)
            if self.g_stopEvent and self.g_stopEvent.isSet():
                return
            keys = filter(lambda k: k.uri.split('/')[-1] == file, self.original_media_list.keys)
            retry = retry - 1

        if len(keys) <= 0:
            self.log("ERROR: KEY NOT FOUND: %s | PLAYLIST: %s" % (file, self.original_media_list.dumps()))
            raise Exception("KEY NOT FOUND: %s" % file)

        self.key = keys[0]
        absolute_uri = self.key.absolute_uri

        self.log('DOWNLOADING BINARY ABSOLUTE URI: %s' % absolute_uri)

        for chunk in self.__download_chunks(absolute_uri):
            self.__send_back(chunk, dest_stream)

    def download_segment_media(self, segment_uri, stream):

        self.log("REQUESTED MEDIA: %s" % segment_uri)

        if self.g_stopEvent and self.g_stopEvent.isSet():
            return

        parsed_url = urlparse.urlparse(segment_uri)
        parsed_segment_uri = parsed_url.path

        dummy_segment = self.original_media_list.segments[0]

        segment_parsed_url = urlparse.urlparse(dummy_segment.uri)
        segment_base_uri = segment_parsed_url.scheme + '://' + segment_parsed_url.netloc if segment_parsed_url.scheme else self.manifest_playlist.base_uri

        absolute_uri = segment_base_uri + parsed_segment_uri

        self.log("REQUESTED MEDIA URI: %s | DOWNLOADING MEDIA URI: %s" % (segment_uri, absolute_uri))

        for chunk in self.__download_chunks(absolute_uri):
            if self.g_stopEvent.isSet():
                stream.flush()
                return

            stream.write(chunk)

        stream.flush()

    def __get_url(self, url, timeout=15, return_response=False, stream=False):
        self.log("GET URL: %s" % url)
        self.log("GET URL Cookies: %s" % self.cookieJar.as_lwp_str())

        try:
            post = None

            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

            if self.clientHeader:
                for n,v in self.clientHeader:
                    headers[n]=v

            proxies = {}

            if self.use_proxy and self.proxy:
                self.log("DOWNLOADING WITH PROXY: %s" % self.proxy)
                proxies={"http": self.proxy, "https": self.proxy}

            if post:
                response = self.session.post(url, headers=headers, data=post, proxies=proxies, verify=False, timeout=timeout, stream=stream)
            else:
                response = self.session.get(url, headers=headers, proxies=proxies, verify=False, timeout=timeout, stream=stream)

            # IF 403 RETRY WITH PROXY
            if not self.use_proxy and self.proxy and response.status_code == 403:
                self.log("RETRYING WITH PROXY DUE TO 403: %s" % self.proxy)
                proxies= {"http": self.proxy, "https": self.proxy}
                self.use_proxy = True
                if post:
                    response = self.session.post(url, headers=headers, data=post, proxies=proxies, verify=False, timeout=timeout, stream=stream)
                else:
                    response = self.session.get(url, headers=headers, proxies=proxies, verify=False, timeout=timeout, stream=stream)

            response.raise_for_status()

            if return_response:
                return response
            else:
                return response.content
        except:
            self.log("ERROR GET URL: %s" % url)
            traceback.print_exc()
            return None

    def __download_chunks(self, URL, chunk_size=65536):
        response = self.__get_url(URL, timeout=6, return_response=True, stream=True)

        for chunk in response.iter_content(chunk_size=chunk_size):
            yield chunk

    def __send_back(self, data, stream):
        stream.write(data)
        stream.flush()

    def __load_playlist_from_uri(self, uri):
        response = self.__get_url(uri, return_response=True)
        content = response.content.strip()
        self.log("PLAYLIST: %s" % content)
        parsed_url = urlparse.urlparse(uri)
        prefix = parsed_url.scheme + '://' + parsed_url.netloc
        base_path = os.path.normpath(parsed_url.path + '/..')
        base_uri = urlparse.urljoin(prefix, base_path)

        return m3u8.M3U8(content, base_uri=base_uri)
