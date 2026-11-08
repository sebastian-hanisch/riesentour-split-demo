"""Riesentour und Split - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 1 der Reihe „Tourenbildung“: Eine einzige Reihenfolge aller Kunden (Riesentour) wird im Hilfsgraphen per kürzestem Weg optimal in Routen zerlegt (Split).
Die Demo zeigt, warum das Optimum unter diesen Reihenfolgen liegt, wie selten es dort ist und warum die kürzeste Rundreise keine gute Riesentour sein muss.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import rsp_algorithm as A
import rsp_constants as C
from rsp_evaluation import (
    Settings,
    analyse,
    band_rows,
    cell_label,
    de,
    num,
    pct,
    verdict_bands,
    verdict_count,
    verdict_dominance,
    verdict_fill,
    verdict_order,
    verdict_tour,
)
from rsp_layout import dunkles_design, kopf_css
from rsp_pdf_export import build_pdf
from rsp_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from rsp_visualization import build_aux_graph, build_bands, build_histogram, build_map

st.set_page_config(page_title="Riesentour und Split – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


def _routes_table(inst, result) -> str:
    rows = ["| Route | Kunden | Last | Länge |", "|---|---|---|---|"]
    for r, route in enumerate(result.routes):
        rows.append(f"| {r + 1} | {' '.join(str(c) for c in route)} | {inst.load(route)} von {inst.capacity} | {de(A.route_length(inst, route))} |")
    return "\n".join(rows)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in rsp_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧭 Riesentour und Split")
st.markdown(
    """
**Muss man Routen suchen, oder genügt eine Reihenfolge?** Eine **Riesentour** ist eine Reihenfolge aller Kunden, ohne Rücksicht auf die Fahrzeugkapazität.
Der **Split** zerlegt sie auf einem kleinen Graphen per kürzestem Weg optimal in Routen. Zur optimalen Lösung gibt es Riesentouren, deren Split genau so teuer ist:
Das Optimum liegt also unter den Reihenfolgen. Die Demo zählt alle Reihenfolgen durch, zeigt, **wie selten** das Optimum dort ist, und prüft, ob die **kürzeste Rundreise** eine gute Riesentour ist.

