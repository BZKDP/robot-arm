import os, sys, cv2, urllib.request
sys.path.insert(0, r"C:\pantilt\twin"); os.chdir(r"C:\pantilt\twin")
if not os.path.exists("bus.jpg"):
    urllib.request.urlretrieve("https://ultralytics.com/images/bus.jpg","bus.jpg")
from dml_pose import DmlPose
m=DmlPose("yolo11s-pose.onnx", imgsz=640, conf=0.25)
img=cv2.imread("bus.jpg"); print("img",img.shape,"provider",m.provider)
d=m.detect(img)
print("detekcij lyudej:",len(d))
for i,p in enumerate(sorted(d,key=lambda x:-(x['box'][2]-x['box'][0])*(x['box'][3]-x['box'][1]))[:4]):
    b=p['box']; nose=p['kp'][0]
    print("  conf=%.2f box=(%d,%d,%d,%d) nos=(%d,%d c%.2f)"%(p['conf'],b[0],b[1],b[2],b[3],nose[0],nose[1],nose[2]))
