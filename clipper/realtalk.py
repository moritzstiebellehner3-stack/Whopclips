"""Kurze Clips (15–30 s) nach Moritz' 5 Vorlagen vom 25.10.2026.

TJR „Real Talk“ (style "tjr"):
- TJR redet einfach (Mindset, Real Talk) – kein Trading-Erklären, keine Charts, kein Hook
- Quadrat in der Mitte wie bei den TJR-Clip-Accounts, weicher Glow-Look
- Untertitel: 1–2 Wörter, weiß, fett, weicher Schatten, in der Bildmitte
- Musik leise unter der Stimme; am Ende ein Edit aus Luxus-Schnitten im Beat, der Drop sitzt auf dem ersten Schnitt

Juliano „Cold Call“ / „Hype“ (style "juliano"):
- schwarzes 9:16, Titel mit Emojis, Bild als Band mit weich gewölbten Kanten
- große weiße Serifen-Wörter (DM Serif Display) mitten im Bild, Schlüsselwörter extra groß – wie in seinen Podcast-Clips
- Musik am Anfang (er wartet auf den Call), aus während des Calls, danach wieder voll mit Energie

    python -m clipper.realtalk edits/2026-10-26-tjr-realtalk-noone.json

Plan:
    {"out": "output/2026-10-26/tjr/tiktok.mp4", "style": "tjr", "title": "", "music": "thunder", "drop": 52.0,
     "parts": [
        {"src": "...", "start": 1.0, "end": 9.0, "box": [x, y, w, h], "music": "under"},
        {"src": "...", "start": 0.0, "end": 2.0, "music": "full", "voice": false, "subs": false},
        {"edit": [{"src": "...", "start": 3.0, "box": [x, y, w, h]}, ...], "beats": 2}],
     "big": ["fire", "fight"], "fix": {"Kysonat": "Kai Cenat"}, "caption": "..."}
- music: "full" | "under" (−16 dB, `under_db`) | "off" | Zahl in dB
- box: Ausschnitt in der Quelle (Pixel), wird auf Quadrat/Band gefüllt; cx/cy verschieben den Ausschnitt darin
- frame: "tjr" | "juliano" | "full" oder [Breite, Höhe, y] für ein eigenes Band (z. B. 4:5 für Ganzkörper-Szenen)
- Der Drop fällt auf den Teil mit "sync": true, sonst auf den Anfang des Edits; `drop` = Hinweis in Sekunden im Song
"""
import argparse
import json
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from clipper.batch import ROOT, music_file
from clipper.core import title_layer, words_for
from clipper.edit import analyse
from clipper.render import H, W, censor, chunk_words

FPS = 30
FONTS = {
    "DMSerifDisplay": "https://fonts.gstatic.com/s/dmserifdisplay/v17/-nFnOHM81r4j6k0gjAW3mujVU2B2K_c.ttf",
    "Montserrat-ExtraBold": "https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvr70w-.ttf",
}
# Bildfläche je Stil: (Breite, Höhe, y-Position im 9:16)
FRAMES = {"tjr": (W, W, (H - W) // 2), "juliano": (W, 900, 500), "full": (W, H, 0)}
LOOK = {
    "tjr": "split[a][b];[b]gblur=sigma=26[g];[a][g]blend=all_mode=screen:all_opacity=0.12,"
           "eq=saturation=1.08:contrast=1.07:brightness=-0.03",
    "juliano": "eq=saturation=1.12:contrast=1.05,unsharp=5:5:0.5",
}
BULGE = 44  # Juliano: so viel höher ist das Band in der Mitte als am Rand (gewölbte Kanten wie in der Vorlage)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = ROOT / "work" / "fonts" / f"{name}.ttf"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(FONTS[name], path)
    return ImageFont.truetype(str(path), size)


def lens_layer(fw: int, fh: int, fy: int) -> Image.Image:
    """Schwarz mit einem Loch fürs Bild; Ober- und Unterkante zur Mitte hin gewölbt, weich auslaufend."""
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for x in range(W):
        k = (2 * x / (W - 1) - 1) ** 2
        d.line([(x, fy + BULGE * k), (x, fy + fh - BULGE * k)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(5))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    black.putalpha(mask.point(lambda v: 255 - v))
    return black


def shadowed(canvas: Image.Image, xy, text: str, f, blur: int, offset: int, alpha: int, fill) -> None:
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0], xy[1] + offset), text, font=f, fill=(0, 0, 0, alpha), anchor="mm")
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(canvas).text(xy, text, font=f, fill=fill, anchor="mm")


