"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import rsp_constants as C
from rsp_evaluation import Analysis, Settings, de, gap_percent, num, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, a: Analysis) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Riesentour und Split"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Kunden, Karte: {C.FAMILIES[s.family]}, Depot: {C.DEPOTS[s.depot].lower()}, Zielroutenzahl {s.routes}, Seed {s.seed}. "
                            f"Kapazität {a.inst.capacity}, Gesamtnachfrage {sum(a.inst.demand)}. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    widths = (70, 30, 25, 55)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, ("Plan", "Kosten", "Routen", "Abstand zum Optimum")):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    rows = (
        ("Optimum (alle Tourenpläne)", a.exact.cost, len(a.exact.routes)),
        (f"Split: {C.ORDER_KINDS[s.order]}", a.chosen.cost, len(a.chosen.routes)),
        ("Füllen bis voll (dieselbe Reihenfolge)", a.fill.cost, len(a.fill.routes)),
        ("Split der kürzesten Rundreise", a.tour.cost, len(a.tour.routes)),
    )
    for name, cost, k in rows:
        for w, v in zip(widths, (name, de(cost), str(k), pct(gap_percent(cost, a.exact.cost)))):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.5, _s(f"Reihenfolge: {' '.join(str(c) for c in a.order)}. Routen des Splits: "
                              + "; ".join("(" + " ".join(str(c) for c in r) + ")" for r in a.chosen.routes)
                              + f". Reihenfolgen insgesamt: {num(a.n_orders)}, davon {num(a.n_opt)} mit optimalem Split."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Der Split zerlegt eine Reihenfolge per kürzestem Weg im Hilfsgraphen optimal in Routen. Quelle: riesentour-split-demo, Sebastian Hanisch."),
                   new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
