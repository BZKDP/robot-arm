import time, numpy as np, torch
torch.set_num_threads(8)
from ultralytics import YOLO
img = np.random.randint(0,255,(480,640,3),np.uint8)
for m in ["yolo11s-pose.pt","yolo11m-pose.pt","yolo11l-pose.pt"]:
    try:
        model=YOLO(m); model.predict(img, imgsz=640, verbose=False)
        t=time.time(); N=8
        for _ in range(N): model.predict(img, imgsz=640, verbose=False)
        ms=(time.time()-t)/N*1000
        print("%-20s %5.0f ms  %4.1f fps"%(m, ms, 1000/ms))
    except Exception as e:
        print(m,"ERR",e)
