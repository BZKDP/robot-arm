import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8')); c.setdefault('track',{})
c['track'].update({'imgsz':640,'conf':0.2,'yaw_sign':-1,'tilt_sign':1,'max_step':60,'kp_yaw':280,'kp_tilt':260,
                   'move_spd':1400,'deadzone':0.04,'model':'yolov8s-pose.pt'})
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED')
