#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import numpy
import unittest
from airtest.aircv import aircv
from airtest.aircv import aircv_focus_ignore_template
from airtest.aircv import aircv_pos_predict
from airtest.aircv import aircv_smart_crop
from airtest.aircv import aircv_tool_func
from airtest.aircv import generate_character_img

THIS_DIR = os.path.dirname(__file__)


class TestAircvToolFunc(unittest.TestCase):

    def test_show_img(self):
        save_path = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img_rgb = aircv.imread(screen_file)
        aircv_tool_func.show_origin_size(img_rgb, test_flag=True)
        aircv_tool_func.show(img_rgb, test_flag=True)

    def test_crop(self):
        save_path = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img_rgb = aircv.imread(screen_file)
        cropped_img = aircv_tool_func.crop(img_rgb, rect=[0, 0, 0.1, 0.1], save_file_path=save_path)
        cropped_img = aircv_tool_func.crop(img_rgb, rect=[0, 0, 100, 100], save_file_path=save_path)
        self.assertIsInstance(cropped_img, numpy.ndarray)
        self.assertIs(os.path.exists(save_path), True)
        os.remove(save_path)

    def test_crop_by_margin(self):
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img_rgb = aircv.imread(screen_file)
        cropped_img = aircv_tool_func.crop_by_margin(img_rgb, margin=[0, 0, 100, 100])
        self.assertIsInstance(cropped_img, numpy.ndarray)

    def test_img_2_string(self):
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        string_img = aircv_tool_func.img_2_string(img)
        img = aircv_tool_func.string_2_img(string_img)
        self.assertIsInstance(img, numpy.ndarray)

    def test_img_2_pil(self):
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        pil_img = aircv_tool_func.cv2_2_pil(img)
        img = aircv_tool_func.pil_2_cv2(pil_img)
        self.assertIsInstance(img, numpy.ndarray)

    def test_mark_point(self):
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        img = aircv_tool_func.mark_point(img, [100, 100])
        self.assertIsInstance(img, numpy.ndarray)

    def test_rotate(self):
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        img = aircv_tool_func.rotate(img, angle=90, clockwise=True)
        img = aircv_tool_func.rotate(img, angle=90, clockwise=False)
        img = aircv_tool_func.rotate(img, angle=180, clockwise=True)
        img = aircv_tool_func.rotate(img, angle=180, clockwise=False)
        img = aircv_tool_func.rotate(img, angle=270, clockwise=True)
        img = aircv_tool_func.rotate(img, angle=270, clockwise=False)
        self.assertIsInstance(img, numpy.ndarray)

    def test_crop_image(self):
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        img_cropped, left_up_pos = aircv_tool_func.crop_image(img, rect=None)
        img_cropped, left_up_pos = aircv_tool_func.crop_image(img, rect=[0, 0, 100, 100])
        self.assertIsInstance(img_cropped, numpy.ndarray)

    def test_mask_img(self):
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        img_masked = aircv_tool_func.mask_image(img, None)
        img_masked = aircv_tool_func.mask_image(img, [0, 0, 100, 100])
        self.assertIsInstance(img_masked, numpy.ndarray)

    def test_crop_img_file(self):
        save_path = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        target_img = aircv_tool_func.crop_img_file(screen_file, [0, 0, 100, 100], save_path, save_file=False)
        self.assertIsInstance(target_img, numpy.ndarray)
        target_img = aircv_tool_func.crop_img_file(screen_file, [0, 0, 100, 100], save_path)
        self.assertIs(os.path.exists(save_path), True)
        os.remove(save_path)

    def test_cover_img_file(self):
        save_path = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        aircv.imwrite(save_path, img)
        target_img = aircv_tool_func.cover_img_file(save_path, [0, 0, 100, 100], save_file=False)
        self.assertIsInstance(target_img, numpy.ndarray)
        target_img = aircv_tool_func.cover_img_file(save_path, [0, 0, 100, 100])
        self.assertIs(os.path.exists(save_path), True)
        os.remove(save_path)

    def test_focus_img_file(self):
        save_path = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        aircv.imwrite(save_path, img)
        target_img = aircv_tool_func.focus_img_file(save_path, [0, 0, 100, 100], save_file=False)
        self.assertIsInstance(target_img, numpy.ndarray)
        target_img = aircv_tool_func.focus_img_file(save_path, [0, 0, 100, 100])
        self.assertIs(os.path.exists(save_path), True)
        os.remove(save_path)

    def test_circle_pt_img_file(self):
        save_path = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        aircv.imwrite(save_path, img)
        target_img = aircv_tool_func.circle_pt_img_file(save_path, [100, 100], save_file=False)
        self.assertIsInstance(target_img, numpy.ndarray)
        target_img = aircv_tool_func.circle_pt_img_file(save_path, [100, 100])
        self.assertIs(os.path.exists(save_path), True)
        os.remove(save_path)

    def test_img_editor_settle_img_file(self):
        save_path = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        aircv.imwrite(save_path, img)
        crop_rect = [0, 0, 150, 150]
        steps = [{"operation":"crop"}, 
            {"operation":"ignore", "rect":[0, 0, 10, 10]}
            , {"operation":"focus", "rect":[20, 50, 60, 100]}]
        target_img = aircv_tool_func.img_editor_settle_img_file(save_path, crop_rect, steps, save_path, save_file=False)
        self.assertIsInstance(target_img, numpy.ndarray)
        target_img = aircv_tool_func.img_editor_settle_img_file(save_path, crop_rect, steps, save_path)
        self.assertIs(os.path.exists(save_path), True)
        os.remove(save_path)

    def test_check_and_settle_rect(self):
        save_path = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        crop_rect = [0, 0, 150, 150]
        rect_list = aircv_tool_func.check_and_settle_rect(crop_rect)
        self.assertIsInstance(rect_list, list)
    
    def test_swipe_find_end_pos(self):
        save_path = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img = aircv.imread(screen_file)
        swipe_end_pos = aircv_tool_func.swipe_find_end_pos(img, [500, 500], direction="left")
        swipe_end_pos = aircv_tool_func.swipe_find_end_pos(img, [500, 500], direction="right")
        swipe_end_pos = aircv_tool_func.swipe_find_end_pos(img, [500, 500], direction="up")
        swipe_end_pos = aircv_tool_func.swipe_find_end_pos(img, [500, 500], direction="down")
        self.assertIsInstance(swipe_end_pos, tuple)



