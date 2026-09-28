# C Fashion × Agentforce — Product Exchange Agent demo video

Output: `CFashion_Agentforce_Product_Exchange.mp4` (1920×1080, 30 fps, 35.5 s, voiceover + subtitles).

## Rebuild
```sh
npm install
pip install kokoro-onnx soundfile imageio-ffmpeg
python3 scripts/tts.py <dir with kokoro-v1.0.onnx + voices-v1.0.bin>   # -> audio/s1..s4.wav
export FFMPEG=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p out && node scripts/render.js   # -> out/video_silent.mp4
sh scripts/mux.sh                        # -> out/CFashion_Agentforce_Product_Exchange.mp4
```
Scenes live in `video/index.html` (timings are absolute seconds in CSS `--s/--e/--d`).
