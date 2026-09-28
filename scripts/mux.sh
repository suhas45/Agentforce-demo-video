#!/bin/sh
# Mix voiceover lines at scene offsets + soft synth pad, then mux onto rendered video.
FF=${FFMPEG:-ffmpeg}
PAD="0.035*(sin(2*PI*220*t)+sin(2*PI*277.18*t)+sin(2*PI*329.63*t)+0.6*sin(2*PI*110*t))*(0.75+0.25*sin(2*PI*0.2*t))"
$FF -y -f lavfi -i "aevalsrc=$PAD:s=24000:d=35.5" -c:a pcm_s16le out/pad.wav
$FF -y -i out/pad.wav -i audio/s1.wav -i audio/s2.wav -i audio/s3.wav -i audio/s4.wav \
 -filter_complex "[0]lowpass=f=900,afade=t=in:d=2,afade=t=out:st=33:d=2.5,volume=0.5[m];\
[1]adelay=3200:all=1[a1];[2]adelay=11700:all=1[a2];[3]adelay=21800:all=1[a3];[4]adelay=27000:all=1[a4];\
[m][a1][a2][a3][a4]amix=inputs=5:normalize=0:duration=first[aout]" \
 -map "[aout]" -ar 48000 -c:a pcm_s16le out/mix.wav
$FF -y -i out/video_silent.mp4 -i out/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
 -movflags +faststart out/CFashion_Agentforce_Product_Exchange.mp4
