#! /usr/bin/env python
# -*- coding: utf-8 -*-


import requests
import six
import time
import wda

if six.PY3:
    from urllib.parse import urljoin
else:
    from urlparse import urljoin

import aircv
from airtest.core.device import Device
from airtest.core.error import MoaError
from airtest.core.utils.logger import get_logger


logger = get_logger("ios")


class IOS(Device):
    """ios client
        # befor this you have to run WebDriverAgent
        # xcodebuild -project path/to/WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination "id=$(idevice_id -l)" test
        # iproxy $port 8100 $udid
    """

    def __init__(self, addr="http://localhost:8100/"):
        super(IOS, self).__init__()
        self.addr = addr

        # wda driver, use to home, start app
        # init wda session, updata when start app
        # use to click/swipe/close app/get wda size
        self.driver = wda.Client(addr)
        self.udid = self.driver.status()['udid']
        self.serialno = self.udid
        self._size = {'width': 0, 'height': 0}
        self._wda_sca = 1

        # take a snapshot to refresh display info
        self.refreshOrientationInfo()

    @property
    def session(self):
        return self.driver.session()

    def shell(self):
        raise NotImplementedError

    def wake(self):
        # TODO: 需要优化速度，按了home键并解了锁，如果没有进入到home而是回到某个应用的话，会白白等待20秒。
        # 需要判断当前是否解锁完成和是否处于home
        try:
            self.driver.home()  # active screen backlight
            self.driver.home()  # slide to unlock
            self.driver.home()  # enter SpringBoard if other app is running
        except wda.WDAError:
            pass

    def home(self):
        return self.driver.home()

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
        self._refresh_display_info(screen)
        return screen

    def touch(self, pos, times=1, duration=0.01):
        x, y = pos[0] / self._wda_sca, pos[1] / self._wda_sca
        if times == 2:
            self.session.double_tap(x, y)
        else:
            for _ in range(times):
                self.session.tap(x, y)

    def swipe(self, fpos, tpos, duration=0.5, step=5):
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
        if enter:
            text += '\n'
        self._send_keys(text)

    def _send_keys(self, keys):
        ex = None
        for i in range(3):
            # try N times waiting for keyboard present
            try:
                self.session.send_keys(keys)
                return
            except wda.WDAError as e:
                ex = e
        raise ex

    def start_app(self, package, activity=None):
        """
        Launch app by bundleId. A MoaError will raise if given bundleId not exists.
        """
        current_package = self.session.bundle_id
        logger.info("current app(bundleId) is {}, will launch {}".format(current_package, package))
        if current_package != package:
            if package not in self.list_app():
                raise MoaError('Fail to start app({}) because of not installed.'.format(package))
            self.driver.session(package)
            self._try_to_finish_alert('accept')

    def stop_app(self, package):
        """
        Stop current top activity app.
        Do nothing if the top activity's bundle id is not equal to package
        """
        current_package = self.session.bundle_id
        logger.info("current app(bundleId) is {}, will stop {}".format(current_package, package))
        self.session.close()

    def clear_app(self, upload_file_path):
        pass

    def list_app(self, third_only=True):
        r = requests.get(urljoin(self.addr, '/api/v1/packages'))
        if r.status_code == 200:
            packages = r.json()['value']
            return map(lambda v: v['bundleId'], packages)
        raise RuntimeError("fail to connect to wda when fetching package list. "
                           "status_code={}, content={}".format(r.status_code, r.text))

    def install_app(self, uri, package, **kwargs):
        uri = uri.strip()
        self.wake()
        self.driver.session('com.apple.mobilesafari')
        self._try_to_finish_alert('dismiss')
        url_control = self.session(class_name='Button', name='URL')
        url_control.tap()
        self.text(uri)
        time.sleep(3)

        self._try_to_finish_alert('accept')  # 是否打开App Store？
        if uri.endswith('.plist'):
            # 通过plist安装，是否安装？
            logger.info('install via .plist')
            self._try_to_finish_alert('accept')
        else:
            # 通过AppStore下载安装
            logger.info('install via App Store')
            purchase_button = self.session(class_name='Button', name='PurchaseButton')
            purchase_button_text = purchase_button.attribute('label')
            if purchase_button_text == u'下载':
                purchase_button.tap()
            else:
                raise MoaError("{} are not purchased from app store. "
                               "please purchase and trust the publisher first.".format(uri))
        self._wait_until_app_installed(package)

    def uninstall_app(self, package):
        installed_apps = self.list_app()
        if package in installed_apps:
            r = requests.delete(urljoin(self.addr, urljoin('/api/v1/packages/', package)))
            if r.status_code != 200 or not r.json()['success']:
                raise MoaError("fail to uninstall with network error. App(bundleId) is {}. status_code={}, text={}"
                               .format(package, r.status_code, r.text))
            if package not in self.list_app():
                return True
            else:
                raise MoaError("fail to uninstall, app still exists. App(bundleId) is {}. status_code={}, text={}"
                               .format(package, r.status_code, r.text))

    def getPhysicalDisplayInfo(self):
        raise NotImplementedError

    def getDisplayOrientation(self):
        """
        return orientation code
        """
        return self._size["orientation"]

    def getCurrentScreenResolution(self):
        """
        Get the resolution(w, h) of snapshot real size
        Returns:
            w, h
        """
        return self._size["width"], self._size["height"]

    def refreshOrientationInfo(self, ori=None):
        """
        update dev orientation
        Orientation will keep up to date automatically in this class impl
        """
        orientation = self.session.orientation
        self._size["orientation"] = 0 if orientation == 'PORTRAIT' else 1
        self._size["rotation"] = self._size["orientation"] * 90

    def _refresh_display_info(self, screen):
        """
        Returns:
        display info as <dict>
          rotation: <int> in degrees
          height, width: <int> logic pixels of screen output, not the touch panel
        """

        # 当画面确实发生了旋转才需要重新获取一次，否则不用刷新
        h, w = screen.shape[:2]
        if (h, w) != (self._size["height"], self._size["width"]):
            self.refreshOrientationInfo()
            self._size["height"], self._size["width"] = h, w
            self._wda_sca = 1.0 * min(self._size["height"], self._size["width"]) / min(self.session.window_size())
            print(self._size)
        return self._size

    def _try_to_finish_alert(self, method, times=1, interval=2):
        success = False
        for i in range(times):
            time.sleep(interval)
            try:
                fn = getattr(self.driver.session().alert, method)
                fn()
                success = True
                break
            except wda.WDAError:
                pass
        return success

    def _get_alert_text(self):
        for i in range(2):
            try:
                return self.driver.session().alert.text
            except wda.WDAError:
                time.sleep(2)
        return None

    def _wait_until_app_installed(self, package, timeout=800):
        check_interval = 3
        start_time = time.time()
        while time.time() - start_time < timeout:
            if package in self.list_app():
                return True
            else:
                self._try_to_finish_alert('accept')
                time.sleep(check_interval)
        raise MoaError('Fail to install because of timeout. timeout={}'.format(timeout))

    def get_device_external_ip(self):
        return self.driver.status()['ios']['ip']


if __name__ == "__main__":
    start = time.time()
    ios = IOS()
    ios.home()
    # ios._try_to_finish_alert('dismiss')
    # print(ios.list_app())
    # print(ios.start_app('com.netease.mhxyhtb'))
    # ios.uninstall_app('com.netease.oa2')
    # # ios.install_app('https://adl.netease.com/d/g/xyq/c/htb?from=qr', com.netease.mhxyhtb)
    # ios.install_app('itms-services://?action=download-manifest&url=https://m.oa.netease.com/IOS/newOA_iOS8.plist', 'com.netease.oa2')
    # ios.start_app('com.netease.oa2')
    # ios.uninstall_app('com.netease.oa2')
    # print time.time() - start
    # ios.start_app('com.netease.mhxyhtb')
    # ios.stop_app('com.netease.mhxyhtb')
    # print ios.getCurrentScreenResolution()
