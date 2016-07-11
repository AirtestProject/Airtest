# encoding=utf-8
import os
import requests
import sys


def get_script_dirs(path):
    """获取脚本列表"""
    for root, dirs, files in os.walk(path, True):
        for name in dirs:
            if name.endswith(".owl"):
                print(os.path.join(root,name))

def write_number_to_file(number):
    print number

def restart_from_checkpoint(Number,checkpoint,job):
    url = "http://192.168.40.218:8081/job/%s/%s/checkpoints/%s/restart" % (job,Number,checkpoint)
    requests.post(url)

if __name__ == '__main__':
    action = sys.argv[1]
    thismodule = sys.modules[__name__]
    func = getattr(thismodule, action, None)
    if not func:
        raise Exception("invalid action:"+action)
    func(*sys.argv[2:])
