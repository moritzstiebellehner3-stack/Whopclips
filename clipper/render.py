"""Schneidet einen Ausschnitt aus einem Quellvideo zu einem fertigen 9:16-Clip (1080x1920).

- Hook-Titel oben (schwarze Schrift auf weißem Kasten, wie bei den erfolgreichen Clip-Accounts)
- Wort-für-Wort-Untertitel, das gesprochene Wort ist gelb hervorgehoben
- Layout "fit": Video mittig, unscharfer Hintergrund. Layout "crop": Vollbild-Ausschnitt (gut für Gesichter)
- Lautstärke auf -14 LUFS normalisiert, optional Hintergrundmusik 14 dB unter der Stimme (nur lizenzfreie Tracks!)

    python -m clipper.render --src work/sources/ID.mp4 --words work/sources/ID.words.json \
        --start 61.2 --end 92.8 --hook "He made $800K in one day" --out output/clip.mp4
"""
import argparse
import json
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

W, H = 1080, 1920
YELLOW = "&H0000E1FF&"  # ASS-Farben sind BGR
WHITE = "&H00FFFFFF&"


def ass_time(t: float) -> str:
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def clean(s: str) -> str:
    return s.replace("{", "(").replace("}", ")").replace("\\", "")


SWEARS = re.compile(r"\b(FUCK|FUCKING|FUCKED|SHIT|BITCH|NIGGA|NIGGER|DICK|PUSSY|CUNT|ASSHOLE)", re.I)


def censor(s: str) -> str:
    """Schimpfwörter im Bild zensieren (F*CK), sonst drosseln TikTok/Instagram die Reichweite."""
    return SWEARS.sub(lambda m: m.group(1)[0] + "*" + m.group(1)[2:], s)


def chunk_words(words, max_words=3, max_gap=0.45):
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["start"] - cur[-1]["end"] > max_gap or cur[-1]["word"][-1:] in ".?!,"):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def build_ass(words, start, end, hook, hook_y, cap_y) -> str:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Inter Black,70,&H00000000,&H00000000,{WHITE},&H00000000,0,0,0,0,100,100,0,0,3,18,0,5,60,60,0,1
Style: Cap,Inter Black,80,{WHITE},{WHITE},&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dur = end - start
    ev = []
    if hook:
        hook_txt = "\\N".join(textwrap.wrap(clean(hook), 24))
        ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(dur)},Hook,,0,0,0,,{{\\pos({W // 2},{hook_y})}}{hook_txt}")

    clip_words = []
    for w in words:
        if not (w["end"] > start and w["start"] < end and w["word"]):
            continue
        if clip_words and w["word"][0] in "-'":  # Whisper trennt "push-ups" in "push" + "-ups"
            clip_words[-1] = {**clip_words[-1], "word": clip_words[-1]["word"] + w["word"], "end": w["end"]}
        else:
            clip_words.append(w)
    caps = []  # (t0, t1, text) – jedes Wort einzeln, damit nie zwei Untertitel gleichzeitig stehen
    for chunk in chunk_words(clip_words):
        for i, w in enumerate(chunk):
            t0 = (chunk[0]["start"] if i == 0 else w["start"]) - start
            parts = []
            for j, x in enumerate(chunk):
                txt = censor(clean(x["word"].upper()))
                parts.append(f"{{\\c{YELLOW}}}{txt}{{\\c{WHITE}}}" if j == i else txt)
            pop = "{\\fscx112\\fscy112\\t(0,90,\\fscx100\\fscy100)}" if i == 0 else ""
            caps.append([max(t0, 0), w["end"] + 0.25 - start, pop + " ".join(parts)])
    for k, (t0, t1, text) in enumerate(caps):
        if k + 1 < len(caps):
            t1 = min(t1, caps[k + 1][0])
        if t1 > t0:
            ev.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(min(t1, dur))},Cap,,0,0,0,,{{\\pos({W // 2},{cap_y})}}{text}")
    return head + "\n".join(ev) + "\n"


def render(a) -> None:
    words = json.loads(Path(a.words).read_text()) if a.words else []
    dur = a.end - a.start

    pre = f"crop={a.precrop}," if a.precrop else ""
    if a.layout == "fit":
        fg_w = int(W * a.zoom) // 2 * 2
        fg_h = int(fg_w * 9 / 16) // 2 * 2
        hook_y, cap_y = (H - fg_h) // 2 - 150, (H + fg_h) // 2 + 170
        video = (
            f"[0:v]{pre}split[a][b];"
            f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=40,eq=brightness=-0.18[bg];"
            f"[b]scale={fg_w}:-2,crop=min(iw\\,{W}):ih[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
    else:
        hook_y, cap_y = 300, 1380
        video = f"[0:v]{pre}crop=ih*9/16:ih:(iw-ow)*{a.crop_x}:0,scale={W}:{H}"

    with tempfile.TemporaryDirectory() as tmp:
        ass = Path(tmp) / "subs.ass"
        ass.write_text(build_ass(words, a.start, a.end, a.hook, hook_y, cap_y))
        video += f",ass={ass},fps=30,format=yuv420p[v]"

        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(a.start), "-t", str(dur), "-i", a.src]
        audio = "[0:a]loudnorm=I=-14:TP=-1.5:LRA=11"
        if a.music:
            cmd += ["-stream_loop", "-1", "-i", a.music]
            # Musik auf feste Lautheit unter der Stimme bringen (Stimme = -14 LUFS), damit jeder Track gleich leise liegt
            audio += (
                f"[voice];[1:a]loudnorm=I={-14 + a.music_db}:TP=-3,afade=t=in:d=0.4,"
                f"afade=t=out:st={max(dur - 1.5, 0)}:d=1.5[mus];"
                f"[voice][mus]amix=inputs=2:duration=first:normalize=0"
            )
        audio += "[a]"

        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        cmd += [
            "-filter_complex", f"{video};{audio}", "-map", "[v]", "-map", "[a]", "-t", str(dur),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", a.out,
        ]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True)
    p.add_argument("--words")
    p.add_argument("--start", type=float, required=True)
    p.add_argument("--end", type=float, required=True)
    p.add_argument("--hook", default="")
    p.add_argument("--out", required=True)
    p.add_argument("--layout", choices=["fit", "crop"], default="fit")
    p.add_argument("--zoom", type=float, default=1.25, help="nur fit: wie stark das Video vergrößert wird")
    p.add_argument("--crop-x", type=float, default=0.5, help="nur crop: 0 = links, 0.5 = Mitte, 1 = rechts")
    p.add_argument("--precrop", help="ffmpeg-crop vorab, z. B. 'iw:ih*0.85:0:ih*0.15' schneidet oben Overlays/Logos weg")
    p.add_argument("--music", help="lizenzfreie Musikdatei")
    p.add_argument("--music-db", type=float, default=-14, help="Musik-Lautstärke relativ zur Stimme in dB")
    render(p.parse_args())
