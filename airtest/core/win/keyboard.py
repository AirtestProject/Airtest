# -*- coding: utf-8 -*-
from keycode import VK_CODE, SHIFT_KCODE
import time
import win32api
import win32con


def one_key_input(key_code):
    win32api.keybd_event(key_code,0,0,0)
    win32api.keybd_event(key_code,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(0.01)

def _key_input(str='', alt=False):
    for c in str:
        if c == " ":
            c = "spacebar"
            one_key_input(VK_CODE[c])
        elif c in SHIFT_KCODE:
            win32api.keybd_event(VK_CODE["shift"],0,0,0)
            one_key_input(VK_CODE[SHIFT_KCODE[c]])
            win32api.keybd_event(VK_CODE["shift"],0,win32con.KEYEVENTF_KEYUP,0)
        else:
            if c.isalpha() and c.isupper(): # 如果是大写字母，按下shift同时按下字母按键
                win32api.keybd_event(VK_CODE["shift"],0,0,0)
                one_key_input(VK_CODE[c.lower()])
                win32api.keybd_event(VK_CODE["shift"],0,win32con.KEYEVENTF_KEYUP,0)
            else:
                one_key_input(VK_CODE[c])

def key_input(msg='', escape=False, combine=None):
    #如果有alt，就先按住alt
    if combine:
        win32api.keybd_event(VK_CODE[combine],0,0,0)
    #如果没有转义，直接输入每个字
    if not escape:
        _key_input(msg)
    #如果有转义，
    else:
        if (msg.startswith('f') or msg.startswith('F')) and len(msg)>1:
            one_key_input(VK_CODE[msg.upper()]) # 针对F1-F12
        else:
            one_key_input(VK_CODE[msg.lower()])
    #如果有alt，就在这里释放alt
    if combine:
        win32api.keybd_event(VK_CODE[combine],0,win32con.KEYEVENTF_KEYUP,0)
