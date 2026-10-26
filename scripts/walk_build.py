"""Release walkthrough: intro card -> one split-screen chapter per ticket -> end card.
Usage: FFMPEG=... python3 scripts/walk_build.py <release dir> <kokoro model dir> [--only ID,...] [--preview]
"""
import hashlib, json, os, subprocess, sys
import numpy as np, soundfile as sf

FF = os.environ.get("FFMPEG", "ffmpeg")
D, M = sys.argv[1].rstrip("/"), sys.argv[2]
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
PREVIEW = "--preview" in sys.argv
REL = json.load(open(f"{D}/release.json"))
B = f"build/{os.path.basename(D)}"
os.makedirs(f"{B}/tts", exist_ok=True)
SR, FPS = 24000, 30
CARD_END, GAP, TAIL = 2.4, 0.4, 1.0
_k = None


def ff(*a):
    subprocess.run([FF, "-y", "-loglevel", "error", *a], check=True)


def tts(text):
    """Kokoro line, silence-trimmed, cached by text."""
    global _k
    f = f"{B}/tts/{hashlib.md5((REL['voice'] + text).encode()).hexdigest()[:12]}.wav"
    if not os.path.exists(f):
        if _k is None:
            from kokoro_onnx import Kokoro
            _k = Kokoro(f"{M}/kokoro-v1.0.onnx", f"{M}/voices-v1.0.bin")
        a, _ = _k.create(text, voice=REL["voice"], speed=REL["speed"], lang="en-us")
        nz = np.nonzero(np.abs(a) > 1e-3)[0]
        sf.write(f, a[max(nz[0] - 240, 0): nz[-1] + 480], SR)
    a, _ = sf.read(f)
    return a


def render(cfg, out):
    p = out.replace(".mp4", ".json")
    json.dump(cfg, open(p, "w"))
    if PREVIEW:
        ts = ",".join(f"{x:.2f}" for x in cfg.get("preview", [1.0]))
        subprocess.run(["node", "scripts/walk_render.js", p, out[:-4], "preview", ts], check=True)
    else:
        subprocess.run(["node", "scripts/walk_render.js", p, out], check=True)


def card(kind, text, eyebrow, title, subtitle, lst=None):
    a = tts(text)
    start = 0.9
    dur = start + len(a) / SR + 1.4
    cfg = {"mode": "card", "dur": dur, "eyebrow": eyebrow, "title": title, "subtitle": subtitle, "list": lst,
           "lines": [{"start": start, "end": start + len(a) / SR, "text": text}], "preview": [dur - 0.5]}
    render(cfg, f"{B}/{kind}.mp4")
    return dur, [(start, a)]


def chapter(tid, idx):
    T = json.load(open(f"{D}/tickets/{tid}/ticket.json"))
    t, lines, audio = CARD_END + 0.2, [], []
    for l in T["lines"]:
        a = tts(l.get("say", l["text"]))
        lines.append({**{k: l[k] for k in ("beat", "head", "sub", "text")}, "start": round(t, 3), "end": round(t + len(a) / SR, 3)})
        audio.append((t, a))
        t += len(a) / SR + GAP
    dur = lines[-1]["end"] + TAIL
    rec_start = CARD_END - 0.6
    # recording retimed so each piece plays under its narration line
    bounds = [rec_start] + [l["start"] for l in lines[1:]] + [dur]
    chains, labels, segs = [], [], []
    for li, pieces in enumerate([l["pieces"] for l in T["lines"]]):
        span, wsum, o = bounds[li + 1] - bounds[li], sum(p[2] for p in pieces), bounds[li]
        for a, b, w in pieces:
            tgt = span * w / wsum
            sp = max((b - a) / tgt, 0.8)
            j = len(labels)
            chains.append(f"[s{len(labels)}]trim={a}:{b},setpts=(PTS-STARTPTS)/{sp:.4f},fps={FPS},"
                          f"tpad=stop_mode=clone:stop_duration={tgt + .2:.3f},trim=0:{tgt:.4f},setpts=PTS-STARTPTS[p{j}]")
            labels.append(f"[p{j}]")
            segs.append((a, b, o, sp, tgt))
            o += tgt
    fdir = f"{B}/{tid}_frames"
    os.makedirs(fdir, exist_ok=True)
    for f in os.listdir(fdir):
        os.remove(f"{fdir}/{f}")
    split = f"[0:v]split={len(labels)}" + "".join(f"[s{j}]" for j in range(len(labels)))
    ff("-i", T["recording"], "-filter_complex", split + ";" + ";".join(chains) + f";{''.join(labels)}concat=n={len(labels)}:v=1:a=0[v]",
       "-map", "[v]", "-fps_mode", "cfr", "-r", str(FPS), "-q:v", "3", f"{fdir}/%05d.jpg")
    n = len(os.listdir(fdir))

    def m(src):  # source time -> chapter time
        for a, b, o, sp, tgt in segs:
            if a <= src <= b:
                return o + min((src - a) / sp, tgt)
        return segs[-1][2] + segs[-1][4]
    cam = [{"t": m(c["src"]), "x": c["x"], "y": c["y"], "w": c["w"]} for c in T["cam"]]
    focus = [{"t0": m(f["src0"]), "t1": m(f["src1"]), **{k: f[k] for k in "xywh"}} for f in T["focus"]]
    cfg = {"mode": "chapter", "dur": dur, "id": T["id"], "title": T["title"], "area": T["area"], "index": idx,
           "total": REL["total"], "cardEnd": CARD_END, "lines": lines, "cam": cam, "focus": focus,
           "rec": {"start": rec_start, "n": n, "dir": "../../" + fdir},
           "preview": [1.2] + [l["start"] + 1.5 for l in lines] + [f["t0"] + .6 for f in focus]}
    render(cfg, f"{B}/{tid}.mp4")
    return dur, audio


