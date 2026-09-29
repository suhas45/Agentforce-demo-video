"""Generate the full voiceover in one voice with even pacing.
Usage: python3 scripts/voice.py <project dir> <kokoro model dir>  -> <project>/audio/voiceover.wav + timings.json"""
import json, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

D, M = sys.argv[1], sys.argv[2]
V = json.load(open(f"{D}/voiceover.json"))
k = Kokoro(f"{M}/kokoro-v1.0.onnx", f"{M}/voices-v1.0.bin")
os.makedirs(f"{D}/audio", exist_ok=True)
SR = 24000
out, t, timings = [np.zeros(int(V["lead"] * SR))], V["lead"], {}
for si, sec in enumerate(V["sections"]):
    if si:
        out.append(np.zeros(int(V["gap_section"] * SR))); t += V["gap_section"]
    rows = []
    for li, (say, sub) in enumerate(sec["lines"]):
        if li:
            out.append(np.zeros(int(V["gap_line"] * SR))); t += V["gap_line"]
        a, sr = k.create(say, voice=V["voice"], speed=V["speed"], lang="en-us")
        nz = np.nonzero(np.abs(a) > 1e-3)[0]            # trim model's leading/trailing silence
        a = a[max(nz[0] - 240, 0): nz[-1] + 480]
        rows.append([round(t, 3), round(t + len(a) / SR, 3), sub or say])
        out.append(a); t += len(a) / SR
    timings[sec["id"]] = rows
out.append(np.zeros(int(V["tail"] * SR))); t += V["tail"]
y = np.concatenate(out)
y = y / np.max(np.abs(y)) * 0.89
sf.write(f"{D}/audio/voiceover.wav", y, SR)
timings["total"] = round(t, 3)
json.dump(timings, open(f"{D}/audio/timings.json", "w"), indent=1)
for s in V["sections"]:
    print(s["id"], timings[s["id"]][0][0], timings[s["id"]][-1][1])
print("total", t)
