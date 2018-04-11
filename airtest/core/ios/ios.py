#! /usr/bin/env python
# -*- coding: utf-8 -*-


import requests
import six
import time
import json
import wda

if six.PY3:
    from urllib.parse import urljoin
else:
    from urlparse import urljoin

from airtest import aircv
from airtest.core.device import Device
from airtest.core.ios.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD
from airtest.utils.logger import get_logger


logger = get_logger(__name__)
DEFAULT_ADDR = "http://localhost:8100/"


class IOS(Device):
    """ios client
        # befor this you have to run WebDriverAgent
        # xcodebuild -project path/to/WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination "id=$(idevice_id -l)" test
        # iproxy $port 8100 $udid
    """

    def __init__(self, addr=DEFAULT_ADDR,
                 cap_method=CAP_METHOD.WDACAP,
                 touch_method=TOUCH_METHOD.WDATOUCH,
                 ime_method=IME_METHOD.WDAIME):
        super(IOS, self).__init__()
        self.addr = addr
        self.cap_method = cap_method
        self.touch_method = touch_method
        self.ime_method = ime_method

        # wda driver, use to home, start app
        # init wda session, updata when start app
        # use to click/swipe/close app/get wda size
        wda.DEBUG = True
        self.driver = wda.Client(addr)
        self._size = {'width': 0, 'height': 0}
        self._touch_factor = 0.5

    @property
    def session(self):
        return self.driver.session()

    def home(self):
        return self.driver.home()

    def snapshot(self, filename=None):
        """
        take snapshot
        filename: save screenshot to filename
        """
        data = None

        if self.cap_method == CAP_METHOD.MINICAP:
            raise NotImplementedError
        elif self.cap_method == CAP_METHOD.MINICAP_STREAM:
            raise NotImplementedError
        elif self.cap_method == CAP_METHOD.WDACAP:
            data = self.driver.screenshot(filename)  # wda 截图不用考虑朝向
        
        # output cv2 object 
        try:
            screen = aircv.utils.string_2_img(data)
        except:
            # may be black/locked screen or other reason, print exc for debugging
            import traceback
            traceback.print_exc()
            return None

        return screen

    def touch(self, pos, times=1, duration=0.01):
        x, y = pos[0] * self._touch_factor, pos[1] * self._touch_factor
        # if times == 2:
        #     self.session.double_tap(x, y)
        # else:
        #     for _ in range(times):
        #         self.session.tap(x, y)
        r = requests.get(urljoin(self.addr, "status"))
        sid = r.json()["sessionId"]
        url = urljoin(self.addr, "session/%s/wda/tap/0" % sid)
        print(url, x, y)
        r = requests.post(url, json={"x": x, "y": y})
        print(r.json())
        return r

    def swipe(self, fpos, tpos, duration=0.5):
        self.session.swipe(fpos[0] * self._touch_factor, fpos[1] * self._touch_factor,
                           tpos[0] * self._touch_factor, tpos[1] * self._touch_factor, duration)

    def keyevent(self, keys):
        """bug in wda for now"""
        self.session.send_keys(keys)

    def text(self, text, enter=True):
        """bug in wda for now"""
        if enter:
            text += '\n'
        self.keyevent(text)

    def install_app(self, uri, package):
        """
        curl -X POST $JSON_HEADER \
        -d "{\"desiredCapabilities\":{\"bundleId\":\"com.apple.mobilesafari\", \"app\":\"[host_path]/magicapp.app\"}}" \
        $DEVICE_URL/session
        https://github.com/facebook/WebDriverAgent/wiki/Queries
        """
        raise NotImplementedError

    def start_app(self, package):
        self.driver.session(package)

    def stop_app(self, package):
        self.driver.session().close()

    def get_ip_address(self):
        """
        get ip address from webDriverAgent

        Returns:
            raise if no IP address has been found, otherwise return the IP address

        """
        return self.driver.status()['ios']['ip']

    def device_status(self):
        """
        show status return by webDriverAgent
        Return dicts of infos
        """
        return self.driver.status()


if __name__ == "__main__":
    start = time.time()
    ios = IOS()

    ios.snapshot()
    # ios.touch((242 * 2 + 10, 484 * 2 + 20))
    
    # ios.start_app("com.tencent.xin")
    ios.home()
    ios.start_app('com.apple.mobilesafari')
    ios.touch((88, 88))
    ios.stop_app('com.apple.mobilesafari')
    ios.swipe((100, 100), (800, 100))

    print(ios.device_status())
    print(ios.get_ip_address())
