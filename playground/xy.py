from airtest.cli.runner import AirtestCase, run_script
from airtest.cli.parser import runner_parser


class CustomAirtestCase(AirtestCase):

    def setUp(self):
        # add var/function/class/.. to globals
        # self.scope["hunter"] = "i am hunter"
        # self.scope["add"] = lambda x: x+1

        # exec setup script
        # self.exec_other_script("setup.owl")
        print("custom setup")

    def tearDown(self):
        # exec teardown script
        # self.exec_other_script("teardown.owl")
        print("custom tearDown")


if __name__ == '__main__':
    ap = runner_parser()
    args = ap.parse_args()
    run_script(args, CustomAirtestCase)
