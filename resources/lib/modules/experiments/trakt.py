# -*- coding: utf-8 -*-

import json
import re
import time
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules.experiments import cleandate


def getTrakt(url, post=None):
    try:
        url = urlparse.urljoin('http://api-v2launch.trakt.tv', url)

        headers = {'Content-Type': 'application/json', 'trakt-api-key': 'c029c80fd3d3a5284ee820ba1cf7f0221da8976b8ee5e6c4af714c22fc4f46fa', 'trakt-api-version': '2'}

        if not post == None: post = json.dumps(post)


        if getTraktCredentialsInfo() == False:
            result = client.request(url, post=post, headers=headers)
            return result


        headers['Authorization'] = 'Bearer %s' % control.setting('trakt.token')

        result = client.request(url, post=post, headers=headers, output='extended', error=True)
        if not (result[1] == '401' or result[1] == '405'): return result[0]


        oauth = 'http://api-v2launch.trakt.tv/oauth/token'
        opost = {'client_id': 'c029c80fd3d3a5284ee820ba1cf7f0221da8976b8ee5e6c4af714c22fc4f46fa', 'client_secret': '90a1840447a1e39d350023263902fe7010338d19789e6260f18df56a8b07a68a', 'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob', 'grant_type': 'refresh_token', 'refresh_token': control.setting('trakt.refresh')}

        result = client.request(oauth, post=json.dumps(opost), headers=headers)
        result = json.loads(result)

        token, refresh = result['access_token'], result['refresh_token']

        control.setSetting(id='trakt.token', value=token)
        control.setSetting(id='trakt.refresh', value=refresh)

        headers['Authorization'] = 'Bearer %s' % token

        result = client.request(url, post=post, headers=headers)
        return result
    except:
        pass


def authTrakt():
    try:
        if getTraktCredentialsInfo() == True:
            if control.yesnoDialog(control.lang(32511).encode('utf-8'), control.lang(32512).encode('utf-8'), '', 'Trakt'):
                control.setSetting(id='trakt.user', value='')
                control.setSetting(id='trakt.token', value='')
                control.setSetting(id='trakt.refresh', value='')
            raise Exception()

        result = getTrakt('/oauth/device/code', {'client_id': 'c029c80fd3d3a5284ee820ba1cf7f0221da8976b8ee5e6c4af714c22fc4f46fa'})
        result = json.loads(result)
        verification_url = (control.lang(32513) % result['verification_url']).encode('utf-8')
        user_code = (control.lang(32514) % result['user_code']).encode('utf-8')
        expires_in = int(result['expires_in'])
        device_code = result['device_code']
        interval = result['interval']

        progressDialog = control.progressDialog
        progressDialog.create('Trakt', verification_url, user_code)

        for i in range(0, expires_in):
            try:
                if progressDialog.iscanceled(): break
                time.sleep(1)
                if not float(i) % interval == 0: raise Exception()
                r = getTrakt('/oauth/device/token', {'client_id': 'c029c80fd3d3a5284ee820ba1cf7f0221da8976b8ee5e6c4af714c22fc4f46fa', 'client_secret': '90a1840447a1e39d350023263902fe7010338d19789e6260f18df56a8b07a68a', 'code': device_code})
                r = json.loads(r)
                if 'access_token' in r: break
            except:
                pass

        try: progressDialog.close()
        except: pass

        token, refresh = r['access_token'], r['refresh_token']

        headers = {'Content-Type': 'application/json', 'trakt-api-key': 'c029c80fd3d3a5284ee820ba1cf7f0221da8976b8ee5e6c4af714c22fc4f46fa', 'trakt-api-version': '2', 'Authorization': 'Bearer %s' % token}

        result = client.request('http://api-v2launch.trakt.tv/users/me', headers=headers)
        result = json.loads(result)

        user = result['username']

        control.setSetting(id='trakt.user', value=user)
        control.setSetting(id='trakt.token', value=token)
        control.setSetting(id='trakt.refresh', value=refresh)
        raise Exception()
    except:
        control.openSettings('3.1')


def getTraktCredentialsInfo():
    user = control.setting('trakt.user').strip()
    token = control.setting('trakt.token')
    refresh = control.setting('trakt.refresh')
    if (user == '' or token == '' or refresh == ''): return False
    return True


