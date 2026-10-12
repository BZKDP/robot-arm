import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8')); c.setdefault('track',{})
c['track'].update({'imgsz':640,'conf':0.15,'yaw_sign':-1,'tilt_sign':1,'max_step':30,'kp_yaw':140,'kp_tilt':130,'model':'yolov8n-pose.pt'})
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED:',json.dumps(c['track']))
