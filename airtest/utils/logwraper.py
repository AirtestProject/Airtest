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

    def log(self, tag, data, depth=None):
        ''' Not thread safe '''
        # LOGGING.debug("%s: %s" % (tag, data))
        if depth is None:
            depth = len(self.running_stack)

        if self.logfd:
            if not isinstance(data.get('name', ''), str):
                if isinstance(data.get('name', ''), Exception):
                    data['traceback'] = data['name'].message
                    data['name'] = data['name'].__class__.__name__
                else:
                    raise AssertionError("TypeError: message must be str or Exception")
            log_data = json.dumps({'tag': tag, 'depth': depth, 'time': time.time(), 'data': data}, default=self._dumper)
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
            logger.log('function', fndata)
            logger.running_stack.pop()
        return res
    return wrapper
