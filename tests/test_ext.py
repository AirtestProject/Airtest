import os
import unittest
import subprocess


class TestExt(unittest.TestCase):

    def test_dns(self):
        proc = subprocess.Popen("python -m airtest.ext.testlab.cli devices", shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 0) 

    def test_wtf(self):
        proc = subprocess.Popen("python -m airtest.ext.testlab.wtf", shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 1) 

    def test_import(self):
        with self.assertRaises(UnboundLocalError):
            print airtest.ext.testlab
        import airtest.ext.testlab
        self.assertIsNotNone(airtest.ext.testlab)

    def test_import_from(self):
        with self.assertRaises(UnboundLocalError):
            print testlab
        from airtest.ext import testlab
        self.assertIsNotNone(testlab)


if __name__ == '__main__':
    unittest.main()
