"""Holt Moritz' Rohmaterial in die Cloud: Videos\\Whop-Campaign\\Material auf seinem PC → privates Repo → work/material/.

    python -m clipper.material               # holen und auflisten (neu = noch kein Transkript)
    python -m clipper.material --transcribe  # dazu alle neuen Videos transkribieren

Der PC-Task „Whop-Clips holen“ (`tools/whop-sync.ps1`) lädt den Ordner alle 30 Minuten hoch; Videos über 95 MB
kommen in Teilen (`_teile/<Name>.partNNN`) und werden hier wieder zusammengesetzt.
Das Repo `moritzstiebellehner3-stack/Whop-Material` muss zur Session hinzugefügt sein (privat).
"""
import argparse
import subprocess

from clipper.batch import ROOT
from clipper.transcribe import transcribe

OUT = ROOT / "work" / "material"
MEDIA = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".mp3", ".m4a", ".wav"}


def git(*args, cwd=None):
    subprocess.run(["git", *args], cwd=cwd, check=True)


def assemble() -> None:
    """Große Videos kommen vom PC als _teile/<Name>.part001, .part002 … (GitHub-Grenze 100 MB pro Datei)."""
    groups = {}
    for part in sorted((OUT / "_teile").rglob("*.part[0-9][0-9][0-9]")):
        groups.setdefault(part.relative_to(OUT / "_teile").with_suffix(""), []).append(part)
    for rel, parts in groups.items():
        target = OUT / rel
        size = sum(p.stat().st_size for p in parts)
        if target.exists() and target.stat().st_size == size:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as out:
            for p in parts:
                out.write(p.read_bytes())
        print(f"zusammengesetzt: {rel} ({len(parts)} Teile)")


def fetch() -> None:
    if (OUT / ".git").exists():
        git("fetch", "--quiet", "--depth", "1", "origin", "main", cwd=OUT)
        git("reset", "--quiet", "--hard", "FETCH_HEAD", cwd=OUT)  # Transkripte (ungetrackt) bleiben liegen
        return
    url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True, text=True,
                         check=True).stdout.strip()
    git("clone", "--quiet", "--depth", "1", url.rsplit("/", 1)[0] + "/Whop-Material", str(OUT))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--transcribe", action="store_true")
    a = p.parse_args()
    fetch()
    assemble()
    for f in sorted(x for x in OUT.rglob("*") if x.suffix.lower() in MEDIA and ".git" not in x.parts):
        done = f.with_suffix(".words.json").exists()
        if a.transcribe and not done:
            transcribe(f, "small.en")
            done = True
        print(f"{'   ' if done else 'NEU'}  {f.stat().st_size / 1e6:6.1f} MB  {f.relative_to(OUT)}")
