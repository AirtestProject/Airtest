from airtest.cli.runner import AirtestCase, run_script
from airtest.cli.parser import runner_parser


class G18AirtestCase(AirtestCase):

    def setUp(self):
        # self.scope["hunter"] = "i am hunter"
        # self.exec_other_script("pre.owl")
        print("custom setup")

    def tearDown(self):
        # self.exec_other_script("post.owl")
        print("custom tearDown")


if __name__ == '__main__':
    ap = runner_parser()
    args = ap.parse_args()
    run_script(args, G18AirtestCase)
