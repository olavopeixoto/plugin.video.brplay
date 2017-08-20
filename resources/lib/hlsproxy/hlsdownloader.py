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

def log(msg):
    pass
    # if is_standalone:
    #     print msg
    # else:
    #     xbmc.log(msg,level=xbmc.LOGNOTICE)

try:
    from Crypto.Cipher import AES
    xbmc.log("DECRYPTOR: Native PyCrypto", xbmc.LOGNOTICE)
except:
    try:
        from  androidsslPy import AESDecrypter
        AES=AESDecrypter()
        xbmc.log("DECRYPTOR: Android PyCrypto", xbmc.LOGNOTICE)
    except:
        from decrypter import AESDecrypter
        AES = AESDecrypter()
        xbmc.log("DECRYPTOR: SOFTWARE", xbmc.LOGNOTICE)


gproxy=None
use_proxy = False

cookieJar=cookielib.LWPCookieJar()
session=None
clientHeader=None
average_download_speed = 0.0


def log_error(msg):
    if is_standalone:
        print msg
    else:
        xbmc.log(msg,level=xbmc.LOGERROR)


def sleep(time_ms):
    if not is_standalone:
        xbmc.sleep(time_ms)


class HLSDownloader():
    global cookieJar

    MAIN_MIME_TYPE = 'video/MP2T'

    """
    A downloader for hls manifests
    """
    def __init__(self):
        self.init_done=False
        self.url = None
        self.maxbitrate = 0
        self.g_stopEvent = None
        self.init_url = None

    def init(self, out_stream, url, proxy=None, g_stopEvent=None, maxbitrate=0):
        global clientHeader,gproxy,session,use_proxy

        try:
            session = requests.Session()
            session.cookies = cookieJar
            self.init_done=False
            self.init_url=url
            clientHeader=None
            self.proxy = proxy
            use_proxy = False

            if self.proxy and len(self.proxy)==0:
                self.proxy=None

            gproxy=self.proxy

            self.out_stream=out_stream

            if g_stopEvent: g_stopEvent.clear()

            self.g_stopEvent=g_stopEvent
            self.maxbitrate=maxbitrate

            if '|' in url:
                sp = url.split('|')
                url = sp[0]
                clientHeader = sp[1]
                log( clientHeader )
                clientHeader= urlparse.parse_qsl(clientHeader)
                log ('header received now url and headers are %s | %s' % (url, clientHeader))

            self.url=url

            return True
        except: 
            traceback.print_exc()

        return False

    def keep_sending_video(self, dest_stream):
        global average_download_speed
        try:
            average_download_speed = float(control.setting('average_download_speed')) if control.setting('average_download_speed') else 0.0
            queue = Queue.Queue()
            worker = workers.Thread(queue_processor, queue, dest_stream, self.g_stopEvent)
            worker.daemon = True
            worker.start()
            download_internal(self.url, queue, self.maxbitrate, self.g_stopEvent)
            control.setSetting('average_download_speed', str(average_download_speed))

            if not self.g_stopEvent.isSet():
                log("WAITING FOR QUEUE...")
                queue.join()
                log("DONE.")
                self.g_stopEvent.set()
                log("WAITING FOR WORKER THREAD...")
                worker.join()
                log("DONE.")
        except:
            traceback.print_exc()
        finally:
            self.g_stopEvent.set()


def get_url(url, timeout=15, return_response=False, stream=False):
    log("GET URL: %s" % url)

    global session
    global clientHeader
    global use_proxy

    try:
        post=None

        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        if clientHeader:
            for n,v in clientHeader:
                headers[n]=v

        proxies={}

        if use_proxy and gproxy:
            proxies={"http": gproxy, "https": gproxy}

        if post:
            response = session.post(url, headers=headers, data=post, proxies=proxies, verify=False, timeout=timeout, stream=stream)
        else:
            response = session.get(url, headers=headers, proxies=proxies, verify=False, timeout=timeout, stream=stream)

        #IF 403 RETRY WITH PROXY
        if not use_proxy and gproxy and response.status_code == 403:
            proxies= {"http": gproxy, "https": gproxy}
            use_proxy = True
            if post:
                response = session.post(url, headers=headers, data=post, proxies=proxies, verify=False, timeout=timeout, stream=stream)
            else:
                response = session.get(url, headers=headers, proxies=proxies, verify=False, timeout=timeout, stream=stream)

        response.raise_for_status()

        if return_response:
            return response
        else:
            return response.content

    except Exception, e:
        traceback.print_exc()
        return None


def download_chunks(URL, chunk_size=2048):

    response=get_url(URL, timeout=6, return_response=True, stream=True)

    for chunk in response.iter_content(chunk_size=chunk_size):
        yield chunk


def send_back(data,file):
    file.write(data)
    file.flush()


def queue_processor(queue, file, stop_event):
    while not stop_event.isSet():
        data = queue.get()
        file.write(data)
        file.flush()
        queue.task_done()


def load_playlist_from_uri(uri):
    response = get_url(uri, return_response=True)
    content = response.content.strip()
    log("PLAYLIST: %s" % content)
    parsed_url = urlparse.urlparse(uri)
    prefix = parsed_url.scheme + '://' + parsed_url.netloc
    base_path = os.path.normpath(parsed_url.path + '/..')
    base_uri = urlparse.urljoin(prefix, base_path)

    return m3u8.M3U8(content, base_uri=base_uri)


