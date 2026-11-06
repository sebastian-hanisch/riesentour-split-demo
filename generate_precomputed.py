"""Erzeugt rsp_bands.json: die Bänder über die festen Instanzen BAND_SEEDS für n = 8 und n = 9 (vollständige Aufzählung aller Reihenfolgen).

n = 9 ist für die Seitenleiste zu langsam (362 880 Reihenfolgen je Instanz), deshalb liegen die Zahlen vorberechnet im Repo. tests/test_bands.py rechnet n = 8
vollständig und eine Stichprobe von n = 9 neu nach und vergleicht mit der Datei.

Aufruf: python generate_precomputed.py"""

import json
import time
from pathlib import Path

import rsp_constants as C
from rsp_evaluation import band_cell

if __name__ == "__main__":
    start = time.time()
    cells = []
    for n in C.BAND_SIZES:
        for family, depot in C.BAND_CELLS:
            cells.append(band_cell(n, family, depot))
            print(n, family, depot, f"{time.time() - start:.0f} s", flush=True)
    data = {"seeds": [C.BAND_SEEDS[0], C.BAND_SEEDS[-1]], "routes": C.BAND_ROUTES, "fill": C.FILL, "cells": cells}
    Path(__file__).with_name(C.BAND_FILE).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("geschrieben:", C.BAND_FILE)
