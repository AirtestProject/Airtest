# encoding=utf-8
import sys
sys.path.append("..\\..\\..\\..\\")

from airtest.core.android.android import ADB, AdbError, DEFAULT_ADB_SERVER, MoaError
import unittest
import subprocess

#import mock
from new_test.config_test import st_config as config
from new_test.mock_content import mock_content
from new_test.adbmock import adbmock
from  airtest.core.android.utils import iputils

# mock content
        



class TestIpUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        '''
            open mock or use real device to set up adb()
        '''

        if config.enable_mock:
            adb=adbmock() 
        else:
            serialno = adb.devices(state=ADB.status_device)[0][0]
            adb.set_serialno(serialno)
            cls.adb = adb
        cls.adb = adb

    '''
      test get_ip_address
    '''
    def test_get_ip_address_real(self):
        # for real device could get ipaddress
        if config.enable_mock:
            return

        ipaddress = iputils.get_ip_address(self.adb)
        self.assertIsNotNone(ipaddress)


    def test_get_ip_address_netcfg(self):
        # for mock

        if config.enable_mock:
            self.adb.set_enable("netcfg | grep wlan0",True)
        else:
            return

        ipaddress = iputils.get_ip_address(self.adb)
        self.assertEqual(ipaddress,"10.254.35.40")

    def test_get_ip_address_ifconfig(self):
        # for mock ifconfig methrod

        if config.enable_mock:
            self.adb.set_enable("netcfg | grep wlan0",False)
            self.adb.set_enable("ifconfig",True)            
        else:
            return

        ipaddress = iputils.get_ip_address(self.adb)
        self.assertEqual(ipaddress,"10.254.35.40")

    def test_get_ip_address_getprop(self):
        # for mock ifconfig methrod

        if config.enable_mock:
            self.adb.set_enable("netcfg | grep wlan0",False)
            self.adb.set_enable("ifconfig",False)            
            self.adb.set_enable("getprop dhcp.wlan0.ipaddress",False)                
        else:
            return 

        ipaddress=iputils.get_ip_address(self.adb)
        self.assertEqual(ipaddress, None)

    '''
        get_gateway_address
    '''
    def test_get_gateway_address_getprop(self):
        # for mock getprop methrod

        if config.enable_mock:
            self.adb.set_enable("getprop dhcp.wlan0.gateway",True)              
        else:
            return 

        gate=iputils.get_gateway_address(self.adb)
        self.assertEqual(gate,"10.254.0.1")

    def test_get_gateway_address_getprop(self):
        # for mock netcfg methrod

        if config.enable_mock:
            self.adb.set_enable("getprop dhcp.wlan0.gateway",False) 
            self.adb.set_enable("netcfg | grep wlan0",True)              
        else:
            return 

        gate=iputils.get_gateway_address(self.adb)
        self.assertEqual(gate,"10.254.0.1")

    def test_get_gateway_address_default(self):
        # for mock default methrod

        if config.enable_mock:
            self.adb.set_enable("getprop dhcp.wlan0.gateway",False) 
            self.adb.set_enable("netcfg | grep wlan0",False)              
        else:
            return 

        gate=iputils.get_gateway_address(self.adb)
        self.assertEqual(gate,"10.254.0.1")


    def test_get_gateway_address_default(self):
        # for real phone methrod

        if config.enable_mock:
            return          

        gate=iputils.get_gateway_address(self.adb)
        self.assertIsNotNone(gate)

    '''
     test get_subnet_mask_len
    '''
    def test_get_subnet_mask_len_real(self):
        if config.enable_mock:
            return          

        mask=iputils.get_subnet_mask_len(self.adb)
        self.assertIsNotNone(mask)

    def test_get_subnet_mask_len(self):
        # for mock default methrod

        if config.enable_mock:
            self.adb.set_enable("netcfg | grep wlan0",True)             
        else:
            return 

        mask=iputils.get_subnet_mask_len(self.adb)
        self.assertEqual(mask,"18")




if __name__ == '__main__':
    #print config.enable_mock
    pass
    unittest.main()
