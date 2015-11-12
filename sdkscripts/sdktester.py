# encoding=utf8
import sys
import os
sys.path.insert(0, "..")
from moa.moa import *
from moa import moa


class sdktester(object):
    apk_name = 'netease.apk'
    #pkg_name = 'com.netease.xyq'
    pkg_name = 'com.example.netease'
    username = 'unisdktester@163.com'
    password = '163a163a'
    icon_sdk_login = 'sdk_login_icon.png'
    icon_sdk_login_submit = 'sdk_login_submit.png'
    icon_sdk_tips = 'sdk_tips.png'
    icon_login_success = 'login_success.png'

    def connect_device(self):
        set_serialno()
        sleep(3)

    def install_sdk(self):
        install_result = moa.install(self.apk_name)
        print install_result
        if install_result.find("Success") < 0 :
            raise  Exception("install fail")
        else:
            print "install apk success"
        sleep(3)

    def start_sdk(self):
        moa.amstart(self.pkg_name)
        sleep(10)

    def stop_sdk(self):
        moa.amstop(self.pkg_name)
        sleep(3)

    def click_sdk_login(self):
        sleep(4)
        snapshot("before_click.jpg")
        touch(self.icon_sdk_login)
        sleep(3)
        moa.text(self.username)
        sleep(10)
        moa.keyevent("66")
        sleep(10)
        moa.text(self.password)
        sleep(5)
        touch(self.icon_sdk_login_submit)
        sleep(5)
        touch(self.icon_sdk_tips)

    def check_login(self):
        if moa.exists(self.icon_login_success):
            print "check login success"
        else:
            raise Exception("check login failed")

    def uninstall_sdk(self):
        uninstall_result = moa.uninstall(self.pkg_name)
        if uninstall_result.find("Success") < 0 :
            raise  Exception("uninstall fail")
        else:
            print "uninstall apk success"

    def run_test(self):
        self.connect_device()
        self.install_sdk()
        self.start_sdk()
        self.click_sdk_login()
        self.check_login()
        self.stop_sdk()
        self.uninstall_sdk()
        print "auto test pass"
        
if __name__ == '__main__':
    abc = sdktester()
    abc.run_test()
    

    
