"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rsp_scenario import Instance  # noqa: E402

S2, S8, S13, S18, S20, S29, S32, S37, S45, S53, S72, S74 = (math.sqrt(v) for v in (2, 8, 13, 18, 20, 29, 32, 37, 45, 53, 72, 74))


@pytest.fixture
def hand():
    """Das Handbeispiel (PLAN-01): Depot (0,0); Kunden 1 (6,-6), 2 (-2,5), 3 (-4,-4), 4 (0,-7), 5 (-1,-1), 6 (-6,3); Nachfragen 3, 2, 2, 4, 2, 1; Kapazität 7.

    Von Hand: Route (1, 4) = sqrt(72) + sqrt(37) + 7; Route (2, 6, 3, 5) = sqrt(29) + sqrt(20) + sqrt(53) + sqrt(18) + sqrt(2); beide Lasten 7.
    Das Optimum ist ihre Summe 44,3623; kürzeste Rundreise 5, 1, 4, 3, 6, 2 (oder rückwärts) mit Länge 38,2367."""
    return Instance(((0.0, 0.0), (6.0, -6.0), (-2.0, 5.0), (-4.0, -4.0), (0.0, -7.0), (-1.0, -1.0), (-6.0, 3.0)), (3, 2, 2, 4, 2, 1), 7)


OPTIMUM = S72 + S37 + 7 + S29 + S20 + S53 + S18 + S2     # 44,3623
TOUR_LENGTH = S29 + S20 + S53 + 5 + S37 + S74 + S2       # 38,2367
