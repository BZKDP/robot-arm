# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

def dim(ax, x0, y0, x1, y1, label, off=1.2, color='#c00', fs=9):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='<->', color=color, lw=1.2))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 + off, label, color=color, ha='center', va='center',
            fontsize=fs, fontweight='bold', bbox=dict(fc='white', ec='none', pad=0.3))

def minitable(ax, x, ytop, w, title, rows, rh=4.2):
    ax.text(x + w / 2, ytop + 2, title, ha='center', fontsize=10, fontweight='bold')
    ax.add_patch(Rectangle((x, ytop - rh), w, rh, fc='#e8ecf7', ec='#333'))
    ax.text(x + 2, ytop - rh / 2, 'Код', va='center', fontsize=7.5, fontweight='bold')
    ax.text(x + 11, ytop - rh / 2, 'Что мерить', va='center', fontsize=7.5, fontweight='bold')
    ax.text(x + w - 12, ytop - rh / 2, 'мм', va='center', fontsize=7.5, fontweight='bold')
    for i, (c, d) in enumerate(rows):
        ry = ytop - rh * (i + 2)
        ax.add_patch(Rectangle((x, ry), w, rh, fill=False, ec='#333'))
        ax.add_patch(Rectangle((x + w - 15, ry), 15, rh, fc='#fffbe6', ec='#333'))
        ax.text(x + 2, ry + rh / 2, c, va='center', fontsize=7.5, fontweight='bold')
        ax.text(x + 11, ry + rh / 2, d, va='center', fontsize=6.9)
    for xx in [x + 9, x + w - 15]:
        ax.plot([xx, xx], [ytop - rh * (len(rows) + 1), ytop], color='#333', lw=0.7)

# ================= SHEET A: OUTPUT + AS5600 =================
figA, ax = plt.subplots(figsize=(11, 8.6))
ax.set_xlim(0, 120); ax.set_ylim(0, 94); ax.set_aspect('equal'); ax.axis('off')
ax.text(60, 90, 'ЗАМЕРЫ (A): выход редуктора + AS5600', ha='center', fontsize=14, fontweight='bold')
ax.text(60, 86, 'Мерить штангенциркулем, в мм. Заполнить жёлтые клетки.', ha='center', fontsize=8.5, color='#333')

ax.add_patch(Rectangle((3, 45), 56, 38, fill=False, ec='#94a3b8'))
ax.text(6, 79, '1) ВЫХОД РЕДУКТОРА (сбоку)', fontsize=10, fontweight='bold', color='#1550aa')
ax.add_patch(Rectangle((10, 60), 9, 10, fc='#3a3a3a'))
ax.add_patch(Rectangle((19, 61), 15, 8, fc='#2b4a9b'))
ax.add_patch(Rectangle((34, 64), 9, 2.4, fc='#8a8f96'))
dim(ax, 25, 61, 25, 69, '', off=0)
ax.text(27, 65, 'O4', color='#c00', fontsize=9, fontweight='bold')
dim(ax, 34, 58.5, 43, 58.5, 'O2')
ax.text(45, 65, 'O1', color='#c00', fontsize=9, fontweight='bold')
dim(ax, 10, 73, 43, 73, 'O5')
ax.text(11, 56, 'вал (O3: есть лыска?)', fontsize=7, color='#555')
ax.add_patch(Circle((51, 53), 6, fill=False, ec='#333'))
ax.add_patch(Circle((51, 53), 2, fill=False, ec='#333'))
ax.add_patch(Circle((51, 58), 0.9, fc='#333'))
ax.add_patch(Circle((51, 48), 0.9, fc='#333'))
ax.text(51, 44, 'торец выхода: O6 отв., O7 поясок', ha='center', fontsize=6.6, color='#555')

ax.add_patch(Rectangle((62, 45), 55, 38, fill=False, ec='#94a3b8'))
ax.text(65, 79, '2) МОДУЛЬ AS5600 + магнит', fontsize=10, fontweight='bold', color='#1a7a3a')
ax.add_patch(Rectangle((72, 54), 28, 20, fc='#dcfce7', ec='#166534'))
for hx in (75, 97):
    for hy in (57, 71):
        ax.add_patch(Circle((hx, hy), 0.9, fill=False, ec='#333'))
ax.add_patch(Rectangle((84, 62), 4, 4, fc='#333'))
ax.add_patch(Circle((108, 64), 3, fc='#dc2626'))
dim(ax, 72, 77, 100, 77, 'A1 Д')
ax.text(67, 64, 'A1 Ш', color='#c00', fontsize=8, fontweight='bold', rotation=90, va='center')
ax.text(86, 59, 'чип', ha='center', fontsize=6.5, color='#fff')
ax.annotate('A4 (центр чипа от края)', xy=(86, 64), xytext=(90, 50), fontsize=6.8, color='#c00',
            fontweight='bold', ha='center', arrowprops=dict(arrowstyle='->', color='#c00'))
