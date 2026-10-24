"""Rendert alle Clips eines Tages aus einer Plan-Datei und schreibt die Captions zum Kopieren.

    python -m clipper.batch plans/2026-10-24.json

Plan-Format (eine Liste):
    [{"campaign": "tjr", "platform": "tiktok", "src": "work/sources/tjr/ID.mp4",
      "start": 6.4, "end": 59.2, "layout": "crop", "hook": "...", "caption": "...", "sound": "..."}]
"""
import argparse
import json
from pathlib import Path

from clipper.render import render

ROOT = Path(__file__).resolve().parent.parent


def main(plan_path: Path, only: str | None) -> None:
    plan = json.loads(plan_path.read_text())
    day = plan_path.stem
    out_dir = ROOT / "output" / day
    notes = [f"# Clips {day}\n"]

    for c in plan:
        out = out_dir / c["campaign"] / f"{c['platform']}.mp4"
        if not only or only in str(out):
            src = Path(c["src"])
            words = src.with_suffix(".words.json")
            render(argparse.Namespace(
                src=str(src), words=str(words) if words.exists() else None,
                start=c["start"], end=c["end"], hook=c.get("hook", ""), out=str(out),
                layout=c.get("layout", "fit"), zoom=c.get("zoom", 1.25), crop_x=c.get("crop_x", 0.5),
                precrop=c.get("precrop"), music=c.get("music"), music_vol=c.get("music_vol", 0.10),
            ))
            print(f"fertig: {out}", flush=True)
        notes.append(
            f"## {c['campaign'].upper()} – {c['platform']}\n"
            f"Datei: `{out.relative_to(ROOT)}`  \n"
            f"Caption:\n```\n{c['caption']}\n```\n"
            f"Sound-Tipp: {c.get('sound', '-')}  \n"
            f"Quelle: {c.get('source_url', c['src'])} ({c['start']}s–{c['end']}s)\n"
        )
    (out_dir / "CAPTIONS.md").write_text("\n".join(notes))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("plan", type=Path)
    p.add_argument("--only", help="nur Clips rendern, deren Pfad das enthält, z. B. 'tjr/tiktok'")
    a = p.parse_args()
    main(a.plan, a.only)
