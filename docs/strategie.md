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
