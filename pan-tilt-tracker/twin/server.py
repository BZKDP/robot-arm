#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Pan-Tilt sledyaschiy server (mini-PC): most serv (COM4) + kamera (COM3, JPEG-potok)
# + detektor lic (mediapipe) + P-regulyator + 3D-dvoynik + MJPEG-video. Dostup po LAN.
import os, json, time, threading, queue
import http.server, socketserver
from urllib.parse import urlparse
import serial

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

# zhivye parametry slezheniya (menyayutsya cherez /trackcfg bez perezapuska)
TRACK = {"kp_yaw":280,"kp_tilt":260,"deadzone":0.04,"yaw_sign":1,"tilt_sign":1,"max_step":60,"fps":20,"move_spd":1400,
         "search":1,"search_after":1.5,"search_step":22,"search_lo":1300,"search_hi":2800,"search_tilt":2300,
         "model":"yolo11s-pose.pt","imgsz":640,"conf":0.12,"coast":1.0,
         "backend":"dml","onnx":"yolo11s-pose.onnx","lead":0.12,"smooth":0.4,"enhance":1,
         "lock_hold":1.5,"lock_dist":0.35}
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
                    ser = serial.Serial(CFG["port"], CFG["baud"], timeout=0.25)
                    time.sleep(1.8); ser.reset_input_buffer()
                    state["ok"] = True; state["err"] = ""
                try:
                    while True:
                        line = cmdq.get_nowait(); ser.write((line + "\n").encode()); time.sleep(0.02)
                except queue.Empty:
                    pass
                ser.reset_input_buffer(); ser.write(b"P\n"); t0 = time.time()
                while time.time() - t0 < 0.4:
                    ln = ser.readline().decode(errors="replace").strip()
                    if ln.startswith("P "):
                        try:
                            _, p1, p2 = ln.split(); state["raw"][1] = int(p1); state["raw"][2] = int(p2)
                        except Exception: pass
                        break
                time.sleep(0.03)
            except Exception as e:
                state["ok"] = False; state["err"] = str(e)
                try: ser and ser.close()
                except Exception: pass
                ser = None; time.sleep(1.5)

