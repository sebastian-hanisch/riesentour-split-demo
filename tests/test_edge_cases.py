"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1 und n = 2, Kunde auf dem Depot, Kunden am selben Ort,
Nachfrage gleich Kapazität, ein einziger Kunde je Route, Gleichstände, Reglergrenzen."""

import dataclasses

import numpy as np
import pytest

import rsp_algorithm as A
import rsp_constants as C
import rsp_evaluation as ev
from rsp_scenario import Instance, make_instance


def test_one_customer():
    inst = Instance(((0.0, 0.0), (3.0, 4.0)), (2,), 2)
    assert A.exact_cvrp(inst).cost == pytest.approx(10.0)
    assert A.exact_cvrp(inst).routes == ((1,),)
    assert A.tsp_tour(inst) == (pytest.approx(10.0), (1,))
    assert A.split(inst, (1,)).routes == ((1,),)
    assert A.all_split_costs(inst).tolist() == [pytest.approx(10.0)]
    assert A.reproducing_orders(((1,),)) == 1


def test_exactly_two_customers_one_or_two_routes():
    together = Instance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0)), (1, 1), 2)       # Last 2 passt: eine Route 5 + 5 + 10
    assert A.exact_cvrp(together).routes == ((1, 2),) and A.exact_cvrp(together).cost == pytest.approx(20.0)
    apart = dataclasses.replace(together, capacity=1)                          # Last 2 passt nicht: zwei Fahrten 10 + 20
    assert A.exact_cvrp(apart).routes == ((1,), (2,)) and A.exact_cvrp(apart).cost == pytest.approx(30.0)
    assert A.split(apart, (2, 1)).routes == ((2,), (1,))


def test_customer_on_the_depot_costs_nothing_extra():
    inst = Instance(((0.0, 0.0), (0.0, 0.0), (3.0, 4.0)), (1, 1), 2)
    assert A.exact_cvrp(inst).cost == pytest.approx(10.0)
    assert A.tsp_tour(inst)[0] == pytest.approx(10.0)
    assert float(A.all_split_costs(inst).min()) == pytest.approx(10.0)


def test_a_customer_on_the_depot_that_fits_into_several_routes_gives_more_optimal_orders_than_the_formula():
    inst = make_instance(6, 0, 0, 2, 1)                                        # Kunde 1 liegt auf dem Depot (8, 8): er kostet in jeder Route nichts
    assert inst.xy[1] == inst.xy[0]
    ex = A.exact_cvrp(inst)
    hits = int((A.all_split_costs(inst) <= ex.cost + 1e-9).sum())
    assert (hits, A.reproducing_orders(ex.routes)) == (24, 8)                  # drei gleich gute Lösungen statt einer


def test_demand_equal_to_capacity_forces_a_route_of_its_own():
    inst = Instance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0), (-3.0, 4.0)), (4, 1, 1), 4)
    ex = A.exact_cvrp(inst)
    assert (1,) in ex.routes
    assert A.is_feasible_plan(inst, ex.routes)


def test_infeasible_plans_are_rejected_by_the_checker(hand):
    assert not A.is_feasible_plan(hand, ((1, 4, 2), (6, 3, 5)))                # Last 9 von 7
    assert not A.is_feasible_plan(hand, ((1, 4), (2, 6, 3)))                   # Kunde 5 fehlt
    assert not A.is_feasible_plan(hand, ((1, 4), (2, 6, 3, 5), (5,)))          # Kunde 5 doppelt
    assert A.is_feasible_plan(hand, ((1, 4), (2, 6, 3, 5)))


def test_ties_between_equal_splits_choose_the_longer_last_route():
    """Gleichstandsregel des Splits: gewinnt die Zerlegung mit dem kleinsten Startknoten des letzten Bogens."""
    inst = Instance(((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)), (1, 1, 1), 3)    # alle auf einer Geraden: eine Route kostet 6, drei Einzelfahrten kosten 12
    assert A.split(inst, (1, 2, 3)).routes == ((1, 2, 3),)
    flat = Instance(((0.0, 0.0), (1.0, 0.0), (-1.0, 0.0)), (1, 1), 2)                  # zusammen 4, einzeln 2 + 2 = 4: Gleichstand
    assert A.split(flat, (1, 2)).routes == ((1, 2),)


def test_fill_until_full_with_a_single_oversized_start_never_creates_an_empty_route(hand):
    result = A.fill_until_full(hand, (4, 1, 2, 6, 3, 5))
    assert all(result.routes)
    assert A.concatenate(result.routes) == (4, 1, 2, 6, 3, 5)


def test_generator_is_deterministic_and_respects_capacity_and_bounds():
    for family in range(len(C.FAMILIES)):
        for depot in range(2):
            a = make_instance(8, family, depot, 4, 123)
            assert a == make_instance(8, family, depot, 4, 123)
            assert a != make_instance(8, family, depot, 4, 124)
            assert a.capacity >= max(a.demand)
            assert a.min_routes >= 1 and a.n == 8
            xs = [p[0] for p in a.xy[1:]]
            assert 0 <= min(xs) and max(xs) <= (16 if family == 0 else 100)


def test_sliders_at_their_limits_give_valid_analyses():
    for n in (C.N_MIN, C.N_MAX):
        for routes in (C.ROUTES_MIN, C.ROUTES_MAX):
            for order in range(len(C.ORDER_KINDS)):
                a = ev.analyse(ev.Settings(n, 2, 1, routes, C.SEED_MAX, order))
                assert a.n_orders == np.prod(range(1, n + 1))
                assert a.chosen.cost >= a.exact.cost - 1e-9
                assert a.n_opt >= a.formula >= 1


def test_gap_and_share_helpers_at_their_edges():
    assert ev.gap_percent(10.0, 0.0) == 0.0                                    # keine Referenzkosten
    assert ev.gap_percent(5.0 + 1e-12, 5.0) == 0.0                             # unter der Toleranz kein Abstand, auch kein negatives Null
    assert ev.gap_percent(11.0, 10.0) == pytest.approx(10.0)
    assert ev.share_percent(0, 0) == 0.0 and ev.share_percent(1, 4) == 25.0
    assert ev.num(40320) == "40 320" and ev.de(3.14159) == "3,14"
    assert ev.pct(4.26) == "4,3 %" and ev.pct(4.24) == "4,2 %"
