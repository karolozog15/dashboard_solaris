"""Budowa figury Plotly oraz renderowanie wykresu"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import AXIS_GAP, MAX_DOMAIN_START
from state import handle_zoom_box_select

# Klucze widgetów i stanów
def _widget_key(chart_key, name):
    """Tworzy unikalny klucz dla konkretnego wykresu."""
    return f"{chart_key}_{name}"


def _chart_keys(chart_key):
    """Zwraca słownik wszystkich kluczy session_state/widgetów dla wykresu."""
    names = [
        "show_minmax",
        "all_axes_left",
        "markers_enabled",
        "marker_1",
        "marker_2",
        "last_marker_signature",
        "chart",
        "reset_markers",
    ]
    return {name: _widget_key(chart_key, name) for name in names}


# Czas i wartości
def _to_naive_timestamp(value):
    """Konwertuje wartość na pandas.Timestamp bez strefy czasowej."""
    if value is None:
        return None

    value = pd.to_datetime(value, errors="coerce")

    if pd.isna(value):
        return None

    if getattr(value, "tzinfo", None) is not None:
        value = value.tz_localize(None)

    return value


def _to_python_datetime(value):
    value = _to_naive_timestamp(value)
    return value.to_pydatetime() if value is not None else None


def _format_dt(value):
    value = _to_naive_timestamp(value)

    if value is None:
        return "—"

    return value.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _interpolate_value(df, x):
    """Zwraca interpolowaną wartość VALUE_AVG dla czasu X."""
    if df is None or df.empty or x is None:
        return None

    if not {"time", "VALUE_AVG"}.issubset(df.columns):
        return None

    temp = pd.DataFrame(
        {
            "time": pd.to_datetime(df["time"], errors="coerce"),
            "value": pd.to_numeric(df["VALUE_AVG"], errors="coerce"),
        }
    ).dropna()

    if temp.empty:
        return None

    if isinstance(temp["time"].dtype, pd.DatetimeTZDtype):
        temp["time"] = temp["time"].dt.tz_localize(None)

    temp = temp.sort_values("time")

    x = _to_naive_timestamp(x)

    if x is None or not (temp["time"].iloc[0] <= x <= temp["time"].iloc[-1]):
        return None

    interpolated = np.interp(
        x.value,
        temp["time"].astype("int64").to_numpy(),
        temp["value"].to_numpy(),
    )

    return None if pd.isna(interpolated) else float(interpolated)


# Osie
def _get_y_range(series):
    """Zwraca ręcznie ustawiony zakres osi Y."""
    if series.get("y_auto", True):
        return None

    try:
        y_min = float(series.get("y_min"))
        y_max = float(series.get("y_max"))
    except (TypeError, ValueError):
        return None

    return [y_min, y_max] if y_min < y_max else None


def _axis_for_series(series_idx, label, color, y_range, all_axes_left, domain_start, extra_used):
    """Zwraca (yaxis_ref, axis_key, axis_conf, zaktualizowane extra_used)."""
    title = dict(text=label, font=dict(color=color), standoff=5)

    if series_idx == 0:
        axis_conf = dict(
            title=title,
            tickfont=dict(color=color),
            side="left",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            range=y_range,
        )
        return "y", "yaxis", axis_conf, extra_used

    if series_idx == 1 and not all_axes_left:
        axis_conf = dict(
            title=title,
            tickfont=dict(color=color),
            side="right",
            overlaying="y",
            showgrid=False,
            range=y_range,
        )
        return "y2", "yaxis2", axis_conf, extra_used

    extra_used += 1
    position = max(0.0, domain_start - AXIS_GAP * extra_used)

    axis_conf = dict(
        title=title,
        tickfont=dict(color=color),
        side="left",
        overlaying="y",
        anchor="free",
        position=position,
        showgrid=False,
        range=y_range,
    )
    return f"y{series_idx + 1}", f"yaxis{series_idx + 1}", axis_conf, extra_used


# Budowanie dashboardu
def _add_series_trace(fig, x, y, yaxis, customdata, *, name, color, width, value_label,
                       dash=None, opacity=1.0, markers=False, showlegend=True):
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines+markers" if markers else "lines",
            name=name,
            line=dict(color=color, width=width, dash=dash),
            marker=dict(size=5, color=color) if markers else None,
            opacity=opacity,
            yaxis=yaxis,
            customdata=customdata,
            showlegend=showlegend,
            hovertemplate=(
                f"<b>Czas:</b> %{{x}}<br><b>{value_label}:</b> %{{y:.6f}}<extra></extra>"
            ),
        )
    )


def _build_figure(all_series, start_time, end_time, show_minmax, all_axes_left, markers_enabled=False):
    num_series = len(all_series)
    extra_left = max(0, num_series - (1 if all_axes_left else 2))
    domain_start = min(extra_left * AXIS_GAP, MAX_DOMAIN_START)

    fig = go.Figure()
    layout_axes = {}
    extra_used = 0
    required_columns = {"time", "VALUE_AVG", "VALUE_MIN", "VALUE_MAX"}

    for series_idx, series in enumerate(all_series):
        data = series["df"]

        if data is None or data.empty or not required_columns.issubset(data.columns):
            continue

        color, label = series["color"], series["label"]
        y_range = _get_y_range(series)
        customdata = [series_idx] * len(data)

        yaxis_ref, axis_key, axis_conf, extra_used = _axis_for_series(
            series_idx, label, color, y_range, all_axes_left, domain_start, extra_used
        )
        layout_axes[axis_key] = axis_conf

        if show_minmax:
            _add_series_trace(
                fig, data["time"], data["VALUE_MIN"], yaxis_ref, customdata,
                name=f"MIN — {label}", color=color, width=1, dash="dot",
                opacity=0.4, showlegend=False, value_label="MIN",
            )
            _add_series_trace(
                fig, data["time"], data["VALUE_MAX"], yaxis_ref, customdata,
                name=f"MAX — {label}", color=color, width=1, dash="dot",
                opacity=0.4, showlegend=False, value_label="MAX",
            )

        _add_series_trace(
            fig, data["time"], data["VALUE_AVG"], yaxis_ref, customdata,
            name=f"AVG — {label}", color=color, width=2, markers=True,
            showlegend=True, value_label="AVG",
        )

    fig.update_layout(
        **layout_axes,
        height=700,
        template="plotly_dark",
        hovermode="closest",
        clickmode="event+select",
        dragmode="zoom",
        legend=dict(orientation="h", y=-0.15),
        xaxis=dict(
            title="Czas",
            domain=[domain_start, 1],
            range=[_to_naive_timestamp(start_time), _to_naive_timestamp(end_time)],
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
        ),
        margin=dict(l=60, r=60, t=30, b=40),
    )

    return fig


# Obsługa eventów Plotly
def _get_attr(obj, name, default=None):
    """Czyta atrybut zarówno z dict, jak i obiektu (np. PlotlyState)."""
    if obj is None:
        return default

    try:
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)
    except Exception:
        return default


def _get_selection(chart_event):
    """Zwraca sekcję selection z eventu Plotly."""
    return _get_attr(chart_event, "selection", {}) or {}


def _get_selection_points(chart_event):
    """Zwraca listę punktów z eventu Plotly."""
    return list(_get_attr(_get_selection(chart_event), "points", []) or [])


def _get_box_selections(chart_event):
    """Zwraca listę zaznaczeń prostokątnych."""
    return list(_get_attr(_get_selection(chart_event), "box", []) or [])


def _extract_series_idx(customdata):
    """Odczytuje indeks serii z customdata."""
    if customdata is None:
        return None

    if isinstance(customdata, (list, tuple)):
        if not customdata:
            return None
        customdata = customdata[0]

    try:
        return int(customdata)
    except (TypeError, ValueError):
        return None


def _marker_signature(marker):
    if not marker:
        return None

    return (
        str(marker.get("x")),
        marker.get("series_idx"),
        marker.get("curve_number"),
        marker.get("point_number"),
        marker.get("point_index"),
    )


def _get_last_clicked_point(chart_event):
    """
    Pobiera ostatni kliknięty punkt z eventu Plotly.

    """
    points = _get_selection_points(chart_event)

    if not points:
        return None

    point = points[-1]
    x = _get_attr(point, "x")

    if x is None:
        return None

    curve_number = _get_attr(point, "curve_number")

    try:
        curve_number = int(curve_number) if curve_number is not None else None
    except (TypeError, ValueError):
        curve_number = None

    y = _get_attr(point, "y")

    try:
        y = float(y) if y is not None else None
    except (TypeError, ValueError):
        y = None

    return {
        "x": x,
        "y": y,
        "curve_number": curve_number,
        "point_number": _get_attr(point, "point_number"),
        "point_index": _get_attr(point, "point_index"),
        "series_idx": _extract_series_idx(_get_attr(point, "customdata")),
    }


def _handle_marker_event(chart_event, keys):
    """Dodaje kliknięty punkt do listy dwóch markerów."""
    marker = _get_last_clicked_point(chart_event)

    if marker is None:
        return False

    signature = _marker_signature(marker)

    # Streamlit może zwrócić ten sam event podczas kolejnego rerunu.
    if st.session_state.get(keys["last_marker_signature"]) == signature:
        return False

    st.session_state[keys["last_marker_signature"]] = signature

    marker_1 = st.session_state.get(keys["marker_1"])
    marker_2 = st.session_state.get(keys["marker_2"])

    if marker_1 is None:
        st.session_state[keys["marker_1"]] = marker
    elif marker_2 is None:
        st.session_state[keys["marker_2"]] = marker
    else:
        # Trzeci klik: stary M2 staje się M1, nowy punkt staje się M2.
        st.session_state[keys["marker_1"]] = marker_2
        st.session_state[keys["marker_2"]] = marker

    return True


def _reset_markers(keys):
    """Czyści markery dla konkretnego wykresu."""
    st.session_state[keys["marker_1"]] = None
    st.session_state[keys["marker_2"]] = None
    st.session_state[keys["last_marker_signature"]] = None


# Awaryjne mapowanie trace -> seria

def _series_index_from_curve(curve_number, show_minmax):
    """
    Awaryjne mapowanie numeru trace do serii.

    Normalnie używane jest customdata.
    """
    if curve_number is None:
        return None

    try:
        curve_number = int(curve_number)
    except (TypeError, ValueError):
        return None

    if curve_number < 0:
        return None

    traces_per_series = 3 if show_minmax else 1
    return curve_number // traces_per_series


# Markery wizualne na figurze
def _add_marker_traces(fig, all_series, show_minmax, keys):
    """Dodaje widoczne markery M1/M2 do figury."""
    marker_definitions = [
        (st.session_state.get(keys["marker_1"]), "M1", "#00e5ff"),
        (st.session_state.get(keys["marker_2"]), "M2", "#ff3bd4"),
    ]

    for marker, label, color in marker_definitions:
        if not marker:
            continue

        x = marker.get("x")
        curve_number = marker.get("curve_number")
        series_idx = marker.get("series_idx")

        if x is None:
            continue

        # Fallback dla starych markerów zapisanych bez series_idx.
        if series_idx is None:
            series_idx = _series_index_from_curve(curve_number, show_minmax)

        if series_idx is None or not (0 <= series_idx < len(all_series)):
            continue

        y = marker.get("y")

        if y is None:
            continue

        yaxis_ref = "y"

        try:
            curve_number_int = int(curve_number)
            if 0 <= curve_number_int < len(fig.data):
                yaxis_ref = fig.data[curve_number_int].yaxis or "y"
        except (TypeError, ValueError):
            pass

        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                name=label,
                yaxis=yaxis_ref,
                text=[label],
                textposition="top center",
                marker=dict(size=15, color=color, line=dict(color="white", width=2)),
                customdata=[[series_idx]],
                hovertemplate=(
                    f"<b>{label}</b><br>Czas: %{{x}}<br>Wartość: %{{y:.6f}}<extra></extra>"
                ),
                showlegend=True,
            )
        )

        fig.add_vline(x=x, line_width=1, line_dash="dash", line_color=color, opacity=0.75)
        fig.add_hline(y=y, line_width=1, line_dash="dash", line_color=color, opacity=0.75)


# Tabele
def _series_summary_row(series):
    """Zwraca wiersz podsumowania (aktualna/średnia AVG, MIN, MAX) dla jednej serii."""
    row = {
        "Seria": series["label"],
        "Tabela": f"{series['schema']}.{series['table']}",
        "Aktualna AVG": None,
        "Średnia AVG": None,
        "MIN": None,
        "MAX": None,
    }

    data = series["df"]
    required_columns = {"VALUE_AVG", "VALUE_MIN", "VALUE_MAX"}

    if data is None or data.empty or not required_columns.issubset(data.columns):
        return row

    avg = pd.to_numeric(data["VALUE_AVG"], errors="coerce").dropna()
    vmin = pd.to_numeric(data["VALUE_MIN"], errors="coerce").dropna()
    vmax = pd.to_numeric(data["VALUE_MAX"], errors="coerce").dropna()

    if not avg.empty:
        row["Aktualna AVG"] = round(float(avg.iloc[-1]), 3)
        row["Średnia AVG"] = round(float(avg.mean()), 3)
    if not vmin.empty:
        row["MIN"] = round(float(vmin.min()), 3)
    if not vmax.empty:
        row["MAX"] = round(float(vmax.max()), 3)

    return row


def _render_summary_table(all_series):
    rows = [_series_summary_row(series) for series in all_series]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _render_marker_info(all_series, marker_1, marker_2):
    """Wyświetla dane tylko dla serii, na których postawiono markery."""
    series_idx_1 = marker_1.get("series_idx") if marker_1 else None
    series_idx_2 = marker_2.get("series_idx") if marker_2 else None

    relevant_indices = sorted(
        {idx for idx in (series_idx_1, series_idx_2) if idx is not None}
    )

    rows = []

    for idx in relevant_indices:
        if idx >= len(all_series):
            continue

        x1 = marker_1["x"] if idx == series_idx_1 else None
        y1 = marker_1["y"] if idx == series_idx_1 else None
        x2 = marker_2["x"] if idx == series_idx_2 else None
        y2 = marker_2["y"] if idx == series_idx_2 else None

        delta_y = delta_t = slope = None

        if y1 is not None and y2 is not None:
            delta_y = y2 - y1
            delta_t = (_to_naive_timestamp(x2) - _to_naive_timestamp(x1)).total_seconds()
            if delta_t != 0:
                slope = delta_y / delta_t

        rows.append(
            {
                "Seria": all_series[idx]["label"],
                "M1 X": _format_dt(x1),
                "M1 Y": round(y1, 6) if y1 is not None else None,
                "M2 X": _format_dt(x2),
                "M2 Y": round(y2, 6) if y2 is not None else None,
                "ΔY": round(delta_y, 6) if delta_y is not None else None,
                "Δt [s]": round(delta_t, 6) if delta_t is not None else None,
                "ΔY/Δt": round(slope, 9) if slope is not None else None,
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


# Fragment

def make_chart_fragment(refresh_seconds, chart_key="main_chart"):
    """
    Zwraca funkcję-fragment z aktualnym interwałem odświeżania.

    Jeżeli aplikacja ma jeden wykres, można używać:
        make_chart_fragment(refresh_seconds)

    Przy wielu wykresach należy podać różne chart_key.
    """

    @st.fragment(run_every=refresh_seconds)
    def _render_chart_fragment(all_series, start_time, end_time):
        _render_chart_body(all_series, start_time, end_time, chart_key=chart_key)

    return _render_chart_fragment


# Tryb markerów

def _render_chart_body(all_series, start_time, end_time, chart_key="main_chart"):
    """Treść fragmentu wykresu."""
    st.subheader("📈 Wartość w czasie")

    keys = _chart_keys(chart_key)

    if keys["markers_enabled"] not in st.session_state:
        st.session_state[keys["markers_enabled"]] = False

    col_opt1, col_opt2, col_opt3 = st.columns(3)

    with col_opt1:
        show_minmax = st.checkbox(
            "Pokaż zakres MIN/MAX",
            value=(len(all_series) <= 2),
            key=keys["show_minmax"],
        )

    with col_opt2:
        all_axes_left = st.checkbox(
            "Wszystkie osie po lewej",
            value=False,
            key=keys["all_axes_left"],
            help=(
                "Jeśli wyłączone: 1. seria po lewej, 2. po prawej, kolejne po lewej. "
                "Jeśli włączone: wszystkie osie (od 2. serii) po lewej stronie."
            ),
        )

    with col_opt3:
        markers_enabled = st.checkbox("📍 Markery klikane", key=keys["markers_enabled"])

    fig = _build_figure(
        all_series, start_time, end_time, show_minmax, all_axes_left, markers_enabled
    )

    if markers_enabled:
        _add_marker_traces(fig, all_series, show_minmax, keys)

    _render_summary_table(all_series)

    chart_config = {
        "doubleClick": "reset+autosize",
        "displaylogo": False,
        "scrollZoom": True,
    }

    st.caption(
        "📍 Kliknij (double-click) bezpośrednio punkt na wykresie. Pierwszy klik=M1, drugi=M2, "
        "trzeci przesuwa M1/M2."
        if markers_enabled
        else "🔍 Przeciągnij po wykresie, aby zrobić zaznaczenie (Box Select) i przybliżyć zakres."
    )

    chart_event = st.plotly_chart(
        fig,
        width="stretch",
        config=chart_config,
        on_select="rerun",
        selection_mode=("points", "box"),
        key=keys["chart"],
    )

    points = _get_selection_points(chart_event)
    box_selections = _get_box_selections(chart_event)

    # Kliknięcia markerów
    if markers_enabled and points and not box_selections:
        if _handle_marker_event(chart_event, keys):
            st.rerun(scope="fragment")

    # Box Select z paska Plotly
    if box_selections:
        box_x_raw = _get_attr(box_selections[0], "x", []) or []

        if len(box_x_raw) >= 2:
            box_x = [v for v in (_to_python_datetime(v) for v in box_x_raw[:2]) if v is not None]

            if len(box_x) >= 2 and handle_zoom_box_select(box_x):
                st.rerun(scope="app")

    # Informacje o markerach
    if markers_enabled:
        marker_1 = st.session_state.get(keys["marker_1"])
        marker_2 = st.session_state.get(keys["marker_2"])

        col_marker_1, col_marker_2, col_reset = st.columns(3)

        with col_marker_1:
            if marker_1:
                st.success(f"M1: {_format_dt(marker_1.get('x'))}")
            else:
                st.info("M1: kliknij pierwszy punkt")

        with col_marker_2:
            if marker_2:
                st.success(f"M2: {_format_dt(marker_2.get('x'))}")
            else:
                st.info("M2: kliknij drugi punkt")

        with col_reset:
            if st.button("Wyczyść markery", key=keys["reset_markers"], width="stretch"):
                _reset_markers(keys)
                st.rerun(scope="fragment")

        if marker_1 or marker_2:
            _render_marker_info(all_series, marker_1, marker_2)

    # Opis osi
    num_series = len(all_series)

    if num_series > 1:
        if all_axes_left:
            st.caption("Wszystkie serie mają własną, opisaną oś po lewej stronie wykresu.")
        elif num_series > 2:
            st.caption(
                "1. seria → oś po lewej, 2. seria → oś po prawej, "
                "kolejne serie → dodatkowe osie doklejane po lewej stronie."
            )
