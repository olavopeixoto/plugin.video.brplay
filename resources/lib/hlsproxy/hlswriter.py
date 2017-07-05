# -*- coding: utf-8 -*-

import cookielib
import os
import traceback
import urlparse

import requests
import datetime
import urllib
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

gproxy=None

cookieJar=cookielib.LWPCookieJar()
session=None
clientHeader=None
average_download_speed = 0.0
manifest_playlist = None
media_list = None
selected_bandwidth_index = None
queue = None

def log(msg):
    if is_standalone:
        print msg
    else:
        xbmc.log(msg,level=xbmc.LOGNOTICE)


def sleep(time_ms):
    if not is_standalone:
        xbmc.sleep(time_ms)


class HLSWriter():
    global cookieJar

    MAIN_MIME_TYPE = 'application/vnd.apple.mpegurl'

    """
    A downloader for hls manifests
    """
    def __init__(self):
        pass

    def init(self, out_stream, url, proxy=None, use_proxy_for_chunks=True, g_stopEvent=None, maxbitrate=0):
        global clientHeader,gproxy,session

        try:
            session = requests.Session()
            session.cookies = cookieJar
            clientHeader=None
            self.proxy = proxy

            if self.proxy and len(self.proxy)==0:
                self.proxy=None

            gproxy=self.proxy

            self.use_proxy_for_chunks=use_proxy_for_chunks
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

            global queue
            queue = Queue.Queue()
            worker = workers.Thread(set_media_list, queue, self.g_stopEvent)
            worker.daemon = True
            worker.start()

            return True
        except: 
            traceback.print_exc()

        return False

    def download_binary(self, url, dest_stream):
        global manifest_playlist

        base_uri = manifest_playlist.base_uri
        for chunk in download_chunks(base_uri + '/' + url):
            send_back(chunk, dest_stream)

    def download_segment_playlist(self, url, base_uri, dest_stream):
        download_segment_playlist(url, base_uri, dest_stream, self.g_stopEvent)

    def download_segment_media(self, url, dest_stream):
        global queue
        download_segment_media(url, dest_stream, self.g_stopEvent, queue, self.maxbitrate)

    def keep_sending_video(self, dest_stream):
        global average_download_speed
        try:
            average_download_speed = float(control.setting('average_download_speed')) if control.setting('average_download_speed') else 0.0
            download_main_playlist(self.url, dest_stream, self.g_stopEvent, self.maxbitrate)
            control.setSetting('average_download_speed', str(average_download_speed))
        except Exception, e:
            log('ERROR SENDING MAIN PLAYLIST: %s' % e.message)
            traceback.print_exc()

        
def get_url(url, timeout=15, return_response=False, stream=False):
    log("GET URL: %s" % url)

    global cookieJar
    global session
    global clientHeader

    log("GET URL Cookies: %s" % cookieJar.as_lwp_str())

    try:
        post=None

        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        if clientHeader:
            for n,v in clientHeader:
                headers[n]=v

        proxies={}

        if gproxy:
            proxies= {"http": gproxy, "https": gproxy}

        if post:
            response = session.post(url, headers=headers, data=post, proxies=proxies, verify=False, timeout=timeout, stream=stream)
        else:
            response = session.get(url, headers=headers, proxies=proxies, verify=False, timeout=timeout, stream=stream)

        response.raise_for_status()

        if return_response:
            return response
        else:
            return response.content

    except:
        traceback.print_exc()
        return None


def download_chunks(URL, chunk_size=65536):

    response=get_url(URL, timeout=6, return_response=True, stream=True)

    for chunk in response.iter_content(chunk_size=chunk_size):
        yield chunk


def send_back(data, stream):
    stream.write(data)
    stream.flush()


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


def get_segment_number(segment_uri):
    return segment_uri.split('-')[-1:][0].split('.')[0]


def queue_processor(queue, stream, stop_event):
    while not stop_event.isSet():
        data = queue.get()
        stream.write(data)
        stream.flush()
        queue.task_done()


