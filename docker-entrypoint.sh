#!/bin/bash

set -e

sex="$1"
birthday="$2"
max_height="$3"

cd /app
./clear.sh

# body
sed -i -e "s/female/$sex/g" config/user.json
sed -i -e "s@2011/12/9@$birthday@g" config/user.json
sed -i -e "s/120$/$max_height/g" config/image.json
cat config/user.json
cat config/image.json
./body.py /app/data/*.jpg
./create_create_video_script.py work/body/renamed/*.jpg
xvfb-run /app/create_video.sh

# face
framerate=5

./face.py /app/data

i=0
for f in $(ls -1 work/face/renamed/*.jpg | sort -t'-' -k2h)
do
  mv "$f" $(printf "work/face/movie/movie_%05d.jpg" $i)
  : $((i++))
done

ffmpeg -y -framerate $framerate -i work/face/movie/movie_%05d.jpg -vcodec libx264 -pix_fmt yuv420p -r 60 work/face.mp4
