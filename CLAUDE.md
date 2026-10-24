# Whopclips

Whopclips ist eine Plattform für Clipping-Kampagnen: Creator stellen Kampagnen ein, Clipper reichen Kurzvideos (TikTok, Reels, Shorts) ein und werden pro View bezahlt. Der Tech-Stack steht noch nicht fest.

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
