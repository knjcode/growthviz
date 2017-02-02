ffmpeg -framerate 5 -i work/face/movie/movie_%05d.jpg -vcodec libx264 -pix_fmt yuv420p -r 60 ./face.mp4
