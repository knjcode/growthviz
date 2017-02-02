#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import json
import math

from datetime import datetime
from PIL import Image

import util


def image_size(photo_file):
    f = Image.open(photo_file)
    with Image.open(photo_file) as im:
        width, height = im.size
        return width, height


def read_config(json_file):
    return json.load(open(json_file))


def write_config(data, json_file):
    f = open(json_file, 'w')
    json.dump(data, f, sort_keys=True, indent=4)
    f.close()


def birthday(user_config):
    return datetime.strptime(user_config['birthday'], '%Y/%m/%d')


def taken_years_old_and_days(taken_date, birthday):
    return (taken_date - birthday).days / 365, (taken_date - birthday).days % 365


def make_config():
    user_config = read_config(util.config_dir() + '/user.json')['user']
    if user_config['sex'] == 'female':
        height_file = util.config_dir() + '/woman_ave_height.json'
    else:
        height_file = util.config_dir() + '/man_ave_height.json'
    height_config = read_config(height_file)['height']
    head_body_config = read_config(
        util.config_dir() + '/head_body_ratio.json')['head_body_ratio']
    image_config = read_config(util.config_dir() + '/image.json')['image']
    config = {'user': user_config, 'height': height_config,
              'head_body_ratio': head_body_config, 'image': image_config}
    return argparse.Namespace(**config)


def main(photo_files):
    config = make_config()
    for photo_file in photo_files:
        _main(photo_file, config)


def _main(photo_file, config):
    if face_bound(photo_file) is None:
        return
    print photo_file
    photo_info = make_photo_info(photo_file, config)
    resized_file, angle = resize_photo(photo_file, photo_info['ratio'])
    if angle is None:
        angle = 0
    resized_face_bounds = resize_points(photo_info['face_bounds'], photo_info[
                                        'ratio'], angle, (photo_info['width_px'], photo_info['height_px']))
    offset_file = offset_photo(
        resized_file, resized_face_bounds, config, photo_info)
    symlink(offset_file, util.taken_date(photo_file))
    print offset_file


def symlink(src_file, taken_date):
    src_full_path = os.path.abspath(src_file)
    dest_full_path = util.body_work_dir() + '/renamed/' + \
        taken_date.strftime('%Y%m%d%H%M%S') + '.jpg'
    # print 'src: %s, dest: %s' % (src_full_path, dest_full_path)
    if os.path.isfile(dest_full_path):
        # print 'remove %s' % dest_full_path
        os.unlink(dest_full_path)
    os.symlink(src_full_path, dest_full_path)


def make_photo_info(photo_file, config):
    # 1200 px / 200 cm  = converted_image_px_per_cm
    # orig_image_face_heigt_px / face_height_cm = orig_image_px_per_cm
    # orig_image_px * ratio = converted_image_px
    # ratio = converted_image_px  / orig_image_px
    # converted_image_px = face_height_cm * converted_image_px_per_cm
    # ratio = face_height_cm * converted_image_px_per_cm / orig_image_px
    bd = birthday(config.user)
    td = util.taken_date(photo_file)
    # print('taken date: %s') % str(td)
    yo, days = taken_years_old_and_days(td, bd)
    # print 'years old: %s' % str(yo)
    height_cm = config.height[
        yo] + (config.height[yo + 1] - config.height[yo]) * days / 365
    # print 'height: %s cm' % str(height_cm)
    face_height_cm = height_cm / config.head_body_ratio[yo]
    # print 'face height: %s cm' % str(face_height_cm)
    face_bounds = face_bound(photo_file)
    x0, x1, y0, y1 = face_bounds
    orig_image_face_height_px = y1 - y0
    converted_image_px_per_cm = float(
        config.image['height_px']) / config.image['max_height_cm']
    ratio = face_height_cm * converted_image_px_per_cm / orig_image_face_height_px
    width_px, height_px = image_size(photo_file)
    return {'width_px': width_px, 'height_px': height_px, 'ratio': ratio,
            'face_bounds': face_bounds, 'height_cm': height_cm,
            'converted_image_px_per_cm': converted_image_px_per_cm}


def resize_photo(photo_file, scale):
    filename = os.path.basename(photo_file)
    resized_file = util.body_work_dir() + '/resized/' + filename
    angle = resize(photo_file, resized_file, scale)
    return resized_file, angle


