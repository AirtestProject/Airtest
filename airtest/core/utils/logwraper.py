# _*_ coding:UTF-8 _*_
import os
import sys
import json
import time
import functools
import traceback


class MoaLogger(object):
    """logger """
    def __init__(self, logfile, debug=False):
        super(MoaLogger, self).__init__()
        self.logfile = None
        self.logfd = None
        self.debug = debug
        self.running_stack = []
        self.extra_log = {}
        self.set_logfile(logfile)
        # atexit.register(self.handle_stacked_log)

    def set_logfile(self, logfile):
        if logfile is None:
            self.logfile = None
            self.logfd = None
        else:
            self.handle_stacked_log()
            self.logfile = os.path.realpath(logfile)
            self.logfd = open(self.logfile, "w")

    @staticmethod
    def _dumper(obj):
        try:
            return obj.__dict__
        except:
            return None

    def log(self, tag, data, in_stack=True):
        ''' Not thread safe '''
        if self.debug:
            print(tag, data)

        if in_stack:
            depth = len(self.running_stack)
        else:
            depth = 1

        if self.logfd:
            self.logfd.write(json.dumps({'tag': tag, 'depth': depth, 'time': time.strftime("%Y-%m-%d %H:%M:%S"), 'data': data}, default=self._dumper) + '\n')
            self.logfd.flush()

    def handle_stacked_log(self):
        # 处理stack中的log
        while self.running_stack:
            # 先取最后一个，记了log之后再pop，避免depth错误
            log_stacked = self.running_stack[-1]
            self.log("function", log_stacked)
            self.running_stack.pop()


def Logwrap(f, logger):
    LOGGER = logger

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        fndata = {'name': f.__name__, 'args': args, 'kwargs': kwargs}
        LOGGER.running_stack.append(fndata)
        try:
            res = f(*args, **kwargs)
        except Exception, e:
            data = {"traceback": traceback.format_exc(), "time_used": time.time()-start, "error_str": str(e)}
            fndata.update(data)
            fndata.update(LOGGER.extra_log)
            LOGGER.log("error", fndata)
            LOGGER.running_stack.pop()
            raise
        else:
            time_used = time.time() - start
            print('>'*len(LOGGER.running_stack), f.__name__, 'Time used:', "%.3f" % time_used, "s")
            sys.stdout.flush()
            fndata.update({'time_used': time_used, 'ret': res})
            fndata.update(LOGGER.extra_log)
            LOGGER.log('function', fndata)
            LOGGER.running_stack.pop()
        finally:
            LOGGER.extra_log = {}
        return res
    return wrapper
