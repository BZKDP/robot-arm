# -*- coding: utf-8 -*-
# YOLO11-pose inference cherez onnxruntime-DirectML (AMD iGPU). Bez ultralytics.
# Vyhod modeli [1,56,8400]: 4 box(xywh,px640) + 1 conf + 51 keypoints(17*(x,y,conf)).
import numpy as np, cv2, onnxruntime as ort

class DmlPose:
    def __init__(self, onnx_path, imgsz=640, conf=0.10, iou=0.45):
        prov = ["DmlExecutionProvider", "CPUExecutionProvider"]
        self.sess = ort.InferenceSession(onnx_path, providers=prov)
        self.inp = self.sess.get_inputs()[0].name
        self.imgsz = imgsz; self.conf = conf; self.iou = iou
        self.provider = self.sess.get_providers()[0]

    def _nms(self, b, s, th):
        x1, y1, x2, y2 = b[:,0], b[:,1], b[:,2], b[:,3]
        areas = (x2-x1)*(y2-y1); order = s.argsort()[::-1]; keep = []
        while order.size > 0:
            i = order[0]; keep.append(i)
            if order.size == 1: break
            xx1 = np.maximum(x1[i], x1[order[1:]]); yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]]); yy2 = np.minimum(y2[i], y2[order[1:]])
            w = np.maximum(0, xx2-xx1); h = np.maximum(0, yy2-yy1); inter = w*h
            iou = inter/(areas[i]+areas[order[1:]]-inter+1e-6)
            order = order[1:][iou < th]
        return keep

    def detect(self, frame, conf=None):
        cf = self.conf if conf is None else conf
        h0, w0 = frame.shape[:2]; sz = self.imgsz
        r = min(sz/h0, sz/w0); nw, nh = int(round(w0*r)), int(round(h0*r))
        dw, dh = (sz-nw)//2, (sz-nh)//2
        canvas = np.full((sz, sz, 3), 114, np.uint8)
        canvas[dh:dh+nh, dw:dw+nw] = cv2.resize(frame, (nw, nh))
        blob = canvas[:, :, ::-1].transpose(2,0,1)[None].astype(np.float32)/255.0
        out = self.sess.run(None, {self.inp: blob})[0][0].T   # [8400,56]
        sc = out[:, 4]; m = sc > cf
        out = out[m]; sc = sc[m]
        if len(out) == 0: return []
        xy = out[:, :2]; wh = out[:, 2:4]
        bb = np.concatenate([xy - wh/2, xy + wh/2], 1)   # xyxy v 640
        keep = self._nms(bb, sc, self.iou)
        res = []
        for i in keep:
            b = bb[i]; kp = out[i, 5:].reshape(17, 3)
            ux = lambda x: (x - dw)/r; uy = lambda y: (y - dh)/r
            box = (float(ux(b[0])), float(uy(b[1])), float(ux(b[2])), float(uy(b[3])))
            kps = [(float(ux(kp[j,0])), float(uy(kp[j,1])), float(kp[j,2])) for j in range(17)]
            res.append({"box": box, "conf": float(sc[i]), "kp": kps})
        return res
