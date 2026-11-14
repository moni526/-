import sys, subprocess, wave, json, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from script import SCENES
FF = sys.argv[1]; TMP = sys.argv[2]; RATE = sys.argv[3] if len(sys.argv) > 3 else "+0%"
VOICE = sys.argv[4] if len(sys.argv) > 4 else "ko-KR-InJoonNeural"   # Microsoft neural voice via edge-tts
EDGE = os.path.join(os.path.dirname(sys.executable), "edge-tts")
SR = 44100
def clip(text, path):
    mp3 = path + ".mp3"
    for _ in range(4):
        r = subprocess.run([EDGE, "--voice", VOICE, f"--rate={RATE}", "--text", text, "--write-media", mp3], capture_output=True)
        if r.returncode == 0 and os.path.getsize(mp3) > 1000: break
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", path], check=True)
    with wave.open(path) as w: d = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    # trim silence
    idx = np.where(np.abs(d) > 0.008)[0]
    return d[max(0, idx[0] - 800): idx[-1] + 2000] if len(idx) else d
GAP_S, GAP_SC, LEAD = 0.18, 0.45, 0.45
tl = []; parts = []; t = LEAD
parts.append(np.zeros(int(LEAD * SR)))
for si, (name, sents) in enumerate(SCENES):
    sc = dict(name=name, start=t, cues=[])
    for k, s in enumerate(sents):
        d = clip(s, f"{TMP}/vo_{si:02d}_{k}.wav")
        sc["cues"].append(dict(t=t, dur=len(d) / SR, text=s))
        parts.append(d); t += len(d) / SR
        g = GAP_S if k < len(sents) - 1 else GAP_SC
        parts.append(np.zeros(int(g * SR))); t += g
    sc["end"] = t; tl.append(sc)
vo = np.concatenate(parts)
np.save(f"{TMP}/vo.npy", vo)
json.dump(dict(scenes=tl, total=t), open(f"{TMP}/timeline.json", "w"), ensure_ascii=False, indent=1)
print("total %.1fs" % t); [print(f"{s['name']:<10} {s['start']:6.1f} → {s['end']:6.1f} ({s['end']-s['start']:.1f}s)") for s in tl]
