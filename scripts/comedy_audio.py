"""Build the two-voice dialogue track for projects/comedy from one source voice.
Each line is cut from the source and re-voiced (formant + pitch shift per character);
"tts" lines (Arey / Orey) are synthesised with Kokoro and matched to the manager's pitch.
Writes audio/dialogue.wav and audio/timings.json (line times + 30fps mouth envelope per speaker).
Usage: python3 scripts/comedy_audio.py projects/comedy <kokoro dir>"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf, librosa

D, KD = sys.argv[1].rstrip("/"), sys.argv[2]
L = json.load(open(f"{D}/lines.json"))
SR, FPS, LEAD, TAIL = 44100, 30, 2.0, 6.0
A = f"{D}/audio"
os.makedirs(A, exist_ok=True)
src, _ = librosa.load(L["src"], sr=SR, mono=True)

# Kokoro phonemes (hm_omega): Telugu interjections said the Telugu way
TTS = {"arey": ("ʌɾˈeː!", 0.9), "orey": ("oːɾˈeː...", 0.8), "orey_arjun": ("oːɾˈeː, ˈʌɾdʒʊn!", 0.9)}


def af(x, chain):
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", chain, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
                       input=x.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32)


def revoice(x, v):
    f, p = v["formant"], v["pitch"]
    return af(x, f"asetrate={SR * f:.0f},aresample={SR},atempo={1 / f:.4f},"
                 f"rubberband=pitch={p / f:.4f}:formant=preserved")


def f0(x):
    g, _, _ = librosa.pyin(librosa.resample(x, orig_sr=SR, target_sr=16000), fmin=60, fmax=400, sr=16000)
    return float(np.nanmedian(g))


clips = []
for ln in L["lines"]:
    if "src" in ln:
        a, b = ln["src"]
        x = revoice(src[int(a * SR):int(b * SR)], L["voices"][ln["spk"]])
    else:
        from kokoro_onnx import Kokoro
        k = Kokoro(f"{KD}/kokoro.onnx", f"{KD}/voices.bin")
        ph, sp = TTS[ln["tts"]]
        y, r = k.create(ph, voice="hm_omega", speed=sp, is_phonemes=True)
        x = librosa.resample(np.asarray(y, np.float32), orig_sr=r, target_sr=SR)
        x, _ = librosa.effects.trim(x, top_db=35)
        ln["_tts"] = True
    if ln.get("phone"):
        x = af(x, "highpass=f=320,lowpass=f=3300,acompressor=threshold=0.1:ratio=4,volume=1.6")
    clips.append(x)

# match Kokoro lines to the re-voiced manager's pitch and loudness
mgr = np.concatenate([c for c, l in zip(clips, L["lines"]) if l["spk"] == "manager" and "src" in l and not l.get("phone")])
mf, mr = f0(mgr), np.sqrt(np.mean(mgr ** 2))
for i, ln in enumerate(L["lines"]):
    if ln.get("_tts"):
        c = af(clips[i], f"rubberband=pitch={mf / f0(clips[i]):.4f}:formant=preserved")
        clips[i] = c * (mr / max(np.sqrt(np.mean(c ** 2)), 1e-6))

# lay out: keep the source pauses, give the inserted words their own breath
out, t, prev_end, T = [np.zeros(int(LEAD * SR), np.float32)], LEAD, None, []
for i, (ln, c) in enumerate(zip(L["lines"], clips)):
    if i:
        if "src" in ln and "src" in L["lines"][i - 1]:
            gap = max(ln["src"][0] - L["lines"][i - 1]["src"][1], 0.25)
        else:
            gap = 0.3 if ln.get("_tts") else 0.12
        if ln.get("phone") and not L["lines"][i - 1].get("phone"):
            gap = 1.2  # cut to the phone call
        gap = ln.get("pre", gap)
        out.append(np.zeros(int(gap * SR), np.float32)); t += gap
    out.append(c)
    T.append({"spk": ln["spk"], "start": round(t, 3), "end": round(t + len(c) / SR, 3), "sub": ln["sub"],
              "phone": bool(ln.get("phone"))})
    t += len(c) / SR
out.append(np.zeros(int(TAIL * SR), np.float32))
y = np.concatenate(out)
y = y / np.max(np.abs(y)) * 0.89
sf.write(f"{A}/dialogue.wav", y, SR)

# mouth envelope per speaker, 0..1 at 30fps
n = int(len(y) / SR * FPS) + 1
env = {"manager": [0.0] * n, "arjun": [0.0] * n}
hop = SR // FPS
rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop)[0]
rms = np.clip(rms / np.percentile(rms[rms > 1e-4], 95), 0, 1)
for l in T:
    for f in range(int(l["start"] * FPS), min(int(l["end"] * FPS) + 1, n, len(rms))):
        env[l["spk"]][f] = round(float(rms[f]), 3)
json.dump({"total": round(len(y) / SR, 3), "lines": T, "env": env}, open(f"{A}/timings.json", "w"))
print(f"{len(y) / SR:.2f}s, manager f0 {mf:.0f}Hz")
for l in T: print(l["start"], l["end"], l["spk"], l["sub"])
