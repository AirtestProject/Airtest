#!/usr/bin/env python
# -*- coding:utf8 -*-
import json
import os
import io
import sys
import jinja2
from collections import defaultdict
from airtest.utils.compat import decode_path, PY3

LOGFILE = "log.txt"


class LogToHtml(object):
    """Convert log to html display """
    scale = 0.5

    def __init__(self, script_root="", log_root="", static_root="", author="", logfile=LOGFILE):
        self.log = []
        self.script_root = script_root
        self.log_root = log_root
        self.static_root = static_root or os.path.dirname(__file__)
        self.test_result = True
        self.run_start = None
        self.run_end = None
        self.author = author
        self.img_type = ('touch', 'swipe', 'wait', 'exists', 'assert_not_exists', 'assert_exists', 'snapshot')
        self.logfile = os.path.join(log_root, logfile)
        self._load()
        self.error_str = ""
        self._steps = None
        self.all_step = None

    def _load(self):
        # 假如log.txt不存在，以前是直接抛出异常，现在改为读不到文件就设置log为空，看看会不会有什么问题
        with io.open(self.logfile.encode(sys.getfilesystemencoding()) if not PY3 else self.logfile) as f:
            for line in f.readlines():
                self.log.append(json.loads(line))

    def analyse(self):
        """ 进一步解析成模板可显示的内容 """
        steps = []
        temp = {}
        current_step = 'main_script'
        all_step = defaultdict(list)

        for log in self.log:
            if log["depth"] == 0 and log.get("tag") in ["main_script", "pre_script", "post_script"]:
                # 根据脚本执行的pre,main,post，将log区分开
                current_step = log.get("tag", "main_script")

            #拆分成每一个步骤，并且加上traceback的标志
            #depth相同，后来的数据直接覆盖（目前只有截图数据会这样）
            log.update(log["data"])
            if 'start_time' not in temp and log.get('time'):
                temp['start_time'] = log['time']

            if log['depth'] in temp:
                temp[log['depth']].update(log)
            else:
                temp[log['depth']] = log

            if log['depth'] == 1:
                #depth到1才是一个完整操作语句，转换成模板需要的数据
                #exists 中间有报错也是正常的 以depth = 1 为准
                temp['end_time'] = log['time']
                if log['tag'] == "error":
                    # 假如有trace，把异常的信息临时记下来，如果是重复的异常就不重复显示在页面上了
                    if self.error_str and self.error_str == log['data'].get('error_str'):
                        continue
                    else:
                        self.error_str = log['data'].get('error_str') or ''
                    temp['trace'] = True
                    temp['traceback'] = log['data']['traceback']
                    self.test_result = False
                else:
                    temp['trace'] = False

                temp = self.translate(temp)
                if temp is not None:
                    steps.append(temp)
                    all_step[current_step].append(temp)

                temp = {}

        self._steps = steps
        self.all_step = all_step
        if steps:
            self.run_start = steps[0].get('start_time')
            self.run_end = steps[-1].get('end_time')

        return steps

    def translate(self, step):
        """
        按照depth = 1 的name来分类
        touch,swipe,wait,exist 都是搜索图片位置，然后执行操作，包括3层调用
                            3=screenshot 2= _loop_find  1=本身操作
        keyevent,text,sleep 和图片无关，直接显示一条说明就可以
                            1= 本身
        assert 类似于exist
        """
        scale = LogToHtml.scale
        self.scale = scale
        step['type'] = step[1]['name']

        if step['type'] in self.img_type:
            # 一般来说会有截图 没有这层就无法找到截图了
            st = 1
            while st in step:
                if 'screen' in step[st]:
                    step['screenshot'] = os.path.join(self.log_root, step[st]['screen'])
                    break
                st += 1

            if step['type'] == 'snapshot':
                step['screenshot'] = step[1]['ret'] or ""
                step['text'] = step[1]['kwargs'].get('msg', '') if step[1]['kwargs'] else ''

            elif step.get(2):
                if step['type'] in self.img_type:
                    # testlab那边会将所有执行的脚本内容放到同一个文件夹下，然而如果是本地执行会导致找不到pre/post脚本里的图片
                    if len(step[2]['args']) > 0 and 'filename' in step[2]['args'][0]:
                        image_path = os.path.join(self.script_root, str(step[2]['args'][0]['filename']))
                    else:
                        image_path = ""
                    if not os.path.isfile(image_path) and step[2]['args'] and len(step[2]['args']) > 0 and 'filepath' in step[2]['args'][0]:
                        image_path = step[2]['args'][0]['filepath']
                    if not os.path.isfile(image_path) and step.get("trace"):
                        step['desc'] = self.func_desc(step)
                        step['title'] = self.func_title(step)
                        return step
                    step['image_to_find'] = image_path
                    if step[2]['args'] and len(step[2]['args']) > 0:
                        step['resolution'] = step[2]['args'][0].get("resolution", None)
                        step['record_pos'] = step[2]['args'][0].get("record_pos", None)
                if not step['trace']:
                    if step[2]["name"] == "loop_find":
                        step['target_pos'] = step[2].get('ret')
                        cv = step[2].get('cv', {})
                        if cv:
                            step['confidence'] = self.to_percent(cv.get('confidence'))
                            # 如果存在wnd_pos，说明是windows截图，由于target_pos是相对屏幕坐标，mark_pos是相对截屏坐标
                            #       因此需要一次wnd_pos的标记偏移，才能保证报告中标记位置的正确。
                            if 'wnd_pos' in step[2]:
                                wnd_pos = step[2]['wnd_pos']
                                mark_pos = (step['target_pos'][0] - wnd_pos[0], step['target_pos'][1] - wnd_pos[1])
                            else:
                                mark_pos = step['target_pos']

                            step['rect'] = self.div_rect(cv.get('rectangle', []))
                            if isinstance(mark_pos, (tuple, list)):
                                step['top'] = round(mark_pos[1])
                                step['left'] = round(mark_pos[0])

            if step['type'] == 'touch':
                try:
                    target = step[1]['args'][0]
                except (IndexError, KeyError):
                    target = None
                if isinstance(target, (tuple, list)):
                    step['target_pos'] = target
                    step['left'], step['top'] = target

            # swipe 需要显示一个方向
            if step['type'] == 'swipe':
                vector = step[1]["kwargs"].get("vector")
                if vector:
                    step['swipe'] = self.dis_vector(vector)
                    step['vector'] = vector

            # print step['type']
            if step['type'] in ['assert_exists', 'assert_not_exists']:
                args = step[1]["args"]
                if len(args) >= 2:
                    step['assert'] = args[1]

            if step['type'] == 'exists':
                # ret 为false表示图片没有找到
                step['exists_ret'] = u"不" if step[1].get('ret', False) == False else ""

        elif step['type'] in ['text', 'sleep', 'keyevent']:
            step[step['type']] = step[1]['args'][0]

        elif step['type'] in ['assert_equal', 'assert_not_equal']:
            args = step[1]["args"]
            if len(args) >= 2:
                step['assert'] = args[2]
            # 单独对assert_equal和assert_not_equal进行步骤说明。
            step['desc'] = u'assert_equal [ "%s", "%s", "%s" ]' % (args[0], args[1], args[2])
            step['title'] = self.func_title(step)
            return step

        step['desc'] = self.func_desc(step)
        step['title'] = self.func_title(step)
        return step

    @staticmethod
    def to_percent(p):
        if not p:
            return ''
        
        return round(p * 100, 1)

    @staticmethod
    def div_rect(r, offset=None):
        if not r:
            return {}
        
        xs = [p[0] for p in r]
        ys = [p[1] for p in r]
        
        left = min(xs)
        top = min(ys)
        w = max(xs) - left
        h = max(ys) - top

        # offset参数，是在log中点击坐标和识别坐标不同时(人为点击偏移)，绘制识别区域也需要同样的偏移：
        if offset:
            left = left + offset[0]
            top = top + offset[1]
        
        return {'left': left, 'top': top, 'width': w, 'height': h}

    @staticmethod
    def func_desc(step):
        """ 把对应函数(depth=1)的name显示成中文 """
        name = step['type']
        desc = {
            "snapshot": u"截图描述：%s" % step.get('text', ''),
            "touch": u"寻找目标图片，触摸屏幕坐标%s" % repr(step.get('target_pos', '')),
            "swipe": u"从目标坐标点%s向%s滑动%s" % (repr(step.get('target_pos', '')), step.get('swipe', ''), repr(step.get('vector', ""))),

            "wait": u"等待目标图片出现",
            "exists": u"图片%s存在" % step.get('exists_ret', ''),

            "text": u"输入文字:%s" % step.get('text', ''),
            "keyevent": u"点击[%s]按键" % step.get('keyevent', ''),
            "sleep": u"等待%s秒" % step.get('sleep', ''),

            "assert_exists": u"目标图片应当存在",
            "assert_not_exists": u"目标图片应当不存在",
            "traceback": u"异常信息",
            # "snapshot": step[1]['args'][0],
        }
        return desc.get(name, '%s%s' % (name, step.get(1).get('args', "") if 1 in step else ""))

    @staticmethod
    def func_title(step):
        title = {
            "touch": u"点击",
            "swipe": u"滑动",
            "wait": u"等待",
            "exists": u"根据图片是否存在选择分支",
            "text": u"输入",
            "keyevent": u"按键",
            "sleep": u"sleep",
            "server_call": u"调用服务器方法",
            "assert_exists": u"验证图片存在",
            "assert_not_exists": u"验证图片不存在",
            "snapshot": u"截图",
            "assert_equal": u"验证相等",
            "assert_not_equal": u"验证不相等",
        }
        name = step['type']
        return title.get(name, name)

    @staticmethod
    def dis_vector(v):
        x = v[0]
        y = v[1]
        a = ''
        b = ''
        if x > 0:
            a = u'右'
        if x < 0:
            a = u'左'
        if y < 0:
            b = u'上'
        if y > 0:
            b = u'下'
        return a+b

    @staticmethod
    def _render(template_name, **template_vars):
        """ 用jinja2输出html 
        """
        TEMPLATE_DIR = '.'
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
            extensions=(),
            autoescape=True
        )
        template = env.get_template(template_name)
        return template.render(**template_vars)

    def render(self, template_name, record_list=None):
        if not record_list:
            record_list = [f for f in os.listdir(self.log_root) if f.endswith(".mp4")]
        records = [os.path.join(self.log_root, f) for f in record_list]

        if not self.static_root.endswith(os.path.sep):
            self.static_root += "/"

        if self.all_step is None:
            self.analyse()

        data = {}
        data['all_steps'] = self.all_step
        data['host'] = self.script_root
        data['script_name'] = get_script_name(self.script_root)
        data['scale'] = self.scale
        data['test_result'] = self.test_result
        data['run_end'] = self.run_end
        data['run_start'] = self.run_start
        data['static_root'] = self.static_root
        data['author'] = self.author
        data['records'] = records

        return self._render(template_name, **data)


