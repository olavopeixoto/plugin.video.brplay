# -*- coding: utf-8 -*-

import os, json, threading

import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs

lang = xbmcaddon.Addon().getLocalizedString

lang2 = xbmc.getLocalizedString

setting = xbmcaddon.Addon().getSetting

setSetting = xbmcaddon.Addon().setSetting

openSettings = xbmcaddon.Addon().openSettings

addon = xbmcaddon.Addon

addItem = xbmcplugin.addDirectoryItem

addItems = xbmcplugin.addDirectoryItems

item = xbmcgui.ListItem

directory = xbmcplugin.endOfDirectory

content = xbmcplugin.setContent

property = xbmcplugin.setProperty

category = xbmcplugin.setPluginCategory

monitor = xbmc.Monitor()

addSortMethod = xbmcplugin.addSortMethod
SORT_METHOD_NONE = xbmcplugin.SORT_METHOD_NONE
SORT_METHOD_UNSORTED = xbmcplugin.SORT_METHOD_UNSORTED
SORT_METHOD_TRACKNUM = xbmcplugin.SORT_METHOD_TRACKNUM
SORT_METHOD_FILE = xbmcplugin.SORT_METHOD_FILE
SORT_METHOD_TITLE = xbmcplugin.SORT_METHOD_TITLE
SORT_METHOD_TITLE_IGNORE_THE = xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE
SORT_METHOD_VIDEO_TITLE = xbmcplugin.SORT_METHOD_VIDEO_TITLE
SORT_METHOD_VIDEO_SORT_TITLE = xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE
SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE = xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE
SORT_METHOD_VIDEO_RUNTIME = xbmcplugin.SORT_METHOD_VIDEO_RUNTIME
SORT_METHOD_FULLPATH = xbmcplugin.SORT_METHOD_FULLPATH
SORT_METHOD_LABEL = xbmcplugin.SORT_METHOD_LABEL
SORT_METHOD_LABEL_IGNORE_THE = xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
SORT_METHOD_LABEL_IGNORE_FOLDERS = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS
SORT_METHOD_CHANNEL = xbmcplugin.SORT_METHOD_CHANNEL
SORT_METHOD_DATE = xbmcplugin.SORT_METHOD_DATE
SORT_METHOD_DATEADDED = xbmcplugin.SORT_METHOD_DATEADDED
SORT_METHOD_PLAYLIST_ORDER = xbmcplugin.SORT_METHOD_PLAYLIST_ORDER

#
# SORT_METHOD_ALBUM = 13
# SORT_METHOD_ALBUM_IGNORE_THE = 14
# SORT_METHOD_ARTIST = 11
# SORT_METHOD_ARTIST_IGNORE_THE = 12
# SORT_METHOD_BITRATE = 39
# SORT_METHOD_CHANNEL = 38
# SORT_METHOD_COUNTRY = 16
# SORT_METHOD_DATE = 3
# SORT_METHOD_DATEADDED = 19
# SORT_METHOD_DATE_TAKEN = 40
# SORT_METHOD_DRIVE_TYPE = 6
# SORT_METHOD_DURATION = 8
# SORT_METHOD_EPISODE = 22
# SORT_METHOD_FILE = 5
# SORT_METHOD_FULLPATH = 32
# SORT_METHOD_GENRE = 15
# SORT_METHOD_LABEL = 1
# SORT_METHOD_LABEL_IGNORE_FOLDERS = 33
# SORT_METHOD_LABEL_IGNORE_THE = 2
# SORT_METHOD_LASTPLAYED = 34
# SORT_METHOD_LISTENERS = 36
# SORT_METHOD_MPAA_RATING = 28
# SORT_METHOD_NONE = 0
# SORT_METHOD_PLAYCOUNT = 35
# SORT_METHOD_PLAYLIST_ORDER = 21
# SORT_METHOD_PRODUCTIONCODE = 26
# SORT_METHOD_PROGRAM_COUNT = 20
# SORT_METHOD_SIZE = 4
# SORT_METHOD_SONG_RATING = 27
# SORT_METHOD_STUDIO = 30
# SORT_METHOD_STUDIO_IGNORE_THE = 31
# SORT_METHOD_TITLE = 9
# SORT_METHOD_TITLE_IGNORE_THE = 10
# SORT_METHOD_TRACKNUM = 7
# SORT_METHOD_UNSORTED = 37
# SORT_METHOD_VIDEO_RATING = 18
# SORT_METHOD_VIDEO_RUNTIME = 29
# SORT_METHOD_VIDEO_SORT_TITLE = 24
# SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE = 25
# SORT_METHOD_VIDEO_TITLE = 23
# SORT_METHOD_VIDEO_YEAR = 17

