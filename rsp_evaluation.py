"""Kennzahlen, Verdikt-Logik und Bänder. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import median

import numpy as np

import rsp_algorithm as A
import rsp_constants as C
from rsp_scenario import Instance, make_instance


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    family: int = C.DEFAULT_FAMILY
    depot: int = C.DEFAULT_DEPOT
    routes: int = C.DEFAULT_ROUTES
    seed: int = C.DEFAULT_SEED
    order: int = C.DEFAULT_ORDER


@dataclass(frozen=True, eq=False)
class Analysis:
    settings: Settings
    inst: Instance
    order: tuple[int, ...]               # die gewählte Reihenfolge
    exact: A.ExactResult                 # Optimum über alle Tourenpläne
    chosen: A.SplitResult                # Split der gewählten Reihenfolge
    fill: A.SplitResult                  # „Füllen bis voll“ auf derselben Reihenfolge
    fill_reversed: A.SplitResult         # … auf der umgekehrten Reihenfolge (der Split ist richtungsunabhängig, „Füllen bis voll“ nicht)
    tour_length: float                   # Länge der kürzesten Rundreise durch Depot und alle Kunden
    tour_order: tuple[int, ...]
    tour: A.SplitResult                  # Split der kürzesten Rundreise
    costs: np.ndarray                    # Split-Kosten aller n! Reihenfolgen
    n_orders: int
    n_opt: int                           # Reihenfolgen, deren Split das Optimum trifft
    formula: int                         # k!·2^j für die gefundene optimale Lösung
    n_better_chosen: int                 # Reihenfolgen, die nach dem Split billiger sind als die gewählte
    n_better_tour: int                   # … als die kürzeste Rundreise
    dom_order: tuple[int, ...]           # Aneinanderreihung der optimalen Routen
    dom_cost: float                      # Split dieser Aneinanderreihung


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def num(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{int(n):,}".replace(",", " ")


def routes_word(k: int) -> str:
    return f"{k} Route" if k == 1 else f"{k} Routen"


def gap_percent(cost: float, reference: float) -> float:
    """Mehrkosten gegenüber der Referenz in Prozent der Referenz; unter der Toleranz oder ohne Referenzkosten gibt es keinen Abstand."""
    if reference <= 0 or abs(cost - reference) <= C.TOL:
        return 0.0
    return 100.0 * (cost - reference) / reference


def share_percent(count: int, total: int) -> float:
    return 0.0 if total <= 0 else 100.0 * count / total


# ----------------------------------------------------------------------------------------------------------------------------------- Analyse

def choose_order(kind: int, inst: Instance, seed: int, exact: A.ExactResult, tour_order) -> tuple[int, ...]:
    if kind == 0:
        return tuple(tour_order)
    if kind == 1:
        return A.nearest_neighbour_order(inst)
    if kind == 2:
        return A.sweep_order(inst)
    if kind == 3:
        return A.random_order(inst, seed)
    return A.concatenate(exact.routes)


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.n, settings.family, settings.depot, settings.routes, settings.seed)
    exact = A.exact_cvrp(inst)
    tour_length, tour_order = A.tsp_tour(inst)
    order = choose_order(settings.order, inst, settings.seed, exact, tour_order)
    chosen = A.split(inst, order)
    tour = A.split(inst, tour_order)
    costs = A.all_split_costs(inst)
    dom_order = A.concatenate(exact.routes)
    return Analysis(
        settings, inst, order, exact, chosen, A.fill_until_full(inst, order), A.fill_until_full(inst, order[::-1]), tour_length, tour_order, tour, costs, len(costs),
        int(np.sum(costs <= exact.cost + C.TOL)), A.reproducing_orders(exact.routes),
        int(np.sum(costs < chosen.cost - C.TOL)), int(np.sum(costs < tour.cost - C.TOL)),
        dom_order, A.split(inst, dom_order).cost,
    )


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

def band_cell(n: int, family: int, depot: int, seeds=C.BAND_SEEDS, routes: int = C.BAND_ROUTES) -> dict:
    """Eine Zelle der Bänder: feste Instanzen, vollständige Aufzählung; Spannen sind Minimum, Median, Maximum über die Instanzen."""
    gaps, betters, fills, dominance, tour_optimal, optimal_share = [], [], [], 0, 0, []
    for seed in seeds:
        inst = make_instance(n, family, depot, routes, seed)
        exact = A.exact_cvrp(inst)
        _, tour_order = A.tsp_tour(inst)
        tour = A.split(inst, tour_order)
        costs = A.all_split_costs(inst)
        gaps.append(gap_percent(tour.cost, exact.cost))
        betters.append(share_percent(int(np.sum(costs < tour.cost - C.TOL)), len(costs)))
        fills.append(gap_percent(A.fill_until_full(inst, tour_order).cost, exact.cost))
        optimal_share.append(share_percent(int(np.sum(costs <= exact.cost + C.TOL)), len(costs)))
        dominance += int(abs(float(costs.min()) - exact.cost) <= C.TOL)
        tour_optimal += int(gaps[-1] == 0.0)
    return {
        "n": n, "family": family, "depot": depot, "count": len(seeds), "dominance": dominance, "tour_optimal": tour_optimal,
        "gap_min": min(gaps), "gap_median": median(gaps), "gap_max": max(gaps),
        "better_min": min(betters), "better_median": median(betters), "better_max": max(betters),
        "fill_median": median(fills), "fill_max": max(fills), "optimal_share_median": median(optimal_share),
    }


@lru_cache(maxsize=1)
def load_bands() -> dict:
    """Vorberechnete Bänder für n = 8 und n = 9 (generate_precomputed.py); {} wenn die Datei fehlt."""
    path = Path(__file__).with_name(C.BAND_FILE)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def band_rows(n: int) -> list[dict]:
    rows = load_bands().get("cells", [])
    order = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
    return sorted((r for r in rows if r["n"] == n), key=lambda r: order[(r["family"], r["depot"])])


KIND_LABELS = ("kleine Karte", "zufällig verteilt", "in Gruppen")


def cell_label(row: dict) -> str:
    return f"{C.DEPOTS[row['depot']]}, {KIND_LABELS[row['family']]}"


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_tour(a: Analysis) -> tuple[str, str]:
    """Kernfrage: Wie gut ist die kürzeste Rundreise als Riesentour?"""
    gap = gap_percent(a.tour.cost, a.exact.cost)
    if gap == 0.0:
        return "success", (f"Hier ist die kürzeste Rundreise (Länge {de(a.tour_length)}) auch als Riesentour optimal: Der Split ergibt {de(a.tour.cost)}, das Optimum. "
                           f"Keine der {num(a.n_orders)} Reihenfolgen ist besser. Das ist ein Glücksfall der Instanz, keine Regel.")
    kind = "info" if gap < C.GAP_WARN else "warning"
    return kind, (f"Die kürzeste Rundreise (Länge {de(a.tour_length)}) ergibt nach dem Split {de(a.tour.cost)}: **{pct(gap)}** über dem Optimum {de(a.exact.cost)}. "
                  f"{num(a.n_better_tour)} von {num(a.n_orders)} Reihenfolgen ({pct(share_percent(a.n_better_tour, a.n_orders))}) sind nach dem Split besser als sie.")


def verdict_order(a: Analysis) -> tuple[str, str]:
    """Experiment 1: die gewählte Reihenfolge, ihr Split und das Optimum."""
    gap = gap_percent(a.chosen.cost, a.exact.cost)
    if gap == 0.0:
        return "success", (f"Der Split dieser Reihenfolge ergibt {de(a.chosen.cost)} in {routes_word(len(a.chosen.routes))}: das Optimum. "
                           f"Keine der {num(a.n_orders)} Reihenfolgen ist besser.")
    kind = "info" if gap < C.GAP_WARN else "warning"
    return kind, (f"Der Split dieser Reihenfolge kostet {de(a.chosen.cost)} in {routes_word(len(a.chosen.routes))}: {pct(gap)} über dem Optimum {de(a.exact.cost)} "
                  f"({routes_word(len(a.exact.routes))}). {num(a.n_better_chosen)} von {num(a.n_orders)} Reihenfolgen ({pct(share_percent(a.n_better_chosen, a.n_orders))}) sind besser.")


def _reverse_note(a: Analysis) -> str:
    if abs(a.fill_reversed.cost - a.fill.cost) <= C.TOL:
        return " In umgekehrter Richtung gelesen ändert sich daran nichts."
    return (f" In umgekehrter Richtung gelesen kostet „Füllen bis voll“ {de(a.fill_reversed.cost)} in {routes_word(len(a.fill_reversed.routes))}; "
            f"der Split bleibt bei {de(a.chosen.cost)}, denn er hängt nicht von der Leserichtung ab.")


def verdict_fill(a: Analysis) -> tuple[str, str]:
    """Experiment 2: Split gegen „Füllen bis voll“ auf derselben Reihenfolge."""
    extra = gap_percent(a.fill.cost, a.chosen.cost)
    if extra == 0.0:
        return "info", (f"Auf dieser Reihenfolge fällt „Füllen bis voll“ mit dem Split zusammen ({de(a.chosen.cost)}): "
                        "Die Schnitte, die die Kapazität erzwingt, sind auch die billigsten." + _reverse_note(a))
    return "success", (f"„Füllen bis voll“ kostet {de(a.fill.cost)} in {routes_word(len(a.fill.routes))}, der Split {de(a.chosen.cost)} in {len(a.chosen.routes)}: "
                       f"„Füllen bis voll“ kostet **{pct(extra)}** mehr als der Split." + _reverse_note(a))


def verdict_count(a: Analysis) -> tuple[str, str]:
    """Experiment 3: wie viele Reihenfolgen treffen das Optimum, und was sagt die Formel?"""
    k = len(a.exact.routes)
    j = sum(1 for r in a.exact.routes if len(r) >= 2)
    share = pct(share_percent(a.n_opt, a.n_orders), 3)
    base = f"{num(a.n_opt)} von {num(a.n_orders)} Reihenfolgen ({share}) ergeben nach dem Split das Optimum. "
    formula = f"Eine Lösung mit {routes_word(k)}, davon {j} mit mindestens zwei Kunden, entsteht aus {k}!·2^{j} = {num(a.formula)} Reihenfolgen. "
    if a.n_opt == a.formula:
        return "success", base + formula + "Die Zahlen stimmen überein: Die optimale Lösung ist eindeutig."
    if a.n_opt > a.formula:
        return "info", base + formula + (f"Es gibt mehr: Mehrere Lösungen sind gleich gut (zum Beispiel, weil ein Kunde auf dem Depot oder auf einem anderen Kunden liegt), "
                                         f"gezählt werden {num(a.n_opt)}.")
    return "warning", base + formula + "Das sind weniger, als die Formel erwartet: Das darf nicht vorkommen."


def verdict_dominance(a: Analysis) -> tuple[str, str]:
    """Experiment 4: Aneinanderreihung der optimalen Routen, danach Split."""
    order = " ".join(str(c) for c in a.dom_order)
    if abs(a.dom_cost - a.exact.cost) <= C.TOL:
        return "success", f"Die Reihenfolge {order} (die optimalen Routen hintereinander) ergibt nach dem Split {de(a.dom_cost)}: dieselben Kosten wie das Optimum."
    return "warning", f"Die Reihenfolge {order} ergibt nach dem Split {de(a.dom_cost)} statt {de(a.exact.cost)}: Das darf nicht vorkommen."


def verdict_bands(rows: list[dict]) -> tuple[str, str]:
    """Experiment 5: Bänder über die festen Instanzen (eine Zeile je Zelle)."""
    if not rows:
        return "warning", "Die vorberechneten Bänder fehlen (rsp_bands.json)."
    total = sum(r["count"] for r in rows)
    good = sum(r["tour_optimal"] for r in rows)
    dominance = sum(r["dominance"] for r in rows)
    low = min(r["gap_median"] for r in rows)
    high = max(r["gap_median"] for r in rows)
    worst = max(r["gap_max"] for r in rows)
    kind = "warning" if good * 2 < total else "info"
    return kind, (f"Bei n = {rows[0]['n']} ist die kürzeste Rundreise nach dem Split in {good} von {total} Instanzen optimal. Der Abstand zum Optimum liegt im Median "
                  f"je Zelle zwischen {pct(low)} und {pct(high)}, im schlechtesten Fall bei {pct(worst)}. Das Minimum über alle Reihenfolgen war in {dominance} von {total} "
                  "Instanzen gleich dem Optimum.")
