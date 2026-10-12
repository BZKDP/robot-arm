import time, numpy as np, onnxruntime as ort
x=np.random.rand(1,3,640,640).astype(np.float32)
for onx in [r"C:\pantilt\twin\yolo11s-pose.onnx", r"C:\pantilt\twin\yolo11m-pose.onnx"]:
    s=ort.InferenceSession(onx,providers=["DmlExecutionProvider"]); inp=s.get_inputs()[0].name
    for _ in range(3): s.run(None,{inp:x})
    t=time.time(); n=20
    for _ in range(n): s.run(None,{inp:x})
    ms=(time.time()-t)/n*1000; print("%-18s DML iGPU %5.0f ms  %4.1f fps"%(onx.split(chr(92))[-1],ms,1000/ms))
