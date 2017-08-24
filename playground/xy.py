from airtest.cli.runner import AirtestCase, run_script
from airtest.cli.parser import argparse, runner_parser


class G18AirtestCase(AirtestCase):

    def setUp(self):
        self.scope["hunter"] = "i am hunter"


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap = runner_parser(ap)
    args = ap.parse_args()
    run_script(args, G18AirtestCase)
