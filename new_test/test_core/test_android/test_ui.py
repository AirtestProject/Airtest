# encoding=utf-8
import sys
sys.path.append("..\\..\\..\\")

from playground.ui import AutomatorWrapper, UiAutomator
import unittest
import subprocess
from new_test.adbmock import adbmock


class TestUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.uihand = UiAutomator()

    def test_info(self):
        print(self.uihand.info)

    def test_click(self):
        self.uihand.click(0, 0)

    def test_getatt(self):
        self.uihand.press.home()

    def test_sele(self):
        print(self.uihand._get_selector_obj())


#class kkk():



if __name__ == '__main__':
    unittest.main()
