# Soft corporate underscore (synthesized, royalty-free) ducked under the VO, plus transition ticks.
import sys, json, wave
import numpy as np
TMP = sys.argv[1]; SR = 44100
TL = json.load(open(f"{TMP}/timeline.json")); TOTAL = TL["total"] + 2.3; N = int(TOTAL * SR)
vo = np.load(f"{TMP}/vo.npy"); vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
vo = vo / (np.abs(vo).max() + 1e-9) * 0.89
t = np.arange(N) / SR
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
BPM = 100; BEAT = 60 / BPM; BAR = BEAT * 4
prog = [(57, [57, 60, 64, 67]), (53, [53, 57, 60, 64]), (48, [48, 52, 55, 59]), (55, [55, 59, 62, 66])]  # Am9-Fmaj7-Cmaj7-G
mus = np.zeros(N)
nb = int(TOTAL / BAR) + 1
for b in range(nb):
    root, ch = prog[b % 4]; s0 = int(b * BAR * SR); n = int(BAR * SR * 1.25); seg = np.arange(n) / SR
    env = np.minimum(1, seg / 0.9) * np.clip((BAR * 1.25 - seg) / 0.9, 0, 1)
    pad = sum(np.sin(2 * np.pi * mtof(m + 12) * seg + d) * 0.5 + np.sin(2 * np.pi * mtof(m + 12) * 1.003 * seg) * 0.5 for d, m in enumerate(ch)) / len(ch)
    bass = np.sin(2 * np.pi * mtof(root - 12) * seg) * np.exp(-seg * 0.8)
    e = min(N, s0 + n); mus[s0:e] += (pad * env * 0.55 + bass * 0.35)[:e - s0]
    for k in range(8):  # soft eighth-note pluck
        ps = s0 + int(k * BEAT / 2 * SR); m = ch[(k * 3) % 4] + 24; pn = int(0.4 * SR); ss = np.arange(pn) / SR
        pl = np.sin(2 * np.pi * mtof(m) * ss) * np.exp(-ss * 9) * (0.22 if k % 2 == 0 else 0.13)
        pe = min(N, ps + pn); mus[ps:pe] += pl[:pe - ps]
# fade in/out
mus *= np.minimum(1, t / 1.5) * np.clip((TOTAL - t) / 2.5, 0, 1)
mus = mus / (np.abs(mus).max() + 1e-9)
# ducking from VO envelope
env = np.convolve(np.abs(vo), np.ones(4410) / 4410, mode="same"); env = np.convolve(env, np.ones(8820) / 8820, mode="same")
duck = 1 - 0.55 * np.clip(env / 0.05, 0, 1)
music = mus * 0.16 * duck
# transition ticks
for sc in TL["scenes"][1:]:
    i = int((sc["start"] - 0.25) * SR); n = int(0.25 * SR); ss = np.arange(n) / SR
    tick = (np.sin(2 * np.pi * 1760 * ss) * 0.5 + np.sin(2 * np.pi * 2640 * ss) * 0.3) * np.exp(-ss * 30) * 0.07
    music[i:i + n] += tick[:max(0, min(n, N - i))]
L = vo + music; R = vo + music
mx = max(np.abs(L).max(), 1e-9); L /= mx / 0.95; R /= mx / 0.95
with wave.open(f"{TMP}/mix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([L, R], 1) * 32767).astype(np.int16).tobytes())
print("mix", TOTAL)
