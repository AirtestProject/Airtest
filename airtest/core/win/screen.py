# -*- coding: utf-8 -*-
import win32gui
import win32api
import win32ui
import win32con
from airtest.aircv.utils import Image, pil_2_cv2


SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79


def screenshot(filename, hwnd=None):
    """
    Take the screenshot of Windows app

    Args:
        filename: file name where to store the screenshot
        hwnd:

    Returns:
        bitmap screenshot file

    """
    # import ctypes
    # user32 = ctypes.windll.user32
    # user32.SetProcessDPIAware()

    if hwnd is None:
        """all screens"""
        hwnd = win32gui.GetDesktopWindow()
        # get complete virtual screen including all monitors
        w = win32api.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        h = win32api.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        x = win32api.GetSystemMetrics(SM_XVIRTUALSCREEN)
        y = win32api.GetSystemMetrics(SM_YVIRTUALSCREEN)
    else:
        """window"""
        rect = win32gui.GetWindowRect(hwnd)
        w = abs(rect[2] - rect[0])
        h = abs(rect[3] - rect[1])
        x, y = 0, 0
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
    saveDC.SelectObject(saveBitMap)
    saveDC.BitBlt((0, 0), (w, h), mfcDC, (x, y), win32con.SRCCOPY)
    # saveBitMap.SaveBitmapFile(saveDC, filename)
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    pil_image = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)
    cv2_image = pil_2_cv2(pil_image)

    mfcDC.DeleteDC()
    saveDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    win32gui.DeleteObject(saveBitMap.GetHandle())
    return cv2_image
