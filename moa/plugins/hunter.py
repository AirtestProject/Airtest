# coding=utf-8
__author__ = 'lxn3032'


import json
import requests
import moa.core.main as moa
from moa.core.android.utils import iputils


HUNTER_API_HOST = 'hunter.nie.netease.com'


def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


@moa.logwrap
@moa.platform(on=['Android', 'IOS', 'Windows'])
def get_wlanip():
    if moa.get_platform() == 'IOS':  # temporary: using hardcode ip address for ios device
        return "10.254.140.145"
    else:
        return iputils.get_ip_address(moa.DEVICE.adb)


@moa.logwrap
def get_hunter_devid(tokenid, process, wlanip=None):
    if process in ['g18', 'CallMeLeaderJack']:
        life_detection = '''
local console = hunter.require('safaia.console')
console.write('sys', '-ok-')
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
            try:
                dev_ret = hunter_sendto(tokenid, {
                            'lang': lang,
                            'data': life_detection,
                            'devid': devid,
                        },
                        watch_type='sys',
                        need_reply=True,
                        timeout=5)
                if dev_ret['data'] == '-ok-':
                    return devid
            except HunterApiException:
                pass
    return None


def whoami(tokenid):
    r = requests.get('http://{}/api/userinfo'.format(HUNTER_API_HOST), headers={'tokenid': tokenid})
    if r.status_code == 200:
        return r.json()['user']
    return None


def hunter_sendto(tokenid, data, **kwargs):
    data.update(kwargs)
    r = requests.post('http://{}/api/sendto_device'.format(HUNTER_API_HOST), headers={'tokenid': tokenid}, data=data)
    if r.status_code == 201:
        return r.json()
    else:
        raise HunterApiException('sendto_device', data, r)


def get_devices(tokenid, **kwargs):
    r = requests.get('http://{}/api/devices'.format(HUNTER_API_HOST), headers={'tokenid': tokenid}, params=kwargs)
    if r.status_code == 200:
        return r.json()['devices']
    else:
        raise HunterApiException('devices', kwargs, r)


def release_devices(tokenid, devid=None):
    r = requests.post('http://{}/api/release_device'.format(HUNTER_API_HOST), headers={'tokenid': tokenid}, data={'devid': devid})
    if r.status_code == 201:
        return r.json()
    else:
        raise HunterApiException('release_device', devid, r)


class HunterApiException(Exception):
    def __init__(self, api, data, resp):
        reply = ''
        try:
            reply = resp.json()['message']
        except:
            pass
        messageprefix = u'Exceprions occured when invoking hunter api, '
        message = messageprefix + u'name={}, data={}, status_code={}, reply={}'.format(api, data, resp.status_code, reply)
        message = message.encode('utf-8')
        super(HunterApiException, self).__init__(message)
        self.api = api
        self.data = data
        self.status_code = resp.status_code
        self.response = resp


class HunterDevidError(Exception):
    def __init__(self, message):
        super(HunterDevidError, self).__init__(message)


class Hunter(object):
    def __init__(self, tokenid, process, devid=None, apihost=None):
        super(Hunter, self).__init__()
        self.tokenid = tokenid
        self.process = process
        self.devid = devid
        if self.process in ['g18', 'CallMeLeaderJack']:
            self.lang = 'lua'
        else:
            self.lang = 'python'

        if apihost is not None:
            global HUNTER_API_HOST
            HUNTER_API_HOST = apihost

        self.HunterApiException = HunterApiException
        self.HunterDevidError = HunterDevidError

    def require(self, mod):
        return HunterInstructionModule(self, mod)

    def call(self, mod):
        return HunterInstructionModule(self, mod).real_value()

    def script(self, code, watch='ret'):
        if not self.devid:
            self.refresh_devid()
        if not self.devid:
            raise HunterDevidError('hunter devid is None, check whether the device is available on website')
        data = {'lang': self.lang, 'devid': self.devid, 'data': code}
        if watch:
            data['watch_type'] = watch
            data['need_reply'] = True
        ret = hunter_sendto(self.tokenid, data)
        if watch:
            return ret.get('data', None)
        else:
            return ret

    def refresh_devid(self):
        self.devid = get_hunter_devid(self.tokenid, self.process)


class HunterInstructionModule(object):
    def __init__(self, hobj, mod_name, methods=None):
        super(HunterInstructionModule, self).__init__()
        self.hobj = hobj
        self.mod_name = mod_name
        self.mod_val = None
        self.methods = methods or []

    @staticmethod
    def make_arglist(lang, *args, **kwargs):
        if lang == 'lua':
            arglist = repr(json.dumps(list(args) + kwargs.values(), default=set_default))
        else:
            arglist = ', '.join([repr(a) for a in args] + ['{}={}'.format(repr(k), repr(v)) for k, v in kwargs.items()])
        return arglist

    def __calculate_value__(self):
        if not self.mod_val:
            expr = ''
            if self.methods:
                expr = '.' + '.'.join(self.methods)
            if self.hobj.lang == 'python':
                code = '''
