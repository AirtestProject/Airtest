# coding=utf-8
__author__ = 'lxn3032'


import re
import requests
import moa.core.main as moa


def _handle_api_request_err(r, data):
    print '======================================================================\n'
    print '*** hunter api request err. ***'
    print 'r.status_code=', r.status_code
    print 'data=', data
    print 'message=', r.json()['message']
    print '======================================================================\n'


@moa.logwrap
@moa.platform(on=['Android', 'IOS', 'Windows'])
def get_wlanip():
    if moa.get_platform() == 'IOS':  # temporary: using hardcode ip address for ios device
        return "10.254.140.145"
    else:
        netcfg = moa.DEVICE.adb.shell('netcfg')
        for l in netcfg.split('\n'):
            if 'wlan' in l:
                addr_matcher = re.search(r'(\d+\.){3}\d+', l)
                return addr_matcher.group(0)
    return None


@moa.logwrap
def get_hunter_devid(tokenid, process, wlanip=None):
    life_detection = '''
console = require('safaia.console')
console.write('sys', '-ok-', logging=False)
'''
    wlanip = wlanip or get_wlanip()
    if wlanip:
        devs = get_devices(tokenid, process=process, ip=wlanip, online=True)
        for devid, dev in devs.items():
            dev_ret = hunter_sendto(tokenid, {
                        'lang': 'python',
                        'data': life_detection,
                        'devid': devid,
                    },
                    watch_type='sys',
                    need_reply=True)
            if dev_ret and dev_ret['data'] == '-ok-':
                return devid
    return None


def hunter_sendto(tokenid, data, **kwargs):
    data.update(kwargs)
    r = requests.post('http://hunter.nie.netease.com/api/sendto_device', headers={'tokenid': tokenid}, data=data)
    if r.status_code == 201:
        try:
            return r.json()
        except:
            pass
    else:
        _handle_api_request_err(r, data)
    return None


def get_devices(tokenid, **kwargs):
    r = requests.get('http://hunter.nie.netease.com/api/devices', headers={'tokenid': tokenid}, params=kwargs)
    if r.status_code == 200:
        try:
            return r.json()['devices']
        except:
            pass
    else:
        _handle_api_request_err(r, kwargs)
    return None


def release_devices(tokenid, devid=None):
    r = requests.post('http://hunter.nie.netease.com/api/release_device', headers={'tokenid': tokenid}, data={'devid': devid})
    if r.status_code == 201:
        try:
            return r.json()
        except:
            pass
    else:
        _handle_api_request_err(r, devid)
    return None


if __name__ == '__main__':
    tokenid = "eyJhbGciOiJIUzI1NiIsImV4cCI6MTY0MDE1NTE5NiwiaWF0IjoxNDY3MzU1MTk2fQ.eyJ1c2VybmFtZSI6Imd6bGl1eGluIn0.GaWGg0E8_snNm3o6Zdn4P_evqKXTgea_0pLwdpb9TWI"
    print get_hunter_devid(tokenid, 'mh', '10.250.190.182')