addonInfo = xbmcaddon.Addon().getAddonInfo

infoLabel = xbmc.getInfoLabel

condVisibility = xbmc.getCondVisibility

jsonrpc = xbmc.executeJSONRPC

window = xbmcgui.Window(10000)

dialog = xbmcgui.Dialog()

progressDialog = xbmcgui.DialogProgress()

progressDialogBG = xbmcgui.DialogProgressBG()

windowDialog = xbmcgui.WindowDialog()

button = xbmcgui.ControlButton

image = xbmcgui.ControlImage

keyboard = xbmc.Keyboard

sleep = xbmc.sleep

execute = xbmc.executebuiltin

skin = xbmc.getSkinDir()

player = xbmc.Player()

playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

resolve = xbmcplugin.setResolvedUrl

openFile = xbmcvfs.File

makeFile = xbmcvfs.mkdir

deleteFile = xbmcvfs.delete

deleteDir = xbmcvfs.rmdir

listDir = xbmcvfs.listdir

transPath = xbmc.translatePath

skinPath = xbmc.translatePath('special://skin/')

tempPath = xbmc.translatePath('special://temp/')

addonPath = xbmc.translatePath(addonInfo('path'))

dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')

settingsFile = os.path.join(dataPath, 'settings.xml')

viewsFile = os.path.join(dataPath, 'views.db')

bookmarksFile = os.path.join(dataPath, 'bookmarks.db')

providercacheFile = os.path.join(dataPath, 'providers.13.db')

metacacheFile = os.path.join(dataPath, 'meta.5.db')

cacheFile = os.path.join(dataPath, 'cache.db')

isJarvis = infoLabel("System.BuildVersion").startswith("16.")

isKrypton = infoLabel("System.BuildVersion").startswith("17.")

isFTV = skin.lower().startswith('skin.ftv')

cookieFile = os.path.join(tempPath, 'cookies.dat')

proxy_url = xbmcaddon.Addon().getSetting('proxy_url') if xbmcaddon.Addon().getSetting('use_proxy') == 'true' else None

show_adult_content = xbmcaddon.Addon().getSetting('show_adult') == 'true'

__inputstream_addon_available = None

ignore_channel_authorization = xbmcaddon.Addon().getSetting('ignore_channel_authorization') == 'true'

is_4k_enabled =  xbmcaddon.Addon().getSetting('enable_4k') == 'true'

is_4k_images_enabled =  xbmcaddon.Addon().getSetting('enable_4k_fanart') == 'true'

log_enabled = setting('enable_log') == 'true'

enable_inputstream_adaptive = setting("enable_inputstream_adaptive") == 'true'


def get_current_brasilia_utc_offset():
    try:
        import pytz
        import datetime
        import resources.lib.modules.util as util

        sp_timezone = pytz.timezone('America/Sao_Paulo')
        return util.get_total_seconds(datetime.datetime.now(sp_timezone).utcoffset()) / 60 / 60
    except Exception as ex:
        log("TIMEZONE ERROR: %s" % repr(ex))
        return -3


def get_inputstream_addon():
    """Checks if the inputstream addon is installed & enabled.
       Returns the type of the inputstream addon used and if it's enabled,
       or None if not found.
    Returns
    -------
    :obj:`tuple` of obj:`str` and bool, or None
        Inputstream addon and if it's enabled, or None
    """
    type = 'inputstream.adaptive'
    payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'Addons.GetAddonDetails',
        'params': {
            'addonid': type,
            'properties': ['enabled']
        }
    }
    response = xbmc.executeJSONRPC(json.dumps(payload))
    data = json.loads(response)
    if 'error' not in data.keys():
        return type, data['result']['addon']['enabled']
    return None, None


def is_inputstream_available():
    global enable_inputstream_adaptive

    if not enable_inputstream_adaptive:
        return False

    global __inputstream_addon_available

    if __inputstream_addon_available is None:
        lock = threading.RLock()

        try:
            lock.acquire()
            if __inputstream_addon_available is None:
                (inputstream_addon, inputstream_enabled) = get_inputstream_addon()
                __inputstream_addon_available = inputstream_addon is not None and inputstream_enabled
        except Exception as ex:
            log("ERROR FINDING INPUTSTREAM ADDON, CONSIDERING MISSING: %s" % repr(ex))
            __inputstream_addon_available = False
        finally:
            lock.release()

    return __inputstream_addon_available


