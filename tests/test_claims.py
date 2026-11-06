"""Jede Zahl der README („Befunde“) und der Preset-Hilfen, nachgerechnet mit denselben Funktionen wie die App (DEMO-PLAYBOOK §4).

Die Aufzählung ist deterministisch; Kosten werden auf zwei Stellen verglichen, Prozentwerte auf eine."""

import pytest

import rsp_algorithm as A
import rsp_constants as C
import rsp_evaluation as ev


def _preset(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


# ----------------------------------------------------------------------------------------------------------------------------------- Handbeispiel (Preset)

def test_default_example_numbers():
    a = _preset("Handbeispiel (n = 6)")
    assert round(a.exact.cost, 2) == 63.30 and len(a.exact.routes) == 2
    assert round(a.tour_length, 2) == 47.22
    assert round(a.tour.cost, 2) == 68.38 and len(a.tour.routes) == 3
    assert round(ev.gap_percent(a.tour.cost, a.exact.cost), 1) == 8.0
    assert (a.n_better_tour, a.n_orders) == (30, 720) and round(ev.share_percent(30, 720), 1) == 4.2
    assert (a.n_opt, a.formula) == (8, 8)
    assert round(a.fill.cost, 2) == 71.11 and round(ev.gap_percent(a.fill.cost, a.chosen.cost), 1) == 4.0
    assert A.fill_until_full(a.inst, a.order[::-1]).cost == pytest.approx(a.fill.cost)         # hier ändert die Leserichtung nichts
    assert a.inst.capacity == 9 and a.inst.demand == (3, 1, 3, 1, 4, 4)


def test_default_example_nearest_neighbour_is_optimal_while_the_tour_is_not():
    a = _preset("Handbeispiel (n = 6)")
    assert A.split(a.inst, A.nearest_neighbour_order(a.inst)).cost == pytest.approx(a.exact.cost)
    assert a.tour.cost > a.exact.cost + 1


# ----------------------------------------------------------------------------------------------------------------------------------- Preset-Hilfetexte

def test_preset_help_numbers():
    a = _preset("Rundreise trifft das Optimum (n = 6)")
    assert ev.gap_percent(a.tour.cost, a.exact.cost) == 0.0 and a.n_better_tour == 0
    nn = A.split(a.inst, A.nearest_neighbour_order(a.inst)).cost
    assert nn > a.exact.cost + 1                                            # „der Nächste Nachbar dagegen nicht“

    a = _preset("Fast alle Reihenfolgen besser (n = 8)")
    assert a.n_better_tour / a.n_orders > 2 / 3 and (a.n_better_tour, a.n_orders) == (29712, 40320)

    a = _preset("Vier Routen (n = 8)")
    assert (len(a.exact.routes), a.n_opt, a.n_orders) == (4, 192, 40320) and a.n_opt == a.formula

    a = _preset("Mehr Routen als nötig (n = 8)")
    assert len(a.exact.routes) == 5 and a.inst.min_routes == 4

    a = _preset("Gleich gute Lösungen (n = 6)")
    assert (a.n_opt, a.formula) == (24, 8) and a.inst.xy[1] == a.inst.xy[0]


# ----------------------------------------------------------------------------------------------------------------------------------- Handbeispiel von Hand (Fixture)

def test_hand_example_from_the_plan(hand):
    ex = A.exact_cvrp(hand)
    order = (5, 1, 4, 3, 6, 2)
    assert round(ex.cost, 2) == 44.36
    assert round(A.tsp_tour(hand)[0], 2) == 38.24
    assert round(A.split(hand, order).cost, 2) == 47.19 and round(ev.gap_percent(A.split(hand, order).cost, ex.cost), 1) == 6.4
    assert round(A.fill_until_full(hand, order).cost, 2) == 55.26 and round(ev.gap_percent(A.fill_until_full(hand, order).cost, ex.cost), 1) == 24.6
    nn = A.nearest_neighbour_order(hand)
    assert round(A.split(hand, nn).cost, 2) == 49.45 and round(ev.gap_percent(A.split(hand, nn).cost, ex.cost), 1) == 11.5
    costs = A.all_split_costs(hand)
    assert len(costs) == 720 and int((costs <= ex.cost + 1e-9).sum()) == 8 and int((costs < A.split(hand, order).cost - 1e-9).sum()) == 16


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder (aus rsp_bands.json)

def _col(n, key):
    return [r[key] for r in ev.band_rows(n)]


def test_bands_dominance_and_counts():
    for n in C.BAND_SIZES:
        rows = ev.band_rows(n)
        assert len(rows) == 4 and all(r["count"] == 20 for r in rows)
        assert [r["dominance"] for r in rows] == [20, 20, 20, 20]       # das Minimum über alle Reihenfolgen ist in jeder Instanz das Optimum
    assert _col(8, "tour_optimal") == [8, 4, 4, 2] and sum(_col(8, "tour_optimal")) == 18
    assert _col(9, "tour_optimal") == [5, 4, 1, 4] and sum(_col(9, "tour_optimal")) == 14


def test_bands_gap_of_the_shortest_tour():
    assert [round(v, 1) for v in _col(8, "gap_median")] == [0.1, 2.9, 3.1, 2.6]
    assert [round(v, 1) for v in _col(8, "gap_max")] == [5.3, 30.0, 18.0, 24.2]
    assert [round(v, 1) for v in _col(9, "gap_median")] == [0.9, 1.7, 4.3, 1.6]
    assert [round(v, 1) for v in _col(9, "gap_max")] == [7.2, 17.9, 21.9, 25.6]
    assert all(v == 0.0 for v in _col(8, "gap_min") + _col(9, "gap_min"))


def test_bands_share_of_better_orders():
    assert [round(v, 2) for v in _col(8, "better_median")] == [0.12, 0.75, 0.88, 4.01]
    assert [round(v, 1) for v in _col(8, "better_max")] == [1.1, 37.6, 24.0, 67.1]
    assert [round(v, 2) for v in _col(9, "better_median")] == [0.03, 0.10, 0.34, 0.51]
    assert [round(v, 1) for v in _col(9, "better_max")] == [0.8, 22.0, 33.0, 73.5]


def test_bands_share_of_orders_that_hit_the_optimum_equals_the_formula():
    # Median über 20 Instanzen je Zelle: 48 optimale Reihenfolgen, also 3!·2^3 (drei Routen mit mindestens zwei Kunden), von n! Reihenfolgen
    assert [round(v, 3) for v in _col(8, "optimal_share_median")] == [0.119] * 4          # 48 / 40 320
    assert [round(v, 3) for v in _col(9, "optimal_share_median")] == [0.013] * 4          # 48 / 362 880


def test_bands_fill_until_full_on_the_shortest_tour():
    assert [round(v, 1) for v in _col(8, "fill_median")] == [5.5, 9.9, 6.2, 9.4]
    assert [round(v, 1) for v in _col(9, "fill_median")] == [2.5, 2.7, 5.9, 2.8]
    assert max(_col(8, "fill_max") + _col(9, "fill_max")) == pytest.approx(58.8, abs=0.05)
