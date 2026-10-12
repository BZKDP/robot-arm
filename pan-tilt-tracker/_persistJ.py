import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8')); c.setdefault('track',{})
c['track'].update({'conf':0.15})
c['cam_quality']=16   # balans rezkost/fps
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED q16 conf0.15')
