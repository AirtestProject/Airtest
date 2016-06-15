# _*_ coding:UTF-8 _*_
import socket
import time
import platform
import functools
import os


def look_path(program):
    system = platform.system()

    def is_exe(fpath):
        if system.startswith('Windows') and not fpath.lower().endswith('.exe'):
            fpath += '.exe'
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def get_adb_path():
    system = platform.system()
    base_path = os.path.dirname(os.path.realpath(__file__))
    moa_adb_path = {
        "Windows": os.path.join("android", "adb", "windows", "adb.exe"),
        "Darwin": os.path.join("android", "adb", "mac", "adb"),
        "Linux": os.path.join("android", "adb", "linux", "adb")
    }
    moa_adb = os.path.join(base_path, moa_adb_path[system])
    # overwrite uiautomator adb
    if "ANDROID_HOME" in os.environ:
        del os.environ["ANDROID_HOME"]
    os.environ["PATH"] = os.path.dirname(moa_adb) + os.pathsep + os.environ["PATH"]

    return moa_adb


class SafeSocket(object):
    """safe and exact recv & send"""
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.buf = ""

    def connect(self, (host, port)):
        self.sock.connect((host, port))

    def send(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise socket.error("socket connection broken")
            totalsent += sent

    def recv(self, size):
        while len(self.buf) < size:
            trunk = self.sock.recv(min(size-len(self.buf), 4096))
            if trunk == "":
                raise socket.error("socket connection broken")
            self.buf += trunk
        ret, self.buf = self.buf[:size], self.buf[size:]
        return ret

    def recv_with_timeout(self, size, timeout=2):
        self.sock.settimeout(timeout)
        try:
            ret = self.recv(size)
        except socket.timeout:
            ret = None
        finally:
            self.sock.settimeout(None)
        return ret

    def recv_nonblocking(self, size):
        self.sock.settimeout(0)
        try:
            ret = self.recv(size)
        except socket.error, e:
            #10035 no data when nonblocking
            if e.args[0] == 10035: #errno.EWOULDBLOCK: 尼玛errno似乎不一致
                ret = None
            #10053 connection abort by client
            #10054 connection reset by peer
            elif e.args[0] in [10053, 10054]: #errno.ECONNABORTED:
                raise
            else:
                raise
        return ret

    def close(self):
        self.sock.close()


from threading import Thread, Event
from Queue import Queue, Empty


class NonBlockingStreamReader:

    def __init__(self, stream, raise_EOF=False, print_output=True, print_new_line=True):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        raise_EOF: if True, raise an UnexpectedEndOfStream 
                when stream is EOF before kill
        print_output: if True, print when readline
        '''
        self._s = stream
        self._q = Queue()
        self._lastline = None

        def _populateQueue(stream, queue, kill_event):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''
            while not kill_event.is_set():
                line = stream.readline()
                if line:
                    queue.put(line)
                    if print_output:
                        # print only new line 
                        if print_new_line and line == self._lastline:
                            continue
                        self._lastline = line
                        print line.strip()
                        sys.stdout.flush()
                elif kill_event.is_set():
                    break
                elif raise_EOF:
                    raise UnexpectedEndOfStream
                else:
                    print "EndOfStream"
                    break

        self._kill_event = Event()
        self._t = Thread(target=_populateQueue, args=(self._s, self._q, self._kill_event))
        self._t.daemon = True
        self._t.start() #start collecting lines from the stream

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            return None

    def read(self, timeout=0):
        time.sleep(timeout)
        lines = []
        while True:
            line = self.readline()
            if line is None:
                break
            lines.append(line)
        return "".join(lines)

    def kill(self):
        self._kill_event.set()


class UnexpectedEndOfStream(Exception):
    pass


import atexit


def reg_cleanup(func, *args, **kwargs):
    atexit.register(func, *args, **kwargs)


def _isstr(s):
    return isinstance(s, basestring)

def _islist(v):
    return isinstance(v, list) or isinstance(v, tuple)


def retries(max_tries, delay=1, backoff=2, exceptions=(Exception,), hook=None):
    """Function decorator implementing retrying logic.
    delay: Sleep this many seconds * backoff * try number after failure
    backoff: Multiply delay by this factor after each failure
    exceptions: A tuple of exception classes; default (Exception,)
    hook: A function with the signature myhook(tries_remaining, exception);
          default None
    The decorator will call the function up to max_tries times if it raises
    an exception.
    By default it catches instances of the Exception class and subclasses.
    This will recover after all but the most fatal errors. You may specify a
    custom tuple of exception classes with the 'exceptions' argument; the
    function will only be retried if it raises one of the specified
    exceptions.
    Additionally you may specify a hook function which will be called prior
    to retrying with the number of remaining tries and the exception instance;
    see given example. This is primarily intended to give the opportunity to
    log the failure. Hook is not called after failure if no retries remain.
    """
    def dec(func):
        def f2(*args, **kwargs):
            mydelay = delay
            tries = range(max_tries)
            tries.reverse()
            for tries_remaining in tries:
                try:
                   return func(*args, **kwargs)
                except exceptions as e:
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(tries_remaining, e, mydelay)
                        time.sleep(mydelay)
                        mydelay = mydelay * backoff
                    else:
                        raise
                else:
                    break
        return f2
    return dec


import json
import sys
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
        atexit.register(self.handle_stacked_log)

    def set_logfile(self, logfile):
        if logfile is None:
            self.logfile = None
            self.logfd = None
        elif logfile != self.logfile:
            self.logfile = logfile
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
            print tag, data

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
        except Exception:
            data = {"traceback": traceback.format_exc(), "time_used": time.time()-start}
            fndata.update(data)
            fndata.update(LOGGER.extra_log)
            LOGGER.log("error", fndata)
            raise
        else:
            time_used = time.time() - start
            print '>'*len(LOGGER.running_stack), 'Time used:', f.__name__, time_used
            sys.stdout.flush()
            fndata.update({'time_used': time_used, 'ret': res})
            fndata.update(LOGGER.extra_log)
            LOGGER.log('function', fndata)
        finally:
            LOGGER.extra_log = {}
            LOGGER.running_stack.pop()
        return res
    return wrapper




class TargetPos(object):
    """
    点击目标图片的不同位置，默认为中心点0
    1 2 3
    4 0 6
    7 8 9
    """
    LEFTUP, UP, RIGHTUP = 1, 2, 3
    LEFT, MID, RIGHT = 4, 5, 6
    LEFTDOWN, DOWN, RIGHTDOWN = 7, 8, 9

    def getXY(self, cvret, pos):
        if pos == 0 or pos == self.MID:
            return cvret["result"]
        rect = cvret.get("rectangle")
        if not rect:
            print "could not get rectangle, use mid point instead"
            return cvret["result"]
        w = rect[2][0] - rect[0][0]
        h = rect[2][1] - rect[0][1]
        if pos == self.LEFTUP:
            return rect[0]
        elif pos == self.LEFTDOWN:
            return rect[1]
        elif pos == self.RIGHTDOWN:
            return rect[2]
        elif pos == self.RIGHTUP:
            return rect[3]
        elif pos == self.LEFT:
            return rect[0][0], rect[0][1] + h / 2
        elif pos == self.UP:
            return rect[0][0] + w / 2, rect[0][1]
        elif pos == self.RIGHT:
            return rect[2][0], rect[2][1] - h / 2
        elif pos == self.DOWN:
            return rect[2][0] - w / 2, rect[2][1]
        else:
            print "invalid target_pos:%s, use mid point instead" % pos
            return cvret["result"]