import numpy as np, subprocess, wave, sys
SR = 44100
VOICE = sys.argv[1]
subprocess.run(['ffmpeg', '-y', '-i', VOICE, '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_s16le', 'voice.wav'], check=True, capture_output=True)
with wave.open('voice.wav') as w:
    v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
N = len(v)
DUR = N / SR
rng = np.random.default_rng(7)

def put(buf, t0, sig, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain

def fq(m): return 440.0 * 2 ** ((m - 69) / 12)
def tarr(d): return np.arange(int(d * SR)) / SR

def pluck(f, d, bright=1.0):
    t = tarr(d)
    env = np.exp(-t * 4.2) * (1 - np.exp(-t * 500))
    s = np.sin(2*np.pi*f*t) + .45*bright*np.sin(2*np.pi*2*f*t) + .2*bright*np.sin(2*np.pi*3*f*t) + .08*np.sin(2*np.pi*4*f*t)
    return s * env

def bass(f, d):
    t = tarr(d)
    env = np.exp(-t * 3.0) * (1 - np.exp(-t * 300))
    return (np.sin(2*np.pi*f*t) + .3*np.sin(2*np.pi*2*f*t)) * env

def pad(f, d, att=.6):
    t = tarr(d)
    env = np.minimum(t / att, 1) * np.minimum((d - t) / .8, 1)
    env = np.clip(env, 0, 1)
    return (np.sin(2*np.pi*f*t) + .5*np.sin(2*np.pi*f*1.005*t) + .25*np.sin(2*np.pi*2*f*t)) * env

def bell(f, d, dec=3.0):
    t = tarr(d)
    env = np.exp(-t * dec) * (1 - np.exp(-t * 800))
    return (np.sin(2*np.pi*f*t) + .6*np.sin(2*np.pi*f*2.76*t) + .35*np.sin(2*np.pi*f*5.4*t)) * env

def nz(d): return rng.standard_normal(int(d * SR))

def bandnoise(d, lo, hi):
    n = int(d * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    y = np.fft.irfft(X, n)
    return y / (np.max(np.abs(y)) + 1e-9)

def thud(d=.35, f0=130, f1=45):
    t = tarr(d)
    ph = 2*np.pi*np.cumsum(f0 * (f1 / f0) ** (t / d)) / SR
    return (np.sin(ph) * np.exp(-t * 11) + .35 * bandnoise(d, 200, 2500) * np.exp(-t * 40))

def whoosh(d=.35):
    t = tarr(d)
    y = bandnoise(d, 500, 5000)
    return y * np.sin(np.pi * t / d) ** 2 * .6

def tick(d=.05, f=1800):
    t = tarr(d)
    return (bandnoise(d, 800, 6000) * .6 + np.sin(2*np.pi*f*t)) * np.exp(-t * 90)

def blip(f0, f1, d=.12):
    t = tarr(d)
    ph = 2*np.pi*np.cumsum(f0 * (f1 / f0) ** (t / d)) / SR
    return np.sin(ph) * np.exp(-t * 22)

def slide(f0, f1, d=.5):
    t = tarr(d)
    ph = 2*np.pi*np.cumsum(f0 * (f1 / f0) ** (t / d)) / SR
    return (np.sin(ph) + .5 * np.sign(np.sin(ph)) * .3) * np.minimum(t / .02, 1) * np.minimum((d - t) / .05, 1)

def sparkle(t0, buf, g=1.0):
    for i, m in enumerate([84, 88, 91, 96, 100]):
        put(buf, t0 + i * .07, bell(fq(m), .5, 7), g * .5)

# ------------------------------------------------------------------ music
M = np.zeros(N)
CH = {'C': ([60, 64, 67], 36), 'G': ([59, 62, 67], 43), 'Am': ([60, 64, 69], 45), 'F': ([60, 65, 69], 41),
      'E': ([59, 64, 68], 40), 'Dm': ([57, 62, 65], 38), 'C2': ([64, 67, 72], 36), 'G2': ([62, 67, 71], 43)}

def ragtime(t0, t1, prog, bpm, melody=True, tick_on=False, vol=1.0):
    B = 60 / bpm; bar = 4 * B; i = 0; t = t0
    while t < t1 - .01:
        name = prog[i % len(prog)]; notes, root = CH[name]
        for b in range(4):
            tb = t + b * B
            if tb >= t1: break
            if b in (0, 2):
                put(M, tb, bass(fq(root + (7 if b == 2 else 0)), B * .9), .9 * vol)
            else:
                for m in notes: put(M, tb, pluck(fq(m - 12), B * .8, .8), .22 * vol)
            if melody:
                for h in range(2):
                    th = tb + h * B / 2
                    pat = [2, 1, 2, 0, 1, 2, 1, 0]
                    m = notes[pat[(b * 2 + h + i) % 8] % 3] + 12
                    if (b * 2 + h + i) % 3 != 2:
                        put(M, th, pluck(fq(m), B * .6, 1.0), .26 * vol)
            if tick_on and b in (1, 3):
                put(M, tb, tick(.04, 1500), .12 * vol)
        t += bar; i += 1

def arps(t0, t1, prog, bpm, oct_=0, vol=1.0, padv=.0):
    B = 60 / bpm; bar = 4 * B; i = 0; t = t0
    while t < t1 - .01:
        name = prog[i % len(prog)]; notes, root = CH[name]
        if padv:
            for m in notes: put(M, t, pad(fq(m - 12 + oct_), min(bar, t1 - t) + .4), padv * vol)
        put(M, t, bass(fq(root), bar * .9), .7 * vol)
        for k in range(8):
            tb = t + k * B / 2
            if tb >= t1: break
            m = notes[[0, 1, 2, 1, 0, 1, 2, 1][k]] + oct_
            put(M, tb, pluck(fq(m), B * 1.0, .7), .3 * vol)
        t += bar; i += 1

ragtime(0, 22.6, ['C', 'G', 'Am', 'F'], 104, True, False, .9)
ragtime(22.6, 53.0, ['C', 'G', 'Am', 'F', 'C', 'F', 'G', 'C'], 112, True, True, 1.0)
arps(53.0, 59.0, ['Am', 'F', 'C', 'G'], 80, 0, .9, .10)
arps(59.0, 68.2, ['Am', 'Dm', 'E', 'Am'], 66, -12, .8, .14)
arps(68.2, DUR, ['F', 'C2', 'G2', 'C'], 72, 0, .9, .16)
# final warm chord + bell
for m in [48, 55, 60, 64, 67]: put(M, 71.6, pad(fq(m), DUR - 71.6, 1.2), .18)
put(M, 72.0, bell(fq(84), 3.0, 1.4), .3); put(M, 73.2, bell(fq(88), 2.4, 1.6), .22)

# rain bed
t = tarr(DUR); rain = bandnoise(DUR, 1500, 9000) * .5
renv = np.clip((t - 59.0) / 1.5, 0, 1) * np.clip((68.6 - t) / 1.8, 0, 1)
M += rain * renv * .35

# ------------------------------------------------------------------ sfx
S = np.zeros(N)
put(S, .22, thud(.4), 1.0)
put(S, 2.45, bell(fq(88), .8, 6), .6)
for k, x in enumerate([6.3, 6.5, 6.75]): put(S, x, blip(500 + 150 * k, 180, .1), .6)
for x in [8.6, 14.55, 22.6, 28.2, 34.3, 39.0, 43.5, 47.9, 53.0]: put(S, x - .05, whoosh(.3), .5)
for k in range(6): put(S, 12.3 + k * .1, thud(.25, 110, 50), .55)
put(S, 12.45, slide(330, 247, .45), .35); put(S, 12.95, slide(247, 165, .7), .35)
put(S, 20.1, bandnoise(.25, 1500, 7000) * np.hanning(int(.25 * SR)), .5)
for k, m in enumerate([72, 76, 79, 84]): put(S, 21.3 + k * .08, bell(fq(m), .9, 4), .5)
for k in range(int((28.2 - 22.6) / .31)): put(S, 22.6 + k * .31, thud(.1, 220, 80), .6)
sparkle(29.05, S, .8); put(S, 29.5, blip(260, 620, .2), .6); put(S, 31.55, bandnoise(.18, 2500, 9000) * np.hanning(int(.18 * SR)), .6)
put(S, 34.5, whoosh(1.4), .5); put(S, 36.2, thud(.4, 150, 55), 1.0)
put(S, 37.45, slide(392, 175, .7), .45)
for k in range(8): put(S, 39.15 + k * .27, thud(.09, 240, 90), .55)
for x in [41.45, 41.62]: put(S, x, bell(fq(96), .35, 12), .7)
put(S, 42.45, bell(fq(88), 1.0, 4), .6); put(S, 42.6, bell(fq(95), 1.0, 4), .5)
for k in range(4): put(S, 43.75 + k * .28, tick(.08, 2600), 1.0)
put(S, 44.6, bandnoise(.4, 3000, 10000) * np.hanning(int(.4 * SR)), .5)
for k, x in enumerate([45.5, 45.9, 46.3]): put(S, x, blip(450 + 120 * k, 200, .1), .6)
put(S, 48.25, bell(fq(91), .9, 5), .6); sparkle(48.3, S, .5)
for k in range(7): put(S, 50.25 + k * .3, tick(.05, 1400), .9)
put(S, 52.5, thud(.3, 170, 60), .9)
put(S, 53.25, slide(300, 600, .25), .4); put(S, 53.45, bell(fq(84), .8, 5), .5)
put(S, 56.0, bell(fq(79), .9, 4), .4)
for x in [57.5, 57.7]: put(S, x, blip(700, 900, .1), .5)
for k in range(2): put(S, 62.3 + k * .35, thud(.22, 100, 55), .35)
put(S, 62.65, whoosh(.5), .4)
put(S, 64.4, bell(fq(55), 3.5, 1.1), .9); put(S, 66.4, bell(fq(55), 3.0, 1.3), .55)
put(S, 69.6, thud(.4, 150, 55), .9)
put(S, 71.5, bell(fq(48), 3.0, 1.2), .5)

# ------------------------------------------------------------------ levels: music + sfx at HALF the voice level
act = np.abs(v) > .01
vrms = np.sqrt(np.mean(v[act] ** 2)); vpk = np.max(np.abs(v))
# normalise the voice so it carries the mix (peak -2 dBFS)
gv = .8 / vpk; v = v * gv; vrms *= gv; vpk *= gv
mrms = np.sqrt(np.mean(M ** 2)); M *= (.5 * vrms) / mrms
spk = np.max(np.abs(S)); S *= (.5 * vpk) / spk
mix = v + M + S
pk = np.max(np.abs(mix))
if pk > .97: mix *= .97 / pk; v *= .97 / pk; M *= .97 / pk; S *= .97 / pk
print('voice rms %.4f peak %.3f | music rms %.4f (%.2fx voice) | sfx peak %.3f (%.2fx voice peak) | mix peak %.3f' % (
    np.sqrt(np.mean(v[act] ** 2)), np.max(np.abs(v)), np.sqrt(np.mean(M ** 2)), np.sqrt(np.mean(M ** 2)) / np.sqrt(np.mean(v[act] ** 2)),
    np.max(np.abs(S)), np.max(np.abs(S)) / np.max(np.abs(v)), np.max(np.abs(mix))))
import wave as _w
def _wr(name,x):
    with _w.open(name,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.clip(x,-1,1)*32767).astype(np.int16).tobytes())
_wr('stem_voice_orig.wav',v);_wr('stem_music_sfx_orig.wav',M+S)
st = np.stack([mix, mix], 1)
with wave.open('mix.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
