"""Holt Ausschnitte aus TJRs Kick-VODs (offizielle Quelle) – z. B. das Stream-Ende, wo er Real Talk redet.

    python -m clipper.kickvod list                                   # VODs mit Länge und Titel
    python -m clipper.kickvod get 132109909 --tail 25                # letzte 25 min in 160p (zum Transkribieren)
    python -m clipper.kickvod get 132109909 --from 8150 --to 8200 --quality 1080p60   # Clip-Ausschnitt in voller Qualität

Lädt die HLS-Segmente direkt (über den Proxy der Umgebung) und hängt sie mit ffmpeg zusammen.
Die Zeiten (--from/--to) sind Sekunden ab Stream-Beginn; die Ausgabe beginnt am ersten Segment davor,
der Versatz steht im Dateinamen-Begleiter `<datei>.offset`.
"""
import argparse
import json
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from clipper.batch import ROOT

API = "https://kick.com/api/v2/channels/tjr/videos"
OUT = ROOT / "work" / "sources" / "tjr_vod"
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def vods() -> list[dict]:
    return json.loads(fetch(API))


def segments(source: str, quality: str) -> list[tuple[float, float, str]]:
    """(Start, Dauer, URL) aller Segmente einer Qualitätsstufe."""
    base = source.rsplit("/", 1)[0] + f"/{quality}/"
    out, t, dur = [], 0.0, 0.0
    for line in fetch(base + "playlist.m3u8").decode().splitlines():
        if line.startswith("#EXTINF:"):
            dur = float(line[8:].split(",")[0])
        elif line and not line.startswith("#"):
            out.append((t, dur, base + line))
            t += dur
    return out


def get(vod_id: int, start: float | None, end: float | None, tail: float | None, quality: str) -> Path:
    v = next(v for v in vods() if v["id"] == vod_id)
    segs = segments(v["source"], quality)
    total = segs[-1][0] + segs[-1][1]
    if tail:
        start, end = total - tail * 60, total
    start, end = start or 0.0, end or total
    pick = [s for s in segs if s[0] + s[1] > start and s[0] < end]
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"vod{vod_id}_{round(pick[0][0])}-{round(pick[-1][0] + pick[-1][1])}_{quality}.mp4"
    with tempfile.TemporaryDirectory() as tmp:
        lst = Path(tmp) / "list.txt"
        with lst.open("w") as f:
            for i, (_, _, url) in enumerate(pick):
                (Path(tmp) / f"{i}.ts").write_bytes(fetch(url))
                f.write(f"file '{i}.ts'\n")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", "-bsf:a", "aac_adtstoasc", str(out)], check=True)
    out.with_suffix(".offset").write_text(f"{pick[0][0]:.3f}\n")
    print(f"{out}  (beginnt bei {pick[0][0]:.1f} s im Stream)")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    g = sub.add_parser("get")
    g.add_argument("vod", type=int)
    g.add_argument("--from", dest="start", type=float)
    g.add_argument("--to", dest="end", type=float)
    g.add_argument("--tail", type=float, help="letzte N Minuten")
    g.add_argument("--quality", default="160p30", help="160p30, 360p30, 480p30, 720p60 oder 1080p60")
    a = p.parse_args()
    if a.cmd == "list":
        for v in vods():
            print(v["id"], v["created_at"][:10], f"{v['duration'] // 60000:4d} min", v["session_title"][:70])
    else:
        get(a.vod, a.start, a.end, a.tail, a.quality)
