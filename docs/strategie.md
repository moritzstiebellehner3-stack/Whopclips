# Whopclips – Strategie und Analyse (Stand 24.10.2026)

## Ziel
Pro Tag **6 Clips**: je Kampagne (TJR, Juliano Massarelli) 3 *verschiedene* Clips – einer für TikTok, einer für Instagram Reels, einer für YouTube Shorts.

## Kampagnen auf einen Blick

| | TJR | Juliano Massarelli |
|---|---|---|
| Bezahlung | $0,75 / 1K Views ($3,75 min, $750 max pro Clip) | $1 / 1K Views ($10 min, $500 max pro Clip) |
| Mindest-Views | 5.000 | 10.000 |
| Pflicht-Hashtag | `#TJR` | `#JulianoMassarelli` |
| Account | Nischen-passender Account reicht, eigener TJR-Account empfohlen | **Muss ein eigener Juliano-Account sein**, der nur Juliano postet |
| Quellen | YouTube @TJRTrades, @TRichesTrades, Kick kick.com/tjr, Instagram @tjr | YouTube @Julianomass, Instagram @julianomass, TikTok @thewolfofinsurance |

Beide Kampagnen verbieten:
- Logos jeder Art (Sponsor-Overlays aus TJRs Streams wie „USE CODE TJR“, Alpha Futures, Lucid, Tradeify oder Polymarket müssen weggeschnitten werden)
- KI-generierte Inhalte (z. B. die animierten KI-Videos, auf die TJR im Stream reagiert)
- Reposts, Collab-Posts und Botting
- die Person negativ darzustellen

Den Link musst du **innerhalb von 30 Minuten nach dem Posten** in Content Rewards (Whop) einreichen. Es gilt „One strike and you're out“: Ein Verstoß sperrt dich für alle Reach-Kampagnen.

## Was die erfolgreichen Clip-Accounts machen

**@.tjr.him** ist der stärkste Account. Er hat im Median 54K Views, der Top-Clip liegt bei 653K.
- Er nutzt rohe Talking-Head-Ausschnitte von TJR im Hochformat, ohne viel Schnitt.
- Die Caption besteht oft nur aus `#TJR`.
- Unter dem Original-Ton liegt ein Trend-Sound aus der TikTok-Bibliothek: „ski slopes“, „LEGACY (main)“, „we found love slowed“, „Shayd3s.beats“.
- Die Länge liegt bei 20–60 Sekunden.

**@tjr.clips02** erreicht im Median nur 1,3K Views, einzelne Hits aber 80–115K.
- Das Video läuft im Querformat auf schwarzem Hintergrund, mit einer Hook-Zeile im Bild.
- Die Caption folgt dem Muster `<Hook> @TJR #tjr #tjrtrades #tjrclips`.
- Am besten laufen Geld-Hooks: „1 million dollars“, „800k in one day“.

**@tjrbuilt** erreicht im Median 900 Views, einzelne Clips bis 118K.
- TJRs Stimme läuft über Stock- oder Filmszenen, mit „X vs Y“-Titeln wie „Money vs Knowledge“.
- ⚠️ Wir machen das nicht, weil die Kampagne verlangt, dass TJR im Video zu sehen ist.

**Juliano selbst (@thewolfofinsurance)**: Am besten laufen „A regular day in my life“ (363K Views), „Haunted in here“ (121K) und „Win the day“ (52K). Seine Themen sind Sales, Geld, Mindset und „Lock in“, verpackt als Day-in-the-life eines 19-jährigen Agentur-Inhabers. Ein guter Juliano-Clip-Account läuft gerade nicht. Das ist eine Chance.

