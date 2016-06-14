#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
import json
import urllib  
import urllib2  
import cookielib
import requests
from config import STF_TOKEN_ID as TOKEN_ID

# need modify params, please config yours...
# STF_WEB
HOST_IP = 'phone.nie.netease.com'
# User Token_Id
# 在stf-web个人设置页的“Setting UI”——“密钥”——“访问令牌”生成的，需要自行纪录一下
# TOKEN_ID = '0bdfdb70533d415ba2781c0dff47c3c5528d23a0dac44e81882cb2874c37ce3e'
# end modify

def _islist(v):
    return isinstance(v, list) or isinstance(v, tuple)

def http_get(host, data={}, headers={}):
 
    data = urllib.urlencode(data) 
    url = '%s?%s' % (host, data)
    
    opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
    
    urllib2.install_opener(opener)
    
    request = urllib2.Request(url, headers=headers)
    
    response = opener.open(request)
    response.status_code = response.getcode()
    response.data = response.read()
      
    return response

# REST API Demos 详情请参考/openstf/doc/API.md
# token认证方式:将用户在Setting UI生成的Token_id放在每一次请求的header中即可
DEV_USABLE = "usable"
DEV_ONLINE = "present"


# 获取设备列表
def get_device_list_rest(req, status=DEV_USABLE):
    if status:
        url = "http://%s:7100/api/v1/devices/status/%s" % (HOST_IP, status)
    else:
        url = "http://%s:7100/api/v1/devices" % (HOST_IP)
    res = http_get(url, headers={'authorization':'Bearer %s' % TOKEN_ID})   
    # print res.status_code
    return json.loads(res.data)['devices']

# 获取单台设备信息
def get_device_info_rest(req, serial):    
    url = "http://%s:7100/api/v1/devices/%s" % (HOST_IP, serial)
    res = http_get(url, headers={'authorization':'Bearer %s' % TOKEN_ID})   
    # print res.status_code
    return json.loads(res.data)

# 获取设备列表中特定字段
# fields参数为目标字段列表
def get_device_list_fields(req, fields=[]):
    if(_islist(fields)):
        fields = ','.join(fields)
    url = "http://%s:7100/api/v1/devices?fields=%s" % (HOST_IP, fields)
    res = http_get(url, headers={'authorization':'Bearer %s' % TOKEN_ID})   
    # print res.status_code
    return json.loads(res.data)

# 使用设备
def join_group(serial):
    url = "http://%s:7100/api/v1/user/devices" % HOST_IP
    headers = {
        'content-type': 'application/json',
        'authorization':'Bearer %s' % TOKEN_ID
    }

    data = {"serial": serial}

    res = requests.post(url, data=json.dumps(data), headers=headers)
    # print 'joinGroup ', res.json()
    return res.json()

# 释放设备
def leave_group(serial):
    url = "http://%s:7100/api/v1/user/devices/%s" % (HOST_IP, serial)
    headers = {'authorization':'Bearer %s' % TOKEN_ID}

    res = requests.delete(url, headers=headers)

    print 'leaveGroup ', res.json()
    return res.json()

# 远程设备连接，返回远程连接url
def remote_connect(serial):
    url = "http://%s:7100/api/v1/user/devices/%s/remoteConnect" % (HOST_IP, serial)
    headers = {
        'content-type': 'application/json',
        'authorization':'Bearer %s' % TOKEN_ID
    }

    res = requests.post(url, headers=headers)
    # print 'remoteConnect ', res.json()
    return res.json()

# 结束远程设备连接
def remote_disconnect(serial):
    url = "http://%s:7100/api/v1/user/devices/%s/remoteConnect" % (HOST_IP, serial)
    headers = {'authorization':'Bearer %s' % TOKEN_ID}

    res = requests.delete(url, headers=headers)
    print 'remoteConnect ', res.json()
    return res.json()

# 获取当前Token_id对应user的信息
def get_user_info():
    url = "http://%s:7100/api/v1/user" % HOST_IP 
    res = http_get(url, headers={'authorization':'Bearer %s' % TOKEN_ID})   
    # print res.status_code
    return json.loads(res.data)

# 获取当前Token_id对应user使用设备的信息
def get_user_devices(req):    
    url = "http://%s:7100/api/v1/user/devices" % HOST_IP 
    res = http_get(url, headers={'authorization':'Bearer %s' % TOKEN_ID})   
    # print res.status_code
    return json.loads(res.data)

# 获取使用情况统计信息的数据
# Response Description
#   - usestat (list or array)
def get_use_statistics(req):
    url = "http://%s:7100/api/v1/usestat" % HOST_IP 
    res = http_get(url, headers={'authorization':'Bearer %s' % TOKEN_ID})   
    # print res.status_code
    return json.loads(res.data)


if __name__ == "__main__":
    from pprint import pprint
    import time
    req = ""
    listDevices = get_device_list_rest(req)
    print "Available devices:", len(listDevices) 
    pprint(listDevices)

    for i in range(2):
        serial = listDevices[i]['serial']
        print serial
        pprint(listDevices[i])

        join_group(serial)
        remote_connect(serial)

        time.sleep(10)

        remote_disconnect(serial)
        leave_group(serial)

    # listFields = get_device_list_fields(req, fields)
    # print ''
    # print listFields

    # get use statistics data
    # res_info = get_use_statistics(req)
    # print res_info
