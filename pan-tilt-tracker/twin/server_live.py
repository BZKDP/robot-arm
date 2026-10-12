#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Pan-Tilt sledyaschiy server (mini-PC): most serv (COM4) + kamera (COM3, JPEG-potok)
# + detektor lic (mediapipe) + P-regulyator + 3D-dvoynik + MJPEG-video. Dostup po LAN.
import os, json, time, threading, queue, math
from collections import deque
import http.server, socketserver
from urllib.parse import urlparse
import serial
import serial.tools.list_ports as list_ports

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
PORT_HTTP = 8200

YAW_ID  = CFG["tilt"]["id"]   # verhniy serv = povorot vlevo/vpravo
TILT_ID = CFG["pan"]["id"]    # nizhniy serv = naklon vverh/vniz
LIMITS = {}
for _ax in ("pan", "tilt"):
    a = CFG.get(_ax, {})
    if "min" in a and "max" in a: LIMITS[a["id"]] = (a["min"], a["max"])
def clamp_pos(idn, pos):
    if idn in LIMITS:
        lo, hi = LIMITS[idn]; pos = max(lo, min(hi, pos))
    return max(0, min(4095, int(pos)))

# avto-poisk portov po USB-chipu (ne zavisит ot nomera COM posle rebuta/pereezda)
BRIDGE_VID = 0x10C4   # CP210x = most serv
CAM_VID    = 0x1A86   # CH340  = ESP32-CAM
def find_port(vid, fallback=None):
    try:
        for x in list_ports.comports():
            if x.vid == vid: return x.device
    except Exception: pass
    return fallback

# zhivye parametry slezheniya (menyayutsya cherez /trackcfg bez perezapuska)
TRACK = {"kp_yaw":280,"kp_tilt":260,"deadzone":0.04,"yaw_sign":1,"tilt_sign":1,"max_step":60,"fps":20,"move_spd":1400,
         "search":1,"search_after":1.5,"search_step":26,"search_lo":700,"search_hi":3400,"search_tilt":2300,
         "patrol_ay":2596,"patrol_at":1960,"patrol_by":1541,"patrol_bt":2025,"patrol_spd":400,"patrol_step":18,
         "model":"yolo11s-pose.pt","imgsz":640,"conf":0.12,"coast":1.0,
         "backend":"dml","onnx":"yolo11s-pose.onnx","lead":0.12,"smooth":0.4,"enhance":1,
         "react":0.05,"smooth_fast":0.05,"err_fast":0.15,"acc_fast":80,
         "ff_tau":0.25,"ff_on":130,"kfov_y":1100,"kfov_t":760,"max_step_run":300,
         "lock_hold":1.5,"lock_dist":0.3,"lock_lost":2.0,
         "gesture":0,"nod_times":3,"nod_amp":140,"wave_cd":5.0,
         "wave_min":3,"wave_revs":2,"wave_amp":0.03,"wave_dx":0.006,"wave_conf":0.3,
         "rotate":0,"maxbox":0.82,"roll":0,"acc":40}
TRACK.update(CFG.get("track", {}))

state = {"raw": {1: None, 2: None}, "ok": False, "err": ""}
cmdq = queue.Queue()
def enqueue(line): cmdq.put(line)
camcmdq = queue.Queue()
def camcmd(code, val): camcmdq.put(bytes([code & 0xFF, int(val) & 0xFF]))

# ---------------- Serial bridge (COM4) ----------------
class SerialWorker(threading.Thread):
    daemon = True
    def run(self):
        ser = None
        while True:
            try:
                if ser is None:
                    port = find_port(BRIDGE_VID, CFG["port"])   # most serv po chipu CP210x
                    ser = serial.Serial(port, CFG["baud"], timeout=0.05)   # korotkiy timeout = M ne zhdyot P
                    time.sleep(1.8); ser.reset_input_buffer()
                    state["ok"] = True; state["err"] = ""
                try:
                    while True:
                        line = cmdq.get_nowait(); ser.write((line + "\n").encode()); time.sleep(0.004)
                except queue.Empty:
                    pass
                ser.reset_input_buffer(); ser.write(b"P\n"); t0 = time.time()
                while time.time() - t0 < 0.15:
                    ln = ser.readline().decode(errors="replace").strip()
                    if ln.startswith("P "):
                        try:
                            _, p1, p2 = ln.split(); state["raw"][1] = int(p1); state["raw"][2] = int(p2)
                        except Exception: pass
                        break
                time.sleep(0.008)   # P vsegda dochityvaem: svezhiy raw vazhnee 10ms (stale raw = polzuchie komandy)
            except Exception as e:
                state["ok"] = False; state["err"] = str(e)
                try: ser and ser.close()
                except Exception: pass
                ser = None; time.sleep(1.5)

