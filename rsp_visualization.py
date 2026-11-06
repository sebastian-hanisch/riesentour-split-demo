"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import numpy as np
import plotly.graph_objects as go

import rsp_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, routes, title_prefix="Route"):
    """Karte: Depot als Quadrat, Kunden als Kreise (Größe = Nachfrage, Beschriftung = Kundennummer), jede Route als Linie in eigener Farbe.
    Gleicher Maßstab in x und y über scaleanchor mit autorange; der Rand kommt von zwei unsichtbaren Eckmarken (DEMO-PLAYBOOK §3)."""
    xs = [p[0] for p in inst.xy]
    ys = [p[1] for p in inst.xy]
    pad = 0.08 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    for r, route in enumerate(routes):
        pts = [inst.xy[0]] + [inst.xy[c] for c in route] + [inst.xy[0]]
        color = C.ROUTE_COLORS[r % len(C.ROUTE_COLORS)]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color=color, width=3),
                                 name=f"{title_prefix} {r + 1} (Last {inst.load(route)} von {inst.capacity})", hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=[inst.xy[c][0] for c in range(1, inst.n + 1)], y=[inst.xy[c][1] for c in range(1, inst.n + 1)], mode="markers+text",
        text=[str(c) for c in range(1, inst.n + 1)], textposition="top center",
        marker=dict(size=[9 + 2.5 * d for d in inst.demand], color="rgba(150,150,150,0.55)", line=dict(color="#555", width=1)),
        customdata=[[inst.demand[c - 1]] for c in range(1, inst.n + 1)], hovertemplate="Kunde %{text}: Nachfrage %{customdata[0]}<extra></extra>",
        name="Kunden (Größe = Nachfrage)"))
    fig.add_trace(go.Scatter(x=[inst.xy[0][0]], y=[inst.xy[0][1]], mode="markers", marker=dict(symbol="square", size=15, color="#222"), name="Depot", hoverinfo="skip"))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, 420)


def _arc(i, j, height, steps=24):
    xs = [i + (j - i) * t / steps for t in range(steps + 1)]
    ys = [height * math.sin(math.pi * t / steps) for t in range(steps + 1)]
    return xs, ys


def build_aux_graph(order, arcs, path):
    """Hilfsgraph: Knoten 0 bis n auf einer Linie (Knoten i: die ersten i Kunden sind bedient), jeder Bogen eine Wölbung. Der kürzeste Weg ist dick und farbig;
    die Kosten stehen an den Bögen des Weges, alle anderen Bögen zeigen sie beim Überfahren."""
    n = len(order)
    on_path = {(a.start, a.end) for a in path}
    fig = go.Figure()
    top = 1.0
    for a in arcs:
        if (a.start, a.end) in on_path:
            continue
        h = 0.22 * (a.end - a.start) + 0.15
        top = max(top, h)
        xs, ys = _arc(a.start, a.end, h)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="rgba(150,150,150,0.6)", width=1.5), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=[(a.start + a.end) / 2], y=[h], mode="markers", marker=dict(size=8, color="rgba(150,150,150,0.01)"), showlegend=False,
                                 hovertemplate=f"Kunden {' '.join(str(c) for c in a.customers)}<br>Last {a.load}, Kosten {a.cost:.2f}<extra></extra>"))
    for a in path:
        h = 0.22 * (a.end - a.start) + 0.15
        top = max(top, h)
        xs, ys = _arc(a.start, a.end, h)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_PATH, width=4), hoverinfo="skip", showlegend=False))
        fig.add_annotation(x=(a.start + a.end) / 2, y=h, text=f"{a.cost:.2f}", showarrow=False, yshift=11, bgcolor="rgba(255,255,255,0.88)", font=dict(color="#222", size=12))
    labels = ["Start"] + [f"nach {c}" for c in order]
    fig.add_trace(go.Scatter(x=list(range(n + 1)), y=[0] * (n + 1), mode="markers", marker=dict(size=11, color="#222"), showlegend=False,
                             hovertemplate="Knoten %{x}<extra></extra>"))
    fig.update_xaxes(tickmode="array", tickvals=list(range(n + 1)), ticktext=labels, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-0.35, top + 0.45], showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, 360)


def build_histogram(costs, optimum, tour_cost, chosen_cost):
    """Verteilung der Split-Kosten über ALLE Reihenfolgen mit Marken für Optimum, kürzeste Rundreise und gewählte Reihenfolge."""
    fig = go.Figure(go.Histogram(x=np.asarray(costs), nbinsx=60, marker_color=C.COLOR_OTHER, hovertemplate="Kosten %{x}: %{y} Reihenfolgen<extra></extra>", name="alle Reihenfolgen"))
    marks = [(optimum, C.COLOR_OPT, "Optimum"), (tour_cost, C.COLOR_TSP, "kürzeste Rundreise"), (chosen_cost, C.COLOR_ORDER, "gewählte Reihenfolge")]
    for k, (x, color, name) in enumerate(marks):
        fig.add_vline(x=x, line=dict(color=color, width=3, dash="dash" if k == 2 else "solid"))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=color, width=3, dash="dash" if k == 2 else "solid"), name=f"{name}: {x:.2f}"))
    fig.update_xaxes(title_text="Kosten nach dem Split")
    fig.update_yaxes(title_text="Zahl der Reihenfolgen")
    return _base(fig)


def build_bands(rows):
    """Median des Abstands der Rundreise zum Optimum je Zelle, mit Spanne (Minimum bis Maximum) als Fehlerbalken."""
    labels = [f"{'In der Mitte' if r['depot'] == 0 else 'In der Ecke'}, {'zufällig' if r['family'] == 1 else 'Gruppen'}" for r in rows]
    fig = go.Figure(go.Bar(
        x=labels, y=[r["gap_median"] for r in rows], marker_color=C.COLOR_TSP,
        error_y=dict(type="data", symmetric=False, array=[r["gap_max"] - r["gap_median"] for r in rows], arrayminus=[r["gap_median"] - r["gap_min"] for r in rows]),
        hovertemplate="%{x}: Median %{y:.1f} %<extra></extra>", name="Median (Balken: Minimum bis Maximum)"))
    fig.update_yaxes(title_text="Abstand zum Optimum (%)", rangemode="tozero")
    return _base(fig, 340)
