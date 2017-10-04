# -*- coding: UTF-8 -*-

import datetime
import re
import requests
import urlparse
from resources.lib.modules import control

try:
    import HTMLParser
except:
    import html.parser as HTMLParser

try:
    import cPickle as pickle
except:
    import pickle

class auth:

    ENDPOINT_URL = None
    PROVIDER_ID = None

    OAUTH_URL = 'http://globosatplay.globo.com/-/auth/gplay/'
    GLOBOSAT_CREDENTIALS = 'globosat_credentials'

    def __init__(self):
        self.session = requests.Session()
        try:
            self.proxy = control.proxy_url
            self.proxy = None if self.proxy is None or self.proxy == '' else {
                                                                  'http': self.proxy,
                                                                  'https': self.proxy,
                                                                }
            if self.proxy is not None: control.log("proxy: %s" % self.proxy)
            if self.GLOBOSAT_CREDENTIALS:
                credentials = control.setting(self.GLOBOSAT_CREDENTIALS)
                control.log("Loaded credentials from: %s" % self.GLOBOSAT_CREDENTIALS)
                self.credentials = pickle.loads(credentials)
            else:
                self.credentials = {}
        except:
            self.credentials = {}

    def clearCredentials(self):
        if self.GLOBOSAT_CREDENTIALS:
            control.setSetting(self.GLOBOSAT_CREDENTIALS, None)
        self.credentials = {}

    def get_token(self, username, password, select_profile=True):
        #token should not vary by provider, return first valid one if cached
        if len(self.credentials) > 0:
            token_key = "token_%s" % str(self.PROVIDER_ID)
            session_key = "sessionId_%s" % str(self.PROVIDER_ID)
            token_key = next((x for x in self.credentials.keys() if x == token_key), None)
            session_key = next((x for x in self.credentials.keys() if x == session_key), None)
            if token_key != None:
                token = self.credentials[token_key]
                sessionId = self.credentials[session_key] if session_key in self.credentials else None
                control.log("returning cached token: %s" % token)
                if not sessionId is None:
                    control.log("returning cached session key: %s" % sessionId)
                return token, sessionId

        control.log("requesting token from provider: %s (%s)" % (self.PROVIDER_ID,self.OAUTH_URL))

        # get a client_id token
        r1 = self.session.get(self.OAUTH_URL, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'}, verify=False)

        # get backend url
        r2 = self.session.post(r1.url + '&duid=None', data={'config': self.PROVIDER_ID}, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'}, verify=False)

        url, qs = r2.url.split('?', 1)

        # provider authentication
        try:
            r3 = self._provider_auth(url, urlparse.parse_qs(qs), username, password, r2.text)
        except Exception as e:
            self.error(str(e))
            return None, None

        # set profile
        urlp, qp = r3.url.split('?', 1)

        if select_profile:
            sessionId = None
            token = self._select_profile(urlp, r3.text)
        else:
            control.log('COOKIES: %s' % repr(dict(r3.cookies)))

            # control.log('VERIFYING HISTORY: %s' % pickle.dumps(r3))
            # if r3.history:
            #     control.log('HAS HISTORY (%s): %s' % (len(r3.history), repr(r3.history)))
            #     last_response = r3.history[-1]
            #     control.log('HISTORY COOKIES: %s' % dict(last_response.cookies))

            sessionId = dict(r3.cookies)['sexyhotplay_sessionid']
            token = qp.replace('code=', '')

        self.credentials.update({
            ("token_%s" % str(self.PROVIDER_ID)): token,
            ("sessionId_%s" % str(self.PROVIDER_ID)): sessionId
        })
        self._save_credentials()

        if sessionId is not None:
            control.log('SESSION_KEY: %s' % sessionId)
        control.log('TOKEN: %s' % token)

        return token, sessionId

    def _select_profile(self, urlp, html):
        try:
            accesstoken = re.findall('<form id="bogus-form" action="/perfis/selecionar/\?access_token=(.*)" method="POST">', html)[0]
            post_data = {
                '_method': 'PUT',
                'duid': 'None',
                'perfil_id': re.findall('<div data-id="(\d+)" class="[\w ]+avatar', html)[0]
            }

            r4 = self.session.post(urlp + '?access_token=' + accesstoken, data=post_data, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'}, verify=False)

            # build credentials
            credentials = dict(r4.cookies)

            return credentials[credentials['b64globosatplay']]
        except Exception as ex:
            raise Exception('There was a problem in the authetication process. - %s' % repr(ex))

    def _authenticate(self, provider_id, username, password, select_profile):

        token, sessionKey = self.get_token(username, password, select_profile)

        now = datetime.datetime.now()
        expiration = now + datetime.timedelta(days=7)

        providerkey = "WMPTOKEN_%s" % provider_id
        expirationkey = providerkey + '_expiration'

        return {
            providerkey: token,
            expirationkey: expiration
        }

    def _save_credentials(self):
        if self.GLOBOSAT_CREDENTIALS:
            control.log("Saving credentials with key: %s" % self.GLOBOSAT_CREDENTIALS)
            control.setSetting(self.GLOBOSAT_CREDENTIALS, pickle.dumps(self.credentials))

    def is_authenticated(self, provider_id):
        for key in self.credentials.keys():
            if key.endswith(provider_id) and self.credentials[key] is not None and (key + "_expiration") in self.credentials.keys():
                if self.credentials[key + "_expiration"] > datetime.datetime.now():
                    return True
                try:
                    self.credentials.pop(key, None)
                    self.credentials.pop(key + "_expiration", None)
                    self.credentials.pop("token_%" % str(self.PROVIDER_ID), None)
                except:
                    pass
                return False

        return False

    def authenticate(self, provider_id, username, password, select_profile=True):

        if not self.is_authenticated(provider_id) and (username and password):
            control.log('username/password set. trying to authenticate')

            credentials = self._authenticate(provider_id, username, password, select_profile)

            self.credentials.update(credentials)

            if self.is_authenticated(provider_id):
                control.log('successfully authenticated')
                self._save_credentials()
            else:
                control.log('wrong username or password')
                control.infoDialog('[%s] %s' % (self.__class__.__name__, control.infoLabel(32003)), icon='ERROR')
                pass
        elif self.is_authenticated(provider_id):
            control.log('already authenticated')
            pass
        else:
            control.log('no username set to authenticate')
            pass

        control.log("credentials: %s" % repr(self.credentials))

        credentials_cookie = {}

        for key in self.credentials.keys():
            if key.endswith(provider_id):
                credentials_cookie.update({
                    key: self.credentials[key]
                })

        control.log("credentials_cookie: %s" % repr(credentials_cookie))

        return credentials_cookie

    def error(self, msg):
        control.log("ERROR AUTH: %s" % msg)
        control.infoDialog('[%s] %s' % (self.__class__.__name__, msg), 'ERROR')


class net(auth):
    PROVIDER_ID = 64

    def _provider_auth(self, url, qs, username, password, html):
        qs.update({
            '_submit.x': '126',
            '_submit.y': '18',
            '_submit': 'entrar',
            'username': username,
            'password': password,
            'passwordHint': '',
            'Auth_method': 'UP',
        })
        url = 'https://auth.netcombo.com.br/login'
        return self.session.post(url, data=qs, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})


class tv_oi(auth):
    PROVIDER_ID = 66

    def _provider_auth(self, url, qs, username, password, html):

        url += '?sid=0'
        # prepare auth
        r = self.session.post(url + '&id=tve&option=credential', proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})

        # authenticate
        post_data = {
            'option': 'credential',
            'urlRedirect': url,
            'Ecom_User_ID': username,
            'Ecom_Password': password,
        }
        r1 = self.session.post(url, data=post_data, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})

        r2 = self.session.get(url, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})

        try:
            html_parser = HTMLParser.HTMLParser()
            redirurl = re.findall(r'<form method=\"POST\" enctype=\"application/x-www-form-urlencoded\" action=\"(.*)\">', r2.text)[0]
            argsre = dict([(match.group(1), html_parser.unescape(match.group(2))) for match in re.finditer(r'<input type=\"hidden\" name=\"(\w+)\" value=\"([^\"]+)\"/>', r2.text)])

            return self.session.post(redirurl, data=argsre, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})
        except:
            raise Exception('Invalid user name or password.')


