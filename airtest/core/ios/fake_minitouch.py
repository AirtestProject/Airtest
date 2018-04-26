# coding=utf-8
import subprocess
import os
import re
import struct
import logging
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.safesocket import SafeSocket

LOGGING = get_logger(__name__)


class fakeMiniTouch(object):
    lastDown = {'x': None, 'y': None}
    recentPoint = {'x': None, 'y': None}

    def __init__(self, dev):
        self.dev = dev
        self.swipe_threshold = 10

    def setup(self):
        pass

    def operate(self, operate_arg):
        # TODO FIX IPHONT TOUCH
        # start down
        if operate_arg['type'] == 'down':
            self.lastDown['x'] = operate_arg['x']
            self.lastDown['y'] = operate_arg['y']

        # mouse up
        if operate_arg['type'] == 'up':
            # in case they may be None
            if self.lastDown['x'] is None or self.lastDown['y'] is None:
                return

            # has recent point
            if self.recentPoint['x'] and self.recentPoint['y']:
                # swipe need to move longer
                # TODO：设定滑动和点击的阈值，目前为10
                if abs(self.recentPoint['x'] - self.lastDown['x']) > self.swipe_threshold \
                    or abs(self.recentPoint['y'] - self.lastDown['y']) > self.swipe_threshold:
                        self.dev.swipe((self.lastDown['x'], self.lastDown['y']),
                        (self.recentPoint['x'], self.recentPoint['y']))
                else:
                    self.dev.touch((self.lastDown['x'], self.lastDown['y']))
            else:
                self.dev.touch((self.lastDown['x'], self.lastDown['y']))

            # clear infos
            self.lastDown = {'x': None, 'y': None}
            self.recentPoint = {'x': None, 'y': None}

        if operate_arg['type'] == 'move':
            self.recentPoint['x'] = operate_arg['x']
            self.recentPoint['y'] = operate_arg['y']


if __name__ == '__main__':
    pass
