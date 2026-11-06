"""Aufbau der App: Abschnitte, Diagramme, Verdikte; Reihenfolge-Arten, Band-Auswahl, Permalink und PDF (AppTest, DEMO-PLAYBOOK §5).

Expander werden per Titel gesucht, nie per Index (neue Expander verschieben sonst die Positionen)."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import rsp_constants as C
import rsp_evaluation as ev
from rsp_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SUBHEADERS = ["🔬 Der Hilfsgraph: der Split von Hand", "🔬 Split gegen „Füllen bis voll“", "🔬 Alle Riesentouren", "🔬 Von der Lösung zur Reihenfolge",
              "🔬 Wie oft ist die Rundreise gut?", "🚧 Wo die Annahmen enden"]


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _messages(at) -> int:
    return len(at.success) + len(at.info) + len(at.warning) + len(at.error)


def _texts(at) -> str:
    """Alle Verdikt-Texte der Seite (Erfolg, Info, Warnung) in einem String."""
    return " ".join(m.value for group in (at.success, at.info, at.warning) for m in group)


def test_sections_charts_and_verdicts_are_all_there():
    at = _app()
    assert [s.value for s in at.subheader] == SUBHEADERS
    assert len(at.get("plotly_chart")) == 7                    # vier Karten, Hilfsgraph, Histogramm, Bänder
    assert _messages(at) == 6                                  # Kernfrage, Hilfsgraph, Füllen bis voll, Alle Riesentouren, Lösung zur Reihenfolge, Bänder
    labels = [e.label for e in at.expander]
    for wanted in ("So funktioniert Riesentour und Split", "⚠️ Annahmen, Grenzen und bekannte Probleme", "📐 Mathematische Formulierung"):
        assert wanted in labels


def test_metrics_show_optimum_and_the_two_splits():
    at = _app()
    values = [m.value for m in at.metric]
    assert values == ["63,30", "68,38", "68,38"]               # Handbeispiel: Optimum, Split der Rundreise (gewählt), Split der Rundreise
    assert at.metric[1].delta == at.metric[2].delta == "+5,08 gegen Optimum"


@pytest.mark.parametrize("kind", range(len(C.ORDER_KINDS)))
def test_every_kind_of_order_runs_and_is_named_in_the_metric(kind):
    at = _app()
    at.sidebar.selectbox(key="order_select").set_value(kind).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert C.ORDER_KINDS[kind].lower() in at.metric[1].label
    assert _messages(at) == 6


def test_best_order_reaches_the_optimum_in_the_default_example():
    at = _app()
    at.sidebar.selectbox(key="order_select").set_value(4).run()
    assert at.metric[1].value == at.metric[0].value == "63,30"


def test_band_selection_switches_between_n8_and_n9():
    at = _app()
    assert "Bei n = 8" in _texts(at)
    at.radio(key="band_n").set_value(9).run()
    assert not at.exception
    assert "Bei n = 9" in _texts(at)


def test_smaller_instance_counts_fewer_orders():
    at = _app()
    at.sidebar.slider(key="n_slider").set_value(4).run()
    assert not at.exception
    assert "von 24 Reihenfolgen" in _texts(at)


def test_permalink_sets_the_controls_from_the_address():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["n"] = "5"
    at.query_params["seed"] = "3"
    at.query_params["routes"] = "3"
    at.run()
    assert not at.exception
    assert at.sidebar.slider(key="n_slider").value == 5 and at.sidebar.number_input(key="seed_input").value == 3 and at.sidebar.slider(key="routes_slider").value == 3


def test_pdf_export_has_a_pdf_header_and_names_the_numbers():
    s = ev.Settings()
    a = ev.analyse(s)
    data = build_pdf(s, a)
    assert data[:5] == b"%PDF-" and len(data) > 1500
