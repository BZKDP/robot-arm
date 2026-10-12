import time, numpy as np, onnxruntime as ort
for f,sz in [(r"C:\pantilt\twin\yolo11m-pose-640.onnx",640),(r"C:\pantilt\twin\yolo11m-pose.onnx",512)]:
    s=ort.InferenceSession(f,providers=["DmlExecutionProvider","CPUExecutionProvider"]); inp=s.get_inputs()[0]
    x=np.random.rand(1,3,sz,sz).astype(np.float32)
    for _ in range(3): s.run(None,{inp.name:x})
    t=time.time(); n=20
    for _ in range(n): s.run(None,{inp.name:x})
    ms=(time.time()-t)/n*1000; print("m@%d FP32 DML: %.0f ms  %.1f fps"%(sz,ms,1000/ms))
