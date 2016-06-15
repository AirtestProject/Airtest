# encoding=utf-8
from moa.core.android.android import Android
# from moa import airtest_runner
from pprint import pprint
import stf
import sys
import os


def devices():
    listDevices = stf.get_device_list_rest("")
    for i in listDevices:
        serialno = i['serial']
        print serialno


def join(serialno):
    """
    占用stf设备，通过设备号获取connect的地址
    注意，这里不能print addr作为输出，一定不要print其他信息(坑爹的jenkins pipeline)
    """
    join = stf.join_group(serialno)
    if not join['success']:
        pprint(join)
        raise RuntimeError("join group failed")

    connect = stf.remote_connect(serialno)
    if not connect["success"]:
        # pprint(connect)
        raise RuntimeError("remote connect failed")
    addr = connect["remoteConnectUrl"]
    print addr
    return addr


def test(addr):
    """测试任务"""
    a = Android(addr, minicap=False, minitouch=False)
    a.wake()
    # if a.is_locked():
    #     raise
    a.touch((100,100))
    a.snapshot()
    # a.install(r"C:\Users\game-netease\Desktop\thdmx\apks\thdmx_netease_coolapk_dev_1.0.5.apk")
    # a.amstart("com.netease.thdmx")


def setdns(addr, dns):
    """设置dns"""
    pass


def install(addr, apk):
    """安装apk"""
    a = Android(addr, minicap=False, minitouch=False)
    a.install(apk, reinstall=True, check=True)


def startapp(addr, package):
    """打开app"""
    a = Android(addr, minicap=False, minitouch=False)
    a.amstart(package)


def run(addr, moa_script):
    """运行moa任务，并生成报告"""
    import shutil
    import subprocess
    filename = os.path.basename(moa_script)
    shutil.copytree(moa_script, filename)
    p = subprocess.Popen(["python", "-m", "moa.airtest_runner", filename,
        "--setsn", addr, "--log", "--screen"
    ])
    p.wait()
    exit(p.returncode)


def report(moa_script_name, filename, staticroot):
    import subprocess
    p = subprocess.Popen(["python", "-m", "moa.report.report_one", moa_script_name, filename, staticroot])
    p.wait()
    exit(p.returncode)


def upload(src, dst):
    import pyscp
    pyscp.upload(src, os.path.join("/home/gzliuxin/testlab/", dst))


def cleanup(serialno):
    """清场，释放stf设备"""
    stf.remote_disconnect(serialno)
    stf.leave_group(serialno)


if __name__ == '__main__':
    action = sys.argv[1]
    thismodule = sys.modules[__name__]
    func = getattr(thismodule, action, None)
    if not func:
        raise Exception("invalid action:"+action)
    func(*sys.argv[2:])
