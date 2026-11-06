# Riesentour und Split – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-riesentour-split-demo.streamlit.app/)** -->

Erstes Stück der **Tourenbildung**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel). Die Fall-Demo [vrp_demo](https://sebastianhanisch-vrp-demo.streamlit.app/) rechnet Touren mit mehreren Fahrzeugen; diese Demo erklärt den Baustein, auf dem ihr genetischer Algorithmus dekodiert: eine Reihenfolge aller Kunden (die **Riesentour**), die ein kürzester Weg auf einem kleinen Graphen (der **Split**) optimal in Routen zerlegt.

## Kernfrage

Muss man Routen suchen, oder genügt eine Reihenfolge? Und ist die kürzeste Rundreise durch alle Kunden eine gute Reihenfolge? Die Demo zählt für bis zu acht Kunden alle Reihenfolgen durch (n! Stück), zerlegt jede per Split und vergleicht mit dem exakten Optimum über alle Tourenpläne.

## Modell

Ein Depot, n Kunden mit ganzzahliger Nachfrage, beliebig viele gleiche Fahrzeuge der Kapazität Q, euklidische Entfernungen, jede Route Depot – Kunden – Depot. **Hilfsgraph:** Knoten 0 bis n; ein Bogen von i nach j (i < j), wenn die Kunden i + 1 bis j der Reihenfolge zusammen höchstens die Kapazität belasten; sein Gewicht ist die Länge dieser Route. **Split** = kürzester Weg von 0 nach n (Dynamische Programmierung in Knotenreihenfolge). Alle Formeln und die Lesehilfe stehen im 📐-Expander der App.

## Methodik

- **Split** (`rsp_algorithm.split`): Bögen aus `split_arcs`, Rekursion `f(j) = min f(i) + c(i, j)`. Gleichstand: gewinnt die Zerlegung mit dem kleinsten Startknoten des letzten Bogens.
- **Alle Reihenfolgen** (`all_split_costs`): n! Reihenfolgen in Blöcken, der Split vektorisiert in numpy (`split_all`), gleiche Werte wie der Einzel-Split.
- **Exaktes Optimum** (`exact_cvrp`): beste Route je Kundenmenge per Held–Karp, dann Mengenzerlegung über alle Teilmengen (höchstens 2^9 Mengen).
- **Kürzeste Rundreise** (`tsp_tour`): Held–Karp über Depot und alle Kunden, in der lexikographisch kleineren Richtung gelesen.
- **Füllen bis voll** (`fill_until_full`): neue Route, sobald der nächste Kunde nicht mehr passt; schaut nie auf Entfernungen.
- **Instanzen:** drei Kartenarten (kleine Karte mit ganzen Koordinaten 0 bis 16; zufällig verteilt 0 bis 100; drei Häufungen), Depot in der Mitte oder in der Ecke, Kapazität aus der Zielroutenzahl (Gesamtnachfrage / (Zielroutenzahl · 0,9), aufgerundet).
- **Fünf Experimente:** Hilfsgraph von Hand, Split gegen „Füllen bis voll“, alle Riesentouren, von der Lösung zur Reihenfolge, Bänder über feste Instanzen.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an den Instanzen dieser Demo (feste Seeds), nachgerechnet in `tests/test_claims.py`, `tests/test_bands.py` und `tests/test_algorithm.py`.

| Frage | Befund |
|---|---|
| Liegt das Optimum unter den Reihenfolgen? | Ja: Das Minimum über alle n! Reihenfolgen ist in **80 von 80** Instanzen bei n = 8 und in **80 von 80** bei n = 9 gleich dem exakten Optimum (je 4 Zellen × 20 Instanzen). Unabhängig bestätigt gegen eine Aufzählung aller Zerlegungen und Reihenfolgen (`tests/test_oracle_riesentour_split.py`) |
| Wie selten ist es dort? | Eine Lösung mit k Routen, davon j mit mindestens zwei Kunden, entsteht aus genau **k!·2^j** Reihenfolgen. Median der Bänder: 48 von 40 320 (**0,119 %**) bei n = 8, 48 von 362 880 (**0,013 %**) bei n = 9. Bei eindeutigem Optimum stimmt die Zählung mit der Formel überein (148 von 150 Testinstanzen); bei Gleichständen gibt es mehr |
| Ist die kürzeste Rundreise eine gute Riesentour? | Meist nicht: Ihr Split ist bei n = 8 in **8 / 4 / 4 / 2** von 20 Instanzen optimal (Zellen: zufällig und Gruppen, Depot in der Mitte und in der Ecke), bei n = 9 in **5 / 4 / 1 / 4**. Abstand zum Optimum im Median 0,1 / 2,9 / 3,1 / 2,6 % (n = 8) und 0,9 / 1,7 / 4,3 / 1,6 % (n = 9), im Maximum 5,3 / 30,0 / 18,0 / 24,2 % und 7,2 / 17,9 / 21,9 / 25,6 % |
| Wie viele Reihenfolgen sind besser als die Rundreise? | Median je Zelle 0,03 bis 4,01 %; im Maximum **73,5 %** aller Reihenfolgen (n = 9, Gruppen, Depot in der Ecke) |
| „Füllen bis voll“ auf der Rundreise | Median 5,5 / 9,9 / 6,2 / 9,4 % über dem Optimum (n = 8), 2,5 / 2,7 / 5,9 / 2,8 % (n = 9), Maximum 58,8 %. Der Split ist nie schlechter als „Füllen bis voll“ auf derselben Reihenfolge (`tests/test_properties.py`) |
| Handbeispiel (Voreinstellung, 6 Kunden, kleine Karte, Depot in der Ecke, Seed 11) | Optimum 63,30 (2 Routen); kürzeste Rundreise 47,22 lang, ihr Split 68,38 in 3 Routen: **+8,0 %**; **30 von 720** Reihenfolgen (4,2 %) sind besser; **8 von 720** treffen das Optimum (2!·2²); „Füllen bis voll“ 71,11 (4,0 % mehr als der Split) |
| Von Hand nachgerechnetes Beispiel (`tests/conftest.py`, Depot (0,0), Kapazität 7) | Optimum 44,36 (Routen (1 4), (2 6 3 5)); Rundreise 38,24; ihr Split 47,19 in 3 Routen (+6,4 %), „Füllen bis voll“ 55,26 (+24,6 %), Nächster Nachbar + Split 49,45 (+11,5 %); 8 von 720 Reihenfolgen treffen das Optimum, 16 sind besser als die Rundreise |
| Der Split hängt nicht von der Leserichtung ab | Dieselbe Reihenfolge rückwärts gelesen hat denselben Split (`test_split_of_the_tour_uses_three_routes`); „Füllen bis voll“ dagegen kann sich ändern |

## Ehrliche Grenzen

- Alle Aussagen gelten für **höchstens 9 Kunden** und sagen nichts über große Instanzen. Dass Savings die perfekte Riesentour mit Split schlagen kann, wurde in der Vormessung bei n = 12 gesehen, ist aber nicht Gegenstand dieser Demo (Stück 4 der Linie).
- Die Instanzen stammen aus einem Eigenbau nach grobem Muster, nicht aus den Benchmarkinstanzen der Literatur.
- Der Maßstab ist das exakte Optimum bei unbegrenzter Flotte; mit höchstens B Fahrzeugen ändert sich der Split.
- Die kürzeste Rundreise ist unter gleich langen eine feste (Held–Karp); „Füllen bis voll“ hängt von der Leserichtung ab, die Demo liest in der lexikographisch kleineren Richtung.
- Die Bänder sind Spannen über 20 feste Instanzen je Zelle, keine Trends.
- Die Diagramme wurden im Browser angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Bögen geprüft.

### Annahmen, Grenzen und bekannte Probleme (Text wie in der App)

**Annahmen**
- Ein Depot, beliebig viele gleiche Fahrzeuge, euklidische und symmetrische Entfernungen, keine Zeitfenster; jeder Kunde wird genau einmal von einem Fahrzeug bedient, seine Nachfrage ist nicht teilbar.
- Alles ist simuliert: Karten aus Zufallszahlen, kein Straßennetz, keine echten Aufträge.

**Grenzen**
- Live werden höchstens 8 Kunden aufgezählt, 9 stehen vorberechnet in den Bändern; alle Aussagen gelten für höchstens 9 Kunden und sagen nichts über große Instanzen.
- Der Maßstab ist das exakte Optimum (Mengenzerlegung über alle Kundenmengen); für größere Instanzen wird es nicht gerechnet.
- Die kürzeste Rundreise ist unter gleich langen Rundreisen eine feste (Held–Karp, kleinster Kunde zuerst) und wird in der lexikographisch kleineren Richtung gelesen. Der Split hängt nicht von der Leserichtung ab, „Füllen bis voll“ schon.

**Bekannte Probleme und Unsicherheiten**
- Die Bänder sind Spannen über 20 feste Instanzen je Zelle, keine Trends und keine Aussagen über andere Kartenarten.
- Der Instanzgenerator ist ein Eigenbau nach grobem Muster, nicht die Benchmarkinstanzen der Literatur.
- Die Literaturangaben zur Idee der Riesentour (Beasley, Prins) wurden nicht im Volltext geprüft.
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Bögen geprüft.

## Befunde und Korrekturen gegenüber dem Plan

- **Kapazitätsenge:** Der Plan vermutete, der Vorteil des Splits gegenüber „Füllen bis voll“ wachse mit der Enge der Kapazität. Die Vormessung (n = 9, vier Auslastungen) hat das nicht bestätigt; die Demo enthält keinen Regler dafür und macht keine Aussage dazu.
- **„Füllen bis voll“ hängt von der Leserichtung ab:** Die Vormessung nannte Median 1,1 bis 7,5 % (andere Leserichtung der Rundreise). Die Demo liest in der lexikographisch kleineren Richtung und misst Median 2,5 bis 9,9 %; der Split bleibt in beiden Richtungen gleich. Die Demo zeigt die umgekehrte Lesart im Verdikt.
- **Handbeispiel als Seed statt fester Koordinaten:** Damit alle Regler wirken (kein Regler wird zum No-Op), ist die Voreinstellung ein erzeugter Fall (Seed 11) statt des Planbeispiels mit festen Koordinaten; dieses liegt als Fixture in `tests/conftest.py` und ist in `tests/test_algorithm.py` von Hand nachgerechnet.
- **Zeigen und Rechnen:** Die Differenz an den Kennzahlen wird aus den angezeigten, gerundeten Werten gebildet (68,38 − 63,30 = 5,08, nicht 5,07).
- **Fehler beim Bau gefunden:** Die Aufzählung scheiterte bei genau einem Kunden (leere Restfolge, falsche Form beim Umformen); behoben, `tests/test_edge_cases.py::test_one_customer` fängt es.

## Verifikation

- **Kern:** Split, Hilfsgraph, exakter Löser, Held–Karp und Zählung gegen das Handbeispiel, das aus Wurzeln von Hand zusammengesetzt ist (`tests/test_algorithm.py`).
- **Orakel:** Split gegen die Aufzählung aller Schnittmengen in reinem Python; exakter Löser gegen Aufzählung aller Zerlegungen und Reihenfolgen; Held–Karp gegen alle Permutationen; vektorisierter Split gegen den Einzel-Split; Dominanz (`tests/test_oracle_riesentour_split.py`).
- **Eigenschaften:** Split nie schlechter als „Füllen bis voll“ und nie unter dem Optimum, Umkehr der Reihenfolge, Verschieben, Skalieren, Umnummerieren, mehr Kapazität (`tests/test_properties.py`).
- **Randfälle:** ein und zwei Kunden, Kunde auf dem Depot, Nachfrage gleich Kapazität, Gleichstände, Reglergrenzen (`tests/test_edge_cases.py`).
- **Verdikte:** jede Schwelle und jede Zahl im Text an gesetzten Werten (`tests/test_verdicts.py`).
- **Zahlen der README:** `tests/test_claims.py`; die vorberechneten Bänder gegen eine frische Rechnung (n = 8 vollständig, von n = 9 eine Zelle) in `tests/test_bands.py`.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Aufbau der App, jede Art der Reihenfolge, Permalink, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout (Schnellstart oben, fester Kopf, aktives Preset hervorgehoben), Laufzeit-Importe.

## Tests

300 Tests. Laufzeit lokal etwa ein bis zwei Minuten, davon etwa 20 Sekunden für die frische Nachrechnung einer Zelle von n = 9.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `generate_precomputed.py` | erzeugt `rsp_bands.json` (vollständige Aufzählung für n = 8 und 9, rund zwei Minuten) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `rsp_algorithm.py` | Kern: Split, Hilfsgraph, Aufzählung, exakter Löser, Held–Karp, Reihenfolgen |
| `rsp_bands.json` | vorberechnete Bänder (4 Zellen × 2 Größen × 20 Instanzen) |
| `rsp_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets, Annahmentext |
| `rsp_evaluation.py` | Analyse, Bänder, Verdikt-Logik |
| `rsp_layout.py` | Fester Kopf (Stylesheet) |
| `rsp_pdf_export.py` | PDF-Export des Ergebnisses |
| `rsp_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `rsp_scenario.py` | Instanzen (Depot, Kunden, Nachfrage, Kapazität) |
| `rsp_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handinstanz, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Flottengrenze** (höchstens B Fahrzeuge): der Split braucht dann eine Dimension mehr; Stück 3 der Linie.
- **Konstruktionsverfahren** (Nächster Nachbar, Einfügen, Savings, Sweep) als eigene Verfahren: Stücke 2, 4 und 6; Savings und Sweep rechnet die Fall-Demo [vrp_demo](https://sebastianhanisch-vrp-demo.streamlit.app/).
- **Zeitfenster** (Etiketten im Hilfsgraphen): Stück 8.
- **Suche über Reihenfolgen** (memetischer Algorithmus mit Split): Stück 11; Lokalsuche zwischen Routen: [vrp-nachbarschaften-demo](https://sebastianhanisch-vrp-nachbarschaften-demo.streamlit.app/).
- **Eigene Reihenfolge eintippen** und beliebige Koordinaten: die Reihenfolge wird aus fünf festen Arten gewählt.
- **Große Instanzen:** kein exaktes Optimum, keine Aufzählung.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
