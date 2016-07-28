# _*_ coding:UTF-8 _*_
import win32api
import win32con
import win32gui
import win32ui
import cv2
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
    '=':0xBB,
    # '+':0xBB,
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
    "+": "=",

    "{": "[",
    "}": "]",
    "|": "\\",
    ":": ";",
    "?": "/",
    "<": ",",
    ">": ".",
    '"': "'"
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


import win32gui, win32ui, win32con, win32api
import re

class WindowMgr:
    """Encapsulates some calls to the winapi for window management"""
    def __init__ (self):
        """Constructor"""
        self.handle = None
        self._handle_found = None
        self._handle_list_found = []

    def snapshot_by_hwnd(self, hwnd, filename="tmp.png"):
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

    def crop_screen_by_hwnd(self, screen, hwnd, filename="tmp.png"):
        rect = win32gui.GetWindowRect(hwnd)
        h, w = screen.shape[:2]
        x_min, y_min = max(0, rect[0]), max(1, rect[1])
        x_max, y_max = min(w - 1, rect[2]), min(h - 1, rect[3])
        if x_min > w-1 or y_min > h - 1 or x_max < 0 or y_max < 0:
            raise Exception("hwnd area is out of screen, cannot get its image.")
        img_crop = screen[y_min:y_max, x_min:x_max]
        return img_crop

    def get_wnd_pos_by_hwnd(self, hwnd, use_crop_screen=False):
        rect = win32gui.GetWindowRect(hwnd)

        if use_crop_screen:
            pos = (max(0, rect[0]), max(0, rect[1]))
        else:
            pos = (rect[0], rect[1])
        return pos

    def get_childhwnd_list_by_hwnd(self, hwnd, child_hwnd_list, w_h):
        # 传入当前的child_hwnd_list，去除当前已经不在hwnd内的child_hwnd
        #     如果发现全都不在了，那么就使用w_h进行查找新的child_hwnd_list
        #     如果发现w_h的也不在了，那么就按照w_h的比例相同的原则进行查找，还没有，就报错...

        # 第一步:根据父窗口的hwnd，将子窗口的hwnd、信息[x,y,w,h]一一提取出来：
        self.target_child_hwnd_dict = {}
        try:
            win32gui.EnumChildWindows(hwnd, self._find_child_hwnd_in_target_wnd, None)
        except:  # 该父窗口没有子窗口，直接return [].
            return []
        # 第二步：找到子窗口hwnd是否存在，剔除不存在的子窗口，如果child_hwnd_list中仍然有子窗口存在，直接返回：
        all_child_hwnd_list = self.target_child_hwnd_dict.keys()
        for c_hwnd in child_hwnd_list:
            if c_hwnd not in all_child_hwnd_list:
                child_hwnd_list.remove(c_hwnd)
        if child_hwnd_list:
            return child_hwnd_list
        # 第三步：发现child_hwnd_list已变成[]，根据w_h重新查找一遍：
        for key in all_child_hwnd_list:
            width, height = self.target_child_hwnd_dict[key][2], self.target_child_hwnd_dict[key][3]
            if width == w_h[0] and height == w_h[1]:
                child_hwnd_list.append(key)
        if child_hwnd_list:
            return child_hwnd_list
        # 第四步：发现child_hwnd_list仍为[]，则根据w_h的宽高比重新查找一遍：
        for key in all_child_hwnd_list:
            width, height = self.target_child_hwnd_dict[key][2], self.target_child_hwnd_dict[key][3]
            if (width / height - w_h[0] / w_h[1]) < 0.00001:
                child_hwnd_list.append(key)
        if child_hwnd_list:
            return child_hwnd_list
        else:
            raise Exception("no child_hwnd found, cannot get the precise pos of record-area! (from winutils.py)")

    def _find_child_hwnd_in_target_wnd(self, hwnd, lparam):
        '''本函数用于将单个父窗口的所有子窗口存入self.wnd_rect_origin'''
        rect = win32gui.GetWindowRect(hwnd)
        if win32gui.IsWindowVisible(hwnd):
            # 将目标父窗口中的子窗口hwnd和rect一一加入目标self.target_child_hwnd_dict：
            # self.target_child_hwnd_dict[hwnd] = rect
            # 将[x,y,w,h]存入child_hwnd_dict的value内：
            rect_xywh = [rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]]
            # hwnd_data = {"title": title, "resolution": reso, "target_child_hwnd_list": rect_xywh}
            self.target_child_hwnd_dict[hwnd] = rect_xywh
            
    def find_window(self, class_name, window_name = None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def find_hwnd_title(self, h_wnd):
        """获取指定hwnd的title."""
        def _wnd_enum_callback(hwnd, h_wnd=None):
            if hwnd == h_wnd:
                window_title = win32gui.GetWindowText(hwnd)
                window_title = window_title.decode("gbk")
                self._wnd_title_toget = window_title
                # print window_title.encode("utf8")

        self._wnd_title_toget = None
        win32gui.EnumWindows(_wnd_enum_callback, h_wnd)
        return self._wnd_title_toget

    def find_all_hwnd(self):
        """获取所有一级窗口的hwnd."""
        def _wnd_enum_callback(hwnd, test_str=None):
            self._all_hwnd_list.append(hwnd)

        self._all_hwnd_list = []
        win32gui.EnumWindows(_wnd_enum_callback, "")
        return self._all_hwnd_list

    def _window_enum_callback(self, hwnd, wildcard):
        '''Pass to win32gui.EnumWindows() to check all the opened windows'''
        window_title = win32gui.GetWindowText(hwnd)
        window_title = window_title.decode("gbk")
        # print "%s %s" % (repr(window_title), repr(wildcard))
        if window_title:
            try:
                m = re.search(wildcard, window_title)
            except:
                m = None
            if m != None:
                self._handle_found = hwnd
                self._handle_list_found.append(hwnd)
                print window_title.encode("utf8")

    def find_window_wildcard(self, wildcard):
        self._handle_found = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)
        return self._handle_found

    def find_window_list(self, wildcard):
        self._handle_list_found = []
        win32gui.EnumWindows(self._window_enum_callback, wildcard)
        return self._handle_list_found

    # def find_window_wildcard(self, wildcard):
    #     self._handle_found = None
    #     # win32gui.EnumWindows(self._window_enum_callback, wildcard)
    #     self.find_hwnd_from_all_hwnd_info(wildcard)
    #     return self._handle_found

    # def find_window_list(self, wildcard):
    #     self._handle_list_found = []
    #     # win32gui.EnumWindows(self._window_enum_callback, wildcard)
    #     self.find_hwnd_from_all_hwnd_info(wildcard)
    #     return self._handle_list_found

    # def find_hwnd_from_all_hwnd_info(self, wildcard):
    #     self.all_hwnd_info_list = self.get_all_hwnd_info()
    #     for hwnd_info in self.all_hwnd_info_list:
    #         window_title, hwnd = hwnd_info["title"], hwnd_info["hwnd"]
    #         if window_title:
    #             try:
    #                 m = re.search(wildcard, window_title)
    #             except:
    #                 m = None
    #             if m != None:
    #                 self._handle_found = hwnd
    #                 self._handle_list_found.append(hwnd)
    #                 # print window_title.encode("utf8")

    # def get_all_hwnd_info(self):
    #     all_hwnd_info_list = []  # 用于存储所有的窗口信息dict的列表
    #     all_parent_hwnd = self.get_main_windows()
    #     for parent_hwnd in all_parent_hwnd:
    #         rect = win32gui.GetWindowRect(parent_hwnd)
    #         window_title = win32gui.GetWindowText(parent_hwnd)
    #         window_title = window_title.decode("gbk")
    #         info = {"rect": rect, "title": window_title, "hwnd": parent_hwnd, "is_parent": 1}
    #         all_hwnd_info_list.append(info)

    #         try:
    #             win32gui.EnumChildWindows(parent_hwnd, self.find_child_hwnd_in_parent_wnd, None)
    #         except:
    #             pass
    #     for i in all_hwnd_info_list:
    #         if i["title"]:
    #             # print i["hwnd"], i["title"].encode("utf8")
    #             pass
    #     return all_hwnd_info_list

    # def get_main_windows(self):
    #     '''
    #         获取一级窗口: Returns windows in z-order (top first)
    #     '''
    #     user32 = windll.user32
    #     wndList = []
    #     top = user32.GetTopWindow(None)
    #     if not top:
    #         return wndList
    #     wndList.append(top)
    #     while True:
    #         next = user32.GetWindow(wndList[-1], win32con.GW_HWNDNEXT)
    #         if not next:
    #             break
    #         wndList.append(next)
    #     return wndList

    # def find_child_hwnd_in_parent_wnd(self, hwnd, lparam):
    #     """遍历子窗口回调函数"""
    #     rect = win32gui.GetWindowRect(hwnd)
    #     window_title = win32gui.GetWindowText(hwnd)
    #     window_title = window_title.decode("gbk")
    #     info = {"rect": rect, "title": window_title, "hwnd": hwnd, "is_parent": 0}
    #     all_hwnd_info_list.append(info)

    def set_foreground(self):
        """put the window in the foreground"""
        # 如果窗口最小化，那么需要将窗口正常显示出来:
        if win32gui.IsIconic(self.handle):
            win32gui.ShowWindow(self.handle, 4)
        time.sleep(0.01)
        win32gui.SetForegroundWindow(self.handle)

    def get_window_pos(self):
        """get window pos in (x0, y0, x1, y1)"""
        return win32gui.GetWindowRect(self.handle)

    def set_window_pos(self,x,y):
        rec = self.get_window_pos()
        return win32gui.SetWindowPos(self.handle,win32con.HWND_TOP,x,y,rec[2]-rec[0],rec[3]-rec[1],0)

    def get_window_title(self):
        return win32gui.GetWindowText(self.handle)

