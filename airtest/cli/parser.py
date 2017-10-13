# -*- coding: utf-8 -*-
import argparse
from airtest.report.report import get_parger as report_parser


def get_parser():
    ap = argparse.ArgumentParser()
    subparsers = ap.add_subparsers(dest="action", help="run/info/snapshot/report")
    # subparser run
    ap_run = subparsers.add_parser("run", help="run script")
    runner_parser(ap_run)
    # subparser info
    ap_info = subparsers.add_parser("info", help="get & print author/title/desc info of script")
    ap_info.add_argument("script", help="script filename")
    # subparser report
    ap_report = subparsers.add_parser("report", help="generate report of script")
    report_parser(ap_report)
    # subparser snapshot
    ap_screen = subparsers.add_parser("snapshot", help="get snapshot list of script")
    ap_screen.add_argument("script", help="script filename")
    return ap


def runner_parser(ap=None):
    if not ap:
        ap = argparse.ArgumentParser()
    ap.add_argument("script", help="script filename")
    ap.add_argument("--device", help="connect dev by uri string", nargs="?", action="append")
    ap.add_argument("--log", help="set log dir, default to be script dir", nargs="?", const=True)
    ap.add_argument("--kwargs", help="extra kwargs used in script as global variables, eg: a=1,b=2")
    ap.add_argument("--pre", help="run before script, setup environment")
    ap.add_argument("--post", help="run after script, clean up environment, will run whether script success or fail")
    ap.add_argument("--performance", help="collect performance data", nargs="?", const=True, default=False)
    return ap
