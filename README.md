# C Fashion × Agentforce — Product Exchange Agent demo video

- `CFashion_Agentforce_Retail_Demo.mp4` — full demo (2:20, 1920×1080): intro → Salesforce data → site login → agent chat → outcome/end card, aligned to the recorded voiceover with subtitles.
- `CFashion_Agentforce_Product_Exchange.mp4` — standalone end segment (TTS voiceover).

## Rebuild the full demo
Put the recordings in `recordings/` (`salesforcedata.mp4`, `siteloginagent.mp4`, `agentchat.mp4`), then:
```sh
npm install && pip install pillow imageio-ffmpeg kokoro-onnx soundfile
python3 scripts/voice.py <kokoro model dir>   # voiceover.json -> audio/voiceover.wav + audio/timings.json
export FFMPEG=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
python3 scripts/build.py                      # -> CFashion_Agentforce_Retail_Demo.mp4
```
- `voiceover.json`: narration script (one voice, even pacing) + subtitle text.
- `plan.json`: which recording piece plays under each narration line; crossfade length.
- `video/intro.html`, `video/end.html`: animated scenes (retimed to the narration automatically); `video/frame.html`: recording frame + subtitle style.
