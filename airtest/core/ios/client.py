#! /usr/bin/env python
# -*- coding: utf-8 -*-

# import utils  # 暂时不用使用，需要修改utils里的逻辑
from airtest.aircv import aircv
from airtest.core.device import Device
from airtest.core.utils.logger import get_logger
import wda


logger = get_logger("ios")


class IOS(Device):
    """ios client
        # befor this you have to run WebDriverAgent
        # xcodebuild -project path/to/WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination "id=$(idevice_id -l)" test
        # iproxy $port 8100 $udid
    """

    def __init__(self, udid):
        super(IOS, self).__init__()
        self.udid = udid

        # auto detect local device or remote device. using default 8100 port for local device's wda
        if 'http' in udid and '//' in udid:
            device_url = udid
        else:
            device_url = 'http://localhost:8100'

        # wda driver, use to home, start app
        # init wda session, updata when start app
        # use to click/swipe/close app/get wda size
        self.driver = wda.Client(device_url)
        self.session = self.driver.session()
        self._last_activated_session_name = None  # package or bundleId
        self._size = {}
        self._wda_sca = 1

        # take a snapshot to refresh display info
        self.snapshot()

    def shell(self):
        raise NotImplementedError

    def wake(self):
        try:
            self.driver.home()  # active screen backlight
            self.driver.home()  # slide to unlock
            self.driver.home()  # enter SpringBoard if other app is running
        except wda.WDAError:
            pass

    def home(self):
        self.driver.home()

    def snapshot(self, filename=None):
        return self._snapshot(filename)
        
    def _snapshot(self, filename=None):
        """
        take snapshot
        filename: save screenshot to filename
        """
        filename = filename or "tmp.png"
        data = self.driver.screenshot(filename)  # wda 截图不用考虑朝向

        # 输出cv2对象
        screen = aircv.string_2_img(data)
        self.refresh_display_info(screen)
        return screen

    def touch(self, pos, duration=None):
        self.session.tap(pos[0] / self._wda_sca, pos[1] / self._wda_sca)

    def swipe(self, fpos, tpos, duration=0.5, step=4):
        self.session.swipe(fpos[0] / self._wda_sca, fpos[1] / self._wda_sca,
                           tpos[0] / self._wda_sca, tpos[1] / self._wda_sca, step)

    def keyevent(self, key):
        key = key.upper()
        if key == 'HOME':
            self.home()
        else:
            EVENT_CODE_TABLE = {
                'ENTER': '\n',
                'KEYCODE_DEL': '\b',
            }
            key = EVENT_CODE_TABLE.get(key)
            self._send_keys(key)

    def text(self, text, enter=True):
        """you need to click textfield first"""
        self._send_keys(text)
        if enter:
            self.keyevent('ENTER')

    def _send_keys(self, keys):
        for i in range(3):
            # try N times waiting for keyboard present
            try:
                self.session.send_keys(keys)
                break
            except wda.WDAError:
                pass

    def start_app(self, package, activity=None):
        """launch an app by appid"""
        logger.info("current package is {}, will launch {}".format(self._last_activated_session_name, package))
        if self._last_activated_session_name != package or self.driver.status()['sessionId'] != self.session._sid:
            self._last_activated_session_name = package
            self.session = self.driver.session(package)

    def stop_app(self, package):
        """stop an app by appid"""
        logger.info("current package is {}, will stop {}".format(self._last_activated_session_name, package))
        if self._last_activated_session_name == package:
            self._last_activated_session_name = None
        else:
            logger.warn("stop package not at top activity is not recommended.")
        self.session.close()
        self.session = self.driver.session()  # get default session

    def clear_app(self, upload_file_path):
        pass
        # utils.cleanup(upload_file_path, self.udid)

    def install_app(self, filepath, reinstall=True, appid=None):
        pass
        # if reinstall:
        #     utils.uninstall_app(appid, self.udid)
        # upload_file_path = utils.upload_file(filepath, udid=self.udid)
        # utils.install_file(upload_file_path)
        # self.clear_app(upload_file_path)

    def uninstall_app(self, package):
        pass
        # utils.uninstall_app(package, self.udid)

    def getPhysicalDisplayInfo(self):
        pass

    def getDisplayOrientation(self):
        """
        return orientation code
        """
        try:
            orientation = self.session.orientation  # 不在主屏中且没有调用过start_app会报错
            return 0 if orientation == 'PORTRAIT' else 1
        except wda.WDAError:
            return 0

    # use to resize
    def getCurrentScreenResolution(self):
        return self._size["width"], self._size["height"]

    def refreshOrientationInfo(self, ori=None):
        """
        update dev orientation
        if ori is assigned, set to it(useful when running a orientation monitor outside)
        """
        pass

    def refresh_display_info(self, screen):
        """
        Returns:
        display info as <dict>
          rotation: <int> in degrees
          height, width: <int> logic pixels of screen output, not the touch panel
        """
        self._size["orientation"] = self.getDisplayOrientation()
        self._size["rotation"] = self._size["orientation"] * 90
        self._size["height"], self._size["width"] = screen.shape[:2]
        self._wda_sca = 1.0 * min(self._size["height"], self._size["width"]) / min(self.session.window_size())
        print self._size
        return self._size

    def get_device_external_ip(self):
        return self.driver.status()['ios']['ip']


if __name__ == "__main__":
    ios = IOS('http://10.251.93.160:8100')
    # print dir(ios)
    # try:
    #     ios.home()
    #     ios.home()
    #     ios.home()
    # except wda.WDAError:
    #     pass
    # ios.start_app('com.netease.mhxyhtb')
    # ios.stop_app('com.netease.mhxyhtb')
    print ios.getCurrentScreenResolution()
