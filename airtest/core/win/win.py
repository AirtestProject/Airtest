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
        self._dpifactor = dpifactor  # windows high dpi scale factor, no exact way to auto get this value for a window, reference: https://msdn.microsoft.com/en-us/library/windows/desktop/mt843498(v=vs.85).aspx
        self._app = Application()
        self._top_window = None
        self.mouse = mouse
        self.keyboard = keyboard
        self._init_connect(handle, kwargs)

    def _init_connect(self, handle, kwargs):
        if handle:
            self.connect(handle=handle)
        elif kwargs:
            self.connect(**kwargs)

    def connect(self, **kwargs):
        print(kwargs)
        self.app = self._app.connect(**kwargs)
        self._top_window = self.app.top_window().wrapper_object()
        self.set_foreground()

    def shell(self, cmd):
        return subprocess.check_output(cmd, shell=True)

    def snapshot(self, filename="tmp.png"):
        if not filename:
            filename = "tmp.png"
        if self.app:
            screenshot(filename, self._top_window.handle)
        else:
            screenshot(filename)
        return aircv.imread(filename)

    def keyevent(self, keyname, **kwargs):
        """https://pywinauto.readthedocs.io/en/latest/code/pywinauto.keyboard.html"""
        self.keyboard.SendKeys(keyname)

    def text(self, text, **kwargs):
        self.keyevent(text)

    def touch(self, pos, **kwargs):
        """https://pywinauto.readthedocs.io/en/latest/code/pywinauto.mouse.html"""
        self.mouse.click(coords=self._action_pos(pos), **kwargs)

    def swipe(self, p1, p2, duration=0.8, steps=5):
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
        self.app = self._app.start(path)

    def stop_app(self, pid):
        self._app.connect(process=pid).kill()

    @require_app
    def set_foreground(self):
        """将对应的窗口置到最前."""
        SetForegroundWindow(self._top_window)

    @require_app
    def get_rect(self):
        return self._top_window.rectangle()

    @require_app
    def get_title(self):
        return self._top_window.texts()

    @require_app
    def get_pos(self):
        rect = self.get_rect()
        return (rect.left, rect.top)

    @require_app
    def move(self, pos):
        self._top_window.MoveWindow(x=pos[0], y=pos[1])

    @require_app
    def kill(self):
        self.app.kill()

    def _action_pos(self, pos):
        if self.app:
            pos = self._windowpos_to_screenpos(pos)
        return pos

    def _windowpos_to_screenpos(self, pos):
        """convert pos relative to window's topleft cornor to screen pos"""
        rect = self.get_rect()
        pos = (int((pos[0] + rect.left) * self._dpifactor), int((pos[1] + rect.top) * self._dpifactor))
        return pos
