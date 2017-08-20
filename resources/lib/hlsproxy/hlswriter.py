# -*- coding: utf-8 -*-

import cookielib
import os
import traceback
import urlparse
import time

import requests
import datetime
import copy
from resources.lib.modules import util
from resources.lib.modules import control
from resources.lib.modules import m3u8 as m3u8

import Queue
from resources.lib.modules import workers

try:
    import xbmc
    is_standalone = False
except:
    is_standalone = True


def log(msg):
    # pass
    if is_standalone:
        print msg
    else:
        xbmc.log(msg,level=xbmc.LOGNOTICE)


class HLSWriter():

    MAIN_MIME_TYPE = 'application/vnd.apple.mpegurl'
    DOWNLOAD_IN_BACKGROUND = False

    """
    A downloader for hls manifests
    """
    def __init__(self):
        self.cookieJar = cookielib.LWPCookieJar()
        self.session = None
        self.clientHeader = None
        self.average_download_speed = 0.0
        self.manifest_playlist = None
        self.media_list = None
        self.selected_bandwidth_index = None
        self.use_proxy = False
        self.proxy = None
        self.g_stopEvent = None
        self.maxbitrate = 0
        self.url = None
        self.media_buffer = {}
        self.requested_segment = None
        self.key = None

    def init(self, out_stream, url, proxy=None, stopEvent=None, maxbitrate=0):

        try:
            self.session = requests.Session()
            self.session.cookies = self.cookieJar
            self.clientHeader=None
            self.proxy = proxy

            if self.proxy and len(self.proxy)==0:
                self.proxy=None

            self.use_proxy = False

            if stopEvent: stopEvent.clear()

            self.g_stopEvent=stopEvent
            self.maxbitrate=maxbitrate

            if '|' in url:
                sp = url.split('|')
                url = sp[0]
                self.clientHeader = sp[1]
                log( self.clientHeader )
                self.clientHeader= urlparse.parse_qsl(self.clientHeader)
                log ('header received now url and headers are %s | %s' % (url, self.clientHeader))

            self.url=url

            if self.DOWNLOAD_IN_BACKGROUND:
                worker = workers.Thread(self.load_buffer)
                worker.daemon = True
                worker.start()

            return True
        except:
            traceback.print_exc()

        return False

    def load_buffer(self):
        decay = 0.90  # must be between 0 and 1 see: https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average

        log("STARTING BUFFER LOADER...")

        while self.manifest_playlist is None or not self.requested_segment:
            if self.g_stopEvent.isSet():
                log("QUITTING BUFFER LOADER...")
                return
            log("WAITING FOR HLS PLAYLIST...")
            xbmc.sleep(100)

        log("BUFFERED MODE - STARTING MEDIA DOWNLOAD WITH AVERAGE SPEED: %s" % self.average_download_speed)

        while not self.g_stopEvent.isSet():

            playlist = self.manifest_playlist.playlists[self.selected_bandwidth_index] if self.manifest_playlist.is_variant else self.manifest_playlist

            log("BUFFERED MODE - LOADING PLAYLIST: %s" % playlist.absolute_uri)

            media_list = self.load_playlist_from_uri(playlist.absolute_uri)

            log("BUFFERED MODE - LOADING %s SEGMENT(S)" % len(media_list.segments))

            # self.__download_segments_sequentially(media_list.segments)
            self.__download_segments_parallel(media_list.segments)

    def __download_segments_sequentially(self, segments):
        for segment in segments:

            if self.g_stopEvent.isSet():
                return

            segment_number = self.get_segment_number(segment.absolute_uri)

            if str(segment_number) in self.media_buffer or int(self.requested_segment) > int(segment_number):
                log("SKIPPING SEGMENT %s" % segment_number)
                continue

            start = datetime.datetime.now()
            segment_size = 0.0
            segment_data = []
            for chunk in self.download_chunks(segment.absolute_uri):
                if self.g_stopEvent.isSet():
                    return

                segment_size += len(chunk)
                segment_data.append(chunk)

            log("SEGMENT %s READY!" % segment_number)

            self.media_buffer[str(segment_number)] = b''.join(segment_data)

        stop = datetime.datetime.now()

        worker = workers.Thread(self.__calculate_bitrate, start, stop, segment_size, segment.duration)
        worker.daemon = True
        worker.start()

    def __download_segments_parallel(self, segments):
        threads = []
        for segment in segments:

            if self.g_stopEvent.isSet():
                return

            segment_number = self.get_segment_number(segment.absolute_uri)

            if str(segment_number) in self.media_buffer or int(self.requested_segment) > int(segment_number):
                log("SKIPPING SEGMENT %s" % segment_number)
                continue

            worker = workers.Thread(self.__download_single_segment, segment)
            worker.daemon = True
            threads.append(worker)

        [i.start() for i in threads]
        [i.join() for i in threads]

    def __download_single_segment(self, segment):
        if self.g_stopEvent.isSet():
            return

        segment_number = self.get_segment_number(segment.absolute_uri)

        if str(segment_number) in self.media_buffer or int(self.requested_segment) > int(segment_number):
            log("SKIPPING SEGMENT %s" % segment_number)
            return

        start = datetime.datetime.now()
        segment_size = 0.0
        segment_data = []
        for chunk in self.download_chunks(segment.absolute_uri):
            if self.g_stopEvent.isSet():
                return

            segment_size += len(chunk)
            segment_data.append(chunk)

        log("SEGMENT %s READY!" % segment_number)

        self.media_buffer[str(segment_number)] = b''.join(segment_data)

        stop = datetime.datetime.now()

        worker = workers.Thread(self.__calculate_bitrate, start, stop, segment_size, segment.duration)
        worker.daemon = True
        worker.start()

    def download_binary(self, url, dest_stream):

        log('DOWNLOADING BINARY URI: %s' % url)

        current_bandwidth_index = self.find_bandwidth_index(self.manifest_playlist,
                                                            min(self.maxbitrate, self.average_download_speed))
        self.selected_bandwidth_index = current_bandwidth_index
        playlist = self.manifest_playlist.playlists[self.selected_bandwidth_index]
        self.media_list = self.load_playlist_from_uri(playlist.absolute_uri)

        file = url.split('/')[-1]
        keys = filter(lambda k: k.uri.split('/')[-1] == file, self.media_list.keys)

        if len(keys) <= 0:
            log("ERROR: KEY NOT FOUND: %s | PLAYLIST: %s" % (file, self.media_list.dumps()))
            raise Exception("KEY NOT FOUND: %s" % file)

        self.key = keys[0]
        absolute_uri = self.key.absolute_uri

        log('DOWNLOADING BINARY ABSOLUTE URI: %s' % absolute_uri)

        for chunk in self.download_chunks(absolute_uri):
            self.send_back(chunk, dest_stream)

    def keep_sending_video(self, dest_stream):
        try:
            self.average_download_speed = float(control.setting('average_download_speed')) if control.setting('average_download_speed') else 0.0
            self.download_main_playlist(self.url, dest_stream, self.g_stopEvent, self.maxbitrate)
            control.setSetting('average_download_speed', str(self.average_download_speed))
        except Exception, e:
            log('ERROR SENDING MAIN PLAYLIST: %s' % e.message)
            traceback.print_exc()
        
    def get_url(self, url, timeout=15, return_response=False, stream=False):
        log("GET URL: %s" % url)
        log("GET URL Cookies: %s" % self.cookieJar.as_lwp_str())

        try:
            post=None

            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

            if self.clientHeader:
                for n,v in self.clientHeader:
                    headers[n]=v

            proxies = {}

            if self.use_proxy and self.proxy:
                proxies={"http": self.proxy, "https": self.proxy}

            if post:
                response = self.session.post(url, headers=headers, data=post, proxies=proxies, verify=False, timeout=timeout, stream=stream)
            else:
                response = self.session.get(url, headers=headers, proxies=proxies, verify=False, timeout=timeout, stream=stream)

            #IF 403 RETRY WITH PROXY
            if not self.use_proxy and self.proxy and response.status_code == 403:
                proxies= {"http": self.proxy, "https": self.proxy}
                use_proxy = True
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
            traceback.print_exc()
            return None

    def download_chunks(self, URL, chunk_size=65536):
        response=self.get_url(URL, timeout=6, return_response=True, stream=True)

        for chunk in response.iter_content(chunk_size=chunk_size):
            yield chunk

    def send_back(self, data, stream):
        stream.write(data)
        stream.flush()

    def load_playlist_from_uri(self, uri):
        response = self.get_url(uri, return_response=True)
        content = response.content.strip()
        log("PLAYLIST: %s" % content)
        parsed_url = urlparse.urlparse(uri)
        prefix = parsed_url.scheme + '://' + parsed_url.netloc
        base_path = os.path.normpath(parsed_url.path + '/..')
        base_uri = urlparse.urljoin(prefix, base_path)

        return m3u8.M3U8(content, base_uri=base_uri)

    def find_bandwidth_index(self, playlist, average_download_speed, safe_ratio=1.0):
        if not playlist.is_variant:
            return 0

        bandwidth_options = []
        for index, playlist_item in enumerate(playlist.playlists):
            bandwidth_options.append({
                'index': index,
                'bandwidth': float(playlist.playlists[index].stream_info.bandwidth)
            })
        bandwidth_options = sorted(bandwidth_options, key=lambda k: int(k['bandwidth']), reverse=True)

        for bandwidth_option in bandwidth_options:
            if bandwidth_option['bandwidth'] * safe_ratio < average_download_speed:
                log("SELECTED BANDWIDTH: %s" % bandwidth_option['bandwidth'])
                return bandwidth_option['index']

        return 0

    def get_segment_number(self, segment_uri):
        return segment_uri.split('-')[-1:][0].split('.')[0]

    def download_segment_media_from_buffer(self, segment_uri, stream):
        if self.g_stopEvent and self.g_stopEvent.isSet():
            return

        segment_number = self.get_segment_number(segment_uri)

        self.requested_segment = segment_number

        if str(segment_number) not in self.media_buffer:
            self.average_download_speed = 0
            log("SEGMENT %s NOT READY..." % str(segment_number))
            return False

        log("LOADING SEGMENT %s FROM BUFFER! :-)" % str(segment_number))

        segment_bytes = self.media_buffer[str(segment_number)]

        self.media_buffer[str(segment_number)] = None

        self.send_back(segment_bytes, stream)

        return True

    def download_segment_media(self, segment_uri, stream):
        if self.g_stopEvent and self.g_stopEvent.isSet():
            return

        if self.DOWNLOAD_IN_BACKGROUND and self.download_segment_media_from_buffer(segment_uri, stream):
            return

        log ("STARTING MEDIA DOWNLOAD (%s) WITH AVERAGE SPEED: %s" % (segment_uri, self.average_download_speed))

        segment_size = 0.0

        segment_number = self.get_segment_number(segment_uri)

        log("SEGMENT NUMBER: %s" % segment_number)

        segment_result_list = filter(lambda k: self.get_segment_number(k.uri) == segment_number, self.media_list.segments)

        if len(segment_result_list) == 0:
            log("SEGMENT NOT FOUND!!! Requested URI: %s | Parsed Number: %s" % (segment_uri, segment_number))
            segment = self.media_list.segments[0]
        else:
            segment = segment_result_list[0]

        log("SEGMENT URL: %s" % segment.absolute_uri)

        start = datetime.datetime.now()
        for chunk in self.download_chunks(segment.absolute_uri):
            if self.g_stopEvent.isSet():
                stream.flush()
                return

            segment_size += len(chunk)

            self.send_back(chunk, stream)

        stop = datetime.datetime.now()
        worker = workers.Thread(self.__calculate_bitrate, start, stop, segment_size, segment.duration)
        worker.daemon = True
        worker.start()

    def __calculate_bitrate(self, start, stop, segment_size, duration):

        if not self.manifest_playlist.is_variant:
            return

        decay = 0.70  # must be between 0 and 1 see: https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average

        # Calculate optimal bitrate
        elapsed = float(util.get_total_seconds_float(stop - start))
        current_segment_download_speed = float(segment_size) / elapsed

        log("SEGMENT SIZE: %s" % segment_size)
        log("ELAPSED SEGMENT (%s sec) DOWNLOAD TIME: %s | BANDWIDTH: %s" % (
        str(float(duration)), str(elapsed), current_segment_download_speed))

        real_measured_bandwidth = float(
            self.manifest_playlist.playlists[self.selected_bandwidth_index].stream_info.bandwidth) * (
                                  float(duration) / elapsed)

        self.average_download_speed = self.moving_average_bandwidth_calculator(self.average_download_speed, decay,
                                                                               real_measured_bandwidth)

        log("MAX CALCULATED BITRATE: %s" % real_measured_bandwidth)
        log("AVERAGE DOWNLOAD SPEED: %s" % self.average_download_speed)

        if self.media_list.keys and len(self.media_list.keys) > 0 and self.media_list.keys[-1]:
            log("%s" % self.media_list.dumps())
            log("ENCRYPTED PLAYLIST, SKIPPING RELOADING...")
            return

        current_bandwidth_index = self.find_bandwidth_index(self.manifest_playlist,
                                                            min(self.maxbitrate, self.average_download_speed))

        if current_bandwidth_index != self.selected_bandwidth_index:
            playlist = self.manifest_playlist.playlists[current_bandwidth_index]
            log("CHANGING BANDWIDTH TO: %s" % playlist.stream_info.bandwidth)
            self.selected_bandwidth_index = current_bandwidth_index
            self.media_list = self.load_playlist_from_uri(playlist.absolute_uri)

    def download_segment_playlist(self, uri, base_uri, stream, stopEvent=None):
        if stopEvent and stopEvent.isSet():
            return

        log("STARTING SEGMENT PLAYLIST DOWNLOAD. URI: %s" % uri)

        absolute_uri = self.manifest_playlist.base_uri + uri

        log("SEGMENT PLAYLIST ABSOLUTE URI: %s" % absolute_uri)

        media_list = self.load_playlist_from_uri(absolute_uri)

        playlist = self.manifest_playlist.playlists[self.selected_bandwidth_index] if self.manifest_playlist.is_variant else self.manifest_playlist

        log("PLAYING PLAYLIST ABSOLUTE URI: %s" % playlist.absolute_uri)

        self.media_list = self.load_playlist_from_uri(playlist.absolute_uri)

        media_list_copy = copy.deepcopy(media_list)

        media_list_copy.base_uri = base_uri
        for segment in media_list_copy.segments:
            segment.base_uri = base_uri
            parsed_url = urlparse.urlparse(segment.uri)
            segment.uri = parsed_url.path

        media_playlist_response = media_list_copy.dumps()

        log("SENDING MEDIA PLAYLIST: %s" % media_playlist_response)

        self.send_back(media_playlist_response, stream)

    def download_main_playlist(self, url, stream, stop_event=None, max_bitrate=0):
        if stop_event and stop_event.isSet():
            return

        self.average_download_speed = 0.0 #min(max_bitrate, self.average_download_speed)

        self.manifest_playlist = self.load_playlist_from_uri(url)

        self.selected_bandwidth_index = 0 #self.find_bandwidth_index(self.manifest_playlist, self.average_download_speed)

        if self.manifest_playlist.is_variant:
            manifest_playlist_copy = copy.deepcopy(self.manifest_playlist)
            playlist = self.manifest_playlist.playlists[self.selected_bandwidth_index]

            self.average_download_speed = float(playlist.stream_info.bandwidth)

            items_to_remove = filter(lambda p: p.stream_info.bandwidth != playlist.stream_info.bandwidth, manifest_playlist_copy.playlists)
            for p in items_to_remove:
                manifest_playlist_copy.playlists.remove(p)

            playlist = manifest_playlist_copy
        else:
            playlist = self.manifest_playlist

        playlist_response = playlist.dumps()
        log("SENDING PLAYLIST: %s" % playlist_response)

        self.send_back(playlist_response, stream)

    #https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average
    def moving_average_bandwidth_calculator(self, average, decay, real_bandwidth):
        return decay * real_bandwidth + (1 - decay) * average if average > 0 else real_bandwidth