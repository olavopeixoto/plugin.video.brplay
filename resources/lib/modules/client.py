# -*- coding: utf-8 -*-

import HTMLParser
import StringIO
import base64
import cookielib
import gzip
import json
import random
import re
import sys
import time
import urllib
import urllib2
import urlparse

from resources.lib.modules import control, cache
from resources.lib.modules import workers


def request(url, close=True, redirect=True, error=False, proxy=None, post=None, headers=None, mobile=False, XHR=False, limit=None, referer=None, cookie=None, output='', timeout='30'):
    try:
        handlers = []

        if not proxy == None:
            control.log("proxy: %s" % proxy)
            handlers += [urllib2.ProxyHandler(proxy), urllib2.HTTPHandler]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)


        if output == 'cookie' or output == 'extended' or not close == True:
            cookies = cookielib.LWPCookieJar()
            handlers += [urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.HTTPCookieProcessor(cookies)]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)


        try:
            if sys.version_info < (2, 7, 9): raise Exception()
            import ssl; ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            handlers += [urllib2.HTTPSHandler(context=ssl_context)]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)
        except:
            pass


        try: headers.update(headers)
        except: headers = {}
        if 'User-Agent' in headers:
            pass
        elif not mobile == True:
            #headers['User-Agent'] = agent()
            headers['User-Agent'] = cache.get(randomagent, 1)
        else:
            headers['User-Agent'] = 'Apple-iPhone/701.341'
        if 'Referer' in headers:
            pass
        elif referer == None:
            headers['Referer'] = '%s://%s/' % (urlparse.urlparse(url).scheme, urlparse.urlparse(url).netloc)
        else:
            headers['Referer'] = referer
        if not 'Accept-Language' in headers:
            headers['Accept-Language'] = 'en-US'
        if 'X-Requested-With' in headers:
            pass
        elif XHR == True:
            headers['X-Requested-With'] = 'XMLHttpRequest'
        if 'Cookie' in headers:
            pass
        elif not cookie == None:
            headers['Cookie'] = printCookieDict(cookie) if isinstance(cookie, dict) else cookie


        if redirect == False:

            class NoRedirection(urllib2.HTTPErrorProcessor):
                def http_response(self, request, response): return response

            opener = urllib2.build_opener(NoRedirection)
            opener = urllib2.install_opener(opener)

            try: del headers['Referer']
            except: pass

        request = urllib2.Request(url, data=post, headers=headers)

        control.log("Url request: %s" % url)

        try:
            response = urllib2.urlopen(request, timeout=int(timeout))
        except urllib2.HTTPError as response:

            if response.code == 503:
                cf_result = response.read(5242880)
                try: encoding = response.info().getheader('Content-Encoding')
                except: encoding = None
                if encoding == 'gzip':
                    cf_result = gzip.GzipFile(fileobj=StringIO.StringIO(cf_result)).read()

                if 'cf-browser-verification' in cf_result:

                    netloc = '%s://%s' % (urlparse.urlparse(url).scheme, urlparse.urlparse(url).netloc)

                    ua = headers['User-Agent']

                    cf = cache.get(cfcookie().get, 168, netloc, ua, timeout)

                    headers['Cookie'] = cf

                    request = urllib2.Request(url, data=post, headers=headers)

                    response = urllib2.urlopen(request, timeout=int(timeout))

                elif error == False:
                    return
            elif response.code == 403:
                raise Exception("Permission Denied")
            elif error == False:
                return


        if output == 'cookie':
            try: result = '; '.join(['%s=%s' % (i.name, i.value) for i in cookies])
            except: pass
            try: result = cf
            except: pass
            if close == True: response.close()
            return result

        elif output == 'geturl':
            result = response.geturl()
            if close == True: response.close()
            return result

        elif output == 'headers':
            result = response.headers
            if close == True: response.close()
            return result

        elif output == 'chunk':
            try: content = int(response.headers['Content-Length'])
            except: content = (2049 * 1024)
            if content < (2048 * 1024): return
            result = response.read(16 * 1024)
            if close == True: response.close()
            return result


        if limit == '0':
            result = response.read(224 * 1024)
        elif not limit == None:
            result = response.read(int(limit) * 1024)
        else:
            result = response.read(5242880)

        try: encoding = response.info().getheader('Content-Encoding')
        except: encoding = None
        if encoding == 'gzip':
            result = gzip.GzipFile(fileobj=StringIO.StringIO(result)).read()


        if 'sucuri_cloudproxy_js' in result:
            su = sucuri().get(result)

            headers['Cookie'] = su

            request = urllib2.Request(url, data=post, headers=headers)

            response = urllib2.urlopen(request, timeout=int(timeout))

            if limit == '0':
                result = response.read(224 * 1024)
            elif not limit == None:
                result = response.read(int(limit) * 1024)
            else:
                result = response.read(5242880)

            try: encoding = response.info().getheader('Content-Encoding')
            except: encoding = None
            if encoding == 'gzip':
                result = gzip.GzipFile(fileobj=StringIO.StringIO(result)).read()

        if 'application/json' in response.headers.get('content-type') or 'text/javascript' in response.headers.get('content-type'):
            #control.log("response: %s" % result)
            return json.loads(result)

        if output == 'extended':
            response_headers = response.headers
            response_code = str(response.code)
            try: cookie = '; '.join(['%s=%s' % (i.name, i.value) for i in cookies])
            except: pass
            try: cookie = cf
            except: pass
            if close == True: response.close()
            return (result, response_code, response_headers, headers, cookie)
        else:
            if close == True: response.close()
            return result
    except:
        return

