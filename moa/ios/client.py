#! /usr/bin/env python
# -*- coding: utf-8 -*-

# import sys
# sys.path.append("..")
# from error import MoaError
from ..error import MoaError
import utils
from ...aircv import aircv

class IOS(object):
    """ios client"""

    def __init__(self,udid=None):
        self.udid = udid
        self.get_display_info()

    def launch_app(self, appid):
        """launch an app by appid"""
        utils.launch_app(appid, self.udid)

    def stop_app(self, appid):
        """stop an app by appid"""
        utils.stop_app(appid, self.udid)

    def install(self, ipa_name):
        """
        install an app on device
        ipa_name: local ipa file name
        """

        upload_file_path = utils.upload_file(ipa_name,udid=self.udid)
        utils.install_file(upload_file_path)

    def uninstall(self, appid):
        """unistall an app on device by appid"""

        utils.uninstall_app(appid, self.udid)

    def snapshot(self, filename="tmp.png"):
        """
        take snapshot
        filename: save screenshot to filename
        """
        datas = utils.screenshot(self.udid)
        try:
            open(filename,'wb').write(datas)
        except IOError:
            raise MoaError("snapshot error, write file %s failed" %filename)
        else:
            # 输出cv2对象
            screen = aircv.string_2_img(datas)
            return screen

    def get_display_info(self):
        self.size = self.getPhysicalDisplayInfo()
        self.size["orientation"] = self.getDisplayOrientation()
        self.size["rotation"] = self.size["orientation"] * 90
        return self.size

    def getPhysicalDisplayInfo(self):
        """
        get size of screen, height must be bigger then width
        """

        screen = self.snapshot()
        h,w = screen.shape[:2]
        size = dict(
            width = w,
            height = h,
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
