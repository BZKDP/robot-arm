# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow

fig,ax=plt.subplots(figsize=(11,5.6))
ax.set_xlim(0,124); ax.set_ylim(-34,44); ax.set_aspect('equal'); ax.axis('off')

ax.text(62,41,'Как редуктор садится на мотор (вид в разрезе)',ha='center',fontsize=14,fontweight='bold')

# centerline
ax.plot([2,122],[0,0],ls='-.',color='#999',lw=0.8)

# ===== MOTOR (left) =====
ax.add_patch(Rectangle((6,-24),26,48,fc='#3a3a3a',ec='#111'))
ax.text(19,-28,'МОТОР',ha='center',fontsize=10,fontweight='bold',color='#222')
# pilot boss (wide, short)
ax.add_patch(Rectangle((32,-11),3,22,fc='#b8b8b8',ec='#333'))
# shaft (thin, long)
ax.add_patch(Rectangle((32,-2.5),26,5,fc='#8a8f96',ec='#333'))

# ===== GEARBOX (right) =====
gxf=82
ax.add_patch(Rectangle((gxf,-28),34,56,fc='#2b4a9b',ec='#111'))
ax.text(gxf+17,-32,'РЕДУКТОР',ha='center',fontsize=10,fontweight='bold',color='#222')
# recess (wide) for boss
ax.add_patch(Rectangle((gxf,-11),4.5,22,fc='#e9edf7',ec='#333'))
# bore (thin, deep) for shaft
ax.add_patch(Rectangle((gxf,-2.5),15,5,fc='#ffffff',ec='#333'))

# alignment dashed
ax.plot([58,gxf],[2.5,2.5],ls=':',color='#c00',lw=1)
ax.plot([58,gxf],[-2.5,-2.5],ls=':',color='#c00',lw=1)
ax.plot([35,gxf],[11,11],ls=':',color='#1a7a3a',lw=1)
ax.plot([35,gxf],[-11,-11],ls=':',color='#1a7a3a',lw=1)

# insertion arrows
ax.annotate('',xy=(gxf-1,0),xytext=(60,0),arrowprops=dict(arrowstyle='-|>',color='#c00',lw=2))
ax.text(70,3.2,'ВАЛ сюда',ha='center',fontsize=9.5,color='#c00',fontweight='bold')
ax.annotate('',xy=(gxf-1,16),xytext=(40,16),arrowprops=dict(arrowstyle='-|>',color='#1a7a3a',lw=2))
ax.text(60,18.5,'БОБЫШКА сюда',ha='center',fontsize=9.5,color='#1a7a3a',fontweight='bold')

# labels motor
ax.annotate('ВАЛ ~5мм\n(тонкий, длинный)',xy=(50,0),xytext=(30,-30),
            fontsize=9,color='#c00',fontweight='bold',ha='center',
            arrowprops=dict(arrowstyle='->',color='#c00'))
ax.annotate('БОБЫШКА ~22мм\n(широкая, короткая)',xy=(33.5,9),xytext=(20,30),
            fontsize=9,color='#1a7a3a',fontweight='bold',ha='center',
            arrowprops=dict(arrowstyle='->',color='#1a7a3a'))
# labels gearbox
ax.annotate('тонкое отверстие\n(муфта) — под ВАЛ',xy=(gxf+7,2.5),xytext=(104,26),
            fontsize=9,color='#c00',fontweight='bold',ha='center',
            arrowprops=dict(arrowstyle='->',color='#c00'))
ax.annotate('широкая выточка —\nпод БОБЫШКУ',xy=(gxf+2,11),xytext=(108,-24),
            fontsize=9,color='#1a7a3a',fontweight='bold',ha='center',
            arrowprops=dict(arrowstyle='->',color='#1a7a3a'))

ax.text(62,-38,'В тонкое отверстие входит ТОЛЬКО вал. Бобышка садится в широкую выточку вокруг — не в это отверстие!',
        ha='center',fontsize=10,fontweight='bold',color='#a00')

plt.savefig('fit_section.png',dpi=130,bbox_inches='tight',facecolor='white')
print('OK')
