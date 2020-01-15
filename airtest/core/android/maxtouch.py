# -*- coding: utf-8 -*-
import os
import six
import time

from airtest.utils.logger import get_logger
from airtest.utils.safesocket import SafeSocket
from airtest.core.android.constant import STATICPATH
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.snippet import (on_method_ready,
                                   ready_method, reg_cleanup)

LOGGING = get_logger(__name__)
PATH_IN_ANDROID = "/data/local/tmp/maxpresent.jar"


class Maxtouch(object):
    """
        Developed by airtest team, for support touch in android phones >= 10
    """

    def __init__(self, adb, ori_function=None):
        self.adb = adb
        self.server_proc = None
        self.client = None
        self.size_info = None
        self.ori_function = ori_function if callable(ori_function) else self.adb.getPhysicalDisplayInfo
        reg_cleanup(self.teardown)

    @ready_method
    def install_and_setup(self):
        """
        Install and setup maxtouch

        Returns:
            None

        """
        self.install()
        self.size_info = self.ori_function()
        self.setup_server()
        self.setup_client()

    def uninstall(self):
        """
        Uninstall maxtouch

        Returns:
            None

        """
        self.adb.raw_shell("rm %s" % PATH_IN_ANDROID)

    def install(self):
        """
        Install maxtouch

        Returns:
            None

        """
        path = os.path.join(STATICPATH, "maxpresent.jar")

        if self.adb.exists_file(PATH_IN_ANDROID):
            local_minitouch_size = int(os.path.getsize(path))
            try:
                file_size = self.adb.file_size(PATH_IN_ANDROID)
            except Exception:
                self.uninstall()
            else:
                if local_minitouch_size == file_size:
                    LOGGING.debug("install maxpresent.jar skipped")
                    return
                self.uninstall()

        self.adb.push(path, PATH_IN_ANDROID)
        self.adb.shell("chmod 755 %s" % PATH_IN_ANDROID)
        LOGGING.info("install maxpresent.jar finished")

    def __transform_xy(self, x, y):
        """
        Normalized coordinates (x, y)

        Args:
            x: coordinate x
            y: coordinate y

        Returns:
            transformed coordinates (x, y)

        """
        width, height = self.size_info['width'], self.size_info['height']

        # print(x, y, width, height)
        return x / width, y/height

    def setup_server(self):
        """
        Setip maxtouch server and adb forward

        Returns:
            server process

        """
        if self.server_proc:
            self.server_proc.kill()
            self.server_proc = None

        self.localport, deviceport = self.adb.setup_forward("localabstract:maxpresent")
        deviceport = deviceport[len("localabstract:"):]
        p = self.adb.start_shell("app_process -Djava.class.path=%s /data/local/tmp com.netease.maxpresent.MaxPresent socket" % PATH_IN_ANDROID)

        nbsp = NonBlockingStreamReader(p.stdout, name="airtouch_server")
        line = nbsp.readline(timeout=5.0)
        if line is None:
            raise RuntimeError("airtouch setup timeout")

        if p.poll() is not None:
            # server setup error, may be already setup by others
            # subprocess exit immediately
            raise RuntimeError("airtouch server quit immediately")
        self.server_proc = p
        # reg_cleanup(self.server_proc.kill)
        return p

    @on_method_ready('install_and_setup')
    def touch(self, tuple_xy, duration=0.01):
        """
        Perform touch event


        maxtouch protocol example::

            d 0 0.1 0.1 0.5
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
        self.handle("d 0 {0} {1} 0.5\nc\n".format(x, y))
        time.sleep(duration)
        self.handle("u 0\nc\n")

    def __swipe_move(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5):
        """
        Return a sequence of swipe motion events (only MoveEvent)

        maxtouch protocol example::

            d 0 0 0 0.5
            c
            m 0 0.1 0 0.5
            c
            m 0 0.2 0 0.5
            c
            m 0 0.3 0 0.5
            c
            m 0 0.4 0 0.5
            c
            m 0 0.5 0 0.5
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

        maxtouch protocol example::

            d 0 0 0 0.5
            d 1 0.001 0 0.5
            c
            m 0 0.1 0 0.5
            m 1 0.101 0 0.5
            c
            m 0 0.2 0 0.5
            m 1 0.201 0 0.5
            c
            m 0 0.3 0 0.5
            m 1 0.301 0 0.5
            c
            m 0 0.4 0 0.5
            m 1 0.401 0 0.5
            c
            m 0 0.5 0 0.5
            m 1 0.501 0 0.5
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
        # shift_x = 1 if from_x + 1 >= w else -1
        # shift_x 第二个手指和第一个手指的横坐标 x 差 1px
        # maxpresent做归一化处理，所以是 1/w
        shift_x = 1/w
        shift_x = shift_x if from_x + shift_x >= 1 else -shift_x

        interval = float(duration) / (steps + 1)
        self.handle("d 0 {} {} 0.5\nd 1 {} {} 0.5\nc\n".format(from_x, from_y, from_x + shift_x, from_y))
        time.sleep(interval)
        for i in range(1, steps + 1):
            self.handle("m 0 {} {} 0.5\nm 1 {} {} 0.5\nc\n".format(
                from_x + (to_x - from_x) * i / steps,
                from_y + (to_y - from_y) * i / steps,
                from_x + (to_x - from_x) * i / steps + shift_x,
                from_y + (to_y - from_y) * i / steps,
            ))
            time.sleep(interval)
        time.sleep(interval)
        self.handle("u 0\nu 1\nc\n")

    @on_method_ready('install_and_setup')
    def pinch(self, center=None, percent=0.5, duration=0.5, steps=5, in_or_out='in'):
        """
        Perform pinch action

        maxtouch protocol example::

            d 0 0.25 0.25 0.5
            d 1 0.75 0.75 0.5
            c
            m 0 0.3 0.3 0.5
            m 1 0.7 0.7 0.5
            c
            m 0 0.35 0.35 0.5
            m 1 0.65 0.65 0.5
            c
            m 0 0.4 0.4 0.5
            m 1 0.6 0.6 0.5
            c
            m 0 0.45 0.45 0.5
            m 1 0.55 0.55 0.5
            c
            m 0 0.5 0.5 0.5
            m 1 0.5 0.5 0.5
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
            cmds.append("d 0 {} {} 0.5\nd 1 {} {} 0.5\nc\n".format(x1, y1, x2, y2))
            for i in range(1, steps):
                cmds.append("m 0 {} {} 0.5\nm 1 {} {} 0.5\nc\n".format(
                    x1+(x0-x1)*i/steps, y1+(y0-y1)*i/steps,
                    x2+(x0-x2)*i/steps, y2+(y0-y2)*i/steps
                ))
            cmds.append("m 0 {} {} 0.5\nm 1 {} {} 0.5\nc\n".format(x0, y0, x0, y0))
            cmds.append("u 0\nu 1\nc\n")
        elif in_or_out == 'out':
            cmds.append("d 0 {} {} 0.5\nd 1 {} {} 0.5\nc\n".format(x0, y0, x0, y0))
            for i in range(1, steps):
                cmds.append("m 0 {} {} 0.5\nm 1 {} {} 0.5\nc\n".format(
                    x0+(x1-x0)*i/steps, y0+(y1-y0)*i/steps,
                    x0+(x2-x0)*i/steps, y0+(y2-y0)*i/steps
                ))
            cmds.append("m 0 {} {} 0.5\nm 1 {} {} 0.5\nc\n".format(x1, y1, x2, y2))
            cmds.append("u 0\nu 1\nc\n")
        else:
            raise RuntimeError("center should be 'in' or 'out', not {}".format(repr(in_or_out)))

        interval = float(duration) / (steps + 1)
        for i, c in enumerate(cmds):
            self.handle(c)
            time.sleep(interval)

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
        self.client = s
        self.handle = self.safe_send

    def teardown(self):
        """
        Stop the server and client

        Returns:
            None

        """
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
    def __init__(self, coordinates, contact=0, pressure=0.5):
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
        cmd = "d {} {} {} {}\nc\n".format(self.contact, x, y, self.pressure)
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
        cmd = "u {}\nc\n".format(self.contact)
        return cmd


class MoveEvent(MotionEvent):
    def __init__(self, coordinates, contact=0, pressure=0.5):
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
        cmd = "m {} {} {} {}\nc\n".format(self.contact, x, y, self.pressure)
        return cmd


class SleepEvent(MotionEvent):
    def __init__(self, seconds):
        self.seconds = seconds

    def getcmd(self, transform=None):
        return None
