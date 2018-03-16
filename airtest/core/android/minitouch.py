# -*- coding: utf-8 -*-
import os
import sys
import re
import time
import socket
import threading
import warnings
from airtest.core.error import MinitouchError
from airtest.core.android.constant import STFLIB
from airtest.utils.compat import queue
from airtest.utils.safesocket import SafeSocket
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.snippet import reg_cleanup, get_std_encoding, on_method_ready, ready_method
from airtest.utils.logger import get_logger
LOGGING = get_logger(__name__)


class Minitouch(object):
    """
    Super fast operation from minitouch

    References:
    https://github.com/openstf/minitouch
    """

    def __init__(self, adb, backend=False):
        self.adb = adb
        self.backend = backend
        self.server_proc = None
        self.client = None
        self.display_info = None
        self.max_x, self.max_y = None, None
        reg_cleanup(self.teardown)

    @ready_method
    def install_and_setup(self):
        """
        Install and setup minitouch

        Returns:
            None

        """
        self.install()
        self.display_info = self.adb.display_info
        self.setup_server()
        if self.backend:
            self.setup_client_backend()
        else:
            self.setup_client()

    def uninstall(self):
        """
        Uninstall minitouch

        Returns:
            None

        """
        self.adb.raw_shell("rm /data/local/tmp/minitouch*")

    def install(self):
        """
        Install minitouch

        Returns:
            None

        """
        if self.adb.exists_file('/data/local/tmp/minitouch'):
            LOGGING.debug("install_minitouch skipped")
            return

        abi = self.adb.getprop("ro.product.cpu.abi")
        sdk = int(self.adb.getprop("ro.build.version.sdk"))

        if sdk >= 16:
            binfile = "minitouch"
        else:
            binfile = "minitouch-nopie"

        device_dir = "/data/local/tmp"
        path = os.path.join(STFLIB, abi, binfile).replace("\\", r"\\")
        self.adb.push(path, "%s/minitouch" % device_dir)
        self.adb.shell("chmod 755 %s/minitouch" % (device_dir))
        LOGGING.info("install_minitouch finished")

    def __transform_xy(self, x, y):
        """
        Transform coordinates (x, y) according to the device display

        Args:
            x: coordinate x
            y: coordinate y

        Returns:
            transformed coordinates (x, y)

        """
        if not (self.display_info and self.display_info['max_x'] and self.display_info['max_y']):
            return x, y

        width, height = self.display_info['physical_width'], self.display_info['physical_height']
        if width > height and self.display_info['orientation'] in [1, 3]:
            width, height = height, width

        nx = x * self.max_x / width
        ny = y * self.max_y / height
        return nx, ny

    def setup_server(self):
        """
        Setip minitouch server and adb forward

        Returns:
            server process

        """
        if self.server_proc:
            self.server_proc.kill()
            self.server_proc = None

        self.localport, deviceport = self.adb.setup_forward("localabstract:minitouch_{}".format)
        deviceport = deviceport[len("localabstract:"):]
        p = self.adb.start_shell("/data/local/tmp/minitouch -n '%s' 2>&1" % deviceport)
        nbsp = NonBlockingStreamReader(p.stdout, name="minitouch_server")
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("minitouch setup timeout")

            line = line.decode(get_std_encoding(sys.stdout))

            # 识别出setup成功的log，并匹配出max_x, max_y
            m = re.match("Type \w touch device .+ \((\d+)x(\d+) with \d+ contacts\) detected on .+ \(.+\)", line)
            if m:
                self.max_x, self.max_y = int(m.group(1)), int(m.group(2))
                break
            else:
                self.max_x = 32768
                self.max_y = 32768
        # nbsp.kill() # 保留，不杀了，后面还会继续读取并pirnt
        if p.poll() is not None:
            # server setup error, may be already setup by others
            # subprocess exit immediately
            raise RuntimeError("minitouch server quit immediately")
        self.server_proc = p
        # reg_cleanup(self.server_proc.kill)
        return p

    @on_method_ready('install_and_setup')
    def touch(self, tuple_xy, duration=0.01):
        """
        Perform touch event


        minitouch protocol example::

            d 0 10 10 50
            c
            <wait in your own code>
            u 0
            c

        Args:
            tuple_xy: coordinates (x, y)
            duration: time interval for touch event, default is 0.01

        Returns:
            None

        """
        x, y = tuple_xy
        x, y = self.__transform_xy(x, y)
        self.handle(b"d 0 %d %d 50\nc\n" % (x, y))
        time.sleep(duration)
        self.handle(b"u 0\nc\n")

    @on_method_ready('install_and_setup')
    def swipe(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5):
        """
        Perform swipe event

        minitouch protocol example::

            d 0 0 0 50
            c
            m 0 20 0 50
            c
            m 0 40 0 50
            c
            m 0 60 0 50
            c
            m 0 80 0 50
            c
            m 0 100 0 50
            c
            u 0
            c

        Args:
            tuple_from_xy: start point
            tuple_to_xy: end point
            duration: time interval for swipe duration, default is 0.8
            steps: size of swipe step, default is 5

        Returns:
            None

        """
        from_x, from_y = tuple_from_xy
        to_x, to_y = tuple_to_xy

        from_x, from_y = self.__transform_xy(from_x, from_y)
        to_x, to_y = self.__transform_xy(to_x, to_y)

        interval = float(duration) / (steps + 1)
        self.handle(b"d 0 %d %d 50\nc\n" % (from_x, from_y))
        time.sleep(interval)
        for i in range(1, steps):
            self.handle(b"m 0 %d %d 50\nc\n" % (
                from_x + (to_x - from_x) * i / steps,
                from_y + (to_y - from_y) * i / steps,
            ))
            time.sleep(interval)
        for i in range(10):
            self.handle(b"m 0 %d %d 50\nc\n" % (to_x, to_y))
        time.sleep(interval)
        self.handle(b"u 0\nc\n")

    @on_method_ready('install_and_setup')
    def pinch(self, center=None, percent=0.5, duration=0.5, steps=5, in_or_out='in'):
        """
        Perform pinch action

        minitouch protocol example::

            d 0 0 100 50
            d 1 100 0 50
            c
            m 0 10 90 50
            m 1 90 10 50
            c
            m 0 20 80 50
            m 1 80 20 50
            c
            m 0 20 80 50
            m 1 80 20 50
            c
            m 0 30 70 50
            m 1 70 30 50
            c
            m 0 40 60 50
            m 1 60 40 50
            c
            m 0 50 50 50
            m 1 50 50 50
            c
            u 0
            u 1
            c
        """
        w, h = self.display_info['width'], self.display_info['height']
        if isinstance(center, (list, tuple)):
            x0, y0 = center
        elif center is None:
            x0, y0 = w / 2, h / 2
        else:
            raise RuntimeError("center should be None or list/tuple, not %s" % repr(center))

        x1, y1 = x0 - w * percent / 2, y0 - h * percent / 2
        x2, y2 = x0 + w * percent / 2, y0 + h * percent / 2
        cmds = []
        if in_or_out == 'in':
            cmds.append(b"d 0 %d %d 50\nd 1 %d %d 50\nc\n" % (x1, y1, x2, y2))
            for i in range(1, steps):
                cmds.append(b"m 0 %d %d 50\nm 1 %d %d 50\nc\n" % (
                    x1+(x0-x1)*i/steps, y1+(y0-y1)*i/steps,
                    x2+(x0-x2)*i/steps, y2+(y0-y2)*i/steps
                ))
            cmds.append(b"m 0 %d %d 50\nm 1 %d %d 50\nc\n" % (x0, y0, x0, y0))
            cmds.append(b"u 0\nu 1\nc\n")
        elif in_or_out == 'out':
            cmds.append(b"d 0 %d %d 50\nd 1 %d %d 50\nc\n" % (x0, y0, x0, y0))
            for i in range(1, steps):
                cmds.append(b"m 0 %d %d 50\nm 1 %d %d 50\nc\n" % (
                    x0+(x1-x0)*i/steps, y0+(y1-y0)*i/steps,
                    x0+(x2-x0)*i/steps, y0+(y2-y0)*i/steps
                ))
            cmds.append(b"m 0 %d %d 50\nm 1 %d %d 50\nc\n" % (x1, y1, x2, y2))
            cmds.append(b"u 0\nu 1\nc\n")
        else:
            raise RuntimeError("center should be 'in' or 'out', not %s" % repr(in_or_out))

        interval = float(duration)/(steps+1)
        for i, c in enumerate(cmds):
            self.handle(c)
            time.sleep(interval)

    @on_method_ready('install_and_setup')
    def operate(self, args):
        """
        Perform down, up and move actions

        Args:
            args: action arguments, dictionary containing type and x, y coordinates, e.g.::

                  {
                  "type" : "down",
                  "x" : 10,
                  "y" : 10
                  }

        Raises:
            RuntimeError: is invalid arguments are provided

        Returns:
            None

        """
        if args["type"] == "down":
            x, y = self.__transform_xy(args["x"], args["y"])
            # support py 3
            cmd = b"d 0 %d %d 50\nc\n" % (x, y)
        elif args["type"] == "move":
            x, y = self.__transform_xy(args["x"], args["y"])
            # support py 3
            cmd = b"m 0 %d %d 50\nc\n" % (x, y)
        elif args["type"] == "up":
            # support py 3
            cmd = b"u 0\nc\n"
        else:
            raise RuntimeError("invalid operate args: %s" % args)
        self.handle(cmd)

    def safe_send(self, data):
        """
        Send data to client

        Args:
            data: data to send

        Raises:
            Exception: when data cannot be sent

        Returns:
            None

        """
        try:
            self.client.send(data)
        except Exception as err:
            # raise MinitouchError(err)
            raise err

    def _backend_worker(self):
        """
        Backend worker queue thread

        Returns:
            None

        """
        while not self.backend_stop_event.isSet():
            cmd = self.backend_queue.get()
            if cmd is None:
                break
            self.safe_send(cmd)

    def setup_client_backend(self):
        """
        Setup backend client thread as daemon

        Returns:
            None

        """
        self.backend_queue = queue.Queue()
        self.backend_stop_event = threading.Event()
        self.setup_client()
        t = threading.Thread(target=self._backend_worker, name="minitouch")
        # t.daemon = True
        t.start()
        self.backend_thread = t
        self.handle = self.backend_queue.put

    def setup_client(self):
        """
        Setup client in following steps::

            1. connect to server
            2. receive the header
                v <version>
                ^ <max-contacts> <max-x> <max-y> <max-pressure>
                $ <pid>
            3. prepare to send

        Returns:
            None

        """
        s = SafeSocket()
        s.connect((self.adb.host, self.localport))
        s.sock.settimeout(2)
        header = b""
        while True:
            try:
                header += s.sock.recv(4096)  # size is not strict, so use raw socket.recv
            except socket.timeout:
                # raise RuntimeError("minitouch setup client error")
                warnings.warn("minitouch header not recved")
                break
            if header.count(b'\n') >= 3:
                break
        LOGGING.debug("minitouch header:%s", repr(header))
        self.client = s
        self.handle = self.safe_send

    def teardown(self):
        """
        Stop the server and client

        Returns:
            None

        """
        if hasattr(self, "backend_stop_event"):
            self.backend_stop_event.set()
            self.backend_queue.put(None)
        if self.client:
            self.client.close()
        if self.server_proc:
            self.server_proc.kill()