def resize(file_path, file_dest, resize_rate):
    img = Image.open(file_path)
    size = get_dest_size(img, resize_rate)
    img_resized = img.resize(size, Image.LANCZOS)
    angle = util.orientation(file_path)
    if angle is not None:
        # print ('rotate %s' % str(angle))
        img_resized = img_resized.rotate(angle, expand=True)
    img_resized.save(file_dest, quality=90, optimize=True)
    return angle


def get_dest_size(image, resize_rate):
    (w, h) = image.size
    w_dest = int(w * resize_rate)
    h_dest = int(h * resize_rate)
    return (w_dest, h_dest)


def resize_points(face_bounds, scale, angle, size_px):
    s = lambda p: (p * scale)
    x0, x1, y0, y1 = map(s, face_bounds)
    offset_x, offset_y = 0, 0
    img_width, img_height = size_px
    if angle == 90:
        offset_y = s(img_width)
    elif angle == 270:
        offset_x = s(img_height)
    # print "size_px: %s" % str(size_px)
    r = math.radians(angle)
    rx = lambda x, y: math.cos(-r) * x - math.sin(-r) * y + offset_x
    ry = lambda x, y: math.sin(-r) * x + math.cos(-r) * y + offset_y
    rx0, rx1, ry0, ry1 = map(
        int, (rx(x0, y0), rx(x1, y1), ry(x0, y0), ry(x1, y1)))
    resized_points = bound([{'x': rx0, 'y': ry0}, {'x': rx1, 'y': ry1}])
    # print("scale: %s angle: %s points: %s resized_points: %s" % (str(scale), str(angle), str(face_bounds), str(resized_points)))
    return resized_points


def offset_photo(photo_file, face_bounds, config, photo_info):
    # dirname = os.path.dirname(photo_file)
    filename = os.path.basename(photo_file)
    # root, ext = os.path.splitext(filename)
    # photo_file = dirname + '/' + filename
    offset_file = util.body_work_dir() + '/offset/' + filename
    #  x座標のオフセット: x0(顔の左座標) → 中心 - 顔の幅px/2
    #  y座標のオフセット: y0(顔の上座標) → 高さ - height_px
    x0, x1, y0, y1 = face_bounds
    face_width_px = x1 - x0
    new_x0 = config.image['width_px'] / 2 - face_width_px / 2
    new_y0 = config.image[
        'height_px'] - int(photo_info['height_cm'] * photo_info['converted_image_px_per_cm'])
    # print 'new y0: %s' % str(new_y0)
    diff = (new_x0 - x0, new_y0 - y0)
    im = Image.open(photo_file)
    new_im = Image.new(
        'RGB', (config.image['width_px'], config.image['height_px']), (0, 0, 0))
    new_im.paste(im, diff)
    new_im.save(offset_file, quality=90, optimize=True)
    return offset_file


def face_bound(photo_file):
    log = util.face_detection(photo_file, True)
    if 'faceAnnotations' not in log['responses'][0]:
        return None
    face_vertices = log['responses'][0][
        'faceAnnotations'][0]['fdBoundingPoly']['vertices']
    return bound(face_vertices)


def bound(vertices):
    min_x, min_y, max_x, max_y = 100000, 100000, 0, 0
    for v in vertices:
        x, y = v.get('x', 0), v.get('y', 0)
        if x < min_x:
            min_x = x
        if y < min_y:
            min_y = y
        if x > max_x:
            max_x = x
        if y > max_y:
            max_y = y
    return min_x, max_x, min_y, max_y

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'image_files', nargs='*', help='The image you\'d like to detect face.')
    args = parser.parse_args()
    main(args.image_files)

# ### テキトーに浮かんだアルゴリズム

# * 前提: 顔の位置情報取得済み
# * 入力パラメータ
#   * ディスプレイの幅、高さのpx数
# * 作成済みデータ
#   * cm/px = 年齢-身長マップの最大身長/ディスプレイの高さpx

# 1. 画像から、画像の顔位置px、画像顔サイズpxを取得
# 2. exifから撮影日を取得
# 3. 年齢 = 撮影日-誕生日
# 4. 身長cm = 年齢-身長マップ[年齢]
# 5. 顔サイズcm = 身長cm/年齢-頭身比率マップ[年齢]
# 6. 表示顔サイズpx = 顔サイズcm / cm/px
# 7. 画像縮小率 = 表示顔サイズpx / 画像顔サイズpx
# 8. 顔を、身長pxのところに画像縮小率で縮小(拡大)した画像にして表示
#    x座標のオフセット: x0(顔の左座標) → 中心-顔の幅px/2
#    y座標のオフセット: y0(顔の上座標) → 高さ - height_px
