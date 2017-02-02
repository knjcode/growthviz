#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse

import body


def main(photo_files):
    profile_filename = 'create_video.profile'
    make_profile(profile_filename)
    make_create_video_script(photo_files, profile_filename)


def make_profile(profile_filename):
    config = body.make_config()
    profile = make_profile_str(
        config.image['width_px'], config.image['height_px'])
    write_file(profile_filename, profile)


def make_create_video_script(photo_files, profile_filename):
    head = photo_files[0]
    rest = photo_files[1:]
    prefix = '#!/bin/sh \nMLT_PROFILE=%s melt -verbose \\\n' % profile_filename
    head_s = '%s out=50 \\\n' % head
    rest_s = ''
    for f in rest:
        rest_s += '%s out=75 -mix 25 -mixer luma \\\n' % f
    postfix = '-consumer avformat:work/body.mp4 vcodec=libx264 an=1\n'
    s = prefix + head_s + rest_s + postfix
    write_file('create_video.sh', s)


def write_file(file_name, s):
    if os.path.isfile(file_name):
        os.remove(file_name)
    with os.fdopen(os.open(file_name, os.O_WRONLY | os.O_CREAT, 0o755), 'w') as handle:
        handle.write(s)


def calc_display_aspect(width, height):
    diff_16_9 = abs(16.0 / 9 - float(width) / height)
    diff_9_16 = abs(9.0 / 16 - float(width) / height)
    if diff_16_9 < diff_9_16:
        return 16, 9
    else:
        return 9, 16


def make_profile_str(width, height):
    num, den = calc_display_aspect(width, height)
    template = """
description=HD 720p 25 fps
frame_rate_num=25
frame_rate_den=1
width=%s
height=%s
progressive=1
sample_aspect_num=1
sample_aspect_den=1
display_aspect_num=%s
display_aspect_den=%s
colorspace=709
"""[1:]
    profile = template % (str(width), str(height), str(num), str(den))
    return profile

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'image_files', nargs='*', help='The image you\'d like to make video.')
    args = parser.parse_args()
    main(args.image_files)
