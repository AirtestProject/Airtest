# -*- coding: utf-8 -*-
from airtest import aircv
from airtest.core.device import Device
from pywinauto.application import Application
from pywinauto import Desktop
from pywinauto.win32functions import SetForegroundWindow, ShowWindow, MoveWindow
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

    def __init__(self, **kwargs):
        self._app = Application()
        self.app = None
        self.mouse = mouse
        self.keyboard = keyboard

        if kwargs:
            self.connect(**kwargs)

    def connect(self, **kwargs):
        self.app = self._app.connect(handle=handle, **kwargs)

    def shell(self, cmd):
        return subprocess.check_output(cmd, shell=True)

    def snapshot(self, filename="tmp.png"):
        if self.app:
            screenshot(filename, self.app.handle)
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
        self.mouse.click(coords=pos, **kwargs)

    def swipe(self, p1, p2, duration=0.8, steps=5):
        from_x, from_y = p1
        to_x, to_y = p2

        interval = float(duration) / (steps + 1)
        self.mouse.press(coords=(from_x, from_y))
        time.sleep(interval)
        for i in range(1, steps):
            self.mouse.move(coords=(
                from_x + (to_x - from_x) * i / steps,
                from_y + (to_y - from_y) * i / steps,
            ))
            time.sleep(interval)
        for i in range(10):
            self.mouse.move(coords=(to_x, to_y))
        time.sleep(interval)
        self.mouse.release(coords=(to_x, to_y))

    def start_app(self, path):
        self.app = self._app.start(path)

    def stop_app(self, pid):
        self._app.connect(process=pid).kill()

    @require_app
    def set_foreground(self):
        """将对应的窗口置到最前."""
        SetForegroundWindow(self.app.wrapper_object())

    @require_app
    def get_rect(self):
        return self.app.wrapper_object().rectangle()

    @require_app
    def get_pos(self):
        rect = self.get_rect()
        return (rect.left, rect.top)

    @require_app
    def move(self, tuple_xy):
        self.app.MoveWindow(x=tuple_xy[0], y=tuple_xy[1])

    @require_app
    def kill(self, pid):
        self.app.kill()
