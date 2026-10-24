# Whopclips

Whopclips produziert Clips für Whop-/Reach-Clipping-Kampagnen, aktuell **TJR** und **Juliano Massarelli**. Pro Kampagne und Tag entstehen 3 verschiedene Clips: TikTok, Instagram Reels, YouTube Shorts.

- Regeln, Analyse und Stil stehen in `docs/strategie.md`, die Kampagnen-Daten in `campaigns/`. **Halte dich strikt an die Regeln:**
  - keine Logos
  - keine KI-Inhalte
  - die Person nie negativ darstellen
  - Pflicht-Hashtag
  - nur offizielle Quellen
- Ablauf: Material holen → `python -m clipper.transcribe` → Momente aussuchen → `plans/<datum>.json` → `python -m clipper.batch plans/<datum>.json`. Details stehen in `README.md`.
- Cloud-Hinweise:
  - YouTube blockt Downloads aus der Cloud.
  - TJR-Material kommt deshalb von Kick (`kick.com/api/v2/channels/tjr/clips?sort=view&time=week`).
  - Juliano-Material kommt von TikTok, mit `yt-dlp --impersonate chrome`.
- Prüfe jeden fertigen Clip anhand von Standbildern, ob Logos oder Overlays zu sehen sind.
- In Cloud-Sessions ist kein Zugriff auf Obsidian möglich. Schreib dann den Tageslog nach `obsidian-log/YYYY-MM-DD.md`. Eine lokale Session kopiert ihn später in den Vault.

## Obsidian-Vault (Gedächtnis des Nutzers)

Der Nutzer hält seine Arbeit mit Claude jeden Tag in Obsidian fest. Der Vault ist ein Ordner auf seinem eigenen Computer. Das hier gilt deshalb nur für Sessions, die lokal laufen (Claude Desktop oder `claude remote-control`). Eine Cloud-Session kommt an den Vault nicht heran und soll das dem Nutzer kurz sagen.

**Vault-Pfad:** _noch nicht eingetragen_

- Ist oben kein Pfad eingetragen, frag den Nutzer danach, trag ihn hier ein und committe die Änderung.
- Liegt der Vault außerhalb dieses Repos, braucht Claude Zugriff auf den Ordner, z. B. über `claude --add-dir "<Vault-Pfad>"` oder `additionalDirectories` in `.claude/settings.local.json`.

### Zu Beginn einer Session

Lies die Notizen im Vault (vor allem die neuesten), damit du weißt, wer der Nutzer ist, woran er arbeitet und was zuletzt gemacht wurde.

### Am Ende jeder Arbeit an Whopclips

Schreib eine kurze Notiz in den Vault:

- Datei: `<Vault-Pfad>/Whopclips/YYYY-MM-DD.md`. Gibt es die Datei für heute schon, häng einen neuen Abschnitt an.
- Inhalt auf Deutsch:
  - was gemacht wurde
  - welche Entscheidungen gefallen sind und warum
  - welche Dateien oder Commits geändert wurden
  - was als Nächstes offen ist
- Format: normales Obsidian-Markdown mit dem Tag `#whopclips` und einem Link zur Übersicht `[[Whopclips]]`.
