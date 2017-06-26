#!/usr/bin/env python
# -*- coding:utf8 -*-
import json
import os
import io
import argparse
import jinja2
from airtest.report.report_gif import gen_gif

LOGFILE = "log.txt"
SCREENDIR = "img_record"


class MoaLogDisplay(object):
    """change Moa log to html display """
    scale = 0.5

    def __init__(self, script_root="", log_root="", static_root="", author=""):
        """ logpath """
        self.log = []
        self.script_root = script_root
        self.log_root = log_root
        self.static_root = static_root
        self.run_start = None
        self.run_end = None
        self.author = author
        self.img_type = ('touch', 'swipe', 'wait', 'exists', 'assert_not_exists', 'assert_exists', 'snapshot')
        self.uiautomator_img_type = ('click', 'long_click', 'ui.swipe', 'drag', 'fling', 'scroll', 'press', 'clear_text', 'set_text', 'end', 'assert')
        self.uiautomator_ignore_type = ('select', )
        self.logfile = os.path.join(log_root, LOGFILE)
        self._load()

    def _load(self):
        with io.open(self.logfile, encoding="utf-8")as f:
            for line in f.readlines():
                self.log.append(json.loads(line))

    def analyse(self):
        """ 进一步解析成模板可显示的内容 """
        step = []
        temp = {}
        self.test_result = True
        for log in self.log:
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
                    temp['trace'] = True
                    temp['traceback'] = log['data']['traceback']
                    self.test_result = False
                else:
                    temp['trace'] = False
                temp = self.translate(temp)
                if temp is not None:
                    step.append(temp)
                temp = {}

        self.step = step
        if step:
            self.run_start = step[0].get('start_time')
            self.run_end = step[-1].get('end_time')

        return step

    def translate(self, step):
        """
        按照depth = 1 的name来分类
        touch,swipe,wait,exist 都是搜索图片位置，然后执行操作，包括3层调用
                            3=screenshot 2= _loop_find  1=本身操作
        keyevent,text,sleep 和图片无关，直接显示一条说明就可以
                            1= 本身
        server_call没有log
        assert 类似于exist
        """
        scale = MoaLogDisplay.scale
        self.scale = scale
        step['type'] = step[1]['name']
        
        if step['type'] in self.uiautomator_ignore_type:
            return None

        if step['type'] in self.img_type or step['type'] in self.uiautomator_img_type:
            # 一般来说会有截图 没有这层就无法找到截图了
            st = 3
            while st in step:
                if 'screen' in step[st]:
                    step['screenshot'] = os.path.join(self.log_root, step[st]['screen'])
                    break
                st += 1
            if 'screenshot' not in step:
                step['target_pos'] = step[1].get('args')

            if step['type'] == 'snapshot':
                # 对于截图的展示，把截图内容本身作为运行时屏幕，截图文件的文件名作为错误描述
                step['screenshot'] = os.path.join(self.log_root, os.path.dirname(step[2]['screen']), step[1]['args'][0])
            elif step.get(2):
                if step['type'] in self.img_type:
                    step['image_to_find'] = os.path.join(self.script_root, step[2]['args'][0]['filename'])
                    step['resolution'] = step[2]['args'][0].get("resolution", None)
                    step['record_pos'] = step[2]['args'][0].get("record_pos", None)
            
                if not step['trace']:
                    step['target_pos'] = step[2].get('ret')
                    if step['target_pos']:
                        cv = step[2].get('cv', {})
                        step['confidence'] = self.to_percent(cv.get('confidence'))

                        # 如果存在wnd_pos，说明是windows截图，由于target_pos是相对屏幕坐标，mark_pos是相对截屏坐标
                        #       因此需要一次wnd_pos的标记偏移，才能保证报告中标记位置的正确。
                        if 'wnd_pos' in step[2]:
                            wnd_pos = step[2]['wnd_pos']
                            # mark_pos = (step['target_pos'][0] - step["wnd_pos"][0], step[2]['target_pos'][1] - step[2]["wnd_pos"][1])
                            mark_pos = (step['target_pos'][0] - wnd_pos[0], step['target_pos'][1] - wnd_pos[1])
                        else:
                            mark_pos = step['target_pos']
                        
                        # 如果点击坐标target_pos和识别坐标result不同，绘制识别区域rectangle时，需要进行相应的偏移：
                        # if mark_pos != cv.get('result'):
                        #     operate_pos = mark_pos
                        #     match_pos = cv.get('result')
                        #     offset = (operate_pos[0] - match_pos[0], operate_pos[1] - match_pos[1])
                        #     step['rect'] = self.div_rect(cv.get('rectangle', []), offset)
                        # else:
                        step['rect'] = self.div_rect(cv.get('rectangle', []))
                        step['top'] = round(mark_pos[1])
                        step['left'] = round(mark_pos[0])

            # swipe 需要显示一个方向
            if step['type'] == 'swipe':
                vector = step[1]["kwargs"].get("vector")
                if vector:
                    step['swipe'] = self.dis_vector(vector)

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
            step['desc'] = u'assert_equal [ "%s", "%s", "%s" ]' %(args[0], args[1], args[2])
            step['title'] = self.func_title(step)
            return step

        elif step['type'] in ['server_call']:
            args = step[1]["args"]
            # 单独对server_call进行步骤说明。
            step['desc'] = u'server_call [ "%s" ] ' %(args[0])
            step['title'] = self.func_title(step)
            return step

        step['desc'] = self.func_desc(step)
        step['title'] = self.func_title(step)
        return step

    def to_percent(self, p):
        if not p:
            return ''
        
        return round(p * 100, 1)

    def div_rect(self, r, offset=None):
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

    def func_desc(self, step):
        """ 把对应函数(depth=1)的name显示成中文 """
        name = step['type']
        desc = {
            # "snapshot":"截图",
            # "_loop_find":"寻找目标位置",
            "touch": u"寻找目标图片，触摸屏幕坐标%s" % repr(step.get('target_pos', '')),
            "swipe": u"从目标坐标点%s向着%s滑动" % (repr(step.get('target_pos', '')), step.get('swipe', '')),

            "wait": u"等待目标图片出现",
            "exists": u"图片%s存在" % step.get('exists_ret', ''),

            "text": u"输入文字:%s" % step.get('text', ''),
            "keyevent": u"点击[%s]按键" % step.get('keyevent', ''),
            "sleep": u"等待%s秒" % step.get('sleep', ''),

            "assert_exists": u"目标图片应当存在",
            "assert_not_exists": u"目标图片应当不存在",

            # "snapshot": step[1]['args'][0],
        }

        return desc.get(name, '%s%s' % (name, step[1]['args']))

    def func_title(self, step):
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

            "assert_equal": u"验证相等",
            "assert_not_equal": u"验证不相等",
        }
        name = step['type']
        return title.get(name, name)

    def dis_vector(self, v):

        x = int(v[0])
        y = int(v[1])
        a = ''
        b = ''
        if x > 0:
            a = u'右'
        if x < 0:
            a = u'左'
        if y > 0:
            b = u'上'
        if y < 0:
            b = u'下'

        return a+b

    def _render(self, template_name, **template_vars):
        """ 用jinja2输出html 
        """
        TEMPLATE_DIR = '.'
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
            extensions=(
            ),
            autoescape = True
        )
        #env.globals['static'] = STATIC
        template = env.get_template(template_name)
        return template.render(**template_vars)

    def render(self, template_name):

        data = {}
        data['steps'] = self.analyse()
        data['host'] = self.script_root
        data['img_type'] = self.img_type
        data['uiautomator_img_type'] = self.uiautomator_img_type
        data['script_name'] = get_script_name(self.script_root)     
        data['scale'] = self.scale
        data['test_result'] = self.test_result
        data['run_end'] = self.run_end
        data['run_start'] = self.run_start
        data['static_root'] = self.static_root
        data['author'] = self.author
        return self._render(template_name, **data)     


