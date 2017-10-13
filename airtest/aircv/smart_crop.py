# coding=utf-8

'''
    本文件用于智能monkey，自动检测画面中可点击的控件：
    控件分类：
        1、文字按键类型（商城-背包-聊天框）
        2、完整轮廓（比如按钮-图标-人物头像）
        3、特殊角点（箭头）
    方法1：
        integral_preprocess(gray_img):
            Laplacian → 二值化 → 膨胀-膨胀 → 提取轮廓 → 轮廓筛选
            适用于UI界面的主要控件提取，细节提取较为不足。
    方法2：
        detail_detect(img):
            sobel → 二值化 → 膨胀-腐蚀-膨胀 → 提取轮廓 → 轮廓筛选
            默认使用Sobel预处理：适用于各种界面，细节完备，但是提取点太多。
'''

import cv2
import time

# 默认截图长宽
MIN_WIDTH = 20
MAX_WIDTH = 100
# 选择边缘检测方法：0: Laplacian  1：Sobel_x  2：Sobel_y  3: Sobel_x_y  4:Canny
# Laplacian整体性好，Sobel细节好， Canny效果较差
CONTOUR_METHOD = 1
# 膨胀、腐蚀、膨胀的算子
KERNEL = [(5, 5), (6, 6), (5, 5)]
# 膨胀、腐蚀算子
DILATE_KERNEL_1 = KERNEL[0]  # (24, 6)    (10, 8)
EROSION_KERNEL = KERNEL[1]   # (30, 9)   (20, 8)
DILATE_KERNEL_2 = KERNEL[2]   # (30, 9)   (20, 8)

# MIN_AREA = 600 # 筛选掉选中区域面积小的
MIN_AREA = 400   # 筛选掉选中区域面积小的
# 显示结果，存储处理过程图像
STORE_CACHE = False


def integral_preprocess(gray_img):
    '''
        预处理方法1： Laplacian → 二值化 → 膨胀-膨胀 → 提取
    '''
    contour_result = cv2.Laplacian(gray_img, cv2.CV_8U)
    ret, binary = cv2.threshold(
        contour_result, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)
    dilate_element1 = cv2.getStructuringElement(
        cv2.MORPH_RECT, DILATE_KERNEL_1)
    dilation = cv2.dilate(binary, dilate_element1, iterations=1)
    dilation2 = cv2.dilate(dilation, dilate_element1, iterations=1)

    return dilation2


def preprocess(gray_img):
    '''
        预处理方法2： Sobel(默认) → 二值化 → 膨胀-膨胀 → 提取
    '''
    # 1、求出边缘提取结果：
    if CONTOUR_METHOD == 0:
        # '''使用laplacian边缘检测算法，细节易丢失'''
        contour_result = cv2.Laplacian(gray_img, cv2.CV_8U)
    elif CONTOUR_METHOD == 1:
        # '''使用sobel算子进行边缘检测（默认使用x方向）'''
        contour_result = cv2.Sobel(gray_img, cv2.CV_8U, 1, 0, ksize=3)
    elif CONTOUR_METHOD == 2:
        # '''使用sobel算子进行边缘检测（默认使用y方向）'''
        contour_result = cv2.Sobel(gray_img, cv2.CV_8U, 0, 1, ksize=3)
    elif CONTOUR_METHOD == 3:
        # '''使用sobel算子进行边缘检测（默认使用x_y方向）'''
        contour_result = cv2.Sobel(gray_img, cv2.CV_8U, 1, 1, ksize=3)
    elif CONTOUR_METHOD == 4:
        # '''使用canny边缘检测算法，实现初始的边缘检测.'''
        threshold_one, threshold_two = 0, 255          # threshold_one, threshold_two = 100, 200
        blur = cv2.GaussianBlur(gray_img, (5, 5), 0)   # 高斯模糊，减少噪点
        contour_result = cv2.Canny(blur, threshold_one, threshold_two)      # 检测边缘
    # 2. 二值化
    ret, binary = cv2.threshold(
        contour_result, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)
    # 3. 膨胀和腐蚀操作的核函数
    dilate_element1 = cv2.getStructuringElement(
        cv2.MORPH_RECT, DILATE_KERNEL_1)   # 膨胀1的核函数
    erosion_element = cv2.getStructuringElement(
        cv2.MORPH_RECT, EROSION_KERNEL)    # 腐蚀的核函数
    dilate_element2 = cv2.getStructuringElement(
        cv2.MORPH_RECT, DILATE_KERNEL_2)   # 膨胀2的核函数
    # 4. 膨胀一次，让轮廓突出
    dilation = cv2.dilate(binary, dilate_element1, iterations=1)
    # 5. 腐蚀一次，去掉线状物细节。注意这里去掉的是竖直的线（因为sobel算子使用x向的边缘提取）
    erosion = cv2.erode(dilation, erosion_element, iterations=1)
    # 6. 再次膨胀，让轮廓明显一些
    dilation2 = cv2.dilate(erosion, dilate_element2, iterations=3)  # 膨胀2的核函数

    # 存储中间图片
    if STORE_CACHE:
        cv2.imwrite("binary.png", binary)
        cv2.imwrite("dilation.png", dilation)
        cv2.imwrite("erosion.png", erosion)
        cv2.imwrite("dilation2.png", dilation2)

    return dilation2