def is_globosat_available():
    return setting('globosat_available') == 'true' and (is_globoplay_available() if setting('use_globoplay_credentials_for_globosat') == 'true' else setting('globosat_username') != '' and setting('globosat_password') != '')


def is_globoplay_available():
    username = setting('globoplay_username')
    password = setting('globoplay_password')

    return username and password and username.strip() != '' and password.strip() != ''


def getKodiVersion():
    return infoLabel("System.BuildVersion").split(' ')[0]


def addonIcon():
    art = artPath()
    if not (art is None): return os.path.join(art, 'icon.png')
    return addonInfo('icon')


def getBandwidthLimit():
    json_result = xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","method":"Settings.GetSettingValue","params":{"setting":"network.bandwidth"},"id":1}')
    data_object = json.loads(json_result)
    return data_object['result']['value']


def addonThumb():
    art = artPath()
    if not (art is None): return os.path.join(art, 'poster.png')
    return addonInfo('icon')


def addonPoster():
    art = artPath()
    if not (art is None): return os.path.join(art, 'poster.png')
    return 'DefaultVideo.png'


def addonBanner():
    art = artPath()
    if not (art is None): return os.path.join(art, 'banner.png')
    return 'DefaultVideo.png'


def addonFanart():
    return os.path.join(addonPath, 'fanart.jpg')


def addonNext():
    art = artPath()
    if not (art is None): return os.path.join(art, 'next.png')
    return 'DefaultVideo.png'


def artPath():
    return os.path.join(addonPath, 'resources', 'media')


def okDialog(heading, line1, line2=None, line3=None):
    dialog.ok(heading=heading, line1=line1, line2=line2, line3=line3)


def infoDialog(message, heading=addonInfo('name'), icon='', time=3000, sound=False):
    if icon == '':
        icon = addonIcon()
    elif icon == 'INFO':
        icon = xbmcgui.NOTIFICATION_INFO
    elif icon == 'WARNING':
        icon = xbmcgui.NOTIFICATION_WARNING
    elif icon == 'ERROR':
        icon = xbmcgui.NOTIFICATION_ERROR
    dialog.notification(heading=heading, message=message, icon=icon, time=time, sound=sound)


def yesnoDialog(line1, line2, line3, heading=addonInfo('name'), nolabel='', yeslabel=''):
    return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)


def selectDialog(list, heading=addonInfo('name')):
    return dialog.select(heading, list)


