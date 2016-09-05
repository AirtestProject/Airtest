#! /usr/bin/env python
# -*- coding: utf-8 -*-

import win32gui
import win32api
import pythoncom
import os
import re
from airtest.core.android.emulator.emulator_config import SUPPORT_EMULATOR, EMULATOR_INFO


class EmulatorHelper(object):
    """
        自动查找模拟器的句柄用
        :return {'10000': {'title': window_title, 'emu_info': EMULATOR_INFO[name]}
    """
    @classmethod
    def get_emu_hwnd_title_dict(cls, name_list=['bluestacks']):
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
        hwnd_title_dict = EmulatorHelper.get_emu_hwnd_title_dict([emulator_name])
        if not hwnd_title_dict:
            return None
        for k, v in hwnd_title_dict.items():
            if v.get('emu_info') and v['emu_info']['name'] == emulator_name:
                get_children = EmulatorHelper.get_child_windows(k)
                for hwnd in get_children:
                    title = win32gui.GetWindowText(hwnd)
                    clsname = win32gui.GetClassName(hwnd)
                    if title == get_emu_info['sub_title'] and clsname == get_emu_info['class_name']:
                        return hwnd
        raise RuntimeError("please run App first")

    @classmethod
    def find_emu_embed_airtestide(cls, emulator_name='bluestacks'):
        """
        如果模拟器已经被嵌入到airtest ide里面的话，直接搜索会找不到模拟器句柄
        :param emulator_name:
        :return:
        """
        hwnd_title_dict = EmulatorHelper.get_emu_hwnd_title_dict([])
        if not hwnd_title_dict:
            return None
        emu_info = EMULATOR_INFO[emulator_name]
        for k, v in hwnd_title_dict.items():
            if v['title'] and v['title'].find('Airtest IDE') != -1:
                get_children = EmulatorHelper.get_child_windows(k)
                for hwnd in get_children:
                    title = win32gui.GetWindowText(hwnd)
                    clsname = win32gui.GetClassName(hwnd)
                    if title == emu_info['sub_title'] and clsname == emu_info['class_name']:
                        return hwnd
        raise RuntimeError("please start App ")

    @classmethod
    def get_support_emulator_hwnd(cls):
        """
        拿到当前运行中的、支持的模拟器列表
        :return:
        """
        emu_dict = EmulatorHelper.get_emu_hwnd_title_dict()
        if not emu_dict:
            return []
        ret = []
        for hwnd, value in emu_dict.items():
            if value.get('emu_info'):
                ret.append({'name': value['emu_info']['name'], 'title': value['title'], 'hwnd': hwnd})
        return ret

    @classmethod
    def search_emulator_path(cls, emulator='bluestacks'):
        """
        搜索本机目录下有没有安装支持的模拟器，根据事先配置好的文件夹/exe名字的正则表达式来快速查找目录
        默认只查2层目录，提升效率，基本上几秒钟之内能有结果，搜不到就提供手工输入路径的方式
        :param emulator: 模拟器名字，比如bluestacks
        :return: 找到的路径，找不到返回''
        """
        emulator_info = EMULATOR_INFO.get(emulator)
        if not emulator_info or not emulator_info.get('folder_re') or not emulator_info.get('exe_re'):
            return ''

        def walklevel(some_dir, level=2):
            # 按照路径层级来walk，不查超过层级的文件夹
            assert os.path.isdir(some_dir)
            num_sep = some_dir.count(os.path.sep)
            for root, dirs, files in os.walk(some_dir):
                yield root, dirs, files
                num_sep_this = root.count(os.path.sep)
                if num_sep + level <= num_sep_this:
                    del dirs[:]

        drivers_string = win32api.GetLogicalDriveStrings()
        drivers = drivers_string.split('\x00')
        find_dirs = []
        for driver in drivers:
            if os.path.exists(driver):
                # 遍历看看能不能找到模拟器安装路径
                # 首先从各个驱动器路径下面遍历2层目录，找到有可能存放模拟器exe的路径列表
                for root, dirs, files in walklevel(driver, 1):
                    d = filter(lambda x: re.search(emulator_info['folder_re'], x.decode('gbk')), dirs)
                    if d:
                        find_dirs = [os.path.join(root, dir_name) for dir_name in d]
                        break
            if find_dirs:
                # 只要能找到结果就够了，不需要继续找其他的路径，缩短查找时长
                break

        # 上面拿到的是安装路径，下面在路径里搜exe
        filename = ''
        if find_dirs:
            for path in find_dirs:
                for root, dirs, files in os.walk(path):
                    m = re.search(emulator_info['exe_re'], repr(files))
                    if m:
                        filename = os.path.join(root, m.group())
                        break
                if filename:
                    break
        return filename

    @classmethod
    def start_emulator(cls, emulator_path=''):
        """
        启动模拟器
        :param emulator_path: 模拟器的exe路径，如果没有的话，就在硬盘里搜索一个
        :return: True 是否成功找到对应exe, emulator_path
        """
        # 首先搜索一下当前启动中的所有支持的模拟器列表，如果已经打开就不要重复启动
        running_emu_list = EmulatorHelper.get_support_emulator_hwnd()
        if running_emu_list:
            running_emu = [e['name'] for e in running_emu_list]
        else:
            running_emu = []
        emulator_path, emu_name = EmulatorHelper.check_emulator_exe_path(emulator_path)
        if emu_name in running_emu:
            return True, ''
        if emulator_path:
            try:
                os.startfile(emulator_path)
            except:
                return False, ''
            return True, emulator_path
        else:
            for emu in SUPPORT_EMULATOR:
                emulator_path = EmulatorHelper.search_emulator_path(emu)
                if emulator_path:
                    emulator_path, emu_name = EmulatorHelper.check_emulator_exe_path(emulator_path)
                    if emu_name in running_emu:
                        return True, ''
                    if emulator_path:
                        try:
                            os.startfile(emulator_path)
                            return True, emulator_path
                        except:
                            return False, ''
            return False, ''

    @classmethod
    def check_emulator_exe_path(cls, emulator_path):
        """
        确认一下传入的exe是不是可用的模拟器路径
        :param emulator_path: 模拟器的可执行exe完整路径
        :return: 返回2个值，第一个是可用的exe路径或者空字符串''，第二个是模拟器的名称
        """
        emulator_path = os.path.normpath(emulator_path)
        if os.path.isfile(emulator_path):
            for emu in SUPPORT_EMULATOR:
                if re.search(EMULATOR_INFO[emu].get('exe_re'), emulator_path):
                    return emulator_path, emu
        return '', ''