def tjr_words(text: str, y: int) -> Image.Image:
    """1–2 Wörter, weiß, fett, weicher Schatten (wie die TJR-Real-Talk-Vorlagen)."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size = 74
    while font("Montserrat-ExtraBold", size).getlength(text) > W * 0.84 and size > 40:
        size -= 4
    shadowed(canvas, (W // 2, y), text, font("Montserrat-ExtraBold", size), 7, 4, 210, "white")
    return canvas


def serif_words(text: str, y: int, big: bool) -> Image.Image:
    """Große weiße Serifen-Wörter mit weichem Schatten (wie Julianos Podcast-Clips); Schlüsselwörter extra groß."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size = 184 if big else 108
    while font("DMSerifDisplay", size).getlength(text) > W * 0.86 and size > 50:
        size -= 6
    shadowed(canvas, (W // 2, y), text, font("DMSerifDisplay", size), 12, 7, 190, (246, 246, 248, 255))
    return canvas


def caption_track(tmp: Path, name: str, base: Image.Image, chunks, start: float, dur: float, draw) -> Path:
    """ffconcat-Liste aus Vollbild-PNGs: Grundebene + jeweils ein Untertitel-Stück, mit exakten Anzeigedauern."""
    blank = tmp / f"{name}_blank.png"
    base.save(blank)
    frames, t = [], 0.0
    for i, c in enumerate(chunks):
        w0 = max(c[0]["start"] - start, t)
        nxt = chunks[i + 1][0]["start"] - start if i + 1 < len(chunks) else dur
        w1 = min(nxt, c[-1]["end"] - start + 0.6, dur)
        text = censor(" ".join(w["word"].strip() for w in c).strip(" ,"))
        if not text or w1 - w0 < 1 / FPS:
            continue
        if w0 > t:
            frames.append((blank, w0 - t))
        png = tmp / f"{name}_{i:03d}.png"
        Image.alpha_composite(base, draw(text)).save(png)
        frames.append((png, w1 - w0))
        t = w1
    if t < dur:
        frames.append((blank, dur - t))
    lst = tmp / f"{name}.ffconcat"
    lst.write_text("ffconcat version 1.0\n" + "".join(f"file '{p}'\nduration {d:.4f}\n" for p, d in frames)
                   + f"file '{frames[-1][0]}'\n")
    return lst


def chunks_for(words, style: str, big: set[str]):
    if style != "juliano":
        return chunk_words(words, max_words=2, max_gap=0.35)
    out = []
    for c in chunk_words(words, max_words=2, max_gap=0.35):
        cur = []
        for w in c:  # Schlüsselwörter stehen allein (und groß)
            if norm(w["word"]) in big:
                if cur:
                    out.append(cur)
                out.append([w])
                cur = []
            else:
                cur.append(w)
        if cur:
            out.append(cur)
    return out


def norm(word: str) -> str:
    return word.strip(" .,!?\"“”'").lower()


def picture(s: dict, frame: tuple[int, int, int], look: str, fx: str = "") -> str:
    """Ausschnitt (box) → auf die Bildfläche füllen → Look (+ Effekte nur im Bild) → auf 9:16 schwarz setzen."""
    fw, fh, fy = frame
    box = "crop={2}:{3}:{0}:{1},".format(*s["box"]) if "box" in s else ""
    return (f"setpts=PTS-STARTPTS,{box}scale={fw}:{fh}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={fw}:{fh}:(iw-ow)*{s.get('cx', 0.5)}:(ih-oh)*{s.get('cy', 0.5)},{look},{fx}"
            f"pad={W}:{H}:0:{fy}:black,setsar=1,fps={FPS}")


def encode(args: list[str], out: Path) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-an", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)], check=True)


def voice(src: Path | None, start: float, dur: float, out: Path) -> None:
    if src is None:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                        "-t", f"{dur:.4f}", str(out)], check=True)
        return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", f"{dur:.4f}", "-i", str(src), "-vn",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,apad", "-t", f"{dur:.4f}",
                    "-ar", "48000", "-ac", "2", str(out)], check=True)


