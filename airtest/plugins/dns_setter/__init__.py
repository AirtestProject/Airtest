# coding=utf-8
__author__ = 'lxn3032'


import time
import traceback
import re
import os
import uiutils

from particular_devices import particular_case
from particular_devices.xiaomi import MI2
from particular_devices.vivo import Vivo, VivoY27, VivoX6S
from particular_devices.meizu import MX4, MX3, MeiLanNote, MeilanMetal
from particular_devices.samsung import Galaxy, Galaxy4, GalaxyNote2, GalaxyNote5
from particular_devices.lenovo import LenovoPad
from particular_devices.oppo import OPPOR9

from airtest.core.android.android import Android
from airtest.core.android.uiautomator import Device
from airtest.core.android.android import ADB
from airtest.plugins.testlab import stf, stf_runner
from airtest.core.android.utils import iputils
from airtest.core.android.ime_helper import UiautomatorIme


SONY_XPERIA = ('CB5A1NW8WK', )


class DefaultDnsSetter(object):
    def __init__(self, rsn, sn):
        super(DefaultDnsSetter, self).__init__()
        self.rsn = rsn
        self.sn = sn
        self.d = Device(rsn)
        self.android = Android(rsn, init_display=False, minicap=False, minitouch=False, init_ime=True)
        self.adb = self.android.adb
        self.uiutil = uiutils.UIUtil(self.d)
        self.ime_helper = UiautomatorIme(self.adb)

        # ensure accessibility services disabled
        self.android.disable_accessibility_service()

    def clear_float_tips(self):
        self.uiutil.click_any({'text': u'取消'}, {'text': u'确定'}, {'text': u'好'})

    @particular_case.specified(['2053d814', 'd523384'])
    def enter_wlan_list(self):
        self.adb.shell('am start -a "android.settings.WIFI_SETTINGS" --activity-clear-top')

    @particular_case.default_call
    def enter_wlan_list(self):
        self.adb.shell('am start -a "android.net.wifi.PICK_WIFI_NETWORK" --activity-clear-top')

    @particular_case.default_call
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
        uiobj.click()
        time.sleep(1)

        # 优先连接
        self.uiutil.click_any({'textMatches': ur'连接|連接'}, {'textMatches': ur'完成|取消|关闭|關閉'})
        time.sleep(1.5)
        self.uiutil.wait_any({'textMatches': ur'(已连接|已連線|connected).*$'}, timeout=40000)
        if strict:
            self.test_netease_game_connected()

    @particular_case.specified(SONY_XPERIA)
    def enter_wlan_settings(self):
        self.d(text='netease_game').long_click()
        time.sleep(0.5)
        self.uiutil.click_any({'textMatches': ur'^.*(修改|設定)(網|网)(路|絡|络).*$'}, {'textMatches': ur'^.*(網|网)(路|絡|络)(修改|設定|设置).*$'})

    @particular_case.specified(['57b8a250'])
    def enter_wlan_settings(self):
        self.d(text='netease_game').long_click()
        time.sleep(0.5)
        self.uiutil.click_any({'text': u'管理网络设置'})

    @particular_case.default_call
    def enter_wlan_settings(self):
        clicked = self.uiutil.click_any(
            {'resourceId': 'com.android.settings:id/detail_arrow'},
            {'resourceId': 'com.android.wifisettings:id/advance_layout'},
        )
        if clicked is None:
            self.d(text='netease_game').long_click()
            time.sleep(0.5)
            self.uiutil.click_any({'text': u'静态IP'}, {'textMatches': ur'^.*(修改|設定)(網|网)(路|絡|络).*$'}, {'textMatches': ur'^.*(網|网)(路|絡|络)(修改|設定).*$'})

    @particular_case.specified(SONY_XPERIA)
    def enter_wlan_advanced_settings(self):
        pass

    @particular_case.specified(['LC53ZYH00485'])
    def enter_wlan_advanced_settings(self):
        # HTC one E9+
        uiobj = self.uiutil.scroll_find({'resourceId': "com.android.settings:id/wifi_advanced_togglebox"})
        if uiobj and not uiobj.checked:
            uiobj.click()
            time.sleep(0.5)

    @particular_case.default_call
    def enter_wlan_advanced_settings(self):
        uiobj = self.uiutil.scroll_find({'textContains': u'高级选项'}, {'resourceId': 'com.android.settings:id/wifi_advanced_togglebox'})
        if uiobj and not uiobj.checked:
            uiobj.click()
            time.sleep(0.5)

    @particular_case.default_call
    def is_dhcp_mode(self):
        ipsettings = self.uiutil.scroll_find({'resourceIdMatches': '^.*:id/ip_settings$'})
        if ipsettings and ipsettings.exists:
            if ipsettings.text in ['DHCP', 'dhcp', '自动']:
                return True
            else:
                ipsettings = ipsettings.child(textMatches=ur'DHCP|dhcp|自动', className="android.widget.TextView")
                if ipsettings and ipsettings.exists:
                    return True
        return False

    @particular_case.default_call
    def use_dhcp(self):
        self.uiutil.scroll_to_click_any({'resourceIdMatches': '^.*:id/ip_settings$'})
        self.uiutil.click_any({'textMatches': ur'DHCP|dhcp|自动'})
        self.uiutil.click_any({'textMatches': ur'保存|确定|儲存|储存|ok|OK|Ok'})

    @particular_case.default_call
    def use_static_ip(self):
        self.uiutil.scroll_to_click_any({'resourceIdMatches': '^.*:id/ip_settings$'})
        self.uiutil.click_any({'textMatches': ur'静态|static|STATIC|靜態|静止'})

    @particular_case.default_call
    def modify_wlan_settings_fields(self, dns1, ip_addr=None, gateway=None, masklen=None):
        uiobj = self.uiutil.scroll_find({'resourceIdMatches': '^.*:id/dns1$'})
        if uiobj:
            self.uiutil.replace_text(uiobj, dns1)
        if ip_addr is not None:
            uiobj = self.uiutil.scroll_find({'resourceIdMatches': '^.*:id/ipaddress$'})
            if uiobj:
                self.uiutil.replace_text(uiobj, ip_addr)
        if gateway is not None:
            uiobj = self.uiutil.scroll_find({'resourceIdMatches': '^.*:id/gateway$'})
            if uiobj:
                self.uiutil.replace_text(uiobj, gateway)
        if masklen is not None:
            uiobj = self.uiutil.scroll_find({'resourceIdMatches': '^.*:id/network_prefix_length$'})
            if uiobj:
                self.uiutil.replace_text(uiobj, masklen)
        self.uiutil.click_any({'textMatches': ur'保存|确定|儲存|储存|ok|OK|Ok'})
        time.sleep(2)

    @particular_case.default_call
    def get_current_ssid(self):
        netinfo = self.adb.shell("dumpsys netstats | grep -E 'iface=wlan.*networkId'")
        matcher = re.search(r'networkId=(.*?)[\]|\}]\]', netinfo)
        if matcher:
            return matcher.group(1).strip('"')
        return None

    def test_unlock_success(self):
        time.sleep(1)
        if not self.d(textMatches='^.*(netease|WLAN|Wi-Fi|WiFi|Wifi).*$').exists:
            raise Exception('device unlock fail or stuck. cannot get ui hierarchy.')

    def test_netease_game_connected(self):
        ssid = self.get_current_ssid()
        if ssid is None:
            success = self.uiutil.wait_any({'textMatches': ur'(已连接|已連線|connected).*$'}, timeout=40000)
            if not success:
                raise Exception('cannot connect to netease_game. network not available.')
        elif ssid != 'netease_game':
            raise Exception('cannot connect to netease_game. current AP is {}'.format(ssid))

    def test_ping(self, server, max_try=5):
        """
        try 5 times to ping a server, success if any of ping is ok
        """
        def _ping(cmd):
            res = self.adb.shell(cmd)
            matcher = re.search(r'packets transmitted.*?(\d).*?received', res, re.DOTALL)
            if matcher and matcher.group(1) != '0':
                return res
            else:
                return False

        result = ''
        for i in range(max_try):
            result = _ping('ping -c2 {}'.format(server)) or _ping(['echo "ping -c2 {}" | su'.format(server)])
            if not result:
                time.sleep(2)
                self.connect_netease_game()
            else:
                return
        raise Exception('cannot ping to {}. cmd `ping` results: \n{}'.format(server, result))

    def test_dns(self, dns1):
        test_getdns = self.adb.shell('getprop net.dns1')  # 这样获取的dns才是准的
        if dns1 not in test_getdns:
             raise Exception('set dns failed. current dns is {}'.format(test_getdns))

    def network_prepare(self):
        self.d.screen.on()
        self.d.press('home')
        print '[DNS SETTER] launch wlan list activity'
        self.enter_wlan_list()
        print '[DNS SETTER] test device unlock status'
        self.test_unlock_success()
        print '[DNS SETTER] connecting to netease_game'
        ssid = self.get_current_ssid()
        if ssid != 'netease_game':
            print '[first connect] current ssid is {}. connecting netease_game.'.format(ssid)
            try:
                self.connect_netease_game()
            except:
                print '[final connect] try second times to connect to netease_game.'
                self.connect_netease_game()

    def set_dns(self, dns1):
        # skip if dns already satisfied
        if dns1 in self.adb.shell('getprop net.dns1'):
            print '[DNS SETTER] skip, dns already satisfied.'
            return True

        # change STATIC mode and dns
        with self.ime_helper:
            print '[DNS SETTER] enter wlan config page'
            self.enter_wlan_settings()
            print '[DNS SETTER] enable wlan advanced settings'
            self.enter_wlan_advanced_settings()
            if dns1 != '-1':
                if self.is_dhcp_mode():
                    # get ip, gateway, mask_len first
                    # fix above field if not matched
                    # otherwise, those field should be correct
                    ip_addr = iputils.get_ip_address(self.adb)
                    gateway = iputils.get_gateway_address(self.adb)
                    masklen = iputils.get_subnet_mask_len(self.adb)
                    print '[DNS SETTER] ip:{}  gateway:{}  mask len:{}'.format(ip_addr, gateway, masklen)
                    print '[DNS SETTER] switch to static IP mode'
                    self.use_static_ip()
                    print '[DNS SETTER] change dns1 and fix ipaddress'
                    self.modify_wlan_settings_fields(dns1, ip_addr, gateway, masklen)
                else:
                    print '[DNS SETTER] change dns1'
                    self.modify_wlan_settings_fields(dns1)
            else:
                print '[DNS SETTER] use dhcp mode'
                self.use_dhcp()

            # reconnect
            time.sleep(2)
            self.d.press.back()
            print '[DNS SETTER] back to wlan list to check whether connected to netease_game'
            self.enter_wlan_list()
            ssid = self.get_current_ssid()
            if ssid != 'netease_game':
                print '[final connect] current ssid is {}. connecting netease_game.'.format(ssid)
                try:
                    self.connect_netease_game()
                except:
                    print '[final connect] try second times to connect to netease_game.'
                    self.connect_netease_game()

        time.sleep(0.5)
        if dns1 != '-1':
            print '[DNS SETTER] check current dns1'
            self.test_dns(dns1)


