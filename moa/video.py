from PIL import Image
from subprocess import Popen, PIPE

# fps, duration = 24, 100
# p = Popen(['ffmpeg', '-y', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', '24', '-i', '-', '-vcodec', 'mpeg4', '-qscale', '5', '-r', '24', 'video.avi'], stdin=PIPE)
# for i in range(fps * duration):
#     im = Image.new("RGB", (1080, 1920), (i, 1, 1))
#     im.save(p.stdin, 'JPEG')
# p.stdin.close()
# p.wait()

cmd = """
ffmpeg -y -f image2pipe -vcodec libx264 -preset slow
 -profile main -crf 2 -r 30  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" movie2.avi
"""
cmd = cmd.split()
print cmd
import os
p = Popen(['ffmpeg', '-y', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', '24', '-i', '-', '-vcodec', 'mpeg4', '-qscale', '5', '-r', '24', '-f', 'segment', '-'], stdin=PIPE, stdout=PIPE)
# p = Popen(['ffmpeg', '-y', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', '24', '-i', '-', '-vcodec', 'mpeg4', '-qscale', '5', '-r', '24', 'video.avi'], stdin=PIPE)
# p = Popen(cmd, stdin=PIPE)

for i in range(30):
    print i
    im = Image.open("img/%s.jpg"%i) 
    im.save(p.stdin, 'JPEG')

cnt = 0
while cnt<100:
    print cnt, repr(p.stdout.read())
    cnt += 1

p.stdin.close()
p.wait()
