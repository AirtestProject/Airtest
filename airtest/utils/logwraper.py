# _*_ coding:UTF-8 _*_

import os
import json
import time
import inspect
import functools
import traceback
from copy import copy
from .logger import get_logger
from .snippet import reg_cleanup
LOGGING = get_logger(__name__)


class AirtestLogger(object):
    """logger """
    def __init__(self, logfile):
        super(AirtestLogger, self).__init__()
        self.running_stack = []
        self.logfile = None
        self.logfd = None
        self.set_logfile(logfile)
        reg_cleanup(self.handle_stacked_log)

    def set_logfile(self, logfile):
        if logfile:
            self.logfile = os.path.realpath(logfile)
            self.logfd = open(self.logfile, "w")
        else:
            # use G.LOGGER.set_logfile(None) to reset logfile
            self.logfile = None
            if self.logfd:
                self.logfd.close()
                self.logfd = None

    @staticmethod
    def _dumper(obj):
        if hasattr(obj, "to_json"):
            return obj.to_json()
        try:
            d = copy(obj.__dict__)
            try:
                d["__class__"] = obj.__class__.__name__
            except AttributeError:
                pass
            return d
        except AttributeError:
            return repr(obj)

    def log(self, tag, data, depth=None, timestamp=None):
        ''' Not thread safe '''
        # LOGGING.debug("%s: %s" % (tag, data))
        if depth is None:
            depth = len(self.running_stack)
        if self.logfd:
            # 如果timestamp为None，或不是float，就设为默认值time.time()
            try:
                timestamp = float(timestamp)
            except (ValueError, TypeError):
                timestamp = time.time()
            try:
                log_data = json.dumps({'tag': tag, 'depth': depth, 'time': timestamp,
                                       'data': data}, default=self._dumper)
            except UnicodeDecodeError:
                # PY2
                log_data = json.dumps({'tag': tag, 'depth': depth, 'time': timestamp,
                                       'data': data}, default=self._dumper, ensure_ascii=False)
            self.logfd.write(log_data + '\n')
            self.logfd.flush()

    def handle_stacked_log(self):
        # 处理stack中的log
        while self.running_stack:
            # 先取最后一个，记了log之后再pop，避免depth错误
            log_stacked = self.running_stack[-1]
            self.log("function", log_stacked)
            self.running_stack.pop()


def Logwrap(f, logger):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # py3 only: def wrapper(*args, depth=None, **kwargs):
        depth = kwargs.pop('depth', None)  # For compatibility with py2
        start = time.time()
        m = inspect.getcallargs(f, *args, **kwargs)
        fndata = {'name': f.__name__, 'call_args': m, 'start_time': start}
        logger.running_stack.append(fndata)
        try:
            res = f(*args, **kwargs)
        except Exception as e:
            data = {"traceback": traceback.format_exc(), "end_time": time.time()}
            fndata.update(data)
            raise
        else:
            fndata.update({'ret': res, "end_time": time.time()})
        finally:
            logger.log('function', fndata, depth=depth)
            logger.running_stack.pop()
        return res
    return wrapper
