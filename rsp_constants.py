"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 4, 8, 6
ENUM_MAX = 8                                  # bis hierher werden alle n! Reihenfolgen live aufgezählt; n = 9 steht vorberechnet in rsp_bands.json
SEED_MAX, DEFAULT_SEED = 999999, 11
ROUTES_MIN, ROUTES_MAX, DEFAULT_ROUTES = 2, 4, 2
FILL = 0.9                                    # Kapazität = aufgerundet Gesamtnachfrage / (Zielroutenzahl * FILL)
CLUSTERS, CLUSTER_SIGMA = 3, 7.0              # Familie „In Gruppen“
FAMILIES = ("Kleine Karte (ganze Zahlen)", "Zufällig verteilt (0 bis 100)", "In Gruppen (0 bis 100)")
FAMILY_KEYS = ("small", "random", "clustered")
DEFAULT_FAMILY = 0
DEPOTS = ("In der Mitte", "In der Ecke")
DEFAULT_DEPOT = 1
ORDER_KINDS = ("Kürzeste Rundreise", "Nächster Nachbar", "Nach Winkel um das Depot", "Zufällige Reihenfolge", "Beste Riesentour")
DEFAULT_ORDER = 0

BAND_SEEDS = tuple(range(300000, 300020))     # feste Instanzen für die Bänder: nie ein einzelner Seed als Befund
BAND_SIZES = (8, 9)
BAND_ROUTES = 3                               # Zielroutenzahl der Bänder
BAND_CELLS = ((1, 0), (2, 0), (1, 1), (2, 1))  # (Familie, Depotlage): zufällig/Gruppen mal Mitte/Ecke
BAND_FILE = "rsp_bands.json"
TOL = 1e-9                                    # Gleichstände und Optimum-Treffer: absolut
GAP_WARN = 5.0                                # Abstand in Prozent, ab dem das Verdikt warnt

COLOR_PATH = "#2F6B65"
COLOR_OPT = "#c0504d"
COLOR_TSP = "#7b5ea7"
COLOR_ORDER = "#d8a13a"
COLOR_OTHER = "rgba(150,150,150,0.35)"
ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b")

# Presets: Werte werden in der App an den Seeds geprüft (tests/test_presets.py, tests/test_claims.py)
PRESETS = {
    "Handbeispiel (n = 6)": {"n": 6, "family": 0, "depot": 1, "routes": 2, "seed": 11, "order": 0},
    "Rundreise trifft das Optimum (n = 6)": {"n": 6, "family": 0, "depot": 0, "routes": 2, "seed": 9, "order": 0},
    "Fast alle Reihenfolgen besser (n = 8)": {"n": 8, "family": 2, "depot": 1, "routes": 3, "seed": 8, "order": 0},
    "Vier Routen (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 4, "seed": 10, "order": 0},
    "Mehr Routen als nötig (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 4, "seed": 17, "order": 0},
    "Gleich gute Lösungen (n = 6)": {"n": 6, "family": 0, "depot": 0, "routes": 2, "seed": 1, "order": 0},
}
PRESET_HELP = {
    "Handbeispiel (n = 6)": "Sechs Kunden auf einer kleinen Karte, Depot in der Ecke: Die kürzeste Rundreise ergibt nach dem Split deutlich mehr als das Optimum.",
    "Rundreise trifft das Optimum (n = 6)": "Hier ist die kürzeste Rundreise als Riesentour optimal; der Nächste Nachbar dagegen nicht (Reihenfolge links wählen).",
    "Fast alle Reihenfolgen besser (n = 8)": "Die Kunden liegen in Gruppen, das Depot in der Ecke: Mehr als zwei Drittel aller Reihenfolgen sind nach dem Split besser als die kürzeste Rundreise.",
    "Vier Routen (n = 8)": "Vier Routen bei acht Kunden: 192 von 40 320 Reihenfolgen treffen per Split das Optimum.",
    "Mehr Routen als nötig (n = 8)": "Die optimale Lösung fährt fünf Routen, obwohl vier genügen würden.",
    "Gleich gute Lösungen (n = 6)": "Ein Kunde liegt auf dem Depot: 24 Reihenfolgen treffen das Optimum, mehr als die 8, die eine einzelne Lösung erzeugt.",
}

# Text des Expanders „Annahmen, Grenzen und bekannte Probleme“; derselbe Text steht in der README (tests/test_readme.py vergleicht beide)
ASSUMPTIONS_MARKDOWN = """**Annahmen**
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
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Bögen geprüft."""
