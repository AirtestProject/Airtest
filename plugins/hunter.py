# coding=utf-8
__author__ = 'lxn3032'


import re
import requests
from moa.core.main import DEVICE, logwrap, platform, get_platform


@logwrap
@platform(on=['Android','IOS'])
def get_wlanip():
    if get_platform() == 'IOS': # temporary: using hardcode ip address for ios device
        return "10.254.140.145"
    else:
        netcfg = DEVICE.adb.shell('netcfg')
        for l in netcfg.split('\n'):
            if 'wlan' in l:
                addr_matcher = re.search(r'(\d+\.){3}\d+', l)
                return addr_matcher.group(0)
    return None


@logwrap
@platform(on=['Android','IOS'])
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
