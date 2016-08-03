#! /usr/bin/env python
# -*- coding: utf-8 -*-

# 当前支持的模拟器名称
SUPPORT_EMULATOR = ['bluestacks', 'mumu_old']

# 模拟器信息的配置表
EMULATOR_INFO = {
    'mumu_old': {
        'name': 'mumu_old',
        'title': ur'网易手游助手',
        'class_name': 'BlueStacksApp',
        'sub_title': '_ctl.Window',
        'adb_connect': '127.0.0.1:5555',
        'kernel': 'bluestacks',
        'folder_re': ur'网易手游助手',
        'exe_re': ur'EmulatorShell\.exe',
    },
    'bluestacks': {
        'name': 'bluestacks',
        'title': ur'Bluestacks App Player',
        'class_name': 'BlueStacksApp',
        'sub_title': '_ctl.Window',
        'adb_connect': '127.0.0.1:5555',
        'kernel': 'bluestacks',
        'folder_re': ur'[Bb]lue[Ss]tacks',
        'exe_re': ur'[Bb]lue[Ss]tacks\w*\.exe',
    },
    'xyaz': {
        'name': 'xyaz',
        'title': ur'逍遥安卓',
        'class_name': 'subWin',
        'sub_title': 'sub',
        'adb_connect': '127.0.0.1:21503',
        'kernel': 'vbox'
    }
}
