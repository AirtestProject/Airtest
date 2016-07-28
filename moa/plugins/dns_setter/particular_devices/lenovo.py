# coding=utf-8
__author__ = 'lxn3032'


import time
from . import particular_case


LENOVO_PAD = ('CQSCMVOFHI5TEY8D', )


class LenovoPad(object):
    @particular_case.specified(LENOVO_PAD)
    def enter_wlan_settings(self):
        self.d(text='netease_game').long_click()
        time.sleep(0.5)
        self.d(text=u'修改网络').click()
        time.sleep(0.5)

    @particular_case.specified(LENOVO_PAD)
    def is_dhcp_mode(self):
        ipsettings = self.uiutil.scroll_find({'text': u'IP 设置'}).right(className="android.widget.TextView")
        if ipsettings and ipsettings.exists:
            if ipsettings.text == 'DHCP':
                return True
        return False

    @particular_case.specified(LENOVO_PAD)
    def use_dhcp(self):
        ipsettings = self.uiutil.scroll_find({'text': u'IP 设置'}).right(className="android.widget.TextView")
        ipsettings.click()
        time.sleep(0.5)
        self.uiutil.click_any({'text': 'DHCP'})
        self.uiutil.click_any({'text': u'保存'})

    @particular_case.specified(LENOVO_PAD)
    def use_static_ip(self):
        ipsettings = self.uiutil.scroll_find({'text': u'IP 设置'}).right(className="android.widget.TextView")
        ipsettings.click()
        time.sleep(0.5)
        self.uiutil.click_any({'text': '静态'})

    @particular_case.specified(LENOVO_PAD)
    def modify_wlan_settings_fields(self, dns1, ip_addr=None, gateway=None, masklen=None):
        dnsfield = self.uiutil.scroll_find({'text': u'域名 1'}).right(className="android.widget.EditText")
        self.uiutil.replace_text(dnsfield, dns1)
        self.uiutil.click_any({'text': u'保存'})
        time.sleep(2)