# ---------------- Camera reader: USB-vebka (cv2) prioritet, ESP32-CAM serial fallback ----------------
class CameraReader(threading.Thread):
    daemon = True
    MAGIC = b"\xAA\x55\xAA\x55"
    def __init__(self):
        super().__init__(); self.jpeg = None; self.frame = None; self.fid = 0; self.lock = threading.Lock()
        self.fps = 0.0; self._n = 0; self._t = time.time(); self.ok = False; self.src = "none"
    def get(self):
        with self.lock: return self.jpeg
    def get_frame(self):   # syroy kadr dlya trekera (bez JPEG encode/decode petli = -25ms latencii)
        with self.lock: return self.frame, self.fid
    def _bump(self):
        self._n += 1
        if time.time() - self._t >= 1.0:
            self.fps = self._n / (time.time() - self._t); self._n = 0; self._t = time.time()
    def _find_webcam(self):
        try:
            import cv2
            for i in range(4):
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                good = False
                if cap.isOpened():
                    ok, fr = cap.read(); good = bool(ok) and fr is not None
                cap.release()
                if good: return i
        except Exception:
            pass
        return None
    def run(self):
        while True:
            idx = self._find_webcam()
            if idx is not None:
                self._run_webcam(idx)
            else:
                self._run_serial()
            self.ok = False; time.sleep(1.5)
    def _run_webcam(self, idx):
        try:
            import cv2
            self.src = "usb%d" % idx
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(CFG.get("usb_w", 1280)))
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(CFG.get("usb_h", 720)))
            cap.set(cv2.CAP_PROP_FPS, 30)
            state["err"] = ""; fails = 0
            while True:
                ok, fr = cap.read()
                if not ok or fr is None:
                    fails += 1
                    if fails > 30: break     # kamera propala -> vyhod na re-detekt
                    time.sleep(0.03); continue
                fails = 0
                ok2, enc = cv2.imencode(".jpg", fr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                with self.lock:
                    self.frame = fr; self.fid += 1   # syroy kadr trekeru SRAZU (jpeg tolko dlya saita)
                    if ok2: self.jpeg = enc.tobytes()
                self.ok = True; self._bump()
            cap.release()
        except Exception as e:
            state["err"] = "usbcam:" + str(e); time.sleep(0.5)
    def _run_serial(self):
        with self.lock: self.frame = None   # serial-put: syrogo kadra net, treker padaet na jpeg-dekod
        cport = find_port(CAM_VID, None)   # ESP32-CAM po chipu CH340 (bez fallbacka - net chipa = net kamery)
        if cport is None:
            self.src = "none"; state["err"] = "cam: net kamery (voткni USB-vebku ili ESP32-CAM)"; time.sleep(1.0); return
        self.src = "serial:%s" % cport; ser = None; buf = b""; cfg_n = 0; conn_t = 0.0
        try:
            ser = serial.Serial(cport, CFG["cam_baud"], timeout=0.2)
            ser.setDTR(False); ser.setRTS(True); time.sleep(0.2)
            ser.setRTS(False); time.sleep(0.2); ser.reset_input_buffer(); buf = b""
            cfg_n = 0; conn_t = time.time(); state["err"] = ""
            while True:
                if self.jpeg is not None and cfg_n < 3 and (time.time() - conn_t) > (2.0 + cfg_n):
                    if CFG.get("cam_quality") is not None: ser.write(bytes([0xF1, int(CFG["cam_quality"])])); time.sleep(0.05)
                    if CFG.get("cam_framesize") is not None: ser.write(bytes([0xF0, int(CFG["cam_framesize"])]))
                    cfg_n += 1
                try:
                    while True: ser.write(camcmdq.get_nowait()); time.sleep(0.02)
                except queue.Empty: pass
                buf += ser.read(32768)
                while True:
                    i = buf.find(self.MAGIC)
                    if i < 0:
                        if len(buf) > (1 << 20): buf = buf[-4:]
                        break
                    if len(buf) < i + 8: break
                    ln = int.from_bytes(buf[i+4:i+8], "little")
                    if ln <= 0 or ln > 300000: buf = buf[i+4:]; continue
                    if len(buf) < i + 8 + ln: break
                    jpg = buf[i+8:i+8+ln]; buf = buf[i+8+ln:]
                    if jpg[:2] == b"\xff\xd8":
                        with self.lock: self.jpeg = jpg
                        self.ok = True; self._bump()
        except Exception as e:
            state["err"] = "cam:" + str(e)
        finally:
            try: ser and ser.close()
            except Exception: pass

# ---------------- Face tracker (mediapipe + P-control) ----------------
class Tracker(threading.Thread):
    daemon = True
    def __init__(self, cam):
        super().__init__(); self.cam = cam; self.enabled = False
        self.annot = None; self.lock = threading.Lock()
        self.has_face = False; self.err = (0.0, 0.0); self.ready = False; self.note = ""
        self.cv2 = None; self.np = None; self.fd = None; self.dml = None; self.model = None
        self.loop_fps = 0.0; self._ln = 0; self._lt = 0.0
        self.pcx = None; self.pcy = None; self.pt = 0.0; self.vx = 0.0; self.vy = 0.0  # prediktor
        self.cvy = 0.0; self.cvt = 0.0; self._pry = None; self._prt2 = None; self._prtm = 0.0  # sobstv. skorost kamery (ed/s)
        self.shx = None; self.shy = None; self.clahe = None  # sglazhivanie + osvetlenie
        self.lock_pos = None; self.lock_t = 0.0  # lock-on na cheloveka
        self.wave = deque(); self.gesture_until = 0.0; self.last_gesture = 0.0  # zhesty
        self.nod_count = 0; self.mode = "init"; self.n_people = 0  # diagnostika
    def setup(self):
        import cv2, numpy as np
        self.cv2 = cv2; self.np = np
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        be = TRACK.get("backend", "dml")
        try:
            if be == "dml":
                from dml_pose import DmlPose
                for _att in range(8):   # posle boota iGPU mozhet byt eshchyo ne gotov -> zhdyom DML, ne padaem na CPU
                    self.dml = DmlPose(TRACK.get("onnx", "yolo11s-pose.onnx"),
                                       imgsz=TRACK.get("imgsz", 640), conf=TRACK.get("conf", 0.10))
                    if "Dml" in self.dml.provider: break
                    time.sleep(5)
                self.dml.detect(np.zeros((480, 640, 3), np.uint8))  # warmup iGPU
                self.note = "DML/%s %s" % (self.dml.provider.replace("ExecutionProvider", ""),
                                           TRACK.get("onnx", "yolo11s-pose.onnx"))
            else:
                from ultralytics import YOLO
                import torch
                try: torch.set_num_threads(8)
                except Exception: pass
                self.model = YOLO(TRACK.get("model", "yolo11s-pose.pt"))
                self.model.predict(np.zeros((320, 320, 3), np.uint8), imgsz=320, verbose=False)
                self.note = "yolo " + TRACK.get("model", "yolo11s-pose.pt")
        except Exception as e:
            self.note = "BACKEND FAIL: " + str(e)
        self.ready = True
    def get_annot(self):
        with self.lock: return self.annot
    def do_nod(self):   # otvet na vzmah: STOP slezheniya -> ROVNO kivnut N raz -> vernut slezhenie
        base = state["raw"][TILT_ID]
        if base is None: self.gesture_until = 0.0; return
        self.nod_count += 1
        T = TRACK; times = int(T.get("nod_times", 3)); amp = int(T.get("nod_amp", 182))
        lo, hi = LIMITS.get(TILT_ID, (0, 4095))
        c = max(lo + amp, min(hi - amp, base))   # centr tak, chtob kivok byl ROVNYY (bez upora v limit)
        down = clamp_pos(TILT_ID, c + amp); up = clamp_pos(TILT_ID, c - amp)
        self.last_gesture = time.time()
        def go(target, spd=2200, tol=22, tmo=0.9):   # edem do pozicii PO FEEDBACK -> kazhdyy kivok ODINAKOVYY
            self.gesture_until = time.time() + 2.0     # rolling: slezhenie zablokirovano vsyo vremya kivka
            enqueue("M %d %d %d" % (TILT_ID, target, spd)); tw = time.time()
            while time.time() - tw < tmo:
                if not self.enabled: return False       # vyklyuchili slezhenie -> preryvaem kivok
                cur = state["raw"][TILT_ID]
                if cur is not None and abs(cur - target) <= tol: break
                time.sleep(0.04)
            return self.enabled
        for _ in range(times):
            if not go(down): break    # vniz do tochki (po feedback)
            if not go(up): break      # vverh do tochki
        if self.enabled: go(base, spd=1600)   # vernut na ishodnuyu
        self.gesture_until = time.time() + 0.15   # totchas vozobnovit slezhenie
    def _go(self, idn, target, spd, tol=25, tmo=1.0):   # dvizhenie do pozicii po feedback (dlya golosa, bez enabled-gate)
        target = clamp_pos(idn, target)
        self.gesture_until = time.time() + 2.0
        enqueue("M %d %d %d 40" % (idn, target, spd)); tw = time.time()
        while time.time() - tw < tmo:
            cur = state["raw"][idn]
            if cur is not None and abs(cur - target) <= tol: break
            time.sleep(0.04)
    def voice_nod(self, times=2, amp=180):     # golos "Privet" -> kivok N raz (naklon vniz-vverh)
        base = state["raw"][TILT_ID]
        if base is None: return
        lo, hi = LIMITS.get(TILT_ID, (0, 4095)); c = max(lo+amp, min(hi-amp, base))
        self.last_gesture = time.time()
        for _ in range(times):
            self._go(TILT_ID, c+amp, 2600); self._go(TILT_ID, c-amp, 2600)
        self._go(TILT_ID, base, 1600); self.gesture_until = time.time() + 0.15
    def voice_shake(self, times=2, amp=200):   # golos "Net" -> motanie vlevo-vpravo N raz (povorot)
        base = state["raw"][YAW_ID]
        if base is None: return
        lo, hi = LIMITS.get(YAW_ID, (0, 4095)); c = max(lo+amp, min(hi-amp, base))
        self.last_gesture = time.time()
        for _ in range(times):
            self._go(YAW_ID, c-amp, 2800); self._go(YAW_ID, c+amp, 2800)
        self._go(YAW_ID, base, 1800); self.gesture_until = time.time() + 0.15
    def voice_circle(self, amp=260, steps=20, loops=1):   # golos "Ey" -> risuet KRUG (yaw+tilt po okruzhnosti)
        cy = state["raw"][YAW_ID]; ct = state["raw"][TILT_ID]
        if cy is None or ct is None: return
        loY, hiY = LIMITS.get(YAW_ID, (0, 4095)); loT, hiT = LIMITS.get(TILT_ID, (0, 4095))
        cy = max(loY+amp, min(hiY-amp, cy)); ct = max(loT+amp, min(hiT-amp, ct))   # centr chtob krug v limitah
        self.last_gesture = time.time()
        for k in range(steps*loops + 1):
            th = 2*math.pi*k/steps
            y = int(cy + amp*math.cos(th)); t = int(ct + amp*math.sin(th))
            self.gesture_until = time.time() + 2.0
            enqueue("M %d %d 3000 25" % (YAW_ID, clamp_pos(YAW_ID, y)))    # nepreryvno -> plavnyy krug
            enqueue("M %d %d 3000 25" % (TILT_ID, clamp_pos(TILT_ID, t)))
            time.sleep(0.11)
        self._go(YAW_ID, cy, 1800); self._go(TILT_ID, ct, 1800)   # vernut v centr
        self.gesture_until = time.time() + 0.15
    def voice_sad(self, drop=380, hold=2.0):   # golos "Poka" -> grustno opustit golovu na 2 sek
        base = state["raw"][TILT_ID]
        if base is None: return
        lo, hi = LIMITS.get(TILT_ID, (0, 4095))
        down = clamp_pos(TILT_ID, min(hi, base + drop))   # id2 bolshe = vniz (opustit golovu)
        self.last_gesture = time.time()
        self.gesture_until = time.time() + hold + 4.0
        enqueue("M %d %d 700 60" % (TILT_ID, down))   # MEDLENNO vniz (spd 700) = grustno
        time.sleep(1.4)
        self.gesture_until = time.time() + hold + 0.6
        time.sleep(hold)                              # visit opushchennaya 2 sek
        self._go(TILT_ID, base, 1400)                 # podnyat obratno
        self.gesture_until = time.time() + 0.15
    def run(self):
        self.setup()
        cv2, np = self.cv2, self.np
        last_face = 0.0; sdir = 1; last_pos = None
        while True:
            t0 = time.time(); T = TRACK
            period = 1.0 / max(5, T.get("fps", 20))
            fr, fid = self.cam.get_frame()
            if fr is not None:
                if fid == getattr(self, "_lfid", -1):   # zhdyom SVEZHIY kadr, dubl ne zhzhom na GPU
                    time.sleep(0.004); continue
                self._lfid = fid; frame = fr.copy()
            else:   # fallback ESP32-CAM serial: kadr tolko kak jpeg
                jpg = self.cam.get()
                if jpg is None: time.sleep(0.03); continue
                frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                if frame is None: time.sleep(0.01); continue
            rot = T.get("rotate", 0)   # gruboe: kamera smontirovana bokom/vverh nogami
            if rot == 90: frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif rot == 180: frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif rot == 270: frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            roll = T.get("roll", 0)   # tonkaya korrekciya KRENA (gradusy) -> chelovek vertikalno, yolo lovit stabilno
            if roll:
                hh0, ww0 = frame.shape[:2]
                Mrl = cv2.getRotationMatrix2D((ww0/2.0, hh0/2.0), float(roll), 1.0)
                frame = cv2.warpAffine(frame, Mrl, (ww0, hh0), borderMode=cv2.BORDER_REPLICATE)
            if T.get("enhance", 1) and self.clahe is not None:   # ADAPTIVNOE osvetlenie: tolko temnye kadry
                if frame[::8, ::8].mean() < T.get("enhance_below", 115):   # deshyovaya otsenka (bez LAB kazhdyi kadr)
                    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                    lab[:, :, 0] = self.clahe.apply(lab[:, :, 0])
                    frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            h, w = frame.shape[:2]; face = None
            dets = []
            if self.dml is not None:
                dets = self.dml.detect(frame, conf=TRACK.get("conf", 0.10))
            elif self.model is not None:
                r = self.model.track(frame, persist=True, classes=[0], conf=TRACK.get("conf", 0.10),
                                     imgsz=TRACK.get("imgsz", 640), verbose=False)[0]
                if r.boxes is not None:
                    for i, bx in enumerate(r.boxes.xyxy.tolist()):
                        kp = []
                        if r.keypoints is not None and r.keypoints.xy is not None and len(r.keypoints.xy) > i:
                            xy = r.keypoints.xy[i].tolist()
                            kc = r.keypoints.conf[i].tolist() if r.keypoints.conf is not None else [1.0]*len(xy)
                            kp = [(xy[j][0], xy[j][1], kc[j]) for j in range(len(xy))]
                        dets.append({"box": tuple(bx), "conf": 1.0, "kp": kp})
            area = lambda d: (d["box"][2]-d["box"][0])*(d["box"][3]-d["box"][1])
            if dets:   # otsech fullframe-lozhnye boksy (tekstura steny/shtor) + ostavit do 4 chelovek (krupneyshie)
                fa = float(w * h)
                dets = [d for d in dets if area(d) < TRACK.get("maxbox", 0.82) * fa]
                dets = sorted(dets, key=area, reverse=True)[:4]
            self.n_people = len(dets)
            if dets:
                def head_of(d):
                    x1, y1, x2, y2 = d["box"]
                    # golova = REALNYE tochki nos/glaza/ushi (rabotaet v lyuboy poze: stoya/lyozha)
                    pts = [(p[0], p[1]) for k, p in enumerate(d["kp"])
                           if k in (0, 1, 2, 3, 4) and p[2] > 0.4 and (p[0] or p[1])]
                    if pts:
                        return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))
                    return ((x1+x2)/2, y1 + (y2-y1)*0.14)   # fallback: verh boksa
                tnow = time.time(); cand = None
                # STICKY-LOCK: vedyom ODNOGO poka ne propadyot (>lock_lost sek), potom blizhaishego
                if self.lock_pos is not None:
                    lx, ly = self.lock_pos; best = 1e9; bd = None
                    for d in dets:
                        hh = head_of(d); dist = ((hh[0]/w-lx)**2 + (hh[1]/h-ly)**2)**0.5
                        if dist < best: best = dist; bd = (d, hh)
                    if best <= T.get("lock_dist", 0.35):
                        cand = bd; self.lock_t = tnow                # nash chelovek viden -> vedyom
                    elif (tnow - self.lock_t) >= T.get("lock_lost", 2.0):
                        cand = bd; self.lock_t = tnow                # propal NADOLGO -> perehod na blizhaishego
                    # inache: kratkiy propusk (<lock_lost) -> cand=None -> koasting, NE pereklyuchaemsya
                else:
                    d0 = max(dets, key=area); cand = (d0, head_of(d0)); self.lock_t = tnow  # net locka -> krupneyshiy
                PAL = [(0,170,255), (80,220,80), (255,190,0), (230,90,255)]   # cveta raznyh lyudey (BGR)
                tgt = cand[0] if cand else None
                for idx, dd in enumerate(dets):   # VSE boksy raznym cvetom, cel - tolstyy + "CEL"
                    b = dd["box"]; col = PAL[idx % 4]
                    cv2.rectangle(frame, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), col, 3 if dd is tgt else 1)
                    if dd is tgt:
                        cv2.putText(frame, "CEL", (int(b[0])+3, int(b[1])+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
                if cand is not None:
                    d, (hx, hy) = cand
                    cx = hx/w; cy = hy/h; face = (cx, cy)
                    if self.lock_pos is None: self.lock_pos = (cx, cy)
                    else: self.lock_pos = (0.5*self.lock_pos[0]+0.5*cx, 0.5*self.lock_pos[1]+0.5*cy)  # EMA -> ne prygaet na soseda
                    self.lock_t = tnow
                    cv2.circle(frame, (int(hx), int(hy)), 6, (0, 0, 255), -1)
                    # --- ZHEST: vzmah rukoy -> kivok ---
                    if self.enabled and TRACK.get("gesture", 0) and len(d["kp"]) >= 11:
                        kp = d["kp"]; wc = TRACK.get("wave_conf", 0.3)
                        shy = [kp[k][1] for k in (5, 6) if kp[k][2] > wc]
                        shy = min(shy) if shy else None
                        wr = None
                        for k in (9, 10):
                            if kp[k][2] > wc and shy is not None and kp[k][1] < shy:
                                wr = kp[k]; break
                        if wr is not None: self.wave.append((tnow, wr[0] / w))
                        while self.wave and tnow - self.wave[0][0] > 1.6: self.wave.popleft()
                        if (tnow > self.gesture_until and tnow - self.last_gesture > TRACK.get("wave_cd", 5.0)
                                and len(self.wave) >= TRACK.get("wave_min", 3)):
                            xs = [x for _, x in self.wave]; revs = 0; prev = 0; dxth = TRACK.get("wave_dx", 0.006)
                            for i in range(1, len(xs)):
                                dx = xs[i] - xs[i-1]
                                if abs(dx) < dxth: continue
                                s = 1 if dx > 0 else -1
                                if prev and s != prev: revs += 1
                                prev = s
                            if revs >= TRACK.get("wave_revs", 2) and (max(xs) - min(xs)) > TRACK.get("wave_amp", 0.03):
                                self.wave.clear()
                                self.gesture_until = tnow + 4.0
                                self.last_gesture = tnow
                                threading.Thread(target=self.do_nod, daemon=True).start()
            cv2.line(frame, (w//2, 0), (w//2, h), (90, 90, 90), 1)
            cv2.line(frame, (0, h//2), (w, h//2), (90, 90, 90), 1)
            dz = T.get("deadzone", 0.05); mx = T.get("max_step", 45); now = time.time(); mode = "manual"
            # sobstvennaya skorost kamery (ed/s) iz feedback pozitsiy - dlya ego-kompensacii uprezhdeniya
            ry = state["raw"][YAW_ID]; rt2 = state["raw"][TILT_ID]
            if ry is not None and self._pry is not None and 0.01 < (now - self._prtm) < 0.5:
                dtc = now - self._prtm
                self.cvy = 0.5*self.cvy + 0.5*((ry - self._pry)/dtc)
                if rt2 is not None and self._prt2 is not None:
                    self.cvt = 0.5*self.cvt + 0.5*((rt2 - self._prt2)/dtc)
            if ry is not None: self._pry = ry; self._prt2 = rt2; self._prtm = now
            gesturing = now < self.gesture_until   # vo vremya kivka ne dvigaem naklon slezheniem
            if face:
                last_face = now; last_pos = face; self.has_face = True
                sm = T.get("smooth", 0.4); lead = T.get("lead", 0.0)   # EMA-sglazhivanie + Kalman-lite uprezhdenie
                if self.shx is None: self.shx, self.shy = face[0], face[1]
                # ADAPTIVNOE sglazhivanie (1-euro): stoish -> sglazhivaem (bez drozhi);
                # NACHAL dvigatsya -> sglazhivanie pochti otklyuchaetsya = MGNOVENNAYA reakciya
                mv = ((face[0]-self.shx)**2 + (face[1]-self.shy)**2) ** 0.5   # skachok tseli za kadr
                react = T.get("react", 0.05)
                if mv > react:
                    f = min(1.0, (mv - react) / max(1e-6, react))            # 0..1 = naskolko rezko poshyol
                    sm = sm*(1.0-f) + T.get("smooth_fast", 0.05)*f
                self.shx = sm*self.shx + (1-sm)*face[0]; self.shy = sm*self.shy + (1-sm)*face[1]
                if self.pcx is not None:
                    dt = max(1e-2, min(0.4, now - self.pt)); a = 0.45
                    self.vx = a*((self.shx-self.pcx)/dt) + (1-a)*self.vx
                    self.vy = a*((self.shy-self.pcy)/dt) + (1-a)*self.vy
                self.pcx, self.pcy, self.pt = self.shx, self.shy, now
                px = min(1.0, max(0.0, self.shx + self.vx*lead)); py = min(1.0, max(0.0, self.shy + self.vy*lead))
                ex = px - 0.5; ey = py - 0.5; self.err = (float(ex), float(ey))
                if self.enabled and not gesturing:
                    mode = "AUTO"
                    spd = T.get("move_spd", 1200); acc = int(T.get("acc", 40))   # acc = plavnost razgona (trapeciya)
                    if max(abs(ex), abs(ey)) > T.get("err_fast", 0.15):
                        acc = int(T.get("acc_fast", 80))   # bolshaya oshibka -> REZKIY start (dognat cheloveka)
                    # EGO-KOMPENSIROVANNOE uprezhdenie: istinnaya skorost celi (ed/s) =
                    # skorost v KADRE * kfov + SOBSTVENNAYA skorost kamery. Kamera gonitsya -> cel "plyvet
                    # nazad" v kadre -> chleny vzaimno gasyatsya = fantomnoy pogoni NET. Stoish: oba ~0.
                    tau = T.get("ff_tau", 0.25); pv_on = T.get("ff_on", 130); mxr = T.get("max_step_run", 300)
                    pvy = T.get("yaw_sign",1) * self.vx * T.get("kfov_y", 1100) + self.cvy
                    pvt = T.get("tilt_sign",1) * self.vy * T.get("kfov_t", 760) + self.cvt
                    runx = abs(pvy) > pv_on; runy = abs(pvt) > pv_on   # vorota: melkiy shum ne budit servu
                    if (abs(ex) > dz or runx) and state["raw"][YAW_ID] is not None:
                        step = T.get("yaw_sign",1) * ex * T.get("kp_yaw",170) + (pvy * tau if runx else 0.0)
                        cap = mxr if runx else mx; step = max(-cap, min(cap, step))
                        enqueue("M %d %d %d %d" % (YAW_ID, clamp_pos(YAW_ID, state["raw"][YAW_ID] + step), spd, acc))
                    if (abs(ey) > dz or runy) and state["raw"][TILT_ID] is not None:
                        step = T.get("tilt_sign",1) * ey * T.get("kp_tilt",150) + (pvt * tau if runy else 0.0)
                        cap = mxr if runy else mx; step = max(-cap, min(cap, step))
                        enqueue("M %d %d %d %d" % (TILT_ID, clamp_pos(TILT_ID, state["raw"][TILT_ID] + step), spd, acc))
            elif (now - last_face) <= T.get("coast", 1.0) and last_pos is not None:
                self.has_face = True   # koasting: kratkiy propusk detekta - derzhim, ne ischem
                cv2.circle(frame, (int(last_pos[0]*w), int(last_pos[1]*h)), 7, (0, 150, 255), 2)
                if self.enabled: mode = "AUTO~"
            else:
                self.has_face = False; self.shx = None; self.lock_pos = None   # sbros pri polnoy potere
                if self.enabled and not gesturing and T.get("search",1) and (now - last_face) > T.get("search_after",1.5):
                    mode = "PATRUL"   # nikogo net -> patrulirovanie mezhdu tochkami A i B
                    ay = T.get("patrol_ay", 2596); by = T.get("patrol_by", 1541)   # yaw A i B
                    at = T.get("patrol_at", 1960); bt = T.get("patrol_bt", 2025)   # tilt A i B
                    lo, hi = min(ay, by), max(ay, by); sp = int(T.get("patrol_spd", 400))
                    cur = state["raw"][YAW_ID]
                    if cur is not None:
                        nxt = cur + sdir * int(T.get("patrol_step", 18))
                        if nxt >= hi: sdir = -1; nxt = hi
                        elif nxt <= lo: sdir = 1; nxt = lo
                        enqueue("M %d %d %d 30" % (YAW_ID, clamp_pos(YAW_ID, nxt), sp))   # acc 30 = plavno
                        frac = (nxt - ay) / float(by - ay) if by != ay else 0.0   # naklon interpol A->B po yaw
                        frac = max(0.0, min(1.0, frac)); ttgt = int(at + frac * (bt - at))
                        tc = state["raw"][TILT_ID]
                        if tc is not None and abs(tc - ttgt) > 18:
                            enqueue("M %d %d %d 30" % (TILT_ID, clamp_pos(TILT_ID, ttgt), sp))
            tag = ("KIVOK :)" if gesturing else mode) + ((" | vedu 1 iz %d" % self.n_people) if self.has_face else " | net lica") + ((" (+%d)" % (self.n_people-1)) if (self.has_face and self.n_people > 1) else "")
            self.mode = "KIVOK" if gesturing else mode
            cv2.putText(frame, tag, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0,255,0) if self.has_face else (180,180,180), 1)
            ok, enc = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                with self.lock: self.annot = enc.tobytes()
            self._ln += 1
            if t0 - self._lt >= 1.0:
                self.loop_fps = self._ln / (t0 - self._lt) if self._lt else 0.0
                self._ln = 0; self._lt = t0
            dt = time.time() - t0
            if dt < period: time.sleep(period - dt)

# ---------------- Voice: mic kamery + Vosk RU -> "privet"=kivok, "net"=motanie ----------------
class VoiceListener(threading.Thread):
    daemon = True
    def __init__(self, tracker):
        super().__init__(); self.tk = tracker; self.status = "init"; self.last_cmd = ""; self.level = 0.0; self.heard = ""
    def run(self):
        model_dir = CFG.get("vosk_model", r"C:\pantilt\vosk-model-small-ru-0.22")
        try:
            import sounddevice as sd, vosk, queue as _q, json as _json, numpy as _np
        except Exception as e:
            self.status = "net libs: %s" % e; return
        if not os.path.isdir(model_dir):
            self.status = "net modeli vosk"; return
        try:
            vosk.SetLogLevel(-1)
            model = vosk.Model(model_dir)
            rec = vosk.KaldiRecognizer(model, 16000)   # svobodnoe raspoznavanie (nadyozhnee dlya keyword)
        except Exception as e:
            self.status = "vosk fail: %s" % e; return
        dev = None; best_rms = -1.0   # vybrat RABOCHIY mic kamery (mnogo variantov MME/DS/WASAPI, chast myortvye)
        try:
            for i, d in enumerate(sd.query_devices()):
                if d["max_input_channels"] <= 0 or "Camera" not in d["name"]: continue
                try:
                    smp = sd.rec(int(0.4*16000), samplerate=16000, channels=1, dtype="int16", device=i); sd.wait()
                    rms = float(_np.sqrt(_np.mean(smp.astype(_np.float32)**2)))   # smp - ne rec! (rec = vosk raspoznavatel)
                    if rms > best_rms: best_rms = rms; dev = i
                except Exception: continue
        except Exception: pass
        q = _q.Queue()
        def cb(indata, frames, tinfo, status): q.put(indata.copy())   # numpy int16 (kak sd.rec chto srabotal)
        HELLO = "привет"   # privet
        NO = "нет"                        # net
        HEY = "эй"                        # ey -> krug
        BYE = "пока"                      # poka -> grustno opustit golovu
        last = 0.0
        while True:
            try:
                with sd.InputStream(samplerate=16000, blocksize=4000, dtype="int16",
                                    channels=1, device=dev, callback=cb):
                    self.status = "slushayu (dev %s)" % dev
                    while True:
                        a = q.get().reshape(-1)
                        self.level = min(100.0, float(_np.sqrt(_np.mean(a.astype(_np.float32)**2))) / 100.0)
                        g = int(CFG.get("mic_gain", 3))   # usilenie tihogo mic kamery pered vosk
                        data = (_np.clip(a.astype(_np.int32) * g, -32767, 32767).astype(_np.int16)).tobytes()
                        if rec.AcceptWaveform(data):
                            txt = _json.loads(rec.Result()).get("text", "")
                        else:
                            txt = _json.loads(rec.PartialResult()).get("partial", "")
                        if not txt: continue
                        self.heard = txt[-40:]   # chto raspoznalos (dlya otladki na sayte)
                        now = time.time()
                        if now - last < 3.0: continue    # kuldaun mezhdu komandami
                        if HELLO in txt:
                            last = now; self.last_cmd = "privet->kivok"
                            threading.Thread(target=self.tk.voice_nod, daemon=True).start()
                        elif NO in txt:
                            last = now; self.last_cmd = "net->motanie"
                            threading.Thread(target=self.tk.voice_shake, daemon=True).start()
                        elif HEY in txt:
                            last = now; self.last_cmd = "ey->krug"
                            threading.Thread(target=self.tk.voice_circle, daemon=True).start()
                        elif BYE in txt:
                            last = now; self.last_cmd = "poka->grust"
                            threading.Thread(target=self.tk.voice_sad, daemon=True).start()
            except Exception as e:
                self.status = "audio fail: %s" % e; time.sleep(3.0)

# ---------------- HTTP ----------------
cam = CameraReader(); tracker = Tracker(cam); voice = VoiceListener(tracker)
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=os.path.join(HERE, "static"), **k)
    def log_message(self, *a): pass
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()
    def _json(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/config": return self._json(CFG)
        if p == "/pos":
            return self._json({"raw": state["raw"], "ok": state["ok"], "err": state["err"],
                               "cam_fps": round(cam.fps, 1), "cam_ok": cam.ok, "cam_src": cam.src, "loop_fps": round(tracker.loop_fps, 1),
                               "track": tracker.enabled, "face": tracker.has_face,
                               "gesturing": time.time() < tracker.gesture_until, "nods": tracker.nod_count,
                               "wave_n": len(tracker.wave), "mode": tracker.mode, "people": tracker.n_people,
                               "voice": voice.status, "voice_cmd": voice.last_cmd,
                               "mic_level": round(voice.level, 1), "voice_heard": voice.heard,
                               "err_xy": [round(float(tracker.err[0]),3), round(float(tracker.err[1]),3)], "note": tracker.note})
        if p == "/video":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                while True:
                    jpg = tracker.get_annot() or cam.get()
                    if jpg:
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " +
                                         str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                    time.sleep(0.045)
            except Exception: pass
            return
        if p == "/" or p == "": self.path = "/index.html"
        return super().do_GET()
    def do_POST(self):
        p = urlparse(self.path).path; n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        if p == "/move":
            idn = int(body["id"]); enqueue("M %d %d %d" % (idn, clamp_pos(idn, int(body["pos"])), int(body.get("spd", 600))))
            return self._json({"ok": True})
        if p == "/stop": enqueue("H %d" % int(body["id"])); return self._json({"ok": True})
        if p == "/torque":
            en = 1 if body.get("on") else 0; enqueue("T 1 %d" % en); enqueue("T 2 %d" % en); return self._json({"ok": True})
        if p == "/nod":   # test: prinuditelno trignut kivok (dlya proverki)
            threading.Thread(target=tracker.do_nod, daemon=True).start(); return self._json({"ok": True})
        if p == "/pick":  # klik po video -> vybrat cheloveka (lock na blizhaishego k tochke x,y 0..1)
            tracker.lock_pos = (float(body.get("x", 0.5)), float(body.get("y", 0.5)))
            tracker.lock_t = time.time(); return self._json({"ok": True})
        if p == "/track":
            tracker.enabled = bool(body.get("on"))
            if not tracker.enabled: tracker.gesture_until = 0.0   # ruchnoe upravlenie -> srazu gasim kivok/gesturing
            return self._json({"ok": True, "track": tracker.enabled})
        if p == "/trackcfg":
            for k, v in body.items():
                if k in TRACK: TRACK[k] = v
            return self._json({"ok": True, "track_cfg": TRACK})
        if p == "/cam":
            if "framesize" in body: camcmd(0xF0, int(body["framesize"]))
            if "quality" in body: camcmd(0xF1, int(body["quality"]))
            return self._json({"ok": True})
        return self._json({"err": "unknown"}, 404)

if __name__ == "__main__":
    SerialWorker().start(); cam.start(); tracker.start(); voice.start()
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(("0.0.0.0", PORT_HTTP), H)
    print("Pan-Tilt tracker: http://0.0.0.0:%d  bridge=%s cam=%s" % (PORT_HTTP, CFG["port"], CFG["cam_port"]))
    srv.serve_forever()
