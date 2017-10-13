#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy as np
# import matplotlib.cm
# import matplotlib.pyplot as plt
from .error import TemplateInputError

from PIL import Image


def generate_result(middle_point, pypts, confi):
    '''
    Format the result: 定义图像识别结果格式
    '''
    ret = dict(result=middle_point,
             rectangle=pypts,
             confidence=confi)
    return ret


def check_image_param_input(im_source, im_search, check_size_flag=False):
    """检查图像识别的输入."""
    # 图像格式, 确保输入图像为指定的矩阵格式:
    if not isinstance(im_source, np.ndarray) or not isinstance(im_search, np.ndarray):
        raise InvalidImageInputError("Error: invalid image input, must be <type 'numpy.ndarray'>")

    if check_size_flag:
        # 图像大小, 检查截图宽、高是否大于了截屏的宽、高:
        h_search, w_search = im_search.shape[:2]
        h_source, w_source = im_source.shape[:2]
        if h_search > h_source or w_search > w_source:
            raise TemplateInputError("error: in template match, found im_search bigger than im_source.")


def img_mat_rgb_2_gray(img_mat):
    '''
        turn img_mat into gray_scale, so that template match can figure the img data.
        "print(type(im_search[0][0])")  can check the pixel type.
    '''
    if len(img_mat) == 0:
        raise NoneImageError("Input Error: image mat pass into img_mat_rgb_2_gray is null !!")
    if isinstance(img_mat[0][0], np.ndarray):
        return cv2.cvtColor(img_mat, cv2.COLOR_BGR2GRAY)
    if isinstance(img_mat[0][0], np.uint8):
        return img_mat


# def show_result(result, im_source, im_search):
#     '''
#     Function:
#         Show the result in a matplotlib image. (with the im_search and target area)

#     Args:
#         im_source: the bigger image to be searched in.(源图像)  im_search: image to search. (搜索图像)
#         result: result foundwith template or SIFT method.
#     '''
#     # 注意：windows环境下进行打包时存在库的编码问题,此函数主要在test脚本中使用，必要时可注释.
#     if result is None:
#         print("None result, check the input images !")
#         return None
#     confidence = result['confidence']
#     # middle = result['result']
#     rect = result['rectangle']
#     if rect == ():
#         print("No Rectangle in result, cannot crop the target area !!")
#         return None
#     # 若为彩色输入时，将OpenCV的BGR格式转换成RGB格式：
#     if isinstance(im_search[0][0], np.ndarray) and isinstance(im_source[0][0], np.ndarray):
#         im_search = cv2.cvtColor(im_search, cv2.COLOR_BGR2RGB)
#         im_source = cv2.cvtColor(im_source, cv2.COLOR_BGR2RGB)

#     crop_img = im_source[rect[0][1]:rect[2][1], rect[0][0]:rect[2][0]]
#     h_rect, w_rect = crop_img.shape[:2]
#     confidence = '%.3f' % confidence
#     fig_title = "\n\nconfidence=" + str(confidence)
#     # 指定输出窗口的大小：fig = plt.figure(fig_title, (12, 7))
#     fig = plt.figure()
#     fig.suptitle(fig_title, fontsize=24, fontweight='bold')
#     fig.add_subplot(121)
#     plt.title("Search Img:\n")
#     plt.imshow(im_search, cmap=matplotlib.cm.Greys_r)
#     fig.add_subplot(122)
#     plt.title("Target in Source Img:\n")
#     plt.imshow(crop_img, cmap=matplotlib.cm.Greys_r)
#     # 保存图片到本地的方法：fig.savefig('E:/result_figure.png', dpi=500)
#     plt.show(fig)
#     plt.close()


def img_2_string(img):
    _, png = cv2.imencode('.png', img)
    return png.tostring()


def string_2_img(pngstr):
    nparr = np.fromstring(pngstr, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def pil_2_cv2(pil_image):
    open_cv_image = np.array(pil_image)
    # Convert RGB to BGR (method-1):
    try:
        open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
    except:
        # 如果图片转换失败，直接return None
        return None
    # Convert RGB to BGR (method-2):
    # b, g, r = cv2.split(open_cv_image)
    # open_cv_image = cv2.merge([r, g, b])
    return open_cv_image


def cv2_2_pil(cv2_image):
    cv2_im = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_im = Image.fromarray(cv2_im)
    return pil_im
