import requests
HOST, PORT = "192.168.10.191", 17800
HOST, PORT = "192.168.10.104", 27030 
USERNUM = 31996757

def server_call(cmd):
    r = requests.post("http://192.168.11.243:8015/webcmd", data={
            "serverport": PORT,
            "serverip": HOST,
            "usernum": USERNUM,
            "content": cmd
        })
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


if __name__ == '__main__':
    server_call("$at h")
    print server_call("at/G1/sm/main->get_sm_leaf(\"$id@89\")")

    print type(get_var('_gzj_true_pos'))
    print set_var('_gzj_true_pos',"abc" )
    print get_daycnt('im_private_task')
    print set_daycnt('im_private_task', 0)

