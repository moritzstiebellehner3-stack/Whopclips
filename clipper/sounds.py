"""Schneidet lizenzfreie Tracks (campaigns/music.json, Mixkit) auf die stärksten ~28 s inkl. Drop – für Moritz' CapCut-Edits.

    python -m clipper.sounds 2026-10-26

Ausgabe: output/<Tag>/sounds/NN_<Vibe>_<Titel>_<BPM>BPM.mp3 (−14 LUFS, Fade-in/out).
Die MP3s nicht öffentlich ins Repo/auf den Branch `videos` legen (Mixkit erlaubt keine Weitergabe der Rohdateien).
Beliebte Copyright-Sounds gibt es nur als Linkliste (SOUNDS.md) zum Auswählen in der App.
"""
import argparse
import json
import subprocess
from pathlib import Path

import librosa
import numpy as np

from clipper.batch import MUSIC, ROOT, music_file
from clipper.edit import analyse

PICKS = [  # (Track aus campaigns/music.json, Vibe für den Dateinamen)
    ("thunder", "Phonk-Drop"), ("trap", "Dark-Trap"), ("trapanomics", "Money-Trap"), ("head-bang", "Hard-Trap"),
    ("sparta", "Hype"), ("epical-drums-01", "Epic"), ("driving-ambition", "Motivation"),
    ("dreaming-big", "Motivation-Piano"), ("tears-of-joy", "Emotional"), ("silent-descent", "Cinematic"),
]
LENGTH = 28.0


def cut(name: str, vibe: str, idx: int, out_dir: Path) -> Path:
    src = music_file(name)
    _, period = analyse(src, None)
    # größter Lautheitssprung (Sekundenraster), der noch ein volles 28-s-Fenster dahinter hat
    y, sr = librosa.load(src, sr=22050)
    rms = librosa.feature.rms(y=y)[0]
    t = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    sec = np.array([rms[(t >= k) & (t < k + 1)].mean() for k in range(int(t[-1]))])
    jumps = np.diff(sec)
    last = len(sec) - int(LENGTH) + 3
    j = int(np.argmax(jumps[3:last])) + 4 if last > 4 else 4
    start = float(j - 4)  # Drop nach ~4 s, damit man ihn im Edit sofort hat
    title = MUSIC[name]["title"].replace(" ", "-")
    out = out_dir / f"{idx:02d}_{vibe}_{title}_{round(60 / period)}BPM.mp3"
    # zwei Durchgänge: erst messen, dann linear auf −14 LUFS (einfacher loudnorm landete bis −16)
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{start:.2f}", "-t", str(LENGTH), "-i", src,
                            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-t", str(LENGTH), "-i", src,
                    "-af", f"{norm},afade=t=in:d=0.3,afade=t=out:st={LENGTH - 1.5}:d=1.5",
                    "-ar", "44100", "-b:a", "192k", str(out)], check=True)
    print(f"{out.name}: Start {start:.1f} s, Drop bei 4 s", flush=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("day")
    out_dir = ROOT / "output" / p.parse_args().day / "sounds"
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, (name, vibe) in enumerate(PICKS, 1):
        cut(name, vibe, i, out_dir)