def get_script_name(path):
    pp = path.replace('\\', '/').split('/')
    for p in pp:
        if p.endswith('.owl'):
            return p
    return ''


def get_file_author(file_path):
    author = ''
    if not os.path.exists(file_path) and not PY3:
        file_path = file_path.encode(sys.getfilesystemencoding())
    if os.path.exists(file_path):
        fp = io.open(file_path)
        for line in fp:
            if '__author__' in line and '=' in line:
                author = line.split('=')[-1].strip()[1:-1]
                break
    return author


def simple_report(logpath, tplpath=".", logfile=LOGFILE, output="log.html"):
    jinja_environment = jinja2.Environment(autoescape=True, loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
    htmltpl = jinja_environment.get_template("log_template.html")
    rpt = LogToHtml(tplpath, logpath, logfile=logfile)
    rpt.analyse()
    html = rpt.render(htmltpl)
    with io.open(output, 'w', encoding="utf-8") as f:
        f.write(html)
    print(output)


def get_parger(ap):
    ap.add_argument("script", help="script filepath")
    ap.add_argument("--outfile", help="output html filepath, default to be log.html", default="log.html")
    ap.add_argument("--static_root", help="static files root dir")
    ap.add_argument("--log_root", help="log & screen data root dir, logfile should be log_root/log.txt")
    ap.add_argument("--snapshot", help="get all snapshot", nargs='?', const=True, default=False)
    ap.add_argument("--record", help="custom screen record file path", nargs="+")
    return ap


def main(args):
    # script filepath
    path = decode_path(args.script)
    basename = os.path.basename(path).split(".")[0]
    py_file = os.path.join(path, basename + ".py")
    author = get_file_author(py_file)

    # output html filepath
    outfile = args.outfile
    # static file root
    if args.static_root is not None:
        static_root = decode_path(args.static_root)
    else:
        static_root = decode_path(os.path.dirname(__file__))

    # log data root
    log_root = decode_path(args.log_root) or os.path.join(path, "log")
    jinja_environment = jinja2.Environment(autoescape=True, loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
    tpl = jinja_environment.get_template("log_template.html")
    rpt = LogToHtml(path, log_root, static_root, author)

    # gen html report
    if args.record:
        record = args.record
    else:
        record = []
    html = rpt.render(tpl, record_list=record)
    with io.open(outfile, 'w', encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    args = get_parger(ap).parse_args()
    main(args)
