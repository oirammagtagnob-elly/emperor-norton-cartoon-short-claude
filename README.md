# Emperor Norton: vertical cartoon short

A 59-second vertical (1080x1920, 30 fps) cartoon short about Joshua Norton, the man who declared himself Emperor of the United States. The whole animation is drawn in code on an HTML canvas and rendered frame by frame in headless Chromium, with a synthesized music bed and sound effects mixed under a recorded voiceover.

Captions are off by default in the render commands below (`&nocap=1`), so you can add your own in CapCut. Drop that flag to burn in the built-in captions.

## Layout

| Path | What it is |
| --- | --- |
| `src/index.html` | The whole short. `draw(t)` renders any moment from time `t` (seconds, in the original 74.84 s voiceover timeline). 14 scenes, bean-head cast, lighting and shading pass. |
| `tools/render.mjs` | Renders frames to JPEG with Playwright. |
| `tools/stills.mjs` | Renders a few still frames at chosen times for quick checks. |
| `tools/sheet.py` | Builds a contact sheet from stills. |
| `tools/mix.py` | Synthesizes music and SFX, mixes them under the voiceover, and exports stems. |
| `tools/finish.sh` | Speeds up the audio, levels it, encodes the MP4 and runs QA. |
| `script/voiceover.txt` | The narration text. |

## Requirements

- Node 18+, then `npm i playwright && npx playwright install chromium`
- Python 3 with `numpy` and `pillow`
- ffmpeg

Your own voiceover recording is not in this repo. Record the text in `script/voiceover.txt` and keep the file locally.

## How it works

- **Timing.** The 30 entries in the `CAP` table inside `src/index.html` are the start and end times of each spoken phrase, taken from the silences in the original 74.84 s recording. Scenes are cut on those silences, so if you re-record, redo that table first.
- **Speed.** The original read runs 74.84 s. The published cut is sped up 1.27x (pitch preserved) to 58.9 s, so the renderer maps real time to animation time with `time = frame / 30 * 1.27` (set `SPEED` to change it).
- **Look.** Soft contact and cast shadows under characters, shaded coats and faces, per-scene colour grading (soft-light tint, light bloom, vignette), dust motes in interiors, a lamp glow and wet-street reflection in the rain, and soft-focus background layers.
- **Audio.** Music and SFX are generated with numpy. They are mixed at half the voice level (music RMS = 0.5x voice RMS, SFX peak = 0.5x voice peak). The full mix is then sped up and levelled to about -14 LUFS with a -1.4 dBFS peak.

## Render it

```bash
npm i playwright && npx playwright install chromium

# frames (1768 at 1080x1920); run in chunks if your machine is slow
node tools/render.mjs 0 900    frames "&nocap=1"
node tools/render.mjs 900 1768 frames "&nocap=1"

# audio: writes mix.wav and the stems in the original timeline
python3 tools/mix.py path/to/voiceover.mp3

# speed up, level, encode, QA
bash tools/finish.sh emperor_norton_NO_captions
```

Quick look at a few moments first:

```bash
node tools/stills.mjs 3 21.5 36.5 61
python3 tools/sheet.py sheet.jpg stills/t3.jpg stills/t21_5.jpg stills/t36_5.jpg stills/t61.jpg
```

## For CapCut

`tools/mix.py` also writes `stem_voice_orig.wav` and `stem_music_sfx_orig.wav`. Speed each one with `ffmpeg -i X.wav -af atempo=1.27 -ar 48000 out.wav` to get stems that line up with the final video.

## Notes

- A full 3D version (three.js world with 2D cards) is possible with the separate cartoon-short kit; this repo is the 2D canvas version.
