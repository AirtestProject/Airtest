# -*- coding: utf-8 -*-
import os
import re
import socket
import sys
import threading
import time
import warnings
import six
from six.moves import queue

from airtest.core.android.constant import STFLIB
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.safesocket import SafeSocket
from airtest.utils.snippet import (get_std_encoding, on_method_ready,
                                   ready_method, reg_cleanup)

LOGGING = get_logger(__name__)


class Minitouch(object):
    """
    Super fast operation from minitouch

    References:
    https://github.com/openstf/minitouch
    """

    def __init__(self, adb, backend=False, ori_function=None):
        self.adb = adb
        self.backend = backend
        self.server_proc = None
        self.client = None
        self.size_info = None
        self.ori_function = ori_function if callable(ori_function) else self.adb.getPhysicalDisplayInfo
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
        self.size_info = self.ori_function()
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

        abi = self.adb.getprop("ro.product.cpu.abi")
        sdk = int(self.adb.getprop("ro.build.version.sdk"))

        if sdk >= 16:
            binfile = "minitouch"
        else:
            binfile = "minitouch-nopie"

        device_dir = "/data/local/tmp"
        path = os.path.join(STFLIB, abi, binfile).replace("\\", r"\\")

        if self.adb.exists_file('/data/local/tmp/minitouch'):
            local_minitouch_size = int(os.path.getsize(path))
            try:
                file_size = self.adb.file_size('/data/local/tmp/minitouch')
            except Exception:
                self.uninstall()
            else:
                if local_minitouch_size == file_size:
                    LOGGING.debug("install_minitouch skipped")
                    return
                self.uninstall()

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
        width, height = self.size_info['width'], self.size_info['height']

        nx = x * self.max_x / width
        ny = y * self.max_y / height

        # print(nx, ny, self.max_x, self.max_y, width, height)

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
        self.handle("d 0 {:.0f} {:.0f} 50\nc\n".format(x, y))
        time.sleep(duration)
        self.handle("u 0\nc\n")

    def __swipe_move(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5):
        """
        Return a sequence of swipe motion events (only MoveEvent)

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
            [MoveEvent(from_x, from_y), ..., MoveEvent(to_x, to_y)]

        """
        from_x, from_y = tuple_from_xy
        to_x, to_y = tuple_to_xy

        ret = []
        interval = float(duration) / (steps + 1)

        for i in range(1, steps):
            ret.append(MoveEvent((from_x + (to_x - from_x) * i / steps,
                                  from_y + (to_y - from_y) * i / steps)))
            ret.append(SleepEvent(interval))
        ret += [MoveEvent((to_x, to_y)), SleepEvent(interval)]
        return ret

    @on_method_ready('install_and_setup')
    def swipe_along(self, coordinates_list, duration=0.8, steps=5):
        """
        Perform swipe event across multiple points in sequence.

        Args:
            coordinates_list: list of coordinates: [(x1, y1), (x2, y2), (x3, y3)]
            duration: time interval for swipe duration, default is 0.8
            steps: size of swipe step, default is 5

        Returns:
            None

        """
        tuple_from_xy = coordinates_list[0]
        swipe_events = [DownEvent(tuple_from_xy), SleepEvent(0.1)]
        for tuple_to_xy in coordinates_list[1:]:
            swipe_events += self.__swipe_move(tuple_from_xy, tuple_to_xy, duration=duration, steps=steps)
            tuple_from_xy = tuple_to_xy

        swipe_events.append(UpEvent())
        self.perform(swipe_events)

    @on_method_ready('install_and_setup')
    def swipe(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5):
      
        """
        Perform swipe event.

        Args:
            tuple_from_xy: start point
            tuple_to_xy: end point
            duration: time interval for swipe duration, default is 0.8
            steps: size of swipe step, default is 5

        Returns:
            None

        """
        swipe_events = [DownEvent(tuple_from_xy), SleepEvent(0.1)]
        swipe_events += self.__swipe_move(tuple_from_xy, tuple_to_xy, duration=duration, steps=steps)
        swipe_events.append(UpEvent())
        self.perform(swipe_events)

    @on_method_ready('install_and_setup')
    def two_finger_swipe(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5):
        """
        Perform two finger swipe action

        minitouch protocol example::

            d 0 0 0 50
            d 1 1 0 50
            c
            m 0 20 0 50
            m 1 21 0 50
            c
            m 0 40 0 50
            m 1 41 0 50
            c
            m 0 60 0 50
            m 1 61 0 50
            c
            m 0 80 0 50
            m 1 81 0 50
            c
            m 0 100 0 50
            m 1 101 0 50
            c
            u 0
            u 1
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

        w = self.size_info['width']
        shift_x = 1 if from_x + 1 >= w else -1
        
        interval = float(duration) / (steps + 1)
        self.handle("d 0 {:.0f} {:.0f} 50\nd 1 {:.0f} {:.0f} 50\nc\n".format(from_x, from_y, from_x + shift_x, from_y))
        time.sleep(interval)
        for i in range(1, steps):
            self.handle("m 0 {:.0f} {:.0f} 50\nm 1 {:.0f} {:.0f} 50\nc\n".format(
                from_x + (to_x - from_x) * i / steps,
                from_y + (to_y - from_y) * i / steps,
                from_x + (to_x - from_x) * i / steps + shift_x,
                from_y + (to_y - from_y) * i / steps,
            ))
            time.sleep(interval)
        for i in range(10):
            self.handle("m 0 {:.0f} {:.0f} 50\nm 1 {:.0f} {:.0f} 50\nc\n".format(to_x, to_y, to_x + shift_x, to_y))
        time.sleep(interval)
        self.handle("u 0\nu 1\nc\n")

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
        w, h = self.size_info['width'], self.size_info['height']
        if isinstance(center, (list, tuple)):
            x0, y0 = center
        elif center is None:
            x0, y0 = w / 2, h / 2
        else:
            raise RuntimeError("center should be None or list/tuple, not %s" % repr(center))

        x1, y1 = x0 - w * percent / 2, y0 - h * percent / 2
        x2, y2 = x0 + w * percent / 2, y0 + h * percent / 2
        # 对计算出的原始坐标进行实际滑动位置的转换
        x0, y0 = self.__transform_xy(x0, y0)
        x1, y1 = self.__transform_xy(x1, y1)
        x2, y2 = self.__transform_xy(x2, y2)

        cmds = []
        if in_or_out == 'in':
            cmds.append("d 0 {:.0f} {:.0f} 50\nd 1 {:.0f} {:.0f} 50\nc\n".format(x1, y1, x2, y2))
            for i in range(1, steps):
                cmds.append("m 0 {:.0f} {:.0f} 50\nm 1 {:.0f} {:.0f} 50\nc\n".format(
                    x1+(x0-x1)*i/steps, y1+(y0-y1)*i/steps,
                    x2+(x0-x2)*i/steps, y2+(y0-y2)*i/steps
                ))
            cmds.append("m 0 {:.0f} {:.0f} 50\nm 1 {:.0f} {:.0f} 50\nc\n".format(x0, y0, x0, y0))
            cmds.append("u 0\nu 1\nc\n")
        elif in_or_out == 'out':
            cmds.append("d 0 {:.0f} {:.0f} 50\nd 1 {:.0f} {:.0f} 50\nc\n".format(x0, y0, x0, y0))
            for i in range(1, steps):
                cmds.append("m 0 {:.0f} {:.0f} 50\nm 1 {:.0f} {:.0f} 50\nc\n".format(
                    x0+(x1-x0)*i/steps, y0+(y1-y0)*i/steps,
                    x0+(x2-x0)*i/steps, y0+(y2-y0)*i/steps
                ))
            cmds.append("m 0 {:.0f} {:.0f} 50\nm 1 {:.0f} {:.0f} 50\nc\n".format(x1, y1, x2, y2))
            cmds.append("u 0\nu 1\nc\n")
        else:
            raise RuntimeError("center should be 'in' or 'out', not {}".format(repr(in_or_out)))

        interval = float(duration) / (steps + 1)
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
            cmd = "d 0 {:.0f} {:.0f} 50\nc\n".format(x, y)
        elif args["type"] == "move":
            x, y = self.__transform_xy(args["x"], args["y"])
            # support py 3
            cmd = "m 0 {:.0f} {:.0f} 50\nc\n".format(x, y)
        elif args["type"] == "up":
            # support py 3
            cmd = "u 0\nc\n"
        else:
            raise RuntimeError("invalid operate args: {}".format(args))
        self.handle(cmd)

    @on_method_ready('install_and_setup')
    def perform(self, motion_events, interval=0.01):
        """
        Perform a sequence of motion events including: UpEvent, DownEvent, MoveEvent, SleepEvent
        :param motion_events: a list of MotionEvent instances
        :param interval: minimum interval between events
        :return: None
        """
        for event in motion_events:
            if isinstance(event, SleepEvent):
                time.sleep(event.seconds)
            else:
                cmd = event.getcmd(transform=self.__transform_xy)
                self.handle(cmd)
                time.sleep(interval)

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
        if isinstance(data, six.text_type):
            data = data.encode('utf-8')
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


class MotionEvent(object):
    """
    Motion Event to be performed by Minitouch
    """
    def getcmd(self, transform=None):
        raise NotImplementedError

class DownEvent(MotionEvent):
    def __init__(self, coordinates, contact=0, pressure=50):
        """
        Finger Down Event
        :param coordinates: finger down coordinates in (x, y)
        :param contact: multi-touch action, starts from 0
        :param pressure: touch pressure
        """
        super(DownEvent, self).__init__()
        self.coordinates = coordinates
        self.contact = contact
        self.pressure = pressure

    def getcmd(self, transform=None):
        if transform:
            x, y = transform(*self.coordinates)
        else:
            x, y = self.coordinates
        cmd = "d {:.0f} {:.0f} {:.0f} {:.0f}\nc\n".format(self.contact, x, y, self.pressure)
        return cmd


class UpEvent(MotionEvent):
    def __init__(self, contact=0):
        """
        Finger Up Event
        :param contact: multi-touch action, starts from 0
        """
        super(UpEvent, self).__init__()
        self.contact = contact

    def getcmd(self, transform=None):
        cmd = "u {:.0f}\nc\n".format(self.contact)
        return cmd


class MoveEvent(MotionEvent):
    def __init__(self, coordinates, contact=0, pressure=50):
        """
        Finger Move Event
        :param coordinates: finger move to coordinates in (x, y)
        :param contact: multi-touch action, starts from 0
        :param pressure: touch pressure
        """
        super(MoveEvent, self).__init__()
        self.coordinates = coordinates
        self.contact = contact
        self.pressure = pressure

    def getcmd(self, transform=None):
        if transform:
            x, y = transform(*self.coordinates)
        else:
            x, y = self.coordinates
        cmd = "m {:.0f} {:.0f} {:.0f} {:.0f}\nc\n".format(self.contact, x, y, self.pressure)
        return cmd


class SleepEvent(MotionEvent):
    def __init__(self, seconds):
        self.seconds = seconds

    def getcmd(self, transform=None):
        return None
