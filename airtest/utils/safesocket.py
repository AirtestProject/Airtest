# _*_ coding:UTF-8 _*_
import socket
import errno


class SafeSocket(object):
    """safe and exact recv & send"""
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.buf = b""

    def __enter__(self):
        try:
            return self.sock.__enter__()
        except AttributeError:
            return self.sock

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            return self.sock.__exit__(exc_type, exc_val, exc_tb)
        except AttributeError:
            self.sock.close()

    # PEP 3113 -- Removal of Tuple Parameter Unpacking
    # https://www.python.org/dev/peps/pep-3113/
    def connect(self, tuple_hp):
        host, port = tuple_hp
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
            if trunk == b"":
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
        except(socket.error) as e:
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
        if hasattr(self.sock, "_closed") and not self.sock._closed:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                if e.errno != errno.ENOTCONN:  # 'Socket is not connected'
                    raise
            self.sock.close()
        else:
            self.sock.close()
