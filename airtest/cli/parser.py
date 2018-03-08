# -*- coding: utf-8 -*-
import argparse
from airtest.report.report import get_parger as report_parser


def get_parser():
    ap = argparse.ArgumentParser()
    subparsers = ap.add_subparsers(dest="action", help="run/info/report")
    # subparser run
    ap_run = subparsers.add_parser("run", help="run script")
    runner_parser(ap_run)
    # subparser info
    ap_info = subparsers.add_parser("info", help="get & print author/title/desc info of script")
    ap_info.add_argument("script", help="script filename")
    # subparser report
    ap_report = subparsers.add_parser("report", help="generate report of script")
    report_parser(ap_report)
    return ap


def runner_parser(ap=None):
    if not ap:
        ap = argparse.ArgumentParser()
    ap.add_argument("script", help="air path")
    ap.add_argument("--device", help="connect dev by uri string, e.g. Android:///", nargs="?", action="append")
    ap.add_argument("--log", help="set log dir, default to be script dir", nargs="?", const=True)
    ap.add_argument("--recording", help="record screen when running", nargs="?", const=True)
    return ap
