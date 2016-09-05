# _*_ coding:UTF-8 _*_
import sys
import time
from threading import Thread, Event
from Queue import Queue, Empty


class NonBlockingStreamReader:

    def __init__(self, stream, raise_EOF=False, print_output=True, print_new_line=True, name=None):
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
        self.name = name or id(self)

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
                        print "[nbsp][%s]%s" % (self.name, repr(line.strip()))
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
