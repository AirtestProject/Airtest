#!/usr/bin/python
# -*- coding: utf-8 -*-
# Use python to forward the iOS mobile phone port
# refer to: http://iphonedevwiki.net/index.php/SSH_Over_USB
# https://github.com/nabla-c0d3/multcprelay
# 通过Python对iOS端口进行转发，可以参考网上的tcprelay代码，或是tidevice的relay.py（使用了tornado）
import socketserver as SocketServer
import select
import sys
import threading
from optparse import OptionParser
from airtest.utils.logger import get_logger


LOGGING = get_logger(__name__)


class SocketRelay(object):
    def __init__(self, a, b, maxbuf=65535):
        self.a = a
        self.b = b
        self.atob = b""
        self.btoa = b""
        self.maxbuf = maxbuf

    def handle(self):
        while True:
            rlist = []
            wlist = []
            xlist = [self.a, self.b]
            if self.atob:
                wlist.append(self.b)
            if self.btoa:
                wlist.append(self.a)
            if len(self.atob) < self.maxbuf:
                rlist.append(self.a)
            if len(self.btoa) < self.maxbuf:
                rlist.append(self.b)
            rlo, wlo, xlo = select.select(rlist, wlist, xlist)
            if xlo:
                return
            if self.a in wlo:
                n = self.a.send(self.btoa)
                self.btoa = self.btoa[n:]
            if self.b in wlo:
                n = self.b.send(self.atob)
                self.atob = self.atob[n:]
            if self.a in rlo:
                s = self.a.recv(self.maxbuf - len(self.atob))
                if not s:
                    return
                self.atob += s
            if self.b in rlo:
                s = self.b.recv(self.maxbuf - len(self.btoa))
                if not s:
                    return
                self.btoa += s


class TCPRelay(SocketServer.BaseRequestHandler):
    def handle(self):
        dev = self.server.device
        dsock = dev.create_inner_connection(self.server.rport)._sock
        lsock = self.request
        LOGGING.info("Connection established, relaying data")
        try:
            fwd = SocketRelay(dsock, lsock, self.server.bufsize * 1024)
            fwd.handle()
        finally:
            dsock.close()
            lsock.close()
        LOGGING.info("Connection closed")


class TCPServer(SocketServer.TCPServer):
    allow_reuse_address = True


class ThreadedTCPServer(SocketServer.ThreadingMixIn, TCPServer):
    # 显式指定为True，否则脚本运行完毕时，因为连接没有断开，导致线程不会终止
    daemon_threads = True


if __name__ == '__main__':
    """
    本文件可以在usb仅插入一台iOS手机时，执行命令行：python relay.py -t 5001:5001
    """
    from wda.usbmux import Usbmux
    HOST = "localhost"

    parser = OptionParser(usage="usage: %prog [OPTIONS] RemotePort[:LocalPort] [RemotePort[:LocalPort]]...")
    parser.add_option("-t", "--threaded", dest='threaded', action='store_true', default=False, help="use threading to handle multiple connections at once")
    parser.add_option("-b", "--bufsize", dest='bufsize', action='store', metavar='KILOBYTES', type='int', default=128, help="specify buffer size for socket forwarding")
    parser.add_option("-s", "--socket", dest='sockpath', action='store', metavar='PATH', type='str', default=None, help="specify the path of the usbmuxd socket")

    options, args = parser.parse_args()

    serverclass = TCPServer
    if options.threaded:
        serverclass = ThreadedTCPServer

    if len(args) == 0:
        parser.print_help()
        sys.exit(1)

    ports = []

    for arg in args:
        try:
            if ':' in arg:
                rport, lport = arg.split(":")
                rport = int(rport)
                lport = int(lport)
                ports.append((rport, lport))
            else:
                ports.append((int(arg), int(arg)))
        except:
            parser.print_help()
            sys.exit(1)

    servers=[]

    for rport, lport in ports:
        LOGGING.info("Forwarding local port %d to remote port %d"%(lport, rport))
        server = serverclass((HOST, lport), TCPRelay)
        # 当前仅有一台iOS手机连接usb时
        dev_uuid = Usbmux().get_single_device_udid()
        dev = Usbmux().device(dev_uuid)
        server.rport = rport
        server.device = dev
        server.bufsize = options.bufsize
        servers.append(server)

    alive = True

    while alive:
        # sleep(1)
        try:
            rl, wl, xl = select.select(servers, [], [])
            for server in rl:
                server.handle_request()
        except:
            alive = False
