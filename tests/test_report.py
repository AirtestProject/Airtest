import os
import sys
import unittest
import subprocess
from airtest.report import report_one


TEST_PKG = "org.cocos.Rabbit"
TEST_APK = os.path.join(os.path.dirname(__file__), 'Rabbit.apk')
TEST_OWL = os.path.join(os.path.dirname(__file__), 'test_owl.owl')
KWARGS = "PKG=%s,APK=%s" % (TEST_PKG, TEST_APK)
OUTPUT_HTML = 'log.html'
OUTPUT_GIF = 'log.gif'


class TestReportOnAndroid(unittest.TestCase):

    def setUp(self):
        if os.path.exists(OUTPUT_HTML):
            os.remove(OUTPUT_HTML)
        if os.path.exists(OUTPUT_GIF):
            os.remove(OUTPUT_GIF)

    def test_cli(self):
        cmd = "python -m airtest.report.report_one %s" % (TEST_OWL,)
        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()
        self.assertIs(proc.returncode, 0)
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_default_params(self):
        sys.argv = [sys.argv[0], TEST_OWL]
        report_one.main()
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_report_with_log_dir(self):
        sys.argv = [sys.argv[0], TEST_OWL, '--log', TEST_OWL]
        report_one.main()
        self.assertTrue(os.path.exists(OUTPUT_HTML))

    def test_gen_gif(self):
        sys.argv = [sys.argv[0], TEST_OWL, '--gif']
        report_one.main()
        self.assertTrue(os.path.exists(OUTPUT_GIF))


if __name__ == '__main__':
    unittest.main()