ax.text(108, 58.5, 'A5 магнит\nØ×толщ', ha='center', fontsize=6.8, color='#c00', fontweight='bold')
ax.text(74, 51, 'A2 Ø отв · A3 шаг отв', fontsize=6.8, color='#555')

minitable(ax, 4, 40, 54, 'Выход редуктора', [
    ('O1', 'Ø выходного вала'), ('O2', 'длина вала (торчит)'), ('O3', 'лыска? да/нет+ширина'),
    ('O4', 'Ø корпуса редуктора'), ('O5', 'длина мотор+редуктор'),
    ('O6', 'торец: отв. (шт/Ø/шаг)'), ('O7', 'Ø пояска на торце')])
minitable(ax, 63, 40, 54, 'AS5600 модуль', [
    ('A1', 'плата Д×Ш'), ('A2', 'Ø монтаж. отв.'), ('A3', 'шаг монтаж. отв.'),
    ('A4', 'центр чипа от края'), ('A5', 'магнит Ø×толщина')])
figA.savefig('measure_A_output_as5600.png', dpi=130, bbox_inches='tight', facecolor='white')

# ================= SHEET B: FRAME =================
figB, ax = plt.subplots(figsize=(11, 8.6))
ax.set_xlim(0, 120); ax.set_ylim(0, 94); ax.set_aspect('equal'); ax.axis('off')
ax.text(60, 90, 'ЗАМЕРЫ (B): каркас — U-кронштейн + балка', ha='center', fontsize=14, fontweight='bold')
ax.text(60, 86, 'Мерить штангенциркулем, в мм. Заполнить жёлтые клетки.', ha='center', fontsize=8.5, color='#333')

ax.add_patch(Rectangle((3, 45), 56, 38, fill=False, ec='#94a3b8'))
ax.text(6, 79, '3) U-КРОНШТЕЙН (спереди)', fontsize=10, fontweight='bold', color='#1550aa')
ax.add_patch(Rectangle((16, 54), 4, 20, fc='#cbd5e1', ec='#64748b'))
ax.add_patch(Rectangle((36, 54), 4, 20, fc='#cbd5e1', ec='#64748b'))
ax.add_patch(Rectangle((16, 54), 24, 4, fc='#cbd5e1', ec='#64748b'))
for cx in (18, 38):
    for cy in (62, 70):
        ax.add_patch(Circle((cx, cy), 0.9, fill=False, ec='#333'))
dim(ax, 16, 77, 40, 77, 'K1 ширина')
dim(ax, 20, 59, 36, 59, 'K5 (внутри U)', off=-1.5, fs=7.5)
ax.text(42, 66, 'K2 толщина', color='#c00', fontsize=7.5, fontweight='bold')
ax.text(8, 50, 'K3 Ø отв · K4 шаг отв (на стенке)', fontsize=7, color='#555')

ax.add_patch(Rectangle((62, 45), 55, 38, fill=False, ec='#94a3b8'))
ax.text(65, 79, '4) БАЛКА 4×8×184', fontsize=10, fontweight='bold', color='#1a7a3a')
ax.add_patch(Rectangle((66, 62), 48, 5, fc='#94a3b8', ec='#64748b'))
for hx in (72, 84, 96, 108):
    ax.add_patch(Circle((hx, 64.5), 1.0, fill=False, ec='#333'))
dim(ax, 72, 59, 84, 59, 'Б3 шаг')
ax.text(66, 56, 'Б4 от края', color='#c00', fontsize=7.5, fontweight='bold')
ax.text(90, 71, 'Б2 Ø отв', color='#c00', fontsize=7.5, fontweight='bold')
ax.text(66, 74, 'Б1 сечение 4×8 (подтвердить)', fontsize=7, color='#555')

minitable(ax, 4, 40, 54, 'U-кронштейн', [
    ('K1', 'габарит Д×Ш×В'), ('K2', 'толщина стенки'), ('K3', 'Ø крепёжных отв.'),
    ('K4', 'шаг отверстий'), ('K5', 'внутр. ширина U')])
minitable(ax, 63, 40, 54, 'Балка', [
    ('Б1', 'сечение (4×8?)'), ('Б2', 'Ø отверстий'), ('Б3', 'шаг отверстий'),
    ('Б4', 'от края до 1-го отв.')])
figB.savefig('measure_B_frame.png', dpi=130, bbox_inches='tight', facecolor='white')
print('OK')
