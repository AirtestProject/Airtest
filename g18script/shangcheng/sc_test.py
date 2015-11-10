# -*- coding: utf-8 -*-
import os
import sys
import time

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, '../../../')

sys.path.append(PROJECT_DIR)

from g18script.utils.TestParser import TestParser


if __name__ == '__main__':
    testcase_file = os.path.join(SCRIPT_DIR, "sc_tc.json")
    tc = TestParser(testcase_file)
    tc.run_case()
