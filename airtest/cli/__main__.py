# -*- coding: utf-8 -*-
import os
import sys

from airtest.cli.parser import get_parser
from airtest.utils.snippet import get_airtest_version


def main(argv=None):
    ap = get_parser()
    args = ap.parse_args(argv)
    if args.action == "info":
        from airtest.cli.info import get_script_info
        print(get_script_info(args.script))
    elif args.action == "report":
        from airtest.report.report import main as report_main
        report_main(args)
    elif args.action == "run":
        from airtest.cli.runner import run_script
        run_script(args)
    elif args.action == "version":
        sys.stdout.write(get_airtest_version())
        sys.stdout.write(os.linesep)
        sys.exit()
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
