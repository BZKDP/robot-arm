import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8')); c.setdefault('track',{})
c['track'].update({'conf':0.25,'lock_hold':1.5,'lock_dist':0.35,'smooth':0.3,'lead':0.12})
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED conf0.25+lock')
