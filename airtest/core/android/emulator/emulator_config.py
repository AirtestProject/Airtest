#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals    # at top of module
# support py 3

# 当前支持的模拟器名称
SUPPORT_EMULATOR = ['bluestacks', 'mumu_old']

# 模拟器信息的配置表
EMULATOR_INFO = {
    'mumu_old': {
        'name': 'mumu_old',
        'title': r'网易手游助手',
        'class_name': 'BlueStacksApp',
        'sub_title': '_ctl.Window',
        'adb_connect': '127.0.0.1:5555',
        'kernel': 'bluestacks',
        'folder_re': r'网易手游助手',
        'exe_re': r'EmulatorShell\.exe',
    },
    'bluestacks': {
        'name': 'bluestacks',
        'title': r'Bluestacks App Player',
        'class_name': 'BlueStacksApp',
        'sub_title': '_ctl.Window',
        'adb_connect': '127.0.0.1:5555',
        'kernel': 'bluestacks',
        'folder_re': r'[Bb]lue[Ss]tacks',
        'exe_re': r'[Bb]lue[Ss]tacks\w*\.exe',
    },
    'xyaz': {
        'name': 'xyaz',
        'title': r'逍遥安卓',
        'class_name': 'subWin',
        'sub_title': 'sub',
        'adb_connect': '127.0.0.1:21503',
        'kernel': 'vbox'
    }
}