def getTraktIndicatorsInfo():
    indicators = control.setting('indicators') if getTraktCredentialsInfo() == False else control.setting('indicators.alt')
    indicators = True if indicators == '1' else False
    return indicators


def getTraktAddonMovieInfo():
    try: scrobble = control.addon('script.trakt').getSetting('scrobble_movie')
    except: scrobble = ''
    try: ExcludeHTTP = control.addon('script.trakt').getSetting('ExcludeHTTP')
    except: ExcludeHTTP = ''
    try: authorization = control.addon('script.trakt').getSetting('authorization')
    except: authorization = ''
    if scrobble == 'true' and ExcludeHTTP == 'false' and not authorization == '': return True
    else: return False


def getTraktAddonEpisodeInfo():
    try: scrobble = control.addon('script.trakt').getSetting('scrobble_episode')
    except: scrobble = ''
    try: ExcludeHTTP = control.addon('script.trakt').getSetting('ExcludeHTTP')
    except: ExcludeHTTP = ''
    try: authorization = control.addon('script.trakt').getSetting('authorization')
    except: authorization = ''
    if scrobble == 'true' and ExcludeHTTP == 'false' and not authorization == '': return True
    else: return False


def manager(name, imdb, tvdb, content):
    try:
        post = {"movies": [{"ids": {"imdb": imdb}}]} if content == 'movie' else {"shows": [{"ids": {"tvdb": tvdb}}]}

        items = [(control.lang(32516).encode('utf-8'), '/sync/collection')]
        items += [(control.lang(32517).encode('utf-8'), '/sync/collection/remove')]
        items += [(control.lang(32518).encode('utf-8'), '/sync/watchlist')]
        items += [(control.lang(32519).encode('utf-8'), '/sync/watchlist/remove')]
        items += [(control.lang(32520).encode('utf-8'), '/users/me/lists/%s/items')]

        result = getTrakt('/users/me/lists')
        result = json.loads(result)
        lists = [(i['name'], i['ids']['slug']) for i in result]
        lists = [lists[i//2] for i in range(len(lists)*2)]
        for i in range(0, len(lists), 2):
            lists[i] = ((control.lang(32521) % lists[i][0]).encode('utf-8'), '/users/me/lists/%s/items' % lists[i][1])
        for i in range(1, len(lists), 2):
            lists[i] = ((control.lang(32522) % lists[i][0]).encode('utf-8'), '/users/me/lists/%s/items/remove' % lists[i][1])
        items += lists

        select = control.selectDialog([i[0] for i in items], control.lang(32515).encode('utf-8'))

        if select == -1:
            return
        elif select == 4:
            t = control.lang(32520).encode('utf-8')
            k = control.keyboard('', t) ; k.doModal()
            new = k.getText() if k.isConfirmed() else None
            if (new == None or new == ''): return
            result = getTrakt('/users/me/lists', post={"name": new, "privacy": "private"})

            try: slug = json.loads(result)['ids']['slug']
            except: return control.infoDialog(control.lang(32515).encode('utf-8'), heading=str(name), sound=True, icon='ERROR')
            result = getTrakt(items[select][1] % slug, post=post)
        else:
            result = getTrakt(items[select][1], post=post)

        icon = control.infoLabel('ListItem.Icon') if not result == None else 'ERROR'

        control.infoDialog(control.lang(32515).encode('utf-8'), heading=str(name), sound=True, icon=icon)
    except:
        return


def slug(name):
    name = name.strip()
    name = name.lower()
    name = re.sub('[^a-z0-9_]', '-', name)
    name = re.sub('--+', '-', name)
    return name


def getActivity():
    try:
        result = getTrakt('/sync/last_activities')
        i = json.loads(result)

        activity = []
        activity.append(i['movies']['collected_at'])
        activity.append(i['episodes']['collected_at'])
        activity.append(i['movies']['watchlisted_at'])
        activity.append(i['shows']['watchlisted_at'])
        activity.append(i['seasons']['watchlisted_at'])
        activity.append(i['episodes']['watchlisted_at'])
        activity.append(i['lists']['updated_at'])
        activity.append(i['lists']['liked_at'])
        activity = [int(cleandate.iso_2_utc(i)) for i in activity]
        activity = sorted(activity, key=int)[-1]

        return activity
    except:
        pass


def getWatchedActivity():
    try:
        result = getTrakt('/sync/last_activities')
        i = json.loads(result)

        activity = []
        activity.append(i['movies']['watched_at'])
        activity.append(i['episodes']['watched_at'])
        activity = [int(cleandate.iso_2_utc(i)) for i in activity]
        activity = sorted(activity, key=int)[-1]

        return activity
    except:
        pass


def cachesyncMovies(timeout=0):
    indicators = cache.get(syncMovies, timeout, control.setting('trakt.user').strip(), table='trakt')
    return indicators


def timeoutsyncMovies():
    timeout = cache.timeout(syncMovies, control.setting('trakt.user').strip(), table='trakt')
    return timeout


def syncMovies(user):
    try:
        if getTraktCredentialsInfo() == False: return
        indicators = getTrakt('/users/me/watched/movies')
        indicators = json.loads(indicators)
        indicators = [i['movie']['ids'] for i in indicators]
        indicators = [str(i['imdb']) for i in indicators if 'imdb' in i]
        return indicators
    except:
        pass


def cachesyncTVShows(timeout=0):
    indicators = cache.get(syncTVShows, timeout, control.setting('trakt.user').strip(), table='trakt')
    return indicators


def timeoutsyncTVShows():
    timeout = cache.timeout(syncTVShows, control.setting('trakt.user').strip(), table='trakt')
    return timeout


def syncTVShows(user):
    try:
        if getTraktCredentialsInfo() == False: return
        indicators = getTrakt('/users/me/watched/shows?extended=full')
        indicators = json.loads(indicators)
        indicators = [(i['show']['ids']['tvdb'], i['show']['aired_episodes'], sum([[(s['number'], e['number']) for e in s['episodes']] for s in i['seasons']], [])) for i in indicators]
        indicators = [(str(i[0]), int(i[1]), i[2]) for i in indicators]
        return indicators
    except:
        pass


def syncSeason(imdb):
    try:
        if getTraktCredentialsInfo() == False: return
        indicators = getTrakt('/shows/%s/progress/watched?specials=false&hidden=false' % imdb)
        indicators = json.loads(indicators)['seasons']
        indicators = [(i['number'], [x['completed'] for x in i['episodes']]) for i in indicators]
        indicators = ['%01d' % int(i[0]) for i in indicators if not False in i[1]]
        return indicators
    except:
        pass


def markMovieAsWatched(imdb):
    if not imdb.startswith('tt'): imdb = 'tt' + imdb
    return getTrakt('/sync/history', {"movies": [{"ids": {"imdb": imdb}}]})


def markMovieAsNotWatched(imdb):
    if not imdb.startswith('tt'): imdb = 'tt' + imdb
    return getTrakt('/sync/history/remove', {"movies": [{"ids": {"imdb": imdb}}]})


def markTVShowAsWatched(tvdb):
    return getTrakt('/sync/history', {"shows": [{"ids": {"tvdb": tvdb}}]})


def markTVShowAsNotWatched(tvdb):
    return getTrakt('/sync/history/remove', {"shows": [{"ids": {"tvdb": tvdb}}]})


def markEpisodeAsWatched(tvdb, season, episode):
    season, episode = int('%01d' % int(season)), int('%01d' % int(episode))
    return getTrakt('/sync/history', {"shows": [{"seasons": [{"episodes": [{"number": episode}], "number": season}], "ids": {"tvdb": tvdb}}]})


def markEpisodeAsNotWatched(tvdb, season, episode):
    season, episode = int('%01d' % int(season)), int('%01d' % int(episode))
    return getTrakt('/sync/history/remove', {"shows": [{"seasons": [{"episodes": [{"number": episode}], "number": season}], "ids": {"tvdb": tvdb}}]})


def getMovieTranslation(id, lang):
    url = '/movies/%s/translations/%s' % (id, lang)
    try: return json.loads(getTrakt(url))[0]['title'].encode('utf-8')
    except: pass


def getTVShowTranslation(id, lang):
    url = '/shows/%s/translations/%s' % (id, lang)
    try: return json.loads(getTrakt(url))[0]['title'].encode('utf-8')
    except: pass


def getMovieSummary(id):
    return getTrakt('/movies/%s' % id)


def getTVShowSummary(id):
    return getTrakt('/shows/%s' % id)


