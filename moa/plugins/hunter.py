# coding=utf-8
__author__ = 'lxn3032'


import re
import requests
import moa.core.main as moa
from moa.core.android.utils import iputils


HUNTER_API_HOST = 'hunter.nie.netease.com'


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
        return iputils.get_ip_address(moa.DEVICE.adb)


@moa.logwrap
def get_hunter_devid(tokenid, process, wlanip=None):
    if process in ['g18']:
        life_detection = '''
local console = hunter.require('console')
console.write('sys', '-ok-', {logging = false})
'''
        lang = 'lua'
    else:
        life_detection = '''
console = require('safaia.console')
console.write('sys', '-ok-', logging=False)
'''
        lang = 'python'

    wlanip = wlanip or get_wlanip()
    if wlanip:
        devs = get_devices(tokenid, process=process, ip=wlanip, online=True)
        for devid, dev in devs.items():
            dev_ret = hunter_sendto(tokenid, {
                        'lang': lang,
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
    r = requests.post('http://{}/api/sendto_device'.format(HUNTER_API_HOST), headers={'tokenid': tokenid}, data=data)
    if r.status_code == 201:
        try:
            return r.json()
        except:
            pass
    else:
        _handle_api_request_err(r, data)
    return None


def get_devices(tokenid, **kwargs):
    r = requests.get('http://{}/api/devices'.format(HUNTER_API_HOST), headers={'tokenid': tokenid}, params=kwargs)
    if r.status_code == 200:
        try:
            return r.json()['devices']
        except:
            pass
    else:
        _handle_api_request_err(r, kwargs)
    return None


def release_devices(tokenid, devid=None):
    r = requests.post('http://{}/api/release_device'.format(HUNTER_API_HOST), headers={'tokenid': tokenid}, data={'devid': devid})
    if r.status_code == 201:
        try:
            return r.json()
        except:
            pass
    else:
        _handle_api_request_err(r, devid)
    return None


if __name__ == '__main__':
    # tokenid = "eyJhbGciOiJIUzI1NiIsImV4cCI6MTY0MzQyMTUxNiwiaWF0IjoxNDcwNjIxNTE2fQ.eyJ1c2VybmFtZSI6IndiLmxpbnNoYW9mZW4ifQ.Te0EYRfvA2wvQJBAho56qeW-m92i2Mc8KZSd_nQStuY"
    tokenid = 'eyJhbGciOiJIUzI1NiIsImV4cCI6MTY0NDczNjMwNSwiaWF0IjoxNDcxOTM2MzA1fQ.eyJ1c2VybmFtZSI6Imx4bjMwMzIifQ.Ykcb8-NKVJnkT9NO31inDCG2WGEdk6H68rlj9CvUAV0'
    HUNTER_API_HOST = '10.251.93.179:32022'
    print get_hunter_devid(tokenid, 'g18', '10.251.91.35')

    # for i in range(100):
    #     import json
    #     r = requests.post('http://192.168.40.111:3000/api/device/0815f8485f032404/extra',
    #                   data=json.dumps({'extra': {'456': [i]}}), headers={'content-type': 'application/json'})
    #     # if r.status_code == 201:
    #     print r.text