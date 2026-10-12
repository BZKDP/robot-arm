import json
p=r'C:\pantilt\twin\config.json'; c=json.load(open(p,encoding='utf-8'))
c['cam_framesize']=5   # QVGA - stabilno, 12fps (optimum dlya trekinga po serial)
c['cam_quality']=10    # chut luchshe JPEG bez poteri fps
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print('SAVED QVGA q10')