# ---------------- Camera reader (COM3, MAGIC+len+JPEG) ----------------
class CameraReader(threading.Thread):
    daemon = True
    MAGIC = b"\xAA\x55\xAA\x55"
    def __init__(self):
        super().__init__(); self.jpeg = None; self.lock = threading.Lock()
        self.fps = 0.0; self._n = 0; self._t = time.time(); self.ok = False
    def get(self):
        with self.lock: return self.jpeg
    def run(self):
        ser = None; buf = b""; cfg_n = 0; conn_t = 0.0
        while True:
            try:
                if ser is None:
                    ser = serial.Serial(CFG["cam_port"], CFG["cam_baud"], timeout=0.2)
                    ser.setDTR(False); ser.setRTS(True); time.sleep(0.2)
                    ser.setRTS(False); time.sleep(0.2); ser.reset_input_buffer(); buf = b""
                    cfg_n = 0; conn_t = time.time()
                # nastroyki kamery (quality/framesize) posle zagruzki, 3 raza dlya nadyozhnosti
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
                        self.ok = True; self._n += 1
                        if time.time() - self._t >= 1.0:
                            self.fps = self._n / (time.time() - self._t); self._n = 0; self._t = time.time()
            except Exception as e:
                state["err"] = "cam:" + str(e)
                try: ser and ser.close()
                except Exception: pass
                ser = None; time.sleep(1.0)

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
        self.shx = None; self.shy = None; self.clahe = None  # sglazhivanie + osvetlenie
        self.lock_pos = None; self.lock_t = 0.0  # lock-on na cheloveka
    def setup(self):
        import cv2, numpy as np
        self.cv2 = cv2; self.np = np
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        be = TRACK.get("backend", "dml")
        try:
            if be == "dml":
                from dml_pose import DmlPose
                self.dml = DmlPose(TRACK.get("onnx", "yolo11s-pose.onnx"),
                                   imgsz=TRACK.get("imgsz", 640), conf=TRACK.get("conf", 0.10))
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
    def run(self):
        self.setup()
        cv2, np = self.cv2, self.np
        last_face = 0.0; sdir = 1; last_pos = None
        while True:
            t0 = time.time(); T = TRACK
            period = 1.0 / max(5, T.get("fps", 20))
            jpg = self.cam.get()
            if jpg is None: time.sleep(0.03); continue
            frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
            if frame is None: time.sleep(0.01); continue
            if T.get("enhance", 1) and self.clahe is not None:   # ADAPTIVNOE osvetlenie: tolko temnye kadry
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                if lab[:, :, 0].mean() < T.get("enhance_below", 115):
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
            if dets:
                def head_of(d):
                    x1, y1, x2, y2 = d["box"]; bx = (x1+x2)/2; by = y1 + (y2-y1)*0.14
                    pts = [(p[0], p[1]) for k, p in enumerate(d["kp"])
                           if k in (0,1,2,3,4) and p[2] > 0.5 and (p[0] or p[1]) and p[1] < y1+(y2-y1)*0.5]
                    if pts:
                        return (0.5*bx + 0.5*sum(p[0] for p in pts)/len(pts), 0.5*by + 0.5*sum(p[1] for p in pts)/len(pts))
                    return (bx, by)
                area = lambda d: (d["box"][2]-d["box"][0])*(d["box"][3]-d["box"][1])
                tnow = time.time(); cand = None
                if self.lock_pos is not None and (tnow - self.lock_t) < T.get("lock_hold", 1.5):
                    lx, ly = self.lock_pos; best = 1e9
                    for d in dets:
                        hh = head_of(d); dist = ((hh[0]/w-lx)**2 + (hh[1]/h-ly)**2)**0.5
                        if dist < best: best = dist; cand = (d, hh)
                    if best > T.get("lock_dist", 0.35): cand = None   # vse daleko -> ne tot chelovek
                if cand is None:
                    d0 = max(dets, key=area); cand = (d0, head_of(d0))
                d, (hx, hy) = cand
                x1, y1, x2, y2 = d["box"]
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 170, 0), 2)
                cx = hx/w; cy = hy/h; face = (cx, cy)
                self.lock_pos = (cx, cy); self.lock_t = tnow
                cv2.circle(frame, (int(hx), int(hy)), 6, (0, 0, 255), -1)
            cv2.line(frame, (w//2, 0), (w//2, h), (90, 90, 90), 1)
            cv2.line(frame, (0, h//2), (w, h//2), (90, 90, 90), 1)
            dz = T.get("deadzone", 0.05); mx = T.get("max_step", 45); now = time.time(); mode = "manual"
            if face:
                last_face = now; last_pos = face; self.has_face = True
                sm = T.get("smooth", 0.4); lead = T.get("lead", 0.0)   # EMA-sglazhivanie + Kalman-lite uprezhdenie
                if self.shx is None: self.shx, self.shy = face[0], face[1]
                self.shx = sm*self.shx + (1-sm)*face[0]; self.shy = sm*self.shy + (1-sm)*face[1]
                if self.pcx is not None:
                    dt = max(1e-2, min(0.4, now - self.pt)); a = 0.45
                    self.vx = a*((self.shx-self.pcx)/dt) + (1-a)*self.vx
                    self.vy = a*((self.shy-self.pcy)/dt) + (1-a)*self.vy
                self.pcx, self.pcy, self.pt = self.shx, self.shy, now
                px = min(1.0, max(0.0, self.shx + self.vx*lead)); py = min(1.0, max(0.0, self.shy + self.vy*lead))
                ex = px - 0.5; ey = py - 0.5; self.err = (float(ex), float(ey))
                if self.enabled:
                    mode = "AUTO"
                    spd = T.get("move_spd", 1200)
                    if abs(ex) > dz and state["raw"][YAW_ID] is not None:
                        step = max(-mx, min(mx, T.get("yaw_sign",1) * ex * T.get("kp_yaw",170)))
                        enqueue("M %d %d %d" % (YAW_ID, clamp_pos(YAW_ID, state["raw"][YAW_ID] + step), spd))
                    if abs(ey) > dz and state["raw"][TILT_ID] is not None:
                        step = max(-mx, min(mx, T.get("tilt_sign",1) * ey * T.get("kp_tilt",150)))
                        enqueue("M %d %d %d" % (TILT_ID, clamp_pos(TILT_ID, state["raw"][TILT_ID] + step), spd))
            elif (now - last_face) <= T.get("coast", 1.0) and last_pos is not None:
                self.has_face = True   # koasting: kratkiy propusk detekta - derzhim, ne ischem
                cv2.circle(frame, (int(last_pos[0]*w), int(last_pos[1]*h)), 7, (0, 150, 255), 2)
                if self.enabled: mode = "AUTO~"
            else:
                self.has_face = False; self.shx = None; self.lock_pos = None   # sbros pri polnoy potere
                if self.enabled and T.get("search",1) and (now - last_face) > T.get("search_after",1.5):
                    mode = "POISK"
                    cur = state["raw"][YAW_ID]
                    if cur is not None:
                        lo = T.get("search_lo",1300); hi = T.get("search_hi",2800)
                        nxt = cur + sdir * T.get("search_step",22)
                        if nxt >= hi: sdir = -1; nxt = hi
                        elif nxt <= lo: sdir = 1; nxt = lo
                        enqueue("M %d %d 400" % (YAW_ID, clamp_pos(YAW_ID, nxt)))
                    tc = state["raw"][TILT_ID]; tcen = T.get("search_tilt", 2300)
                    if tc is not None and abs(tc - tcen) > 50:
                        enqueue("M %d %d 350" % (TILT_ID, clamp_pos(TILT_ID, tc + (70 if tcen > tc else -70))))
            tag = mode + (" | FACE" if self.has_face else " | net lica")
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

# ---------------- HTTP ----------------
cam = CameraReader(); tracker = Tracker(cam)
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
                               "cam_fps": round(cam.fps, 1), "cam_ok": cam.ok, "loop_fps": round(tracker.loop_fps, 1),
                               "track": tracker.enabled, "face": tracker.has_face,
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
        if p == "/track":
            tracker.enabled = bool(body.get("on")); return self._json({"ok": True, "track": tracker.enabled})
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
    SerialWorker().start(); cam.start(); tracker.start()
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(("0.0.0.0", PORT_HTTP), H)
    print("Pan-Tilt tracker: http://0.0.0.0:%d  bridge=%s cam=%s" % (PORT_HTTP, CFG["port"], CFG["cam_port"]))
    srv.serve_forever()
