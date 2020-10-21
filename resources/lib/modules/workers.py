# -*- coding: utf-8 -*-

import threading
import sys


class Thread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        self._result = None
        self.killed = False
        threading.Thread.__init__(self)

    def run(self):
        sys.settrace(self.globaltrace)
        self._result = self._target(*self._args)

    def get_result(self):
        return self._result

    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True