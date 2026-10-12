# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

fig, ax = plt.subplots(figsize=(8.5, 12.6))
ax.set_xlim(0,100); ax.set_ylim(0,160); ax.set_aspect('equal'); ax.axis('off')

def dim(x0,y0,x1,y1,label,off=1.4,color='#c00'):
    ax.annotate('',xy=(x1,y1),xytext=(x0,y0),
        arrowprops=dict(arrowstyle='<->',color=color,lw=1.3))
    ax.text((x0+x1)/2,(y0+y1)/2+off,label,color=color,ha='center',va='center',
            fontsize=9.5,fontweight='bold',bbox=dict(fc='white',ec='none',pad=0.4))

ax.text(50,156,'ЗАМЕРЫ: мотор NEMA17 + редуктор (не стыкуются)',ha='center',fontsize=13,fontweight='bold')
ax.text(50,152,'Мерить штангенциркулем, в мм. Заполнить последний столбец таблицы.',ha='center',fontsize=8.5,color='#333')

# ===== MOTOR =====
ax.text(5,147,'МОТОР (NEMA17)',fontsize=11,fontweight='bold',color='#1a7a3a')
mx,my,ms=14,118,24
ax.add_patch(Rectangle((mx,my),ms,ms,fill=False,ec='#333',lw=1.6))
for hx in (mx+3,mx+ms-3):
    for hy in (my+3,my+ms-3):
        ax.add_patch(Circle((hx,hy),1.1,fill=False,ec='#333'))
cx,cy=mx+ms/2,my+ms/2
ax.add_patch(Circle((cx,cy),5,fill=False,ec='#333',lw=1.4))
ax.add_patch(Circle((cx,cy),1.6,fc='#333'))
dim(mx,my+ms+2.5,mx+ms,my+ms+2.5,'М1')
dim(mx+3,my-2.6,mx+ms-3,my-2.6,'М4',off=-1.4)
dim(cx-5,cy,cx+5,cy,'М3')
sx,sy,sw,sh=60,122,22,16
ax.add_patch(Rectangle((sx,sy),sw,sh,fc='#eee',ec='#333'))
ax.add_patch(Rectangle((sx+sw,sy+sh/2-1.3),10,2.6,fc='#ccc',ec='#333'))
ax.text(sx+sw/2,sy-3,'вид сбоку',ha='center',fontsize=8,color='#666')
dim(sx+sw,sy+sh/2+4,sx+sw+10,sy+sh/2+4,'М2 длина')
ax.text(sx+sw+12.5,sy+sh/2,'М2 Ø',fontsize=9.5,color='#c00',fontweight='bold',va='center')

# ===== GEARBOX =====
ax.text(5,109,'РЕДУКТОР (сторона входа, к мотору)',fontsize=11,fontweight='bold',color='#1550aa')
gx,gy,gs=14,80,24
ax.add_patch(Rectangle((gx,gy),gs,gs,fill=False,ec='#333',lw=1.6))
for hx in (gx+3,gx+gs-3):
    for hy in (gy+3,gy+gs-3):
        ax.add_patch(Circle((hx,hy),1.1,fill=False,ec='#333'))
gcx,gcy=gx+gs/2,gy+gs/2
ax.add_patch(Circle((gcx,gcy),6,fill=False,ec='#333',lw=1.4))
ax.add_patch(Circle((gcx,gcy),2.4,fill=False,ec='#333'))
dim(gx,gy+gs+2.5,gx+gs,gy+gs+2.5,'G1')
dim(gx+3,gy-2.6,gx+gs-3,gy-2.6,'G4',off=-1.4)
ax.annotate('G2 (выточка)',xy=(gcx+6,gcy+1.5),xytext=(gx+gs+3,gy+gs-1),
            fontsize=9,color='#c00',fontweight='bold',arrowprops=dict(arrowstyle='->',color='#c00'))
ax.annotate('G3 (отв. под вал)',xy=(gcx+2,gcy),xytext=(gx+gs+3,gy+1),
            fontsize=9,color='#c00',fontweight='bold',arrowprops=dict(arrowstyle='->',color='#c00'))
ax.text(64,100,'Загляни во входное отверстие:\nкакой Ø вала принимает?\n(5 / 6.35 / 8 мм?)',fontsize=8.5,color='#333',va='top')

# ===== TABLE =====
rows=[('М1','ширина корпуса мотора (грань-грань)','~42'),
 ('М2','Ø вала / длина вала','5 / ~24'),
 ('М3','Ø центр. бобышки / высота','~22 / ~2'),
 ('М4','шаг крепёжных отв. (центр-центр)','~31'),
 ('G1','ширина входного фланца редуктора','?'),
 ('G2','Ø центральной выточки (под бобышку)','?'),
 ('G3','Ø входного отв. под вал','?'),
 ('G4','шаг крепёжных отв. фланца','?'),
 ('+','сколько крепёжных отв. у редуктора?','—')]
top=63; rh=5
ax.text(50,top+2.5,'ТАБЛИЦА — ЗАПОЛНИТЬ',ha='center',fontsize=11,fontweight='bold')
ax.add_patch(Rectangle((4,top-rh),92,rh,fc='#e8ecf7',ec='#333'))
ax.text(6,top-rh/2,'Код',va='center',fontsize=8.5,fontweight='bold')
ax.text(18,top-rh/2,'Что мерить',va='center',fontsize=8.5,fontweight='bold')
ax.text(73,top-rh/2,'Ожид.',va='center',fontsize=8.5,fontweight='bold')
ax.text(84,top-rh/2,'Замер, мм',va='center',fontsize=8.5,fontweight='bold')
for i,(code,desc,exp) in enumerate(rows):
    ry=top-rh*(i+2)
    ax.add_patch(Rectangle((4,ry),92,rh,fill=False,ec='#333'))
    ax.add_patch(Rectangle((82,ry),14,rh,fc='#fffbe6',ec='#333'))
    ax.text(6,ry+rh/2,code,va='center',fontsize=8.5,fontweight='bold')
    ax.text(18,ry+rh/2,desc,va='center',fontsize=7.8)
    ax.text(73,ry+rh/2,exp,va='center',fontsize=8)
for xx in [16,71,82]:
    ax.plot([xx,xx],[top-rh*(len(rows)+1),top],color='#333',lw=0.8)

plt.savefig('measure_sheet.png',dpi=130,bbox_inches='tight',facecolor='white')
print('OK')
