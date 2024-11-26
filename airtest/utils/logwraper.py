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
from airtest.core.error import LocalDeviceError
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
            try:
                return obj.to_json()
            except:
                repr(obj)
        try:
            d = copy(obj.__dict__)
            try:
                d["__class__"] = obj.__class__.__name__
            except AttributeError:
                pass
            return d
        except (AttributeError, TypeError):
            # use d = obj.__dict__.copy() to avoid TypeError: can't pickle mappingproxy objects
            # but repr(obj) is simpler in the report
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
            try:
                self.log("function", log_stacked)
            except Exception as e:
                LOGGING.error("log_stacked error: %s" % e)
                LOGGING.error(traceback.format_exc())
            self.running_stack.pop()


def Logwrap(f, logger):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        """
        The decorator @logwrap can record the function call information in the airtest log and display it in the report.
        装饰器@logwrap，能够在airtest的log中记录函数的调用信息，显示在报告中

        The following parameters can be appended to the function parameter definition for additional effect:
        在函数参数定义中可以附加以下参数，以获得更多效果：

        snapshot: snapshot: If True, a snapshot can be attached to the report. 如果为True，可以附加一张截图到报告中
        depth: the depth order of the current log in the log. 指定log中当前log的深度顺序

        Examples:

            @logwrap
            def func1():
                pass

            @logwrap
            def func1(snapshot=True):
                pass

        Args:
            *args:
            **kwargs:

        Returns:


        """
        from airtest.core.cv import try_log_screen
        # py3 only: def wrapper(*args, depth=None, **kwargs):
        depth = kwargs.pop('depth', None)  # For compatibility with py2
        start = time.time()
        m = inspect.getcallargs(f, *args, **kwargs)
        # The snapshot parameter is popped from the function parameter,
        # so the function cannot use the parameter name snapshot later
        snapshot = m.pop('snapshot', False)
        m.pop('self', None)  # remove self from the call_args
        m.pop('cls', None)  # remove cls from the call_args
        fndata = {'name': f.__name__, 'call_args': m, 'start_time': start}
        logger.running_stack.append(fndata)
        try:
            res = f(*args, **kwargs)
        except LocalDeviceError:
            # 为了进入airtools中的远程方法，同时不让LocalDeviceError在报告中显示为失败步骤
            raise LocalDeviceError
        except Exception as e:
            data = {"traceback": traceback.format_exc(), "end_time": time.time()}
            fndata.update(data)
            raise
        else:
            fndata.update({'ret': res, "end_time": time.time()})
            return res
        finally:
            if snapshot is True:
                # If snapshot=True, save an image unless ST.SAVE_IMAGE=False
                try:
                    try_log_screen(depth=len(logger.running_stack) + 1)
                except AttributeError:
                    # if G.DEVICE is None
                    pass
            logger.log('function', fndata, depth=depth)
            try:
                logger.running_stack.pop()
            except IndexError:
                # logger.running_stack is empty
                pass
    return wrapper
