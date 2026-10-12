import json
p=r'C:\pantilt\twin\config.json'
c=json.load(open(p,encoding='utf-8'))
c.setdefault('track',{})
c['track']['yaw_sign']=-1
c['track']['tilt_sign']=1
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('SAVED signs:', c['track']['yaw_sign'], c['track']['tilt_sign'])