def download_segment_media(segment_uri, stream, stopEvent, queue, maxbitrate=0):
    global average_download_speed
    global media_list
    global manifest_playlist
    global selected_bandwidth_index

    if stopEvent and stopEvent.isSet():
        return

    log ("STARTING MEDIA DOWNLOAD WITH AVERAGE SPEED: %s" % average_download_speed)

    segment_size = 0.0

    segment_number = get_segment_number(segment_uri)

    log("SEGMENT NUMBER: %s" % segment_number)

    segment = filter(lambda k: get_segment_number(k.uri) == segment_number, media_list.segments)[0]

    log("SEGMENT URL: %s" % segment.absolute_uri)

    start = datetime.datetime.now()
    for chunk in download_chunks(segment.absolute_uri):
        if stopEvent and stopEvent.isSet():
            return

        segment_size = segment_size + len(chunk)

        stream.write(chunk)

    stream.flush()

    elapsed = float(util.get_total_seconds_float(datetime.datetime.now() - start))
    current_segment_download_speed = float(segment_size) / elapsed

    log("SEGMENT SIZE: %s" % segment_size)
    log("ELAPSED SEGMENT (%s sec) DOWNLOAD TIME: %s | BANDWIDTH: %s" % (str(float(segment.duration)), str(elapsed), current_segment_download_speed))

    max_calculated_bandwidth = float(manifest_playlist.playlists[selected_bandwidth_index].stream_info.bandwidth) * (float(segment.duration) / elapsed)

    average_download_speed = (average_download_speed + max_calculated_bandwidth) / 2 if average_download_speed > 0 else max_calculated_bandwidth

    log("MAX CALCULATED BITRATE: %s" % max_calculated_bandwidth)
    log("AVERAGE DOWNLOAD SPEED: %s" % average_download_speed)

    if manifest_playlist.is_variant:
        current_bandwidth_index = find_bandwidth_index(manifest_playlist, min(maxbitrate, average_download_speed))
        if current_bandwidth_index != selected_bandwidth_index:
            playlist = manifest_playlist.playlists[current_bandwidth_index]
            log("CHANGING BANDWIDTH TO: %s" % playlist.stream_info.bandwidth)
            queue.put(playlist.absolute_uri)
            # media_list = load_playlist_from_uri(playlist.absolute_uri)

def set_media_list(queue, stopEvent):
    global media_list

    while not stopEvent.isSet():
        uri = queue.get()
        media_list = load_playlist_from_uri(uri)


def download_segment_playlist(uri, base_uri, stream, stopEvent=None):
    if stopEvent and stopEvent.isSet():
        return

    global manifest_playlist
    global media_list

    log("STARTING SEGMENT PLAYLIST DOWNLOAD. URI: %s" % uri)

    absolute_uri = manifest_playlist.base_uri + '/' + uri

    log("SEGMENT PLAYLIST ABSOLUTE URI: %s" % absolute_uri)

    media_list = load_playlist_from_uri(absolute_uri)

    media_list_copy = copy.deepcopy(media_list)

    media_list_copy.base_uri = base_uri
    for segment in media_list_copy.segments:
        segment.base_uri = base_uri
        parsed_url = urlparse.urlparse(segment.uri)
        segment.uri = parsed_url.path

    media_playlist_response = media_list_copy.dumps()

    log("SENDING MEDIA PLAYLIST: %s" % media_playlist_response)

    send_back(media_playlist_response, stream)


def download_main_playlist(url, stream, stopEvent=None, maxbitrate=0):
    if stopEvent and stopEvent.isSet():
        return

    global average_download_speed
    global manifest_playlist
    global selected_bandwidth_index

    average_download_speed = min(maxbitrate, average_download_speed)

    log("STARTING MEDIA DOWNLOAD WITH AVERAGE SPEED: %s" % average_download_speed)

    manifest_playlist = load_playlist_from_uri(url)

    selected_bandwidth_index = find_bandwidth_index(manifest_playlist, average_download_speed)

    if manifest_playlist.is_variant:
        manifest_playlist_copy = copy.deepcopy(manifest_playlist)
        playlist = manifest_playlist.playlists[selected_bandwidth_index]

        items_to_remove = filter(lambda p: p.stream_info.bandwidth != playlist.stream_info.bandwidth, manifest_playlist_copy.playlists)
        for p in items_to_remove:
            manifest_playlist_copy.playlists.remove(p)

        playlist = manifest_playlist_copy
    else:
        playlist = manifest_playlist

    playlist_response = playlist.dumps()
    log("SENDING PLAYLIST: %s" % playlist_response)

    send_back(playlist_response, stream)