#! /usr/bin/env python
# -*- coding: utf-8 -*-

import win32gui
import re
from airtest.core.android.android import Android, DEFAULT_ADB_SERVER, ADB, Minitouch
from airtest.core.android.ime_helper import YosemiteIme
from airtest.aircv import aircv
from android_emulator import EmulatorHelper


class Emulator(Android):
    """ android emulator
    注意init第一个参数是模拟器的名字
    """
    _props_tmp = "/data/local/tmp/moa_props.tmp"

    def __init__(self, emulator_name='bluestacks', serialno=None, addr=DEFAULT_ADB_SERVER, init_display=True, props=None, minicap=True, \
                 minicap_stream=False, minitouch=True, init_ime=False):
        from airtest.core.android.emulator.android_emulator import EMULATOR_INFO
        if EMULATOR_INFO.get(emulator_name):
            self.emulator_name = emulator_name
            self.emulator_info = EMULATOR_INFO[emulator_name]
        else:
            raise RuntimeError("please use the Bluestacks emulator")
        self.init_emulator()
        if not self.serialno:
            self.serialno = serialno or ADB('').devices(state="device")[0][0]
        self.adb = ADB(self.serialno, server_addr=addr)
        self.adb.start_server()
        self.adb.wait_for_device()
        if init_display:
            self._init_display(props)
            self.minitouch = Minitouch(serialno, size=self.size, adb=self.adb) if minitouch else None
        if init_ime:
            self.ime = YosemiteIme(self)
            self.toggle_shell_ime()

    def _init_display(self, props=None):
        # read props from outside or cached source, to save init time
        self.props = props or self._load_props()
        self.get_display_info()
        # 直接读props的配置可能有点问题，屏幕的朝向不正确
        #self.get_display_info()
        self.orientationWatcher()
        self.sdk_version = self.props.get("sdk_version") or self.adb.sdk_version
        self._dump_props()

    def get_display_info(self):
        """
        发现新版bluestacks有应用分辨率与实际软件设置分辨率大小不匹配的情况
        改用窗口获取大小的方式来拿分辨率准确一点
        :return:
        """
        self.size = self.getPhysicalDisplayInfo()
        self.size["orientation"] = self.getDisplayOrientation()
        self.size["rotation"] = self.size["orientation"] * 90
        self.size["max_x"], self.size["max_y"] = self.getEventInfo()

        hwnd = self.emulator_hwnd
        print('hwnd', hwnd)
        rect = win32gui.GetClientRect(hwnd)
        width = abs(rect[2] - rect[0])
        height = abs(rect[3] - rect[1])
        if self.size['width'] != width or self.size['height'] != height:
            self.size['width'] = width
            self.size['height'] = height
        return self.size

    def getPhysicalDisplayInfo(self):
        # android那边会保证width < height
        # 但是模拟器如果坚持保证宽比长小的话可能会有转置的问题
        info = self._getPhysicalDisplayInfo()
        return info

    def init_emulator(self):
        """
        初始化模拟器，需要1.找到对应的窗口句柄 2.连上adb
        :return:
        """
        emu_info = self.emulator_info
        if not emu_info:
            self.emulator_hwnd = 0
            self.emulator_info = {}
        else:
            self.emulator_info = emu_info
        if emu_info and emu_info['adb_connect']:
            self.serialno = emu_info['adb_connect']
        else:
            self.serialno = ''
        self.emulator_hwnd = EmulatorHelper.find_emu_windows_hwnd(self.emulator_name) or 0
        if not self.emulator_hwnd:
            # 如果模拟器已经被嵌入到IDE里的话，会找不到句柄的，要重新搜索IDE下面的子窗口句柄才能找到
            self.emulator_hwnd = EmulatorHelper.find_emu_embed_airtestide(self.emulator_name) or 0
        if not self.emulator_hwnd or not self.emulator_name:
            print('please launch a emulator first')

    def wake(self):
        """
        模拟器的解锁屏幕有点问题，这里直接return先
        :return:
        """
        return True

    def getDisplayOrientation(self):
        """
        模拟器里的横屏和竖屏，跟真机好像是相反的，一些老版本的机型上可能也有同样问题
        目前尝试过的orientation值：
        网易模拟器：横屏0
        逍遥安卓： 横屏0，竖屏3
        TODO: genymotion 待测，尤其是最后一种返回情况
        但是虽然值不同，坐标的转换规则是一样的，就是即使是横屏，坐标也不需要转换，后续更多情况待测试
        :return:
        """
        SurfaceFlingerRE = re.compile('orientation=(\d+)')
        output = self.adb.shell('dumpsys SurfaceFlinger')
        m = SurfaceFlingerRE.search(output)
        if m:
            ori = int(m.group(1))
            return ori

        # Fallback method to obtain the orientation
        # See https://github.com/dtmilano/AndroidViewClient/issues/128
        surfaceOrientationRE = re.compile('SurfaceOrientation:\s+(\d+)')
        output = self.adb.shell('dumpsys input')
        m = surfaceOrientationRE.search(output)
        if m:
            ori = int(m.group(1))
            return ori

        # 几乎大部分模拟器都是横屏，但是height依然会大于width，先默认返回1
        return 0 if self.size["height"] > self.size['width'] else 1

    def snapshot_bluestacks(self, filename="tmp.png", ensure_orientation=True):
        """这种截图方法是windows窗口截图，不能截最小化状态下的模拟器，
        只能截bluestacks内核的相关模拟器，如果是海马玩等其他类别的模拟器暂不支持

        """
        import win32gui
        import win32ui
        import win32con
        import cv2
        hwnd = self.emulator_hwnd
        if not hwnd:
            raise RuntimeError("please launch a emulator first ")
        try:
            rect = win32gui.GetClientRect(hwnd)
        except:
            print("snapshot failed")
            raise RuntimeError("please launch a emulator first ")
        width = abs(rect[2] - rect[0])
        height = abs(rect[3] - rect[1])
        if width != self.size['width']:
            self.size['width'] = width
        if height != self.size['height']:
            self.size['height'] = height
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

    def snapshot_win_game(self, filename="tmp.png", ensure_orientation=True):
        """
        这种截图方法比上一种稍微慢一些，能够截游戏窗口、genymotion模拟器
        不能截windows下的aero效果，不能截海马玩
        """
        import sys
        import ctypes, win32con
        import cv2
        from PyQt4 import QtGui
        app = QtGui.QApplication(sys.argv)
        # getWindowRect取得的是整个窗口的RECT坐标，left, top, right, bottom
        client_hwnd = self.emulator_hwnd
        print("snapshot_win", client_hwnd, filename)
        rect = win32gui.GetClientRect(client_hwnd)
        width = abs(rect[2] - rect[0])
        height = abs(rect[3] - rect[1])

        gdi = ctypes.windll.gdi32
        targetDC = ctypes.windll.user32.GetDC(client_hwnd)
        bitmapDC = gdi.CreateCompatibleDC(targetDC)
        hBitmap = gdi.CreateCompatibleBitmap(targetDC, width, height)
        oldBitmap = gdi.SelectObject(bitmapDC, hBitmap)
        gdi.BitBlt(bitmapDC, 0, 0, width, height, targetDC, 0, 0, win32con.SRCCOPY)
        iBPP = gdi.GetDeviceCaps(bitmapDC, 12)
        flag = QtGui.QImage.Format_RGB16 if iBPP == 16 else QtGui.QImage.Format_ARGB32
        flashImage = QtGui.QImage(width, height, flag)
        pBits = flashImage.bits()
        gdi.GetBitmapBits(hBitmap, width*height*iBPP/8, int(pBits))
        gdi.SelectObject(bitmapDC, oldBitmap)
        gdi.DeleteDC(bitmapDC)
        gdi.DeleteObject(hBitmap)

        ctypes.windll.user32.ReleaseDC(client_hwnd, targetDC)
        print(flashImage.save(filename))
        img = cv2.imread(filename)
        print(img)
        return img

    def snapshot(self, filename="tmp.png", ensure_orientation=True):
        """
        模拟器的截图
        """
        if self.emulator_info.get('kernel') in ['bluestacks']:
            if not self.emulator_hwnd:
                raise RuntimeError("please lanuch a emulator first")
            return self.snapshot_bluestacks(filename, ensure_orientation)
        else:
            screen = self.adb.snapshot()
            screen = aircv.string_2_img(screen)

            # 保证方向是正的
            if ensure_orientation and self.sdk_version <=16 and self.size["orientation"]:
                h, w = screen.shape[:2] #cv2的shape是高度在前面!!!!
                if w < h: #当前是横屏，但是图片是竖的，则旋转，针对sdk<=16的机器
                    screen = aircv.rotate(screen, self.size["orientation"]*90, clockwise=False)
            if filename:  # 这里图像格式不对，要写+读才对，to be fixed
                # open(filename, "wb").write(screen)
                aircv.imwrite(filename, screen)
            return screen