class sky(auth):
    PROVIDER_ID = 80

    def _provider_auth(self, url, qs, username, password, html):
        qs.update({
            'login': username,
            'senha': password,
            'clientId': '',
        })
        url = 'http://www1.skyonline.com.br/Modal/Logar'
        req = self.session.post(url, data=qs, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})
        match = re.search('^"(http.*)"$', req.text)
        if match:
            return self.session.get(match.group(1).replace("\u0026","&"), proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})

        raise Exception('Invalid user name or password.')


class vivo(auth):
    PROVIDER_ID = 147

    def _provider_auth(self, url, qs, username, password, html):
        nova_url = re.findall('var urlString = \'(.*)\';', html)[0]
        r2 = self.session.get(nova_url, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})
        url, qs = r2.url.split('?', 1)
        qs = urlparse.parse_qs(qs)

        cpf = username
        if len(cpf) == 11:
            cpf = "%s.%s.%s-%s" % (cpf[0:3], cpf[3:6], cpf[6:9], cpf[9:11])
        qs.update({
            'user_Doc': cpf,
            'password': password,
            'password_fake': None,
        })
        req = self.session.post(url, data=qs, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})
        nova_url = re.findall('var urlString = \'(.*)\';', req.text)[0]
        ret_req = self.session.get(nova_url, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})
        return ret_req


class claro(auth):
    PROVIDER_ID = 123

    def _provider_auth(self, url, qs, username, password, html):
        qs.update({
            'cpf': username,
            'senha': password,
        })
        req = self.session.post(url, data=qs, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})
        ipt_values_regex = r'%s=["\'](.*)["\'] '
        try:
            action = re.findall(ipt_values_regex % 'action', req.text)[0]
            value = re.findall(ipt_values_regex[:-1] % 'value', req.text)[0]
        except IndexError:
            raise Exception('Invalid user name or password.')
        return req


class globosat_guest(auth):
    PROVIDER_ID = 50

    def _provider_auth(self, url, qs, username, password, html):
        qs.update({
            'login': username,
            'senha': password,
        })
        req = self.session.post(url, data=qs, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})
        ipt_values_regex = r'%s=["\'](.*)["\'] '
        try:
            action = re.findall(ipt_values_regex % 'action', req.text)[0]
            value = re.findall(ipt_values_regex[:-1] % 'value', req.text)[0]
        except IndexError:
            raise Exception('Invalid user name or password.')
        return req


#incomplete
class multiplay(auth):
    PROVIDER_ID = 63

    def _provider_auth(self, url, qs, username, password, html):

        token_regex = re.match(r'<input type="hidden" name="_token" value="([^"]+)">', html)

        token = token_regex.groups()[0]
        qs.update({
            '_token': token,
            'username': username,
            'password': password
        })

        return self.session.post(url, data=qs, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})


#incomplete
class orm_cabo(auth):
    PROVIDER_ID = 138

    def _provider_auth(self, url, qs, username, password, html):

        qs.update({
            'cpf': username,
            'senha': password
        })

        return self.session.post(url, data=qs, proxies=self.proxy, headers={'Accept-Encoding': 'gzip'})