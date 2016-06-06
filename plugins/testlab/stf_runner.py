from moa.core.android.android import Android
from pprint import pprint
import stf
import sys
import os


def join(serialno):
    join = stf.join_group(serialno)
    if not join['success']:
        pprint(join)
        raise RuntimeError("join group failed")



def run(serialno):
    connect = stf.remote_connect(serialno)
    if not connect["success"]:
        pprint(connect)
        raise RuntimeError("remote connect failed")
    addr = connect["remoteConnectUrl"]

    a = Android(addr)
    a.wake()
    # if a.is_locked():
    #     raise
    a.touch((100,100))


def cleanup(serialno):
    stf.remote_disconnect(serialno)
    stf.leave_group(serialno)


if __name__ == '__main__':
    action = sys.argv[1]
    serialno = sys.argv[2]
    thismodule = sys.modules[__name__]
    func = getattr(thismodule, action, None)
    if not func:
        raise Exception("invalid action:"+action)
    func(serialno)
