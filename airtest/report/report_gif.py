# -*- coding: utf-8 -*-
from airtest.report.images2gif import writeGif
from PIL import Image, ImageDraw
import sys
import os
import json


def draw_circle(img, tup_xy, r=20):
    x,y=tup_xy
    draw = ImageDraw.Draw(img)
    draw.ellipse((x - r, y - r, x + r, y + r), fill='blue', outline='blue')
    return img


def gen_gif(imgdir, steps, output="log.gif", size=0.3):
    file_names = sorted((fn for fn in os.listdir(imgdir) if fn.endswith('.jpg')))
    if not file_names:
        print("no jpg image found")
        return

    """
    # count duration of each frame by filename
    # 因为换了gif生成方式，duration目前只能设置一个固定数字，这个duration的计算暂时没用
    duration = []
    for i in range(len(file_names) - 1):
        def get_time(filename):
            return int(os.path.splitext(os.path.basename(filename))[0])
        iterval = get_time(file_names[i + 1]) - get_time(file_names[i])
        duration.append(iterval / 1000.0)
    # last frame duration=1 second
    duration.append(1)
    """

    images = []
    for f in file_names:
        img = Image.open(os.path.join(imgdir, f))
        target_pos = None
        for step in steps:
            if f in step.get("screenshot", ""):
                if 2 in step:
                    # 如果loop_find中含有wnd_pos变量，则为窗口切图后的匹配，图片位置=操作位置-窗口位置:
                    if step[2].has_key("wnd_pos"):
                        wnd_pos = step[2].get("wnd_pos")
                        ret = step[2].get("ret")
                        target_pos = (ret[0] - wnd_pos[0], ret[1] - wnd_pos[1])
                    else:
                        target_pos = step[2].get("ret")
                        # target_pos = step.get("target_pos")
                else:
                    target_pos = step.get("target_pos", None)
        if target_pos is not None and len(target_pos) > 0 and target_pos[0]:
            draw_circle(img, target_pos)
        w, h = img.size
        # 生成的gif图片体积较大，按照命令行给出的gif_size比例来缩小，默认图片大小30%，大约能将文件大小减少到10%左右
        if size and 0.0 < size < 1.0:
            img.thumbnail((w*size, h*size))
        images.append(img)

    #writeGif(output, images, duration=duration)
    # images2gif库有点问题，直接用PIL的库save就能写成gif图了，只是损失一些色彩和精度
    # 注意Pillow版本最好大于3.x，2.x版本的可能不支持直接导出成gif
    first_im = images[0]
    first_im.save(output, save_all=True, append_images=images, duration=1200, loop=0)
