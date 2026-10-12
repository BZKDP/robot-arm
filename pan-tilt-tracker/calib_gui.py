#!/usr/bin/env python
# -*- coding: utf-8 -*-
# calib_gui.py — desktopnoe okno kalibrovki pan-tilt (tkinter).
# PAN = ID2 (nizhniy), TILT = ID1 (verhniy). Most: sts_bridge na COM9.
import os, json, time
import tkinter as tk
from tkinter import ttk
import serial

PORT = "COM9"; BAUD = 115200
PAN_ID = 2; TILT_ID = 1
HERE = os.path.dirname(os.path.abspath(__file__))
CALIB = os.path.join(HERE, "calib.json")

# --- serial ---
ser = None
serr = ""
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.2)
    time.sleep(1.8)
    ser.reset_input_buffer()
except Exception as e:
    serr = str(e)

def send(line):
    if ser:
        try: ser.write((line + "\n").encode())
        except Exception: pass

def read_pos():
    if not ser: return None, None
    try:
        ser.reset_input_buffer()
        send("P")
        t0 = time.time()
        while time.time() - t0 < 0.5:
            ln = ser.readline().decode(errors="replace").strip()
            if ln.startswith("P "):
                _, p1, p2 = ln.split()
                return int(p1), int(p2)   # ID1(tilt), ID2(pan)
    except Exception:
        pass
    return None, None

# tekuschie celevye pozicii
pan = 2048; tilt = 2048
t1, p2 = read_pos()
if t1 is not None: tilt, pan = t1, p2

calib = {"pan": {"id": PAN_ID}, "tilt": {"id": TILT_ID}}
if os.path.exists(CALIB):
    try: calib.update(json.load(open(CALIB)))
    except Exception: pass

SPEED = 500  # medlenno i bezopasno

def clamp(v): return max(0, min(4095, int(v)))

def move(axis, delta):
    global pan, tilt
    if axis == "pan":
        pan = clamp(pan + delta); send("M %d %d %d" % (PAN_ID, pan, SPEED))
    else:
        tilt = clamp(tilt + delta); send("M %d %d %d" % (TILT_ID, tilt, SPEED))
    refresh()

def goto(axis, val):
    global pan, tilt
    if axis == "pan":
        pan = clamp(val); send("M %d %d %d" % (PAN_ID, pan, SPEED))
    else:
        tilt = clamp(val); send("M %d %d %d" % (TILT_ID, tilt, SPEED))
    refresh()

def mark(axis, key):
    calib[axis][key] = pan if axis == "pan" else tilt
    refresh()

def torque_off():
    send("T 1 0"); send("T 2 0")

def go_centers():
    if "center" in calib["pan"]:  goto("pan",  calib["pan"]["center"])
    if "center" in calib["tilt"]: goto("tilt", calib["tilt"]["center"])

def save():
    json.dump(calib, open(CALIB, "w"), indent=2)
    lbl_saved.config(text="Сохранено -> calib.json", foreground="#0a0")

# ---------- UI ----------
root = tk.Tk()
root.title("Pan-Tilt калибровка")
root.geometry("560x470")
root.configure(bg="#1e1e1e")
st = ttk.Style();
try: st.theme_use("clam")
except Exception: pass
st.configure("TButton", font=("Segoe UI", 11), padding=4)
st.configure("TLabel", background="#1e1e1e", foreground="#eee", font=("Segoe UI", 11))
st.configure("H.TLabel", font=("Segoe UI", 13, "bold"), foreground="#6cf")
st.configure("Big.TLabel", font=("Consolas", 22, "bold"), foreground="#fff", background="#1e1e1e")

top = ttk.Label(root, text=("ОШИБКА COM: " + serr) if serr else "Мост COM9 подключён",
                style="TLabel")
top.pack(pady=(8, 2))

posv = ttk.Label(root, text="", style="Big.TLabel")
posv.pack(pady=2)

def section(parent, title, axis):
    f = tk.Frame(parent, bg="#252526", bd=1, relief="solid")
    f.pack(fill="x", padx=12, pady=6)
    ttk.Label(f, text=title, style="H.TLabel", background="#252526").pack(anchor="w", padx=8, pady=(6,2))
    row = tk.Frame(f, bg="#252526"); row.pack(pady=4)
    for d in (-100, -25, -5, +5, +25, +100):
        ttk.Button(row, text=("%+d" % d), width=5,
                   command=lambda dd=d, a=axis: move(a, dd)).pack(side="left", padx=2)
    row2 = tk.Frame(f, bg="#252526"); row2.pack(pady=(2,8))
    ttk.Button(row2, text="◀ упор (min)", command=lambda a=axis: mark(a, "min")).pack(side="left", padx=3)
    ttk.Button(row2, text="● ЦЕНТР", command=lambda a=axis: mark(a, "center")).pack(side="left", padx=3)
    ttk.Button(row2, text="упор (max) ▶", command=lambda a=axis: mark(a, "max")).pack(side="left", padx=3)
    return f

section(root, "PAN — поворот (нижний, ID2):  a◀  ▶d", "pan")
section(root, "TILT — наклон (верхний, ID1):  s▼  ▲w", "tilt")

bottom = tk.Frame(root, bg="#1e1e1e"); bottom.pack(pady=6)
ttk.Button(bottom, text="Торк OFF", command=torque_off).pack(side="left", padx=4)
ttk.Button(bottom, text="В центры", command=go_centers).pack(side="left", padx=4)
ttk.Button(bottom, text="Сохранить", command=save).pack(side="left", padx=4)

lbl_saved = ttk.Label(root, text="", style="TLabel")
lbl_saved.pack()
lbl_cal = ttk.Label(root, text="", style="TLabel", font=("Consolas", 10))
lbl_cal.pack(pady=2)

def refresh():
    posv.config(text="PAN %4d    TILT %4d" % (pan, tilt))
    lbl_cal.config(text="pan=%s\ntilt=%s" % (
        {k: calib['pan'].get(k) for k in ('min','center','max')},
        {k: calib['tilt'].get(k) for k in ('min','center','max')}))

# klaviatura tozhe rabotaet
root.bind("d", lambda e: move("pan", +25)); root.bind("a", lambda e: move("pan", -25))
root.bind("w", lambda e: move("tilt", +25)); root.bind("s", lambda e: move("tilt", -25))

def poll():
    global pan, tilt
    t1, p2 = read_pos()
    if t1 is not None:
        pass  # ne perezapisyvaem cel, prosto zhivy
    root.after(1500, poll)

refresh()
root.after(1500, poll)
root.mainloop()
if ser: ser.close()
