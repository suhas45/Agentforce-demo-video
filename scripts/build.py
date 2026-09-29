"""Assemble the full demo from audio/timings.json (see scripts/voice.py) and plan.json:
intro (HTML) -> framed screen recordings retimed line-by-line to the voiceover -> end (HTML),
joined with crossfades, plus the voiceover and a soft music bed.
Usage: FFMPEG=... python3 scripts/build.py <project dir>"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw

FF = os.environ.get("FFMPEG", "ffmpeg")
D = sys.argv[1].rstrip("/")
P = json.load(open(f"{D}/plan.json"))
T = json.load(open(f"{D}/audio/timings.json"))
B, FPS, X = f"build/{os.path.basename(D)}", 30, P["xfade"]
os.makedirs(B, exist_ok=True)


def ff(*args):
    subprocess.run([FF, "-y", "-loglevel", "error", *args], check=True)


def window(src):
    """Recording window on the 1920x1080 frame: max 1720x790, fitted to the clip's aspect, centered."""
    info = subprocess.run([FF, "-i", src], capture_output=True, text=True).stderr
    w, h = map(int, re.search(r"Video: .*?, (\d{3,5})x(\d{3,5})", info).groups())
    ww = min(1720, round(790 * w / h / 2) * 2)
    x = (1920 - ww) // 2
    return (x, 130, x + ww, 920)


# section start times on the master timeline
order = P["order"]
start = {"intro": 0.0}
for s in order[1:]:
    start[s] = T[s][0][0] - P["lead"][s]
span = {s: (start[order[i + 1]] if i + 1 < len(order) else T["total"]) - start[s] for i, s in enumerate(order)}
dur = {s: span[s] + (X if i + 1 < len(order) else 0) for i, s in enumerate(order)}  # overlap for xfade


def html_section(s):
    cfg, lines = P[s], T[s]
    anch = [[0, 0]] + [[l[0] - start[s], a] for l, a in zip(lines, cfg["authored"])]
    anch.append([lines[-1][1] - start[s], cfg["authored_end"]])
    out = f"{B}/{s}.mp4"
    env = dict(os.environ, ANCH=json.dumps(anch))
    subprocess.run(["node", "scripts/render.js", cfg["html"], f"{dur[s]:.3f}", out], check=True, env=env)
    return out


def rec_section(s, idx):
    cfg, lines = P["recordings"][s], T[s]
    WIN = window(cfg["src"])
    t0 = start[s]
    bounds = [t0] + [l[0] for l in lines[1:]] + [t0 + dur[s]]
    chains, labels = [], []
    for li, pieces in enumerate(cfg["pieces"]):
        line_len = bounds[li + 1] - bounds[li]
        wsum = sum(p[2] for p in pieces)
        for a, b, w in pieces:
            tgt = line_len * w / wsum
            speed = max((b - a) / tgt, 0.8)   # never slower than 0.8x; hold last frame instead
            j = len(labels)
            chains.append(f"[0:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{speed:.4f},fps={FPS},"
                          f"tpad=stop_mode=clone:stop_duration={tgt + 0.2:.3f},trim=0:{tgt:.4f},setpts=PTS-STARTPTS[p{j}]")
            labels.append(f"[p{j}]")
    w, h = WIN[2] - WIN[0], WIN[3] - WIN[1]
    fc = ";".join(chains) + f";{''.join(labels)}concat=n={len(labels)}:v=1:a=0,scale={w}:{h}:force_original_aspect_ratio=decrease," \
        f"pad={w}:{h}:-1:-1:color=0x0B1F3A,setsar=1[rec];[1:v][rec]overlay={WIN[0]}:{WIN[1]}[x];[x][2:v]overlay=0:0[y0]"
    d = f"{dur[s]:.3f}"
    inputs = ["-i", cfg["src"], "-loop", "1", "-t", d, "-i", f"{B}/frame_{idx}.png", "-loop", "1", "-t", d, "-i", f"{B}/hole_{idx}.png"]
    last = "y0"
    for n, (a, b, _) in enumerate(lines):
        inputs += ["-loop", "1", "-t", d, "-i", f"{B}/sub_{s}_{n}.png"]
        fc += f";[{last}][{3 + n}:v]overlay=0:0:enable='between(t,{a - t0 - 0.1:.2f},{b - t0 + 0.25:.2f})'[s{n}]"
        last = f"s{n}"
    out = f"{B}/{s}.mp4"
    ff(*inputs, "-filter_complex", fc, "-map", f"[{last}]", "-t", d, "-r", str(FPS),
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", out)
    return out


# stills: frames + subtitles for recording sections
recs = [s for s in order if s in P["recordings"]]
stills = {"sections": [{"label": P["recordings"][s]["label"], "win": window(P["recordings"][s]["src"])} for s in recs],
          "subs": [[f"{s}_{n}", l[2]] for s in recs for n, l in enumerate(T[s])]}
json.dump(stills, open(f"{B}/stills.json", "w"))
subprocess.run(["node", "scripts/stills.js", f"{B}/stills.json", B], check=True)
for i, _ in enumerate(recs):
    im = Image.open(f"{B}/frame_{i}.png").convert("RGBA")
    m = Image.new("L", im.size, 255)
    ImageDraw.Draw(m).rounded_rectangle(stills["sections"][i]["win"], 22, fill=0)
    im.putalpha(m)
    im.save(f"{B}/hole_{i}.png")

parts = [html_section(s) if s not in P["recordings"] else rec_section(s, recs.index(s)) for s in order]

# crossfade join
ins, fc, last = [], [], "0:v"
for p in parts:
    ins += ["-i", p]
for i in range(1, len(parts)):
    fc.append(f"[{last}][{i}:v]xfade=transition=fade:duration={X}:offset={start[order[i]]:.3f}[v{i}]")
    last = f"v{i}"
ff(*ins, "-filter_complex", ";".join(fc), "-map", f"[{last}]", "-r", str(FPS),
   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", f"{B}/video.mp4")

# audio: voiceover + soft pad under the whole piece
tot = T["total"]
pad = "0.03*(sin(2*PI*220*t)+sin(2*PI*277.18*t)+sin(2*PI*329.63*t)+0.6*sin(2*PI*110*t))*(0.75+0.25*sin(2*PI*0.1*t))"
ff("-f", "lavfi", "-i", f"aevalsrc={pad}:s=24000:d={tot:.3f}", "-c:a", "pcm_s16le", f"{B}/pad.wav")
ff("-i", f"{D}/audio/voiceover.wav", "-i", f"{B}/pad.wav", "-filter_complex",
   f"[1]lowpass=f=800,afade=t=in:d=2,afade=t=out:st={tot - 3:.2f}:d=3,volume=0.35[m];[0][m]amix=inputs=2:normalize=0:duration=longest[a]",
   "-map", "[a]", "-ar", "48000", "-c:a", "pcm_s16le", f"{B}/mix.wav")
ff("-i", f"{B}/video.mp4", "-i", f"{B}/mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
   "-c:a", "aac", "-b:a", "192k", "-t", f"{tot:.3f}", "-movflags", "+faststart", f"{D}/{P['output']}")
print("done", {s: round(start[s], 2) for s in order}, "total", tot)
