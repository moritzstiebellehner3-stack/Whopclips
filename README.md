# Whopclips

Automatische Clip-Produktion für Whop-/Reach-Clipping-Kampagnen (aktuell **TJR** und **Juliano Massarelli**): pro Kampagne und Tag 3 verschiedene Clips (TikTok, Instagram Reels, YouTube Shorts).

Regeln, Analyse der Referenz-Accounts und Stil: [`docs/strategie.md`](docs/strategie.md)
Kampagnen-Daten: [`campaigns/`](campaigns/)

## Ablauf pro Tag

1. **Material holen** (nur aus den offiziellen Quellen der Kampagne)
   - TJR: Kick-Clips/VODs, z. B. die meistgesehenen Clips der Woche:
     `curl -s "https://kick.com/api/v2/channels/tjr/clips?sort=view&time=week"`, dann
     `yt-dlp -o "work/sources/tjr/%(id)s.%(ext)s" https://kick.com/tjr/clips/<clip_id>`
   - Juliano: TikTok @thewolfofinsurance:
     `yt-dlp --impersonate chrome -o "work/sources/juliano/%(id)s.%(ext)s" <tiktok-url>`
   - YouTube blockt Downloads von Cloud-Servern meist („Sign in to confirm you're not a bot“). Von einem normalen Rechner aus klappt `yt-dlp` mit YouTube in der Regel.
2. **Transkribieren:** `python -m clipper.transcribe work/sources/tjr/<id>.mp4`
3. **Die besten Momente aussuchen** (lustige Momente, starke Zitate, Reaktionen, Geld-Zahlen) und in `plans/<datum>.json` eintragen.
4. **Rendern:** `python -m clipper.batch plans/<datum>.json` → `output/<datum>/<kampagne>/<plattform>.mp4` plus `CAPTIONS.md`
5. **Posten**, Trend-Sound leise darunterlegen und den Link **innerhalb von 30 Minuten** in Content Rewards einreichen.

## Installation

```
pip install -r requirements.txt   # braucht außerdem ffmpeg mit libass und die Schrift "Inter"
```
