# encoding=utf8

__author__ = "刘欣"

from airtest.core.api import *
from airtest.report.report import simple_report


PKG = "org.cocos2d.blackjack"
APK = "blackjack-release-signed.apk"

def cli_setup(args=None):
    from airtest.cli.parser import runner_parser
    from airtest.cli.runner import setup_by_args
    import argparse
    import sys

    if not args:
        if len(sys.argv) < 2:
            print("no cmdline args")
            return False
        args = sys.argv
    print(args)

    ap = argparse.ArgumentParser()
    if "--report" in args:
        from airtest.report.report import main as report_main
        from airtest.report.report import get_parger as report_parser
        ap = report_parser(ap)
        args = ap.parse_args(args)
        report_main(args)
        exit(0)
    else:
        ap = runner_parser(ap)
        args = ap.parse_args(args)
        setup_by_args(args)
    return True


if not cli_setup():
    # set log file if you want a html report
    # set_logdir("log")
    # connect android device with params: cap_method=javacap
    # init_device("Android", cap_method="javacap")

    # or setup env at once
    auto_setup(
        devices=["Android:///?cap_method=javacap&ori_method=adbori"],
        logdir="log",
    )

# install and start the app
wake()
home()

if PKG not in device().list_app():
    install(APK)

stop_app(PKG)
start_app(PKG)
sleep(2)

# next 3 sentences are generated with AirtestIDE
touch(Template(r"tpl1499240443959.png", record_pos=(0.22, -0.165), resolution=(2560, 1536)))
assert_exists(Template(r"tpl1499240472304.png", record_pos=(0.0, -0.094), resolution=(2560, 1536)), "请下注")
p = wait(Template(r"tpl1499240490986.png", record_pos=(-0.443, -0.273), resolution=(2560, 1536)))

# touch a position
touch(p)
sleep(2)

# stop the app
stop_app(PKG)
sleep(2)
snapshot(msg="app stopped")

print("test finished")

# generate html report
simple_report("log", __file__)
