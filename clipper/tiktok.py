"""TikTok-Videos über das offizielle Embed-Widget laden (ohne Browser-Impersonation, ohne Bot-Schutz zu umgehen).

    python -m clipper.tiktok list thewolfofinsurance                 # neueste Videos mit Aufrufen
    python -m clipper.tiktok get 7696641697165348126 work/sources/juliano

Nur für Accounts verwenden, die eine Kampagne ausdrücklich als Quelle erlaubt (oder rein zur Stil-Analyse).
"""
import argparse
import json
import re
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.tiktok.com/"}


def _state(url: str) -> dict:
    html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode()
    return json.loads(re.search(r'id="__FRONTITY_CONNECT_STATE__"[^>]*>(.*?)</script>', html, re.S).group(1))


def _items(o):
    if isinstance(o, dict):
        if "id" in o and "desc" in o:
            yield o
        for v in o.values():
            yield from _items(v)
    elif isinstance(o, list):
        for v in o:
            yield from _items(v)


def list_user(user: str) -> list[dict]:
    """Die Videos, die das Profil-Embed zeigt (angepinnte + die neuesten, etwa 10–13 Stück)."""
    return [{"id": i["id"], "views": i.get("playCount"), "desc": i.get("desc", ""), "url": i.get("playAddr")}
            for i in _items(_state(f"https://www.tiktok.com/embed/@{user}"))]


def get(video_id: str, out_dir: Path) -> Path:
    data = _state(f"https://www.tiktok.com/embed/v2/{video_id}")["source"]["data"][f"/embed/v2/{video_id}"]
    info = data["videoData"]["itemInfos"]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{video_id}.mp4"
    req = urllib.request.Request(info["video"]["urls"][0], headers=UA)
    path.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    (out_dir / f"{video_id}.info.json").write_text(json.dumps(
        {"id": video_id, "text": info.get("text"), "views": info.get("playCount"),
         "url": f"https://www.tiktok.com/@{data['videoData']['authorInfos']['uniqueId']}/video/{video_id}"}, indent=1))
    return path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").add_argument("user")
    g = sub.add_parser("get")
    g.add_argument("id")
    g.add_argument("out_dir", type=Path)
    a = p.parse_args()
    if a.cmd == "list":
        for v in list_user(a.user):
            print(v["id"], v["views"], v["desc"][:70])
    else:
        print(get(a.id, a.out_dir))
