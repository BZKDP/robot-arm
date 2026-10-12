import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8'))
c['cam_quality']=28   # silnoe szhatie -> melkie kadry -> 22fps (rezkost QVGA ok, detekt ok)
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED q28')
