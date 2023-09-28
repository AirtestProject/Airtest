#!/usr/bin/env python
# -*- coding:utf8 -*-
import json
import os
import io
import re
import six
import sys
from PIL import Image
import shutil
import jinja2
import traceback
from copy import deepcopy
from datetime import datetime
from markupsafe import Markup, escape
from six.moves.urllib.parse import parse_qsl, urlparse
try:
    from jinja2 import evalcontextfilter as pass_eval_context  # jinja2<3.1
except:
    from jinja2 import pass_eval_context  # jinja2>=3.1
from airtest.aircv import imread, get_resolution
from airtest.aircv.error import FileNotExistError
from airtest.core.settings import Settings as ST
from airtest.aircv.utils import compress_image
from airtest.utils.compat import decode_path, script_dir_name
from airtest.cli.info import get_script_info
from airtest.utils.logger import get_logger
from airtest.utils.snippet import parse_device_uri
from six import PY3

LOGGING = get_logger(__name__)
DEFAULT_LOG_DIR = "log"
DEFAULT_LOG_FILE = "log.txt"
HTML_TPL = "log_template.html"
HTML_FILE = "log.html"
STATIC_DIR = os.path.dirname(__file__)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@pass_eval_context
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                          for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def timefmt(timestamp):
    """
    Formatting of timestamp in Jinja2 templates
    :param timestamp: timestamp of steps
    :return: "%Y-%m-%d %H:%M:%S"
    """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


