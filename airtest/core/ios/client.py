#! /usr/bin/env python
# -*- coding: utf-8 -*-

# import sys
# sys.path.append("..")
# from error import MoaError
from airtest.core.error import MoaError
import utils
from airtest.aircv import aircv
from airtest.core.device import Device
from constant import *
from hunter_cli import Hunter
import time
import wda
import airtest
from cStringIO import StringIO
import base64
from PIL import Image


class XYTransformer(object):
    """
    transform xy by orientation
    add by gzzhengshenshen, it is different with android
    """

    @staticmethod
    def up_2_ori((x, y), (w, h), orientation):
        if orientation == 1:
            x, y = y, w - x
        elif orientation == 2:
            x, y = w - y, h - x
        elif orientation == 3:
            x, y = h - y, x
        return x, y


class IOS(Device):
    """ios client
        # befor this you have to run WebDriverAgent
        # xcodebuild -project path/to/WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination "id=$(idevice_id -l)" test
        # iproxy $port 8100 $udid
    """

    def __init__(self, udid=None, devip='10.254.40.44', process='mh', port=8100):
        self.udid = udid
        self.driver = wda.Client('http://localhost:%d' % (port))
        sessionId = self.driver.status()['sessionId']
        self.session = wda.Session('http://localhost:%d' % (port), sessionId)
        self.process = process
        hunter_tokenid = devip_tokenid.get(devip)
        self.hunter = Hunter(hunter_tokenid, process, devip=devip)
        self.get_display_info()

    def shell(self):
        raise NotImplementedError

    def home(self):
        self.driver.home()

    def snapshot(self, filename="tmp.png", quick=True):
        """
        take snapshot
        filename: save screenshot to filename
        """
        if quick:
            ##从hunter获取的图片大小和方向需要进行处理
            b64img = self.hunter.script('console.screenshot', watch='ret')
            datas = base64.b64decode(b64img)
            file_data = StringIO(datas)
            image = Image.open(file_data)
            # trans
            method = getattr(Image, 'ROTATE_{}'.format(360 - self.size["rotation"]))
            image = image.transpose(method)
            filename = filename or "tmp.png"
            image.save(filename)
            with open(filename) as f:
                datas = f.read()

        else:
            datas = utils.screenshot(self.udid)
            if filename:
                try:
                    open(filename, 'wb').write(datas)
                except IOError:
                    raise MoaError("snapshot error, write file %s failed" % filename)
        # 输出cv2对象
        screen = aircv.string_2_img(datas)
        self.hunter_sca = 1.0 * self.size["height"] / screen.shape[:2][0] if quick else 1
        return screen

    def touch(self, pos, duration=None, isWDA=False):
        pos = (pos[0] * self.hunter_sca, pos[1] * self.hunter_sca)
        if isWDA:
            self.session.tap(pos[0] / self.wda_sca, pos[1] / self.wda_sca)
        else:
            x, y = XYTransformer.up_2_ori(
                pos,
                (self.size["width"], self.size["height"]),
                self.size["orientation"]
            )
            touch_mode_name = process_op_mod[self.process]["touch"]
            touch_mod = self.hunter.require(touch_mode_name)
            touch_mod(x, y)

    def swipe(self, fpos, tpos, duration=0.5, step=2, isWDA=True):
        fpos = (fpos[0] * self.hunter_sca, fpos[1] * self.hunter_sca)
        tpos = (tpos[0] * self.hunter_sca, tpos[1] * self.hunter_sca)
        if isWDA:
            self.session.swipe(fpos[0] / self.wda_sca, fpos[1] / self.wda_sca,
                               tpos[0] / self.wda_sca, tpos[1] / self.wda_sca, step)

        else:
            x1, y1 = XYTransformer.up_2_ori(
                fpos,
                (self.size["width"], self.size["height"]),
                self.size["orientation"]
            )
            x2, y2 = XYTransformer.up_2_ori(
                tpos,
                (self.size["width"], self.size["height"]),
                self.size["orientation"]
            )

            swipe_mode_name = process_op_mod[self.process]["swipe"]
            swipe_mod = self.hunter.require(swipe_mode_name)
            swipe_mod(x1, y1, x2, y2, step)

    def keyevent(self):
        raise NotImplementedError

    def text(self, text):
        """you need to click first"""
        self.session.send_keys(text)

    def start_app(self, appid, isWDA=True):
        """launch an app by appid"""
        if isWDA:
            self.session = self.driver.session(appid)
        else:
            utils.launch_app(appid, self.udid)

    def stop_app(self, appid, isWDA=True):
        """stop an app by appid"""
        if isWDA:
            self.session.close()
        else:
            utils.stop_app(appid, self.udid)

    def clear_app(self, upload_file_path):
        utils.cleanup(upload_file_path, self.udid)

    def install_app(self, filepath, reinstall=True, appid=None):
        if reinstall:
            utils.uninstall_app(appid, self.udid)
        upload_file_path = utils.upload_file(filepath, udid=self.udid)
        utils.install_file(upload_file_path)
        self.clear_app(upload_file_path)

    def uninstall_app(self, appid):
        utils.uninstall_app(appid, self.udid)

    def get_display_info(self):
        self.size = self.getPhysicalDisplayInfo()
        self.wda_sca = min(self.size.values()) / min(self.session.window_size())
        self.hunter_sca = 1
        self.size["orientation"] = self.getDisplayOrientation()
        self.size["rotation"] = self.size["orientation"] * 90
        return self.size

    def getPhysicalDisplayInfo(self):
        """
        get size of screen, height must be bigger then width
        """
        # have to take snapshot without quick
        screen = self.snapshot(filename="init.png", quick=False)
        h, w = screen.shape[:2]
        size = dict(
            width=w,
            height=h,
        )
        return size

    def getDisplayOrientation(self):
        """
        return orientation code
        """

        return utils.get_orientation(self.udid)

    def getCurrentScreenResolution(self):
        w, h = self.size["width"], self.size["height"]
        if self.size["orientation"] in [1, 3]:
            w, h = h, w
        return w, h

    def refreshOrientationInfo(self, ori=None):
        """
        update dev orientation
        if ori is assigned, set to it(useful when running a orientation monitor outside)
        """
        if ori is None:
            ori = self.getDisplayOrientation()
        self.size["orientation"] = ori
        self.size["rotation"] = ori * 90


if __name__ == "__main__":
    driver = IOS(udid=None, devip='10.254.40.44', process='mh')
    # driver.start_app('com.netease.mhxyhtb')
    # driver.stop_app('com.netease.mhxyhtb')
    # driver.home()
    # driver.touch((701, 168), isWDA=False)
    # driver.touch((726, 168), isWDA=False)

    # driver.touch("123")

    # driver.swipe((482, 753) ,(482, 670))






