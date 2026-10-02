#!/bin/sh
# Render the "5-Minute Job" comedy short: voices -> animation -> mux.
# Usage: sh scripts/comedy_build.sh <kokoro model dir>
set -e
P=projects/comedy
python3 scripts/comedy_audio.py $P "$1"
mkdir -p build/comedy
python3 -c "print('window.TM='+open('$P/audio/timings.json').read()+';')" > build/comedy/timings.js
T=$(python3 -c "import json;print(json.load(open('$P/audio/timings.json'))['total'])")
node scripts/render.js video/comedy.html "$T" build/comedy/video.mp4
ffmpeg -y -loglevel error -i build/comedy/video.mp4 -i $P/audio/dialogue.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest $P/Five_Minute_Job.mp4
