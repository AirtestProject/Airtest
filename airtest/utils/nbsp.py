# _*_ coding:UTF-8 _*_
import time
from threading import Thread, Event
from six.moves import queue
from .logger import get_logger
LOGGING = get_logger(__name__)


class NonBlockingStreamReader:

    def __init__(self, stream, raise_EOF=False, print_output=True, print_new_line=True, name=None, auto_kill=False):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        raise_EOF: if True, raise an UnexpectedEndOfStream
                when stream is EOF before kill
        print_output: if True, print when readline
        '''
        self._s = stream
        self._q = queue.Queue()
        self._lastline = None
        self.name = name or id(self)

        def _populateQueue(stream, queue, kill_event):
            '''
            Collect lines from 'stream' and put them in 'queue'.
            '''
            while not kill_event.is_set():
                line = stream.readline()
                if line is not None:
                    queue.put(line)
                    if print_output:
                        # print only new line
                        if print_new_line and line == self._lastline:
                            continue
                        self._lastline = line
                        LOGGING.debug("[%s]%s" % (self.name, repr(line.strip())))
                    if auto_kill and line == b"":
                        self.kill()
                elif kill_event.is_set():
                    break
                elif raise_EOF:
                    raise UnexpectedEndOfStream
                else:
                    break

        self._kill_event = Event()
        self._t = Thread(target=_populateQueue, args=(self._s, self._q, self._kill_event), name="nbsp_%s"%self.name)
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except queue.Empty:
            return None

    def read(self, timeout=0):
        time.sleep(timeout)
        lines = []
        while True:
            line = self.readline()
            if line is None:
                break
            lines.append(line)
        return b"".join(lines)

    def kill(self):
        self._kill_event.set()


class UnexpectedEndOfStream(Exception):
    pass
