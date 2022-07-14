# -*- coding: utf-8 -*-

import time
import socket
import subprocess
from mss import mss
from functools import wraps
import pywintypes  # noqa
import win32api

from pywinauto.application import Application
from pywinauto import mouse, keyboard
from pywinauto.win32structures import RECT
from pywinauto.win32functions import SetForegroundWindow, GetSystemMetrics

from airtest.core.win.ctypesinput import key_press, key_release
from airtest.core.win.screen import screenshot

from airtest import aircv
from airtest.core.device import Device


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
        super(Windows, self).__init__()
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

        self.screen = mss()
        self.monitor = self.screen.monitors[0]  # 双屏的时候，self.monitor为整个双屏
        self.main_monitor = self.screen.monitors[1]  # 双屏的时候，self.main_monitor为主屏

    @property
    def uuid(self):
        return self.handle

    def _init_connect(self, handle, kwargs):
        if handle:
            self.connect(handle=handle, **kwargs)
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
        if kwargs.get("foreground", True) in (True, "True", "true"):
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

    def snapshot(self, filename=None, quality=10, max_size=None):
        """
        Take a screenshot and save it in ST.LOG_DIR folder

        Args:
            filename: name of the file to give to the screenshot, {time}.jpg by default
            quality: The image quality, integer in range [1, 99]
            max_size: the maximum size of the picture, e.g 1200

        Returns:
            display the screenshot

        """
        if self.handle:
            screen = screenshot(filename, self.handle)
        else:
            screen = screenshot(filename)
            if self.app:
                rect = self.get_rect()
                rect = self._fix_image_rect(rect)
                screen = aircv.crop_image(screen, [rect.left, rect.top, rect.right, rect.bottom])
        if not screen.any():
            if self.app:
                rect = self.get_rect()
                rect = self._fix_image_rect(rect)
                screen = aircv.crop_image(screenshot(filename), [rect.left, rect.top, rect.right, rect.bottom])
        if self._focus_rect != (0, 0, 0, 0):
            height, width = screen.shape[:2]
            rect = (self._focus_rect[0], self._focus_rect[1], width + self._focus_rect[2], height + self._focus_rect[3])
            screen = aircv.crop_image(screen, rect)
        if filename:
            aircv.imwrite(filename, screen, quality, max_size=max_size)
        return screen


    def _fix_image_rect(self, rect):
        """Fix rect in image."""
        # 将rect 转换为左上角为(0,0), 与图片坐标对齐
        rect.left = rect.left - self.monitor["left"]
        rect.right = rect.right - self.monitor["left"]
        rect.top = rect.top - self.monitor["top"]
        rect.bottom = rect.bottom - self.monitor["top"]
        return rect

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

    def _fix_op_pos(self, pos):
        """Fix operation position."""
        # 如果是全屏的话，就进行双屏修正，否则就正常即可
        if not self.handle:
            pos = list(pos)
            pos[0] = pos[0] + self.monitor["left"]
            pos[1] = pos[1] + self.monitor["top"]

        return pos

    def key_press(self, key):
        """Simulates a key press event.

        Sends a scancode to the computer to report which key has been pressed.
        Some games use DirectInput devices, and respond only to scancodes, not
        virtual key codes. You can simulate DirectInput key presses using this
        method, instead of the keyevent() method, which uses virtual key
        codes.

        :param key: A string indicating which key to be pressed.
                    Available key options are:
                    {'ESCAPE', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                    '0', '-', '=', 'BACKSPACE', 'TAB', 'Q', 'W', 'E', 'R', 'T',
                    'Y', 'U', 'I', 'O', 'P', '[', ']', 'ENTER', 'LCTRL', 'A',
                    'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'", '`',
                    'LSHIFT', 'BACKSLASH', 'Z', 'X', 'C', 'V', 'B', 'N', 'M',
                    ',', '.', '/', 'RSHIFT', '*', 'LALT', 'SPACE', 'CAPS_LOCK',
                    'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9',
                    'F10', 'NUM_LOCK', 'SCROLL_LOCK', 'NUMPAD_7', 'NUMPAD_8',
                    'NUMPAD_9', 'NUMPAD_-', 'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6',
                    'NUMPAD_+', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_0',
                    'NUMPAD_.', 'F11', 'F12', 'PRINT_SCREEN', 'PAUSE',
                    'NUMPAD_ENTER', 'RCTRL', 'NUMPAD_/', 'RALT', 'HOME', 'UP',
                    'PAGE_UP', 'LEFT', 'RIGHT', 'END', 'DOWN', 'PAGE_DOWN',
                    'INSERT', 'DELETE', 'LWINDOWS', 'RWINDOWS', 'MENU'}.
        """
        key_press(key)

    def key_release(self, key):
        """Simulates a key release event.

        Sends a scancode to the computer to report which key has been released.
        Some games use DirectInput devices, and respond only to scancodes, not
        virtual key codes. You can simulate DirectInput key releases using this
        method. A call to the key_release() method usually follows a call to
        the key_press() method of the same key.

        :param key: A string indicating which key to be released.
        """
        key_release(key)

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
        steps = kwargs.get("steps", 1)
        offset = kwargs.get("offset", 0)

        start = self._action_pos(win32api.GetCursorPos())
        end = self._action_pos(pos)
        start_x, start_y = self._fix_op_pos(start)
        end_x, end_y = self._fix_op_pos(end)

        interval = float(duration) / steps
        time.sleep(interval)

        for i in range(1, steps):
            x = int(start_x + (end_x-start_x) * i / steps)
            y = int(start_y + (end_y-start_y) * i / steps)
            self.mouse.move(coords=(x, y))
            time.sleep(interval)

        self.mouse.move(coords=(end_x, end_y))

        for i in range(1, offset+1):
            self.mouse.move(coords=(end_x+i, end_y+i))
            time.sleep(0.01)

        for i in range(offset):
            self.mouse.move(coords=(end_x+offset-i, end_y+offset-i))
            time.sleep(0.01)

        self.mouse.press(button=button, coords=(end_x, end_y))
        time.sleep(duration)
        self.mouse.release(button=button, coords=(end_x, end_y))

    def double_click(self, pos):
        pos = self._fix_op_pos(pos)
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
        # 设置坐标时相对于整个屏幕的坐标:
        x1, y1 = self._fix_op_pos(p1)
        x2, y2 = self._fix_op_pos(p2)

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

    def mouse_move(self, pos):
        """Simulates a `mousemove` event.

        Known bug:
            Due to a bug in the pywinauto module, users might experience \
            off-by-one errors when it comes to the exact coordinates of \
            the position on screen.

        :param pos: A tuple (x, y), where x and y are x and y coordinates of
                    the screen to move the mouse to, respectively.
        """
        if not isinstance(pos, tuple) or len(pos) != 2:  # pos is not a 2-tuple
            raise ValueError('invalid literal for mouse_move: {}'.format(pos))
        try:
            self.mouse.move(coords=self._action_pos(pos))
        except ValueError:  # in case where x, y are not numbers
            raise ValueError('invalid literal for mouse_move: {}'.format(pos))

    def mouse_down(self, button='left'):
        """Simulates a `mousedown` event.

        :param button: A string indicating which mouse button to be pressed.
                       Available mouse button options are:
                       {'left', 'middle', 'right'}.
        """
        buttons = {'left', 'middle', 'right'}
        if not isinstance(button, str) or button not in buttons:
            raise ValueError('invalid literal for mouse_down(): {}'.format(button))
        else:
            coords = self._action_pos(win32api.GetCursorPos())
            self.mouse.press(button=button, coords=coords)

    def mouse_up(self, button='left'):
        """Simulates a `mouseup` event.

        A call to the mouse_up() method usually follows a call to the
        mouse_down() method of the same mouse button.

        :param button: A string indicating which mouse button to be released.
        """
        buttons = {'left', 'middle', 'right'}
        if not isinstance(button, str) or button not in buttons:
            raise ValueError('invalid literal for mouse_up(): {}'.format(button))
        else:
            coords = self._action_pos(win32api.GetCursorPos())
            self.mouse.release(button=button, coords=coords)

    def start_app(self, path, **kwargs):
        """
        Start the application

        Args:
            path: full path to the application
            kwargs: reference: https://pywinauto.readthedocs.io/en/latest/code/pywinauto.application.html#pywinauto.application.Application.start

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
        hostname = socket.getfqdn()
        return socket.gethostbyname_ex(hostname)[2][0]
