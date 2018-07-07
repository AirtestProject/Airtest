#!/usr/bin/env python
# -*- coding:utf8 -*-
import json
import os
import io
import sys
import shutil
import jinja2
import traceback
from copy import deepcopy
from airtest.cli.info import get_script_info
from airtest.utils.compat import decode_path
from six import PY3
from pprint import pprint

LOGDIR = "log"
LOGFILE = "log.txt"
HTML_TPL = "log_template.html"
HTML_FILE = "log.html"
STATIC_DIR = os.path.dirname(__file__)


class LogToHtml(object):
    """Convert log to html display """
    scale = 0.5

    def __init__(self, script_root, log_root="", static_root="", export_dir=None, logfile=LOGFILE, lang="en", plugins=None):
        self.log = []
        self.script_root = script_root
        self.log_root = log_root
        self.static_root = static_root or STATIC_DIR
        self.test_result = True
        self.run_start = None
        self.run_end = None
        self.export_dir = export_dir
        self.logfile = os.path.join(log_root, logfile)
        self.lang = lang
        self.init_plugin_modules(plugins)

    @staticmethod
    def init_plugin_modules(plugins):
        if not plugins:
            return
        for plugin_name in plugins:
            print("try loading plugin: %s" % plugin_name)
            try:
                __import__(plugin_name)
            except:
                traceback.print_exc()

    def _load(self):
        logfile = self.logfile.encode(sys.getfilesystemencoding()) if not PY3 else self.logfile
        with io.open(logfile, encoding="utf-8") as f:
            for line in f.readlines():
                self.log.append(json.loads(line))

    def _analyse(self):
        """ 解析log成可渲染的dict """
        steps = []
        children_steps = []

        for log in self.log:
            depth = log['depth']

            if not self.run_start:
                self.run_start = log["time"]
            self.run_end = log["time"]

            if depth == 0:
                # single log line, not in stack
                steps.append(log)
            elif depth == 1:
                step = deepcopy(log)
                step["__children__"] = children_steps
                steps.append(step)
                children_steps = []
            else:
                children_steps.insert(0, log)

        # pprint(steps)
        translated_steps = [self._translate_step(s) for s in steps]
        return translated_steps

    def _translate_step(self, step):
        """translate single step"""
        name = step["data"]["name"]
        title = self._translate_title(name)
        code = self._translate_code(step)
        desc = self._translate_desc(step, code)
        screen = self._translate_screen(step, code)
        traceback = self._translate_traceback(step)
        assertion = self._translate_assertion(step)

        # set test failed if any traceback exists
        if traceback:
            self.test_result = False

        translated = {
            "title": title,
            "time": step["time"],
            "code": code,
            "screen": screen,
            "desc": desc,
            "traceback": traceback,
            "assert": assertion
        }
        return translated

    def _translate_assertion(self, step):
        if "assert" in step["data"]["name"] and "msg" in step["data"]["call_args"]:
            return step["data"]["call_args"]["msg"]

    def _translate_screen(self, step, code):
        if step['tag'] != "function":
            return None
        screen = {
            "src": None,
            "rect": [],
            "pos": [],
            "vector": [],
            "confidence": None,
        }

        for item in step["__children__"]:
            if item["data"]["name"] == "try_log_screen":
                src = item["data"]['ret']
                if self.export_dir:
                    src = os.path.join(LOGDIR, src)
                else:
                    src = os.path.join(self.log_root, src)
                screen['src'] = src
                break

        display_pos = None

        for item in step["__children__"]:
            if item["data"]["name"] == "_cv_match" and "ret" in item["data"] and item["data"]["ret"]:
                cv_result = item["data"]["ret"]
                pos = cv_result['result']
                if isinstance(pos, (list, tuple)):
                    display_pos = [round(pos[0]), round(pos[1])]
                rect = self.div_rect(cv_result['rectangle'])
                screen['rect'].append(rect)
                screen['confidence'] = cv_result['confidence']
                break

        if step["data"]["name"] in ["touch", "assert_exists", "wait", "exists"]:
            # 将图像匹配得到的pos修正为最终pos
            if isinstance(step["data"].get("ret"), (list, tuple)):
                display_pos = step["data"]["ret"]
            elif isinstance(step["data"]["call_args"].get("v"), (list, tuple)):
                display_pos = step["data"]["call_args"]["v"]

        elif step["data"]["name"] == "swipe":
            if "ret" in step["data"]:
                screen["pos"].append(step["data"]["ret"][0])
                target_pos = step["data"]["ret"][1]
                origin_pos = step["data"]["ret"][0]
                screen["vector"].append([target_pos[0] - origin_pos[0], target_pos[1] - origin_pos[1]])

        if display_pos:
            screen["pos"].append(display_pos)

        return screen

    def _translate_traceback(self, step):
        if "traceback" in step["data"]:
            return step["data"]["traceback"]

    def _translate_code(self, step):
        if step["tag"] != "function":
            return None
        step_data = step["data"]
        args = []
        code = {
            "name": step_data["name"],
            "args": args,
        }
        for key, value in step_data["call_args"].items():
            args.append({
                "key": key,
                "value": value,
            })
        for k, arg in enumerate(args):
            value = arg["value"]
            if isinstance(value, dict) and value.get("__class__") == "Template":
                image_path = str(value['filename'])
                if not self.export_dir:
                    if os.path.isfile(os.path.join(self.script_root, image_path)):
                        image_path = os.path.join(self.script_root, image_path)
                    else:
                        image_path = value['_filepath']
                else:
                    if not os.path.isfile(os.path.join(self.script_root, image_path)):
                        shutil.copy(value['_filepath'], self.script_root)
                arg["image"] = image_path
        return code

    @staticmethod
    def div_rect(r):
        """count rect for js use"""
        xs = [p[0] for p in r]
        ys = [p[1] for p in r]
        left = min(xs)
        top = min(ys)
        w = max(xs) - left
        h = max(ys) - top
        return {'left': left, 'top': top, 'width': w, 'height': h}

    def _translate_desc(self, step, code):
        """ 函数描述 """
        if step['tag'] != "function":
            return None
        name = step['data']['name']
        res = step['data'].get('ret')
        args = {i["key"]: i["value"] for i in code["args"]}

        desc = {
            "snapshot": lambda: u"Screenshot description: %s" % args.get("msg"),
            "touch": lambda: u"Touch %s" % ("target image" if isinstance(args['v'], dict) else "coordinates %s" % args['v']),
            "swipe": u"Swipe on screen",
            "wait": u"Wait for target image to appear",
            "exists": lambda: u"Image %s exists" % ("" if res else "not"),
            "text": lambda: u"Input text:%s" % args.get('text'),
            "keyevent": lambda: u"Click [%s] button" % args.get('keyname'),
            "sleep": lambda: u"Wait for %s seconds" % args.get('secs'),
            "assert_exists": u"Assert target image exists",
            "assert_not_exists": u"Assert target image does not exists",
        }

        # todo: 最好用js里的多语言实现
        desc_zh = {
            "snapshot": lambda: u"截图描述: %s" % args.get("msg"),
            "touch": lambda: u"点击 %s" % (u"目标图片" if isinstance(args['v'], dict) else u"屏幕坐标 %s" % args['v']),
            "swipe": u"滑动操作",
            "wait": u"等待目标图片出现",
            "exists": lambda: u"图片%s存在" % ("" if res else "不"),
            "text": lambda: u"输入文字:%s" % args.get('text'),
            "keyevent": lambda: u"点击[%s]按键" % args.get('keyname'),
            "sleep": lambda: u"等待%s秒" % args.get('secs'),
            "assert_exists": u"断言目标图片存在",
            "assert_not_exists": u"断言目标图片不存在",
        }

        if self.lang == "zh":
            desc = desc_zh

        ret = desc.get(name)
        if callable(ret):
            ret = ret()
        return ret

    def _translate_title(self, name):
        title = {
            "touch": u"Touch",
            "swipe": u"Swipe",
            "wait": u"Wait",
            "exists": u"Exists",
            "text": u"Text",
            "keyevent": u"Keyevent",
            "sleep": u"Sleep",
            "assert_exists": u"Assert exists",
            "assert_not_exists": u"Assert not exists",
            "snapshot": u"Snapshot",
            "assert_equal": u"Assert equal",
            "assert_not_equal": u"Assert not equal",
        }

        return title.get(name, name)

    @staticmethod
    def _render(template_name, output_file=None, **template_vars):
        """ 用jinja2渲染html"""
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(STATIC_DIR),
            extensions=(),
            autoescape=True
        )
        template = env.get_template(template_name)
        html = template.render(**template_vars)

        if output_file:
            with io.open(output_file, 'w', encoding="utf-8") as f:
                f.write(html)
            print(output_file)

        return html

    def copy_tree(self, src, dst):
        try:
            shutil.copytree(src, dst)
        except Exception as e:
            print(e)

    def _make_export_dir(self):
        """mkdir & copy /staticfiles/screenshots"""
        dirname = os.path.basename(self.script_root).replace(".air", ".log")
        # mkdir
        dirpath = os.path.join(self.export_dir, dirname)
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath, ignore_errors=True)
        # copy script
        self.copy_tree(self.script_root, dirpath)
        # copy log
        logpath = os.path.join(dirpath, LOGDIR)
        if os.path.normpath(logpath) != os.path.normpath(self.log_root):
            if os.path.isdir(logpath):
                shutil.rmtree(logpath, ignore_errors=True)
            self.copy_tree(self.log_root, logpath)
        # copy static files
        for subdir in ["css", "fonts", "image", "js"]:
            self.copy_tree(os.path.join(STATIC_DIR, subdir), os.path.join(dirpath, "static", subdir))

        return dirpath, logpath

    def report(self, template_name, output_file=None, record_list=None):
        self._load()
        steps = self._analyse()
        info = json.loads(get_script_info(self.script_root))

        if self.export_dir:
            self.script_root, self.log_root = self._make_export_dir()
            output_file = os.path.join(self.script_root, HTML_FILE)
            self.static_root = "static/"

        if not record_list:
            record_list = [f for f in os.listdir(self.log_root) if f.endswith(".mp4")]
        records = [os.path.join(self.log_root, f) for f in record_list]

        if not self.static_root.endswith(os.path.sep):
            self.static_root = self.static_root.replace("\\", "/")
            self.static_root += "/"

        data = {}
        data['steps'] = steps
        data['name'] = self.script_root
        data['scale'] = self.scale
        data['test_result'] = self.test_result
        data['run_end'] = self.run_end
        data['run_start'] = self.run_start
        data['static_root'] = self.static_root
        data['lang'] = self.lang
        data['records'] = records
        data['info'] = info

        return self._render(template_name, output_file, **data)


