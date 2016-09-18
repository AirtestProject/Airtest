# -*- coding: utf-8 -*-
from ctypes import *
from keycode import VK_CODE, SHIFT_KCODE
import time
import win32con
import win32api

class POINT(Structure):
    _fields_ = [("x", c_ulong),("y", c_ulong)]

def get_mouse_point():
    po = POINT()
    windll.user32.GetCursorPos(byref(po))
    return int(po.x), int(po.y)


def mouse_click(pos=None, right_click=False, duration=0.0, shift=False):
    if pos and len(pos)==2:
        mouse_move(pos[0], pos[1])
        time.sleep(0.05)
    if not right_click:
        key_down, key_up = win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP
    else:
        key_down, key_up = win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP

    if shift:
        win32api.keybd_event(VK_CODE["shift"],0,0,0)

    win32api.mouse_event(key_down, 0, 0, 0, 0)
    # 长按
    if duration:
        time.sleep(duration)
    win32api.mouse_event(key_up, 0, 0, 0, 0)

    if shift:
        time.sleep(0.5)
        win32api.keybd_event(VK_CODE["shift"],0,win32con.KEYEVENTF_KEYUP,0)

def mouse_down(pos=None,right_click=False):
    if pos and len(pos) == 2:
        mouse_move(pos[0],pos[1])
    if not right_click:
        key_down, key_up = win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP
    else:
        key_down, key_up = win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP
    win32api.mouse_event(key_down,0,0,0,0)

def mouse_up(right_click=False):
    if not right_click:
        key_down, key_up = win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP
    else:
        key_down, key_up = win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP
    win32api.mouse_event(key_up,0,0,0,0)

def mouse_dclick(x=None,y=None):
    if not x is None and not y is None:
        mouse_move(x,y)
        time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

def mouse_move(x,y):
    windll.user32.SetCursorPos(x, y)

def mouse_drag((x0, y0), (x1, y1), duration=0.3, steps=10):
    mouse_move(x0, y0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    interval = float(duration) / (steps + 1)
    time.sleep(interval)
    for i in range(1, steps+1):
        _x, _y = x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps
        mouse_move(_x, _y)
        time.sleep(interval)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
