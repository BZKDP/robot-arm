import time, numpy as np, onnxruntime as ort
s=ort.InferenceSession(r"C:\pantilt\twin\yolo11m-pose.onnx",providers=["DmlExecutionProvider","CPUExecutionProvider"])
inp=s.get_inputs()[0]; print("provider",s.get_providers()[0],"input dtype",inp.type)
dt=np.float16 if "float16" in inp.type else np.float32
x=np.random.rand(1,3,640,640).astype(dt)
for _ in range(3): s.run(None,{inp.name:x})
t=time.time(); n=20
for _ in range(n): s.run(None,{inp.name:x})
ms=(time.time()-t)/n*1000; print("yolo11m FP16 DML: %.0f ms  %.1f fps"%(ms,1000/ms))
