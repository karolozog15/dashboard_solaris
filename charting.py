"""Budowa figury plotly oraz fragment Streamlit odpowiedzialny za wykres."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import AXIS_GAP, MAX_DOMAIN_START
from state import handle_zoom_box_select


def _build_figure(all_series, start_time, end_time, show_minmax, all_axes_left):
    num_series = len(all_series)

    if all_axes_left:
        extra_left = max(0, num_series - 1)
    else:
        extra_left = max(0, num_series - 2)
    domain_start = min(extra_left * AXIS_GAP, MAX_DOMAIN_START)

    fig = go.Figure()
    layout_axes = {}
    extra_used = 0

    for i, s in enumerate(all_series):
        d = s["df"]
        if d.empty:
            continue

        color = s["color"]
        label = s["label"]

        if i == 0:
            yaxis_ref = "y"
            axis_key = "yaxis"
            axis_conf = dict(
                title=dict(text=label, font=dict(color=color), standoff=5),
                tickfont=dict(color=color),
                side="left",
                showgrid=True,
                gridcolor="rgba(255,255,255,0.08)",
            )
        elif i == 1 and not all_axes_left:
            yaxis_ref = "y2"
            axis_key = "yaxis2"
            axis_conf = dict(
                title=dict(text=label, font=dict(color=color), standoff=5),
                tickfont=dict(color=color),
                side="right",
                overlaying="y",
                showgrid=False,
            )
        else:
            extra_used += 1
            yaxis_ref = f"y{i + 1}"
            axis_key = f"yaxis{i + 1}"
            position = max(0.0, domain_start - AXIS_GAP * extra_used)
            axis_conf = dict(
                title=dict(text=label, font=dict(color=color), standoff=5),
                tickfont=dict(color=color),
                side="left",
                overlaying="y",
                anchor="free",
                position=position,
                showgrid=False,
            )

        layout_axes[axis_key] = axis_conf

        if show_minmax:
            fig.add_trace(go.Scattergl(
                x=d["time"], y=d["VALUE_MIN"], mode="lines", name=f"MIN — {label}",
                line=dict(color=color, width=1, dash="dot"), opacity=0.4,
                yaxis=yaxis_ref, showlegend=False,
                hovertemplate="<b>Czas:</b> %{x}<br><b>MIN:</b> %{y:.6f}<extra></extra>",
            ))
            fig.add_trace(go.Scattergl(
                x=d["time"], y=d["VALUE_MAX"], mode="lines", name=f"MAX — {label}",
                line=dict(color=color, width=1, dash="dot"), opacity=0.4,
                yaxis=yaxis_ref, showlegend=False,
                hovertemplate="<b>Czas:</b> %{x}<br><b>MAX:</b> %{y:.6f}<extra></extra>",
            ))

        fig.add_trace(go.Scattergl(
            x=d["time"], y=d["VALUE_AVG"], mode="lines+markers", name=f"AVG — {label}",
            line=dict(color=color, width=2), marker=dict(size=4, color=color),
            yaxis=yaxis_ref,
            hovertemplate="<b>Czas:</b> %{x}<br><b>AVG:</b> %{y:.6f}<extra></extra>",
        ))

    x_range = [start_time.replace(tzinfo=None), end_time.replace(tzinfo=None)]

    fig.update_layout(
        **layout_axes,
        height=700,
        template="plotly_dark",
        hovermode="closest",
        uirevision="main-chart",
        dragmode="select" if st.session_state.get("auto_zoom_enabled") else "zoom",
        legend=dict(orientation="h", y=-0.15),
        xaxis=dict(
            title="Czas",
            domain=[domain_start, 1],
            range=x_range,
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
        ),
        margin=dict(l=60, r=60, t=30, b=40),
    )

    return fig, domain_start


def _render_summary_table(all_series):
    summary_rows = []
    for s in all_series:
        d = s["df"]
        if d.empty:
            summary_rows.append({
                "Seria": s["label"], "Tabela": f"{s['schema']}.{s['table']}",
                "Aktualna AVG": None, "Średnia AVG": None, "MIN": None, "MAX": None,
            })
        else:
            summary_rows.append({
                "Seria": s["label"],
                "Tabela": f"{s['schema']}.{s['table']}",
                "Aktualna AVG": round(float(d["VALUE_AVG"].iloc[-1]), 3),
                "Średnia AVG": round(float(d["VALUE_AVG"].mean()), 3),
                "MIN": round(float(d["VALUE_MIN"].min()), 3),
                "MAX": round(float(d["VALUE_MAX"].max()), 3),
            })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


def make_chart_fragment(refresh_seconds):
    """Zwraca funkcję-fragment z aktualnym interwałem odświeżania.

    st.fragment(run_every=...) wymaga podania wartości w momencie dekoracji,
    dlatego fragment budujemy na nowo przy każdym uruchomieniu app.py —
    analogicznie do lokalnej definicji funkcji w oryginalnym skrypcie.
    """

    @st.fragment(run_every=refresh_seconds)
    def _render_chart_fragment(all_series, start_time, end_time):
        _render_chart_body(all_series, start_time, end_time)

    return _render_chart_fragment


def _render_chart_body(all_series, start_time, end_time):
    """Treść fragmentu wykresu — wydzielona z dekoratora, żeby nie duplikować kodu."""
    st.subheader("📈 Wartość w czasie")

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        show_minmax = st.checkbox(
            "Pokaż zakres MIN/MAX",
            value=(len(all_series) <= 2),
            key="show_minmax",
        )
    with col_opt2:
        all_axes_left = st.checkbox(
            "Wszystkie osie po lewej",
            value=False,
            key="all_axes_left",
            help="Jeśli wyłączone: 1. seria po lewej, 2. po prawej, kolejne po lewej. "
                 "Jeśli włączone: wszystkie osie (od 2. serii) po lewej stronie.",
        )

    _render_summary_table(all_series)

    auto_zoom_enabled = st.session_state.get("auto_zoom_enabled", False)
    fig, _ = _build_figure(all_series, start_time, end_time, show_minmax, all_axes_left)

    chart_config = {"doubleClick": "reset+autosize", "displaylogo": False}

    if auto_zoom_enabled:
        st.caption(
            "🔍 Tryb automatycznego zoomu: przeciągnij myszką po wykresie, aby "
            "zaznaczyć fragment — dane zostaną pobrane na nowo dla wybranego okresu."
        )
        chart_event = st.plotly_chart(
            fig,
            use_container_width=True,
            config=chart_config,
            on_select="rerun",
            selection_mode="box",
            key=f"main_chart_{st.session_state.chart_key_version}",
        )

        box_selections = []
        if chart_event and chart_event.selection:
            box_selections = chart_event.selection.get("box") or []

        if box_selections:
            box_x_raw = box_selections[0].get("x") or []
            box_x = [pd.to_datetime(v).to_pydatetime() for v in box_x_raw]
            if handle_zoom_box_select(box_x):
                st.rerun(scope="app")
    else:
        st.plotly_chart(fig, use_container_width=True, config=chart_config)

    num_series = len(all_series)
    if num_series > 1:
        if all_axes_left:
            st.caption("Wszystkie serie mają własną, opisaną oś po lewej stronie wykresu.")
        elif num_series > 2:
            st.caption(
                "1. seria → oś po lewej, 2. seria → oś po prawej, "
                "kolejne serie → dodatkowe osie doklejane po lewej stronie."
            )
