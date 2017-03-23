#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import math
import numpy as np
import cv2
import imghdr

import util


def main(photo_file_dir):
    rotate_list = []
    box_list = []
    left_eye_list = []
    right_eye_list = []
    resize_scales = []
    target_files = []
    file_list = os.listdir(photo_file_dir)

    pd_size = 100

    for filename in file_list:
        if util.is_image_file(filename):
            photo_file = photo_file_dir + '/' + filename
            print photo_file
            response = util.face_detection(photo_file, True)

            detected = 0
            try:
                for faces in response['responses'][0]['faceAnnotations']:
                    detected = detected + 1
            except KeyError:
                continue
            except IndexError:
                continue

            if detected > 0:
                face = response['responses'][0]['faceAnnotations'][0]
                print 'rollAngle: %s' % face['rollAngle']
                print 'panAngle: %s' % face['panAngle']
                # if abs(face['panAngle']) > 30:
                #     continue
                print 'tiltAngle: %s' % face['tiltAngle']
                # if abs(face['tiltAngle']) > 30:
                #     continue
                print 'detectionConfidence: %s' % face['detectionConfidence']
                if face['detectionConfidence'] < 0.6:
                    continue

                landmarks = face['landmarks']
                for pos in landmarks:
                    x = pos['position']['x']
                    y = pos['position']['y']

                    if pos['type'] == 'LEFT_EYE_PUPIL':
                        left_eye_pos = (x, y)
                        left_eye_list.append(left_eye_pos)

                    if pos['type'] == 'RIGHT_EYE_PUPIL':
                        right_eye_pos = (x, y)
                        right_eye_list.append(right_eye_pos)

                # 瞳孔間距離の計算
                pupil_distance = math.sqrt(
                    (right_eye_pos[1] - left_eye_pos[1])**2 + (right_eye_pos[0] - left_eye_pos[0])**2)
                print 'pupilDistance: %s' % pupil_distance
                resize_scales.append(pd_size / pupil_distance)

                # 顔の領域を計算
                fdBoundingPoly = [(v['x'], v['y'])
                                  for v in face['fdBoundingPoly']['vertices']]
                expansion_rate = 1
                if util.use_google_face_detection():
                    expansion_rate = 1
                # 顔の領域を拡大 cloudvisionの場合はpupil_distance分拡大、dlibの場合もpupil_distance分拡大
                pd_int = int(round(pupil_distance * expansion_rate))
                im = cv2.imread(photo_file)
                (im_x, im_y) = im.shape[:2]
                startx = max(0, fdBoundingPoly[0][0] - pd_int)
                starty = max(0, fdBoundingPoly[0][1] - pd_int)
                end_x = min(im_x, fdBoundingPoly[2][0] + pd_int)
                end_y = min(im_y, fdBoundingPoly[2][1] + pd_int)
                box_list.append((startx, starty, end_x, end_y))

                # 右目を支点とした左目の位置の傾きを計算
                radian = math.atan2(
                    left_eye_pos[1] - right_eye_pos[1], right_eye_pos[0] - left_eye_pos[0])
                print 'rotate degree: %s' % math.degrees(radian)
                rotate_list.append(radian)

                target_files.append(photo_file)

            else:
                print "Face not found: %s" % photo_file

    # アフィン変換実行
    moved_left_eye = (200.0, 250.0)
    for (photo_file, left_eye, radian, resize) in zip(target_files, left_eye_list, rotate_list, resize_scales):
        dirname = os.path.dirname(photo_file)
        filename = os.path.basename(photo_file)
        if util.is_image_file(filename):
            root, ext = os.path.splitext(filename)
            affined_file = util.face_work_dir() + '/affined/' + root + '-affine' + ext

            cosr = np.cos(radian)
            sinr = np.sin(radian)
            rot = np.matrix((
                (cosr * resize, -sinr * resize),
                (sinr * resize,  cosr * resize)
            ))
            vec = np.array(left_eye)
            roteye = np.dot(rot, vec)
            move = (moved_left_eye[0] - roteye[0, 0],
                    moved_left_eye[1] - roteye[0, 1])

            matrix = [
                [cosr * resize, -sinr * resize, move[0]],
                [sinr * resize,  cosr * resize, move[1]]
            ]
            affine_matrix = np.float64(matrix)

            im = cv2.imread(photo_file)
            size = im.shape[:2]
            im_affine = cv2.warpAffine(
                im, affine_matrix, size, flags=cv2.INTER_LANCZOS4)
            crop_img = im_affine[0:512, 0:512]
            cv2.imwrite(affined_file, crop_img)
            symlink(affined_file, util.taken_date(photo_file))

    return 0


def symlink(src_file, taken_date):
    src_full_path = os.path.abspath(src_file)
    dest_full_path = util.face_work_dir() + '/renamed/' + \
        taken_date.strftime('%Y%m%d%H%M%S') + '.jpg'
    # print 'src: %s, dest: %s' % (src_full_path, dest_full_path)
    if os.path.isfile(dest_full_path):
        # print 'remove %s' % dest_full_path
        os.unlink(dest_full_path)
    os.symlink(src_full_path, dest_full_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'image_file_directory', help='The face image files directory you\'d like to detect face.')
    args = parser.parse_args()
    main(args.image_file_directory)
