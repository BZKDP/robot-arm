import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8')); c.setdefault('track',{})
c['track'].update({'smooth':0.3,'lead':0.12,'kp_yaw':260,'kp_tilt':240,'max_step':45,'deadzone':0.05})
c.pop('cam_framesize',None); c.pop('cam_quality',None)
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED')
