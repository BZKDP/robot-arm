# -*- coding: utf-8 -*-
# Fokus-monitor 120s: lovit kivki, perehody track/gesturing, i ANOMALII -
# dvizhenie serv kogda track VYKL (ruchnoy rezhim) ili pri stope. + nahodit problemy.
import urllib.request, json, time, os
BASE = "http://ROBOT_HOST:8200"
OUT = r"screens"
os.makedirs(OUT, exist_ok=True)
DUR = 120; DT = 0.15

def pos():
    return json.load(urllib.request.urlopen(BASE + "/pos", timeout=3))

log = open(os.path.join(OUT, "track_monitor.log"), "w", encoding="utf-8")
t0 = time.time(); lp1 = lp2 = None; lnods = 0; ltrk = None; lges = None
events = []; anomalies = []
while time.time() - t0 < DUR:
    try:
        s = pos()
    except Exception as e:
        time.sleep(0.3); continue
    tt = time.time() - t0
    p1 = s["raw"]["1"]; p2 = s["raw"]["2"]; trk = s["track"]; ges = s["gesturing"]
    nods = s["nods"]; wn = s["wave_n"]; mode = s["mode"]
    d1 = (p1 - lp1) if (lp1 is not None and p1 is not None) else 0
    d2 = (p2 - lp2) if (lp2 is not None and p2 is not None) else 0
    # sobytiya
    if nods != lnods: events.append("%.1fs KIVOK #%d (mode=%s trk=%d)" % (tt, nods, mode, trk))
    if trk != ltrk and ltrk is not None: events.append("%.1fs track -> %s" % (tt, "ON" if trk else "OFF"))
    if ges != lges and lges is not None: events.append("%.1fs gesturing -> %s" % (tt, ges))
    # ANOMALII: servo dvizhetsya kogda track VYKL (dolzhno stoyat - ruchnoe)
    if trk is False and (abs(d1) > 40 or abs(d2) > 40):
        anomalies.append("%.1fs SERVO DVIGAETSYA pri track=OFF! d1=%+d d2=%+d (mode=%s ges=%s)" % (tt, d1, d2, mode, ges))
    # yaw dvizhetsya vo vremya kivka (dolzhen stoyat, kivok tolko naklon)
    if ges and abs(d1) > 40:
        anomalies.append("%.1fs YAW dvigaetsya vo vremya KIVKA! d1=%+d" % (tt, d1))
    log.write("%6.2f p1=%s(%+d) p2=%s(%+d) trk=%d ges=%d nods=%d wave_n=%d mode=%s\n"
              % (tt, p1, d1, p2, d2, int(trk), int(ges), nods, wn, mode))
    log.flush()
    lp1, lp2, lnods, ltrk, lges = p1, p2, nods, trk, ges
    time.sleep(DT)

print("==== FOKUS-MONITOR ITOG (%ds) ====" % DUR)
print("SOBYTIYA:")
for e in events: print("  ", e)
print("ANOMALII (%d):" % len(anomalies))
for a in anomalies[:40]: print("  ", a)
if not anomalies: print("   net - servy stoyat kogda dolzhny (track off / kivok yaw)")
log.write("\nEVENTS:\n" + "\n".join(events) + "\n\nANOMALIES:\n" + "\n".join(anomalies) + "\n"); log.close()
