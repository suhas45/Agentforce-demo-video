# C Fashion × Agentforce — Product Exchange Agent demo video

- `CFashion_Agentforce_Retail_Demo.mp4` — full demo (2:20, 1920×1080): intro → Salesforce data → site login → agent chat → outcome/end card, aligned to the recorded voiceover with subtitles.
- `CFashion_Agentforce_Product_Exchange.mp4` — standalone end segment (TTS voiceover).

## Rebuild the full demo
Put the source files in `recordings/` (`salesforcedata.mp4`, `siteloginagent.mp4`, `agentchat.mp4`, `Agentforce_Retail_Demo.m4a`), then:
```sh
npm install && pip install pillow imageio-ffmpeg
export FFMPEG=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p build out && python3 scripts/build.py
```
- `plan.json` : section timings, clip pieces `[srcStart, srcEnd, targetDuration]`, subtitles.
- `video/intro.html`, `video/end.html`: animated scenes; `video/frame.html`: recording frame + subtitle style.
