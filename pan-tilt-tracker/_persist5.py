import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8')); c.setdefault('track',{})
c['track'].update({'model':'yolo11m-pose.pt','imgsz':512,'conf':0.2,'yaw_sign':-1,'tilt_sign':1,
                   'max_step':90,'kp_yaw':420,'kp_tilt':390,'move_spd':2400,'deadzone':0.04})
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED')
