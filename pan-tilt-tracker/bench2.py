import time, numpy as np, os
os.chdir(r"C:\pantilt\twin")
from ultralytics import YOLO
import onnxruntime as ort
import torch; torch.set_num_threads(8)
img = np.random.randint(0,255,(640,640,3),np.uint8)
def bench(path,name,n=12):
    try:
        mdl=YOLO(path); mdl.predict(img,imgsz=640,verbose=False)
        t=time.time()
        for _ in range(n): mdl.predict(img,imgsz=640,verbose=False)
        ms=(time.time()-t)/n*1000; print("  %-22s %5.0f ms  %4.1f fps"%(name,ms,1000/ms))
    except Exception as e: print("  %-22s ERR %s"%(name,str(e)[:60]))
for base in ["yolo11s-pose","yolo11m-pose"]:
    print("===",base,"===")
    bench(base+".pt", "torch CPU")
    try:
        ov=YOLO(base+".pt").export(format="openvino",imgsz=640,half=False,verbose=False)
        bench(ov, "openvino CPU")
    except Exception as e: print("  openvino export ERR",str(e)[:80])
    # raw onnx forward DML vs CPU
    try:
        onx=YOLO(base+".pt").export(format="onnx",imgsz=640,verbose=False)
        x=np.random.rand(1,3,640,640).astype(np.float32)
        for prov in [["DmlExecutionProvider"],["CPUExecutionProvider"]]:
            s=ort.InferenceSession(onx,providers=prov); inp=s.get_inputs()[0].name
            s.run(None,{inp:x})
            t=time.time(); n=12
            for _ in range(n): s.run(None,{inp:x})
            ms=(time.time()-t)/n*1000; print("  onnx-fwd %-13s %5.0f ms  %4.1f fps"%(prov[0][:3],ms,1000/ms))
    except Exception as e: print("  onnx ERR",str(e)[:80])