def smart_target_crop(img_rgb=None, point=None, detail=False, max_width=MAX_WIDTH, min_width=MIN_WIDTH):
    '''
        完整性提取（使用Laplacian预处理），适用于web-app、UI界面等。
    '''
    if not img_rgb.any():
        raise Exception("image to crop is NULL !")
    if not point:
        raise Exception("no target point to smart_crop the image !")
    # 1.  转化成灰度图
    gray_img = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    # 2. 形态学变换的预处理，得到可以查找矩形的图片
    if detail:
        dilation = preprocess(gray_img)
    else:
        dilation = integral_preprocess(gray_img)
    # 3. 查找和筛选轮廓
    region = get_proper_contour(dilation)

    target_list = []
    # 根据边缘提取结果，找到point所在的矩形备选区域target_list
    for rect_xywh in region:
        dis = [point[0] - rect_xywh[0], point[1] - rect_xywh[1]]
        if dis[0] > 0 and dis[0] < rect_xywh[2] and dis[1] > 0 and dis[1] < rect_xywh[3]:
            target_list.append(rect_xywh)

    # 尝试从备选区域列表target_list中，找出目标区域（面积最小的那个）
    final_xywh = None
    if target_list:
        target = None
        while len(target_list) >= 1:
            target = target_list[0]
            target_list.remove(target)
            is_the_one = True
            for rect in target_list:
                if target[-1] > rect[-1]:
                    is_the_one = False
            if is_the_one:
                break
        if target:
            # 初步筛选得到的target区域宽、高均大于最低图像宽度时，才认定为有效结果：
            if target[2] > min_width and target[3] > min_width:
                final_xywh = target[:-1]

    # 如果的找到了合适包含区域，那么就结合最大截图区域进行修形
    w = max_width
    if final_xywh:
        # 只要目标区域final_xywh的宽/高大于100时，才需要修形：(区域边缘距离点击位置不要超过50)
        if final_xywh[2] > w or final_xywh[3] > w:
            left_margin, top_margin = point[0] - final_xywh[0], point[1] - final_xywh[1]
            right_margin, bot_margin = final_xywh[2] - left_margin, final_xywh[3] - top_margin
            left_margin, top_margin = min(left_margin, int(w / 2)), min(top_margin, int(w / 2))
            right_margin, bot_margin = min(right_margin, int(w / 2)), min(bot_margin, int(w / 2))
            final_xywh = [point[0] - left_margin, point[1] - top_margin, left_margin + right_margin, top_margin + bot_margin]
    else:
        # 如果发现没有合适的包含区域，直接按照100*100进行截图：
        final_xywh = [int(point[0] - w / 2), int(point[1] - w / 2), w, w]

    target_img = crop_by_xywh(img_rgb, final_xywh)
    return target_img


def crop_by_xywh(img, rect=(0, 0, 0, 0)):
    '''
        Crop image, rect = [x_min, y_min, w ,h]
    '''
    if img is None:
        raise NoneImageError("Image to crop is None !")
    else:
        height, width = img.shape[:2]
        # 获取在图像中的实际有效区域：
        x_min, y_min, x_max, y_max = rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]
        x_min, y_min = max(0, x_min), max(0, y_min)
        x_min, y_min = min(width - 1, x_min), min(height - 1, y_min)
        x_max, y_max = max(0, x_max), max(0, y_max)
        x_max, y_max = min(width - 1, x_max), min(height - 1, y_max)

        # 返回剪切的有效图像：(必须保证截图时的变量为整型)
        img_crop = img[int(y_min):int(y_max), int(x_min):int(x_max)]
        return img_crop


def get_proper_contour(img):
    '''
        轮廓提取：
            获取轮廓后：1、去除面积过小的轮廓； 2、去除比例过于细长的轮廓.
    '''
    region = []
    # 1. 查找轮廓 OpenCV 3.0 使用方法：
    contours, hierarchy = cv2.findContours(
        img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]
    # 2. 轮廓筛选：
    for i in range(len(contours)):
        cnt = contours[i]
        # 计算该轮廓的面积
        area = cv2.contourArea(cnt)
        # 面积小的都筛选掉
        if(area < MIN_AREA):
            continue
        # 截图时，轮廓都是水平矩形：
        x, y, w, h = cv2.boundingRect(cnt)
        # 计算欧式距离，作为实际矩形的宽和高：
        height, width = max(w, h), min(w, h)
        # 筛选那些太细长的矩形
        if(height > width * 3 and width < 20):
            continue
        elif(height > width * 10):
            continue
        # 把计算得到的有效面积也加入进来
        region.append([x, y, w, h, area])

    return region
