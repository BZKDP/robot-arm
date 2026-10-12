import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8')); c.setdefault('track',{})
c['track'].update({'backend':'dml','onnx':'yolo11s-pose.onnx','imgsz':640,'conf':0.10,'coast':1.0,'lead':0.12,
                   'yaw_sign':-1,'tilt_sign':1,'max_step':40,'kp_yaw':240,'kp_tilt':220,'move_spd':2000,'deadzone':0.05,'fps':30})
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED')
