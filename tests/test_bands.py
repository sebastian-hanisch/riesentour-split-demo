"""Die vorberechneten Bänder (rsp_bands.json) gegen eine frische Rechnung: n = 8 vollständig, von n = 9 eine Zelle (Gruppen, Depot in der Ecke, die mit dem größten Ausreißer)."""

import json
from pathlib import Path

import pytest

import rsp_constants as C
import rsp_evaluation as ev

STORED = json.loads((Path(__file__).resolve().parent.parent / C.BAND_FILE).read_text(encoding="utf-8"))
KEYS = ("dominance", "tour_optimal", "gap_min", "gap_median", "gap_max", "better_min", "better_median", "better_max", "fill_median", "fill_max", "optimal_share_median")


def _stored(n, family, depot):
    return next(c for c in STORED["cells"] if (c["n"], c["family"], c["depot"]) == (n, family, depot))


def _same(fresh, stored):
    for key in KEYS:
        assert fresh[key] == pytest.approx(stored[key], abs=1e-9), key


@pytest.mark.parametrize("family,depot", C.BAND_CELLS)
def test_n8_cells_match_a_fresh_computation(family, depot):
    _same(ev.band_cell(8, family, depot), _stored(8, family, depot))


def test_n9_sample_cell_matches_a_fresh_computation():
    _same(ev.band_cell(9, 2, 1), _stored(9, 2, 1))


def test_file_describes_its_inputs_and_has_all_cells():
    assert STORED["seeds"] == [C.BAND_SEEDS[0], C.BAND_SEEDS[-1]] and STORED["routes"] == C.BAND_ROUTES and STORED["fill"] == C.FILL
    assert {(c["n"], c["family"], c["depot"]) for c in STORED["cells"]} == {(n, f, d) for n in C.BAND_SIZES for f, d in C.BAND_CELLS}
    assert all(c["count"] == len(C.BAND_SEEDS) for c in STORED["cells"])


def test_band_rows_are_sorted_like_the_cells_and_empty_for_other_sizes():
    assert [(r["family"], r["depot"]) for r in ev.band_rows(8)] == list(C.BAND_CELLS)
    assert ev.band_rows(7) == []
