# -*- coding: utf-8 -*-
# Proverka stabilnosti: 15s zamer pozicij serv i oshibki. Malen'kiy razmah = uspokoilsya.
import urllib.request, json, time
BASE = "http://NucBox_M5PLUS.local:8200"
p1s = []; p2s = []; exs = []; eys = []; t0 = time.time()
while time.time() - t0 < 15:
    try:
        d = json.load(urllib.request.urlopen(BASE + "/pos", timeout=3))
        if d["raw"]["1"] is not None: p1s.append(d["raw"]["1"]); p2s.append(d["raw"]["2"])
        exs.append(abs(d["err_xy"][0])); eys.append(abs(d["err_xy"][1]))
    except Exception: pass
    time.sleep(0.25)
def rng(a): return (max(a) - min(a)) if a else 0
print("za 15s (ty sidish rovno):")
print("  povorot id1 razmah:", rng(p1s), "(malo = ne dergaetsya)")
print("  naklon  id2 razmah:", rng(p2s))
print("  |err_x| sredn: %.3f  |err_y| sredn: %.3f" % (sum(exs)/len(exs), sum(eys)/len(eys)))
print("  verdikt:", "STABILNO ok" if rng(p1s) < 120 and rng(p2s) < 120 else "ESHCHO KOLEBLETSYA - nuzhno silnee detune")