class DnsSetter(DefaultDnsSetter, MI2, Vivo, VivoY27, VivoX6S, MX4, MX3, MeiLanNote, Galaxy, Galaxy4, GalaxyNote2,
                GalaxyNote5, LenovoPad, OPPOR9, MeilanMetal):
    pass


PASS_LIST = (
    '06d67c13',             # Nexus 7 2013
    '55466646',             # 小米 2
    '4a139669',             # 小米 2s
    '1197d597',             # 小米 2s 电信版 (需要测试)
    '96528427',             # 小米 2s 标准版
    '7220be4f',             # 小米 Note 顶配版
    'c0e82f5f',             # MI 2
    '4e49701b',             # 小米 3 移动版
    '6407413e',             # 小米 4s
    '9557CD33',             # 小米 平板
    'SOW8HULFF6MJGAPN',     # 红米 Note 移动增强版
    '1453b839',             # 红米 Note 联通4G增强版
    'JJDMSSUSFAGEZ5OF',     # 红米 Note 2 移动版
    '473fd2a2',             # HM NOTE 1S (输入法有问题，点变句号)
    '7C5906B60221',         # 红米 2A 增强版
    '28e7fdab7ce3',         # 红米 3（全网通）
    'AVY9KA95A2106482',     # 华为 畅享5 全网通
    '7N2MYN155S029228',     # 华为 Ascend P7 联通4G
    'DU2SSE15CA048623',     # 华为 荣耀6 移动4G版
    'DU2SSE149G047150',     # 华为 荣耀6 移动4G版
    '7N2SQL151N004298',     # 华为 Ascend P7（移动版）
    'JAEDU15A16007444',     # 华为 G7 Plus
    'T3Q4C15B04019605',     # 华为 荣耀畅玩5X（移动版）（GIH-PHO-663）
    'QLXBBBA5B1137702',     # 华为 畅享5S 全网通
    'F8UDU15505001428',     # 华为 荣耀6 Plus 移动版（PE-TL20）
    '69T7N15925010489',     # 华为 荣耀 7i
    'G2W7N15303019507',     # 华为 Ascend Mate 7（MT7-CL00）
    'DU2TAN158M041444',     # 华为 荣耀6 联通4G版
    'JTJ4C15710038858',     # 华为 荣耀4A（SCL-TL00H）
    'G2W7N15930015071',     # MT7-CL00
    'ZTAMDU49ZT59TOAE',     # vivo X6D
    'CQ556955VKOV5T4D',     # vivo X6Plus
    '1042dc55',             # 步步高 vivo Y27
    'b0992898',             # 一加 X 标准版
    '810EBM535P6F',         # 魅族 魅蓝 Note 2（双4G）
    '88MFBM72H9SN',         # 魅族 魅蓝 2 移动公开版
    '71MBBLA238NH',         # 魅族 魅蓝 Note
    '045BBI2H9F9B',         # 魅族 MX2
    '351BBJPZ8F27',         # 魅族 MX3 M351
    '351BBJPTHLR2',         # 魅族 MX3 M351
    '76UBBLR2264A',         # 魅族 MX4 Pro
    '850ABM4YR6UW',         # 魅族 MX5
    '4f1496f5',             # 三星 Galaxy S5 联通版（G9006W）
    '2053d814',             # 三星 Galaxy A7（SM-A7000）
    '07173333',             # 三星 Galaxy Mega GT-I9158
    '3230dd49644a10ad',     # 三星 GT-I9300（S3）
    '93758e81',             # 三星 Galaxy S5 G9008W
    'eebcdab5',             # 三星 Galaxy Note Edge（SM-N9150）
    '0b43bc90',             # 三星 Galaxy Note 3 N9008S
    'FA61CBD01664',         # HTC One M9+（台版）
    'LC53ZYH00485',         # HTC One M9+（E9pw）
    '521249b9',             # OPPO R3 R7007 移动4G
    'YT4T8DVKY5UKRGK7',     # OPPO R7 移动4G版
    'W49TOZV4VCC6RKSS',     # OPPO R7s 移动4G
    'TA9921AVZE',           # Moto X二代 XT1096
    'T3Q6T16520001043',     # KIW-TL00H
    'CB5A21QQEN',           # 索尼 Xperia Z3 联通版
    'BH904FXV16',           # 索尼 Xperia Z2 D6503
    'IRCASKZDHAYLVCP7',     # 360 F4（标准版/移动版）
    'GYZL4H556HCUH6RK',     # 联想 S898t+
    'LGH818a5b8c3ae',       # LG G4 H818 国际版

    # 屏幕无响应
    #'351BBJP8D4SW',         # 魅族 MX3

    # 无法安装uiautomator
    #'67a144be',             # OPPO R7 Plus 全网通

    # 未知原因连接中断或连接不稳定
    #'33005092392ab243',     # 三星 Galaxy A5 2016（A5108/移动4G）
    #'de89a5bd',             # OPPO Find 5
    #'57a7821b',             # 小米 3 联通版

    # 太卡了
    #'XJC6R15619009477',     # 华为 荣耀 X2 标准版
    #'MYVDU15713005533',     # 华为 荣耀 7 移动4G版（TL01H）
    #'MXF5T15831007688',     # 华为 MATE S
    #'X2P0215508002471',     # 华为 P8 移动4G标配版（GRA-TL00）

    # 修改配置需要重新输入密码才能保存
    '8d260bf7',             # 酷派 大神 X7
    'fdcbcc83',             # 酷派 锋尚Max

    # 无法连接netease_game
    #'38d6d441',             # 步步高 vivo X5M

    # 输入法有问题，无法顺利输入，会乱序
    #'351BBJPYF7PF',         # 魅族 MX3 M351

    # 卡在某个界面无法继续下去
    '4df74f4b47e33081',     # 三星 Galaxy Note 2 N7100

    # uiautomator自动帮我点确定问题
    '4c6a4cf2',             # 小米 4s（GIH-PHO-625）

    # uiautomator 识别有问题
    '57b8a250',             # 三星 Galaxy A9（A9000/全网通）

    # 私人手机
    '139db80c',             # 中兴 AXON天机 A2015

    # 暂时跳过
)