def get_script_name(path):

    pp = path.replace('\\', '/').split('/')
    for p in pp:
        if p.endswith('.owl'):
            return p

    return ''


def safe_percent(a, b):
    if b:
        return round(a * 100.0 / b, 1)
    else:
        return 0


def get_file_author(file_path):
    if not os.path.exists(file_path):
        print("get_file_author, file_path %s not existed" % file_path)
        return

    try:
        fp = io.open(file_path, encoding="utf-8")
    except IOError:
        print("read file %s error" % file_path)
        return

    author = ''
    for line in fp:
        if '__author__' in line and '=' in line:
            author = line.split('=')[-1].strip()[1:-1]
            break
    return author


def get_parger(ap):
    ap.add_argument("script", help="script filepath")
    ap.add_argument("--outfile", help="output html filepath, default to be log.html", default="log.html")
    ap.add_argument("--static_root", help="static files root dir")
    ap.add_argument("--log_root", help="log & screen data root dir, logfile should be log_root/log.txt")
    ap.add_argument("--gif", help="generate gif, default to be log.gif", nargs="?", const="log.gif")
    return ap


def main(args):
    # script filepath
    path = args.script
    basename = os.path.basename(path).split(".")[0]
    py_file = path + "/" + basename + ".py"
    author = get_file_author(py_file)
    # output html filepath
    outfile = args.outfile
    # static file root
    if args.static_root is not None:
        static_root = args.static_root
    else:
        static_root = os.path.dirname(__file__)
    if not static_root.endswith(os.path.sep):
        static_root += "/"

    # log data root
    log_root = args.log_root or path
    if not log_root.endswith(os.path.sep):
        log_root += "/"

    jinja_environment = jinja2.Environment(autoescape=True, loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
    tpl = jinja_environment.get_template("log_template.html")
    print(path)
    print(log_root)
    print(static_root)
    # TODO:  File "c:\python27\lib\site-packages\nose\plugins\xunit.py", line 129, in write
    # UnicodeEncodeError: 'ascii' codec can't encode characters in position 0-1: ordinal not in range(128)

    # print(author)
    rpt = MoaLogDisplay(path, log_root, static_root, author)

    # gen gif
    if args.gif is not None:
        steps = rpt.analyse()
        gen_gif(os.path.join(log_root, SCREENDIR), steps, output=args.gif)
    # gen html report
    else:
        html = rpt.render(tpl)
        with io.open(outfile, 'w', encoding="utf-8") as f:
            f.write(html)


if __name__ == "__main__":
    #single runner
    import argparse
    ap = argparse.ArgumentParser()
    args = get_parger(ap).parse_args()

    main(args)
