#!/usr/bin/env python
# -*- coding: utf-8 -*-
# jog.py — zhivaya kalibrovka pan-tilt s klaviatury (Windows, msvcrt).
# PAN  = ID2 (nizhniy), TILT = ID1 (verhniy).
# Klavishi:
#   a / d   : PAN  -/+
#   s / w   : TILT -/+   (w = vverh)
#   [ / ]   : shag menshe / bolshe
#   z x c   : zapomnit PAN  min / max / center (tekuschuyu poziciyu)
#   v b n   : zapomnit TILT min / max / center
#   g       : poehat v zapisannye centry
#   p       : pokazat tekuschie pozicii (chtenie s serv)
#   o       : torque OFF oboih (svobodno rukoy povernut)
#   q       : sohranit calib.json i vyhod
import sys, time, json, os
import serial
try:
    import msvcrt
except ImportError:
    print("Tolko Windows"); sys.exit(1)

PORT = "COM9"; BAUD = 115200
PAN_ID = 2; TILT_ID = 1
HERE = os.path.dirname(os.path.abspath(__file__))
CALIB = os.path.join(HERE, "calib.json")

s = serial.Serial(PORT, BAUD, timeout=0.4)
time.sleep(1.8)
s.reset_input_buffer()

def send(line):
    s.write((line + "\n").encode())

def read_pos():
    s.reset_input_buffer()
    send("P")
    t0 = time.time()
    while time.time() - t0 < 1.0:
        ln = s.readline().decode(errors="replace").strip()
        if ln.startswith("P "):
            try:
                _, p1, p2 = ln.split()
                return int(p1), int(p2)  # ID1(tilt), ID2(pan)
            except: pass
    return None, None

def move(idn, pos, spd=1500):
    pos = max(0, min(4095, pos))
    send("M %d %d %d" % (idn, pos, spd))
    return pos

# nachalnye pozicii
t1, p2 = read_pos()
tilt = t1 if t1 is not None else 2048
pan  = p2 if p2 is not None else 2048
step = 30
calib = {"pan": {"id": PAN_ID}, "tilt": {"id": TILT_ID}}

def status():
    os.system("")  # vkl ANSI
    print("\r PAN(id2)=%4d  TILT(id1)=%4d  shag=%3d   pan:%s  tilt:%s        " % (
        pan, tilt, step,
        {k: calib['pan'].get(k) for k in ('min','center','max')},
        {k: calib['tilt'].get(k) for k in ('min','center','max')}), end="", flush=True)

print(__doc__)
print("Gotovo. Krutite. (q = sohranit i vyhod)\n")
status()

while True:
    ch = msvcrt.getch()
    try: c = ch.decode().lower()
    except: continue
    if c == 'q':
        break
    elif c == 'd': pan  = move(PAN_ID,  pan + step)
    elif c == 'a': pan  = move(PAN_ID,  pan - step)
    elif c == 'w': tilt = move(TILT_ID, tilt + step)
    elif c == 's': tilt = move(TILT_ID, tilt - step)
    elif c == ']': step = min(300, step + 10)
    elif c == '[': step = max(2, step - 10)
    elif c == 'z': calib['pan']['min'] = pan
    elif c == 'x': calib['pan']['max'] = pan
    elif c == 'c': calib['pan']['center'] = pan
    elif c == 'v': calib['tilt']['min'] = tilt
    elif c == 'b': calib['tilt']['max'] = tilt
    elif c == 'n': calib['tilt']['center'] = tilt
    elif c == 'g':
        if 'center' in calib['pan']:  pan  = move(PAN_ID,  calib['pan']['center'], 800)
        if 'center' in calib['tilt']: tilt = move(TILT_ID, calib['tilt']['center'], 800)
    elif c == 'o':
        send("T 1 0"); send("T 2 0")
    elif c == 'p':
        time.sleep(0.05); t1, p2 = read_pos()
        if t1 is not None: tilt, pan = t1, p2
    status()

with open(CALIB, "w") as f:
    json.dump(calib, f, indent=2)
s.close()
print("\n\nSohraneno -> %s" % CALIB)
print(json.dumps(calib, indent=2))
