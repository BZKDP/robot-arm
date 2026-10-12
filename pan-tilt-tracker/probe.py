# -*- coding: utf-8 -*-
# Proba: nayti USB-vebkameru (cv2 VideoCapture) + proverit onnxruntime providery (DML?) + porty.
import cv2, sys
print("=== CAMERA PROBE (cv2 VideoCapture) ===")
found = []
for be_name, be in [("MSMF", cv2.CAP_MSMF), ("DSHOW", cv2.CAP_DSHOW)]:
    for i in range(5):
        try:
            cap = cv2.VideoCapture(i, be)
            if cap.isOpened():
                ok, fr = cap.read()
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                shp = fr.shape if (ok and fr is not None) else None
                print("  %-5s idx %d: OPEN  prop=%dx%d fps=%.0f  read=%s" % (be_name, i, w, h, fps, shp))
                if ok and fr is not None: found.append((be_name, i, w, h))
                cap.release()
        except Exception as e:
            print("  %-5s idx %d: err %s" % (be_name, i, e))
print("NASHEL rabochih:", found)

print("=== ONNXRUNTIME providers ===")
try:
    import onnxruntime as ort
    print("  available:", ort.get_available_providers())
    print("  version:", ort.__version__)
except Exception as e:
    print("  err:", e)

print("=== max razresheniya kamery idx0 (esli est) ===")
if found:
    be = cv2.CAP_MSMF if found[0][0] == "MSMF" else cv2.CAP_DSHOW
    cap = cv2.VideoCapture(found[0][1], be)
    for (tw, th) in [(1920,1080),(1280,720),(2560,1440),(3840,2160)]:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, tw); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, th)
        aw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); ah = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print("  zapros %dx%d -> realno %dx%d" % (tw, th, aw, ah))
    cap.release()
