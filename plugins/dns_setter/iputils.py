# coding=utf-8
__author__ = 'lxn3032'


import re


ip_pattern = re.compile(r'(\d+\.){3}\d+')
ip2int = lambda ip: reduce(lambda a, b: (a << 8) + b, map(int, ip.split('.')), 0)
int2ip = lambda n: '.'.join([str(n >> (i << 3) & 0xFF) for i in range(0, 4)[::-1]])


def get_ip_address(adb):
    res = adb.shell('netcfg | grep wlan0')
    matcher = re.search(r' ((\d+\.){3}\d+)/\d+', res)
    if matcher:
        return matcher.group(1)
    else:
        res = adb.shell('ifconfig')
        matcher = re.search(r'wlan0.*?inet addr:((\d+\.){3}\d+)', res, re.DOTALL)
        if matcher:
            return matcher.group(1)
        else:
            res = adb.shell('getprop dhcp.wlan0.ipaddress')
            matcher = ip_pattern.search(res)
            if matcher:
                return matcher.group(0)
    return None


def get_gateway_address(adb):
    res = adb.shell('getprop dhcp.wlan0.gateway')
    matcher = ip_pattern.search(res)
    if matcher:
        return matcher.group(0)
    else:
        res = adb.shell('netcfg | grep wlan0')
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
    res = adb.shell('netcfg | grep wlan0')
    matcher = re.search(r' (\d+\.){3}\d+/(\d+) ', res)
    if matcher:
        return matcher.group(2)
    else:
        # 获取不到网段长度就默认取17
        return '17'
