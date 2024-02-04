# -*- coding: utf-8 -*-

import time
import socket
import subprocess
import numpy
import mss
import psutil
from functools import wraps
import win32api
import win32clipboard
import pywintypes  # noqa
import os

from pywinauto.application import Application
from pywinauto import mouse, keyboard
from pywinauto.win32structures import RECT

from airtest.core.win.ctypesinput import key_press, key_release

from airtest import aircv
from airtest.aircv.screen_recorder import ScreenRecorder, resize_by_max, get_max_size
from airtest.core.device import Device
from airtest.core.settings import Settings as ST
from airtest.utils.snippet import get_absolute_coordinate
from airtest.utils.logger import get_logger

LOGGING = get_logger(__name__)

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

        self.screen = mss.mss()
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
        if self.app:
            rect = self.get_rect()
            rect = self._fix_image_rect(rect)
            monitor = {"top": rect.top, "left": rect.left, "width": rect.right - rect.left - abs(self.monitor["left"]),
                       "height": rect.bottom - rect.top, "monitor": 1}
        else:
            monitor = self.screen.monitors[0]
        with mss.mss() as sct:
            sct_img = sct.grab(monitor)
            screen = numpy.array(sct_img, dtype=numpy.uint8)[...,:3]
            if filename:
                aircv.imwrite(filename, screen, quality, max_size=max_size)
            return screen

    def _fix_image_rect(self, rect):
        """Fix rect in image."""
        # 将rect 转换为左上角为(0,0), 与图片坐标对齐，另外left不用重新计算
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

        Examples:
            >>> from airtest.core.api import connect_device
            >>> dev = connect_device("Windows:///")
            >>> dev.touch((100, 100))  # absolute coordinates
            >>> dev.touch((0.5, 0.5))  # relative coordinates

        Returns:
            None

        """
        duration = kwargs.get("duration", 0.01)
        right_click = kwargs.get("right_click", False)
        button = "right" if right_click else "left"
        steps = kwargs.get("steps", 1)
        offset = kwargs.get("offset", 0)

        start = self._action_pos(win32api.GetCursorPos())
        ori_end = get_absolute_coordinate(pos, self)
        end = self._action_pos(ori_end)
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
        return ori_end

    def double_click(self, pos):
        ori_pos = get_absolute_coordinate(pos, self)
        coords = self._fix_op_pos(self._action_pos(ori_pos))
        self.mouse.double_click(coords=coords)
        return ori_pos

    def swipe(self, p1, p2, duration=0.8, steps=5, button="left"):
        """
        Perform swipe (mouse press and mouse release)

        Args:
            p1: start point
            p2: end point
            duration: time interval to perform the swipe action
            steps: size of the swipe step
            button: mouse button to press, 'left', 'right' or 'middle', default is 'left'

        Examples:
            >>> from airtest.core.api import connect_device
            >>> dev = connect_device("Windows:///")
            >>> dev.swipe((100, 100), (200, 200), duration=0.5)
            >>> dev.swipe((0.1, 0.1), (0.2, 0.2), duration=0.5)

        Returns:
            None

        """
        # 设置坐标时相对于整个屏幕的坐标:
        ori_from = get_absolute_coordinate(p1, self)
        ori_to = get_absolute_coordinate(p2, self)
        from_x, from_y = self._fix_op_pos(self._action_pos(ori_from))
        to_x, to_y = self._fix_op_pos(self._action_pos(ori_to))

        interval = float(duration) / (steps + 1)
        self.mouse.press(coords=(from_x, from_y), button=button)
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
        self.mouse.release(coords=(to_x, to_y), button=button)
        return ori_from, ori_to

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

    def start_app(self, path, *args, **kwargs):
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
        self._top_window.set_focus()

    set_focus = set_foreground

    def get_rect(self):
        """
        Get rectangle

        Returns:
            win32structures.RECT

        """
        if self.app and self._top_window:
            return self._top_window.rectangle()
        else:
            return RECT(right=win32api.GetSystemMetrics(0), bottom=win32api.GetSystemMetrics(1))

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

    def set_clipboard(self, text):
        """
        Set clipboard content

        Args:
            text: text to be set to clipboard

        Examples:

            >>> from airtest.core.api import connect_device
            >>> dev = connect_device("Windows:///")
            >>> dev.set_clipboard("hello world")
            >>> print(dev.get_clipboard())
            'hello world'
            >>> dev.paste()  # paste the clipboard content

        Returns:
            None

        """
        try:
            win32clipboard.OpenClipboard()
        except pywintypes.error as e:
            # pywintypes.error: (5, 'OpenClipboard', '拒绝访问。')
            # sometimes clipboard is locked by other process, retry after 0.1s
            time.sleep(0.1)
            win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
        finally:
            win32clipboard.CloseClipboard()

    def get_clipboard(self):
        """
        Get clipboard content

        Returns:
            clipboard content

        """
        try:
            win32clipboard.OpenClipboard()
            return win32clipboard.GetClipboardData()
        finally:
            win32clipboard.CloseClipboard()

    def paste(self):
        """
        Perform paste action

        Returns:
            None

        """
        self.keyevent("^v")

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
        ifaces = psutil.net_if_addrs()
        # 常见的虚拟网卡名称关键词
        virtual_iface_keywords = ['vEthernet', 'VirtualBox', 'VMware', 'Hyper-V', 'Wireless', 'VPN', 'Loopback']

        for interface_name, iface_addresses in ifaces.items():
            if any(keyword in interface_name for keyword in virtual_iface_keywords):
                continue

            for iface_address in iface_addresses:
                # 检查IPV4地址
                if iface_address.family == socket.AF_INET:
                    # 检查是否为自动获取的APIPA地址
                    if not iface_address.address.startswith('169.254'):
                        # 返回第一个非APIPA的IPV4地址
                        return iface_address.address

        return None


    def start_recording(self, max_time=1800, output=None, fps=10,
                        snapshot_sleep=0.001, orientation=0, max_size=None, *args, **kwargs):
        """
        Start recording the device display

        Args:
            max_time: maximum screen recording time, default is 1800
            output: ouput file path
            mode: the backend write video, choose in ["ffmpeg"]
                ffmpeg: ffmpeg-python backend, higher compression rate.
            fps: frames per second will record
            snapshot_sleep: sleep time for each snapshot.
            orientation: 1: portrait, 2: landscape, 0: rotation.
            max_size: max size of the video frame, e.g.800, default is None. Smaller sizes lead to lower system load.

        Returns:
            save_path: path of video file

        Examples:

            Record 30 seconds of video and export to the current directory test.mp4:

            >>> from airtest.core.api import connect_device, sleep
            >>> dev = connect_device("Windows:///")
            >>> save_path = dev.start_recording(output="test.mp4")
            >>> sleep(30)
            >>> dev.stop_recording()
            >>> print(save_path)

            You can specify max_size to limit the video's maximum width/length. Smaller video sizes result in lower CPU load.

            >>> dev.start_recording(output="test.mp4", max_size=800)

        Note:
            1 Don't resize the app window duraing recording, the recording region will be limited by first frame.
            2 If recording still working after app crash, it will continuing write last frame before the crash. 

        """
        if fps > 10 or fps < 1:
            LOGGING.warning("fps should be between 1 and 10, becuase of the recording effiency")
            if fps > 10:
                fps = 10
            if fps < 1:
                fps = 1

        if hasattr(self, 'recorder'):
            if self.recorder.is_running():
                LOGGING.warning("recording is already running, please don't call again")
                return None
        
        logdir = "./"
        if not ST.LOG_DIR is None:
            logdir = ST.LOG_DIR
        if output is None:
            save_path = os.path.join(logdir, "screen_%s.mp4"%(time.strftime("%Y%m%d%H%M%S", time.localtime())))
        else:
            if os.path.isabs(output):
                save_path = output
            else:
                save_path = os.path.join(logdir, output)

        max_size = get_max_size(max_size)
        def get_frame():
            frame = self.snapshot()
            
            if max_size is not None:
                frame = resize_by_max(frame, max_size)
            return frame

        self.recorder = ScreenRecorder(
            save_path, get_frame, fps=fps,
            snapshot_sleep=snapshot_sleep, orientation=orientation)
        self.recorder.stop_time = max_time
        self.recorder.start()
        LOGGING.info("start recording screen to {}, don't close or resize the app window".format(save_path))
        return save_path

    def stop_recording(self,):
        """
        Stop recording the device display. Recoding file will be kept in the device.

        """
        LOGGING.info("stopping recording")
        self.recorder.stop()
        return None
