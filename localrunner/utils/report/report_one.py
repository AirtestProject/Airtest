#!/usr/bin/env python
# -*- coding:utf8 -*-
import json
import os
import sys
import time

import jinja2

class MoaLogDisplay(object):
    """change Moa log to html display """
    scale = 0.5
    def __init__(self, path, host="", static_root=""):
        """ logpath """
        self.log = []
        self.host = host
        self.path = path
        self.static_root = static_root
        self.img_type = ['touch', 'swipe', 'wait', 'exists', 'assert_not_exists', 'assert_exists'] 
        with open(path,'rb')as f:
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
                step.append(temp)
                temp = {}

        self.step = step
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
        
        if step['type'] in self.img_type:
            #一般来说会有截图 没有这层就无法找到截图了
            if step.get(3):
                step['screenshot'] = self.host + step[3]['screen']
            if step.get(2):
                step['image_to_find'] = self.host + step[2]['args'][0]['filename']
                step['resolution'] = step[2]['args'][0]['resolution']
            
            if not step['trace']:
                step['target_pos'] = step[2].get('ret')
                if step['target_pos']:
                    step['top'] = round(step['target_pos'][1])
                    step['left'] = round(step['target_pos'][0])
            
            #swipe 需要显示一个方向
            if step['type'] == 'swipe':
                vector = step[1]["kwargs"].get("vector")
                if vector:
                    step['swipe'] = self.dis_vector(vector)

            if step['type'] in ['assert_exists', 'assert_not_exists']:
                args = step[1]["args"]
                if len(args) >= 2:
                    step['assert'] = args[1] 

        elif step['type'] in ['text', 'sleep', 'keyevent']:
            step[step['type']] = step[1]['args'][0]
        
        step['desc'] = self.func_desc(step)
        step['title'] = self.func_title(step)
        return step


    def func_desc(self, step):
        """ 把对应函数(depth=1)的name显示成中文 """
        name = step['type']
        desc = {
            #"snapshot":"截图",
            #"_loop_find":"寻找目标位置",
            "touch":u"寻找目标图片，触摸屏幕坐标%s" % step.get('target_pos',''),
            "swipe":u"从目标坐标点%s向着%s滑动" % (step.get('target_pos',''), step.get('swipe','')),

            "wait":u"等待目标图片出现",
            "exists":u"判断目标图片存在",

            "text":u"输入文字:%s" % step.get('text',''),
            "keyevent":u"点击[%s]按键" % step.get('keyevent',''),
            "sleep":u"等待%s秒" % step.get('sleep',''),

            "assert_exists":u"目标图片应当存在",
            "assert_not_exists":u"目标图片应当不存在",

        }

        return desc.get(name, '%s%s' % (name,step[1]['args']))

    def func_title(self, step):
        title = {
            "touch":u"点击",
            "swipe":u"滑动",
            "wait":u"等待",
            "exists":u"验证存在",
            "text":u"输入",
            "keyevent":u"按键",
            "sleep":u"sleep",
            "server_call":u"调用服务器方法",
            "assert_exists":u"验证存在",
            "assert_not_exists":u"验证不存在",            
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
        data['host'] = self.host
        data['img_type'] = self.img_type
        data['script_name'] = get_script_name(self.path)     
        data['scale'] = self.scale
        data['test_result'] = self.test_result
        data['run_end'] = self.run_end
        data['run_start'] = self.run_start
        data['static_root'] = self.static_root
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
        
 
def main():
    if len(sys.argv) == 1:
        print """
            usage:  
            python report_one.py test.owl [output.html] [static_root]

        """
        return 

    #print path
    path = sys.argv[1].decode(sys.getfilesystemencoding())
    #save to file
    outfile = ''
    if len(sys.argv) > 2:
        outfile = sys.argv[2]
    #static file root
    static_root = ''
    if len(sys.argv) > 3:
        static_root = sys.argv[3].decode(sys.getfilesystemencoding())
        if not (static_root.endswith("\\") or static_root.endswith("/")):
            static_root += "/"

    thisdir = os.path.dirname(sys.argv[0])
    jinja_environment = jinja2.Environment(autoescape=True, loader=jinja2.FileSystemLoader(thisdir))
    tpl = jinja_environment.get_template("log_template.html")
    rpt = MoaLogDisplay(path + "/log.txt", path + "/", static_root)
    html = rpt.render(tpl)

    default = 'log.html'
    f = open(outfile or default, 'w')
    f.write(html.encode('utf8'))
    f.close()

        
if __name__ == "__main__":
    main()

