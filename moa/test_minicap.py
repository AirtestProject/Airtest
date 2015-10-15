import socket
import struct
import cv2
cv2.namedWindow("preview")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 1313))
t = s.recv(24)
print repr(t)
print struct.unpack("<2B5I2B", t)

cnt = 0
while cnt < 300:
    frame_size = struct.unpack("<I", s.recv(4))[0]
    print frame_size
    tmp_size = 0
    trunk = ""
    while len(trunk) < frame_size:
        trunk_size = min(4096, frame_size - len(trunk))
        trunk += s.recv(trunk_size)
    # with open("%s.jpg" % cnt, "wb") as f:
    #     f.write(trunk)
    import numpy as np
    def string_2_img(pngstr):
        nparr = np.fromstring(pngstr, np.uint8)
        img = cv2.imdecode(nparr, cv2.CV_LOAD_IMAGE_COLOR)
        return img
    cv2.imshow("preview", string_2_img(trunk))
    key = cv2.waitKey(1)
    cnt += 1
s.close()
# print repr(trunk)