def music(total):
    """Minimal piano arpeggio I-vi-IV-V, ~100 BPM."""
    chords = [(261.63, 329.63, 392.0), (220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (196.0, 246.94, 293.66)]
    beat, y = 60 / 100, np.zeros(int(total * SR) + SR)
    def note(f, t0, d, amp):
        n = int(d * SR); tt = np.arange(n) / SR
        w = sum(np.sin(2 * np.pi * f * h * tt) / h ** 1.6 for h in (1, 2, 3)) * np.exp(-3.2 * tt) * amp
        i = int(t0 * SR); y[i:i + n] += w[: len(y) - i]
    t, bar = 0.0, 0
    while t < total:
        c = chords[bar % 4]
        note(c[0] / 2, t, 2.4, .10)
        for k, f in enumerate([c[0], c[1], c[2], c[0] * 2, c[2], c[1], c[0], c[1]]):
            note(f, t + k * beat / 2, 1.2, .045)
        t += 4 * beat; bar += 1
    return y[: int(total * SR)]


def whoosh():
    n = int(0.7 * SR); rng = np.random.default_rng(7); x = rng.standard_normal(n)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    y, s = np.zeros(n), 0.0
    for i in range(n):
        a = 0.02 + 0.25 * env[i]; s += a * (x[i] - s); y[i] = s
    return y * env * 0.5


# ---- build segments
parts, voice, sfx, t0 = [], [], [], 0.0
ids = ONLY or REL["tickets"]
d, au = card("intro", REL["intro"]["text"], "RELEASE WALKTHROUGH", REL["title"], REL["subtitle"],
             [f"{i}" for i in REL["tickets"]])
parts.append(f"{B}/intro.mp4"); voice += [(t0 + s, a) for s, a in au]; t0 += d
for k, tid in enumerate(ids):
    idx = REL["tickets"].index(tid) + 1
    d, au = chapter(tid, idx)
    parts.append(f"{B}/{tid}.mp4"); voice += [(t0 + s, a) for s, a in au]
    sfx += [(t0 + 0.05, 0.6), (t0 + CARD_END - 0.6, 1.0)]
    t0 += d
d, au = card("end", REL["end"]["text"], "THAT'S A WRAP", REL["title"], f"{len(REL['tickets'])} of {REL['total']} tickets covered", None)
parts.append(f"{B}/end.mp4"); voice += [(t0 + s, a) for s, a in au]; sfx.append((t0 + 0.05, 0.6)); t0 += d
if PREVIEW:
    print("preview done"); sys.exit()

# ---- video
with open(f"{B}/list.txt", "w") as f:
    f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
ff("-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy", f"{B}/video.mp4")

# ---- audio: voice on top, SFX under, music ducked under speech
N = int(t0 * SR)
v, s = np.zeros(N), np.zeros(N)
for st_, a in voice:
    i = int(st_ * SR); v[i:i + len(a)] += a[: N - i]
w = whoosh()
for st_, g in sfx:
    i = int(st_ * SR); s[i:i + len(w)] += g * w[: N - i]
v = v / (np.sqrt(np.mean(v[np.abs(v) > 1e-3] ** 2)) + 1e-9) * 0.1
sf.write(f"{B}/voice.wav", v, SR); sf.write(f"{B}/sfx.wav", s * 0.5, SR); sf.write(f"{B}/music.wav", music(t0), SR)
ff("-i", f"{B}/voice.wav", "-i", f"{B}/music.wav", "-i", f"{B}/sfx.wav", "-filter_complex",
   "[0]asplit[v][sc];[1]aecho=0.8:0.5:60|120:0.25|0.15,afade=t=in:d=1.5,"
   f"afade=t=out:st={t0 - 2.5:.2f}:d=2.5[m];[m][sc]sidechaincompress=threshold=0.02:ratio=8:attack=120:release=400[md];"
   "[v][md][2]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1:LRA=11[a]",
   "-map", "[a]", "-ar", "48000", f"{B}/mix.wav")
ff("-i", f"{B}/video.mp4", "-i", f"{B}/mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
   "-t", f"{t0:.3f}", "-movflags", "+faststart", f"{D}/{REL['output']}")
print("done", round(t0, 2))
