import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8'))
c['cam_framesize']=7   # HVGA 480x320
c['cam_quality']=10
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED cam HVGA q10')