if __name__ == '__main__':
    # from airtest.core.android.uiautomator import AutomatorDevice
    # d = AutomatorDevice()
    # print d.dump()


    ds = DnsSetter('A10ABNL934ZX', 'A10ABNL934ZX')
    ds.clear_float_tips()
    ds.network_prepare()
    ds.set_dns('192.168.229.227')
    ds.test_ping('www.163.com')
    ds.set_dns('-1')
    ds.test_ping('www.163.com')

    # a = Android('4df74f4b47e33081')
    # print a.shell('echo "ping -c2 www.163.com" | su')


    # for d in stf.get_device_list_rest(None):
    #     sn = d['serial']
    #     if sn not in PASS_LIST:
    #         rsn = stf_runner.join(sn)
    #         try:
    #             dns_setter = DnsSetter(rsn, sn)
    #             dns1 = '192.168.229.227'
    #             dns_setter.network_prepare()
    #             dns_setter.set_dns(dns1)
    #         except:
    #             traceback.print_exc()
    #         stf_runner.cleanup(sn)
    #         print 'finish!'
    #         time.sleep(40)

    # import requests
    #
    # tokenid = 'eyJhbGciOiJIUzI1NiIsImV4cCI6MTQ3MDU2MTIxNiwiaWF0IjoxNDY3OTY5MjE2fQ.eyJ1c2VybmFtZSI6Imx4bjMwMzIifQ.jBrBI4ksqjpU_rCQIlK-JIgBR3YpYn-KCMU7VNoXxsk'
    # # tokenid = 'eyJhbGciOiJIUzI1NiIsImV4cCI6MTQ3MDU2MjQ2MiwiaWF0IjoxNDY3OTcwNDYyfQ.eyJ1c2VybmFtZSI6Imx4bjMwMzIifQ.CMHetTEla9i_0pXFh8R2zAx9glkWvYjvF-MLBekrXWI'
    # def create_instruction(tokenid, data, **kwargs):
    #     data.update(kwargs)
    #     r = requests.post('http://10.251.93.179:32022/api/sendto_device', headers={'tokenid': tokenid}, data=data)
    #     if r.status_code == 201:
    #         try:
    #             return r.json()
    #         except:
    #             pass
    #     else:
    #         print '======================================================================\n'
    #         print 'r.status_code=', r.status_code
    #         print 'data=', data
    #         print 'message=', r.json()['message']
    #         print '======================================================================\n'
    #     return None
    #
    # data = {
    #     'devid': 'g18_at_10-254-29-164',
    #     'data': 'showMessage',
    #     'lang': 'lua',
    # }
    # for i in range(200):
    #     print create_instruction(tokenid, data)
    #     time.sleep(5)
