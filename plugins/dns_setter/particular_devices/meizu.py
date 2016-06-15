# coding=utf-8
__author__ = 'lxn3032'


import time
from . import particular_case


MX_MEILAN = ('88MFBM72H9SN', )
MX_MEILAN_NOTE = ('71MBBLA238NH', )
MX5_ALL = ('850ABM4YR6UW', )
MX4_ALL = ('76UBBLR2264A', '75UBBLE226QD')
MX3_ALL = ('351BBJPYF7PF', '351BBJPTHLR2', '351BBJPZ8F27')


class MX4(object):
    @particular_case.specified(MX4_ALL)
    def enter_wlan_list(self):
        self.adb.shell('am start -S "com.android.settings/.Settings" --activity-clear-top')
        self.d(text='WLAN').swipe.right()
        time.sleep(0.5)
        self.d(text='WLAN').click.topleft()
        time.sleep(0.5)

    @particular_case.specified(MX_MEILAN)
    @particular_case.specified(MX4_ALL)
    @particular_case.specified(MX5_ALL)
    def enter_wlan_advanced_settings(self):
        pass

    @particular_case.specified(MX_MEILAN)
    @particular_case.specified(MX4_ALL)
    @particular_case.specified(MX5_ALL)
    def use_static_ip(self):
        switch = self.d(text="静态IP", resourceId="android:id/title").right(className="com.meizu.common.widget.Switch")
        if not switch.checked:
            switch.click()
            time.sleep(0.5)

    @particular_case.specified(MX_MEILAN)
    @particular_case.specified(MX4_ALL)
    @particular_case.specified(MX5_ALL)
    def modify_wlan_settings_fields(self, dns1, back_after_texting=False):
        uiobj = self.d(text=u'域名 1').right(className="android.widget.EditText")
        self.uiutil.replace_text(uiobj, dns1, back_after_texting)
        self.uiutil.click_any({'text': u'保存'})


class MX3(object):
    @particular_case.specified(MX3_ALL)
    def enter_wlan_settings(self):
        self.d(text='netease_game').long_click()
        time.sleep(0.5)
        self.uiutil.click_any({'text': u'静态IP'})

    @particular_case.specified(MX3_ALL)
    def enter_wlan_advanced_settings(self):
        pass

    @particular_case.specified(MX3_ALL)
    def use_static_ip(self):
        switch = self.d(className="android.widget.Switch", text=u'关闭')
        if switch:
            switch.click()
            time.sleep(0.5)

    @particular_case.specified(MX3_ALL)
    def modify_wlan_settings_fields(self, dns1, back_after_texting=False):
        uiobj = self.d(text=u'域名 1').right(className="android.widget.EditText")
        self.uiutil.replace_text(uiobj, dns1, back_after_texting)
        self.uiutil.click_any({'text': u'保存'})


class MeiLanNote(object):
    @particular_case.specified(MX_MEILAN_NOTE)
    def connect_netease_game(self):
        netease_game = self.uiutil.scroll_find({'text': 'netease_game'})
        if not netease_game:
            raise Exception('AP netease_game not found')

        for i in range(10):
            connected_flag = netease_game.sibling(className="android.widget.TextView")
            if not connected_flag:
                netease_game.click()
                time.sleep(0.5)
            elif connected_flag.text == u'已连接':
                break
            time.sleep(1)

    @particular_case.specified(MX_MEILAN_NOTE)
    def enter_wlan_settings(self):
        self.uiutil.click_any({'text': 'netease_game'})
        time.sleep(1)
        self.uiutil.click_any({'text': u'静态 IP'})

    @particular_case.specified(MX_MEILAN_NOTE)
    def enter_wlan_advanced_settings(self):
        pass

    @particular_case.specified(MX_MEILAN_NOTE)
    def use_static_ip(self):
        switch = self.d(className="com.meizu.common.widget.Switch")
        if not switch.checked:
            switch.click()
            time.sleep(0.5)

    @particular_case.specified(MX_MEILAN_NOTE)
    def modify_wlan_settings_fields(self, dns1, back_after_texting=False):
        uiobj = self.d(text=u'DNS 1').right(className="android.widget.EditText")
        self.uiutil.replace_text(uiobj, dns1, back_after_texting)
        self.uiutil.click_any({'text': u'保存'})
