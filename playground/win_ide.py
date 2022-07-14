# -*- coding: utf-8 -*-

import os
import win32gui
from pywinauto.win32structures import RECT
from airtest import aircv
from airtest.core.win.win import Windows, screenshot


class WindowsInIDE(Windows):
    """Windows Device in Airtest-IDE"""

    def __init__(self, handle=None, dpifactor=1, **kwargs):
        if isinstance(handle, str) and handle.isdigit():
            handle = int(handle)
        super(WindowsInIDE, self).__init__(handle, dpifactor=dpifactor, **kwargs)
        self.handle = handle

    def connect(self, **kwargs):
        """
        Connect to window and set it foreground

        Args:
            **kwargs: optional arguments

        Returns:
            None

        """
        self.app = self._app.connect(**kwargs)
        try:
            self._top_window = self.app.top_window().wrapper_object()
            if kwargs.get("foreground", True) in (True, "True", "true"):
                self.set_foreground()
        except RuntimeError:
            self._top_window = None

    def get_rect(self):
        """
        Get rectangle of app or desktop resolution

        Returns:
            RECT(left, top, right, bottom)

        """
        if self.handle:
            left, top, right, bottom = win32gui.GetWindowRect(self.handle)
            return RECT(left, top, right, bottom)
        else:
            desktop = win32gui.GetDesktopWindow()
            left, top, right, bottom = win32gui.GetWindowRect(desktop)
            return RECT(left, top, right, bottom)

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
        if self.handle:
            try:
                screenshot(filename, self.handle)
            except win32gui.error:
                self.handle = None
                screenshot(filename)
        else:
            screenshot(filename)

        img = aircv.imread(filename)
        os.remove(filename)

        return img

if __name__ == '__main__':
    from airtest.core.api import G
    from airtest.cli.__main__ import main
    G.register_custom_device(WindowsInIDE)
    main()
