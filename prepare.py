#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import imghdr
import math
import util

from PIL import Image, ImageDraw


def main(photo_files, cache_only, no_cache):
    for photo_file in photo_files:
        _main(photo_file, cache_only, no_cache)


def _main(photo_file, cache_only, no_cache):
    print photo_file
    response = util.face_detection(photo_file, no_cache)

    if cache_only == True:
        return 0

    detected = 0
    num = 1
    try:
        for faces in response['responses'][0]['faceAnnotations']:
            detected = detected + 1
    except KeyError:
        pass
    except IndexError:
        pass

    if detected > 0:
        im = Image.open(photo_file)
        draw = ImageDraw.Draw(im)

        circle_diff = max(im.size) / 1000.0
        if circle_diff < 1:
            circle_diff = 1

        number = 1
        try:
            for face in response['responses'][0]['faceAnnotations']:
                landmarks = face['landmarks']
                for pos in landmarks:
                    x = pos['position']['x']
                    y = pos['position']['y']
                    draw.ellipse((x - circle_diff, y - circle_diff,
                                  x + circle_diff, y + circle_diff), fill='#00ff00')

                    if pos['type'] == 'LEFT_EYE_PUPIL':
                        x = pos['position']['x']
                        y = pos['position']['y']
                        left_eye_pos = (x, y)

                    if pos['type'] == 'RIGHT_EYE_PUPIL':
                        x = pos['position']['x']
                        y = pos['position']['y']
                        right_eye_pos = (x, y)

                # 両目の瞳孔の座標
                print 'LEFT_EYE_PUPIL: (%s,%s)' % left_eye_pos
                print 'RIGHT_EYE_PUPIL: (%s,%s)' % right_eye_pos

                # 瞳孔間距離の計算
                pupil_distance = math.sqrt(
                    (left_eye_pos[0] - right_eye_pos[0])**2 + (left_eye_pos[1] - right_eye_pos[1])**2)
                print 'pupilDistance: %s' % pupil_distance

                print 'rollAngle: %s' % face['rollAngle']
                print 'panAngle: %s' % face['panAngle']
                print 'tiltAngle: %s' % face['tiltAngle']
                print 'detectionConfidence: %s' % face['detectionConfidence']

                box = [(v['x'], v['y'])
                       for v in face['fdBoundingPoly']['vertices']]
                draw.line(box + [box[0]], width=5, fill='#00ff00')
                number = number + 1
        except KeyError:
            pass
        except ValueError:
            pass

        # 画像の拡張子判定
        imagetype = imghdr.what(photo_file)
        # 画像データからmd5ハッシュを求めてファイル名に
        md5sum = util.md5(photo_file)
        # 認識結果を書き込んだ画像を保存

        filename = md5sum + '.' + imagetype
        savefile = util.work_dir() + '/face_detected/' + filename
        im.save(savefile)
        im.close()
        del draw

        im = Image.open(photo_file)
        # 両目が水平になるように画像を回転して保存(1件目に検出された顔が対象)
        radian = math.atan2(
            right_eye_pos[1] - left_eye_pos[1], right_eye_pos[0] - left_eye_pos[0])
        rotate_degree = math.degrees(radian)
        print 'rotate degree: %s' % rotate_degree
        rotatefilename = md5sum + '-rotate.' + imagetype
        rotatesavefile = util.work_dir() + '/face_detected/' + rotatefilename
        im.rotate(rotate_degree).save(rotatesavefile)
        im.close()

        print savefile
        util.print_image(savefile)
        util.print_image(rotatesavefile)

    else:
        print "Face not found: %s" % photo_file

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--cache-only', dest='cache_only', action='store_true',
        help='cache only')
    parser.add_argument(
        '-n', '--no-cache', dest='no_cache', action='store_false',
        help='Do not use cache'
    )
    parser.add_argument(
        'image_files', nargs='+', help='The images you\'d like to detect face.')
    args = parser.parse_args()
    main(args.image_files, args.cache_only, args.no_cache)
