#!/usr/bin/env bash
# Speed up + level the mix, encode the video, run QA.   bash tools/finish.sh <name>
# Expects: mix.wav (from tools/mix.py) and frames/f00000.jpg ... in the current directory.
set -e; N="${1:-emperor_norton}"; SPEED="${SPEED:-1.27}"
ffmpeg -v error -y -i mix.wav -af "atempo=$SPEED" mix_fast.wav
ffmpeg -v error -y -i mix_fast.wav -af "volume=3.1dB,alimiter=limit=0.84:attack=5:release=60:level=disabled" -ar 48000 -ac 2 mix_final.wav
ffmpeg -v error -y -framerate 30 -i frames/f%05d.jpg -i mix_final.wav -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart "$N.mp4"
ffprobe -v error -show_entries format=duration -show_entries stream=codec_name,width,height,r_frame_rate -of compact "$N.mp4"
echo "--- QA (nothing listed = no frozen or black spans)"
ffmpeg -i "$N.mp4" -vf "freezedetect=n=0.0005:d=0.4,blackdetect=d=0.05" -an -f null - 2>&1 | tr '\r' '\n' | grep -E "freeze_start|black_start" || true
ffmpeg -i "$N.mp4" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tail -2
