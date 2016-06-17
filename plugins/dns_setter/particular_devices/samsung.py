# coding=utf-8
__author__ = 'lxn3032'


import time
from . import particular_case


GALAXY = ('07173333', )


class Galaxy(object):
    @particular_case.specified(GALAXY)
    def enter_wlan_settings(self):
        self.d(text='netease_game').long_click()
        time.sleep(0.5)
        self.uiutil.click_any({'textMatches': ur'^.*(修改|設定)(網|网)(路|絡|络).*$'})

    @particular_case.specified(GALAXY)
    def use_static_ip(self):
        ipsetting = self.uiutil.scroll_find({'text': "IP 设定"})
        ipsetting.down(className="android.widget.Spinner").click()
        time.sleep(0.5)
        self.uiutil.click_any({'textMatches': ur'静止'})
        time.sleep(1)

    @particular_case.specified(GALAXY)
    def modify_wlan_settings_fields(self, dns1):
        for _ in range(5):
            self.uiutil.get_scrollable().scroll.forward(steps=10)

        # scroll back to find dns 1
        dns_title = self.d(text="DNS 1")
        while not dns_title.exists:
            self.uiutil.get_scrollable().scroll.backward(steps=20)
            dns_title = self.d(text="DNS 1")

        uiobj = dns_title.down(className="android.widget.EditText")
        self.uiutil.replace_text(uiobj, dns1)
        self.uiutil.click_any({'textMatches': ur'保存|确定|儲存|储存|ok|OK|Ok'})
