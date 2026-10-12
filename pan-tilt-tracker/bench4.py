import time, numpy as np, onnxruntime as ort
print("avail:", ort.get_available_providers())
onx=r"C:\pantilt\twin\yolo11s-pose.onnx"
x=np.random.rand(1,3,640,640).astype(np.float32)
for prov in [["DmlExecutionProvider"],["CPUExecutionProvider"]]:
    try:
        s=ort.InferenceSession(onx,providers=prov); used=s.get_providers()[0]
        inp=s.get_inputs()[0].name
        for _ in range(3): s.run(None,{inp:x})
        t=time.time(); n=20
        for _ in range(n): s.run(None,{inp:x})
        ms=(time.time()-t)/n*1000; print("req %-4s -> USED %-22s %5.0f ms  %4.1f fps"%(prov[0][:3],used,ms,1000/ms))
    except Exception as e: print(prov,"ERR",str(e)[:80])
