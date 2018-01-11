# -*- coding: utf-8 -*-
from airtest import aircv
from airtest.core.device import Device
from pywinauto.application import Application
from pywinauto import Desktop
from pywinauto.win32functions import SetForegroundWindow, ShowWindow, MoveWindow #, SetProcessDPIAware
from pywinauto import mouse, keyboard
from functools import wraps
from .screen import screenshot
import time
import subprocess

from airtest.core.settings import Settings as ST  # noqa


def require_app(func):
    @wraps(func)
    def wrapper(inst, *args, **kwargs):
        if not inst.app:
            raise RuntimeError("Connect to an application first to use %s" % func.__name__)
        return func(inst, *args, **kwargs)
    return wrapper


class Windows(Device):
    """Windows client."""

    def __init__(self, handle=None, dpifactor=1, **kwargs):
        self.app = None
        # windows high dpi scale factor, no exact way to auto get this value for a window
        # reference: https://msdn.microsoft.com/en-us/library/windows/desktop/mt843498(v=vs.85).aspx
        self._dpifactor = float(dpifactor)
        self._app = Application()
        self._top_window = None
        self.mouse = mouse
        self.keyboard = keyboard
        self._init_connect(handle, kwargs)

    def _init_connect(self, handle, kwargs):
        if handle:
            self.connect(handle=int(handle))
        elif kwargs:
            self.connect(**kwargs)

    def connect(self, **kwargs):
        """
        Connect to window and set it foreground

        Args:
            **kwargs: optional arguments

        Returns:
            None

        """
        self.app = self._app.connect(**kwargs)
        self._top_window = self.app.top_window().wrapper_object()
        self.set_foreground()

    def shell(self, cmd):
        """
        Run shell command in subprocess

        Args:
            cmd: command to be run

        Raises:
            subprocess.CalledProcessError: when command returns non-zero exit status

        Returns:
            command output as a byte string

        """
        return subprocess.check_output(cmd, shell=True)

    def snapshot(self, filename="tmp.png"):
        """
        Take a screenshot and save it to `tmp.png` filename by default

        Args:
            filename: name of file where to store the screenshot

        Returns:
            display the screenshot

        """
        if not filename:
            filename = "tmp.png"
        if self.app:
            screenshot(filename, self._top_window.handle)
        else:
            screenshot(filename)
        return aircv.imread(filename)

    def keyevent(self, keyname, **kwargs):
        """
        Perform a key event

        References:
            https://pywinauto.readthedocs.io/en/latest/code/pywinauto.keyboard.html

        Args:
            keyname: key event
            **kwargs: optional arguments

        Returns:
            None

        """
        self.keyboard.SendKeys(keyname)

    def text(self, text, **kwargs):
        """
        Input text

        Args:
            text: text to input
            **kwargs: optional arguments

        Returns:
            None

        """
        self.keyevent(text)

    def touch(self, pos, **kwargs):
    # def touch(self, pos, times=1, duration=0.01):
        """
        Perform mouse click action

        References:
            https://pywinauto.readthedocs.io/en/latest/code/pywinauto.mouse.html

        Args:
            pos: coordinates where to click
            **kwargs: optional arguments

        Returns:
            None

        """
        # self.mouse.click(coords=self._action_pos(pos), **kwargs)
        duration = kwargs.get("duration", 0.01)
        times = kwargs.get("times", 1)
        right_click = kwargs.get("right_click", False)
        button = "right" if right_click else "left"
        coords = self._action_pos(pos)

        for _ in range(times):
            self.mouse.press(button=button, coords=coords)
            time.sleep(duration)
            self.mouse.release(button=button, coords=coords)

    def swipe(self, p1, p2, duration=0.8, steps=5):
        """
        Perform swipe (mouse press and mouse release)
        Args:
            p1: start point
            p2: end point
            duration: time interval to perform the swipe action
            steps: size of the swipe step

        Returns:
            None

        """
        from_x, from_y = p1
        to_x, to_y = p2

        interval = float(duration) / (steps + 1)
        self.mouse.press(coords=self._action_pos((from_x, from_y)))
        time.sleep(interval)
        for i in range(1, steps):
            self.mouse.move(coords=(
                from_x + (to_x - from_x) * i / steps,
                from_y + (to_y - from_y) * i / steps,
            ))
            time.sleep(interval)
        for i in range(10):
            self.mouse.move(coords=self._action_pos((to_x, to_y)))
        time.sleep(interval)
        self.mouse.release(coords=self._action_pos((to_x, to_y)))

    def start_app(self, path):
        """
        Start the application

        Args:
            path: full path to the application

        Returns:
            None

        """
        self.app = self._app.start(path)

    def stop_app(self, pid):
        """
        Stop the application

        Args:
            pid: proccess ID of the application to be stopped

        Returns:
            None

        """
        self._app.connect(process=pid).kill()

    @require_app
    def set_foreground(self):
        """
        Bring the window foreground

        Returns:
            None

        """
        SetForegroundWindow(self._top_window)

    @require_app
    def get_rect(self):
        """
        Get rectangle

        Returns:
            None

        """
        return self._top_window.rectangle()

    @require_app
    def get_title(self):
        """
        Get the window title

        Returns:
            window title

        """
        return self._top_window.texts()

    @require_app
    def get_pos(self):
        """
        Get the window position coordinates

        Returns:
            coordinates of topleft corner of the window (left, top)

        """
        rect = self.get_rect()
        return (rect.left, rect.top)

    @require_app
    def move(self, pos):
        """
        Move window to given coordinates

        Args:
            pos: coordinates (x, y) where to move the window

        Returns:
            None

        """
        self._top_window.MoveWindow(x=pos[0], y=pos[1])

    @require_app
    def kill(self):
        """
        Kill the application

        Returns:
            None

        """
        self.app.kill()

    def _action_pos(self, pos):
        if self.app:
            pos = self._windowpos_to_screenpos(pos)
        # op_offset: caused by windows border
        pos = (pos[0] + ST.OP_OFFSET[0], pos[1] + ST.OP_OFFSET[1])

        return pos

    def _windowpos_to_screenpos(self, pos):
        """
        Convert given position relative to window topleft corner to screen coordinates

        Args:
            pos: coordinates (x, y)

        Returns:
            converted position coordinates

        """
        rect = self.get_rect()
        pos = (int((pos[0] + rect.left) * self._dpifactor), int((pos[1] + rect.top) * self._dpifactor))
        return pos
