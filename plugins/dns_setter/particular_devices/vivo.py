# coding=utf-8
__author__ = 'lxn3032'


import time
from . import particular_case


Y27 = ('1042dc55', )
VIVO_SERIALS = ('ZTAMDU49ZT59TOAE', 'CQ556955VKOV5T4D', 'JBRSCYZTS8JN7HZD', '38d6d441')



class Vivo(object):
    @particular_case.specified(VIVO_SERIALS)
    def use_static_ip(self):
        pass

    @particular_case.specified(VIVO_SERIALS)
    def modify_wlan_settings_fields(self, dns1, back_after_texting=False):
        self.d(text='DNS 1').click()
        time.sleep(0.5)
        uiobj = self.uiutil.scroll_find({'resourceId': 'android:id/edit'})
        self.uiutil.replace_text(uiobj, dns1, back_after_texting)
        self.d(text=u'确定').click()
        time.sleep(0.5)
        self.d.press.back()


class VivoY27(object):
    @particular_case.specified(Y27)
    def use_static_ip(self):
        switch = self.d(text=u"使用静态 IP").right(resourceId="android:id/checkbox")
        dnsfield = self.d(text=u'主域名服务器')
        if not dnsfield.enabled:
            switch.click()
            time.sleep(0.5)

    @particular_case.specified(Y27)
    def connect_netease_game(self):
        uiobj = self.uiutil.scroll_find({'text': 'netease_game'})
        if not uiobj:
            raise Exception('AP netease_game not found')
        uiobj.click()
        time.sleep(0.5)
        # 优先连接
        self.uiutil.click_any({'textMatches': ur'连接|連接'}, {'textMatches': ur'完成|取消|关闭|關閉'})
        # success = self.uiutil.wait_any({'text': u'已连接到 netease_game'}, timeout=10000)
        for i in range(10):
            if self.d(text=u'已连接到 netease_game').exists:
                return
            time.sleep(1)
        raise Exception('cannot connect to netease_game. network not available.')

    @particular_case.specified(Y27)
    def enter_wlan_settings(self):
        uiobj = self.d(text='netease_game').sibling(resourceId="com.android.wcnsettings:id/advance_layout")
        uiobj.click()
        time.sleep(0.5)

    @particular_case.specified(Y27)
    def modify_wlan_settings_fields(self, dns1, back_after_texting=False):
        self.d(text='主域名服务器').click()
        time.sleep(0.5)
        uiobj = self.uiutil.scroll_find({'resourceId': 'android:id/edit'})
        self.uiutil.replace_text(uiobj, dns1, back_after_texting)
        self.d(text=u'确定').click()
        time.sleep(0.5)
        self.d.press.back()
