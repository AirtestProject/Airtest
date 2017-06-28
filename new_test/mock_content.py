# -*- coding: utf-8 -*-
class mock_content(object):
	
    shell_dick={}
    cmd_dick={}

    def __init__(self):
        self.shell_dick["getprop dhcp.wlan0.ipaddress"]="sdfsf"
        self.shell_dick["netcfg | grep wlan0"]="wlan0    UP                                10.254.35.40/18  0x00001043"
        self.shell_dick["ifconfig"]='''
            wlan0     Link encap:UNSPEC
            inet addr:10.254.35.40  Bcast:10.254.63.255  Mask:255.255.192.0 
            inet6 addr: fe80::6283:34ff:fee5:2b1e/64 Scope: Link
            UP BROADCAST RUNNING MULTICAST  MTU:1400  Metric:1
            RX packets:1379497 errors:0 dropped:806 overruns:0 frame:0
            TX packets:1187753 errors:0 dropped:0 overruns:0 carrier:0
            collisions:0 txqueuelen:1000
            RX bytes:1360721530 TX bytes:208865228

            lo        Link encap:UNSPEC
            inet addr:127.0.0.1  Mask:255.0.0.0
            inet6 addr: ::1/128 Scope: Host
            UP LOOPBACK RUNNING  MTU:65536  Metric:1
            RX packets:135691 errors:0 dropped:0 overruns:0 frame:0
            TX packets:135691 errors:0 dropped:0 overruns:0 carrier:0
            collisions:0 txqueuelen:0
            RX bytes:64635949 TX bytes:64635949
        '''
        self.cmd_dick['devices']={}
        self.cmd_dick['devices'][0]='''
            Medfield14ABxxxx\tdevice
            Ztedfield14Axxxx\tdevice
            emulator-5554\tdevice
            015d2994ec2xxx\tdevice
        '''
