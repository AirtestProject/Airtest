# coding=utf-8
__author__ = 'lxn3032'


import time
from . import particular_case


GALAXY = ('07173333', )
GALAXY_NOTE2 = ('4df74f4b47e33081', )


class Galaxy(object):
    @particular_case.specified(GALAXY)
    def enter_wlan_settings(self):
        self.d(text='netease_game').long_click()
        time.sleep(1)
        self.uiutil.click_any({'text': u'修改网络配置'})

    @particular_case.specified(GALAXY_NOTE2)
    @particular_case.specified(GALAXY)
    def is_dhcp_mode(self):
        ipsetting = self.uiutil.scroll_find({'text': "IP 设定"})
        ipsetting_field = ipsetting.down(className="android.widget.Spinner")
        if not ipsetting_field:
            raise Exception("cannot find ip settings field.")
        dhcp = ipsetting_field.child(text='DHCP', className='android.widget.TextView')
        return dhcp and dhcp.exists

    @particular_case.specified(GALAXY_NOTE2)
    @particular_case.specified(GALAXY)
    def use_dhcp(self):
        ipsetting = self.uiutil.scroll_find({'text': "IP 设定"})
        ipsetting.down(className="android.widget.Spinner").click()
        time.sleep(0.5)
        self.uiutil.click_any({'text': 'DHCP'})
        time.sleep(1)
        self.uiutil.click_any({'text': u'储存'})

    @particular_case.specified(GALAXY_NOTE2)
    @particular_case.specified(GALAXY)
    def use_static_ip(self):
        ipsetting = self.uiutil.scroll_find({'text': "IP 设定"})
        ipsetting.down(className="android.widget.Spinner").click()
        time.sleep(0.5)
        self.uiutil.click_any({'text': u'静止'})
        time.sleep(1)

    @particular_case.specified(GALAXY)
    def modify_wlan_settings_fields(self, dns1, ip_addr=None, gateway=None, masklen=None):
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


class GalaxyNoet2(object):
    @particular_case.specified(GALAXY_NOTE2)
    def connect_netease_game(self, strict=True):
        uiobj = self.d(text='netease_game')
        if not uiobj.exists:
            for i in range(5):
                uiobj = self.uiutil.scroll_find({'text': 'netease_game'})
                if uiobj:
                    break
                time.sleep(2)
        if not uiobj or not uiobj.exists:
            raise Exception('AP netease_game not found')
        uiobj.click()
        time.sleep(1)

        # 优先连接
        self.uiutil.click_any({'text': u'连接'}, {'text': u'取消'})
        self.uiutil.wait_any({'textMatches': ur'(已连接|已連線|connected).*$'}, timeout=30000)
        if strict:
            self.test_netease_game_connected()

    @particular_case.specified(GALAXY_NOTE2)
    def enter_wlan_settings(self):
        self.d(text='netease_game').long_click()
        time.sleep(1)
        self.uiutil.click_any({'text': u'修改网络配置'})

    @particular_case.specified(GALAXY_NOTE2)
    def enter_wlan_advanced_settings(self):
        uiobj = self.uiutil.scroll_find({'text': "显示高级选项"})
        if uiobj and not uiobj.checked:
            uiobj.click()
            time.sleep(0.5)

    @particular_case.specified(GALAXY_NOTE2)
    def modify_wlan_settings_fields(self, dns1, ip_addr=None, gateway=None, masklen=None):
        dnstitle = self.uiutil.scroll_find({'text': "DNS 1"})
        dnsfield = dnstitle.down(className="android.widget.EditText")
        if dnsfield:
            self.uiutil.replace_text(dnsfield, dns1)
        self.uiutil.click_any({'text': u'储存'})
