"""Kern an der Handinstanz (PLAN-01): jede Zahl ist hier aus Wurzeln von Hand zusammengesetzt, nicht aus dem Code abgeschrieben."""

import math

import pytest

import rsp_algorithm as A
from conftest import OPTIMUM, S2, S18, S20, S29, S32, S37, S45, S53, S72, S74, TOUR_LENGTH

ORDER = (5, 1, 4, 3, 6, 2)   # die kürzeste Rundreise, in der Richtung des Handbeispiels


def test_optimum_and_its_routes(hand):
    ex = A.exact_cvrp(hand)
    assert ex.cost == pytest.approx(OPTIMUM)
    assert ex.routes == ((1, 4), (2, 6, 3, 5))
    assert A.is_feasible_plan(hand, ex.routes)


def test_route_lengths(hand):
    assert A.route_length(hand, (1, 4)) == pytest.approx(S72 + S37 + 7)
    assert A.route_length(hand, (2, 6, 3, 5)) == pytest.approx(S29 + S20 + S53 + S18 + S2)
    assert A.route_length(hand, ()) == 0.0
    assert A.route_length(hand, (5,)) == pytest.approx(2 * S2)


def test_shortest_tour_is_found_in_the_smaller_direction(hand):
    length, order = A.tsp_tour(hand)
    assert length == pytest.approx(TOUR_LENGTH)
    assert order == (2, 6, 3, 4, 1, 5)                       # Rückwärtsrichtung von ORDER, lexikographisch kleiner
    assert order[::-1] == ORDER


def test_split_of_the_tour_uses_three_routes(hand):
    result = A.split(hand, ORDER)
    assert result.routes == ((5,), (1, 4), (3, 6, 2))
    assert result.cost == pytest.approx(2 * S2 + (S72 + S37 + 7) + (S32 + S53 + S20 + S29))   # 47,19
    assert A.split(hand, ORDER[::-1]).cost == pytest.approx(result.cost)                   # die Leserichtung ändert den Split nicht


def test_fill_until_full_cuts_where_the_vehicle_is_full(hand):
    result = A.fill_until_full(hand, ORDER)                  # 5 + 1 = Last 5, dann passt die 4 nicht; 4 + 3 + 6 = Last 7; dann bleibt die 2
    assert result.routes == ((5, 1), (4, 3, 6), (2,))
    assert result.cost == pytest.approx((S2 + S74 + S72) + (7 + 5 + S53 + S45) + 2 * S29)  # 55,26


def test_arcs_of_the_hilfsgraph_for_the_tour_order(hand):
    arcs = {(a.start, a.end): a for a in A.split_arcs(hand, ORDER)}
    expected = {
        (0, 1): 2 * S2, (0, 2): S2 + S74 + S72, (1, 2): 2 * S72, (1, 3): S72 + S37 + 7,
        (2, 3): 14.0, (2, 4): 7 + 5 + S32, (2, 5): 7 + 5 + S53 + S45, (3, 4): 2 * S32,
        (3, 5): S32 + S53 + S45, (3, 6): S32 + S53 + S20 + S29, (4, 5): 2 * S45, (4, 6): S45 + S20 + S29, (5, 6): 2 * S29,
    }
    assert set(arcs) == set(expected)                        # genau 13 Bögen: alle übrigen Folgen von Kunden überschreiten die Kapazität 7
    for key, value in expected.items():
        assert arcs[key].cost == pytest.approx(value), key
    assert arcs[(2, 5)].load == 7 and arcs[(0, 2)].load == 5


def test_split_path_follows_the_routes(hand):
    result = A.split(hand, ORDER)
    path = A.split_path(hand, ORDER, result)
    assert [(a.start, a.end) for a in path] == [(0, 1), (1, 3), (3, 6)]
    assert sum(a.cost for a in path) == pytest.approx(result.cost)


def test_enumeration_counts_of_the_hand_instance(hand):
    costs = A.all_split_costs(hand)
    assert len(costs) == math.factorial(6)
    assert int((costs <= OPTIMUM + 1e-9).sum()) == 8 == A.reproducing_orders(A.exact_cvrp(hand).routes)   # 2! · 2^2
    assert int((costs < A.split(hand, ORDER).cost - 1e-9).sum()) == 16
    assert float(costs.min()) == pytest.approx(OPTIMUM)


def test_concatenating_the_optimal_routes_gives_the_optimum_back(hand):
    ex = A.exact_cvrp(hand)
    assert A.concatenate(ex.routes) == (1, 4, 2, 6, 3, 5)
    assert A.split(hand, A.concatenate(ex.routes)).cost == pytest.approx(ex.cost)


def test_reproducing_orders_counts_routes_and_directions():
    assert A.reproducing_orders(((1, 2), (3, 4))) == 8       # 2! · 2^2
    assert A.reproducing_orders(((1,), (2, 3), (4,))) == 12  # 3! · 2^1: eine Route mit einem Kunden hat keine zweite Richtung
    assert A.reproducing_orders(((1,),)) == 1


def test_orders_nearest_neighbour_and_sweep(hand):
    assert A.nearest_neighbour_order(hand) == (5, 3, 4, 1, 2, 6)
    # Winkel um das Depot: 2 ≈ 112°, 6 ≈ 153°, 3 und 5 genau 225° (Gleichstand: kleinere Nummer zuerst), 4 = 270°, 1 = 315°
    assert A.sweep_order(hand) == (2, 6, 3, 5, 4, 1)
    assert sorted(A.random_order(hand, 3)) == [1, 2, 3, 4, 5, 6]
    assert A.random_order(hand, 3) == A.random_order(hand, 3)
