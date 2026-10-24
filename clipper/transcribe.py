"""Transkribiert ein Video/Audio mit faster-whisper und speichert Wörter mit Zeitstempeln.

Ausgabe: <name>.words.json (für Untertitel) und <name>.txt (Absätze mit Zeitmarken zum Aussuchen der Clips).

    python -m clipper.transcribe work/sources/VIDEO.mp4 --model small.en
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel


def fmt(t: float) -> str:
    return f"{int(t // 60):02d}:{t % 60:05.2f}"


def transcribe(path: Path, model_name: str) -> None:
    # Audio selbst mit ffmpeg dekodieren (funktioniert mit jeder Video-/Audiodatei)
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
        check=True, capture_output=True,
    ).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio, word_timestamps=True, vad_filter=True, language="en")

    words, lines = [], []
    for seg in segments:
        for w in seg.words:
            words.append({"start": round(w.start, 2), "end": round(w.end, 2), "word": w.word.strip()})
        lines.append(f"[{fmt(seg.start)} - {fmt(seg.end)}] {seg.text.strip()}")
        print(lines[-1], flush=True)

    stem = path.with_suffix("")
    Path(f"{stem}.words.json").write_text(json.dumps(words))
    Path(f"{stem}.txt").write_text("\n".join(lines))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("audio", type=Path)
    p.add_argument("--model", default="small.en")
    a = p.parse_args()
    transcribe(a.audio, a.model)
