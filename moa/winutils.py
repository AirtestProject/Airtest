# _*_ coding:UTF-8 _*_
import win32api
import win32con
import win32gui
from ctypes import *
import time
import chardet

VK_CODE = {
    'backspace':0x08,
    'tab':0x09,
    'clear':0x0C,
    'enter':0x0D,
    'shift':0x10,
    'ctrl':0x11,
    'alt':0x12,
    'pause':0x13,
    'caps_lock':0x14,
    'esc':0x1B,
    'spacebar':0x20,
    'page_up':0x21,
    'page_down':0x22,
    'end':0x23,
    'home':0x24,
    'left_arrow':0x25,
    'up_arrow':0x26,
    'right_arrow':0x27,
    'down_arrow':0x28,
    'select':0x29,
    'print':0x2A,
    'execute':0x2B,
    'print_screen':0x2C,
    'ins':0x2D,
    'del':0x2E,
    'help':0x2F,
    '0':0x30,
    '1':0x31,
    '2':0x32,
    '3':0x33,
    '4':0x34,
    '5':0x35,
    '6':0x36,
    '7':0x37,
    '8':0x38,
    '9':0x39,
    'a':0x41,
    'b':0x42,
    'c':0x43,
    'd':0x44,
    'e':0x45,
    'f':0x46,
    'g':0x47,
    'h':0x48,
    'i':0x49,
    'j':0x4A,
    'k':0x4B,
    'l':0x4C,
    'm':0x4D,
    'n':0x4E,
    'o':0x4F,
    'p':0x50,
    'q':0x51,
    'r':0x52,
    's':0x53,
    't':0x54,
    'u':0x55,
    'v':0x56,
    'w':0x57,
    'x':0x58,
    'y':0x59,
    'z':0x5A,
    'numpad_0':0x60,
    'numpad_1':0x61,
    'numpad_2':0x62,
    'numpad_3':0x63,
    'numpad_4':0x64,
    'numpad_5':0x65,
    'numpad_6':0x66,
    'numpad_7':0x67,
    'numpad_8':0x68,
    'numpad_9':0x69,
    'multiply_key':0x6A,
    'add_key':0x6B,
    'separator_key':0x6C,
    'subtract_key':0x6D,
    'decimal_key':0x6E,
    'divide_key':0x6F,
    'F1':0x70,
    'F2':0x71,
    'F3':0x72,
    'F4':0x73,
    'F5':0x74,
    'F6':0x75,
    'F7':0x76,
    'F8':0x77,
    'F9':0x78,
    'F10':0x79,
    'F11':0x7A,
    'F12':0x7B,
    'F13':0x7C,
    'F14':0x7D,
    'F15':0x7E,
    'F16':0x7F,
    'F17':0x80,
    'F18':0x81,
    'F19':0x82,
    'F20':0x83,
    'F21':0x84,
    'F22':0x85,
    'F23':0x86,
    'F24':0x87,
    'num_lock':0x90,
    'scroll_lock':0x91,
    'left_shift':0xA0,
    'right_shift ':0xA1,
    'left_control':0xA2,
    'right_control':0xA3,
    'left_menu':0xA4,
    'right_menu':0xA5,
    'browser_back':0xA6,
    'browser_forward':0xA7,
    'browser_refresh':0xA8,
    'browser_stop':0xA9,
    'browser_search':0xAA,
    'browser_favorites':0xAB,
    'browser_start_and_home':0xAC,
    'volume_mute':0xAD,
    'volume_Down':0xAE,
    'volume_up':0xAF,
    'next_track':0xB0,
    'previous_track':0xB1,
    'stop_media':0xB2,
    'play/pause_media':0xB3,
    'start_mail':0xB4,
    'select_media':0xB5,
    'start_application_1':0xB6,
    'start_application_2':0xB7,
    'attn_key':0xF6,
    'crsel_key':0xF7,
    'exsel_key':0xF8,
    'play_key':0xFA,
    'zoom_key':0xFB,
    'clear_key':0xFE,
    '+':0xBB,
    ',':0xBC,
    '-':0xBD,
    '.':0xBE,
    '/':0xBF,
    '`':0xC0,
    ';':0xBA,
    '[':0xDB,
    '\\':0xDC,
    ']':0xDD,
    "'":0xDE,
    '`':0xC0
}
#按住shift的键值对应的原键值，to be continued
SHIFT_KCODE = {
    "~": "`",
    "!": "1",
    "@": "2",
    "#": "3",
    "$": "4",
    "%": "5",
    "^": "6",
    "&": "7",
    "*": "8",
    "(": "9",
    ")": "0",
    "_": "-",
    "+": "="

}
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

