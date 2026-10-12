import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8')); c.setdefault('track',{})
c['track'].update({'model':'yolo11s-pose.pt','imgsz':640,'conf':0.10,'coast':1.0,'yaw_sign':-1,'tilt_sign':1,
                   'max_step':55,'kp_yaw':300,'kp_tilt':280,'move_spd':2000,'deadzone':0.06})
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED')