## Unser Stil (im Code umgesetzt in `clipper/render.py`)
- Format 1080x1920 mit 30 fps. Die Lautstärke wird auf -14 LUFS normalisiert, das ist der Standard der Plattformen.
- **Hook-Titel** oben: schwarze Schrift auf weißem Kasten. Er formuliert eine Neugier-Lücke oder Geld-Zahl, zum Beispiel „TJR to the guy who trades high at 9AM“.
- **Wort-für-Wort-Untertitel** in Großbuchstaben. Das gesprochene Wort ist gelb, jeder neue Wortblock „poppt“ kurz auf. Schimpfwörter werden im Bild zensiert (F*CK), sonst drosselt TikTok die Reichweite.
- **Immer Vollbild (Moritz' Clean-Stil), kein unscharfer Hintergrund.**
  - **Layout `crop`** ist ein fester Ausschnitt. Er schneidet auch Sponsor-Logos am Rand weg.
  - **Layout `track`** folgt automatisch dem Gesicht und ist gut für Handy-/IRL-Aufnahmen, in denen die Person wandert.

## Musik / Sound
Wir brennen **keine** Chart-Musik ins Video ein. Das würde zu Copyright-Stummschaltung und Ablehnung führen.
1. **TikTok und Instagram:** Beim Posten in der App einen Trend-Sound aus der Bibliothek wählen und auf ca. 5–10 % Lautstärke stellen. Für TJR passen „ski slopes“, „LEGACY (main)“ und „we found love slowed“, die nutzt @.tjr.him. Für Juliano passen motivierende Phonk- oder Piano-Sounds.
2. **YouTube Shorts:** In der YouTube-App über „Sound hinzufügen“ einen Track aus der YouTube-Audio-Library unterlegen. Alternativ `--music` mit einem lizenzfreien Track verwenden.

## Captions (Text unter dem Post)
- TJR: `{Hook} @TJR #TJR #tjrtrades #tjrclips #daytrading`
- Juliano: `{Hook} #JulianoMassarelli #sales #lifeinsurance #motivation #mindset`
- Alles auf Englisch, damit das Publikum zu mindestens 50 % aus USA, UK, CA, AU oder NZ kommt.

## TJR-Stil: @tjr.clips.core (vermessen am 25.10.2026)

Profil: „TJR Clips“, 4.970 Follower, 75,9K Likes, 21 Videos. Die 10 neuesten Videos liegen bei 954 bis 66.200 Aufrufen.

| Video | Aufrufe | Format | Aufbau |
|---|---|---|---|
| „@TJR Mentality.📈💵“ | **66.200** | 9:16, Quadrat in der Mitte | 3 Zitate zum Thema Schule und Geld, dazwischen schwarze „MENTALITY.“-Karten, am Ende „FACTS.“ |
| „W TJR📈“ | 7.318 | 1:1 | Zitat (Vater/Mentor), am Ende kurze Lifestyle-Montage |
| „thoughts on school“ | 7.286 | 1:1 | Zitat, dann Lifestyle-Montage mit „FACTS.“ darüber |
| „The goat.🐐“ | 6.120 | 16:9 | 45 s Podcast-Ausschnitt am Stück |
| „got rugged on beat drop“ | 5.610 | 9:16 split | Facecam oben, Chart unten, weiße Hook-Box |

**Merkmale:**
- **Untertitel:** immer nur **ein Wort**. Groß, in Großbuchstaben, schwere Schrift, metallischer Eis-Verlauf (weiß → hellblau) mit Schatten, auf Stirnhöhe. Flüche zensiert (F\*\*\*ING).
- **Farben:** stark gesättigt (kräftiges Blau/Türkis/Rot).
- **Schnitt:** kaum Schnitte (0–5 pro Video). Das Zitat trägt das Video, nicht die Montage.
- **Ton:** Musik läuft leise unter der Stimme durch (112–144 BPM).
- **Caption:** `@TJR <kurzer Satz>.<Emojis> #TJR #mentality #tjrtrades #daytrading #edit`

**Umsetzung:** `clipper/core.py`
- **Quadrat-Layout** für volle Gesichtsaufnahmen: `cx`/`cy`/`zoom` legen den Ausschnitt fest, `precrop` schneidet vorher etwas weg.
- **Split-Layout** für Stream-Clips: `cam` und `chart` als Pixel-Rechtecke in der Quelle, dazu `hook`.
- **Karten:** `{"card": "MENTALITY."}` zwischen den Zitaten, `{"card": "FACTS."}` am Ende.
- **Schrift:** Montserrat Black und Inter SemiBold (Google Fonts, OFL). Sie werden bei Bedarf nach `work/fonts/` geladen.

## Juliano-Stil: seine eigenen viralen Videos (vermessen am 25.10.2026)

@thewolfofinsurance: 669.900 Follower, 33,5M Likes. Die drei angepinnten Videos sind alle **„Real sales call“** (38,8M, 22,3M, 8,8M Aufrufe), seine normalen Videos liegen bei 6–53K.

- **Bild:** schwarzes 9:16. Darin ein Querformat-Bild von etwa 1,38:1 in der Mitte (bei 1080×1920: y 535–1317), Titel direkt darüber („Real sales call“ + 😂😭🥀).
- **Untertitel:** kleiner weißer Satz-Untertitel (ganze Satzstücke, normale Schreibung) unten im Bild.
- **Ton:** keine Musik, keine Effekte, nur Originalton.
- **Inhalt:** Juliano telefoniert mit einem Lead und spielt dabei Comedy (tanzt, reagiert, übertreibt).

**Umsetzung:** `clipper/core.py`, `layout: "band"`, `cy` = Bildausschnitt in der Höhe, `"music": null`.

**Quelle:** Die Embed-Downloads tragen das TikTok-Wasserzeichen. Deshalb kommen wasserzeichenfreie Videos von Moritz (ssstik) oder von YouTube.

## Neue Formate nach Moritz' 5 Vorlagen (25.10.2026) – gelten ab jetzt

Moritz' Kritik an den bisherigen Clips: zu viel Trading-Erklären und Charts, zu lang (1 Minute), Juliano-Untertitel schlecht. Neue Regeln:
- **Alle Clips 15–30 Sekunden**, nie länger.
- **Bei allen 5 Vorlagen läuft durchgehend Musik unter der Stimme** (gemessen: kein Moment ohne Grundpegel).
- Die 5 Vorlagen selbst (`work/reference/moritz-beispiele/ref1–5.mp4`) sind fremde Clips und werden **nie reposted**.

| Vorlage | Inhalt | Bild | Untertitel |
|---|---|---|---|
| ref1 (26 s) | Juliano im Podcast | schwarzes 9:16, Band mit gewölbten, weich auslaufenden Kanten | **große weiße Serifen-Wörter** (1–2), mitten im Bild, weicher Schatten, Schlüsselwort riesig („what“) |
| ref2 (60 s) | TJR Selfie, Real Talk | 1:1 | kleine weiße Sätze, einzelne Wörter farbig |
| ref3 (34 s) | TJR Real Talk + B-Roll dazwischen (Gym, Strand, Büro) | 1:1, Glow-Look | weiß, fett, 2 Wörter, Bildmitte |
| ref4 (22 s) | TJR redet in die Kamera | 16:9 | große weiße Großbuchstaben, 2 Wörter |
| ref5 (43 s) | Juliano Cold Call („Watch how Juliano handles ‚I'm not interested'“) | Band + Titel darüber | kleine Großbuchstaben |

### TJR „Real Talk“ (`clipper/realtalk.py`, `style: "tjr"`)
- **Inhalt:** TJR redet einfach – Mindset, Ansagen, Respekt, Haters. **Kein Trading-Erklären, keine Charts, kein Hook.**
- **Bild:** nur die Facecam (ohne Sponsor-Badge, ohne „NOT FINANCIAL ADVICE“), als Band `[1080, 760, 580]` auf Schwarz, leichter Glow-Look.
- **Untertitel:** 1–2 Wörter, Montserrat ExtraBold, weiß mit weichem Schatten, auf Brusthöhe.
- **Ton:** Musik −17 dB unter der Stimme, dann **Edit am Ende**: Luxus-Schnitte von TJR im Beat, der Drop sitzt auf dem ersten Schnitt (weißer Flash), Musik voll.
- **Musik:** lizenzfreie, dunkle Trap-/Epic-Tracks (Trap, Thunder, Sparta). LEGACY selbst hat Copyright und wird nicht eingebrannt.
- **Quelle:** Kick-VODs. `python -m clipper.kickvod get <id> --tail 25` holt das Stream-Ende zum Transkribieren, `--from/--to --quality 1080p60` den Ausschnitt.
- **Grenze:** Echter Real Talk ist auf Kick selten, er läuft meist über Trades. Auch Luxus-B-Roll von TJR gibt es dort kaum (Miami-Penthouse, Villa, Chrome-Hearts-Store, Sprinter, **keine Lambos**). Für mehr braucht es Material von YouTube oder Instagram, das Moritz vom PC aus bereitlegt.

### Juliano „Cold Call“ und „Hype“ (`clipper/realtalk.py`, `style: "juliano"`)
- **Cold Call:**
  - Musik am Anfang (er wartet), Musik aus während des Calls.
  - Der Kunde legt auf oder sagt ab, Julianos Reaktion folgt.
  - Dann **Drop**: Musik wieder voll, er ist voller Energie.
- **Hype:** Juliano überdreht im Büro mit seinem Team, Beat-Schnitte, nur Musik.
- **Bild:** wie ref1, schwarzes 9:16 mit Titel und Emojis, Band mit gewölbten Kanten. Für Ganzkörper-Szenen 4:5 (`frame: [1080, 1350, 330]`).
- **Untertitel:** **DM Serif Display**, groß und weiß, 1–2 Wörter mitten im Bild. Schlüsselwörter (`big`) stehen allein und extra groß.
