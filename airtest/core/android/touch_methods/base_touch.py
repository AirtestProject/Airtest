# -*- coding: utf-8 -*-
import threading
import time
import six
from six.moves import queue
from functools import wraps

from airtest.utils.logger import get_logger
from airtest.utils.snippet import (on_method_ready, ready_method, reg_cleanup, kill_proc)

LOGGING = get_logger(__name__)


def retry_when_connection_error(func):
    @wraps(func)
    def wrapper(inst, *args, **kwargs):
        try:
            return func(inst, *args, **kwargs)
        except ConnectionAbortedError:
            # maxtouch有可能会断开，断开时重新初始化一次
            inst.teardown()
            inst.install_and_setup()
            # 由于断开通常是不规范指令导致，因此本次运行结果可以丢弃
            # return func(inst, *args, **kwargs)
    return wrapper


class BaseTouch(object):
    """
    A super class for Minitouch or Maxtouch
    """

    def __init__(self, adb, backend=False, size_info=None, input_event=None, *args, **kwargs):
        self.adb = adb
        self.backend = backend
        self.server_proc = None
        self.client = None
        self.size_info = None
        self.input_event = input_event
        self.handle = None
        self.size_info = size_info or self.adb.get_display_info()
        self.default_pressure = 50
        self.path_in_android = ""
        reg_cleanup(self.teardown)

    @ready_method
    def install_and_setup(self):
        """
        Install and setup airtest touch

        Returns:
            None

        """
        self.install()
        self.setup_server()
        if self.backend:
            self.setup_client_backend()
        else:
            self.setup_client()

    def uninstall(self):
        """
        Uninstall airtest touch

        Returns:
            None

        """
        raise NotImplemented

    def install(self):
        """
        Install airtest touch

        Returns:
            None

        """

        raise NotImplemented

    def setup_server(self):
        """
        Setip touch server and adb forward

        Returns:
            server process

        """
        raise NotImplemented

    @retry_when_connection_error
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
        # 如果连接异常，会抛出ConnectionAbortedError，并自动重试一次
        self.client.send(data)

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
        t = threading.Thread(target=self._backend_worker, name="airtouch")
        # t.daemon = True
        t.start()
        self.backend_thread = t
        self.handle = self.backend_queue.put

    def setup_client(self):
        """
        Setup client

        Returns:
            None

        """
        raise NotImplemented

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
            kill_proc(self.server_proc)

    def transform_xy(self, x, y):
        """
        Transform coordinates (x, y) according to the device display

        Args:
            x: coordinate x
            y: coordinate y

        Returns:
            transformed coordinates (x, y)

        """
        return x, y

    @on_method_ready('install_and_setup')
    def perform(self, motion_events, interval=0.01):
        """
        Perform a sequence of motion events including: UpEvent, DownEvent, MoveEvent, SleepEvent

        Args:
            motion_events: a list of MotionEvent instances
            interval: minimum interval between events

        Returns:
            None
        """
        for event in motion_events:
            if isinstance(event, SleepEvent):
                time.sleep(event.seconds)
            else:
                cmd = event.getcmd(transform=self.transform_xy)
                self.handle(cmd)
                time.sleep(interval)

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
        touch_events = [DownEvent(tuple_xy, pressure=self.default_pressure), SleepEvent(duration), UpEvent()]
        self.perform(touch_events)

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
        ret += [MoveEvent((to_x, to_y), pressure=self.default_pressure), SleepEvent(interval)]
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
        swipe_events = [DownEvent(tuple_from_xy, pressure=self.default_pressure), SleepEvent(0.1)]
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
        swipe_events = [DownEvent(tuple_from_xy, pressure=self.default_pressure), SleepEvent(0.1)]
        swipe_events += self.__swipe_move(tuple_from_xy, tuple_to_xy, duration=duration, steps=steps)
        swipe_events.append(UpEvent())
        self.perform(swipe_events)

    @on_method_ready('install_and_setup')
    def two_finger_swipe(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5, offset=(0, 50)):
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
            offset: coordinate offset of the second finger, default is (0, 50)

        Returns:
            None
        """
        from_x, from_y = tuple_from_xy
        to_x, to_y = tuple_to_xy
        # 根据偏移量计算第二个手指的坐标
        from_x2, from_y2 = (min(max(0, from_x + offset[0]), self.size_info['width']),
                            min(max(0, from_y + offset[1]), self.size_info['height']))
        to_x2, to_y2 = (min(max(0, to_x + offset[0]), self.size_info['width']),
                        min(max(0, to_y + offset[1]), self.size_info['height']))
        swipe_events = [DownEvent(tuple_from_xy, contact=0, pressure=self.default_pressure),
                        DownEvent((from_x2, from_y2), contact=1, pressure=self.default_pressure),
                        ]

        interval = float(duration) / (steps + 1)
        for i in range(1, steps + 1):
            move_events = [
                SleepEvent(interval),
                MoveEvent((from_x + ((to_x - from_x) * i / steps), from_y + (to_y - from_y) * i / steps),
                          contact=0, pressure=self.default_pressure),
                MoveEvent((from_x2 + (to_x2 - from_x2) * i / steps, from_y2 + (to_y2 - from_y2) * i / steps),
                          contact=1, pressure=self.default_pressure),
            ]
            swipe_events.extend(move_events)
        swipe_events.extend([UpEvent(contact=0), UpEvent(contact=1)])
        self.perform(swipe_events)

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

        Args:
            center: the center point of the pinch operation
            percent: pinch distance to half of screen, default is 0.5
            duration: time interval for swipe duration, default is 0.8
            steps: size of swipe step, default is 5
            in_or_out: pinch in or pinch out, default is 'in'

        Returns:
            None

        Raises:
            TypeError: An error occurred when center is not a list/tuple or None

        """
        w, h = self.size_info['width'], self.size_info['height']
        if isinstance(center, (list, tuple)):
            x0, y0 = center
        elif center is None:
            x0, y0 = w / 2, h / 2
        else:
            raise TypeError("center should be None or list/tuple, not %s" % repr(center))

        x1, y1 = x0 - w * percent / 2, y0 - h * percent / 2
        x2, y2 = x0 + w * percent / 2, y0 + h * percent / 2
        pinch_events = []
        interval = float(duration) / (steps + 1)
        # 根据in还是out，设定双指滑动的起始和结束坐标
        if in_or_out == 'in':
            start_pos1_x, start_pos1_y = x1, y1
            start_pos2_x, start_pos2_y = x2, y2
            end_pos1_x, end_pos1_y = x0, y0
            end_pos2_x, end_pos2_y = x0, y0
        else:
            start_pos1_x, start_pos1_y = x0, y0
            start_pos2_x, start_pos2_y = x0, y0
            end_pos1_x, end_pos1_y = x1, y1
            end_pos2_x, end_pos2_y = x2, y2
        # 开始定义pinch的操作
        pinch_events.extend([
            DownEvent((start_pos1_x, start_pos1_y), contact=0, pressure=self.default_pressure),
            DownEvent((start_pos2_x, start_pos2_y), contact=1, pressure=self.default_pressure)
        ])
        for i in range(1, steps):
            pinch_events.extend([
                SleepEvent(interval),
                MoveEvent((start_pos1_x + (end_pos1_x - start_pos1_x) * i / steps,
                           start_pos1_y + (end_pos1_y - start_pos1_y) * i / steps),
                          contact=0, pressure=self.default_pressure),
                MoveEvent((start_pos2_x + (end_pos2_x - start_pos2_x) * i / steps,
                           start_pos2_y + (end_pos2_y - start_pos2_y) * i / steps),
                          contact=1, pressure=self.default_pressure)
            ])
        pinch_events.extend([
            SleepEvent(interval),
            MoveEvent((end_pos1_x, end_pos1_y), contact=0, pressure=self.default_pressure),
            MoveEvent((end_pos2_x, end_pos2_y), contact=1, pressure=self.default_pressure)
        ])
        pinch_events.extend([UpEvent(contact=0), UpEvent(contact=1)])
        self.perform(pinch_events)

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
            x, y = self.transform_xy(args["x"], args["y"])
            cmd = "d 0 {x} {y} {pressure}\nc\n".format(x=x, y=y, pressure=self.default_pressure)
        elif args["type"] == "move":
            x, y = self.transform_xy(args["x"], args["y"])
            cmd = "m 0 {x} {y} {pressure}\nc\n".format(x=x, y=y, pressure=self.default_pressure)
        elif args["type"] == "up":
            cmd = "u 0\nc\n"
        else:
            raise RuntimeError("invalid operate args: {}".format(args))
        self.handle(cmd)


class MotionEvent(object):
    """
    Motion Event to be performed by Minitouch/Maxtouch
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
        cmd = "d {contact} {x} {y} {pressure}\nc\n".format(contact=self.contact, x=x, y=y, pressure=self.pressure)
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
        cmd = "m {contact} {x} {y} {pressure}\nc\n".format(contact=self.contact, x=x, y=y, pressure=self.pressure)
        return cmd


class SleepEvent(MotionEvent):
    def __init__(self, seconds):
        self.seconds = seconds

    def getcmd(self, transform=None):
        return None