Weiter unten: **🔬 Der Hilfsgraph**, **🔬 Split gegen „Füllen bis voll“**, **🔬 Alle Riesentouren**, **🔬 Von der Lösung zur Reihenfolge**, **🔬 Wie oft ist die Rundreise gut?**,
**🚧 Wo die Annahmen enden**, der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert Riesentour und Split", expanded=True):
    st.markdown(
        """
1. **Die Riesentour** ist eine Reihenfolge aller Kunden: erst Kunde 3, dann 5, dann 1 und so weiter. Sie sagt nichts über Fahrzeuge oder Kapazität.
2. **Der Hilfsgraph** hat die Knoten 0 bis n. Ein Bogen von Knoten *i* nach Knoten *j* bedeutet: Die Kunden *i + 1* bis *j* der Reihenfolge fahren zusammen in **einer** Route,
   sofern ihre Nachfrage in ein Fahrzeug passt. Das Gewicht des Bogens ist die Länge dieser Route (Depot, Kunden, Depot).
3. **Der Split** ist der kürzeste Weg von Knoten 0 nach Knoten n. Jeder Bogen auf dem Weg ist eine Route.
4. **Warum eine Reihenfolge genügt:** Hängt man die Routen einer beliebigen Lösung hintereinander, liefert der Split dieser Reihenfolge höchstens deren Kosten. Das Optimum ist also nicht verloren,
   es liegt unter den Reihenfolgen. Es ist dort nur sehr selten, und die kürzeste Rundreise findet es oft nicht.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help=f"Bis n = {C.ENUM_MAX} werden alle Reihenfolgen aufgezählt (n! Stück); n = 9 steht nur in den vorberechneten Bändern.")
    family = st.selectbox("Art der Karte", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="„Kleine Karte“: ganze Koordinaten 0 bis 16, Nachfragen 1 bis 4. Die beiden anderen: Karte 0 bis 100, Nachfragen 1 bis 10; „In Gruppen“: drei Häufungen von Kunden.")
    depot = st.selectbox("Lage des Depots", list(range(len(C.DEPOTS))), key="depot_select", format_func=lambda i: C.DEPOTS[i])
    routes = st.slider("Zielroutenzahl", *bounds("routes_slider"), key="routes_slider",
                       help=f"Legt die Kapazität fest: Gesamtnachfrage geteilt durch (Zielroutenzahl mal {C.FILL}), aufgerundet, mindestens die größte Einzelnachfrage. Die optimale Lösung kann mehr Routen fahren.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Riesentour**")
    order_kind = st.selectbox("Reihenfolge", list(range(len(C.ORDER_KINDS))), key="order_select", format_func=lambda i: C.ORDER_KINDS[i],
                              help="Welche Reihenfolge der Split zerlegt. „Zufällig“ hängt vom Seed der Instanz ab; „Beste Riesentour“ reiht die Routen der optimalen Lösung aneinander.")

sync_query_params({"n_slider": int(n), "family_select": int(family), "depot_select": int(depot), "routes_slider": int(routes), "seed_input": int(seed), "order_select": int(order_kind)})

settings = Settings(int(n), int(family), int(depot), int(routes), int(seed), int(order_kind))
a = _analysis(settings)
inst = a.inst

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: Split der Reihenfolge gegen das Optimum")
m1, m2, m3 = st.columns(3)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2). Die Differenz aus den angezeigten, gerundeten Werten, damit Zahl und Delta zusammenpassen.
m1.metric("Optimum (kürzester Plan)", de(a.exact.cost), delta="Referenz", delta_color="off")
m2.metric(f"Split: {C.ORDER_KINDS[settings.order].lower()}", de(a.chosen.cost), delta=f"{round(a.chosen.cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")
m3.metric("Split der kürzesten Rundreise", de(a.tour.cost), delta=f"{round(a.tour.cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")

left, right = st.columns(2)
with left:
    st.markdown(f"**Split der Reihenfolge: {' '.join(str(c) for c in a.order)}**")
    st.plotly_chart(build_map(inst, a.chosen.routes), width="stretch", key="map_split")
with right:
    st.markdown("**Optimum über alle Tourenpläne**")
    st.plotly_chart(build_map(inst, a.exact.routes), width="stretch", key="map_opt")
st.caption(f"Kapazität {inst.capacity}, Gesamtnachfrage {sum(inst.demand)}, mindestens {inst.min_routes} Routen. Depot: Quadrat; Kunden: Kreise, je größer, desto mehr Nachfrage; jede Route eine Farbe.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, a), file_name="riesentour-und-split.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Ist die kürzeste Rundreise eine gute Riesentour?")
kind, text = verdict_tour(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Der Hilfsgraph: der Split von Hand")
st.caption("Knoten *i* heißt: Die ersten *i* Kunden der Reihenfolge sind bedient. Jede Wölbung ist eine mögliche Route (die Kunden dazwischen), grau mit dem Gewicht im Hover, "
           "grün der kürzeste Weg mit seinen Kosten. Bögen, deren Last die Kapazität übersteigt, gibt es nicht.")
arcs = A.split_arcs(inst, a.order)
path = A.split_path(inst, a.order, a.chosen)
st.plotly_chart(build_aux_graph(a.order, arcs, path), width="stretch", key="aux_chart")
st.markdown(_routes_table(inst, a.chosen))
st.caption(f"Der Hilfsgraph hat {len(arcs)} Bögen; die Summe der grünen Kosten ist {de(a.chosen.cost)}.")
kind, text = verdict_order(a)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Split gegen „Füllen bis voll“")
st.caption("„Füllen bis voll“ beginnt eine neue Route, sobald der nächste Kunde nicht mehr passt, und schaut nie auf die Entfernungen. Der Split schneidet dieselbe Reihenfolge dort, wo es billig ist.")
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"**Füllen bis voll: {de(a.fill.cost)}**")
    st.plotly_chart(build_map(inst, a.fill.routes), width="stretch", key="map_fill")
with c2:
    st.markdown(f"**Split: {de(a.chosen.cost)}**")
    st.plotly_chart(build_map(inst, a.chosen.routes), width="stretch", key="map_split2")
kind, text = verdict_fill(a)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Alle Riesentouren")
st.caption(f"Alle {num(a.n_orders)} Reihenfolgen der {inst.n} Kunden, jede per Split zerlegt. Das Histogramm zählt, wie viele Reihenfolgen welche Kosten ergeben.")
st.plotly_chart(build_histogram(a.costs, a.exact.cost, a.tour.cost, a.chosen.cost), width="stretch", key="hist_chart")
kind, text = verdict_count(a)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Von der Lösung zur Reihenfolge")
order_text = " ".join(str(c) for c in a.dom_order)
st.markdown(
    f"""
1. **Optimale Lösung:** {" und ".join("(" + " ".join(str(c) for c in r) + ")" for r in a.exact.routes)}, Kosten {de(a.exact.cost)}.
2. **Hintereinanderhängen:** Reihenfolge **{order_text}**.
3. **Split dieser Reihenfolge:** {de(a.dom_cost)}.
"""
)
kind, text = verdict_dominance(a)
getattr(st, kind)(text)
st.caption("Das ist kein Beweis, sondern die Probe an dieser Instanz. Der Gedanke dahinter: Der Split sucht über alle Zerlegungen, auch über die, mit der man die Reihenfolge gebaut hat, "
           "also kann er nicht schlechter sein. Dieselben Kosten entstehen aus allen Reihenfolgen, die die Routen in anderer Folge oder Richtung hintereinanderhängen.")

st.markdown("---")

st.subheader("🔬 Wie oft ist die Rundreise gut?")
band_n = st.radio("Kunden n", list(C.BAND_SIZES), horizontal=True, key="band_n",
                  help="Je 20 feste Instanzen je Zelle (Zielroutenzahl 3), alle Reihenfolgen aufgezählt; die Zahlen sind vorberechnet (generate_precomputed.py).")
rows = band_rows(int(band_n))
st.caption(f"Je {len(C.BAND_SEEDS)} feste Instanzen (BAND_SEEDS) je Zelle, vollständig aufgezählt; die Zahlen sind Spannen über Instanzen, kein Satz.")
if rows:
    st.plotly_chart(build_bands(rows), width="stretch", key="band_chart")
    table = ["| Zelle | Rundreise optimal | Abstand Median | Abstand Maximum | Reihenfolgen besser, Median | Reihenfolgen besser, Maximum |", "|---|---|---|---|---|---|"]
    for r in rows:
        table.append(f"| {cell_label(r)} | {r['tour_optimal']} von {r['count']} | {pct(r['gap_median'])} | {pct(r['gap_max'])} | {pct(r['better_median'], 2)} | {pct(r['better_max'])} |")
    st.markdown("\n".join(table))
kind, text = verdict_bands(rows)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Unbegrenzte Flotte** | Mit höchstens *B* Fahrzeugen braucht der Split eine Dimension mehr (Knoten mal Routenzahl); die Dominanz gilt weiter, die Zahl der Reihenfolgen, die das Optimum treffen, ändert sich | Stück 3 (Split gegen gierig, mit Flottengrenze) |
| **Euklidische, symmetrische Entfernungen** | Bei Einbahnstraßen hängt der Split von der Richtung ab, die Umkehrung der Reihenfolge ergibt nicht mehr dieselben Kosten | Kürzeste Wege |
| **Nur Kapazität, keine Zeitfenster** | Mit Zeitfenstern genügt der Bogen *i → j* nicht mehr: Er braucht Etiketten für die Ankunftszeit | Stück 8 (Zeitfenster) |
| **n höchstens 8 live, 9 vorberechnet** | Ab n = 10 gibt es über 3,6 Millionen Reihenfolgen; die Aufzählung wird zum Experiment mit Stichproben | Stück 11 (Riesentour suchen) |
| **Der Maßstab ist das exakte Optimum** | Für große Instanzen kennt man es nicht; die Aussagen hier gelten für höchstens 9 Kunden und sagen nichts über große Instanzen | Stück 15 (Verfahrenswahl) |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind ein Depot, $n$ Kunden mit Nachfragen und eine Fahrzeugkapazität. Gesucht ist ein Tourenplan mit kleinster Gesamtlänge, bei dem jede Route höchstens die Kapazität trägt.

| Symbol | Bedeutung |
|---|---|
| $0$, $1, \dots, n$ | Depot und Kunden |
| $d(u, v)$ | Entfernung zwischen $u$ und $v$ (euklidisch) |
| $q_i$, $Q$ | Nachfrage von Kunde $i$, Fahrzeugkapazität |
| $\pi = (\pi_1, \dots, \pi_n)$ | Riesentour: eine Reihenfolge aller Kunden |
| $c(i, j)$ | Länge der Route, die die Kunden $\pi_{i+1}, \dots, \pi_j$ bedient |
| $k$, $j^{*}$ | Zahl der Routen einer Lösung, davon die mit mindestens zwei Kunden |

**Route.** Für die Kunden $\pi_{i+1}, \dots, \pi_j$ in dieser Reihenfolge ist
$$c(i, j) = d(0, \pi_{i+1}) + \sum_{t = i+1}^{j-1} d(\pi_t, \pi_{t+1}) + d(\pi_j, 0), \qquad \text{zulässig, wenn } \sum_{t=i+1}^{j} q_{\pi_t} \le Q.$$

**Hilfsgraph und Split.** Der Graph hat die Knoten $0, \dots, n$ und für jedes zulässige Paar $i < j$ einen Bogen mit Gewicht $c(i, j)$. Der Split ist der kürzeste Weg von $0$ nach $n$; er folgt aus der Rekursion
$$f(0) = 0, \qquad f(j) = \min_{i < j,\ (i, j)\ \text{zulässig}} \big( f(i) + c(i, j) \big), \qquad \mathrm{Split}(\pi) = f(n).$$
Der Graph ist azyklisch (alle Bögen laufen nach rechts), die Rekursion rechnet die Knoten in ihrer Reihenfolge.

**Dominanz.** Sei $R_1, \dots, R_k$ ein beliebiger zulässiger Tourenplan und $\pi$ die Aneinanderreihung der Routen. Dann ist der Weg, der jede Route $R_r$ als einen Bogen nimmt, ein Weg von $0$ nach $n$ mit den Kosten des Plans; also gilt $\mathrm{Split}(\pi) \le \sum_r \mathrm{Länge}(R_r)$.
Gilt dies für einen optimalen Plan, so ist $\min_{\pi} \mathrm{Split}(\pi)$ gleich dem Optimum (jede Reihenfolge liefert ohnehin einen zulässigen Plan, also nie weniger).

**Zählung.** Eine Lösung mit $k$ Routen, von denen $j^{*}$ mindestens zwei Kunden haben, lässt sich auf genau $k! \cdot 2^{j^{*}}$ Arten hintereinanderhängen: $k!$ Folgen der Routen, und jede Route mit mindestens zwei Kunden in zwei Richtungen. Das gilt für die Aneinanderreihung der Routen; ob weitere Reihenfolgen dieselben Kosten ergeben, zeigt die Aufzählung (bei Gleichständen mehr).

**Literatur.** Die Idee, erst eine Riesentour zu bilden und sie dann in Routen zu zerlegen („route first, cluster second“), geht laut Sekundärquellen auf Beasley (1983) zurück; Prins (2004) hat den Split auf dem azyklischen Hilfsgraphen in einem memetischen Algorithmus verwendet. Diese Quellen wurden nicht im Volltext geprüft; die Demo übernimmt keine Zahl daraus, alle Zahlen sind Messungen an den Instanzen der Demo.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
