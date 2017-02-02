# -*- coding: utf-8 -*-

import os
import sys
import hashlib
import exifread
import math
import cv2
import numpy as np

from PIL import Image
from datetime import datetime
from base64 import b64encode
from StringIO import StringIO
from skimage import io


def dlib_face_detector_version():
    return '001'


def src_dir():
    return os.path.dirname(os.path.abspath(__file__))


def work_dir():
    return src_dir() + '/work'


def dlib_cache_dir():
    return work_dir() + '/dlibcache'


def google_cloud_vision_cache_dir():
    return work_dir() + '/fdcache'


def config_dir():
    return src_dir() + '/config'


def body_work_dir():
    return work_dir() + '/body'


def face_work_dir():
    return work_dir() + '/face'


def md5(fname):
    hash = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()


def md5_google_cloud_vision_logfile(fname):
    md5sum = md5(fname)
    face_detect_log = google_cloud_vision_cache_dir() + '/' + md5sum + '-face.log'
    return face_detect_log


def md5_dlib_logfile(fname):
    md5sum = md5(fname)
    dlib_face_detect_log = dlib_cache_dir() + '/' + md5sum + '-' + \
        dlib_face_detector_version() + '-dlib.log'
    return dlib_face_detect_log


def is_image_file(fname):
    root, ext = os.path.splitext(fname)
    if ext == '.png' or ext == '.jpg' or ext == '.jpeg' or ext == '.gif':
        return True
    return False


def taken_date(fname):
    f = open(fname, 'rb')
    tags = exifread.process_file(f)
    date = tags['EXIF DateTimeOriginal']
    taken_date = datetime.strptime(str(date), '%Y:%m:%d %H:%M:%S')
    return taken_date


def orientation(fname):
    f = open(fname, 'rb')
    tags = exifread.process_file(f)
    # print tags['Image Orientation']
    if 'Rotated 90 CW' in str(tags['Image Orientation']):
        return 270
    elif 'Rotated 90 CCW' in str(tags['Image Orientation']):
        return 90
    return None


def resize(file_path, resize_rate):
    img_orig = Image.open(file_path)
    size = get_dest_size(img_orig, resize_rate)
    return img_orig.resize(size, Image.LANCZOS)


def get_dest_size(image, resize_rate):
    (w, h) = image.size
    w_dest = int(w * resize_rate)
    h_dest = int(h * resize_rate)
    return (w_dest, h_dest)


def read_file_to_buffer(fname):
    f = open(fname, "r")
    buf = StringIO(f.read())
    f.close()
    return buf


def print_image(fname):
    data = read_file_to_buffer(fname)
    sys.stdout.write("\033]1337;File=name=%s;size=%d;inline=1:%s\a\n" %
                     (b64encode(fname), data.len, b64encode(data.getvalue())))
    data.close()


def use_google_face_detection():
    try:
        if os.environ['USE_GOOGLE_FACE_DETECTION'] == '1':
            return True
    except KeyError:
        return False
    return False

if use_google_face_detection():
    import googleapiclient.discovery
else:
    import dlib
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor('./shape_predictor_68_face_landmarks.dat')


def face_detection(fname, cache):
    if use_google_face_detection():
        return google_face_detection(fname, cache)
    return dlib_face_detection(fname, cache)


def dlib_face_detction_dict(left_eye, right_eye, face_rect, left_eyes, tiltAngle, panAngle, rollAngle):
    return {u'responses':
            [
                {u'faceAnnotations':
                 [{
                     u'landmarks':
                     [
                         {u'position': {u'y': left_eye[1], u'x': left_eye[
                             0]}, u'type': u'LEFT_EYE_PUPIL'},
                         {u'position': {u'y': right_eye[1], u'x': right_eye[
                             0]}, u'type': u'RIGHT_EYE_PUPIL'}
                     ],
                     u'rollAngle': rollAngle,
                     u'panAngle': panAngle,
                     u'tiltAngle': tiltAngle,
                     u'detectionConfidence': 0.9,
                     u'fdBoundingPoly': {
                         u'vertices':
                         [
                             {u'y': face_rect[0][1], u'x': face_rect[0][0]},
                             {u'y': face_rect[0][1], u'x': face_rect[1][0]},
                             {u'y': face_rect[1][1], u'x': face_rect[1][0]},
                             {u'y': face_rect[1][1], u'x': face_rect[0][0]}
                         ]
                     }
                 }]
                 }
            ]
            }


def triangle_center(p1, p2, p3):
    x = (p1[0] + p2[0] + p3[0]) / 3
    y = (p1[1] + p2[1] + p3[1]) / 3
    return (x, y)


def triangle_area(p1, p2, p3):
    return ((p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0]))


def polygon_center(count, points):
    s = 0.0
    gx = 0.0
    gy = 0.0
    for i in range(2, count):
        s1 = triangle_area(points[0], points[i - 1], points[i])
        pt = triangle_center(points[0], points[i - 1], points[i])
        gx += s1 * pt[0]
        gy += s1 * pt[1]
        s += s1
    return (gx / s, gy / s)


