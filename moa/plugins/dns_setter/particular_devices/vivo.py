# coding=utf-8
__author__ = 'lxn3032'


import time
from . import particular_case


Y27 = ('1042dc55', )
X6S = ('296eea5d', )
VIVO_SERIALS = ('ZTAMDU49ZT59TOAE', 'CQ556955VKOV5T4D', 'JBRSCYZTS8JN7HZD', '38d6d441')


class Vivo(object):
    @particular_case.specified(VIVO_SERIALS)
    def connect_netease_game(self, strict=True):
        uiobj = self.d(text='netease_game')
        if not uiobj.exists:
            for i in range(5):
                uiobj = self.uiutil.scroll_find({'text': 'netease_game'})
                if uiobj:
                    break
                time.sleep(3)
        if not uiobj or not uiobj.exists:
            raise Exception('AP netease_game not found')
        uiobj.click()
        time.sleep(1)

        # 优先连接
        self.uiutil.click_any({'textMatches': ur'连接|連接'}, {'textMatches': ur'完成|取消|关闭|關閉'})
        time.sleep(1.5)
        connected = self.d(text=u"选取网络").up(text='netease_game')
        for i in range(20):
            if not connected:
                time.sleep(2)
                connected = self.d(text=u"选取网络").up(text='netease_game')
            else:
                break
        if strict:
            self.test_netease_game_connected()

    @particular_case.specified(VIVO_SERIALS)
    def is_dhcp_mode(self):
        # 通过网关这个ui来判断是否静态ip的按钮打开了
        switch = self.d(text=u'网关')
        return not switch.enabled

    @particular_case.specified(VIVO_SERIALS)
    def use_dhcp(self):
        switch = self.d(text=u'网关')
        if switch.enabled:
            self.d(text=u'静态IP').right(resourceId="android:id/checkbox").click()

    @particular_case.specified(VIVO_SERIALS)
    def use_static_ip(self):
        switch = self.d(text=u'网关')
        if not switch.enabled:
            self.d(text=u'静态IP').right(resourceId="android:id/checkbox").click()

    @particular_case.specified(VIVO_SERIALS)
    def modify_wlan_settings_fields(self, dns1, ip_addr=None, gateway=None, masklen=None):
        self.d(text='DNS 1').click()
        time.sleep(0.5)
        uiobj = self.uiutil.scroll_find({'resourceId': 'android:id/edit'})
        self.uiutil.replace_text(uiobj, dns1)
        self.d(text=u'确定').click()
        time.sleep(0.5)
        self.d.press.back()


class VivoY27(object):
    @particular_case.specified(Y27)
    def is_dhcp_mode(self):
        dnsfield = self.d(text=u'主域名服务器')
        return not dnsfield.enabled

    @particular_case.specified(Y27)
    def use_dhcp(self):
        switch = self.d(text=u"使用静态 IP").right(resourceId="android:id/checkbox")
        dnsfield = self.d(text=u'主域名服务器')
        if dnsfield.enabled:
            switch.click()
            time.sleep(0.5)
        self.uiutil.click_any({'text': u'确定'})
        self.d.press.back()

    @particular_case.specified(Y27)
    def use_static_ip(self):
        switch = self.d(text=u"使用静态 IP").right(resourceId="android:id/checkbox")
        dnsfield = self.d(text=u'主域名服务器')
        if not dnsfield.enabled:
            switch.click()
            time.sleep(0.5)

    @particular_case.specified(Y27)
    def connect_netease_game(self, strict=True):
        uiobj = self.uiutil.scroll_find({'text': 'netease_game'})
        if not uiobj:
            raise Exception('AP netease_game not found')
        uiobj.click()
        time.sleep(0.5)
        # 优先连接
        self.uiutil.click_any({'textMatches': ur'连接|連接'}, {'textMatches': ur'完成|取消|关闭|關閉'})
        # success = self.uiutil.wait_any({'text': u'已连接到 netease_game'}, timeout=10000)
        for i in range(30):
            if self.d(textMatches=ur'已连接到\s*netease_game').exists:
                return
            time.sleep(1)
        raise Exception('cannot connect to netease_game. network not available.')

    @particular_case.specified(Y27)
    def enter_wlan_settings(self):
        uiobj = self.d(text='netease_game').sibling(resourceId="com.android.wcnsettings:id/advance_layout")
        uiobj.click()
        time.sleep(0.5)

    @particular_case.specified(Y27)
    def modify_wlan_settings_fields(self, dns1, ip_addr=None, gateway=None, masklen=None):
        self.d(text='主域名服务器').click()
        time.sleep(0.5)
        uiobj = self.uiutil.scroll_find({'resourceId': 'android:id/edit'})
        self.uiutil.replace_text(uiobj, dns1)
        self.uiutil.click_any({'text': u'确定'})
        self.d.press.back()


class VivoX6S(object):
    @particular_case.specified(X6S)
    def connect_netease_game(self, strict=True):
        # vivo X6S Plus（全网通）
        uiobj = self.uiutil.scroll_find({'text': 'netease_game'})
        uiobj.click()
        time.sleep(1)
        self.uiutil.click_any({'textMatches': ur'连接|連接'}, {'textMatches': ur'完成|取消|关闭|關閉'})
        time.sleep(5)
        netease_game = self.d(text='netease_game')
        netease_game.click()
        time.sleep(0.5)
        success = self.uiutil.wait_any({'textMatches': ur'(已连接|已連線|connected).*$'}, timeout=30000)
        if not success:
            raise Exception('cannot connect to netease_game. network not available.')
        self.uiutil.click_any({'textMatches': ur'取消'})