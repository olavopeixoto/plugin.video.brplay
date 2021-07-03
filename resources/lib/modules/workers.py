# -*- coding: utf-8 -*-

import threading
import sys
import traceback
from Queue import Queue


class Thread(threading.Thread):
    def __init__(self, target, *args):
        threading.Thread.__init__(self)
        self._target = target
        self._args = args
        self._result = None
        self.killed = False

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


class Workers:
    def __init__(self, concurrent=30, queue_size=None, target=None, expect_result=True):
        self.concurrent = concurrent
        q_size = queue_size or concurrent * 2
        self.queue = Queue(q_size)
        self.KILL_SIGNAL = None

        def _queue_worker():
            while True:
                try:
                    args = self.queue.get()
                    if args == self.KILL_SIGNAL:
                        break

                    result_list = args[-1:][0] if expect_result else None
                    processing_target = target or args[0]
                    start_index = 1 if not target else None
                    last_index = -1 if expect_result else None
                    args = args[start_index:last_index]
                    try:
                        result = processing_target(*args)
                        if result_list is not None:
                            result_list.append(result)
                    except:
                        if target:
                            print(target.__name__)
                        else:
                            print('target: %s' % target)
                        print(args)
                        traceback.print_exc()
                finally:
                    self.queue.task_done()

        for i in range(concurrent):
            t = Thread(_queue_worker)
            t.daemon = True
            t.start()

    def put(self, item):
        self.queue.put(item)

    def join(self):
        self.queue.join()

    def terminate(self):
        for i in range(self.concurrent):
            self.queue.put(self.KILL_SIGNAL)
