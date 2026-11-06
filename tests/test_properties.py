"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für JEDE Instanz gelten müssen, auf festen Zufallsinstanzen und am Handbeispiel.

Verhält sich der Kern bei Verschieben, Skalieren, Umnummerieren und Erhöhen der Kapazität wie die Theorie es verlangt?"""

import dataclasses
import itertools
import math

import numpy as np
import pytest

import rsp_algorithm as A
from rsp_scenario import Instance, make_instance

CASES = [(f, d, r, s) for f in (0, 1, 2) for d in (0, 1) for r in (2, 3) for s in range(3)]


def _inst(f, d, r, s, n=6):
    return make_instance(n, f, d, r, s)


@pytest.mark.parametrize("f,d,r,s", CASES)
def test_split_is_never_worse_than_filling_until_full(f, d, r, s):
    inst = _inst(f, d, r, s)
    rng = np.random.default_rng(s)
    for _ in range(5):
        order = tuple(int(c) + 1 for c in rng.permutation(inst.n))
        assert A.split(inst, order).cost <= A.fill_until_full(inst, order).cost + 1e-9


@pytest.mark.parametrize("f,d,r,s", CASES)
def test_every_split_is_a_feasible_plan_and_never_below_the_optimum(f, d, r, s):
    inst = _inst(f, d, r, s)
    opt = A.exact_cvrp(inst).cost
    rng = np.random.default_rng(s + 7)
    for _ in range(5):
        order = tuple(int(c) + 1 for c in rng.permutation(inst.n))
        result = A.split(inst, order)
        assert A.is_feasible_plan(inst, result.routes)
        assert A.concatenate(result.routes) == order           # die Routen sind aufeinanderfolgende Stücke der Reihenfolge
        assert result.cost >= opt - 1e-9
        assert A.plan_length(inst, result.routes) == pytest.approx(result.cost)


@pytest.mark.parametrize("f,d,r,s", CASES)
def test_reversing_the_order_does_not_change_the_split(f, d, r, s):
    inst = _inst(f, d, r, s)
    order = A.random_order(inst, s)
    assert A.split(inst, order[::-1]).cost == pytest.approx(A.split(inst, order).cost)


@pytest.mark.parametrize("f,d,r,s", CASES[::3])
def test_scaling_all_coordinates_scales_all_costs(f, d, r, s):
    inst = _inst(f, d, r, s)
    big = dataclasses.replace(inst, xy=tuple((3.0 * x, 3.0 * y) for x, y in inst.xy))
    assert A.exact_cvrp(big).cost == pytest.approx(3.0 * A.exact_cvrp(inst).cost)
    assert A.tsp_tour(big)[0] == pytest.approx(3.0 * A.tsp_tour(inst)[0])
    assert A.exact_cvrp(big).routes == A.exact_cvrp(inst).routes


@pytest.mark.parametrize("f,d,r,s", CASES[::3])
def test_shifting_all_points_changes_nothing(f, d, r, s):
    inst = _inst(f, d, r, s)
    moved = dataclasses.replace(inst, xy=tuple((x + 5.5, y - 2.0) for x, y in inst.xy))
    assert A.exact_cvrp(moved).cost == pytest.approx(A.exact_cvrp(inst).cost)


@pytest.mark.parametrize("f,d,r,s", CASES[::3])
def test_renumbering_the_customers_keeps_the_optimum(f, d, r, s):
    inst = _inst(f, d, r, s)
    perm = list(np.random.default_rng(s + 1).permutation(inst.n))             # neuer Kunde t ist alter Kunde perm[t - 1] + 1
    renamed = Instance((inst.xy[0],) + tuple(inst.xy[p + 1] for p in perm), tuple(inst.demand[p] for p in perm), inst.capacity)
    assert A.exact_cvrp(renamed).cost == pytest.approx(A.exact_cvrp(inst).cost)
    assert A.tsp_tour(renamed)[0] == pytest.approx(A.tsp_tour(inst)[0])


@pytest.mark.parametrize("f,d,r,s", CASES[::2])
def test_more_capacity_never_raises_the_optimum_or_the_split(f, d, r, s):
    inst = _inst(f, d, r, s)
    roomy = dataclasses.replace(inst, capacity=inst.capacity + 3)
    assert A.exact_cvrp(roomy).cost <= A.exact_cvrp(inst).cost + 1e-9
    order = A.random_order(inst, s)
    assert A.split(roomy, order).cost <= A.split(inst, order).cost + 1e-9


@pytest.mark.parametrize("f,d,r,s", CASES[::3])
def test_the_shortest_tour_is_a_lower_bound_for_one_vehicle_and_split_of_it_is_an_upper_bound(f, d, r, s):
    inst = _inst(f, d, r, s)
    length, order = A.tsp_tour(inst)
    opt = A.exact_cvrp(inst).cost
    assert length <= opt + 1e-9                               # mit Dreiecksungleichung: eine Rundreise durch alle ist nie länger als jeder Plan mit Kapazitätsgrenzen
    assert A.split(inst, order).cost >= opt - 1e-9


def test_unlimited_capacity_makes_the_split_the_tour_itself(hand):
    roomy = dataclasses.replace(hand, capacity=sum(hand.demand))
    length, order = A.tsp_tour(roomy)
    result = A.split(roomy, order)
    assert result.routes == (order,)
    assert result.cost == pytest.approx(length)
    assert A.exact_cvrp(roomy).cost == pytest.approx(length)


def test_capacity_equal_to_every_demand_gives_one_route_per_customer():
    inst = Instance(((0.0, 0.0), (3.0, 4.0), (-6.0, 8.0), (0.0, -2.0)), (5, 5, 5), 5)
    assert A.exact_cvrp(inst).cost == pytest.approx(2 * (5 + 10 + 2))
    assert A.split(inst, (2, 1, 3)).routes == ((2,), (1,), (3,))
    costs = A.all_split_costs(inst)
    assert len(costs) == 6 and np.allclose(costs, 34.0)                      # jede der 3! Reihenfolgen ergibt dasselbe: Einzelfahrten


def test_split_all_blocks_cover_all_orders_exactly_once():
    inst = _inst(1, 0, 2, 5, n=5)
    costs = A.all_split_costs(inst)
    assert len(costs) == math.factorial(5)
    perms = np.array(list(itertools.permutations(range(1, 6))))
    assert sorted(costs) == pytest.approx(sorted(A.split_all(inst, perms)))
