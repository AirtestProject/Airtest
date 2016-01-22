#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx
# Created: 2015-07-03 14:55

"""
error classes
"""

class MoaError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class MoaNotFoundError(MoaError):
    pass


class AdbError(Exception):
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "stdout:%s stderr:%s" % (self.stdout, self.stderr)
