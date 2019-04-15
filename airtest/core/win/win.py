# -*- coding: utf-8 -*-
from airtest import aircv
from airtest.core.device import Device
from pywinauto.application import Application
from pywinauto.win32functions import SetForegroundWindow, GetSystemMetrics  # ,SetProcessDPIAware
from pywinauto.win32structures import RECT
from pywinauto import mouse, keyboard
from functools import wraps
from .screen import screenshot
import socket
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
        self.handle = int(handle) if handle else None
        # windows high dpi scale factor, no exact way to auto detect this value for a window
        # reference: https://msdn.microsoft.com/en-us/library/windows/desktop/mt843498(v=vs.85).aspx
        self._dpifactor = float(dpifactor)
        self._app = Application()
        self._top_window = None
        self._focus_rect = (0, 0, 0, 0)
        self.mouse = mouse
        self.keyboard = keyboard
        self._init_connect(handle, kwargs)

    @property
    def uuid(self):
        return self.handle

    def _init_connect(self, handle, kwargs):
        if handle:
            self.connect(handle=handle)
        elif kwargs:
            self.connect(**kwargs)

    def connect(self, handle=None, **kwargs):
        """
        Connect to window and set it foreground

        Args:
            **kwargs: optional arguments

        Returns:
            None

        """
        if handle:
            handle = int(handle)
            self.app = self._app.connect(handle=handle)
            self._top_window = self.app.window(handle=handle).wrapper_object()
        else:
            for k in ["process", "timeout"]:
                if k in kwargs:
                    kwargs[k] = int(kwargs[k])
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

    def snapshot(self, filename=None):
        """
        Take a screenshot and save it in ST.LOG_DIR folder

        Args:
            filename: name of the file to give to the screenshot, {time}.jpg by default

        Returns:
            display the screenshot

        """
        if self.handle:
            screen = screenshot(filename, self.handle)
        else:
            screen = screenshot(filename)
            if self.app:
                rect = self.get_rect()
                screen = aircv.crop_image(screen, [rect.left, rect.top, rect.right, rect.bottom])
        if not screen.any():
            if self.app:
                rect = self.get_rect()
                screen = aircv.crop_image(screenshot(filename), [rect.left, rect.top, rect.right, rect.bottom])
        if self._focus_rect != (0, 0, 0, 0):
            height, width = screen.shape[:2]
            rect = (self._focus_rect[0], self._focus_rect[1], width + self._focus_rect[2], height + self._focus_rect[3])
            screen = aircv.crop_image(screen, rect)
        if filename:
            aircv.imwrite(filename, screen)
        return screen

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
        duration = kwargs.get("duration", 0.01)
        right_click = kwargs.get("right_click", False)
        button = "right" if right_click else "left"
        coords = self._action_pos(pos)

        self.mouse.press(button=button, coords=coords)
        time.sleep(duration)
        self.mouse.release(button=button, coords=coords)

    def double_click(self, pos):
        coords = self._action_pos(pos)
        self.mouse.double_click(coords=coords)

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
        from_x, from_y = self._action_pos(p1)
        to_x, to_y = self._action_pos(p2)

        interval = float(duration) / (steps + 1)
        self.mouse.press(coords=(from_x, from_y))
        time.sleep(interval)
        for i in range(1, steps):
            self.mouse.move(coords=(
                int(from_x + (to_x - from_x) * i / steps),
                int(from_y + (to_y - from_y) * i / steps),
            ))
            time.sleep(interval)
        for i in range(10):
            self.mouse.move(coords=(to_x, to_y))
        time.sleep(interval)
        self.mouse.release(coords=(to_x, to_y))

    def start_app(self, path, **kwargs):
        """
        Start the application

        Args:
            path: full path to the application

        Returns:
            None

        """
        self.app = self._app.start(path, **kwargs)

    def stop_app(self, pid):
        """
        Stop the application

        Args:
            pid: process ID of the application to be stopped

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

    def get_rect(self):
        """
        Get rectangle

        Returns:
            win32structures.RECT

        """
        if self.app and self._top_window:
            return self._top_window.rectangle()
        else:
            return RECT(right=GetSystemMetrics(0), bottom=GetSystemMetrics(1))

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
        pos = (int(pos[0]), int(pos[1]))
        return pos

    # @property
    # def handle(self):
    #     return self._top_window.handle

    @property
    def focus_rect(self):
        return self._focus_rect

    @focus_rect.setter
    def focus_rect(self, value):
        # set focus rect to get rid of window border
        assert len(value) == 4, "focus rect must be in [left, top, right, bottom]"
        self._focus_rect = value

    def get_current_resolution(self):
        rect = self.get_rect()
        w = (rect.right + self._focus_rect[2]) - (rect.left + self._focus_rect[0])
        h = (rect.bottom + self._focus_rect[3]) - (rect.top + self._focus_rect[1])
        return w, h

    def _windowpos_to_screenpos(self, pos):
        """
        Convert given position relative to window topleft corner to screen coordinates

        Args:
            pos: coordinates (x, y)

        Returns:
            converted position coordinates

        """
        rect = self.get_rect()
        pos = (int((pos[0] + rect.left + self._focus_rect[0]) * self._dpifactor), 
            int((pos[1] + rect.top + self._focus_rect[1]) * self._dpifactor))
        return pos

    def get_ip_address(self):
        """
        Return default external ip address of the windows os.

        Returns:
             :py:obj:`str`: ip address
        """
        return socket.gethostbyname(socket.gethostname())