def find_bandwidth_index(playlist, average_download_speed):
    if not playlist.is_variant: return 0

    bandwidth_options = []
    for index, playlist_item in enumerate(playlist.playlists):
        bandwidth_options.append({
            'index': index,
            'bandwidth': float(playlist.playlists[index].stream_info.bandwidth)
        })
    bandwidth_options = sorted(bandwidth_options, key=lambda k: int(k['bandwidth']), reverse=True)

    for bandwidth_option in bandwidth_options:
        if bandwidth_option['bandwidth'] < average_download_speed:
            log("SELECTED BANDWIDTH: %s" % bandwidth_option['bandwidth'])
            return bandwidth_option['index']

    return 0


def download_internal(url, queue, maxbitrate=0, stopEvent=None):
    global average_download_speed

    if stopEvent and stopEvent.isSet():
        return

    # max_buffer_size = 4 * 1024 *1024 #4MB

    decay = 0.85 #must be between 0 and 1 see: https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average

    average_download_speed = min(maxbitrate, average_download_speed)

    log ("STARTING MEDIA DOWNLOAD WITH AVERAGE SPEED: %s" % average_download_speed)

    manifest_playlist = load_playlist_from_uri(url)

    current_bandwidth_index = find_bandwidth_index(manifest_playlist, average_download_speed)
    old_bandwidth_index = current_bandwidth_index

    if manifest_playlist.is_variant:
        log("SELECTING VARIANT PLAYLIST: %s" % manifest_playlist.playlists[current_bandwidth_index].stream_info.bandwidth)
        playlist = manifest_playlist.playlists[current_bandwidth_index]
    else:
        playlist = manifest_playlist

    played_segments = []

    while not stopEvent.isSet():

        media_list = load_playlist_from_uri(playlist.absolute_uri)

        is_bitrate_change = False
        segment_key = None

        for segment_index, segment in enumerate(media_list.segments):

            if stopEvent and stopEvent.isSet():
                return

            segment_number = segment.uri.split('-')[-1:][0].split('.')[0]

            if played_segments.__contains__(segment_number):
                # log("SKIPPING SEGMENT %s" % segment_number)
                continue

            log("PLAYING SEGMENT %s | URI: %s" % (segment_number, segment.absolute_uri))

            try:
                start = datetime.datetime.now()
                played_segments.append(segment_number)

                if segment.key and segment_key != segment.key.uri:
                    segment_key = segment.key.uri
                    # average_download_speed = 0.0
                    # if media_list.faxs.absolute_uri
                    log("MEDIA ENCRYPTED, KEY URI: %s" % segment.key.absolute_uri)
                    segment.key.key_value = ''.join(download_chunks(segment.key.absolute_uri))
                    log("KEY CONTENT: %s" % repr(segment.key.key_value))

                    key = segment.key.key_value
                    iv_data = segment.key.iv or media_list.media_sequence
                    iv = get_key_iv(segment.key, iv_data)

                    decryptor = AES.new(key, AES.MODE_CBC, iv)

                segment_size = 0.0
                chunk_size = 2048 if not segment.key else int(playlist.stream_info.bandwidth)
                for chunk_index, chunk in enumerate(download_chunks(segment.absolute_uri, chunk_size=chunk_size)):
                    if stopEvent and stopEvent.isSet():
                        return

                    segment_size = segment_size + len(chunk)

                    if segment.key: #decrypt chunk
                        chunk = decryptor.decrypt(chunk)

                    # log("ENQUEUING CHUNK %s FROM SEGMENT %s" % (chunk_index, segment_number))
                    queue.put(chunk)

                elapsed = float(util.get_total_seconds_float(datetime.datetime.now() - start))
                current_segment_download_speed = float(segment_size) / elapsed

                log("SEGMENT SIZE: %s" % segment_size)
                log("ELAPSED SEGMENT (%s sec) DOWNLOAD TIME: %s | BANDWIDTH: %s" % (str(float(segment.duration)), str(elapsed), current_segment_download_speed))

                real_measured_bandwidth = float(manifest_playlist.playlists[current_bandwidth_index].stream_info.bandwidth) * (float(segment.duration)/elapsed)

                average_download_speed = movingAvgBandwidthCalculator(average_download_speed, decay, real_measured_bandwidth)

                log("MAX CALCULATED BITRATE: %s" % real_measured_bandwidth)
                log("AVERAGE DOWNLOAD SPEED: %s" % average_download_speed)

                if manifest_playlist.is_variant and old_bandwidth_index == current_bandwidth_index:
                    log("SELECTING NEW BITRATE. MAXBITRATE: %s" % maxbitrate)
                    current_bandwidth_index = find_bandwidth_index(manifest_playlist, min(maxbitrate, average_download_speed))
                    playlist = manifest_playlist.playlists[current_bandwidth_index]

                    if old_bandwidth_index != current_bandwidth_index:
                        log("BANDWIDTH CHANGED TO: %s" % playlist.stream_info.bandwidth)
                        old_bandwidth_index = current_bandwidth_index
                        is_bitrate_change = True
                        break

            except Exception:
                traceback.print_exc()
                log_error('ERROR PROCESSING SEGMENT %s: %s' % (segment_number, Exception.message))
                pass

        if media_list.is_endlist and not is_bitrate_change:
            log("IS END LIST. BYE...")
            return

#https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average
def movingAvgBandwidthCalculator(average, decay, real_bandwidth):
    return decay * real_bandwidth + (1 - decay) * average if average > 0 else real_bandwidth


def get_key_iv(key, media_sequence):
    if key.iv:
        iv = str(key.iv)[2:].zfill(32) # Removes 0X prefix
        log("IV: %s" % iv)
        return iv.decode('hex')
    else:
        iv = '\0' * 8 + struct.pack('>Q', media_sequence)
        log("IV: %s" % repr(iv))
        return iv