console = require('safaia.console')
try:
    mod = require('{mod}')
    console.ret(mod{expr})
except:
    import traceback
    console.ret(traceback.format_exc())
'''
            else:
                code = '''
local console = hunter.require('safaia.console')
xpcall(function()
    local mod = hunter.require('{mod}')
    console.ret(mod{expr})
end, function(errmsg)
    local tb = debug.traceback()
    console.ret(errmsg .. '\\n' .. tb)
end)
'''
            code = code.format(mod=self.mod_name, expr=expr)
            self.mod_val = self.hobj.script(code)

    def real_value(self):
        self.__calculate_value__()
        return self.mod_val

    def __getattr__(self, key):
        if key in ['__calculate_value__', 'real_value']:
            return getattr(self, key)
        else:
            return HunterInstructionModule(self.hobj, self.mod_name, self.methods + [key])

    def __repr__(self):
        self.__calculate_value__()
        return '<object HunterInstructionModule>: ' + str(self.mod_val)

    __str__ = __repr__

    def __int__(self):
        self.__calculate_value__()
        return int(self.mod_val)

    def __call__(self, *args, **kwargs):
        arglist = HunterInstructionModule.make_arglist(self.hobj.lang, *args, **kwargs)
        expr = ''
        if self.methods:
            expr = '.' + '.'.join(self.methods)
        if self.hobj.lang == 'python':
            code = '''
console = require('safaia.console')
try:
    mod = require('{mod}')
    console.ret(mod{expr}({arglist}))
except:
    import traceback
    console.ret(traceback.format_exc())
'''
        else:
            code = '''
local console = hunter.require('safaia.console')
local unpackArgs = nil
unpackArgs = function(t, i)
    i = i or 1
    if t[i] then
        return t[i], unpackArgs(t, i + 1)
    end
end
xpcall(function()
    local mod = hunter.require('{mod}')
    args = json.decode({arglist})
    console.ret(mod{expr}(unpackArgs(args)))
end, function(errmsg)
    local tb = debug.traceback()
    console.ret(errmsg .. '\\n' .. tb)
end)
'''
        code = code.format(mod=self.mod_name, expr=expr, arglist=arglist)
        ret = self.hobj.script(code)
        return ret


if __name__ == '__main__':
    # tokenid = 'eyJhbGciOiJIUzI1NiIsImV4cCI6MTY0NDgyODYxMiwiaWF0IjoxNDcyMDI4NjEyfQ.eyJ1c2VybmFtZSI6Imx4bjMwMzIifQ.7qHpOk3suWWtUuz6VX_IH2mmOtkZwVsxBhhg0CJZgVU'
    tokenid = 'eyJhbGciOiJIUzI1NiIsImV4cCI6MTY0NDczNjMwNSwiaWF0IjoxNDcxOTM2MzA1fQ.eyJ1c2VybmFtZSI6Imx4bjMwMzIifQ.Ykcb8-NKVJnkT9NO31inDCG2WGEdk6H68rlj9CvUAV0'  # g18
    # HUNTER_API_HOST = '10.251.93.179:32022'
    # devid = get_hunter_devid(tokenid, 'g18', '10.251.91.3')
    # print hunter_sendto(tokenid, {'lang': 'lua', 'data': '', 'devid': devid})
    # print whoami(tokenid)['username']

    HUNTER_API_HOST = '10.251.93.179:32022'
    print get_hunter_devid(tokenid, 'g18', '10.254.27.120')
    # hunter = Hunter(tokenid, 'g18', apihost='10.251.93.179:32022')
    # # hunter = Hunter(tokenid, 'CallMeLeaderJack', 'CallMeLeaderJack_at_10-251-83-125')
    # hunter.refresh_devid()
    # print hunter.devid
    # console = hunter.require('safaia.console')
    # print console.write('sys', '=ok=')

