# -*- coding: utf-8 -*-

import time,hashlib

try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

from resources.lib.modules import control


def fetch(items, lang, user):
    try:
        t2 = int(time.time())
        dbcon = database.connect(control.metacacheFile)
        dbcur = dbcon.cursor()
    except:
        return items

    for i in range(0, len(items)):
        try:
            dbcur.execute("SELECT * FROM meta WHERE (imdb = '%s' and lang = '%s' and user = '%s' and not imdb = '0') or (tvdb = '%s' and lang = '%s' and user = '%s' and not tvdb = '0')" % (items[i]['imdb'], lang, user, items[i]['tvdb'], lang, user))
            match = dbcur.fetchone()

            t1 = int(match[5])
            update = (abs(t2 - t1) / 3600) >= 720
            if update == True: raise Exception()

            item = eval(match[4].encode('utf-8'))
            item = dict((k,v) for k, v in item.iteritems() if not v == '0')

            items[i].update(item)
            items[i].update({'metacache': True})
        except:
            pass

    return items


def insert(meta):
    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.metacacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE IF NOT EXISTS meta (""imdb TEXT, ""tvdb TEXT, ""lang TEXT, ""user TEXT, ""item TEXT, ""time TEXT, ""UNIQUE(imdb, tvdb, lang, user)"");")
        t = int(time.time())
        for m in meta:
            try:
                i = repr(m['item'])
                try: dbcur.execute("DELETE * FROM meta WHERE (imdb = '%s' and lang = '%s' and user = '%s' and not imdb = '0') or (tvdb = '%s' and lang = '%s' and user = '%s' and not tvdb = '0')" % (m['imdb'], m['lang'], m['user'], m['tvdb'], m['lang'], m['user']))
                except: pass
                dbcur.execute("INSERT INTO meta Values (?, ?, ?, ?, ?, ?)", (m['imdb'], m['tvdb'], m['lang'], m['user'], i, t))
            except:
                pass

        dbcon.commit()
    except:
        return


def local(items, link, poster, fanart):
    try:
        dbcon = database.connect(control.metaFile())
        dbcur = dbcon.cursor()
        args = [i['imdb'] for i in items]
        dbcur.execute('SELECT * FROM mv WHERE imdb IN (%s)'  % ', '.join(list(map(lambda arg:  "'%s'" % arg, args))))
        data = dbcur.fetchall()
    except:
        return items

    for i in range(0, len(items)):
        try:
            item = items[i]

            match = [x for x in data if x[1] == item['imdb']][0]

            try:
                if poster in item and not item[poster] == '0': raise Exception()
                if match[2] == '0': raise Exception()
                items[i].update({poster: link % ('300', '/%s.jpg' % match[2])})
            except:
                pass
            try:
                if fanart in item and not item[fanart] == '0': raise Exception()
                if match[3] == '0': raise Exception()
                items[i].update({fanart: link % ('1280', '/%s.jpg' % match[3])})
            except:
                pass
        except:
            pass

    return items


