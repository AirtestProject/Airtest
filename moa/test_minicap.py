import socket
import struct


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 1313))
t = s.recv(24)
print repr(t)
print struct.unpack("<2B5I2B", t)

cnt = 0
while cnt < 3:
    frame_size = struct.unpack("<I", s.recv(4))[0]
    print frame_size
    tmp_size = 0
    trunk = ""
    while len(trunk) < frame_size:
        trunk_size = min(4096, frame_size - len(trunk))
        trunk += s.recv(trunk_size)
    with open("%s.jpg" % cnt, "wb") as f:
        f.write(trunk)
    cnt += 1
s.close()
print repr(trunk)