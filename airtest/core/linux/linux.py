# -*- coding: utf-8 -*-
from airtest import aircv
from airtest.core.device import Device
from pywinauto import mouse, keyboard
from Xlib import display, X
from PIL import Image
import socket
import time
import subprocess


class Linux(Device):
    """Linux desktop."""

    def __init__(self, pid=None, **kwargs):
        self.pid = None
        self._focus_rect = (0, 0, 0, 0)
        self.mouse = mouse
        self.keyboard = keyboard

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

    def snapshot(self, filename="tmp.png", quality=None):
        """
        Take a screenshot and save it to `tmp.png` filename by default

        Args:
            filename: name of file where to store the screenshot
            quality: ignored

        Returns:
            display the screenshot

        """
        w, h = self.get_current_resolution()
        dsp = display.Display()
        root = dsp.screen().root
        raw = root.get_image(0, 0, w, h, X.ZPixmap, 0xffffffff)
        image = Image.frombytes("RGB", (w, h), raw.data, "raw", "BGRX")
        from airtest.aircv.utils import pil_2_cv2
        image = pil_2_cv2(image)
        return image

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

        self.mouse.press(button=button, coords=pos)
        time.sleep(duration)
        self.mouse.release(button=button, coords=pos)

    def double_click(self, pos):
        self.mouse.double_click(coords=pos)

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

    def start_app(self, path, *args, **kwargs):
        """
        Start the application

        Args:
            path: full path to the application

        Returns:
            None

        """
        super(Linux, self).start_app(path)

    def stop_app(self, pid):
        """
        Stop the application

        Args:
            pid: process ID of the application to be stopped

        Returns:
            None

        """
        super(Linux, self).stop_app(pid)

    def get_current_resolution(self):
        d = display.Display()
        screen = d.screen()
        w, h = (screen["width_in_pixels"], screen["height_in_pixels"])
        return w, h

    def get_ip_address(self):
        """
        Return default external ip address of the linux os.

        Returns:
             :py:obj:`str`: ip address
        """
        return socket.gethostbyname(socket.gethostname())