class TestAircv(unittest.TestCase):

    def test_cal_strict_confi(self):
        ret = aircv.find_template(None, None)
        self.assertIsNone(ret)
        # 有图片查找
        file_sch_1 = os.path.join(THIS_DIR, "aircv_test_img/template/sch_1_1.png")
        file_sch_2 = os.path.join(THIS_DIR, "aircv_test_img/template/sch_1_2.png")
        file_src= os.path.join(THIS_DIR, "aircv_test_img/template/screen_1.png")
        sch_img_1, sch_img_2 = aircv.imread(file_sch_1), aircv.imread(file_sch_2)
        src_img = aircv.imread(file_src)
        # 不相同的截图，低可信度查找
        ret = aircv.find_template(src_img, sch_img_1, threshold=0.2)
        ret = aircv.cal_strict_confi(src_img, sch_img_1, ret, threshold=0.8)
        self.assertIsNone(ret, dict)
        # 不相同的截图，低可信度查找
        ret = aircv.find_template(src_img, sch_img_2)
        ret = aircv.cal_strict_confi(src_img, sch_img_2, ret, threshold=0.8)
        self.assertIsInstance(ret, dict)
        ret = aircv.cal_strict_confi(src_img, sch_img_2, None)
        self.assertIsNone(ret)


    def test_find_template(self):
        ret = aircv.find_template(None, None)
        self.assertIsNone(ret)
        # 有图片查找
        file_sch_1 = os.path.join(THIS_DIR, "aircv_test_img/template/sch_1_1.png")
        file_sch_2 = os.path.join(THIS_DIR, "aircv_test_img/template/sch_1_2.png")
        file_src= os.path.join(THIS_DIR, "aircv_test_img/template/screen_1.png")
        sch_img_1, sch_img_2 = aircv.imread(file_sch_1), aircv.imread(file_sch_2)
        src_img = aircv.imread(file_src)
        # 不相同的截图，低可信度查找
        ret = aircv.find_template(src_img, sch_img_1, threshold=0.2)
        self.assertIsInstance(ret, dict)
        ret = aircv.find_template(src_img, sch_img_1, threshold=0.2, strict=True)
        self.assertIsInstance(ret, dict)
        # 不相同的截图，高可信度查找
        ret = aircv.find_template(src_img, sch_img_1, threshold=0.9, strict=True, bgremove=True)
        self.assertIsNone(ret)
        # 可信度截图，rgb三通道查找
        ret = aircv.find_template(src_img, sch_img_2, strict=True, rgb=True)
        self.assertIsInstance(ret, dict)
        # 可信度截图，匹配后检查三通道情况
        ret = aircv.find_template(src_img, sch_img_2, strict=True, check_color=True)
        self.assertIsInstance(ret, dict)

    def test_find_template_after_resize(self):
        file_sch = os.path.join(THIS_DIR, "aircv_test_img/template/sch_2.png")
        file_src= os.path.join(THIS_DIR, "aircv_test_img/template/screen_2.jpg")
        sch_img, src_img = aircv.imread(file_sch), aircv.imread(file_src)
        design_reso = [960, 640]
        sch_reso, src_reso = [2200, 1600], [2600, 1800]
        ret = aircv.find_template_after_resize(src_img, sch_img, sch_resolution=sch_reso, src_resolution=src_reso, design_resolution=[], threshold=0.6, strict=True)
        self.assertIsInstance(ret, dict)
        ret = aircv.find_template_after_resize(src_img, sch_img, sch_resolution=sch_reso, src_resolution=src_reso, design_resolution=design_reso, threshold=0.6, strict=True)
        self.assertIsInstance(ret, dict)
        # find_all，返回值为list
        ret = aircv.find_template_after_resize(src_img, sch_img, sch_resolution=sch_reso, src_resolution=src_reso, design_resolution=design_reso, threshold=0.6, strict=True, find_all=True)
        self.assertIsInstance(ret, list)

    def test_find_template_in_pre(self):
        file_sch = os.path.join(THIS_DIR, "aircv_test_img/template/sch_1280_800.png")
        file_src= os.path.join(THIS_DIR, "aircv_test_img/template/src_1280_800.png")
        sch_img, src_img = aircv.imread(file_sch), aircv.imread(file_src)
        design_reso = [960, 640]
        sch_reso, src_reso = [1280, 800], [1280, 800]
        ret = aircv.find_template_in_pre(src_img, sch_img, clk_x=-0.42, clk_y=-0.4, sch_resolution=sch_reso, src_resolution=src_reso, design_resolution=design_reso, threshold=0.6)
        self.assertIsInstance(ret, dict)
        ret = aircv.find_template_in_pre(src_img, sch_img, clk_x=-0.6, clk_y=-0.6, sch_resolution=sch_reso, src_resolution=src_reso, design_resolution=design_reso, threshold=0.6)
        self.assertIsNone(ret)
        ret = aircv.find_template_in_pre(src_img, sch_img, clk_x=-0.42, clk_y=-0.4, sch_resolution=sch_reso, src_resolution=src_reso, design_resolution=[], threshold=0.6)
        self.assertIsInstance(ret, dict)

    def test_find_sift(self):
        file_sch = os.path.join(THIS_DIR, "aircv_test_img/sift/sch_1280_800.png")
        file_src= os.path.join(THIS_DIR, "aircv_test_img/sift/src_1280_800.png")
        sch_img, src_img = aircv.imread(file_sch), aircv.imread(file_src)
        ret = aircv.find_sift(src_img, sch_img)
        self.assertIsInstance(ret, dict)
        ret = aircv.find_sift(src_img, sch_img, strict=True)
        self.assertIsInstance(ret, dict)
        # 两点good点
        file_sch = os.path.join(THIS_DIR, "aircv_test_img/sift/sch_1_1.png")
        file_src= os.path.join(THIS_DIR, "aircv_test_img/sift/screen_1.jpg")
        sch_img, src_img = aircv.imread(file_sch), aircv.imread(file_src)
        ret = aircv.find_sift(src_img, sch_img)
        self.assertIsInstance(ret, dict)
        # 两点good点(strict=False / True)
        file_sch = os.path.join(THIS_DIR, "aircv_test_img/sift/sch_2.png")
        file_src= os.path.join(THIS_DIR, "aircv_test_img/sift/screen_2.png")
        sch_img, src_img = aircv.imread(file_sch), aircv.imread(file_src)
        ret = aircv.find_sift(src_img, sch_img)
        self.assertIsInstance(ret, dict)
        ret = aircv.find_sift(src_img, sch_img, strict=True)
        self.assertIsInstance(ret, dict)

    def test_find_sift_by_pre(self):
        file_sch = os.path.join(THIS_DIR, "aircv_test_img/sift/sch_1280_800.png")
        file_src= os.path.join(THIS_DIR, "aircv_test_img/sift/src_1280_800.png")
        sch_img, src_img = aircv.imread(file_sch), aircv.imread(file_src)
        src_reso = [1280, 800]
        ret = aircv.find_sift_by_pre(src_img, sch_img, src_reso, -0.42, -0.4)
        self.assertIsInstance(ret, dict)
        ret = aircv.find_sift_by_pre(src_img, sch_img, src_reso, -0.6, -0.6)
        self.assertIsNone(ret)
        ret = aircv.find_sift_by_pre(src_img, sch_img, src_reso, -0.3, -0.3, strict=True)
        self.assertIsInstance(ret, dict)

    def test_template_focus_ignore(self):
        file_sch = os.path.join(THIS_DIR, "aircv_test_img\\template_ignore_focus\\sch_1.png")
        file_src = os.path.join(THIS_DIR, "aircv_test_img\\template_ignore_focus\\screen_1.jpg")
        img, tmpl = aircv.imread(file_src), aircv.imread(file_sch)
        ignore = [[38, 28, 353, 120]]
        focus = [[160, 165, 250, 210]]
        h, w = img.shape[:2]
        sch_reso, src_reso = [1920, 1080], [w, h]
        ret = aircv_focus_ignore_template.template_focus_ignore_after_resize(img, tmpl, threshold=0.8, sch_resolution=sch_reso, src_resolution=src_reso, ignore=ignore, focus=focus, resize_method=None)
        self.assertIsInstance(ret, dict)

        file_sch = os.path.join(THIS_DIR,"aircv_test_img\\template_ignore_focus\\g18_sch_emo.png")
        file_src = os.path.join(THIS_DIR,"aircv_test_img\\template_ignore_focus\\g18_screen_emo.jpg")
        img, tmpl = aircv.imread(file_src), aircv.imread(file_sch)
        h, w = img.shape[:2]
        sch_reso, src_reso = [1920, 1080], [w, h]
        ignore, focus = None, [[40, 32, 66, 56], [7, 144, 86, 164]]
        ret = aircv_focus_ignore_template.template_focus_ignore_after_resize(img, tmpl, threshold=0.8, sch_resolution=sch_reso, src_resolution=src_reso, ignore=ignore, focus=focus, resize_method=None)
        self.assertIsInstance(ret, dict)

        file_sch = os.path.join(THIS_DIR, "aircv_test_img/template/sch_2.png")
        file_src= os.path.join(THIS_DIR, "aircv_test_img/template/screen_2.jpg")
        sch_img, src_img = aircv.imread(file_sch), aircv.imread(file_src)
        design_reso = [960, 640]
        sch_reso, src_reso = [2200, 1600], [2600, 1800]
        ignore, focus = None, [[10, 20, 50, 50]]
        ret = aircv_focus_ignore_template.template_focus_ignore_after_resize(src_img, sch_img, sch_resolution=sch_reso, src_resolution=src_reso, design_resolution=[], resize_method=None, ignore=ignore, focus=focus)
        self.assertIsInstance(ret, dict)

    def test_aircv_pos_predict(self):
        _pResolution, _dResolution, _rResolution = [1920, 1080], [960, 640], [1920, 1080]
        predict_instance = aircv_pos_predict.Prediction(_pResolution, _dResolution, _rResolution)
        delta_pos = predict_instance.calPosInPercent([50, 50], [1920,1080])
        self.assertIsInstance(delta_pos, tuple)
        delta_pos = predict_instance.pos_prediction(100, 200)
        self.assertIsInstance(delta_pos, tuple)

        w_h = aircv_pos_predict.g18_resize_method(100, 100, [2560, 1440], [960, 640])
        self.assertIsInstance(delta_pos, tuple)
        w_h = aircv_pos_predict.g18_resize_method(100, 100, [1920, 1080], [960, 640])
        self.assertIsInstance(delta_pos, tuple)
        w_h = aircv_pos_predict.no_resize(100, 100, [1920, 1080], [960, 640])
        self.assertIsInstance(delta_pos, tuple)

    def test_aircv_smart_crop(self):
        screen_file = os.path.join(THIS_DIR, "aircv_test_img/smart_crop/1800_1080.png")
        img_rgb = aircv.imread(screen_file)
        touch_point = [63, 192]
        result_crop_img = aircv_smart_crop.smart_target_crop(img_rgb, touch_point, detail=True)
        self.assertIsInstance(result_crop_img, numpy.ndarray)

        touch_point = [987, 216]
        result_crop_img = aircv_smart_crop.smart_target_crop(img_rgb, touch_point, detail=False)
        self.assertIsInstance(result_crop_img, numpy.ndarray)

    def test_generate_character_img(self):
        save_file = os.path.join(THIS_DIR,"aircv_test_img\\test.png")
        character_img = generate_character_img.gen_text(u"次数", font=u"微软雅黑", size=28, inverse=True)
        character_img = generate_character_img.gen_text(u"次数", font=u"微软雅黑", size=28, inverse=False)
        character_img.save(save_file)
        character_img = aircv.imread(save_file)
        self.assertIsInstance(character_img, numpy.ndarray)
        self.assertIs(os.path.exists(save_file), True)
        os.remove(save_file)

        character_img = generate_character_img.gen_text(u"次数", font=u"宋体", size=28, inverse=True)
        character_img = generate_character_img.gen_text(u"次数", font=u"宋体", size=28, inverse=False)
        character_img.save(save_file)
        character_img = aircv.imread(save_file)
        self.assertIsInstance(character_img, numpy.ndarray)
        character_img = aircv.imwrite(save_file, character_img)
        self.assertIs(os.path.exists(save_file), True)
        os.remove(save_file)

if __name__ == '__main__':
    unittest.main()
