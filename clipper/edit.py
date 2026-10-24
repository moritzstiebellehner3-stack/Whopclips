"""Baut einen Musik-Edit: Intro mit Zitat (Untertitel), dann Schnitte im Beat.

Zwei Looks:
- "hype": Vollbild 9:16, Hook-Box, gelbe Wort-Untertitel, Zoom-Punch + Shake, weißer Flash auf dem Drop
- "cinematic" (wie die TJR-Edits großer Clip-Accounts): 4:3-Bild mit schwarzen Balken, entsättigter
  Film-Look mit Vignette, kleine weiße Untertitel mit leichtem Glow, die Wort für Wort aufbauen, ruhige Schnitte

Beat-Raster und Drop werden aus dem Song gemessen (librosa). Der Drop fällt genau auf das Intro-Ende.

    python -m clipper.edit edits/2026-10-24-tjr-mindset.json
"""
import argparse
import json
import subprocess
import tempfile
import textwrap
from pathlib import Path

import librosa
import numpy as np

from clipper.batch import ROOT, music_file
from clipper.render import H, W, ass_time, chunk_words, clean, censor, render

FPS = 30
PIC_H = W * 3 // 4  # 4:3-Bild im 9:16-Rahmen
PIC_Y = (H - PIC_H) // 2
FILM = "eq=contrast=1.08:saturation=0.72:brightness=-0.03,curves=all='0/0.05 0.5/0.47 1/0.93',vignette=PI/4.5"
HYPE = "eq=contrast=1.12:saturation=1.18:brightness=-0.02,vignette=PI/5"


def analyse(music: str, drop_hint: float | None):
    y, sr = librosa.load(music, sr=22050)
    env = librosa.onset.onset_strength(y=y, sr=sr)
    _, beats = librosa.beat.beat_track(onset_envelope=env, sr=sr)
    beat_t = librosa.frames_to_time(beats, sr=sr)
    times = librosa.frames_to_time(np.arange(len(env)), sr=sr)
    if drop_hint is None:  # größter Lautheitssprung zwischen zwei Sekunden
        rms = librosa.feature.rms(y=y)[0]
        sec = np.array([rms[(times >= s) & (times < s + 1)].mean() for s in range(int(times[-1]) - 1)])
        drop_hint = float(np.argmax(np.diff(sec)) + 1)
    win = (times > drop_hint - 0.4) & (times < drop_hint + 0.4)
    peak = float(times[win][np.argmax(env[win])])  # stärkster Anschlag rund um den Drop
    # Der Schnitt soll auf dem Einsatz sitzen, nicht auf der Spitze: erster Moment, ab dem die Lautheit über die Hälfte steigt
    rms = librosa.feature.rms(y=y, hop_length=128)[0]
    rt = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=128)
    near = (rt > peak - 0.35) & (rt <= peak)
    level = rms[(rt > peak) & (rt < peak + 0.5)].max()
    drop = float(rt[near][np.argmax(rms[near] > level / 2)])
    period = float(np.median(np.diff(beat_t)))
    return drop, period


def frame(s: dict, look: str) -> str:
    """Ausschnitt + Look für einen Schnitt (cinematic: 4:3 mit Balken, hype: Vollbild)."""
    pre = f"crop={s['precrop']}," if s.get("precrop") else ""
    # cx = wo die Person steht (0 = links, 1 = rechts); der Ausschnitt wird darum zentriert und am Rand gestoppt
    x = f"'max(0,min(iw-ow,iw*{s['cx']}-ow/2))'" if "cx" in s else f"(iw-ow)*{s.get('crop_x', 0.5)}"
    if look == "cinematic":
        return (f"{pre}crop=ih*4/3:ih:{x}:0,scale={W}:{PIC_H},setpts=PTS-STARTPTS,"
                f"scale=w='{W}*(1+{s.get('punch', 0.04)}*max(0,1-t/0.25))':h=-2:eval=frame,crop={W}:{PIC_H},"
                f"{FILM},pad={W}:{H}:0:{PIC_Y}:black")
    return (f"{pre}crop=ih*9/16:ih:{x}:0,scale={W}:{H},setpts=PTS-STARTPTS,"
            f"scale=w='{W}*(1+{s.get('punch', 0.12)}*max(0,1-t/0.18))':h=-2:eval=frame,"
            f"crop={W}:{H}:x='(in_w-out_w)/2+14*sin(t*95)*max(0,1-t/0.2)':y='(in_h-out_h)/2+10*cos(t*80)*max(0,1-t/0.2)',"
            f"{HYPE}")


