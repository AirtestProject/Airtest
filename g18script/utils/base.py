# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 NetEase Inc.

""" basic library

"""
import json
import logging
import sys
import subprocess
import shlex
import os


def call(cmd, cwd, daemon=False):
    args = map(lambda s: s.decode('utf-8'), shlex.split(cmd.encode('utf-8')))
    child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    if not daemon:
        stdout, stderr = child.communicate()
        retcode = child.returncode
        if retcode is 0:
            result = {"retcode": retcode, "retval": stdout}
        else:
            result = {"retcode": retcode, "retval": stderr}
        return result
    else:
        return child.pid


def read_json_conf(conf_file):
    if not os.path.exists(conf_file):
        sys.exit('config file require: %s' % conf_file)
    return json.load(open(conf_file))


def setup_custom_logger(name):
    out_handler = logging.StreamHandler(sys.stdout)
    from colorlog import ColoredFormatter
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s] - [%(filename)10s:%(funcName)10s] %(levelname)-7s [%(message)s]",
        datefmt=None,
        reset=True,
        log_colors={
                'DEBUG':    'green',
                'INFO':     'cyan',
                'WARNING':  'red',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    out_handler.setFormatter(formatter)
    out_handler.setLevel(logging.DEBUG)
    custom_log = logging.getLogger(name)
    custom_log.addHandler(out_handler)
    custom_log.setLevel(logging.DEBUG)
    return custom_log

if __name__ == '__main__':
    pass