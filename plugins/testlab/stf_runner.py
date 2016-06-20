# encoding=utf-8
from moa.core.android.android import Android
from config import PKG_NOT_REMOVE, TEST_DEVICE_LIST
from pprint import pprint
import stf
import sys
import os


def devices():
    listDevices = stf.get_device_list_rest("")
    for i in listDevices:
        if i['serial'] in TEST_DEVICE_LIST:
            serialno = i['serial']
            print serialno


def join(serialno):
    """
    占用stf设备，通过设备号获取connect的地址
    注意，这里将print addr作为输出，一定不要print其他信息(坑爹的jenkins pipeline)
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


def setdns(sn, addr, dns):
    """设置dns"""

    # these two device cannot connect to netease_game
    if sn in ('045BBI2H9F9B', ):
        return

    # # stuck with uiautomator
    # if sn in ('4df74f4b47e33081', ):
    #     return

    #
    # # skip device too slow
    # if sn in ('KVAM59CYHYWOS8V8', 'f565e08', '296eea5d', 'f565e08', 'AVY9KA95A2106482', '3230dd49644a10ad', 'X2P0215508002471', 'MXF5T15831007688', 'EMW8BYLJHANZCIBM', 'NX513J', 'JAEDU15A16007444'):
    #     return
    #
    # # cannot not auto install apk
    # if sn in ('JTJ4C15710038858', 'CQ556955VKOV5T4D', 'GYZL4H556HCUH6RK', 'cc9de083'):
    #     return
    #

    # connot save dns settings
    if sn in ('fdcbcc83', '8d260bf7'):
        return
    #
    # # 手机有问题，桌面黑黑的
    # if sn in ('TA9921AVZE', ):
    #     return

    from moa.plugins.dns_setter import DnsSetter
    a = Android(addr, init_display=False, minicap=False, minitouch=False, init_ime=False)
    a.wake()
    dsetter = DnsSetter(addr, sn)
    dsetter.network_prepare()
    dsetter.set_dns(dns)
    a.home()


def clearapk(addr):
    """清理设备，以留出足够的空间"""
    a = Android(addr, init_display=False, minicap=False, minitouch=False, init_ime=False)
    pkgs = a.amlist(third_only=True)
    pkgs = [i for i in pkgs if i.startswith("com.netease.")]
    for i in (set(pkgs) - set(PKG_NOT_REMOVE)):
        print "clear app:", i
        a.amclear(i)
        a.amuninstall(i)


def install(addr, apk):
    """安装apk"""
    clearapk(addr)
    a = Android(addr, init_display=False, minicap=False, minitouch=False, init_ime=False)
    a.install(apk, reinstall=True, check=True)


def startapp(addr, package):
    """打开app"""
    a = Android(addr, init_display=False, minicap=False, minitouch=False, init_ime=False)
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
