import locale
import threading

from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()
BR_DATESHORT_FORMAT = '%a, %d %b - %Hh%M'


@contextmanager
def setlocale(name):
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        except:
            yield
        finally:
            locale.setlocale(locale.LC_ALL, saved)


def format_datetimeshort(date_time):
    with setlocale('pt_BR'):
        return date_time.strftime(BR_DATESHORT_FORMAT)
