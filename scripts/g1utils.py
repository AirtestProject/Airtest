#coding:utf-8
import requests
import json
import re
HOST, PORT = "192.168.10.191", 17800
HOST, PORT = "192.168.10.104", 27030 
USERNUM = 31996757
# USERNUM = 31996760

def server_call(cmd):
    r = requests.post("http://192.168.11.243:8015/webcmd", data={
            "serverport": PORT,
            "serverip": HOST,
            "usernum": USERNUM,
            "content": cmd
        })
    # print r.text
    return r.text

#$at g1/get1 $id var
def get_var(varname):
    ret = server_call('mobile_app/role_cache->get_var("$id@89","%s")' % varname)
    try:
        ret = int(ret)
    except:
        return ret

    return ret

#$at g1/set1 $id var
def set_var(varname, value):
    if isinstance(value, basestring):
        server_call('mobile_app/role_cache->set_var("$id@89","%s","%s")' % (varname, value))
    else:
        server_call('mobile_app/role_cache->set_var("$id@89","%s",%d)' % (varname, value))

    return get_var(varname)

#$at g1/gday $id var
def get_daycnt(varname):
    ret = server_call('mobile_app/module/counter->get_counter("$id@89","day","%s")' % varname)

    try:
        ret = int(ret)
    except:
        return ret

    return ret

#$at g1/sday $id var
def set_daycnt(varname,value):
    if isinstance(value, basestring):
        server_call('mobile_app/module/counter->set_counter("$id@89","day","%s", "%s")' % (varname, value))
    else:
        server_call('mobile_app/module/counter->set_counter("$id@89","day","%s", %d)' % (varname, value))

    return get_var(varname)

def multiple_replace(text, adict):
     rx = re.compile('|'.join(map(re.escape, adict)))
     def one_xlat(match):
           return adict[match.group(0)]
     return rx.sub(one_xlat, text)

lpc_2_py_dict = {
    "([":"{",
    "])":"}",
    "({":"[",
    "})":"]",
}

last_comma = {
    ",}":"}",
    ",]":"]",
}

def lpc_mixed_2_py(mxvar):
    """
    将LPC的mixedload为python obj
    """
    def repl(matched):
        tmp = matched.group()
        for idx,x in enumerate(tmp):
            if x in [" ",":"]:
                return "\"%s\":"%tmp[:idx]

    def json_hook(data):
        if isinstance(data,dict):
            rv={}
            for key in data.keys():
                try:
                    tmpkey = int(key)
                    rv[tmpkey] = json_hook(data[key])
                    del data[key]
                except:
                    rv[key]=json_hook(data[key])
            return rv
        else:
            return data

    intkey = re.compile(r"(-)*(\d)+(\s)*\:")
    value = mxvar
    #lpc array/map --> python list/dict
    value = multiple_replace(value,lpc_2_py_dict)
    #int key --> string key
    value = re.sub(intkey,repl,value)
    #eliminate last , before } and ]
    value = multiple_replace(value,last_comma)
    #gbk-->unicode
    if isinstance(value,str):
        value = value.decode("gbk")
    value = json.loads(value,object_hook=json_hook)

    return value

if __name__ == '__main__':
    # server_call("$at h")
    # print server_call("at/G1/sm/main->get_sm_leaf(\"$id@89\")")
    # print server_call('at/G1/sm/main->check_sm($id, "$id@89", 5, 1, 0, 0)')
    # print type(get_var('_gzj_true_pos'))
    # print set_var('_gzj_true_pos',"abc" )
    # print get_daycnt('im_private_task')
    # # print set_daycnt('im_private_task', 0)
    # print lpc_mixed_2_py(get_daycnt('im_publice_task'))
    server_call("at g1/sday0 $id")
    server_call("at g1/set1 $id mfb 0")
    server_call("at/G1/atdriver->clear_all_task(\"$id@89\")")
    server_call("mb task_event set gEventProb 0")
    server_call("mb task_event set gEventFriend 88")
