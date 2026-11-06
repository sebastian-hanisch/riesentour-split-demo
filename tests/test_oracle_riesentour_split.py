"""Orakel-Tests riesentour-split-demo: Kernroutinen gegen unabhängige Rechenwege (ORACLE-PLAYBOOK §2, DEMO-PLAYBOOK §12).

- Split: Aufzählung aller 2^(n-1) Schnittmengen der Reihenfolge in reinem Python (math.hypot, keine numpy-Matrix) gegen den Hilfsgraphen.
- Exakter Löser: Aufzählung aller Zerlegungen der Kundenmenge und aller Reihenfolgen je Route (itertools) gegen die Teilmengen-Dynamik.
- Kürzeste Rundreise: Aufzählung aller Permutationen gegen Held-Karp.
- Vektorisierter Split (numpy) gegen den Einzel-Split.
Mini-Instanzen mit festen Seeds (range), insgesamt wenige Sekunden."""

import itertools
import math

import numpy as np
import pytest

import rsp_algorithm as A
from rsp_scenario import make_instance


def _dist(inst, a, b):
    (xa, ya), (xb, yb) = inst.xy[a], inst.xy[b]
    return math.hypot(xa - xb, ya - yb)


def _route(inst, customers):
    path = (0, *customers, 0)
    return sum(_dist(inst, u, v) for u, v in zip(path, path[1:]))


def _split_by_cuts(inst, order):
    """Alle Schnittmengen: zwischen je zwei aufeinanderfolgenden Kunden schneiden oder nicht."""
    best = math.inf
    n = len(order)
    for mask in range(1 << (n - 1)):
        routes, current = [], [order[0]]
        for t in range(1, n):
            if (mask >> (t - 1)) & 1:
                routes.append(current)
                current = []
            current.append(order[t])
        routes.append(current)
        if all(sum(inst.demand[c - 1] for c in r) <= inst.capacity for r in routes):
            best = min(best, sum(_route(inst, r) for r in routes))
    return best


def _exact(inst):
    cust = list(range(1, inst.n + 1))
    best_route = {}

    def route_best(group):
        if group not in best_route:
            best_route[group] = min(_route(inst, p) for p in itertools.permutations(group))
        return best_route[group]

    def partitions(rest):
        if not rest:
            yield []
            return
        first, others = rest[0], rest[1:]
        for k in range(len(others) + 1):
            for comb in itertools.combinations(others, k):
                group = (first, *comb)
                if sum(inst.demand[c - 1] for c in group) <= inst.capacity:
                    for tail in partitions(tuple(c for c in others if c not in comb)):
                        yield [group, *tail]

    return min(sum(route_best(g) for g in part) for part in partitions(tuple(cust)))


FAMILIES = [(0, 0, 2), (0, 1, 3), (1, 0, 2), (1, 1, 3), (2, 0, 3), (2, 1, 2)]


@pytest.mark.parametrize("family,depot,routes", FAMILIES)
def test_split_matches_the_enumeration_of_all_cuts(family, depot, routes):
    for seed in range(12):
        inst = make_instance(7, family, depot, routes, seed)
        rng = np.random.default_rng(seed)
        for _ in range(4):
            order = tuple(int(c) + 1 for c in rng.permutation(7))
            assert A.split(inst, order).cost == pytest.approx(_split_by_cuts(inst, order)), (seed, order)


@pytest.mark.parametrize("family,depot,routes", FAMILIES)
def test_exact_solver_matches_the_enumeration_of_all_plans(family, depot, routes):
    for seed in range(8):
        inst = make_instance(6, family, depot, routes, seed)
        ex = A.exact_cvrp(inst)
        assert ex.cost == pytest.approx(_exact(inst)), seed
        assert A.is_feasible_plan(inst, ex.routes), seed
        assert A.plan_length(inst, ex.routes) == pytest.approx(ex.cost), seed


@pytest.mark.parametrize("family,depot,routes", FAMILIES)
def test_shortest_tour_matches_the_enumeration_of_all_orders(family, depot, routes):
    for seed in range(8):
        inst = make_instance(7, family, depot, routes, seed)
        length, order = A.tsp_tour(inst)
        assert length == pytest.approx(min(_route(inst, p) for p in itertools.permutations(range(1, 8)))), seed
        assert _route(inst, order) == pytest.approx(length), seed


@pytest.mark.parametrize("family,depot,routes", FAMILIES)
def test_vectorised_split_matches_the_single_split(family, depot, routes):
    for seed in range(10):
        inst = make_instance(6, family, depot, routes, seed)
        perms = np.array(list(itertools.permutations(range(1, 7))))[::37]
        vec = A.split_all(inst, perms)
        assert vec == pytest.approx([A.split(inst, tuple(int(c) for c in p)).cost for p in perms]), seed


def test_dominance_the_minimum_over_all_orders_is_the_optimum():
    """Der tragende Satz: min über alle Reihenfolgen von Split = exaktes Optimum (unabhängig berechnet)."""
    for family, depot, routes in FAMILIES:
        for seed in range(10):
            inst = make_instance(6, family, depot, routes, seed)
            assert float(A.all_split_costs(inst).min()) == pytest.approx(_exact(inst)), (family, depot, seed)


def test_the_number_of_optimal_orders_is_the_formula_when_the_optimum_is_unique():
    """Zählung k!·2^j: wo kein Gleichstand zweier Lösungen vorliegt (Zahl der Treffer gleich Formel), muss die Formel exakt stimmen; sie ist nie größer als die Zahl."""
    unique = 0
    for family, depot, routes in FAMILIES:
        for seed in range(25):
            inst = make_instance(6, family, depot, routes, seed)
            ex = A.exact_cvrp(inst)
            hits = int((A.all_split_costs(inst) <= ex.cost + 1e-9).sum())
            formula = A.reproducing_orders(ex.routes)
            assert hits >= formula, (family, depot, seed)
            unique += hits == formula
    assert unique == 148                                      # gemessen: 148 von 150 Instanzen (n = 6, sechs Zellen, Seeds 0 bis 24) haben ein eindeutiges Optimum
