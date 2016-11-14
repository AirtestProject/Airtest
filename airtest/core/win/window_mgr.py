# -*- coding: utf-8 -*-
import win32gui
import win32ui
import win32con
import win32api
import re
import time
import cv2


class WindowMgr(object):
    
    """Encapsulates some calls to the winapi for window management"""

    def __init__ (self):
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
            if height != 0 and w_h[1] != 0:
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
        try:
            window_title = window_title.decode("gbk")
        except:
            import chardet
            print "-*-*- windows-title codec:", chardet.detect(window_title)
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
        if self.handle:
            win32gui.SetForegroundWindow(self.handle)

    def get_window_pos(self):
        """get window pos in (x0, y0, x1, y1)"""
        return win32gui.GetWindowRect(self.handle)

    def set_window_pos(self,x,y):
        rec = self.get_window_pos()
        return win32gui.SetWindowPos(self.handle,win32con.HWND_TOP,x,y,rec[2]-rec[0],rec[3]-rec[1],0)

    def get_window_title(self):
        return win32gui.GetWindowText(self.handle)


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


def get_window_pos(window_title):
    w = WindowMgr()
    w.find_window_wildcard(window_title)
    window = w._handle
    if not window:
        raise Exception("window not found")
    pos = win32gui.GetWindowRect(window)
    return pos
