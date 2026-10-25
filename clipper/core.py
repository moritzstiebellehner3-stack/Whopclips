"""TJR-Clips im Stil von @tjr.clips.core (Top-Clip 66K Aufrufe, vermessen am 25.10.2026).

- 9:16 schwarz, TJR in einem Quadrat in der Mitte, kleiner Titel darüber („TJR Mentality.“)
- stark gesättigte Farben
- Untertitel: immer nur EIN Wort, groß, Großbuchstaben, metallischer Eis-Verlauf (weiß → hellblau), über seiner Stirn
- 2–3 Zitate zu einem Thema, getrennt durch schwarze Karten („MENTALITY.“), am Ende „FACTS.“
- Musik läuft leise unter der Stimme durch

    python -m clipper.core edits/2026-10-25-tjr-school.json
"""
import argparse
import json
import subprocess
import tempfile
import textwrap
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from clipper.batch import ROOT, music_file
from clipper.render import H, W, censor, chunk_words

FPS = 30
SQ_Y = (H - W) // 2  # Quadrat 1080×1080 genau in der Mitte
TITLE_Y = SQ_Y - 70
WORD_Y = SQ_Y + 265  # Wortmitte, etwa Stirnhöhe
CARD_LEN = 0.67
# „Real sales call“-Layout von Juliano (38,8M / 22,3M / 8,8M Aufrufe): Querformat-Bild ~1,38:1 in der Mitte
BAND_H = 782
BAND_Y = 535
GRADE = "eq=saturation=1.55:contrast=1.08:gamma=0.97,unsharp=5:5:0.6"
FONTS = {
    "Montserrat-Black": "https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvC70w-.ttf",
    "Inter-SemiBold": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuGKYMZg.ttf",
}
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Lädt die Schrift bei Bedarf nach work/fonts/ (Google Fonts, OFL)."""
    path = ROOT / "work" / "fonts" / f"{name}.ttf"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(FONTS[name], path)
    return ImageFont.truetype(str(path), size)


def title_layer(title: str, y: int = TITLE_Y, size: int = 58) -> Image.Image:
    """Titel über dem Bild; Emojis (z. B. „Real sales call 😂😭“) kommen aus Noto Color Emoji."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not title:
        return img
    f = font("Inter-SemiBold", size)
    parts = []  # (Bild, Breite)
    text = "".join(ch for ch in title if ord(ch) < 0x2000).rstrip()
    emojis = [ch for ch in title if ord(ch) >= 0x2000 and ch not in "\u200d\ufe0f"]
    l, t, r, b = f.getbbox(text)
    txt = Image.new("RGBA", (r - l + 4, size * 2), (0, 0, 0, 0))
    ImageDraw.Draw(txt).text((-l, size), text, font=f, fill="white", anchor="lm")
    parts.append(txt)
    if emojis:
        ef = ImageFont.truetype(EMOJI_FONT, 109)
        for e in emojis:
            em = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
            ImageDraw.Draw(em).text((0, 0), e, font=ef, embedded_color=True)
            em = em.crop(em.getbbox() or (0, 0, 1, 1))
            k = size * 1.05 / em.height
            parts.append(em.resize((max(1, int(em.width * k)), max(1, int(em.height * k)))))
    gap = int(size * 0.18)
    total = sum(p.width for p in parts) + gap * (len(parts) - 1)
    x = W // 2 - total // 2
    for p in parts:
        img.alpha_composite(p, (x, y - p.height // 2))
        x += p.width + gap
    return img


def sentence(text: str, y_mid: int) -> Image.Image:
    """Kleiner weißer Satz-Untertitel mit weichem Schatten (TikTok-Optik)."""
    f = font("Inter-SemiBold", 42)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lines = textwrap.wrap(text, 34)
    for k, line in enumerate(lines):
        yy = y_mid + (k - (len(lines) - 1) / 2) * 52
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((W // 2 + 2, yy + 3), line, font=f, fill=(0, 0, 0, 200), anchor="mm")
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
        ImageDraw.Draw(canvas).text((W // 2, yy), line, font=f, fill="white", anchor="mm")
    return canvas


def hook_layer(text: str, y_mid: int) -> Image.Image:
    """Weiße Box mit schwarzem Text, wie bei „TJR got rugged on beat drop“."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if text:
        f = font("Inter-SemiBold", 50)
        l, t, r, b = f.getbbox(text)
        pad_x, pad_y = 26, 16
        box = (W // 2 - (r - l) // 2 - pad_x, y_mid - (b - t) // 2 - pad_y,
               W // 2 + (r - l) // 2 + pad_x, y_mid + (b - t) // 2 + pad_y)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle(box, radius=10, fill="white")
        d.text((W // 2, y_mid), text, font=f, fill="black", anchor="mm")
    return img


def ice_word(word: str, y_mid: int = WORD_Y) -> Image.Image:
    """Ein Wort mit metallischem Eis-Verlauf und weichem Schatten, auf voller Leinwand."""
    size = 170
    while True:
        f = font("Montserrat-Black", size)
        l, t, r, b = f.getbbox(word)
        if r - l <= W * 0.86 or size <= 70:
            break
        size -= 6
    w, h = r - l, b - t
    mask = Image.new("L", (w + 40, h + 40), 0)
    ImageDraw.Draw(mask).text((20 - l, 20 - t), word, font=f, fill=255)

    # Verlauf: oben weiß, Mitte eisblau, unten stahlblau, dazu ein heller Glanzstreifen
    grad = Image.new("RGB", mask.size)
    gd = ImageDraw.Draw(grad)
    stops = [(0.0, (255, 255, 255)), (0.45, (214, 233, 243)), (0.55, (150, 190, 214)), (1.0, (96, 140, 170))]
    for y in range(mask.size[1]):
        p = min(max((y - 20) / max(h, 1), 0), 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= p <= p1:
                k = (p - p0) / (p1 - p0)
                gd.line([(0, y), (mask.size[0], y)], fill=tuple(int(a + (b2 - a) * k) for a, b2 in zip(c0, c1)))
                break
    word_img = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    word_img.paste(grad, (0, 0), mask)

    shadow = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    shadow.putalpha(mask.point(lambda v: v * 0.6))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))

    # dunkle Kontur, damit das Wort auch auf hellen Charts lesbar bleibt
    edge = Image.new("L", mask.size, 0)
    ImageDraw.Draw(edge).text((20 - l, 20 - t), word, font=f, fill=255, stroke_width=5, stroke_fill=255)
    outline = Image.new("RGBA", mask.size, (12, 26, 42, 0))
    outline.putalpha(edge.point(lambda v: v * 0.8))

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x, y = W // 2 - mask.size[0] // 2, y_mid - mask.size[1] // 2
    canvas.alpha_composite(shadow, (x + 3, y + 8))
    canvas.alpha_composite(outline, (x, y))
    canvas.alpha_composite(word_img, (x, y))
    return canvas


def card(text: str) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    ImageDraw.Draw(img).text((W // 2, H // 2), text, font=font("Montserrat-Black", 76), fill="white", anchor="mm")
    return img


def words_for(src: Path, start: float, end: float):
    words = json.loads(src.with_suffix(".words.json").read_text())
    out = []
    for w in words:
        if not (w["end"] > start and w["start"] < end and w["word"]):
            continue
        if out and w["word"][0] in "-'":  # Whisper trennt „push-ups“ in „push“ + „-ups“
            out[-1] = {**out[-1], "word": out[-1]["word"] + w["word"], "end": w["end"]}
        else:
            out.append(dict(w))
    return out


def overlay_track(tmp: Path, name: str, title: Image.Image, words, start: float, dur: float,
                  word_y: int = WORD_Y, sentences: bool = False) -> Path:
    """ffconcat-Liste aus Vollbild-PNGs: Titel + jeweils ein Wort (oder ein Satzstück), mit exakten Anzeigedauern."""
    frames, t = [], 0.0
    blank = tmp / f"{name}_blank.png"
    title.save(blank)
    if sentences:
        words = [{"start": c[0]["start"], "end": c[-1]["end"], "word": " ".join(x["word"] for x in c)}
                 for c in chunk_words(words, max_words=6, max_gap=0.6)]
    for i, w in enumerate(words):
        w0 = max(w["start"] - start, 0)
        w1 = min(words[i + 1]["start"] - start if i + 1 < len(words) else w["end"] - start + 0.25, dur)
        if w0 > t:
            frames.append((blank, w0 - t))
        txt = censor(w["word"]) if sentences else censor(w["word"].strip(".,!?\"“”").upper())
        if not txt or w1 <= w0:
            continue
        png = tmp / f"{name}_{i:03d}.png"
        Image.alpha_composite(title, sentence(txt, word_y) if sentences else ice_word(txt, word_y)).save(png)
        frames.append((png, w1 - w0))
        t = w1
    if t < dur:
        frames.append((blank, dur - t))
    lst = tmp / f"{name}.ffconcat"
    lst.write_text("ffconcat version 1.0\n" + "".join(f"file '{p}'\nduration {d:.4f}\n" for p, d in frames)
                   + f"file '{frames[-1][0]}'\n")
    return lst


def quote_segment(tmp: Path, i: int, s: dict, title: Image.Image) -> tuple[Path, Path, float]:
    src = ROOT / s["src"]
    dur = s["end"] - s["start"]
    frames = round(dur * FPS)
    if s.get("layout") == "split":
        # Stream-Clip: Facecam oben (volle Breite), Chart darunter, Hook-Box am Facecam-Rand, Wörter dazwischen
        cx_, cy_, cw, ch = s["cam"]
        gx, gy, gw, gh = s["chart"]
        cam_h = round(W * ch / cw / 2) * 2
        vf = (f"[0:v]split[c][g];"
              f"[c]crop={cw}:{ch}:{cx_}:{cy_},scale={W}:{cam_h},{GRADE}[cam];"
              f"[g]crop={gw}:{gh}:{gx}:{gy},scale={W}:{H - cam_h}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H - cam_h},eq=saturation=1.2:contrast=1.05[chart];"
              f"[cam][chart]vstack,fps={FPS}[base];"
              f"[1:v]format=rgba[ov];[base][ov]overlay=0:0:format=auto,format=yuv420p[v]")
        layer = Image.alpha_composite(title_layer(""), hook_layer(s.get("hook", ""), cam_h - 50))
        word_y = cam_h + 170
    elif s.get("layout") == "band":
        # Juliano „Real sales call“: Querformat-Ausschnitt in der Mitte, Titel darüber, Satz-Untertitel unten im Bild
        bh = f"iw*{BAND_H}/{W}"
        # box = festes Rechteck [x, y, b, h] in der Quelle, z. B. um eingebrannte Fremd-Untertitel auszusparen
        crop = ("crop={2}:{3}:{0}:{1}".format(*s["box"]) if "box" in s
                else f"crop=iw:{bh}:0:'max(0,min(ih-oh,ih*{s.get('cy', 0.4)}-oh/2))'")
        vf = (f"[0:v]{crop},"
              f"scale={W}:{BAND_H},pad={W}:{H}:0:{BAND_Y}:black,fps={FPS}[base];"
              f"[1:v]format=rgba[ov];[base][ov]overlay=0:0:format=auto,format=yuv420p[v]")
        layer, word_y = title, BAND_Y + BAND_H - 95
    else:
        pre = f"crop={s['precrop']}," if s.get("precrop") else ""
        side = f"min(iw\\,ih)/{s.get('zoom', 1.0)}"
        cx, cy = s.get("cx", 0.5), s.get("cy", 0.5)
        vf = (f"[0:v]{pre}crop={side}:{side}:'max(0,min(iw-ow,iw*{cx}-ow/2))':'max(0,min(ih-oh,ih*{cy}-oh/2))',"
              f"scale={W}:{W},{GRADE},pad={W}:{H}:0:{SQ_Y}:black,fps={FPS}[base];"
              f"[1:v]format=rgba[ov];[base][ov]overlay=0:0:format=auto,format=yuv420p[v]")
        layer, word_y = title, WORD_Y
    seg = tmp / f"q{i}.mp4"
    lst = overlay_track(tmp, f"q{i}", layer, words_for(src, s["start"], s["end"]), s["start"], dur, word_y,
                        sentences=s.get("layout") == "band")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["start"]), "-i", str(src),
                    "-f", "concat", "-safe", "0", "-i", str(lst), "-filter_complex", vf, "-map", "[v]",
                    "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                    "-r", str(FPS), str(seg)], check=True)
    wav = tmp / f"q{i}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["start"]), "-t", f"{frames / FPS:.4f}", "-i", str(src),
                    "-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,apad", "-t", f"{frames / FPS:.4f}",
                    "-ar", "48000", "-ac", "2", str(wav)], check=True)
    return seg, wav, frames / FPS


def card_segment(tmp: Path, i: int, text: str, title: Image.Image, length: float) -> tuple[Path, Path, float]:
    png = tmp / f"c{i}.png"
    Image.alpha_composite(card(text), title).save(png)
    frames = round(length * FPS)
    seg, wav = tmp / f"c{i}.mp4", tmp / f"c{i}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png), "-frames:v", str(frames),
                    "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                    "-r", str(FPS), str(seg)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-t", f"{frames / FPS:.4f}", str(wav)], check=True)
    return seg, wav, frames / FPS


def build(plan_path: Path) -> None:
    plan = json.loads(plan_path.read_text())
    out = ROOT / plan["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    if plan.get("layout") == "band":
        title = title_layer(plan.get("title", ""), y=BAND_Y - 48, size=54)
    else:
        title = title_layer(plan.get("title", "TJR Mentality."))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts = []
        for i, s in enumerate(plan["segments"]):
            if "card" in s:
                parts.append(card_segment(tmp, i, s["card"], title, s.get("length", CARD_LEN)))
            else:
                parts.append(quote_segment(tmp, i, s, title))
        total = sum(p[2] for p in parts)
        (tmp / "v.txt").write_text("".join(f"file '{p[0]}'\n" for p in parts))
        (tmp / "a.txt").write_text("".join(f"file '{p[1]}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "v.txt"),
                        "-c", "copy", str(tmp / "video.mp4")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "a.txt"),
                        str(tmp / "voice.wav")], check=True)

        music = music_file(plan.get("music"))  # ohne Musik: Stille, Originalton bleibt allein (wie bei Juliano)
        music_in = ["-stream_loop", "-1", "-i", music] if music else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        fade = 0.6
        audio = (f"[2:a]atrim=start={plan.get('music_start', 0)},asetpts=PTS-STARTPTS,aresample=48000,"
                 f"loudnorm=I={-14 + plan.get('music_db', -12)}:TP=-3,afade=t=in:d=0.3[mus];"
                 f"[1:a][mus]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,"
                 f"afade=t=out:st={total - fade}:d={fade}[a]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / "video.mp4"), "-i", str(tmp / "voice.wav"),
                        *music_in, "-filter_complex", audio,
                        "-map", "0:v", "-map", "[a]", "-t", f"{total:.4f}", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    print(f"fertig: {out} ({total:.1f} s)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("plan", type=Path)
    build(p.parse_args().plan)
