# Whopclips

Automatische Clip-Produktion für Whop-/Reach-Clipping-Kampagnen (aktuell **TJR** und **Juliano Massarelli**): pro Kampagne und Tag 3 verschiedene Clips (TikTok, Instagram Reels, YouTube Shorts).

Regeln, Analyse der Referenz-Accounts und Stil: [`docs/strategie.md`](docs/strategie.md)
Kampagnen-Daten: [`campaigns/`](campaigns/)

## Ablauf pro Tag

1. **Material holen** (nur aus den offiziellen Quellen der Kampagne)
   - TJR: Kick-Clips/VODs, z. B. die meistgesehenen Clips der Woche:
     `curl -s "https://kick.com/api/v2/channels/tjr/clips?sort=view&time=week"`, dann
     `yt-dlp -o "work/sources/tjr/%(id)s.%(ext)s" https://kick.com/tjr/clips/<clip_id>`
   - Juliano: YouTube @Julianomass von einem normalen Rechner aus (`yt-dlp`), oder Moritz stellt das Material bereit. TikTok nicht per Impersonation laden.
   - YouTube blockt Downloads von Cloud-Servern meist („Sign in to confirm you're not a bot“). Von einem normalen Rechner aus klappt `yt-dlp` mit YouTube in der Regel.
2. **Transkribieren:** `python -m clipper.transcribe work/sources/tjr/<id>.mp4`
3. **Die besten Momente aussuchen** (lustige Momente, starke Zitate, Reaktionen, Geld-Zahlen) und in `plans/<datum>.json` eintragen.
4. **Rendern:** `python -m clipper.batch plans/<datum>.json` → `output/<datum>/<kampagne>/<plattform>.mp4` plus `CAPTIONS.md`
5. **Posten**, Trend-Sound leise darunterlegen und den Link **innerhalb von 30 Minuten** in Content Rewards einreichen.

## Installation

```
pip install -r requirements.txt   # braucht außerdem ffmpeg mit libass und die Schrift "Inter"
```

## Musik-Edits (Intro-Zitat → Drop → Schnitte im Beat)

```
python -m clipper.edit edits/2026-10-24-tjr-cinematic.json
```
- `look: "cinematic"` ist der Stil der großen TJR-Edit-Accounts: 4:3 mit schwarzen Balken, Film-Look, kleine weiße Untertitel, die Wort für Wort aufbauen.
- `look: "hype"` ist Vollbild mit Hook-Box, gelben Wort-Untertiteln, Zoom-Punch, Shake und Flash auf dem Drop.
- Drop und Beat werden aus dem Song gemessen. Der Drop fällt genau aufs Intro-Ende, jeder Schnitt sitzt auf einem Beat (`beats` pro Shot).
- `cx` ist die Position der Person (0 = links, 1 = rechts). Mit `precrop` schneidest du vorher Overlays, Chat und Logos weg.

## Real Talk, Cold Call, Hype (15–30 s) – Standard seit 25.10.

```
python -m clipper.kickvod list                                    # TJRs Kick-VODs
python -m clipper.kickvod get 131052820 --tail 25                 # Stream-Ende in 160p → transkribieren, Momente suchen
python -m clipper.kickvod get 131052820 --from 3968 --to 4002 --quality 1080p60
python -m clipper.realtalk edits/2026-10-26-tjr-idareyou.json
```
- **Plan:** `parts` ist eine Liste aus Sprech-Teilen (`src`, `start`, `end`, `box`, `music: full|under|off|dB`) und Edit-Teilen (`edit`: Luxus-Schnitte, `beats` pro Schnitt).
- **Drop:** fällt auf den Teil mit `"sync": true`, sonst auf den Anfang des Edits.
- **Stil:** `style: "tjr"` (Facecam, weiße 2-Wort-Untertitel) oder `"juliano"` (Band mit gewölbten Kanten, große Serifen-Wörter, `big` für Schlüsselwörter). `fix` korrigiert Whisper-Fehler in den Untertiteln.

## Clips automatisch auf Moritz' PC

1. In der Cloud: `python -m clipper.publish 2026-10-25`. Das baut `output/Whop-Campaign/<Datum>/…` und pusht die letzten 7 Tage auf den Branch `videos`.
2. Auf dem PC (einmalig, in PowerShell):
   ```powershell
   $d="$env:LOCALAPPDATA\whop-sync"; mkdir $d -Force | Out-Null; irm https://raw.githubusercontent.com/moritzstiebellehner3-stack/Whopclips/refs/heads/claude/serene-gauss-am057q/tools/whop-sync.ps1 -OutFile "$d\whop-sync.ps1"; powershell -ExecutionPolicy Bypass -File "$d\whop-sync.ps1" -Install
   ```
   Das legt den Aufgabenplaner-Task „Whop-Clips holen“ an (bei Anmeldung + alle 30 min). Er kopiert neue Tage nach `Videos\Whop-Campaign` und zeigt eine Benachrichtigung. Er löscht nichts, und selbst gelöschte Tage kommen nicht zurück. Das Protokoll liegt in `%LOCALAPPDATA%\whop-sync\sync.log`.
3. **Material vom PC in die Cloud:** Alles, was Moritz in `Videos\Whop-Campaign\Material` legt, lädt derselbe Task in das private Repo `moritzstiebellehner3-stack/Whop-Material` hoch.
   - Dateien bis 95 MB, größere stehen im Protokoll.
   - Hochgeladen wird in Paketen bis 400 MB (GitHub nimmt höchstens 2 GB pro Push). Fertige Pakete bleiben oben, ein abgebrochener Lauf macht beim nächsten Mal weiter.
   - Git liest den Ordner nur (eigener Git-Ordner `%LOCALAPPDATA%\whop-sync\material.git`, keine Kopie der Dateien).
   - Beim Ausführen der Zeile zeigt das Fenster den Fortschritt: Anmeldung, Dateien/MB, Paket x/y mit Prozent.
   - Was im Ordner gelöscht wird, verschwindet auch im Repo.
   - Einmalig: Repo auf github.com/new anlegen (Name `Whop-Material`, **Private**, ohne README) und die Zeile oben noch einmal ausführen. Beim ersten Hochladen fragt Git evtl. nach der GitHub-Anmeldung.
   - In der Cloud: Repo zur Session hinzufügen, dann `python -m clipper.material --transcribe`. Das holt alles nach `work/material/`, transkribiert neue Videos und listet sie auf.
4. Das Skript aktualisiert sich selbst: `publish` legt die aktuelle Version mit auf den Branch `videos`, der Task übernimmt sie beim nächsten Lauf.
