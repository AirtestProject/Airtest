# -*- coding: utf-8 -*-
import argparse
from airtest.report.report import get_parger as report_parser
from airtest.report.report import main as report_main
from airtest.cli.info import get_script_info
from airtest.cli.runner import run_script


def get_parser():
    ap = argparse.ArgumentParser()
    subparsers = ap.add_subparsers(dest="action", help="run/info/report")
    # subparser run
    ap_run = subparsers.add_parser("run", help="run script")
    run_parser(ap_run)
    # subparser info
    ap_info = subparsers.add_parser("info", help="get & print author/title/desc info of script")
    ap_info.add_argument("script", help="script filename")
    # subparser report
    ap_report = subparsers.add_parser("report", help="generate report of script")
    report_parser(ap_report)
    return ap


def run_parser(ap):
    ap.add_argument("script", help="script filename")
    ap.add_argument("--utilfile", help="utils filepath to implement your own funcs")
    ap.add_argument("--setsn", help="set dev by serialno", nargs="?", const="")
    ap.add_argument("--setudid", help="set ios device udid", nargs="?", const="")
    ap.add_argument("--setwin", help="set dev by windows handle", nargs="?", const="")
    ap.add_argument("--setemulator", help="set emulator name default bluestacks", nargs="?", const=True)
    ap.add_argument("--devcount", help="set dev count autoly", nargs="?", const=1, default=1, type=int)
    ap.add_argument("--nominicap", help="init android without minicap, using adb for screencap", action="store_true")
    ap.add_argument("--nominitouch", help="init android without minitouch, using adb for screentouch", action="store_true")
    ap.add_argument("--log", help="set log dir, default to be script dir", nargs="?", const=True)
    ap.add_argument("--kwargs", help="extra kwargs used in script as global variables, eg: a=1,b=2")
    ap.add_argument("--forever", help="run in forever mode, read stdin and exec", action="store_true")
    ap.add_argument("--pre", help="run before script, setup environment")
    ap.add_argument("--post", help="run after script, clean up environment, will run whether script success or fail")
    return ap


def main():
    ap = get_parser()
    args = ap.parse_args()
    if args.action == "info":
        print(get_script_info(args.script))
    elif args.action == "report":
        report_main(args)
    elif args.action == "run":
        run_script(args)


if __name__ == '__main__':

    main()
