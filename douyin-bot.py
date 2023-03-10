# -*- coding: utf-8 -*-
import sys
import random
import time
from uuid import uuid1
import base64

import numpy as np
from PIL import Image
import argparse
import cv2

if sys.version_info.major != 3:
    print('Please run under Python3')
    exit(1)
try:
    from common import debug, config, screenshot, UnicodeStreamFilter
    from common.auto_adb import auto_adb
    from common import apiutil
    from common.compression import resize_image
except Exception as ex:
    print(ex)
    print('请将脚本放在项目根目录中运行')
    print('请检查项目根目录中的 common 文件夹是否存在')
    exit(1)

VERSION = "0.0.1"

# 申请地址 http://ai.qq.com
AppID = 'xxxxx'
AppKey = 'xxxxx'

DEBUG_SWITCH = True
FACE_PATH = 'face/'

adb = auto_adb()
adb.test_device()
config = config.open_accordant_config()

# 审美标准
BEAUTY_THRESHOLD = 80

# 最小年龄
GIRL_MIN_AGE = 14


def yes_or_no():
    """
    检查是否已经为启动程序做好了准备
    """
    while True:
        yes_or_no = str(input('请确保手机打开了 ADB 并连接了电脑，'
                              '然后打开手机软件，确定开始？[y/n]:'))
        if yes_or_no == 'y':
            break
        elif yes_or_no == 'n':
            print('谢谢使用')
            exit(0)
        else:
            print('请重新输入')


def _random_bias(num):
    """
    random bias
    :param num:
    :return:
    """
    return random.randint(-num, num)


def next_page():
    """
    翻到下一页
    :return:
    """
    cmd = 'shell input swipe {x1} {y1} {x2} {y2} {duration}'.format(
        x1=config['center_point']['x'],
        y1=config['center_point']['y'] + config['center_point']['ry'],
        x2=config['center_point']['x'],
        y2=config['center_point']['y'],
        duration=200
    )
    adb.run(cmd)
    time.sleep(1.5)


def follow_user():
    """
    关注用户
    :return:
    """
    # 需要判断是否已经关注过了 不然会瞎几把跳转页面

    cmd = 'shell input tap {x} {y}'.format(
        x=config['follow_bottom']['x'] + _random_bias(10),
        y=config['follow_bottom']['y'] + _random_bias(10)
    )
    adb.run(cmd)
    print('关注成功')
    time.sleep(0.5)


def thumbs_up():
    """
    点赞
    :return:
    """
    # 需要判断是否已经点过赞了 不然会取消点赞

    cmd = 'shell input tap {x} {y}'.format(
        x=config['star_bottom']['x'] + _random_bias(10),
        y=config['star_bottom']['y'] + _random_bias(10)
    )
    adb.run(cmd)
    print('点赞成功')
    time.sleep(0.5)


def tap(x, y):
    cmd = 'shell input tap {x} {y}'.format(
        x=x + _random_bias(10),
        y=y + _random_bias(10)
    )
    adb.run(cmd)


def auto_reply():
    msg = "垆边人似月，皓腕凝霜雪。就在刚刚，我的心动了一下，小姐姐你好可爱呀！！！-----自动化工具请勿回复"

    # 点击右侧评论按钮
    tap(config['comment_bottom']['x'], config['comment_bottom']['y'])
    time.sleep(1)
    # 弹出评论列表后点击输入评论框
    tap(config['comment_text']['x'], config['comment_text']['y'])
    time.sleep(1)
    # 输入上面msg内容 ，注意要使用ADB keyboard  否则不能自动输入，参考： https://www.jianshu.com/p/2267adf15595
    # cmd = 'shell am broadcast -a ADB_INPUT_TEXT --es msg {text}'.format(text=msg);
    # 将msg转换为base64编码
    cmd = "shell am broadcast -a ADB_INPUT_B64 --es msg {text}".format(
        text=str(base64.b64encode(msg.encode("utf-8")), "utf-8"))
    adb.run(cmd)
    time.sleep(1)
    # 点击发送按钮
    tap(config['comment_send']['x'], config['comment_send']['y'])
    time.sleep(1)

    # 触发返回按钮, keyevent 4 对应安卓系统的返回键，参考KEY 对应按钮操作：  https://www.cnblogs.com/chengchengla1990/p/4515108.html
    # cmd = 'shell input keyevent 4'
    tap(config['close']['x'], config['close']['y'])
    print('自动回复成功')
    # adb.run(cmd)


def parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("-r", "--reply", action='store_true',
                    help="auto reply")
    args = vars(ap.parse_args())
    return args


# 识别是否有关注或点赞按钮
def is_like_follow(img):
    # 加载需要检测的物体的照片
    object_img = cv2.imread('./autojump.png')

    # 加载待匹配的照片
    match_img = cv2.imread(img)

    # 转换为灰度图像
    gray1 = cv2.cvtColor(object_img, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(match_img, cv2.COLOR_BGR2GRAY)

    # 在第二张图像中搜索第一张图像
    result = cv2.matchTemplate(gray2, gray1, cv2.TM_CCOEFF_NORMED)

    # 设置匹配的阈值
    threshold = 0.4

    # 获取匹配结果中符合阈值条件的位置
    locations = []
    yloc, xloc = np.where(result >= threshold)
    for (x, y) in zip(xloc, yloc):
        locations.append((x, y, object_img.shape[1], match_img.shape[0]))

    # 在第二张图像中标记匹配的位置
    for (x, y, w, h) in locations:
        cv2.rectangle(match_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # 判断是否有匹配的结果
    if len(locations) > 0:
        return True

    return False


def main():
    """
    main
    :return:
    """
    global forMat
    print('程序版本号：{}'.format(VERSION))
    print('激活窗口并按 CONTROL + C 组合键退出')
    debug.dump_device_info()
    screenshot.check_screenshot()

    cmd_args = parser()

    while True:
        next_page()

        time.sleep(1)
        screenshot.pull_screenshot()

        resize_image('autojump.png', 'optimized.png', 1024 * 1024)

        with open('optimized.png', 'rb') as bin_data:
            image_data = bin_data.read()

        ai_obj = apiutil.AiPlat(AppID, AppKey)
        rsp = ai_obj.face_detectface(image_data)

        major_total = 0
        minor_total = 0

        if rsp['ret'] == 0:
            beauty = 0

            for s in rsp["FaceInfos"]:
                face = s["FaceAttributesInfo"]

                print(face)

                msg_log = '[INFO] gender: {gender} age: {age} expression: {expression} beauty: {beauty}'.format(
                    gender=face['Gender'],
                    age=face['Age'],
                    expression=face['Expression'],
                    beauty=face['Beauty'],
                )
                print(msg_log)
                face_area = (s['X'], s['Y'], s['X'] + s['Width'], s['Y'] + s['Height'])
                img = Image.open("optimized.png")
                cropped_img = img.crop(face_area).convert('RGB')
                cropped_img.save(FACE_PATH + uuid1().__str__() + '.png')
                # 性别判断
                if face['Beauty'] > beauty and face['Gender'] < 50:
                    beauty = face['Beauty']

                if face['Age'] > GIRL_MIN_AGE:
                    major_total += 1
                else:
                    minor_total += 1

            # 是个美人儿~关注点赞走一波
            if beauty > BEAUTY_THRESHOLD and major_total > minor_total:
                print('发现漂亮妹子！！！')

                # 判断是否有关注按钮
                if is_like_follow('follow.png'):
                    follow_user()
                else:
                    print('已经关注过了')

                # 判断是否有点赞按钮
                if is_like_follow('like.png'):
                    thumbs_up()
                else:
                    print('已经点赞过了')

                # 为了处理发现直播间的情况，这里需要判断是否有评论按钮
                if cmd_args['reply'] and is_like_follow('reply.png'):
                    auto_reply()

                continue
        else:
            print(rsp)
            continue


if __name__ == '__main__':
    try:
        # yes_or_no()
        main()
    except KeyboardInterrupt:
        adb.run('kill-server')
        print('谢谢使用')
        exit(0)
