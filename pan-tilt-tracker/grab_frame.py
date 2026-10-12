# -*- coding: utf-8 -*-
# Vytaskivaet odin JPEG-kadr iz MJPEG-potoka trekera (/video) -> fayl.
import urllib.request, sys
URL = "http://NucBox_M5PLUS.local:8200/video"
out = sys.argv[1]
r = urllib.request.urlopen(URL, timeout=10)
buf = b""
while len(buf) < 3_000_000:
    chunk = r.read(8192)
    if not chunk:
        break
    buf += chunk
    a = buf.find(b"\xff\xd8")
    b = buf.find(b"\xff\xd9", a + 2)
    if a >= 0 and b >= 0:
        open(out, "wb").write(buf[a:b + 2])
        print("saved", b - a + 2, "bytes ->", out)
        break
