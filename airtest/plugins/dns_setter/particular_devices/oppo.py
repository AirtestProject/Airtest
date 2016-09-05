# coding=utf-8
__author__ = 'lxn3032'


import time
from . import particular_case


OPPO_R9 = ('QK7D6LDM4HWWOJBQ', )


class OPPOR9(object):
    @particular_case.specified(OPPO_R9)
    def connect_netease_game(self, strict=True):
        uiobj = self.d(text='netease_game')
        if not uiobj.exists:
            for i in range(10):
                uiobj = self.uiutil.scroll_find({'text': 'netease_game'})
                if uiobj:
                    break
                else:
                    self.uiutil.click_any({'text': '刷新'})
                time.sleep(2)
        if not uiobj or not uiobj.exists:
            raise Exception('AP netease_game not found')

        # check connection and click once to connect
        for i in range(10):
            connected = uiobj.sibling(resourceId="com.coloros.wirelesssettings:id/wifi_check")
            if not connected.checked:
                uiobj.click()
                time.sleep(1.5)
            else:
                break
        time.sleep(1)

        if strict:
            self.test_netease_game_connected()

    @particular_case.specified(OPPO_R9)
    def enter_wlan_settings(self):
        self.uiutil.click_any({'text': 'netease_game'})
        if not self.d(text=u'netease_game详情').exists:
            raise Exception('fail to enter wlan settings page')

    @particular_case.specified(OPPO_R9)
    def enter_wlan_advanced_settings(self):
        pass
