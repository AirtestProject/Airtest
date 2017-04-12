# -*- coding: utf-8 -*-
from images2gif import writeGif
from PIL import Image, ImageDraw
import sys
import os
import json


def draw_circle(img, (x, y), r=20):
    draw = ImageDraw.Draw(img)
    draw.ellipse((x - r, y - r, x + r, y + r), fill='blue', outline='blue')
    return img


def gen_gif(imgdir, steps, output="log.gif"):
    file_names = sorted((fn for fn in os.listdir(imgdir) if fn.endswith('.jpg')))
    if not file_names:
        print "no jpg image found"
        return

    # count duration of each frame by filename
    duration = []
    for i in range(len(file_names) - 1):
        def get_time(filename):
            return int(os.path.splitext(os.path.basename(filename))[0])
        iterval = get_time(file_names[i + 1]) - get_time(file_names[i])
        duration.append(iterval / 1000.0)
    # last frame duration=1 second
    duration.append(1)

    images = []
    for f in file_names:
        img = Image.open(os.path.join(imgdir, f))
        target_pos = None
        for step in steps:
            if f in step.get("screenshot", ""):
                # 如果loop_find中含有wnd_pos变量，则为窗口切图后的匹配，图片位置=操作位置-窗口位置:
                if step[2].has_key("wnd_pos"):
                    wnd_pos = step[2].get("wnd_pos")
                    ret = step[2].get("ret")
                    target_pos = (ret[0] - wnd_pos[0], ret[1] - wnd_pos[1])
                else:
                    target_pos = step[2].get("ret")
                    # target_pos = step.get("target_pos")
        if target_pos is not None:
            draw_circle(img, target_pos)
        images.append(img)

    # images = [Image.open(fn) for fn in file_names]
    # images = [draw_circle(img, 20, 40) for img in images]

    writeGif(output, images, duration=duration)


def main():
    path = sys.argv[1].decode(sys.getfilesystemencoding())
    steps = MoaLogDisplay(path + "/log.txt").analyse()
    gen_gif(path + "/img_record", steps)


if __name__ == '__main__':
    print "warning! deprecated! use 'report_one.py --gif' instead"
