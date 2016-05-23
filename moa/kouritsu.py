# coding=utf-8
__author__ = 'lxn3032'


import re
import os
import requests
from .moa import SERIALNO, logwrap, platform, wake, keyevent, amstop, install, amclear, get_platform
from .core import ADB


adb = ADB(SERIALNO)


@logwrap
def rm_installer(filename):
    if os.path.exists(filename):
        os.remove(filename)
        

@logwrap
def download_installer(app_url, appname):
    r = requests.get(app_url, stream=True)
    if r.status_code == 200:
        with open(appname, 'wb') as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
        return True
    return False


@logwrap
@platform(on=['Android'])
def kinstall(appname, pkgname):
    wake()
    keyevent("HOME")
    adb.shell('settings put secure enabled_accessibility_services com.netease.accessibility/com.netease.accessibility.MyAccessibilityService')
    adb.shell('settings put secure accessibility_enabled 1')
    try:
        amstop(pkgname)
    except:
        pass
    install(appname)
    amclear(pkgname)


@logwrap
@platform(on=['Android','IOS'])
def get_wlanip():
    if get_platform() == 'IOS': # temporary: using hardcode ip address for ios device
        return "10.254.140.145"

    netcfg = adb.shell('netcfg')
    for l in netcfg.split('\n'):
        if 'wlan' in l:
            addr_matcher = re.search(r'(\d+\.){3}\d+', l)
            return addr_matcher.group(0)
    return None


@logwrap
@platform(on=['Android'])
def get_hunter_devid(process):
    wlanip = get_wlanip()
    if not wlanip:
        return None
    else:    
        return '{}_at_{}'.format(process, wlanip.replace('.', '-'))


@logwrap
def hunter_sendto(tokenid, data, **kwargs):
    data.update(kwargs)
    r = requests.post('http://hunter.nie.netease.com/api/sendto_device', headers={'tokenid': tokenid}, data=data)
    if r.status_code == 201:
        try:
            return r.json()
        except:
            pass
    else:
        print '======================================================================\n'
        print 'r.status_code=', r.status_code
        print 'data=', data
        print 'message=', r.json()['message']
        print '======================================================================\n'
    return None