def apiLanguage(ret_name=None):
    langDict = {'Bulgarian': 'bg', 'Chinese': 'zh', 'Croatian': 'hr', 'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl',
                'English': 'en', 'Finnish': 'fi', 'French': 'fr', 'German': 'de', 'Greek': 'el', 'Hebrew': 'he',
                'Hungarian': 'hu', 'Italian': 'it', 'Japanese': 'ja', 'Korean': 'ko', 'Norwegian': 'no', 'Polish': 'pl',
                'Portuguese': 'pt', 'Romanian': 'ro', 'Russian': 'ru', 'Serbian': 'sr', 'Slovak': 'sk',
                'Slovenian': 'sl', 'Spanish': 'es', 'Swedish': 'sv', 'Thai': 'th', 'Turkish': 'tr', 'Ukrainian': 'uk'}

    trakt = ['bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr', 'he', 'hr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl',
             'pt', 'ro', 'ru', 'sk', 'sl', 'sr', 'sv', 'th', 'tr', 'uk', 'zh']
    tvdb = ['en', 'sv', 'no', 'da', 'fi', 'nl', 'de', 'it', 'es', 'fr', 'pl', 'hu', 'el', 'tr', 'ru', 'he', 'ja', 'pt',
            'zh', 'cs', 'sl', 'hr', 'ko']
    youtube = ['gv', 'gu', 'gd', 'ga', 'gn', 'gl', 'ty', 'tw', 'tt', 'tr', 'ts', 'tn', 'to', 'tl', 'tk', 'th', 'ti',
               'tg', 'te', 'ta', 'de', 'da', 'dz', 'dv', 'qu', 'zh', 'za', 'zu', 'wa', 'wo', 'jv', 'ja', 'ch', 'co',
               'ca', 'ce', 'cy', 'cs', 'cr', 'cv', 'cu', 'ps', 'pt', 'pa', 'pi', 'pl', 'mg', 'ml', 'mn', 'mi', 'mh',
               'mk', 'mt', 'ms', 'mr', 'my', 've', 'vi', 'is', 'iu', 'it', 'vo', 'ii', 'ik', 'io', 'ia', 'ie', 'id',
               'ig', 'fr', 'fy', 'fa', 'ff', 'fi', 'fj', 'fo', 'ss', 'sr', 'sq', 'sw', 'sv', 'su', 'st', 'sk', 'si',
               'so', 'sn', 'sm', 'sl', 'sc', 'sa', 'sg', 'se', 'sd', 'lg', 'lb', 'la', 'ln', 'lo', 'li', 'lv', 'lt',
               'lu', 'yi', 'yo', 'el', 'eo', 'en', 'ee', 'eu', 'et', 'es', 'ru', 'rw', 'rm', 'rn', 'ro', 'be', 'bg',
               'ba', 'bm', 'bn', 'bo', 'bh', 'bi', 'br', 'bs', 'om', 'oj', 'oc', 'os', 'or', 'xh', 'hz', 'hy', 'hr',
               'ht', 'hu', 'hi', 'ho', 'ha', 'he', 'uz', 'ur', 'uk', 'ug', 'aa', 'ab', 'ae', 'af', 'ak', 'am', 'an',
               'as', 'ar', 'av', 'ay', 'az', 'nl', 'nn', 'no', 'na', 'nb', 'nd', 'ne', 'ng', 'ny', 'nr', 'nv', 'ka',
               'kg', 'kk', 'kj', 'ki', 'ko', 'kn', 'km', 'kl', 'ks', 'kr', 'kw', 'kv', 'ku', 'ky']

    name = setting('api.language')
    if name[-1].isupper():
        try:
            name = xbmc.getLanguage(xbmc.ENGLISH_NAME).split(' ')[0]
        except:
            pass
    try:
        name = langDict[name]
    except:
        name = 'en'
    lang = {'trakt': name} if name in trakt else {'trakt': 'en'}
    lang['tvdb'] = name if name in tvdb else 'en'
    lang['youtube'] = name if name in youtube else 'en'

    if ret_name:
        lang['trakt'] = [i[0] for i in langDict.iteritems() if i[1] == lang['trakt']][0]
        lang['tvdb'] = [i[0] for i in langDict.iteritems() if i[1] == lang['tvdb']][0]
        lang['youtube'] = [i[0] for i in langDict.iteritems() if i[1] == lang['youtube']][0]

    return lang


def version():
    num = ''
    try:
        version = addon('xbmc.addon').getAddonInfo('version')
    except:
        version = '999'
    for i in version:
        if i.isdigit():
            num += i
        else:
            break
    return int(num)


def cdnImport(uri, name):
    import imp
    from resources.lib.modules import client

    path = os.path.join(dataPath, 'py' + name)
    path = path.decode('utf-8')

    deleteDir(os.path.join(path, ''), force=True)
    makeFile(dataPath)
    makeFile(path)

    r = client.request(uri)
    p = os.path.join(path, name + '.py')
    f = openFile(p, 'w')
    f.write(r)
    f.close()
    m = imp.load_source(name, p)

    deleteDir(os.path.join(path, ''), force=True)
    return m


def openSettings(query=None, id=addonInfo('id')):
    try:
        idle()
        execute('Addon.OpenSettings(%s)' % id)
        if query is None: raise Exception()
        c, f = query.split('.')
        execute('SetFocus(%i)' % (int(c) + 100))
        execute('SetFocus(%i)' % (int(f) + 200))
    except:
        return


def refresh():
    return execute('Container.Refresh')


def idle():
    return execute('Dialog.Close(busydialog)')


def queueItem():
    return execute('Action(Queue)')


def clear_credentials():
    setSetting("sexyhot_credentials", None)
    setSetting("globosat_credentials", None)
    setSetting("globoplay_credentials", None)


def log(msg):
    if log_enabled:
        xbmc.log('[plugin.video.brplay] - ' + str(msg), xbmc.LOGNOTICE)  # xbmc.LOGDEBUG


