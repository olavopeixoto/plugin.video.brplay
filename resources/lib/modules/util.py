import html.entities as htmlentitydefs
import re
import time
import unicodedata
import urllib.parse as urlparse
from urllib.parse import urlencode

try:
    import cPickle as pickle
except:
    import pickle


class struct(object):
    '''
        Simple attributes helper class that behaves like dict.get for unset
        attrs.
    '''
    def __init__(self, kdict=None):
        kdict = kdict or {}
        self.__dict__.update(kdict)

    def __repr__(self):
        return repr(self.__dict__)

    def __getattr__(self, name):
        return None

    def __len__(self):
        return len(self.__dict__)

    def get(self, key):
        return self.__dict__.get(key)


CI_MPAA_Dict = {
    'L':'G',
    'LI':'G',
    'ER':'PG',
    '10':'PG',
    '12':'PG',
    '14':'PG-13',
    '16':'R',
    '18':'NC-17'
    }

# def clear_cookies():
#     try:
#         os.remove(xbmc.translatePath('special://temp/cookies.dat'))
#     except:
#         return


def getMPAAFromCI(ci):
    return CI_MPAA_Dict[ci]


def getBestBitrateUrl(plugin, streams):
    '''
        Chooses best quality limited to bitrate
    '''
    best = 0
    bitrate = int(plugin.get_setting('bitrate')[:-5])
    for bit, url in streams.items():
        if best < int(bit) < bitrate:
            best = int(bit)
    plugin.log.debug('video choosen bitrate: %d' % best)
    plugin.log.debug('video choosen url: %s' % streams[str(best)])
    return streams[str(best)]


def merge_dicts(x, *argv):
    '''Given two or more dicts, merge them into a new dict as a shallow copy.'''
    z = x.copy()
    for y in argv:
        z.update(y)
    return z


def slugify(string):
    '''
        Helper function that slugifies a given string.
    '''
    slug = unicodedata.normalize('NFKD', string)
    slug = slug.encode('ascii', 'ignore').lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    return re.sub(r'[-]+', '-', slug)


def unescape(text):
    '''
        Removes HTML or XML character references and entities from a text string.
        @param text The HTML (or XML) source text.
        @return The plain text, as a Unicode string, if necessary.
    '''
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return re.sub(r"&#?\w+;", fixup, text)


def time_format(time_str=None, input_format=None):
    '''
        Helper function to reformat time according to xbmc expecctation DD.MM.YYYY
    '''
    if time_str:
        time_obj = time.strptime(time_str, input_format)
        return time.strftime('%d.%m.%Y', time_obj)
    else:
        return time.strftime('%d.%m.%Y')


def get_utc_delta():
    import datetime as dt
    return get_total_hours(dt.datetime.now() - dt.datetime.utcnow())


def strptime(date_string, format):
    import time
    from datetime import datetime
    try:
        return datetime.strptime(date_string, format)
    except TypeError:
        return datetime(*(time.strptime(date_string, format)[0:6]))


def strptime_workaround(date_string, format='%Y-%m-%dT%H:%M:%S'):
    import time
    from datetime import datetime
    try:
        return datetime.strptime(date_string, format)
    except Exception:
        try:
            return datetime(*(time.strptime(date_string, format)[0:6]))
        except Exception:
            return datetime.strptime(date_string[0:19], format)


def get_total_seconds(timedelta):
    return (timedelta.microseconds + (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6


def get_total_seconds_float(timedelta):
    return (timedelta.microseconds + (timedelta.seconds + timedelta.days * 24.0 * 3600.0) * 10.0 ** 6.0) / 10.0 ** 6.0


def get_total_hours(timedelta):
    import datetime as dt
    hours = int(round(((timedelta.microseconds + (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6) / 3600.0))
    return dt.timedelta(hours=hours)


def add_url_parameters(url, params):

    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)

    url_parts[4] = urlencode(query)

    return urlparse.urlunparse(url_parts)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
