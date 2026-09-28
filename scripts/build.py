"""Assemble the full demo: intro (HTML) + framed screen recordings (retimed to the voiceover) + end (HTML).
Usage: python3 scripts/build.py   (expects FFMPEG env, recordings/ and build/plan.json)"""
import json, os, subprocess
from PIL import Image, ImageDraw

FF = os.environ.get("FFMPEG", "ffmpeg")
P = json.load(open("plan.json"))
B = "build"
FPS = 30
WIN = (100, 130, 1820, 920)  # recording window on the 1920x1080 frame


def ff(*args):
    subprocess.run([FF, "-y", "-loglevel", "error", *args], check=True)


def render_html(html, dur, out):
    if not os.path.exists(out):
        subprocess.run(["node", "scripts/render.js", html, str(dur), out], check=True)


# 1. stills: frame backgrounds + subtitle overlays
subprocess.run(["node", "scripts/stills.js", "plan.json", B], check=True)
for i, _ in enumerate(P["sections"]):
    im = Image.open(f"{B}/frame_{i}.png").convert("RGBA")
    m = Image.new("L", im.size, 255)
    ImageDraw.Draw(m).rounded_rectangle(WIN, 22, fill=0)
    im.putalpha(m)
    im.save(f"{B}/hole_{i}.png")

# 2. intro / end
render_html(P["intro"]["html"], P["intro"]["dur"], f"{B}/intro.mp4")
render_html(P["end"]["html"], P["end"]["dur"], f"{B}/end.mp4")

# 3. recordings: retime pieces, frame them, burn subtitles
w, h = WIN[2] - WIN[0], WIN[3] - WIN[1]
parts = [f"{B}/intro.mp4"]
for i, s in enumerate(P["sections"]):
    chains, labels = [], []
    for j, (a, b, tgt) in enumerate(s["pieces"]):
        src = b - a
        speed = max(src / tgt, 0.8)          # never slow below 0.8x; hold last frame instead
        hold = max(tgt - src / speed, 0)
        chains.append(f"[0:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{speed:.4f},fps={FPS},"
                      f"tpad=stop_mode=clone:stop_duration={hold + 0.1:.3f},trim=0:{tgt},setpts=PTS-STARTPTS[p{j}]")
        labels.append(f"[p{j}]")
    dur = sum(p[2] for p in s["pieces"])
    t0 = s["start"]
    subs = [(k, a - t0, b - t0) for k, (a, b, _) in enumerate(P["subs"]) if t0 - 0.01 <= a < t0 + dur]
    fc = ";".join(chains)
    fc += f";{''.join(labels)}concat=n={len(labels)}:v=1:a=0,scale={w}:{h}:force_original_aspect_ratio=decrease," \
          f"pad={w}:{h}:-1:-1:color=0x0B1F3A,setsar=1[rec]"
    fc += f";[1:v][rec]overlay={WIN[0]}:{WIN[1]}[x0];[x0][2:v]overlay=0:0[y0]"
    inputs = ["-i", s["src"], "-loop", "1", "-t", str(dur), "-i", f"{B}/frame_{i}.png",
              "-loop", "1", "-t", str(dur), "-i", f"{B}/hole_{i}.png"]
    last = "y0"
    for n, (k, a, b) in enumerate(subs):
        inputs += ["-loop", "1", "-t", str(dur), "-i", f"{B}/sub_{k}.png"]
        fc += f";[{last}][{3 + n}:v]overlay=0:0:enable='between(t,{a:.2f},{min(b, dur):.2f})'[s{n}]"
        last = f"s{n}"
    out = f"{B}/rec_{i}.mp4"
    if not os.path.exists(out): ff(*inputs, "-filter_complex", fc, "-map", f"[{last}]", "-t", f"{dur}", "-r", str(FPS),
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", out)
    parts.append(out)
parts.append(f"{B}/end.mp4")

# 4. concat + voiceover
with open(f"{B}/list.txt", "w") as f:
    f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
ff("-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy", f"{B}/video.mp4")
total = sum(float(subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
                .split("Duration: ")[1].split(",")[0].split(":")[k]) * m for p in [f"{B}/video.mp4"]
            for k, m in ((0, 3600), (1, 60), (2, 1)))
ff("-i", P["voiceover"], "-af", "apad", "-t", f"{total:.3f}", "-ar", "48000", f"{B}/vo.wav")
ff("-i", f"{B}/video.mp4", "-i", f"{B}/vo.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
   "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart",
   "CFashion_Agentforce_Retail_Demo.mp4")
print("done")
