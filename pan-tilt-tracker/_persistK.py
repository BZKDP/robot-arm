import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8')); c.setdefault('track',{})
c['track'].update({'onnx':'yolo11m-pose-640.onnx','imgsz':640,'conf':0.15})
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED m@640')
