# -*- coding: utf-8 -*-
"""模拟键盘输入."""

from keycode import VK_CODE, SHIFT_KCODE
import time
import win32api
import win32con


def one_key_input(key_code):
    """单个按键模拟事件."""
    win32api.keybd_event(key_code, 0, 0, 0)
    win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.01)


def _key_input(str='', alt=False):
    for c in str:
        if c == " ":
            c = "spacebar"
            one_key_input(VK_CODE[c])
        elif c in SHIFT_KCODE:
            win32api.keybd_event(VK_CODE["shift"], 0, 0, 0)
            one_key_input(VK_CODE[SHIFT_KCODE[c]])
            win32api.keybd_event(VK_CODE["shift"], 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            if c.isalpha() and c.isupper():  # 如果是大写字母，按下shift同时按下字母按键
                win32api.keybd_event(VK_CODE["shift"], 0, 0, 0)
                one_key_input(VK_CODE[c.lower()])
                win32api.keybd_event(VK_CODE["shift"], 0, win32con.KEYEVENTF_KEYUP, 0)
            else:
                one_key_input(VK_CODE[c])


def key_input(msg='', escape=False, combine=[]):
# def key_input(msg='', escape=False, combine=False, shift=False, ctrl=False, alt=False):
    """windows模拟按键输入函数."""
    # 校验combine组合键列表:
    for key in combine:
        if key not in VK_CODE.keys():
            raise Exception("'%s' in combine=%s doesn't exist !" % (key, combine))

    for key in combine:
        win32api.keybd_event(VK_CODE[key], 0, 0, 0)

    # 如果没有转义，直接输入每个字
    if not escape:
        _key_input(msg)
    # 如果有转义，就执行转义
    else:
        if (msg.startswith('f') or msg.startswith('F')) and len(msg) > 1:
            one_key_input(VK_CODE[msg.upper()])  # 针对F1-F12
        else:
            one_key_input(VK_CODE[msg.lower()])

    # 释放组合键列表:
    for key in combine:
        # 不需要校验，因为前面键按下时已经校验过了:
        win32api.keybd_event(VK_CODE[key], 0, win32con.KEYEVENTF_KEYUP, 0)
