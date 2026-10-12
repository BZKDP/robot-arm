import time, numpy as np, os
os.chdir(r"C:\pantilt\twin")
from ultralytics import YOLO
onx=YOLO("yolo11s-pose.pt").export(format="onnx",imgsz=640,verbose=False)
print("onnx:",onx)
import onnxruntime as ort
x=np.random.rand(1,3,640,640).astype(np.float32)
for prov in [["DmlExecutionProvider"],["CPUExecutionProvider"]]:
    try:
        s=ort.InferenceSession(onx,providers=prov); inp=s.get_inputs()[0].name
        s.run(None,{inp:x}); s.run(None,{inp:x})
        t=time.time(); n=15
        for _ in range(n): s.run(None,{inp:x})
        ms=(time.time()-t)/n*1000; print("  ONNX-fwd %-8s %5.0f ms  %4.1f fps"%(prov[0][:3],ms,1000/ms))
    except Exception as e: print("  ",prov[0],"ERR",str(e)[:70])