def printCookieDict(cookie_dict):
    cookie_string = ""
    for name in cookie_dict:
        cookie_string += "%s=%s;" % (name, cookie_dict[name])

    return cookie_string


def parseDOM(html, name='', attrs=None, ret=False):
    # Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

    if attrs is None: attrs = {}
    if isinstance(html, str):
        try:
            html = [html.decode("utf-8")]  # Replace with chardet thingy
        except:
            try:
                html = [html.decode("utf-8", "replace")]
            except:
                html = [html]
    elif isinstance(html, unicode):
        html = [html]
    elif not isinstance(html, list):
        return ''

    if not name.strip():
        return ''
    
    if not isinstance(attrs, dict):
        return ''

    ret_lst = []
    for item in html:
        for match in re.findall('(<[^>]*\n[^>]*>)', item):
            item = item.replace(match, match.replace('\n', ' ').replace('\r', ' '))

        if not attrs:
            pattern = '(<%s(?: [^>]*>|/?>))' % (name)
            this_list = re.findall(pattern, item, re.M | re.S | re.I)
        else:
            last_list = None
            for key in attrs:
                pattern = '''(<%s [^>]*%s=['"]%s['"][^>]*>)''' % (name, key, attrs[key])
                this_list = re.findall(pattern, item, re.M | re. S | re.I)
                if not this_list and ' ' not in attrs[key]:
                    pattern = '''(<%s [^>]*%s=%s[^>]*>)''' % (name, key, attrs[key])
                    this_list = re.findall(pattern, item, re.M | re. S | re.I)
        
                if last_list is None:
                    last_list = this_list
                else:
                    last_list = [item for item in this_list if item in last_list]
            this_list = last_list

        lst = this_list

        if isinstance(ret, str):
            lst2 = []

            for match in lst:
                pattern = '''<%s[^>]* %s\s*=\s*(?:(['"])(.*?)\\1|([^'"].*?)(?:>|\s))''' % (name, ret)
                results = re.findall(pattern, match, re.I | re.M | re.S)
                lst2 += [result[1] if result[1] else result[2] for result in results]

            lst = lst2
        else:
            lst2 = []
            for match in lst:
                end_str = "</%s" % (name)
                start_str = '<%s' % (name)

                start = item.find(match)
                end = item.find(end_str, start)
                pos = item.find(start_str, start + 1)

                while pos < end and pos != -1:  # Ignore too early </endstr> return
                    tend = item.find(end_str, end + len(end_str))
                    if tend != -1:
                        end = tend
                    pos = item.find(start_str, pos + 1)

                if start == -1 and end == -1:
                    result = ''
                elif start > -1 and end > -1:
                    result = item[start + len(match):end]
                elif end > -1:
                    result = item[:end]
                elif start > -1:
                    result = item[start + len(match):]
                else:
                    result = ''

                if ret:
                    endstr = item[end:item.find(">", item.find(end_str)) + 1]
                    result = match + result + endstr

                result = result.strip()

                item = item[item.find(result, item.find(match)):]
                lst2.append(result)
            lst = lst2
        ret_lst += lst

    return ret_lst


def replaceHTMLCodes(txt):
    txt = re.sub("(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", txt)
    txt = HTMLParser.HTMLParser().unescape(txt)
    txt = txt.replace("&quot;", "\"")
    txt = txt.replace("&amp;", "&")
    txt = txt.strip()
    return txt


