# -*- coding: utf-8 -*-

import cookielib
import os
import traceback
import urlparse

import requests
import Queue
import datetime

import struct

from resources.lib.modules import util
from resources.lib.modules import workers
from resources.lib.modules import control
from resources.lib.modules import m3u8 as m3u8

try:
    import xbmc

    is_standalone = False
except:
    is_standalone = True

try:
    from Crypto.Cipher import AES

    control.log("DECRYPTOR: Native PyCrypto")
except:
    try:
        from androidsslPy import AESDecrypter

        AES = AESDecrypter()
        control.log("DECRYPTOR: Android PyCrypto")
    except:
        from decrypter import AESDecrypter

        AES = AESDecrypter()
        control.log("DECRYPTOR: SOFTWARE")


class HLSDownloader:

    MAIN_MIME_TYPE = 'video/MP2T'

    """
    A downloader for hls manifests
    """

    def __init__(self):
        self.enable_log = True  # enable/disable verbose logging

        self.max_queue_size = 5  # max number of segment chunks at any time in the streaming queue (chunk size defaults to max of 1 second of content)
        self.pre_buffer_segments = 2  # pre loaded number of segments before sending any content do kodi

        self.init_done = False
        self.url = None
        self.maxbitrate = 0
        self.g_stopEvent = None
        self.init_url = None
        self.out_stream = None
        self.proxy = None
        self.session = None
        self.use_proxy = False
        self.clientHeader = None
        self.average_download_speed = 0.0

    def log(self, msg):
        if self.enable_log:
            if is_standalone:
                print msg
            else:
                import threading
                control.log("%s - %s" % (threading.currentThread(), msg))

    def log_error(self, msg):
        if is_standalone:
            print msg
        else:
            control.log(msg)

    def sleep(self, time_ms):
        if not is_standalone:
            xbmc.sleep(time_ms)

    def init(self, out_stream, url, proxy=None, g_stop_event=None, maxbitrate=0):
        try:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            self.session = requests.Session()
            self.session.cookies = cookielib.LWPCookieJar()
            self.init_done = False
            self.init_url = url
            self.clientHeader = None
            self.proxy = proxy
            self.use_proxy = False

            if self.proxy and len(self.proxy) == 0:
                self.proxy = None

            self.out_stream = out_stream

            if g_stop_event: g_stop_event.clear()

            self.g_stopEvent = g_stop_event
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
            # self.average_download_speed = 0.0
            self.average_download_speed = float(control.setting('average_download_speed')) if control.setting('average_download_speed') else 0.0

            queue = Queue.Queue(self.max_queue_size)
            worker = workers.Thread(self.queue_processor, queue, dest_stream, self.g_stopEvent)
            worker.daemon = True
            worker.start()

            try:
                self.download_loop(self.url, queue, self.maxbitrate, self.g_stopEvent)
            except Exception as ex:
                self.log_error("ERROR DOWNLOADING: %s" % ex)

            control.setSetting('average_download_speed', str(self.average_download_speed))

            if not self.g_stopEvent.isSet():
                self.log("WAITING FOR QUEUE...")
                queue.join()
                self.log("DONE.")
                self.g_stopEvent.set()
                self.log("WAITING FOR WORKER THREAD...")
                worker.join()
                self.log("DONE.")
        except:
            traceback.print_exc()
        finally:
            self.g_stopEvent.set()

    def get_url(self, url, timeout=15, return_response=False, stream=False):
        self.log("GET URL: %s" % url)

        post = None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        if self.clientHeader:
            for n, v in self.clientHeader:
                headers[n] = v

        proxies = {}

        if self.use_proxy and self.proxy:
            proxies = {"http": self.proxy, "https": self.proxy}

        self.log("REQUESTING URL : %s" % repr(url))

        if post:
            response = self.session.post(url, headers=headers, data=post, proxies=proxies, verify=False, timeout=timeout,
                                    stream=stream)
        else:
            response = self.session.get(url, headers=headers, proxies=proxies, verify=False, timeout=timeout, stream=stream)

        # IF 403 RETRY WITH PROXY
        if not self.use_proxy and self.proxy and response.status_code == 403:
            proxies = {"http": self.proxy, "https": self.proxy}
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

    def queue_processor(self, queue, file, stop_event):
        while not stop_event.isSet():
            data = queue.get()
            file.write(data)
            file.flush()

    def download_chunks(self, URL, chunk_size=2048):
        try:
            response = self.get_url(URL, timeout=6, return_response=True, stream=True)

            for chunk in response.iter_content(chunk_size=chunk_size):
                yield chunk
        except Exception as ex:
            traceback.print_exc()

    def load_playlist_from_uri(self, uri):
        response = self.get_url_with_retry(uri, return_response=True)
        content = response.content.strip()
        self.log("PLAYLIST: %s" % content)
        parsed_url = urlparse.urlparse(uri)
        prefix = parsed_url.scheme + '://' + parsed_url.netloc
        base_path = os.path.normpath(parsed_url.path + '/..')
        base_uri = urlparse.urljoin(prefix, base_path)

        return m3u8.M3U8(content, base_uri=base_uri)

    def get_url_with_retry(self, url, timeout=15, return_response=False, stream=False, retry_count=3):
        try:
            return self.get_url(url, timeout, return_response, stream)
        except Exception as ex:
            if retry_count == 0:
                raise ex
            self.log_error("Retrying (%s) request due to error: %s" % (retry_count, ex))
            return self.get_url_with_retry(url, timeout, return_response, stream, retry_count - 1)

    def find_bandwidth_index(self, playlist, average_download_speed):
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
            if bandwidth_option['bandwidth'] < average_download_speed:
                self.log("SELECTED BANDWIDTH: %s" % bandwidth_option['bandwidth'])
                return bandwidth_option['index']

        return 0

    def download_loop(self, url, queue, maxbitrate=0, stopEvent=None):
        if stopEvent and stopEvent.isSet():
            return

        decay = 0.80  # must be between 0 and 1 see: https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average

        segment_buffer = b''
        segment_count = 0
        is_playing = self.pre_buffer_segments <= 0

        self.average_download_speed = min(maxbitrate, self.average_download_speed) if is_playing else 0.0

        self.log("STARTING MEDIA DOWNLOAD WITH AVERAGE SPEED: %s" % self.average_download_speed)

        manifest_playlist = self.load_playlist_from_uri(url)

        current_bandwidth_index = self.find_bandwidth_index(manifest_playlist, self.average_download_speed if is_playing else maxbitrate)
        old_bandwidth_index = current_bandwidth_index

        if manifest_playlist.is_variant:
            self.log("SELECTING VARIANT PLAYLIST: %s" % manifest_playlist.playlists[current_bandwidth_index].stream_info.bandwidth)
            playlist = manifest_playlist.playlists[current_bandwidth_index]
        else:
            playlist = manifest_playlist

        starting = True

        media_segment_time = None

        while not stopEvent.isSet():

            media_list = self.load_playlist_from_uri(playlist.absolute_uri)

            is_vod = (media_list.playlist_type or '').lower() == 'vod'

            self.log("MEDIA LIST IS VOD: %s" % is_vod)

            is_playing = is_playing or is_vod

            is_bitrate_change = False
            segment_key = None

            segments = media_list.segments

            if not is_vod and starting:
                self.log("STARTING PROGRAM DATE TIME: %s" % media_list.program_date_time)
                media_segment_time = media_list.program_date_time
                #starts to play on last 3 segments as described in https://tools.ietf.org/html/draft-pantos-http-live-streaming-07#section-6.3.3
                # mark previous segments as played
                for segment in media_list.segments[:-3]:
                    media_segment_time += datetime.timedelta(seconds=segment.duration)

            starting = False

            current_segment_program_date = media_list.program_date_time

            if not is_vod:
                self.log("ATTEMPTING TO PLAY SEGMENT ON TIME %s" % media_segment_time)

            for segment_index, segment in enumerate(segments):  # segment_index starts at 0 (zero)

                if stopEvent and stopEvent.isSet():
                    return

                if segment_index > 0 and not is_vod:
                    current_segment_program_date += datetime.timedelta(seconds=segments[segment_index-1].duration)

                if not is_vod:
                    if current_segment_program_date < media_segment_time:
                        self.log("SKIPPING SEGMENT %s (%s)" % (segment.uri, current_segment_program_date))
                        continue
                    else:
                        media_segment_time += datetime.timedelta(seconds=segment.duration)

                    media_segment_time = current_segment_program_date


                self.log("PLAYING SEGMENT %s (%s)" % (segment.absolute_uri, current_segment_program_date))

                try:
                    start = datetime.datetime.now()

                    if segment.key and segment_key != segment.key.uri:
                        segment_key = segment.key.uri
                        # average_download_speed = 0.0
                        # if media_list.faxs.absolute_uri
                        self.log("MEDIA ENCRYPTED, KEY URI: %s" % segment.key.absolute_uri)
                        segment.key.key_value = ''.join(self.download_chunks(segment.key.absolute_uri))
                        self.log("KEY CONTENT: %s" % repr(segment.key.key_value))

                        key = segment.key.key_value
                        iv_data = segment.key.iv or media_list.media_sequence
                        iv = self.get_key_iv(segment.key, iv_data)

                        decryptor = AES.new(key, AES.MODE_CBC, iv)

                    segment_size = 0.0
                    chunk_size = int(playlist.stream_info.bandwidth)
                    queue_time = 0.0
                    for chunk_index, chunk in enumerate(self.download_chunks(segment.absolute_uri, chunk_size=chunk_size)):
                        if stopEvent and stopEvent.isSet():
                            return

                        segment_size = segment_size + len(chunk)

                        if segment.key:  # decrypt chunk
                            chunk = decryptor.decrypt(chunk)

                        queue_start = datetime.datetime.now()
                        if is_playing:
                            queue.put(chunk)
                        else:
                            segment_buffer += chunk
                        queue_time_end = datetime.datetime.now()
                        queue_time += float(util.get_total_seconds_float(queue_time_end - queue_start))

                    end_download = datetime.datetime.now()
                    segment_count += 1
                    if not is_playing and segment_count == self.pre_buffer_segments:
                        is_playing = True
                        queue.put(segment_buffer)

                    elapsed = float(util.get_total_seconds_float(end_download - start) - queue_time)
                    current_segment_download_speed = float(segment_size) / elapsed

                    self.log("SEGMENT SIZE: %s" % segment_size)
                    self.log("ELAPSED SEGMENT (%s sec) DOWNLOAD TIME: %s | BANDWIDTH: %s" % (str(float(segment.duration)), str(elapsed), current_segment_download_speed))

                    real_measured_bandwidth = float(manifest_playlist.playlists[current_bandwidth_index].stream_info.bandwidth) * (float(segment.duration) / elapsed)

                    self.average_download_speed = self.moving_average_bandwidth_calculator(self.average_download_speed, decay, real_measured_bandwidth)

                    download_rate = real_measured_bandwidth / playlist.stream_info.bandwidth

                    self.log("MAX CALCULATED BITRATE: %.4f" % real_measured_bandwidth)
                    self.log("AVERAGE DOWNLOAD SPEED: %.4f" % self.average_download_speed)

                    self.log('DOWNLOAD RATE: %s' % download_rate)
                    self.log('CURRENT QUEUE SIZE: %s' % queue.qsize())

                    done_playing = (media_list.is_endlist or is_vod) and len(segments) == segment_index + 1

                    if manifest_playlist.is_variant and old_bandwidth_index == current_bandwidth_index and is_playing and not done_playing:
                        current_bandwidth = playlist.stream_info.bandwidth
                        self.log("CURRENT BANDWIDTH: %s" % current_bandwidth)
                        self.log("SELECTING NEW BITRATE. MAXBITRATE: %s" % maxbitrate)

                        if download_rate < 1 and queue.qsize() == 0:
                            self.average_download_speed = min(self.average_download_speed, real_measured_bandwidth) * float(download_rate) / 1.3
                            self.log("CHANGING AVERAGE DOWNLOAD SPEED TO (DUE TO LOW BUFFER): %s" % self.average_download_speed)

                        current_bandwidth_index = self.find_bandwidth_index(manifest_playlist, min(maxbitrate, self.average_download_speed))
                        new_playlist = manifest_playlist.playlists[current_bandwidth_index]
                        selected_bandwidth = new_playlist.stream_info.bandwidth

                        is_increasing_bandwidth = current_bandwidth < selected_bandwidth

                        if old_bandwidth_index != current_bandwidth_index and (not is_increasing_bandwidth or download_rate > 1.3):
                            self.log("BANDWIDTH CHANGED TO: %s" % selected_bandwidth)
                            old_bandwidth_index = current_bandwidth_index
                            is_bitrate_change = True
                            playlist = new_playlist
                            break

                except Exception as ex:
                    self.log_error('ERROR PROCESSING SEGMENT %s: %s' % (segment.absolute_uri, repr(ex)))
                    traceback.print_exc()

            if (media_list.is_endlist or is_vod) and not is_bitrate_change:
                self.log("IS END LIST. BYE...")
                return

    def get_segment_number(self, uri):
        return '-'.join(uri.split('=')[-1:][0].split('.')[0].split('-')[-2:])

    # https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average
    def moving_average_bandwidth_calculator(self, average, decay, real_bandwidth):
        return decay * real_bandwidth + (1 - decay) * average if average > 0 else real_bandwidth

    def get_key_iv(self, key, media_sequence):
        if key.iv:
            iv = str(key.iv)[2:].zfill(32)  # Removes 0X prefix
            self.log("IV: %s" % iv)
            return iv.decode('hex')
        else:
            iv = '\0' * 8 + struct.pack('>Q', media_sequence)
            self.log("IV: %s" % repr(iv))
            return iv