def mouse_drag((x0, y0), (x1, y1), duration=0.3, steps=5):
    mouse_move(x0,y0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    interval = float(duration)/(steps+1)
    time.sleep(interval)
    for i in range(1, steps):
        _x, _y = x0+(x1-x0)*i/steps, y0+(y1-y0)*i/steps
        mouse_move(_x, _y)
        time.sleep(interval)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

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
        one_key_input(VK_CODE[msg.lower()])
    #如果有alt，就在这里释放alt
    if combine:
        win32api.keybd_event(VK_CODE[combine],0,win32con.KEYEVENTF_KEYUP,0)

#win8/10下面不能用alt
HOTKEY = {
    ("alt","a"): 10,
    ("alt","e"): 11,
    ("alt","t"): 12,
    ("alt","f"): 13,
    ("alt","p"): 14,
    ("alt","g"): 15,
    ("alt","x"): 16,
    ("alt","b"): 17,
    ("alt","s"): 18,
    ("alt","q"): 19,
    ("alt","o"): 20,
    ("alt","w"): 21,
    ("alt","c"): 22,
    ("alt","d"): 23,
    ("tab",): 24,

    #表情占段，待补充

    ("alt","n"): 36,
    ("alt","r"): 37,
    ("alt","u"): 38,

    #快捷技能占段，待补充

    ("alt","h"): 49,
    ("alt","v"): 50,
    ("alt","i"): 52,
}

HOTKEY_FIGHT = {
    ("alt","w"): 10,
    ("alt","s"): 11,
    ("alt","q"): 12,
    ("alt","d"): 13,
    ("alt","a"): 14,
    ("alt","t"): 15,
    ("alt","e"): 16,
    ("alt","g"): 17,
    ("alt","r"): 18,
    ("alt","v"): 19,
    ("alt","p"): 20,
    ("alt","p"): 20,
    ("alt","n"): 21,
    ("alt","x"): 22
}

def t0():
    pass
def t2():
    mouse_click(800,200)
    for c in 'hello':
        win32api.keybd_event(65,0,0,0) #a键位码是86
        win32api.keybd_event(65,0,win32con.KEYEVENTF_KEYUP,0)
    #print get_mouse_point()
def t1():
    #mouse_move(1024,470)aa
    #time.sleep(0.05)
    #mouse_dclick()HELLO
    mouse_dclick(1024,470)
def t3():
    mouse_click(1024,470)
    str = 'hello'
    for c in str:
        win32api.keybd_event(VK_CODE[c],0,0,0) #a键位码是86
        win32api.keybd_event(VK_CODE[c],0,win32con.KEYEVENTF_KEYUP,0)
        time.sleep(0.01)
def t4():
    mouse_click(1024,470)
    str = 'hello'
    _key_input(str)

def get_window_pos(window_title):
    w = WindowMgr()
    w.find_window_wildcard(window_title)
    window = w._handle
    if not window:
        raise Exception("window not found")
    pos = win32gui.GetWindowRect(window)
    return pos


import win32gui
import re

class WindowMgr:
    """Encapsulates some calls to the winapi for window management"""
    def __init__ (self):
        """Constructor"""
        self._handle = None

    def find_window(self, class_name, window_name = None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, wildcard):
        '''Pass to win32gui.EnumWindows() to check all the opened windows'''
        window_title = win32gui.GetWindowText(hwnd)
        window_title = window_title.decode("gbk")
        if re.match(wildcard, window_title) != None:
            self._handle = hwnd
            print window_title.encode("utf8")

    def find_window_wildcard(self, wildcard):
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)
        return self._handle

    def set_foreground(self):
        """put the window in the foreground"""
        print self._handle
        win32gui.SetForegroundWindow(self._handle)

    def get_window_pos(self):
        """get window pos in (x0, y0, x1, y1)"""
        return win32gui.GetWindowRect(self._handle)

    def set_window_pos(self,x,y):
        rec = self.get_window_pos()
        return win32gui.SetWindowPos(self._handle,win32con.HWND_TOP,x,y,rec[2]-rec[0],rec[3]-rec[1],0)

    def get_window_title(self):
        return win32gui.GetWindowText(self._handle)

import wx

#windows获取屏幕截图
def get_screen_shot(output="screenshot.png"):
    # # 改用PIL的ImageGrab.grab()作为截屏工具了..
    # # 这个函数不再被调用
    # print "nima, coming from winutils.py get_screen_shot(), never use this function ! ..."
    # pass
    app = wx.App()
    s = wx.ScreenDC()
    w, h = s.Size.Get()
    b = wx.EmptyBitmap(w, h)
    m = wx.MemoryDCFromDC(s)
    m.SelectObject(b)
    m.Blit(0, 0, w, h, s, 0, 0)
    m.SelectObject(wx.NullBitmap)
    if output:
        b.SaveFile(output, wx.BITMAP_TYPE_PNG)
        return output
    else:
        from PIL import Image
        myWxImage = b.ConvertToImage()
        myPilImage = Image.new( 'RGB', (myWxImage.GetWidth(), myWxImage.GetHeight()) )
        myPilImage.frombytes( myWxImage.GetData() )
        return myPilImage

def get_resolution():
    w = win32api.GetSystemMetrics(0)
    h = win32api.GetSystemMetrics(1)
    return w, h


if __name__ == "__main__":
    """
    x, y = get_mouse_point()
    print x, y
    mouse_click(x, y, True)
    w = WindowMgr()
    w.find_window_wildcard(u"梦幻西游2 ONLINE.*")
    w.set_foreground()
    #print repr(w._handle)
    get_screen_shot()
    mouse_click(duration=2.0)
    print get_window_pos(u"梦幻西游2 ONLINE.*")
    """
    # mouse_click(630, 260)
    print get_resolution()
