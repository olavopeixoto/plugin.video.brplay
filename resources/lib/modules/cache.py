# -*- coding: utf-8 -*-

import re,hashlib,time

try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

from resources.lib.modules import control

try:
    import cPickle as pickle
except:
    import pickle

try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    OrderedDict = None


def get(function, timeout, *args, **kargs):
    # try:
    response = None

    f = repr(function)
    f = re.sub('.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', f)

    a = hashlib.md5()
    for i in args: a.update(str(i))
    for key in kargs:
        if key != 'table':
            a.update('%s=%s' % (key, str(kargs[key])))
    a = str(a.hexdigest())
    # except:
    #     pass

    try:
        table = kargs['table']
        kargs.pop('table', None)
    except:
        table = 'rel_list'

    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.cacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT * FROM %s WHERE func = '%s' AND args = '%s'" % (table, f, a))
        match = dbcur.fetchone()

        response = pickle.loads(match[2].encode('utf-8'))

        t1 = int(match[3])
        t2 = int(time.time())
        update = timeout and (abs(t2 - t1) / 3600) >= int(timeout)
        if update is False:
            control.log('RESULT FROM CACHE')
            return response
        control.log('CACHE EXPIRED')
    except:
        control.log('NO CACHE FOUND')
        pass

    # try:
    if kargs:
        r = function(*args, **kargs)
    else:
        r = function(*args)

    if (r is None or r == []) and response is not None:
        return response
    elif r is None or r == []:
        return r
    # except:
    #     return

    # try:
    # r = repr(r)
    r = pickle.dumps(r)
    t = int(time.time())
    dbcur.execute("CREATE TABLE IF NOT EXISTS %s (""func TEXT, ""args TEXT, ""response TEXT, ""added TEXT, ""UNIQUE(func, args)"");" % table)
    dbcur.execute("DELETE FROM %s WHERE func = '%s' AND args = '%s'" % (table, f, a))
    dbcur.execute("INSERT INTO %s Values (?, ?, ?, ?)" % table, (f, a, r, t))
    dbcon.commit()
    # except:
    #     pass

    # try:
    # return eval(r.encode('utf-8'))
    return pickle.loads(r)
    # except:
    #     return eval(r)


def timeout(function, *args, **table):
    try:
        response = None

        f = repr(function)
        f = re.sub('.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', f)

        a = hashlib.md5()
        for i in args: a.update(str(i))
        a = str(a.hexdigest())
    except:
        pass

    try:
        table = table['table']
    except:
        table = 'rel_list'

    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.cacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT * FROM %s WHERE func = '%s' AND args = '%s'" % (table, f, a))
        match = dbcur.fetchone()
        return int(match[3])
    except:
        return


def delete_file():
    control.deleteFile(control.cacheFile)


def clear(table=None):
    try:
        if table is None: table = ['rel_list', 'rel_lib']
        elif not type(table) == list: table = [table]

        dbcon = database.connect(control.cacheFile)
        dbcur = dbcon.cursor()

        for t in table:
            try:
                dbcur.execute("DROP TABLE IF EXISTS %s" % t)
                dbcur.execute("VACUUM")
                dbcon.commit()
            except:
                pass
    except:
        pass