def simple_report(logpath, tplpath=".", logfile=LOGFILE, output=HTML_FILE):
    rpt = LogToHtml(tplpath, logpath, logfile=logfile)
    rpt.report(HTML_TPL, output_file=output)


def get_parger(ap):
    ap.add_argument("script", help="script filepath")
    ap.add_argument("--outfile", help="output html filepath, default to be log.html", default=HTML_FILE)
    ap.add_argument("--static_root", help="static files root dir")
    ap.add_argument("--log_root", help="log & screen data root dir, logfile should be log_root/log.txt")
    ap.add_argument("--record", help="custom screen record file path", nargs="+")
    ap.add_argument("--export", help="export a portable report dir containing all resources")
    ap.add_argument("--lang", help="report language", default="en")
    ap.add_argument("--plugins", help="load reporter plugins", nargs="+")
    return ap


def main(args):
    # script filepath
    path = decode_path(args.script)
    record_list = args.record or []
    log_root = decode_path(args.log_root) or decode_path(os.path.join(path, LOGDIR))
    static_root = args.static_root or STATIC_DIR
    static_root = decode_path(static_root)
    export = decode_path(args.export) if args.export else None
    lang = args.lang if args.lang in ['zh', 'en'] else 'en'
    plugins = args.plugins

    # gen html report
    rpt = LogToHtml(path, log_root, static_root, export_dir=export, lang=lang, plugins=plugins)
    rpt.report(HTML_TPL, output_file=args.outfile, record_list=record_list)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    args = get_parger(ap).parse_args()
    main(args)
