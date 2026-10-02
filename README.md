# C Fashion × Agentforce — demo videos

| Project | Video |
|---|---|
| Product Exchange & Return agent (web chat) | `projects/exchange/CFashion_Agentforce_Retail_Demo.mp4` |
| Store Transfer agent (Slack) | `projects/transfer/CFashion_Agentforce_Store_Transfer_Demo.mp4` |
| "The 5-Minute Job" (animated Telugu comedy short) | `projects/comedy/Five_Minute_Job.mp4` — rebuild: `sh scripts/comedy_build.sh <kokoro model dir>` |

Each project folder has:
- `voiceover.json` — narration script (one voice, even pacing) + subtitle text, per section.
- `plan.json` — section order, intro/end HTML, and which recording piece `[srcStart, srcEnd, weight]` plays under each narration line.

## Rebuild
Put the screen recordings in `recordings/` (paths as in each `plan.json`), then:
```sh
npm install && pip install pillow imageio-ffmpeg kokoro-onnx soundfile
export FFMPEG=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
python3 scripts/voice.py projects/transfer <kokoro model dir>   # -> projects/transfer/audio/
python3 scripts/build.py projects/transfer                      # -> projects/transfer/<output>.mp4
```
Scenes: `video/<project>_intro.html`, `video/<project>_end.html` (auto-retimed to the narration); `video/frame.html` styles the recording frame and subtitles.
