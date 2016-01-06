import os
import json
import time
import subprocess
from pprint import pprint


RUNDATA = "result.json"
AIRTEST_RUNNER = "../../dist/airtest_runner/airtest_runner.exe"
AIRTEST_REPORTER = "utils/report/report_one.py"
PRESCRIPT = "utils/clear.owl"
POSTSCRIPT = None
REPORT_ROOT = "utils/report"
UTILFILE = os.path.join(os.path.realpath("."), "utils.py")


def list_all_dirs(root_dir, exclude=["dist", "utils"]):
    for root, dirs, files in os.walk(root_dir):
        # print root, dirs, files
        dirs[:] = [d for d in dirs if d not in exclude]
        for name in dirs:
            path = os.path.join(root, name)
            if path.endswith(".owl"):
                yield path

def run_one(path):
    filename = os.path.basename(path).replace(".owl", ".py")
    path = os.path.join(path, filename)
    cmd = [
        AIRTEST_RUNNER,
        path,
        "--utilfile", UTILFILE,
        "--log",
        "--screen"
    ]
    print cmd
    ret = subprocess.call(cmd)
    return ret


def run_dir(output=RUNDATA, run_all=False):
    if os.path.isfile(output):
        run_data = json.load(open(output))
    else:
        run_data = {"result": {}}
    def init(run_data):
        run_data.update({"start_time": time.time()})
    init(run_data)
    gen = list_all_dirs(".")
    for i in gen:
        if not run_all and run_data["result"].get(i) == 0:
            print "skip script", i
            continue
        if PRESCRIPT:
            run_one(PRESCRIPT)
        ret = run_one(i)
        if POSTSCRIPT:
            run_one(POSTSCRIPT)
        run_data["result"][i] = ret
        # print and save
        pprint(run_data)
        json.dump(run_data, open(output, "w"), indent=4)
    # final save
    json.dump(run_data, open(output, "w"), indent=4)


def get_html_path(owlpath):
    htmlpath = owlpath.strip(".\\").replace("\\", "_u_").replace(".owl", ".html")
    return htmlpath


def gen_reports():
    gen = list_all_dirs(".")
    for i in gen:
        subprocess.call([
            "python",
            os.path.basename(AIRTEST_REPORTER),
            os.path.join("../..", i),
            get_html_path(i)
        ], cwd=os.path.dirname(AIRTEST_REPORTER))
    gen_index()


def gen_index(run_data=RUNDATA):
    run_data = json.load(open(RUNDATA))
    run_data["count"] = len(run_data["result"].values())
    run_data["success"] = run_data["result"].values().count(0)
    run_data["rate"] = int(run_data["success"] * 100 / run_data["count"])
    run_data["report_root"] = REPORT_ROOT
    run_data["logdata"] = {}
    for k, v in run_data["result"].iteritems():
        run_data["logdata"][k] = {
            "name": k.strip(".\\"),
            "path": os.path.join(REPORT_ROOT, get_html_path(k)),
            "success": v == 0
        }
    pprint(run_data)
    from jinja2 import Template
    tpl = open("reporttpl.html").read().decode("utf-8")
    t = Template(tpl)
    html = t.render(data=run_data)
    with open("report.html", "w") as f:
        f.write(html.encode("utf-8"))


if __name__ == '__main__':
    # run_one("test.owl")
    run_dir()
    gen_reports()
    # gen_index()