import wx

# #windows获取屏幕截图
# def get_screen_shot(output="screenshot.png"):
#     # # 改用PIL的ImageGrab.grab()作为截屏工具了..
#     # # 这个函数不再被调用
#     # print "nima, coming from winutils.py get_screen_shot(), never use this function ! ..."
#     # pass
#     app = wx.App()
#     s = wx.ScreenDC()
#     w, h = s.Size.Get()
#     b = wx.EmptyBitmap(w, h)
#     m = wx.MemoryDCFromDC(s)
#     m.SelectObject(b)
#     m.Blit(0, 0, w, h, s, 0, 0)
#     m.SelectObject(wx.NullBitmap)
#     if output:
#         b.SaveFile(output, wx.BITMAP_TYPE_PNG)
#         return output
#     else:
#         from PIL import Image
#         myWxImage = b.ConvertToImage()
#         myPilImage = Image.new( 'RGB', (myWxImage.GetWidth(), myWxImage.GetHeight()) )
#         myPilImage.frombytes( myWxImage.GetData() )
#         return myPilImage
        
import cv2
# windows双屏-单屏的截图支持
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
    saveBitMap.SaveBitmapFile(saveDC,  'screencapture.bmp')

    img = cv2.imread("screencapture.bmp")
    # cv2.imshow("123", img)
    # cv2.waitKey(0)
    
    return img










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
    # print get_resolution()
    w = WindowMgr()
    print w.find_window_list(u"Chrome")
    print w.handle
    w.handle = 921578
    w.set_foreground()
