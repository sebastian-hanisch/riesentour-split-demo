"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt eine Analyse mit gesetzten Zahlen, nicht Seeds. Damit prüft der Test die Grenzen (Abstand 0, unter 5 %,
ab 5 %) und jede genannte Zahl direkt."""

import dataclasses

import numpy as np

import rsp_algorithm as A
import rsp_evaluation as ev
from rsp_scenario import Instance

INST = Instance(((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)), (1, 1, 1), 2)


def _a(**kw) -> ev.Analysis:
    base = dict(
        settings=ev.Settings(), inst=INST, order=(1, 2, 3), exact=A.ExactResult(100.0, ((1, 2), (3,))), chosen=A.SplitResult(100.0, ((1, 2), (3,))),
        fill=A.SplitResult(100.0, ((1, 2), (3,))), fill_reversed=A.SplitResult(100.0, ((3,), (2, 1))), tour_length=80.0, tour_order=(1, 2, 3),
        tour=A.SplitResult(100.0, ((1, 2), (3,))), costs=np.array([100.0]), n_orders=720, n_opt=4, formula=4, n_better_chosen=0, n_better_tour=0,
        dom_order=(1, 2, 3), dom_cost=100.0,
    )
    base.update(kw)
    return ev.Analysis(**base)


# ----------------------------------------------------------------------------------------------------------------------------------- Rundreise

def test_tour_verdict_success_when_the_tour_is_optimal():
    kind, text = ev.verdict_tour(_a(tour_length=80.0))
    assert kind == "success"
    assert "Länge 80,00" in text and "Split ergibt 100,00" in text and "Keine der 720 Reihenfolgen ist besser" in text


def test_tour_verdict_threshold_is_inclusive_at_five_percent():
    kind, text = ev.verdict_tour(_a(tour=A.SplitResult(104.9, ((1, 2, 3),)), n_better_tour=36))
    assert kind == "info"
    assert "nach dem Split 104,90" in text and "**4,9 %** über dem Optimum 100,00" in text and "36 von 720 Reihenfolgen (5,0 %)" in text
    kind, text = ev.verdict_tour(_a(tour=A.SplitResult(105.0, ((1, 2, 3),)), n_better_tour=360))
    assert kind == "warning" and "**5,0 %**" in text and "360 von 720 Reihenfolgen (50,0 %)" in text


# ----------------------------------------------------------------------------------------------------------------------------------- gewählte Reihenfolge

def test_order_verdict_success_names_cost_and_route_count():
    kind, text = ev.verdict_order(_a())
    assert kind == "success"
    assert "ergibt 100,00 in 2 Routen: das Optimum" in text and "Keine der 720 Reihenfolgen ist besser" in text


def test_order_verdict_names_costs_routes_and_better_orders():
    kind, text = ev.verdict_order(_a(chosen=A.SplitResult(110.0, ((1,), (2,), (3,))), n_better_chosen=72))
    assert kind == "warning"                                  # 10 % über dem Optimum
    assert "kostet 110,00 in 3 Routen: 10,0 % über dem Optimum 100,00 (2 Routen)" in text and "72 von 720 Reihenfolgen (10,0 %)" in text
    assert ev.verdict_order(_a(chosen=A.SplitResult(102.0, ((1,), (2,), (3,)))))[0] == "info"


# ----------------------------------------------------------------------------------------------------------------------------------- Füllen bis voll

def test_fill_verdict_when_both_coincide():
    kind, text = ev.verdict_fill(_a())
    assert kind == "info"
    assert "fällt „Füllen bis voll“ mit dem Split zusammen (100,00)" in text and "ändert sich daran nichts" in text


def test_fill_verdict_names_the_extra_cost_and_the_reversed_reading():
    kind, text = ev.verdict_fill(_a(fill=A.SplitResult(104.0, ((1,), (2, 3))), fill_reversed=A.SplitResult(112.5, ((3,), (2,), (1,)))))
    assert kind == "success"
    assert "kostet 104,00 in 2 Routen, der Split 100,00 in 2" in text and "**4,0 %** mehr als der Split" in text
    assert "kostet „Füllen bis voll“ 112,50 in 3 Routen" in text and "der Split bleibt bei 100,00" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Zählung

def test_count_verdict_unique_optimum():
    kind, text = ev.verdict_count(_a())
    assert kind == "success"
    assert "4 von 720 Reihenfolgen (0,556 %)" in text and "mit 2 Routen, davon 1 mit mindestens zwei Kunden, entsteht aus 2!·2^1 = 4 Reihenfolgen" in text
    assert "eindeutig" in text


def test_count_verdict_more_orders_than_the_formula():
    kind, text = ev.verdict_count(_a(n_opt=24, formula=8, exact=A.ExactResult(100.0, ((1, 2, 3),)), n_orders=40320))
    assert kind == "info"
    assert "24 von 40 320 Reihenfolgen (0,060 %)" in text and "1 Route, davon 1" in text and "2!·2^1" not in text and "gezählt werden 24" in text


def test_count_verdict_fewer_orders_than_the_formula_is_a_warning():
    kind, text = ev.verdict_count(_a(n_opt=2, formula=4))
    assert kind == "warning" and "darf nicht vorkommen" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Dominanz

def test_dominance_verdict():
    kind, text = ev.verdict_dominance(_a(dom_order=(3, 1, 2)))
    assert kind == "success" and "Reihenfolge 3 1 2" in text and "ergibt nach dem Split 100,00" in text
    kind, text = ev.verdict_dominance(_a(dom_cost=100.5))
    assert kind == "warning" and "100,50 statt 100,00" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

def _row(n, tour_optimal, gap_median, gap_max, dominance=20):
    return {"n": n, "family": 1, "depot": 0, "count": 20, "dominance": dominance, "tour_optimal": tour_optimal, "gap_median": gap_median, "gap_max": gap_max}


def test_band_verdict_counts_and_threshold():
    rows = [_row(8, 8, 0.1, 5.3), _row(8, 4, 2.9, 30.0)]
    kind, text = ev.verdict_bands(rows)
    assert kind == "warning"                                  # 12 von 40: weniger als die Hälfte
    assert "Bei n = 8 ist die kürzeste Rundreise nach dem Split in 12 von 40 Instanzen optimal" in text
    assert "zwischen 0,1 % und 2,9 %" in text and "im schlechtesten Fall bei 30,0 %" in text and "in 40 von 40 Instanzen gleich dem Optimum" in text
    assert ev.verdict_bands([_row(9, 10, 1.0, 2.0), _row(9, 10, 1.0, 2.0)])[0] == "info"   # genau die Hälfte: keine Warnung


def test_band_verdict_without_the_precomputed_file():
    kind, text = ev.verdict_bands([])
    assert kind == "warning" and "rsp_bands.json" in text


def test_cell_label_names_depot_and_kind():
    assert ev.cell_label(_row(8, 1, 0, 0)) == "In der Mitte, zufällig verteilt"
    assert ev.cell_label(dict(_row(8, 1, 0, 0), family=2, depot=1)) == "In der Ecke, in Gruppen"


def test_dataclass_is_frozen():
    a = _a()
    try:
        a.n_orders = 1
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("Analysis muss unveränderlich sein")
