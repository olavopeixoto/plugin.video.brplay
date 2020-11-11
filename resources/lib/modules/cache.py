# -*- coding: utf-8 -*-

import re
import hashlib
import time
import datetime
import traceback
import inspect

try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database

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


def get(function, timeout_hour, *args, **kargs):
    # try:
    response = None

    force_refresh = kargs['force_refresh'] if 'force_refresh' in kargs else False
    kargs.pop('force_refresh', None)

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
        kargs.pop('table')
    except:
        table = 'rel_list'

    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.cacheFile)
        dbcur = dbcon.cursor()

        if not force_refresh:
            dbcur.execute("SELECT * FROM %s WHERE func = '%s' AND args = '%s'" % (table, f, a))
            match = dbcur.fetchone()
            if match and len(match) > 3:
                response = pickle.loads(str(match[2]))

                t1 = int(match[3])
                t2 = int(time.time())
                update = timeout_hour and (abs(t2 - t1) / 3600) >= int(timeout_hour)
                if update is False:
                    control.log('RESULT FROM CACHE: %s' % table)
                    return response
                control.log('CACHE EXPIRED')
            else:
                control.log('NO CACHE FOUND')
        else:
            control.log('BYPASSING CACHE')
    except:
        control.log(traceback.format_exc(), control.LOGERROR)
        control.log('NO CACHE FOUND')

    # try:
    start_time = time.time()
    if kargs:
        r = function(*args, **kargs)
    else:
        r = function(*args)
    end_time = time.time()

    if control.log_enabled:
        control.log('EXECUTED (%s.%s) IN %s' % (inspect.getmodule(function).__name__, f, str(datetime.timedelta(seconds=end_time - start_time))))

    if (r is None or r == []) and response is not None:
        return response
    elif r is None or r == []:
        return r
    # except:
    #     return

    control.log('CACHING RESULTS TO %s' % table)

    # try:
    # r = repr(r)
    r_raw = r
    r = pickle.dumps(r, 0)
    t = int(time.time())
    dbcur.execute("CREATE TABLE IF NOT EXISTS %s (""func TEXT, ""args TEXT, ""response BLOB, ""added TEXT, ""UNIQUE(func, args)"");" % table)
    dbcur.execute("DELETE FROM %s WHERE func = '%s' AND args = '%s'" % (table, f, a))
    dbcur.execute("INSERT INTO %s Values (?, ?, ?, ?)" % table, (f, a, buffer(r), t))
    dbcon.commit()
    # except:
    #     pass

    # try:
    # return eval(r.encode('utf-8'))
    return r_raw
    # except:
    #     return eval(r)


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
                control.log(traceback.format_exc(), control.LOGERROR)
    except:
        control.log(traceback.format_exc(), control.LOGERROR)