class LogToHtml(object):
    """Convert log to html display """
    scale = 0.5

    def __init__(self, script_root, log_root="", static_root="", export_dir=None, script_name="", logfile=None, lang="en", plugins=None):
        self.log = []
        self.devices = {}
        self.script_root = script_root
        self.script_name = script_name
        if not self.script_name or os.path.isfile(self.script_root):
            self.script_root, self.script_name = script_dir_name(self.script_root)
        self.log_root = log_root or ST.LOG_DIR or os.path.join(".", DEFAULT_LOG_DIR)
        self.static_root = static_root or STATIC_DIR
        self.test_result = True
        self.run_start = None
        self.run_end = None
        self.export_dir = export_dir
        self.logfile = logfile or getattr(ST, "LOG_FILE", DEFAULT_LOG_FILE)
        self.lang = lang
        self.init_plugin_modules(plugins)

    @staticmethod
    def init_plugin_modules(plugins):
        if not plugins:
            return
        for plugin_name in plugins:
            LOGGING.debug("try loading plugin: %s" % plugin_name)
            try:
                __import__(plugin_name)
            except:
                LOGGING.error(traceback.format_exc())

    def _load(self):
        logfile = os.path.join(self.log_root, self.logfile)
        if not PY3:
            logfile = logfile.encode(sys.getfilesystemencoding())
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
                self.run_start = log.get('data', {}).get('start_time', '') or log["time"]
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

        translated_steps = [self._translate_step(s) for s in steps]
        if len(translated_steps) > 0 and translated_steps[-1].get("traceback"):
            # Final Error
            self.test_result = False
        return translated_steps

    def _translate_step(self, step):
        """translate single step"""
        name = step["data"]["name"]
        title = self._translate_title(name, step)
        code = self._translate_code(step)
        desc = self._translate_desc(step, code)
        screen = self._translate_screen(step, code)
        info = self._translate_info(step)
        assertion = self._translate_assertion(step)
        self._translate_device(step)

        translated = {
            "title": title,
            "time": step["time"],
            "code": code,
            "screen": screen,
            "desc": desc,
            "traceback": info[0],
            "log": info[1],
            "assert": assertion,
        }
        return translated

    def _translate_assertion(self, step):
        if "assert_" in step["data"].get("name", "") and "msg" in step["data"].get("call_args", {}):
            return step["data"]["call_args"]["msg"]

    def _translate_screen(self, step, code):
        if step['tag'] not in ["function", "info"] or not step.get("__children__"):
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
                snapshot = item["data"].get("ret", None)
                if isinstance(snapshot, six.text_type):
                    src = snapshot
                elif isinstance(snapshot, dict):
                    src = snapshot['screen']
                    screen['resolution'] = snapshot['resolution']
                else:
                    continue
                if self.export_dir:  # all relative path
                    screen['_filepath'] = os.path.join(DEFAULT_LOG_DIR, src)
                else:
                    screen['_filepath'] = os.path.abspath(os.path.join(self.log_root, src))
                screen['src'] = screen['_filepath']
                self.get_thumbnail(os.path.join(self.log_root, src))
                screen['thumbnail'] = self.get_small_name(screen['src'])
                break

        display_pos = None

        for item in step["__children__"]:
            if item["data"]["name"] == "_cv_match" and isinstance(item["data"].get("ret"), dict):
                cv_result = item["data"]["ret"]
                pos = cv_result['result']
                if self.is_pos(pos):
                    display_pos = [round(pos[0]), round(pos[1])]
                rect = self.div_rect(cv_result['rectangle'])
                screen['rect'].append(rect)
                screen['confidence'] = cv_result['confidence']
                break

        if step["data"]["name"] in ["touch", "assert_exists", "wait", "exists"]:
            # 将图像匹配得到的pos修正为最终pos
            if self.is_pos(step["data"].get("ret")):
                display_pos = step["data"]["ret"]
            elif self.is_pos(step["data"]["call_args"].get("v")):
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

    def _translate_device(self, step):
        if step["tag"] == "function" and step["data"]["name"] == "connect_device":
            uri = step["data"]["call_args"]["uri"]
            platform, uuid, params = parse_device_uri(uri)
            if "name" in params:
                uuid = params["name"]
            if uuid not in self.devices:
                self.devices[uuid] = uri
            return uuid
        return None

    @classmethod
    def get_thumbnail(cls, path):
        """compress screenshot"""
        new_path = cls.get_small_name(path)
        if not os.path.isfile(new_path):
            try:
                img = Image.open(path)
                compress_image(img, new_path, ST.SNAPSHOT_QUALITY, max_size=300)
            except Exception:
                LOGGING.error(traceback.format_exc())
            return new_path
        else:
            return None

    @classmethod
    def get_small_name(cls, filename):
        name, ext = os.path.splitext(filename)
        return "%s_small%s" % (name, ext)

    def _translate_info(self, step):
        trace_msg, log_msg = "", ""
        if "traceback" in step["data"]:
            # 若包含有traceback内容，将会认定步骤失败
            trace_msg = step["data"]["traceback"]
        if step["tag"] == "info":
            if "log" in step["data"]:
                # 普通文本log内容，仅显示
                log_msg = step["data"]["log"]
        return trace_msg, log_msg

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
                if self.export_dir:  # all relative path
                    image_path = value['filename']
                    if not os.path.isfile(os.path.join(self.script_root, image_path)) and value['_filepath']:
                        # copy image used by using statement
                        shutil.copyfile(value['_filepath'], os.path.join(self.script_root, value['filename']))
                else:
                    image_path = os.path.abspath(value['_filepath'] or value['filename'])
                arg["image"] = image_path
                try:
                    if not value['_filepath'] and not os.path.exists(value['filename']):
                        crop_img = imread(os.path.join(self.script_root, value['filename']))
                    else:
                        crop_img = imread(value['_filepath'] or value['filename'])
                except FileNotExistError:
                    # 在某些情况下会报图片不存在的错误（偶现），但不应该影响主流程
                    if os.path.exists(image_path):
                        arg["resolution"] = get_resolution(imread(image_path))
                    else:
                        arg["resolution"] = (0, 0)
                else:
                    arg["resolution"] = get_resolution(crop_img)
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
            "connect_device": lambda : u"Connect device: %s" % args.get("uri"),
        }

        # todo: 最好用js里的多语言实现
        desc_zh = {
            "snapshot": lambda: u"截图描述: %s" % args.get("msg"),
            "touch": lambda: u"点击 %s" % (u"目标图片" if isinstance(args['v'], dict) else u"屏幕坐标 %s" % args['v']),
            "swipe": u"滑动操作",
            "wait": u"等待目标图片出现",
            "exists": lambda: u"图片%s存在" % ("" if res else u"不"),
            "text": lambda: u"输入文字:%s" % args.get('text'),
            "keyevent": lambda: u"点击[%s]按键" % args.get('keyname'),
            "sleep": lambda: u"等待%s秒" % args.get('secs'),
            "assert_exists": u"断言目标图片存在",
            "assert_not_exists": u"断言目标图片不存在",
            "connect_device": lambda : u"连接设备： %s" % args.get("uri"),
        }

        if self.lang == "zh":
            desc = desc_zh

        ret = desc.get(name)
        if callable(ret):
            ret = ret()
        return ret

    def _translate_title(self, name, step):
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
            "connect_device": u"Connect device",
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
        env.filters['nl2br'] = nl2br
        env.filters['datetime'] = timefmt
        template = env.get_template(template_name)
        html = template.render(**template_vars)

        if output_file:
            with io.open(output_file, 'w', encoding="utf-8") as f:
                f.write(html)
            LOGGING.info(output_file)

        return html

    def is_pos(self, v):
        return isinstance(v, (list, tuple))

    def copy_tree(self, src, dst, ignore=None):
        try:
            shutil.copytree(src, dst, ignore=ignore)
        except:
            LOGGING.error(traceback.format_exc())

    def _make_export_dir(self):
        """mkdir & copy /staticfiles/screenshots"""
        # let dirname = <script name>.log
        dirname = self.script_name.replace(os.path.splitext(self.script_name)[1], ".log")
        # mkdir
        dirpath = os.path.join(self.export_dir, dirname)
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath, ignore_errors=True)

        # copy script
        def ignore_export_dir(dirname, filenames):
            # 忽略当前导出的目录，防止递归导出
            if os.path.commonprefix([dirpath, dirname]) == dirpath:
                return filenames
            return []
        self.copy_tree(self.script_root, dirpath, ignore=ignore_export_dir)
        # copy log
        logpath = os.path.join(dirpath, DEFAULT_LOG_DIR)
        if os.path.normpath(logpath) != os.path.normpath(self.log_root):
            if os.path.isdir(logpath):
                shutil.rmtree(logpath, ignore_errors=True)
            self.copy_tree(self.log_root, logpath, ignore=shutil.ignore_patterns(dirname))
        # if self.static_root is not a http server address, copy static files from local directory
        if not self.static_root.startswith("http"):
            for subdir in ["css", "fonts", "image", "js"]:
                self.copy_tree(os.path.join(self.static_root, subdir), os.path.join(dirpath, "static", subdir))

        return dirpath, logpath

    def get_relative_log(self, output_file):
        """
        Try to get the relative path of log.txt
        :param output_file: output file: log.html
        :return: ./log.txt or ""
        """
        try:
            html_dir = os.path.dirname(output_file)
            if self.export_dir:
                # When exporting reports, the log directory will be named log/ (DEFAULT_LOG_DIR),
                # so the relative path of log.txt is log/log.txt
                return os.path.join(DEFAULT_LOG_DIR, os.path.basename(self.logfile))
            return os.path.relpath(os.path.join(self.log_root, self.logfile), html_dir)
        except:
            LOGGING.error(traceback.format_exc())
            return ""

    def get_console(self, output_file):
        html_dir = os.path.dirname(output_file)
        file = os.path.join(html_dir, 'console.txt')
        content = ""
        if os.path.isfile(file):
            try:
                content = self.readFile(file)
            except Exception:
                try:
                    content = self.readFile(file, "gbk")
                except Exception:
                    content = traceback.format_exc() + content
                    content = content + "Can not read console.txt. Please check file in:\n" + file
        return content

    def readFile(self, filename, code='utf-8'):
        content = ""
        with io.open(filename, encoding=code) as f:
            for line in f.readlines():
                content = content + line
        return content

    def report_data(self, output_file=None, record_list=None):
        """
        Generate data for the report page

        :param output_file: The file name or full path of the output file, default HTML_FILE
        :param record_list: List of screen recording files
        :return:
        """
        self._load()
        steps = self._analyse()

        script_path = os.path.join(self.script_root, self.script_name)
        info = json.loads(get_script_info(script_path))
        info['devices'] = self.devices

        if record_list:
            records = [os.path.join(DEFAULT_LOG_DIR, f) if self.export_dir
                       else os.path.abspath(os.path.join(self.log_root, f)) for f in record_list]
        else:
            records = []

        if not self.static_root.endswith(os.path.sep):
            self.static_root = self.static_root.replace("\\", "/")
            self.static_root += "/"

        if not output_file:
            output_file = HTML_FILE

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
        data['log'] = self.get_relative_log(output_file)
        data['console'] = self.get_console(output_file)
        # 如果带有<>符号，容易被highlight.js认为是特殊语法，有可能导致页面显示异常，尝试替换成不常用的{}
        info = json.dumps(data).replace("<", "{").replace(">", "}")
        data['data'] = info
        return data

    def report(self, template_name=HTML_TPL, output_file=HTML_FILE, record_list=None):
        """
        Generate the report page, you can add custom data and overload it if needed

        :param template_name: default is HTML_TPL
        :param output_file: The file name or full path of the output file, default HTML_FILE
        :param record_list: List of screen recording files
        :return:
        """
        if not self.script_name:
            path, self.script_name = script_dir_name(self.script_root)

        if self.export_dir:
            self.script_root, self.log_root = self._make_export_dir()
            # output_file可传入文件名，或绝对路径
            output_file = output_file if output_file and os.path.isabs(output_file) \
                else os.path.join(self.script_root, output_file or HTML_FILE)
            if not self.static_root.startswith("http"):
                self.static_root = "static/"

        if not record_list:
            record_list = [f for f in os.listdir(self.log_root) if f.endswith(".mp4")]
        data = self.report_data(output_file=output_file, record_list=record_list)
        return self._render(template_name, output_file, **data)


def simple_report(filepath, logpath=True, logfile=None, output=HTML_FILE):
    path, name = script_dir_name(filepath)
    if logpath is True:
        logpath = os.path.join(path, getattr(ST, "LOG_DIR", DEFAULT_LOG_DIR))
    rpt = LogToHtml(path, logpath, logfile=logfile or getattr(ST, "LOG_FILE", DEFAULT_LOG_FILE), script_name=name)
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
    ap.add_argument("--report", help="placeholder for report cmd", default=True, nargs="?")
    return ap


def main(args):
    # script filepath
    path, name = script_dir_name(args.script)
    record_list = args.record or []
    log_root = decode_path(args.log_root) or decode_path(os.path.join(path, DEFAULT_LOG_DIR))
    static_root = args.static_root or STATIC_DIR
    static_root = decode_path(static_root)
    export = decode_path(args.export) if args.export else None
    lang = args.lang if args.lang in ['zh', 'en'] else 'en'
    plugins = args.plugins

    # gen html report
    rpt = LogToHtml(path, log_root, static_root, export_dir=export, script_name=name, lang=lang, plugins=plugins)
    rpt.report(HTML_TPL, output_file=args.outfile, record_list=record_list)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    args = get_parger(ap).parse_args()
    main(args)
