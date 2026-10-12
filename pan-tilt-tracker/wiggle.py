#!/usr/bin/env python
# wiggle.py <id> [n] — pokachat servo tuda-syuda vokrug centra 2048
import sys, time, serial
PORT="COM9"; BAUD=115200
sid = int(sys.argv[1]) if len(sys.argv)>1 else 1
n   = int(sys.argv[2]) if len(sys.argv)>2 else 4
s = serial.Serial(PORT, BAUD, timeout=1.0)
time.sleep(1.8); s.reset_input_buffer()
seq = []
for _ in range(n):
    seq += [1500, 2600]
seq += [2048]
for p in seq:
    s.write(("M %d %d 1200\n" % (sid, p)).encode())
    time.sleep(0.7)
s.close()
print("done id", sid)