def talk_part(tmp: Path, i: int, s: dict, plan: dict, frame, base: Image.Image) -> tuple[Path, Path, float]:
    src = ROOT / s["src"]
    style = plan["style"]
    frames = round((s["end"] - s["start"]) * FPS)
    dur = frames / FPS
    fw, fh, fy = frame
    if s.get("subs", True):
        big = {norm(b) for b in plan.get("big", [])}
        if style == "juliano":
            y = fy + int(fh * 0.7)
            draw = lambda text: serif_words(text, y, len(text.split()) == 1 and norm(text) in big)  # noqa: E731
        else:
            y = fy + int(fh * 0.68)
            draw = lambda text: tjr_words(text, y)  # noqa: E731
        words = words_for(src, s["start"], s["end"])
        for w in words:  # Whisper-Fehler korrigieren, z. B. {"Kysonat": "Kai Cenat"}
            for wrong, right in plan.get("fix", {}).items():
                w["word"] = re.sub(re.escape(wrong), right, w["word"], flags=re.I)
        lst = caption_track(tmp, f"p{i}", base, chunks_for(words, style, big), s["start"], dur, draw)
    else:
        lst = caption_track(tmp, f"p{i}", base, [], s["start"], dur, None)
    vf = (f"[0:v]{picture(s, frame, LOOK[style])}[pic];[1:v]format=rgba[ov];"
          f"[pic][ov]overlay=0:0:format=auto,format=yuv420p[v]")
    seg = tmp / f"p{i}.mp4"
    encode(["-ss", str(s["start"]), "-i", str(src), "-f", "concat", "-safe", "0", "-i", str(lst),
            "-filter_complex", vf, "-map", "[v]", "-frames:v", str(frames)], seg)
    wav = tmp / f"p{i}.wav"
    voice(src if s.get("voice", True) else None, s["start"], dur, wav)
    return seg, wav, dur


def edit_part(tmp: Path, i: int, s: dict, plan: dict, frame, base: Image.Image, period: float, last: bool):
    """Luxus-Schnitte im Beat: jeder Schnitt `beats` Schläge lang, kurzer Zoom-Punch, weißer Flash auf dem Drop."""
    segs, total = [], 0
    beats = s.get("beats", 2)
    for k, shot in enumerate(s["edit"]):
        n = round((k + 1) * beats * period * FPS) - round(k * beats * period * FPS)
        if shot.get("beats"):
            n = round(shot["beats"] * period * FPS)
        fw, fh, _ = frame
        punch = f"scale=w='iw*(1+0.07*max(0,1-t/0.22))':h=-2:eval=frame,crop={fw}:{fh},"
        flash = "fade=t=in:st=0:d=0.2:color=white," if k == 0 else ""
        out_fade = f"fade=t=out:st={n / FPS - 0.35:.3f}:d=0.35," if last and k == len(s["edit"]) - 1 else ""
        vf = (f"[0:v]{picture(shot, frame, LOOK[plan['style']], punch + flash + out_fade)},"
              f"format=rgba[pic];[pic][1:v]overlay=0:0,format=yuv420p[v]")
        seg = tmp / f"p{i}_{k}.mp4"
        encode(["-ss", str(shot["start"]), "-i", str(ROOT / shot["src"]), "-loop", "1", "-i", str(tmp / "base.png"),
                "-filter_complex", vf, "-map", "[v]", "-frames:v", str(n)], seg)
        segs.append(seg)
        total += n
    lst = tmp / f"p{i}.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in segs))
    seg = tmp / f"p{i}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(seg)], check=True)
    wav = tmp / f"p{i}.wav"
    voice(None, 0, total / FPS, wav)
    return seg, wav, total / FPS