def get_coordinates(affiliate):

    if affiliate == "Rio de Janeiro":
        code, latitude, longitude = "RJ", "-22.970722", "-43.182365"
    elif affiliate == "Sao Paulo":
        code, latitude, longitude = "SP1", '-23.5505', '-46.6333'
    elif affiliate == "Brasilia":
        code, latitude, longitude = "DF", '-15.7942',' -47.8825'
    elif affiliate == "Belo Horizonte":
        code, latitude, longitude = "BH", '-19.9245','-43.9352'
    elif affiliate == "Recife":
        code, latitude, longitude = "PE1", '-8.0476','-34.8770'
    elif affiliate == "Salvador":
        code, latitude, longitude = "SAL", '-12.9722','-38.5014'
    elif affiliate == "Fortaleza":
        code, latitude, longitude = "CE1", '-3.7319','-38.5267'
    elif affiliate == "Aracaju":
        code, latitude, longitude = "SER", '-10.9472','-37.0731'
    elif affiliate == "Maceio":
        code, latitude, longitude = "MAC", '-9.6498','-35.7089'
    elif affiliate == "Cuiaba":
        code, latitude, longitude = "MT", '-15.6014','-56.0979'
    elif affiliate == "Porto Alegre":
        code, latitude, longitude = "RS1", '-30.0347','-51.2177'
    elif affiliate == "Florianopolis":
        code, latitude, longitude = "SC1", '-27.5949','-48.5482'
    elif affiliate == "Curitiba":
        code, latitude, longitude = "CUR", '-25.4244','-49.2654'
    elif affiliate == "Vitoria":
        code, latitude, longitude = "VIT", '-20.2976','-40.2958'
    elif affiliate == "Goiania":
        code, latitude, longitude = "GO01", '-16.6869','-49.2648'
    elif affiliate == "Campo Grande":
        code, latitude, longitude = "MS1", '-20.4697','-54.6201'
    elif affiliate == "Manaus":
        code, latitude, longitude = "MAN", '-3.1190','-60.0217'
    elif affiliate == "Belem":
        code, latitude, longitude = "BEL", '-1.4558','-48.4902'
    elif affiliate == "Macapa":
        code, latitude, longitude = "AMP", '-0.0356','-51.0705'
    elif affiliate == "Palmas":
        code, latitude, longitude = "PAL", '-10.2491','-48.3243'
    elif affiliate == "Rio Branco":
        code, latitude, longitude = "ACR", '-9.9754','-67.8249'
    elif affiliate == "Teresina":
        code, latitude, longitude = "TER", '-5.0920','-42.8038'
    elif affiliate == "Sao Luis":
        code, latitude, longitude = "MA1", '-2.5391','-44.2829'
    elif affiliate == "Joao Pessoa":
        code, latitude, longitude = "JP", '-7.1195','-34.8450'
    elif affiliate == "Natal":
        code, latitude, longitude = "NAT", '-5.7793','-35.2009'
    elif affiliate == "Boa Vista":
        code, latitude, longitude = "ROR", '2.82','-60.672'
    elif affiliate == "Porto Velho":
        code, latitude, longitude = "RON", '-8.76194','-63.90389'
    elif affiliate == "Auto":
        city, latitude, longitude = get_ip_coordinates()
        code = None
    elif affiliate == "Custom":
        latitude = setting('custom_affiliate_latitude')
        longitude = setting('custom_affiliate_longitude')
        if not latitude:
            latitude = None
        if not longitude:
            longitude = None
        code = None
    else:
        code, latitude, longitude = None, None, None

    return code, latitude, longitude


def get_ip_coordinates():
    from urllib2 import urlopen

    url = 'http://ipinfo.io/json'
    response = urlopen(url)
    data = json.load(response)

    loc = data['loc']
    city = data['city']
    loc = loc.split(',')

    latitude = loc[0]
    longitude = loc[1]

    return city, latitude, longitude


def get_affiliates_by_id(id):

    all_affiliates = ['Custom','Auto','Rio de Janeiro','Sao Paulo','Brasilia','Belo Horizonte','Recife','Manaus','Rio Branco','Boa Vista','Porto Velho','Macapa','Goiania','Belem','Salvador','Florianopolis','Sao Luis','Vitoria','Fortaleza','Porto Alegre','Natal','Curitiba']

    if id == 0:  # All
        return all_affiliates

    id = id -1

    if len(all_affiliates) > id >= 0:
        return [all_affiliates[id]]

    # Default Rio de Janeiro
    return [all_affiliates[0]]
