"""Kurze B-Roll-Schnipsel (Autos, Uhren, Luxus) für Moritz' eigene Edits: 9:16, ohne Text, ohne Musik, ohne Ton.

    python -m clipper.broll edits/2026-10-26-broll.json

Plan:
    {"day": "2026-10-26", "clips": [
        {"name": "Juliano_Lamborghini-Urus_01", "src": "work/sources/juliano/ID.mp4", "start": 23.6, "dur": 1.6,
         "cx": 0.5, "precrop": "iw:ih*0.65:0:ih*0.35"}]}
- `precrop` (ffmpeg-crop) schneidet vorher Logos/Overlays/eingebrannte Schrift weg
- `cx` = wo das Motiv steht (0 = links, 1 = rechts); daraus wird der 9:16-Ausschnitt
Ausgabe: output/<day>/broll/<name>.mp4 – `python -m clipper.publish <day>` legt sie nach Luxus-B-Roll/.
"""
import argparse
import json
import subprocess
from pathlib import Path

from clipper.batch import ROOT
from clipper.render import H, W


def render(c: dict, out: Path) -> None:
    pre = f"crop={c['precrop']}," if c.get("precrop") else ""
    cx = c.get("cx", 0.5)
    vf = (f"{pre}crop='min(iw,ih*9/16)':'min(ih,iw*16/9)':'max(0,min(iw-ow,iw*{cx}-ow/2))':(ih-oh)/2,"
          f"scale={W}:{H}:flags=lanczos,eq=contrast=1.05:saturation=1.1,fps=30,format=yuv420p")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["start"]), "-t", str(c["dur"]),
                    "-i", str(ROOT / c["src"]), "-vf", vf, "-an", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "16", "-movflags", "+faststart", str(out)], check=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("plan", type=Path)
    plan = json.loads(p.parse_args().plan.read_text())
    out_dir = ROOT / "output" / plan["day"] / "broll"
    out_dir.mkdir(parents=True, exist_ok=True)
    for c in plan["clips"]:
        render(c, out_dir / f"{c['name']}.mp4")
        print("fertig:", c["name"], flush=True)
