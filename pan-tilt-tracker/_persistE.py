import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8'))
c.pop('cam_framesize',None); c.pop('cam_quality',None)   # ne slat - kamera gruzitsya na defolt QVGA (nadyozhno)
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('CLEANED - kamera na defolte QVGA')