def head_pose_estimation(fname, estimation_points):
    # 顔向き推定
    # http://www.learnopencv.com/head-pose-estimation-using-opencv-and-dlib/
    # http://qiita.com/TaroYamada/items/e3f3d0ea4ecc0a832fac
    im = cv2.imread(fname)
    size = im.shape
    # 2D image points.
    image_points = np.array([
        estimation_points[0],
        estimation_points[1],
        estimation_points[2],
        estimation_points[3],
        estimation_points[4],
        estimation_points[5]
    ], dtype="double")
    # 3D model points.
    model_points = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye left corner
        (225.0, 170.0, -135.0),      # Right eye right corne
        (-150.0, -150.0, -125.0),    # Left Mouth corner
        (150.0, -150.0, -125.0)      # Right mouth corner
    ])
    # Camera internals
    focal_length = size[1]
    center = (size[1] / 2, size[0] / 2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]],
         [0, focal_length, center[1]],
         [0, 0, 1]], dtype="double"
    )
    # print "Camera Matrix :\n {0}".format(camera_matrix)
    dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion
    (success, rotation_vector, translation_vector) = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs)
    # print "Rotation Vector:\n {0}".format(rotation_vector)
    # print "Translation Vector:\n {0}".format(translation_vector)
    (nose_end_point2D, jacobian) = cv2.projectPoints(np.array(
        [(0.0, 0.0, 1000.0)]), rotation_vector, translation_vector, camera_matrix, dist_coeffs)

    rotation_matrix = cv2.Rodrigues(rotation_vector)[0]

    # get Euler angles form rotation_matrix
    projection_matrix = np.float32(
        [
            [rotation_matrix[0][0], rotation_matrix[
                0][1], rotation_matrix[0][2], 0],
            [rotation_matrix[1][0], rotation_matrix[
                1][1], rotation_matrix[1][2], 0],
            [rotation_matrix[2][0], rotation_matrix[2][1], rotation_matrix[2][2], 0]
        ]
    ).reshape(3, -1)
    eulerAngles = cv2.decomposeProjectionMatrix(projection_matrix)[-1]

    return (angle[0] for angle in eulerAngles)


def dlib_face_detection(fname, cache):
    dlib_face_detect_log = md5_dlib_logfile(fname)
    if os.path.exists(dlib_face_detect_log) and cache:
        # 過去に顔認識を実施したログがあればそちらを使う
        print 'Dlib face detect log exists. Using this log. %s' % dlib_face_detect_log
        response = eval(open(dlib_face_detect_log).read())
    else:
        img = io.imread(fname)
        (height_org, width_org) = img.shape[:2]
        dets = detector(img, 1)
        (height_up, width_up) = img.shape[:2]
        (height_scale, width_scale) = (
            height_org / height_up, width_org / width_up)
        (left_eye_x, left_eye_y) = (0, 0)
        (right_eye_x, right_eye_y) = (0, 0)
        if len(dets) > 0:
            d = dets[0]
            shape = predictor(img, d)
            left_eyes = []
            right_eyes = []
            for i in range(36, 42):
                left_eye_x += shape.part(i).x * width_scale
                left_eye_y += shape.part(i).y * height_scale
                left_eyes.append((shape.part(i).x * width_scale,
                                  shape.part(i).y * height_scale))
            for i in range(42, 48):
                right_eye_x += shape.part(i).x * width_scale
                right_eye_y += shape.part(i).y * height_scale
                right_eyes.append(
                    (shape.part(i).x * width_scale, shape.part(i).y * height_scale))
            left_eye = polygon_center(6, left_eyes)
            right_eye = polygon_center(6, right_eyes)
            face_rect = [(d.left() * width_scale, d.top() * height_scale),
                         (d.right() * width_scale, d.bottom() * height_scale)]

            def extract_points(part):
                return (part.x * width_scale, part.y * height_scale)
            # 顔向き推定用の6点
            nose_tip = extract_points(shape.part(30))
            chin = extract_points(shape.part(8))
            left_eye_left_corner = extract_points(shape.part(36))
            right_eye_right_corner = extract_points(shape.part(45))
            left_mouth_corner = extract_points(shape.part(48))
            right_mouth_corner = extract_points(shape.part(54))
            head_pose_estimation_points = (
                nose_tip, chin, left_eye_left_corner, right_eye_right_corner, left_mouth_corner, right_mouth_corner)
            (tiltAngle, panAngle, rollAngle) = head_pose_estimation(
                fname, head_pose_estimation_points)
            response = dlib_face_detction_dict(
                left_eye, right_eye, face_rect, left_eyes, tiltAngle, panAngle, rollAngle)
        else:
            response = {u'responses': [{}]}
        # 顔認識結果をログに保存
        f = open(dlib_face_detect_log, 'w')
        f.write('%s' % response)
        f.close
        print 'dlib face detect log saved. %s' % dlib_face_detect_log
    return response


def google_face_detection(fname, cache):
    face_detect_log = md5_google_cloud_vision_logfile(fname)
    if os.path.exists(face_detect_log) and cache:
        # 過去に顔認識を実施したログがあればそちらを使う
        print 'Face detect log exists. Using this log. %s' % face_detect_log
        response = eval(open(face_detect_log).read())
    else:
        service = googleapiclient.discovery.build('vision', 'v1')
        image_content = b64encode(open(fname, 'rb').read())
        service_request = service.images().annotate(
            body={
                'requests': [{
                    'image': {
                        'content': image_content
                    },
                    'features': [{
                        'type': 'FACE_DETECTION',
                        'maxResults': 1,
                    }]
                }]
            })
        response = service_request.execute()
        if len(response['responses'][0]) >= 0:
            # 顔認識結果をログに保存
            f = open(face_detect_log, 'w')
            f.write('%s' % response)
            f.close
            print 'Face detect log saved. %s' % face_detect_log

    return response