def gain(level, under_db: float) -> float:
    if level == "full":
        return 1.0
    if level == "off":
        return 0.0
    db = under_db if level == "under" else float(level)
    return 10 ** (db / 20)


def build(plan_path: Path) -> None:
    plan = json.loads(plan_path.read_text())
    style = plan["style"]
    out = ROOT / plan["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    frame = tuple(plan["frame"]) if isinstance(plan.get("frame"), list) else FRAMES[plan.get("frame", style)]
    base = lens_layer(*frame) if style == "juliano" else Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if plan.get("title"):
        base = Image.alpha_composite(base, title_layer(plan["title"], y=frame[2] - 56, size=54))

    music = music_file(plan.get("music"))
    drop, period = analyse(music, plan.get("drop")) if music else (0.0, 0.5)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        base.save(tmp / "base.png")
        parts, levels = [], []
        n = len(plan["parts"])
        for i, s in enumerate(plan["parts"]):
            if "edit" in s:
                parts.append(edit_part(tmp, i, s, plan, frame, base, period, i == n - 1))
                levels.append(s.get("music", "full"))
            else:
                parts.append(talk_part(tmp, i, s, plan, frame, base))
                levels.append(s.get("music", "under"))
        starts = [sum(p[2] for p in parts[:k]) for k in range(n)]
        total = sum(p[2] for p in parts)
        sync = next((k for k, s in enumerate(plan["parts"]) if s.get("sync")),
                    next((k for k, s in enumerate(plan["parts"]) if "edit" in s), None))
        music_start = plan.get("music_start", drop - starts[sync] if sync is not None else 0.0)
        if music_start < 0:
            raise SystemExit(f"Drop bei {drop:.1f} s kommt zu früh für den Edit bei {starts[sync]:.1f} s – "
                             "anderen Song oder späteren `drop` wählen")

        (tmp / "v.txt").write_text("".join(f"file '{p[0]}'\n" for p in parts))
        (tmp / "a.txt").write_text("".join(f"file '{p[1]}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "v.txt"),
                        "-c", "copy", str(tmp / "video.mp4")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "a.txt"),
                        str(tmp / "voice.wav")], check=True)

        # Lautstärke-Hüllkurve der Musik: weiche Übergänge (0,25 s), auf dem Drop hart
        under = plan.get("under_db", -16)
        g = [gain(lv, under) for lv in levels]
        expr = f"{g[0]:.4f}"
        for k in range(1, n):
            if g[k] != g[k - 1]:
                ramp = 0.02 if k == sync else 0.25
                expr += f"+({g[k] - g[k - 1]:.4f})*clip((t-{starts[k] - ramp / 2:.3f})/{ramp},0,1)"
        music_in = (["-stream_loop", "-1", "-i", music] if music
                    else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"])
        audio = (f"[2:a]atrim=start={music_start:.3f},asetpts=PTS-STARTPTS,aresample=48000,"
                 f"loudnorm=I=-14:TP=-2,volume='{expr}':eval=frame[mus];"
                 f"[1:a][mus]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,"
                 f"afade=t=out:st={total - 0.5:.3f}:d=0.5[a]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / "video.mp4"), "-i", str(tmp / "voice.wav"),
                        *music_in, "-filter_complex", audio, "-map", "0:v", "-map", "[a]", "-t", f"{total:.4f}",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
                       check=True)
    print(f"fertig: {out} ({total:.1f} s, Musik ab {music_start:.1f} s, Drop {drop:.2f} s, Beat {period:.3f} s)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("plan", type=Path)
    build(p.parse_args().plan)
