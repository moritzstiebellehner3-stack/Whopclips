"""Legt die fertigen Clips eines Tages auf den Branch `videos`, von dem Moritz' PC sie automatisch abholt.

    python -m clipper.publish 2026-10-25            # einen Tag dazunehmen
    python -m clipper.publish 2026-10-24 2026-10-25

Ablauf:
1. `output/Whop-Campaign/<Datum>/<TJR|Juliano>/<Kampagne>_<Plattform>.mp4` + `_Caption.txt` + `Alle_Captions.md`
   aus `plans/<Datum>.json` und `edits/<Datum>-*.json` bauen
2. die letzten 7 Tage als EINEN Commit ohne Vorgänger auf `videos` pushen (force), damit das Repo nicht wächst

Auf dem PC holt `tools/whop-sync.ps1` (Aufgabenplaner, bei Anmeldung + alle 30 min) den Branch nach
`%USERPROFILE%\\Videos\\Whop-Campaign` – nur dazukopieren, nie löschen.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from clipper.batch import ROOT

OUT = ROOT / "output" / "Whop-Campaign"
BRANCH_DIR = ROOT / "work" / "videos-branch"
KEEP_DAYS = 7
NAMES = {"tjr": "TJR", "juliano": "Juliano"}
PLATFORMS = {"tiktok": "TikTok", "instagram": "Instagram", "youtube": "YouTube"}


def clips_for(day: str) -> list[dict]:
    """Alle fertigen Clips eines Tages: aus dem Tagesplan und aus den Edit-Plänen (Edit gewinnt bei gleicher Datei)."""
    clips = {}
    plan = ROOT / "plans" / f"{day}.json"
    if plan.exists():
        for c in json.loads(plan.read_text()):
            out = ROOT / "output" / day / c["campaign"] / f"{c['platform']}.mp4"
            clips[out] = {"out": out, "campaign": c["campaign"], "name": c["platform"], "caption": c["caption"]}
    for e in sorted((ROOT / "edits").glob(f"{day}-*.json")):
        p = json.loads(e.read_text())
        out = ROOT / p["out"]
        clips[out] = {"out": out, "campaign": out.parent.name, "name": out.stem, "caption": p.get("caption", "")}
    return [c for c in clips.values() if c["out"].exists()]


def build_day(day: str) -> Path:
    base = OUT / day
    if base.exists():
        shutil.rmtree(base)
    notes = [f"# Clips {day}\n"]
    for c in clips_for(day):
        camp = NAMES.get(c["campaign"], c["campaign"])
        plat = PLATFORMS.get(c["name"], c["name"].replace("_", " ").title().replace(" ", "_"))
        name = f"{camp}_{plat}"
        (base / camp).mkdir(parents=True, exist_ok=True)
        shutil.copy(c["out"], base / camp / f"{name}.mp4")
        where = PLATFORMS.get(c["name"], "TikTok, Instagram oder YouTube")
        (base / camp / f"{name}_Caption.txt").write_text(
            f"{c['caption']}\n\n---\nPosten auf: {where}\n"
            "Nach dem Posten: Link innerhalb von 30 Minuten in Content Rewards (Whop) einreichen!\n")
        notes.append(f"## {camp} – {plat}\nDatei: `{camp}/{name}.mp4`\n```\n{c['caption']}\n```\n")
    (base / "Alle_Captions.md").write_text("\n".join(notes))
    return base


def git(*args, cwd=BRANCH_DIR):
    subprocess.run(["git", "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", *args],
                   cwd=cwd, check=True)


def push() -> None:
    """Die letzten 7 Tage als einzelnen Commit auf `videos` (force) – alte Tage verschwinden aus dem Branch."""
    days = sorted(p.name for p in OUT.iterdir() if p.is_dir())[-KEEP_DAYS:]
    if BRANCH_DIR.exists():
        shutil.rmtree(BRANCH_DIR)
    BRANCH_DIR.mkdir(parents=True)
    git("init", "-q", "-b", "videos")
    for d in days:
        shutil.copytree(OUT / d, BRANCH_DIR / d)
    (BRANCH_DIR / "README.md").write_text(
        "Fertige Clips der letzten 7 Tage. Wird automatisch überschrieben.\n"
        "Moritz' PC holt sie mit `tools/whop-sync.ps1` (Branch `claude/serene-gauss-am057q`) nach "
        "`Videos\\Whop-Campaign`.\n")
    git("add", "-A")
    git("commit", "-q", "-m", f"Clips {days[0]} bis {days[-1]}")
    url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True, text=True,
                         check=True).stdout.strip()
    git("push", "--force", url, "videos:videos")
    print(f"veröffentlicht: {', '.join(days)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("days", nargs="+")
    for d in p.parse_args().days:
        print("gebaut:", build_day(d))
    push()
