#! /usr/bin/env python
# -*- coding: utf-8 -*-

import win32gui
import re


EMULATOR_INFO = {
    'mumu_old': {'name': 'mumu_old', 'title': ur'网易手游助手', 'class_name': 'BlueStacksApp', 'sub_title': '_ctl.Window',\
                 'adb_connect': '127.0.0.1:5555', 'kernel': 'bluestacks'},
    'bluestacks': {'name': 'bluestacks', 'title': ur'Bluestacks App Player', 'class_name': 'BlueStacksApp', \
                   'sub_title': '_ctl.Window', 'adb_connect': None, 'kernel': 'bluestacks'},
    'xyaz': {'name': 'xyaz', 'title': ur'逍遥安卓', 'class_name': 'subWin', 'sub_title': 'sub', \
             'adb_connect': '127.0.0.1:21503', 'kernel': 'vbox'}
}


class WinHandleFinder(object):
    """
        自动查找模拟器的句柄用
        :return {'10000': {'title': window_title, 'emu_info': EMULATOR_INFO[name]}
    """
    @classmethod
    def get_emu_hwnd_title_dict(cls, name_list=['bluestacks', 'mumu_old']):
        """
        直接拿到所有现在支持的模拟器的句柄列表
        name_list=[] 返回当前所有句柄
        name_list默认值为目前支持的模拟器
        return: {hwnd: title unicode}
        """
        def _window_enum_callback(hwnd, hwnd_title_list):
            window_title = win32gui.GetWindowText(hwnd)
            window_title = window_title.decode("gbk")
            if window_title:
                if name_list:
                    for emu in name_list:
                        info = EMULATOR_INFO.get(emu)
                        if info and re.findall(info['title'], window_title):
                            hwnd_title_list[hwnd] = {'title': window_title, 'emu_info': info}
                            break
                elif not name_list:
                    hwnd_title_list[hwnd] = {'title': window_title, 'emu_info': None}

        hwnd_title_list = {}
        win32gui.EnumWindows(_window_enum_callback, hwnd_title_list)

        return hwnd_title_list

    @classmethod
    def get_child_windows(cls, parent):
        """
        获得parent的所有子窗口句柄
         返回子窗口句柄列表
        """
        if not parent:
            return
        hwndChildList = []
        win32gui.EnumChildWindows(parent, lambda hwnd, param: param.append(hwnd),  hwndChildList)
        return hwndChildList

    @classmethod
    def find_emu_windows_hwnd(cls, emulator_name):
        """
        默认选择一个模拟器
        :param emulator_name:
        :return:
        """
        get_emu_info = EMULATOR_INFO.get(emulator_name, None)
        if not get_emu_info:
            return None
        hwnd_title_dict = WinHandleFinder.get_emu_hwnd_title_dict([emulator_name])
        if not hwnd_title_dict:
            return None
        for k, v in hwnd_title_dict.items():
            if v.get('emu_info') and v['emu_info']['name'] == emulator_name:
                get_children = WinHandleFinder.get_child_windows(k)
                for hwnd in get_children:
                    title = win32gui.GetWindowText(hwnd)
                    clsname = win32gui.GetClassName(hwnd)
                    if title == get_emu_info['sub_title'] and clsname == get_emu_info['class_name']:
                        return hwnd
        return None

    @classmethod
    def get_support_emulator_hwnd(cls):
        """
        拿到当前运行中的、支持的模拟器列表
        :return:
        """
        emu_dict = WinHandleFinder.get_emu_hwnd_title_dict()
        if not emu_dict:
            return []
        ret = []
        for hwnd, value in emu_dict.items():
            if value.get('emu_info'):
                ret.append({'name': value['emu_info']['name'], 'title': value['title']})
        return ret