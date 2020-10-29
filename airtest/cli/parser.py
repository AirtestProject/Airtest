# -*- coding: utf-8 -*-
import argparse
import sys
from airtest.report.report import get_parger as report_parser
from airtest.cli.runner import setup_by_args


def get_parser():
    ap = argparse.ArgumentParser()
    subparsers = ap.add_subparsers(dest="action", help="version/run/info/report")
    # subparser version
    subparsers.add_parser("version", help="show version and exit")
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
    ap.add_argument("--compress", required=False, type=int, choices=range(1, 100), help="set snapshot quality, 1-99", default=10)
    ap.add_argument("--recording", help="record screen when running", nargs="?", const=True)
    ap.add_argument("--no-image", help="Do not save screenshots", nargs="?", const=True)
    return ap


def cli_setup(args=None):
    """future api for setup env by cli"""
    if not args:
        if len(sys.argv) < 2:
            print("no cmdline args")
            return False
        args = sys.argv
    print(args)

    ap = argparse.ArgumentParser()
    if "--report" in args:
        from airtest.report.report import main as report_main
        ap = report_parser(ap)
        args = ap.parse_args(args)
        report_main(args)
        exit(0)
    else:
        ap = runner_parser(ap)
        args = ap.parse_args(args)
        setup_by_args(args)
    return True