def cinematic_ass(words, start, end) -> str:
    """Kleine weiße Großbuchstaben mit Glow, die pro Satzstück Wort für Wort aufbauen."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter ExtraBold,46,&H00FFFFFF,&H00FFFFFF,&H90FFFFFF,&H00000000,0,0,0,0,100,100,3,0,1,2,0,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dur = end - start
    ws = [w for w in words if w["end"] > start and w["start"] < end and w["word"]]
    caps = []
    for chunk in chunk_words(ws, max_words=5, max_gap=0.5):
        for i, w in enumerate(chunk):
            txt = " ".join(censor(clean(x["word"].upper())) for x in chunk[: i + 1])
            caps.append([max(w["start"] - start, 0), chunk[-1]["end"] + 0.3 - start, txt])
    ev = []
    for k, (t0, t1, txt) in enumerate(caps):
        if k + 1 < len(caps):
            t1 = min(t1, caps[k + 1][0])
        if t1 > t0:
            txt = "\\N".join(textwrap.wrap(txt, 30))
            ev.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(min(t1, dur))},Cap,,0,0,0,,"
                      f"{{\\pos({W // 2},{H // 2})\\blur2}}{txt}")
    return head + "\n".join(ev) + "\n"


def encode(args: list, out: Path, frames: int | None = None) -> None:
    cmd = ["ffmpeg", "-v", "error", "-y", *args]
    if frames:
        cmd += ["-frames:v", str(frames)]
    cmd += ["-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)]
    subprocess.run(cmd, check=True)


def build(plan_path: Path) -> None:
    plan = json.loads(plan_path.read_text())
    look = plan.get("look", "hype")
    music = music_file(plan["music"])
    drop, period = analyse(music, plan.get("drop_hint"))
    out = ROOT / plan["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Look {look}, Drop bei {drop:.2f} s, Beat {period:.3f} s ({60 / period:.1f} BPM)")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        intro = plan["intro"]
        intro_len = intro["end"] - intro["start"]
        frame0 = round(intro_len * FPS)
        src = str(ROOT / intro["src"])
        words = json.loads((ROOT / intro["src"]).with_suffix(".words.json").read_text())

        # Intro: Bild (mit Untertiteln) und Stimme getrennt
        if look == "cinematic":
            (tmp / "cap.ass").write_text(cinematic_ass(words, intro["start"], intro["end"]))
            encode(["-ss", str(intro["start"]), "-i", src,
                    "-vf", f"{frame(intro, look)},ass={tmp / 'cap.ass'},fps={FPS}"], tmp / "intro.mp4", frame0)
        else:
            render(argparse.Namespace(
                src=src, words=str((ROOT / intro["src"]).with_suffix(".words.json")), start=intro["start"],
                end=intro["end"], hook=intro.get("hook", ""), out=str(tmp / "hype.mp4"), layout=intro.get("layout", "crop"),
                zoom=1.25, crop_x=intro.get("crop_x", 0.5), precrop=intro.get("precrop"), music=None, music_db=-14))
            encode(["-i", str(tmp / "hype.mp4"), "-vf", f"fps={FPS}"], tmp / "intro.mp4", frame0)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(intro["start"]), "-t", str(intro_len), "-i", src,
                        "-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", str(tmp / "voice.wav")], check=True)

        # Schnitte auf dem Beat-Raster: Zeitpunkte absolut berechnen, damit sich Rundungen nicht aufsummieren
        segs, beat_pos = [tmp / "intro.mp4"], 0
        for i, s in enumerate(plan["shots"]):
            a = frame0 + round(beat_pos * period * FPS)
            beat_pos += s["beats"]
            b = frame0 + round(beat_pos * period * FPS)
            vf = frame(s, look)
            if i == 0 and plan.get("flash", look == "hype"):
                vf += ",fade=t=in:st=0:d=0.25:color=white"
            encode(["-ss", str(s["t"]), "-i", str(ROOT / s["src"]), "-vf", f"{vf},fps={FPS}"], tmp / f"shot{i:02d}.mp4", b - a)
            segs.append(tmp / f"shot{i:02d}.mp4")
        total = (frame0 + round(beat_pos * period * FPS)) / FPS

        (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in segs))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"),
                        "-c", "copy", str(tmp / "video.mp4")], check=True)

        # Ton: Stimme im Intro über der Musik, Drop exakt am Intro-Ende
        music_start = drop - intro_len
        fade = plan.get("fade_out", 0.8)
        under = plan.get("music_under_voice_db", -12)
        audio = (
            f"[1:a]apad,atrim=0:{total}[voice];"
            f"[2:a]atrim=start={music_start}:duration={total},asetpts=PTS-STARTPTS,aresample=48000,"
            f"volume='if(lt(t,{intro_len}),{10 ** (under / 20):.3f},1)':eval=frame[mus];"
            f"[voice][mus]amix=inputs=2:duration=longest:normalize=0,"
            f"loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={total - fade}:d={fade}[a]"
        )
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", str(tmp / "video.mp4"), "-i", str(tmp / "voice.wav"), "-i", music,
            "-filter_complex", f"{audio};[0:v]fade=t=out:st={total - fade}:d={fade}[v]",
            "-map", "[v]", "-map", "[a]", "-t", str(total),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(out),
        ], check=True)
    print(f"fertig: {out} ({total:.1f} s)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("plan", type=Path)
    build(p.parse_args().plan)
