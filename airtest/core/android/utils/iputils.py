# coding=utf-8
__author__ = 'lxn3032'


import re
from functools import reduce

from airtest.core.error import AdbShellError


ip_pattern = re.compile(r'(\d+\.){3}\d+')
ip2int = lambda ip: reduce(lambda a, b: (a << 8) + b, map(int, ip.split('.')), 0)
int2ip = lambda n: '.'.join([str(n >> (i << 3) & 0xFF) for i in range(0, 4)[::-1]])


def get_ip_address(adb):
    try:
        res = adb.shell('netcfg | grep wlan0')
    except AdbShellError:
        res = ''
    matcher = re.search(r' ((\d+\.){3}\d+)/\d+', res)
    if matcher:
        return matcher.group(1)
    else:
        try:
            res = adb.shell('ifconfig')
        except AdbShellError:
            res = ''
        matcher = re.search(r'wlan0.*?inet addr:((\d+\.){3}\d+)', res, re.DOTALL)
        if matcher:
            return matcher.group(1)
        else:
            try:
                res = adb.shell('getprop dhcp.wlan0.ipaddress')
            except AdbShellError:
                res = ''
            matcher = ip_pattern.search(res)
            if matcher:
                return matcher.group(0)
    return None


def get_gateway_address(adb):
    try:
        res = adb.shell('getprop dhcp.wlan0.gateway')
    except AdbShellError:
        res = ''
    matcher = ip_pattern.search(res)
    if matcher:
        return matcher.group(0)
    else:
        try:
            res = adb.shell('netcfg | grep wlan0')
        except AdbShellError:
            res = ''
        matcher = re.search(r' ((\d+\.){3}\d+/\d+) ', res)
        if matcher:
            ip, mask_len = matcher.group(1).split('/')
            mask_len = int(mask_len)
        else:
            # 获取不到网关就默认按照ip前17位+1
            ip, mask_len = get_ip_address(adb), 17

        gateway = (ip2int(ip) & (((1 << mask_len) - 1) << (32 - mask_len))) + 1
        return int2ip(gateway)


def get_subnet_mask_len(adb):
    try:
        res = adb.shell('netcfg | grep wlan0')
    except AdbShellError:
        res = ''
    matcher = re.search(r' (\d+\.){3}\d+/(\d+) ', res)
    if matcher:
        return matcher.group(2)
    else:
        # 获取不到网段长度就默认取17
        print('[iputils WARNING] fail to get subnet mask len. use 17 as default.')
        return '17'
