# -*- coding: utf-8 -*-

import http.cookiejar as cookielib
import os
import traceback
import urllib.parse as urlparse

import requests
import datetime
import copy
from resources.lib.modules import util
from resources.lib.modules import control
from resources.lib.modules import m3u8 as m3u8

from queue import Queue
from resources.lib.modules import workers

try:
    import xbmc
    is_standalone = False
except:
    is_standalone = True


class HLSWriter:

    MAIN_MIME_TYPE = 'application/vnd.apple.mpegurl'

    """
    A downloader for hls manifests
    """
    def __init__(self):
        self.enable_log = control.log_enabled

        self.cookieJar = cookielib.LWPCookieJar()
        self.session = None
        self.clientHeader = None
        self.average_download_speed = 0.0
        self.manifest_playlist = None
        self.media_list = None
        self.original_media_list = None
        self.selected_bandwidth_index = None
        self.use_proxy = False
        self.proxy = None
        self.g_stopEvent = None
        self.maxbitrate = 0
        self.url = None
        self.media_buffer = {}
        self.requested_segment = None
        self.key = None
        self.queue = None

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
                self.proxy=None

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
                self.clientHeader= urlparse.parse_qsl(self.clientHeader)
                self.log('header received now url and headers are %s | %s' % (url, self.clientHeader))

            self.url = url

            self.queue = Queue.Queue()

            worker = workers.Thread(self.__bandwidth_selector)
            worker.daemon = True
            worker.start()

            return True
        except:
            traceback.print_exc()

        return False

    def keep_sending_video(self, dest_stream):
        try:
            # self.average_download_speed = 0.0
            self.average_download_speed = float(control.setting('average_download_speed')) if control.setting('average_download_speed') else 0.0

            self.download_main_playlist(self.url, dest_stream, self.g_stopEvent, self.maxbitrate)

            control.setSetting('average_download_speed', str(self.average_download_speed))
        except Exception as e:
            self.log('ERROR SENDING MAIN PLAYLIST: %s' % e.message)
            traceback.print_exc()

    def download_main_playlist(self, url, stream, stop_event=None, max_bitrate=0):
        if stop_event and stop_event.isSet():
            return

        self.log("STARTING MAIN PLAYLIST DOWNLOAD. URI: %s" % url)

        # load main m3u8 playlist
        self.manifest_playlist = self.__load_playlist_from_uri(url)

        # find max bandwidth to use
        self.average_download_speed = min(max_bitrate, self.average_download_speed)

        if self.manifest_playlist.is_variant:

            # index of selected bandwidth from playlist bandwidth array
            self.selected_bandwidth_index = self.__find_bandwidth_index(self.manifest_playlist, self.average_download_speed)

            # creates a striped version of the original playlist containing only selected bandwidth
            manifest_playlist_copy = copy.deepcopy(self.manifest_playlist)
            playlist = self.manifest_playlist.playlists[self.selected_bandwidth_index]

            # self.average_download_speed = float(playlist.stream_info.bandwidth)

            items_to_remove = filter(lambda p: p.stream_info.bandwidth != playlist.stream_info.bandwidth, manifest_playlist_copy.playlists)
            for p in items_to_remove:
                manifest_playlist_copy.playlists.remove(p)

            playlist = manifest_playlist_copy

        else:
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

        # always send same original bandwidth back to Kodi to avoid errors, we will use proper bandwidth in the background

        start = datetime.datetime.now()

        media_list = self.__load_playlist_from_uri(absolute_uri)

        stop = datetime.datetime.now()

        self.original_media_list = copy.deepcopy(media_list)

        # replace original url with proxy's url so Kodi requests to proxy player instead of media origin
        self.original_media_list.base_uri = base_uri
        for segment in self.original_media_list.segments:
            segment.base_uri = base_uri
            parsed_url = urlparse.urlparse(segment.uri)
            segment.uri = parsed_url.path

        media_playlist_response = self.original_media_list.dumps()

        self.log("SENDING MEDIA PLAYLIST: %s" % media_playlist_response)

        self.queue.put((start, stop, 0, 0))

        self.__send_back(media_playlist_response, stream)

    def download_binary(self, url, dest_stream):

        self.log('DOWNLOADING BINARY URI: %s' % url)

        while not self.media_list or not self.media_list.keys:
            xbmc.sleep(100)
            if self.g_stopEvent and self.g_stopEvent.isSet():
                return

        file = url.split('/')[-1]
        keys = filter(lambda k: k.uri.split('/')[-1] == file, self.media_list.keys)

        retry = 20

        while len(keys) <= 0 and retry > 0:
            xbmc.sleep(50)
            if self.g_stopEvent and self.g_stopEvent.isSet():
                return
            keys = filter(lambda k: k.uri.split('/')[-1] == file, self.media_list.keys)
            retry = retry - 1

        if len(keys) <= 0:
            self.log("ERROR: KEY NOT FOUND: %s | PLAYLIST: %s" % (file, self.media_list.dumps()))
            raise Exception("KEY NOT FOUND: %s" % file)

        self.key = keys[0]
        absolute_uri = self.key.absolute_uri

        self.log('DOWNLOADING BINARY ABSOLUTE URI: %s' % absolute_uri)

        for chunk in self.__download_chunks(absolute_uri):
            self.__send_back(chunk, dest_stream)

    def download_segment_media(self, segment_uri, stream):
        if self.g_stopEvent and self.g_stopEvent.isSet():
            return

        self.log("REQUESTED MEDIA: %s" % segment_uri)

        while not self.media_list or not self.media_list.segments or len(self.media_list.segments) == 0:
            self.log("WAITING FOR MEDIA LIST...")
            xbmc.sleep(50)
            if self.g_stopEvent and self.g_stopEvent.isSet():
                return

        is_vod = (self.media_list.playlist_type or '').lower() == 'vod'

        if is_vod:
            original_segment_index = -1

            media_sequence = int(self.original_media_list.media_sequence)

            found = False

            self.log("ORIGINAL MEDIA LIST: %s" % self.original_media_list.dumps())

            for segment_index, segment in enumerate(self.original_media_list.segments):
                self.log("SEARCHING FOR SEGMENT: '%s'.endswith('%s') = %s" % (segment.uri, segment_uri, segment.uri.endswith(segment_uri)))
                if segment_uri.endswith(segment.uri):
                    original_segment_index = segment_index
                    found = True
                    break

            if not found:
                raise Exception("SEGMENT NOT FOUND!!! Requested URI: %s | Parsed Number: %s | Media Sequence: %s" % (segment_uri, original_segment_index, media_sequence))

            segment_number = media_sequence + original_segment_index

            while not self.media_list or not self.media_list.segments or self.media_list.segments == 0 or media_sequence > int(self.media_list.media_sequence):
                xbmc.sleep(100)
                if self.g_stopEvent and self.g_stopEvent.isSet():
                    return

            segment_number_index = segment_number - int(self.media_list.media_sequence)

            self.log("REQUESTED SEGMENT MEDIA SEQUENCE: %s | REQUESTED PARSED INDEX: %s | SELECTED SEGMENT MEDIA SEQUENCE: %s | SELECTED MEDIA NUMBER: %s | INDEX: %s | LENGTH: %s" % (media_sequence, original_segment_index, self.media_list.media_sequence, segment_number, segment_number_index, len(self.media_list.segments)))

            segment = self.media_list.segments[segment_number_index]
        else:
            original_date = self.original_media_list.program_date_time
            current_date = self.media_list.program_date_time

            self.log("ORIGINAL DATE/TIME: %s" % original_date)
            self.log("CURRENT DATE/TIME: %s" % current_date)

            while original_date > current_date:
                self.log("OLD PLAYLIST, RELOADING...")
                #self.__reload_segment_playlist(0, 0, 0, 0)
                xbmc.sleep(int(self.media_list.target_duration) * 1000 / 2)
                original_date = self.original_media_list.program_date_time
                current_date = self.media_list.program_date_time
                self.log("ORIGINAL DATE/TIME: %s" % original_date)
                self.log("CURRENT DATE/TIME: %s" % current_date)

            self.log("ORIGINAL PLAYLIST: %s" % self.original_media_list.dumps())
            self.log("CURRENT PLAYLIST: %s" % self.media_list.dumps())

            time_delta = current_date - original_date
            delta_seconds = util.get_total_seconds(time_delta)
            target_duration = int(self.media_list.target_duration)
            segments_delta = delta_seconds / target_duration

            self.log("SEGMENT DELTA: %s" % segments_delta)

            for segment_index, segment in enumerate(self.original_media_list.segments):
                self.log("SEARCHING FOR SEGMENT %s: '%s'.endswith('%s') = %s" % (segment_index, segment.uri, segment_uri, segment.uri.endswith(segment_uri)))
                if segment_uri.endswith(segment.uri):
                    original_segment_index = segment_index
                    found = True
                    break

            if not found:
                raise Exception("SEGMENT NOT FOUND!!! Requested URI: %s | Parsed Number: %s" % (segment_uri, original_segment_index))

            segment_index = original_segment_index - segments_delta

            self.log("SEGMENT INDEX: %s" % segment_index)

            segment = self.media_list.segments[segment_index]

            # segment_number = self.__get_segment_number(segment_uri)
            #
            # segment_result_list = filter(lambda k: self.__get_segment_number(k.uri) == segment_number, self.media_list.segments)
            #
            # while len(segment_result_list) == 0:
            #     self.log("WAITING FOR SEGMENT (URI: %s | Number: %s | Media List: %s)..." % (segment_uri, segment_number, self.media_list.dumps()))
            #     xbmc.sleep(50)
            #     if self.g_stopEvent and self.g_stopEvent.isSet():
            #         return
            #     segment_result_list = filter(lambda k: self.__get_segment_number(k.uri) == segment_number, self.media_list.segments)
            #
            # segment = segment_result_list[0]

        self.log("REQUESTED MEDIA URI: %s | DOWNLOADING MEDIA URI: %s" % (segment_uri, segment.absolute_uri))

        segment_size = 0.0
        start = datetime.datetime.now()
        for chunk in self.__download_chunks(segment.absolute_uri):
            if self.g_stopEvent.isSet():
                stream.flush()
                return

            segment_size += len(chunk)

            stream.write(chunk)

        stream.flush()
        stop = datetime.datetime.now()

        self.queue.put((start, stop, segment_size, segment.duration))

    def __bandwidth_selector(self):
        self.log("STARTED BANDWIDTH SELECTOR WORKER")
        while not self.g_stopEvent.isSet():
            try:
                (start, stop, size, duration) = self.queue.get()
                self.__reload_segment_playlist(start, stop, size, duration)
            except Exception as ex:
                self.log_error("ERROR PROCESSING BANDWIDTH: %s" % repr(ex))
                traceback.print_exc()
            finally:
                self.queue.task_done()

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

    def __find_bandwidth_index(self, playlist, average_download_speed, safe_ratio=1.0):
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
                self.log("SELECTED BANDWIDTH: %s" % bandwidth_option['bandwidth'])
                return bandwidth_option['index']

        return 0

    def __reload_segment_playlist(self, start, stop, segment_size, duration):

        if not self.manifest_playlist.is_variant:
            return

        if duration > 0:
            decay = 0.80  # must be between 0 and 1 see: https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average

            # Calculate optimal bitrate
            elapsed = float(util.get_total_seconds_float(stop - start))
            current_segment_download_speed = float(segment_size) * 8 / elapsed

            self.log("SEGMENT SIZE: %s | ELAPSED SEGMENT (%s sec) DOWNLOAD TIME: %s | BANDWIDTH: %s" % (segment_size,str(float(duration)), str(elapsed), current_segment_download_speed))

            playlist = self.manifest_playlist.playlists[self.selected_bandwidth_index]

            real_measured_bandwidth = float(playlist.stream_info.bandwidth) * (float(duration) / elapsed)

            self.average_download_speed = self.__moving_average_bandwidth_calculator(self.average_download_speed, decay, real_measured_bandwidth)

            download_rate = real_measured_bandwidth / playlist.stream_info.bandwidth

            self.log("MAX CALCULATED BITRATE: %s" % real_measured_bandwidth)
            self.log("AVERAGE DOWNLOAD SPEED: %s" % self.average_download_speed)
            self.log('DOWNLOAD RATE: %s' % download_rate)

            current_bandwidth_index = self.__find_bandwidth_index(self.manifest_playlist, min(self.maxbitrate, self.average_download_speed))

            current_bandwidth = playlist.stream_info.bandwidth
            playlist = self.manifest_playlist.playlists[current_bandwidth_index]
            selected_bandwidth = playlist.stream_info.bandwidth
            is_increasing_bandwidth = current_bandwidth < selected_bandwidth

            if current_bandwidth_index != self.selected_bandwidth_index and (not is_increasing_bandwidth or download_rate > 1.3):
                self.log("CHANGING BANDWIDTH TO: %s" % playlist.stream_info.bandwidth)
                self.selected_bandwidth_index = current_bandwidth_index
                self.media_list = self.__load_playlist_from_uri(playlist.absolute_uri)
        else:
            self.media_list = self.__load_playlist_from_uri(self.manifest_playlist.playlists[self.selected_bandwidth_index].absolute_uri)

    # https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average
    def __moving_average_bandwidth_calculator(self, average, decay, real_bandwidth):
        return decay * real_bandwidth + (1 - decay) * average if average > 0 else real_bandwidth

    def __get_segment_number(self, uri):
        return '-'.join(uri.split('=')[-1:][0].split('.')[0].split('-')[-2:])
