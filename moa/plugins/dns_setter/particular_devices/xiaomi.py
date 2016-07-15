# coding=utf-8
__author__ = 'lxn3032'


import time
from . import particular_case


MI_2 = ('c0e82f5f', )
MI_2s = ('1197d597', )
MI_SERIALS = ('96528427', '4c6a4cf2', '4a139669', '4e49701b') + MI_2s + MI_2


class MIx(object):
    @particular_case.specified(MI_SERIALS)
    def enter_wlan_list(self):
        self.adb.shell('am start -a "android.net.wifi.PICK_WIFI_NETWORK" --activity-clear-top')
        time.sleep(0.5)

        # switch on
        wlan_switch = self.d(text='开启WLAN').right(checkable="true")
        if wlan_switch and wlan_switch.exists and not wlan_switch.checked:
            wlan_switch.click()

    @particular_case.specified(MI_SERIALS)
    def enter_wlan_advanced_settings(self):
        pass


class MI2s(MIx):
    @particular_case.specified(MI_2s)
    def get_current_ssid(self):
        current_wlan_title = self.d(text=u'连接的WLAN')
        if current_wlan_title and current_wlan_title.exists:
            current_wlan = current_wlan_title.down(resourceId="android:id/title")
            if current_wlan and current_wlan.exists:
                return current_wlan.text
        return None

class MI2(MIx):
    @particular_case.specified(MI_2)
    def enter_wlan_settings(self):
        self.d(text='netease_game').right(clickable=True, className='android.widget.ImageView').click()
        time.sleep(0.5)

    @particular_case.specified(MI_2)
    def modify_wlan_settings_fields(self, dns1, ip_addr=None, gateway=None, masklen=None):
        for _ in range(5):
            self.uiutil.get_scrollable().scroll.vert.forward(steps=50)
        uiobj = self.d(text=u'域名 1').right(className='android.widget.EditText')
        self.uiutil.replace_text(uiobj, dns1)
        self.uiutil.click_any({'text': u'确定'})