def randomagent():
    BR_VERS = [
        ['%s.0' % i for i in xrange(18, 43)],
        ['37.0.2062.103', '37.0.2062.120', '37.0.2062.124', '38.0.2125.101', '38.0.2125.104', '38.0.2125.111', '39.0.2171.71', '39.0.2171.95', '39.0.2171.99', '40.0.2214.93', '40.0.2214.111',
         '40.0.2214.115', '42.0.2311.90', '42.0.2311.135', '42.0.2311.152', '43.0.2357.81', '43.0.2357.124', '44.0.2403.155', '44.0.2403.157', '45.0.2454.101', '45.0.2454.85', '46.0.2490.71',
         '46.0.2490.80', '46.0.2490.86', '47.0.2526.73', '47.0.2526.80'],
        ['11.0']]
    WIN_VERS = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2', 'Windows NT 6.1', 'Windows NT 6.0', 'Windows NT 5.1', 'Windows NT 5.0']
    FEATURES = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
    RAND_UAS = ['Mozilla/5.0 ({win_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
                'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
                'Mozilla/5.0 ({win_ver}{feature}; Trident/7.0; rv:{br_ver}) like Gecko']
    index = random.randrange(len(RAND_UAS))
    return RAND_UAS[index].format(win_ver=random.choice(WIN_VERS), feature=random.choice(FEATURES), br_ver=random.choice(BR_VERS[index]))


def agent():
    return 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'


class cfcookie:
    def __init__(self):
        self.cookie = None


    def get(self, netloc, ua, timeout):
        threads = []

        for i in range(0, 15): threads.append(workers.Thread(self.get_cookie, netloc, ua, timeout))
        [i.start() for i in threads]

        for i in range(0, 30):
            if not self.cookie == None: return self.cookie
            time.sleep(1)


    def get_cookie(self, netloc, ua, timeout):
        try:
            headers = {'User-Agent': ua}

            request = urllib2.Request(netloc, headers=headers)

            try:
                response = urllib2.urlopen(request, timeout=int(timeout))
            except urllib2.HTTPError as response:
                result = response.read(5242880)
                try: encoding = response.info().getheader('Content-Encoding')
                except: encoding = None
                if encoding == 'gzip':
                    result = gzip.GzipFile(fileobj=StringIO.StringIO(result)).read()

            jschl = re.findall('name="jschl_vc" value="(.+?)"/>', result)[0]

            init = re.findall('setTimeout\(function\(\){\s*.*?.*:(.*?)};', result)[-1]

            builder = re.findall(r"challenge-form\'\);\s*(.*)a.v", result)[0]

            decryptVal = self.parseJSString(init)

            lines = builder.split(';')

            for line in lines:

                if len(line) > 0 and '=' in line:

                    sections=line.split('=')
                    line_val = self.parseJSString(sections[1])
                    decryptVal = int(eval(str(decryptVal)+sections[0][-1]+str(line_val)))

            answer = decryptVal + len(urlparse.urlparse(netloc).netloc)

            query = '%s/cdn-cgi/l/chk_jschl?jschl_vc=%s&jschl_answer=%s' % (netloc, jschl, answer)

            if 'type="hidden" name="pass"' in result:
                passval = re.findall('name="pass" value="(.*?)"', result)[0]
                query = '%s/cdn-cgi/l/chk_jschl?pass=%s&jschl_vc=%s&jschl_answer=%s' % (netloc, urllib.quote_plus(passval), jschl, answer)
                time.sleep(6)

            cookies = cookielib.LWPCookieJar()
            handlers = [urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.HTTPCookieProcessor(cookies)]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)

            try:
                request = urllib2.Request(query, headers=headers)
                response = urllib2.urlopen(request, timeout=int(timeout))
            except:
                pass

            cookie = '; '.join(['%s=%s' % (i.name, i.value) for i in cookies])

            if 'cf_clearance' in cookie: self.cookie = cookie
        except:
            pass


    def parseJSString(self, s):
        try:
            offset=1 if s[0]=='+' else 0
            val = int(eval(s.replace('!+[]','1').replace('!![]','1').replace('[]','0').replace('(','str(')[offset:]))
            return val
        except:
            pass


class sucuri:
    def __init__(self):
        self.cookie = None


    def get(self, result):
        try:
            s = re.compile("S\s*=\s*'([^']+)").findall(result)[0]
            s = base64.b64decode(s)
            s = s.replace(' ', '')
            s = re.sub('String\.fromCharCode\(([^)]+)\)', r'chr(\1)', s)
            s = re.sub('\.slice\((\d+),(\d+)\)', r'[\1:\2]', s)
            s = re.sub('\.charAt\(([^)]+)\)', r'[\1]', s)
            s = re.sub('\.substr\((\d+),(\d+)\)', r'[\1:\1+\2]', s)
            s = re.sub(';location.reload\(\);', '', s)
            s = re.sub(r'\n', '', s)
            s = re.sub(r'document\.cookie', 'cookie', s)

            cookie = '' ; exec(s)
            self.cookie = re.compile('([^=]+)=(.*)').findall(cookie)[0]
            self.cookie = '%s=%s' % (self.cookie[0], self.cookie[1])

            return self.cookie
        except:
            pass