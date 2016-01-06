# -*- coding: utf-8 -*-
import urllib2
HOSTNUM = 16
HOSTIP = "192.168.229.198"
UID = '110353'


@logwrap
def server_call(cmdline, hostnum=None, ip=None):
    if hostnum is None:
        hostnum = HOSTNUM
    if ip is None:
        ip = HOSTIP
    print hostnum, ip

    ##支持gm指令
    gm = cmdline.split(" ")
    gm_cmd = gm[0]
    gm_args = " ".join(gm[1:])
    if gm_cmd != "call":
        cmdline = "call cmd/wizcmd->do_command(%s,\"%s\")" %(UID,cmdline)
        print cmdline

    pos=cmdline.find(' ')
    if pos==-1:
        cmd=cmdline
        args=''
    else:
        cmd=cmdline[:pos]
        args=cmdline[pos:].strip()
    url='http://%s:%d38/gmcmd?cmd=%s&args=%s'%(ip,hostnum,cmd,args)
    req = urllib2.Request(url)
    res = urllib2.urlopen(req)
    the_page = res.read()
    try:
        exec("re=%s"%the_page)
    except:
        return False
    if not isinstance(re,dict):
        return False
    if re["status"]!='ok':
        return False
    size=len('执行完毕. 返回: ')
    #print re
    print re["result"]
    ret=re["result"][size:-2]
    print ret
