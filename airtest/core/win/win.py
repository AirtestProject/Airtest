# -*- coding: utf-8 -*-
from airtest import aircv
from airtest.core.device import Device
from pywinauto.application import Application
from pywinauto import Desktop
from pywinauto.win32functions import SetForegroundWindow, ShowWindow
from pywinauto import mouse, keyboard
import subprocess


class Windows(Device):
    """Windows client."""

    def __init__(self, **kwargs):
        if not kwargs:
            self.app = Desktop()
            self.handle = None
        else:
            self.app = Application().connect(handle=handle, **kwargs)
            self.handle = self.app.handle

    def shell(self, cmd):
        return subprocess.check_output(cmd, shell=True)

    def snapshot(self, filename=None):
        """default not write into file."""
        # snapshot in window handle
        if self.handle is not None:
            return self.snapshot_by_hwnd(filename, self.handle)
        # snapshot in full screen
        screen = get_screen_shot()
        if filename:
            aircv.imwrite(filename, screen)
        return screen

    def keyevent(self, keyname, **kwargs):
        pass

    def text(self, text, **kwargs):
        pass

    def touch(self, pos, **kwargs):
        pass

    def swipe(self, p1, p2, duration=0.8, steps=5):
        pass

    def set_foreground(self):
        """将对应的窗口置到最前."""
        pass

    def get_window_pos(self):
        pass

    def set_window_pos(self, tuple_xy):
        pass

    def start_app(self, path):
        return subprocess.call('start "" "%s"' % path, shell=True)

    def stop_app(self, title=None, pid=None, image=None):
        if title:
            cmd = 'taskkill /FI "WINDOWTITLE eq %s"' % title
        elif pid:
            cmd = 'taskkill /PID %s' % pid
        elif image:
            cmd = 'taskkill /IM %s' % image
        return subprocess.check_output(cmd, shell=True)

    def snapshot(self, filename="tmp.png"):
        rect = win32gui.GetWindowRect(hwnd)
        # pos = (rect[0], rect[1])
        width = abs(rect[2] - rect[0])
        height = abs(rect[3] - rect[1])
        # print "in winutils.py WindowMgr():", pos, width, height
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
        saveBitMap.SaveBitmapFile(saveDC, filename)
        img = cv2.imread(filename)
        return img


def get_screen_shot(output="screenshot.png"):
    hwnd = win32gui.GetDesktopWindow()
    # print hwnd
    # you can use this to capture only a specific window
    #l, t, r, b = win32gui.GetWindowRect(hwnd)
    #w = r - l
    #h = b - t

    # get complete virtual screen including all monitors
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79
    w = vscreenwidth = win32api.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    h = vscreenheigth = win32api.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    l = vscreenx = win32api.GetSystemMetrics(SM_XVIRTUALSCREEN)
    t = vscreeny = win32api.GetSystemMetrics(SM_YVIRTUALSCREEN)
    r = l + w
    b = t + h
    # print l, t, r, b, ' -> ', w, h

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
    saveDC.SelectObject(saveBitMap)
    saveDC.BitBlt((0, 0), (w, h),  mfcDC,  (l, t),  win32con.SRCCOPY)
    saveBitMap.SaveBitmapFile(saveDC,  "screencapture.bmp")
    # get screencapture in cv2 format
    img = cv2.imread("screencapture.bmp")
    # delete temp file:
    os.remove("screencapture.bmp")
    return img
