"""Budowa figury Plotly oraz renderowanie wykresu z markerami klikanymi."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import AXIS_GAP, MAX_DOMAIN_START
from state import handle_zoom_box_select


# ---------------------------------------------------------------------
# Klucze widgetów i stanów
# ---------------------------------------------------------------------


def _widget_key(chart_key, name):
    """
    Tworzy unikalny klucz dla konkretnego wykresu.

    Klucze Streamlit są globalne dla strony, dlatego każdy wykres
    powinien mieć własny chart_key.
    """
    return f"{chart_key}_{name}"


# ---------------------------------------------------------------------
# Czas i wartości
# ---------------------------------------------------------------------


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

    if value is None:
        return None

    return value.to_pydatetime()


def _format_dt(value):
    if value is None:
        return "—"

    value = _to_naive_timestamp(value)

    if value is None:
        return "—"

    return value.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _interpolate_value(df, x):
    """Zwraca interpolowaną wartość VALUE_AVG dla czasu X."""
    if df is None or df.empty or x is None:
        return None

    required_columns = {
        "time",
        "VALUE_AVG",
    }

    if not required_columns.issubset(df.columns):
        return None

    temp = pd.DataFrame(
        {
            "time": pd.to_datetime(
                df["time"],
                errors="coerce",
            ),
            "value": pd.to_numeric(
                df["VALUE_AVG"],
                errors="coerce",
            ),
        }
    ).dropna(
        subset=[
            "time",
            "value",
        ]
    )

    if temp.empty:
        return None

    if isinstance(temp["time"].dtype, pd.DatetimeTZDtype):
        temp["time"] = temp["time"].dt.tz_localize(None)

    temp = temp.sort_values("time")

    x = _to_naive_timestamp(x)

    if x is None:
        return None

    first_time = temp["time"].iloc[0]
    last_time = temp["time"].iloc[-1]

    if x < first_time or x > last_time:
        return None

    # Kliknięcie dokładnie w istniejący punkt.
    exact = temp.loc[
        temp["time"] == x,
        "value",
    ]

    if not exact.empty:
        return float(exact.iloc[0])

    # Interpolacja po nanosekundach.
    time_num = temp["time"].astype("int64").to_numpy()
    value_num = temp["value"].astype(float).to_numpy()
    x_num = x.value

    interpolation_index = sorted(
        set(
            time_num.tolist()
            + [x_num]
        )
    )

    interpolated = (
        pd.Series(
            value_num,
            index=time_num,
        )
        .reindex(interpolation_index)
        .interpolate()
        .loc[x_num]
    )

    if pd.isna(interpolated):
        return None

    return float(interpolated)


# ---------------------------------------------------------------------
# Osie
# ---------------------------------------------------------------------


def _get_y_range(series):
    """Zwraca ręcznie ustawiony zakres osi Y."""
    if series.get("y_auto", True):
        return None

    y_min = series.get("y_min")
    y_max = series.get("y_max")

    if y_min is None or y_max is None:
        return None

    try:
        y_min = float(y_min)
        y_max = float(y_max)
    except (TypeError, ValueError):
        return None

    if y_min >= y_max:
        return None

    return [
        y_min,
        y_max,
    ]


# ---------------------------------------------------------------------
# Budowanie figury
# ---------------------------------------------------------------------


def _build_figure(
    all_series,
    start_time,
    end_time,
    show_minmax,
    all_axes_left,
):
    """
    Buduje figurę Plotly.

    Każdy punkt otrzymuje customdata zawierające indeks serii.
    Dzięki temu kliknięcie nie zależy od curve_number ani od tego,
    czy widoczne są trace MIN/MAX.
    """
    num_series = len(all_series)

    if all_axes_left:
        extra_left = max(
            0,
            num_series - 1,
        )
    else:
        extra_left = max(
            0,
            num_series - 2,
        )

    domain_start = min(
        extra_left * AXIS_GAP,
        MAX_DOMAIN_START,
    )

    fig = go.Figure()
    layout_axes = {}
    extra_used = 0

    for series_idx, series in enumerate(all_series):
        data = series["df"]

        if data is None or data.empty:
            continue

        required_columns = {
            "time",
            "VALUE_AVG",
            "VALUE_MIN",
            "VALUE_MAX",
        }

        if not required_columns.issubset(data.columns):
            continue

        color = series["color"]
        label = series["label"]
        y_range = _get_y_range(series)

        # Indeks serii zapisany bezpośrednio w każdym punkcie.
        series_customdata = [series_idx] * len(data)

        if series_idx == 0:
            yaxis_ref = "y"
            axis_key = "yaxis"

            axis_conf = dict(
                title=dict(
                    text=label,
                    font=dict(color=color),
                    standoff=5,
                ),
                tickfont=dict(color=color),
                side="left",
                showgrid=True,
                gridcolor="rgba(255,255,255,0.08)",
                range=y_range,
            )

        elif series_idx == 1 and not all_axes_left:
            yaxis_ref = "y2"
            axis_key = "yaxis2"

            axis_conf = dict(
                title=dict(
                    text=label,
                    font=dict(color=color),
                    standoff=5,
                ),
                tickfont=dict(color=color),
                side="right",
                overlaying="y",
                showgrid=False,
                range=y_range,
            )

        else:
            extra_used += 1

            yaxis_ref = f"y{series_idx + 1}"
            axis_key = f"yaxis{series_idx + 1}"

            position = max(
                0.0,
                domain_start - AXIS_GAP * extra_used,
            )

            axis_conf = dict(
                title=dict(
                    text=label,
                    font=dict(color=color),
                    standoff=5,
                ),
                tickfont=dict(color=color),
                side="left",
                overlaying="y",
                anchor="free",
                position=position,
                showgrid=False,
                range=y_range,
            )

        layout_axes[axis_key] = axis_conf

        if show_minmax:
            fig.add_trace(
                go.Scatter(
                    x=data["time"],
                    y=data["VALUE_MIN"],
                    mode="lines",
                    name=f"MIN — {label}",
                    line=dict(
                        color=color,
                        width=1,
                        dash="dot",
                    ),
                    opacity=0.4,
                    yaxis=yaxis_ref,
                    customdata=series_customdata,
                    showlegend=False,
                    hovertemplate=(
                        "<b>Czas:</b> %{x}"
                        "<br><b>MIN:</b> %{y:.6f}"
                        "<extra></extra>"
                    ),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=data["time"],
                    y=data["VALUE_MAX"],
                    mode="lines",
                    name=f"MAX — {label}",
                    line=dict(
                        color=color,
                        width=1,
                        dash="dot",
                    ),
                    opacity=0.4,
                    yaxis=yaxis_ref,
                    customdata=series_customdata,
                    showlegend=False,
                    hovertemplate=(
                        "<b>Czas:</b> %{x}"
                        "<br><b>MAX:</b> %{y:.6f}"
                        "<extra></extra>"
                    ),
                )
            )

        fig.add_trace(
            go.Scatter(
                x=data["time"],
                y=data["VALUE_AVG"],
                mode="lines+markers",
                name=f"AVG — {label}",
                line=dict(
                    color=color,
                    width=2,
                ),
                marker=dict(
                    size=5,
                    color=color,
                ),
                yaxis=yaxis_ref,
                customdata=series_customdata,
                showlegend=True,
                hovertemplate=(
                    "<b>Czas:</b> %{x}"
                    "<br><b>AVG:</b> %{y:.6f}"
                    "<extra></extra>"
                ),
            )
        )

    start = _to_naive_timestamp(start_time)
    end = _to_naive_timestamp(end_time)

    fig.update_layout(
        **layout_axes,
        height=700,
        template="plotly_dark",
        hovermode="closest",

        # Kliknięcie punktu działa bez wybierania narzędzia.
        clickmode="event+select",

        # Domyślnie przeciąganie wykresu robi zwykły zoom.
        # Box Select z prawego górnego paska nadal działa po jego
        # ręcznym wybraniu.
        dragmode="zoom",

        # Zachowanie zakresu osi podczas rerunów.
        uirevision="main-chart",

        legend=dict(
            orientation="h",
            y=-0.15,
        ),
        xaxis=dict(
            title="Czas",
            domain=[
                domain_start,
                1,
            ],
            range=[
                start,
                end,
            ],
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
        ),
        margin=dict(
            l=60,
            r=60,
            t=30,
            b=40,
        ),
    )

    return fig


# ---------------------------------------------------------------------
# Obsługa eventów Plotly
# ---------------------------------------------------------------------


def _event_value(event, name, default=None):
    """Czyta wartość zarówno z dict, jak i PlotlyState."""
    if event is None:
        return default

    try:
        if isinstance(event, dict):
            return event.get(
                name,
                default,
            )

        return getattr(
            event,
            name,
            default,
        )
    except Exception:
        return default


def _get_selection(chart_event):
    """Zwraca sekcję selection z eventu Plotly."""
    return _event_value(
        chart_event,
        "selection",
        {},
    ) or {}


def _get_selection_points(chart_event):
    """Zwraca listę punktów z eventu Plotly."""
    selection = _get_selection(chart_event)

    points = _event_value(
        selection,
        "points",
        [],
    )

    if points is None:
        return []

    return list(points)


def _get_box_selections(chart_event):
    """Zwraca listę zaznaczeń prostokątnych."""
    selection = _get_selection(chart_event)

    box_selections = _event_value(
        selection,
        "box",
        [],
    )

    if box_selections is None:
        return []

    return list(box_selections)


def _point_value(point, name, default=None):
    if point is None:
        return default

    try:
        if isinstance(point, dict):
            return point.get(
                name,
                default,
            )

        return getattr(
            point,
            name,
            default,
        )
    except Exception:
        return default


def _extract_series_idx(customdata):
    """
    Odczytuje indeks serii z customdata.

    W zależności od wersji Plotly/Streamlit customdata może być:
    - liczbą,
    - listą,
    - krotką,
    - wartością tekstową.
    """
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

    Indeks serii jest pobierany z customdata.
    """
    points = _get_selection_points(chart_event)

    if not points:
        return None

    point = points[-1]

    x = _point_value(
        point,
        "x",
    )

    if x is None:
        return None

    curve_number = _point_value(
        point,
        "curve_number",
    )
    point_number = _point_value(
        point,
        "point_number",
    )
    point_index = _point_value(
        point,
        "point_index",
    )
    customdata = _point_value(
        point,
        "customdata",
    )

    series_idx = _extract_series_idx(customdata)

    try:
        curve_number = (
            int(curve_number)
            if curve_number is not None
            else None
        )
    except (TypeError, ValueError):
        curve_number = None

    return {
        "x": x,
        "curve_number": curve_number,
        "point_number": point_number,
        "point_index": point_index,
        "series_idx": series_idx,
    }


def _handle_marker_event(
    chart_event,
    chart_key="main_chart",
):
    """Dodaje kliknięty punkt do listy dwóch markerów."""
    marker = _get_last_clicked_point(chart_event)

    if marker is None:
        return False

    marker_1_key = _widget_key(
        chart_key,
        "marker_1",
    )
    marker_2_key = _widget_key(
        chart_key,
        "marker_2",
    )
    signature_key = _widget_key(
        chart_key,
        "last_marker_signature",
    )

    signature = _marker_signature(marker)

    # Streamlit może zwrócić ten sam event podczas kolejnego rerunu.
    if st.session_state.get(signature_key) == signature:
        return False

    st.session_state[signature_key] = signature

    marker_1 = st.session_state.get(marker_1_key)
    marker_2 = st.session_state.get(marker_2_key)

    if marker_1 is None:
        st.session_state[marker_1_key] = marker
    elif marker_2 is None:
        st.session_state[marker_2_key] = marker
    else:
        # Trzeci klik:
        # stary M2 staje się M1,
        # nowy punkt staje się M2.
        st.session_state[marker_1_key] = marker_2
        st.session_state[marker_2_key] = marker

    return True


def _reset_markers(chart_key="main_chart"):
    """Czyści markery dla konkretnego wykresu."""
    marker_1_key = _widget_key(
        chart_key,
        "marker_1",
    )
    marker_2_key = _widget_key(
        chart_key,
        "marker_2",
    )
    signature_key = _widget_key(
        chart_key,
        "last_marker_signature",
    )

    st.session_state[marker_1_key] = None
    st.session_state[marker_2_key] = None
    st.session_state[signature_key] = None


# ---------------------------------------------------------------------
# Awaryjne mapowanie trace -> seria
# ---------------------------------------------------------------------


def _series_index_from_curve(
    curve_number,
    show_minmax,
):
    """
    Awaryjne mapowanie numeru trace do serii.

    Normalnie używane jest customdata.
    """
    if curve_number is None:
        return None

    traces_per_series = 3 if show_minmax else 1

    try:
        curve_number = int(curve_number)
    except (TypeError, ValueError):
        return None

    if curve_number < 0:
        return None

    return curve_number // traces_per_series


# ---------------------------------------------------------------------
# Markery wizualne na figurze
# ---------------------------------------------------------------------


def _add_marker_traces(
    fig,
    all_series,
    show_minmax,
    chart_key,
):
    """
    Dodaje widoczne markery M1/M2 do figury.

    Markery są dodatkowymi trace'ami, ale nie wpływają na mapowanie
    kliknięć, ponieważ indeks serii zapisany jest w markerze.
    """
    marker_1_key = _widget_key(
        chart_key,
        "marker_1",
    )
    marker_2_key = _widget_key(
        chart_key,
        "marker_2",
    )

    marker_definitions = [
        (
            st.session_state.get(marker_1_key),
            "M1",
            "#00e5ff",
        ),
        (
            st.session_state.get(marker_2_key),
            "M2",
            "#ff3bd4",
        ),
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
            series_idx = _series_index_from_curve(
                curve_number,
                show_minmax,
            )

        if series_idx is None:
            continue

        if not (
            0 <= series_idx < len(all_series)
        ):
            continue

        data = all_series[series_idx]["df"]

        y = _interpolate_value(
            data,
            x,
        )

        if y is None:
            continue

        yaxis_ref = "y"

        try:
            curve_number_int = int(curve_number)

            if 0 <= curve_number_int < len(fig.data):
                yaxis_ref = (
                    fig.data[curve_number_int].yaxis
                    or "y"
                )
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
                marker=dict(
                    size=15,
                    color=color,
                    line=dict(
                        color="white",
                        width=2,
                    ),
                ),
                customdata=[
                    [series_idx]
                ],
                hovertemplate=(
                    f"<b>{label}</b>"
                    "<br>Czas: %{x}"
                    "<br>Wartość: %{y:.6f}"
                    "<extra></extra>"
                ),
                showlegend=True,
            )
        )

        fig.add_vline(
            x=x,
            line_width=1,
            line_dash="dash",
            line_color=color,
            opacity=0.75,
        )


# ---------------------------------------------------------------------
# Tabele
# ---------------------------------------------------------------------


def _render_summary_table(all_series):
    summary_rows = []

    for series in all_series:
        data = series["df"]

        table_name = (
            f"{series['schema']}.{series['table']}"
        )

        if data is None or data.empty:
            summary_rows.append(
                {
                    "Seria": series["label"],
                    "Tabela": table_name,
                    "Aktualna AVG": None,
                    "Średnia AVG": None,
                    "MIN": None,
                    "MAX": None,
                }
            )
            continue

        required_columns = {
            "VALUE_AVG",
            "VALUE_MIN",
            "VALUE_MAX",
        }

        if not required_columns.issubset(data.columns):
            summary_rows.append(
                {
                    "Seria": series["label"],
                    "Tabela": table_name,
                    "Aktualna AVG": None,
                    "Średnia AVG": None,
                    "MIN": None,
                    "MAX": None,
                }
            )
            continue

        avg_values = pd.to_numeric(
            data["VALUE_AVG"],
            errors="coerce",
        ).dropna()

        min_values = pd.to_numeric(
            data["VALUE_MIN"],
            errors="coerce",
        ).dropna()

        max_values = pd.to_numeric(
            data["VALUE_MAX"],
            errors="coerce",
        ).dropna()

        summary_rows.append(
            {
                "Seria": series["label"],
                "Tabela": table_name,
                "Aktualna AVG": (
                    round(
                        float(avg_values.iloc[-1]),
                        3,
                    )
                    if not avg_values.empty
                    else None
                ),
                "Średnia AVG": (
                    round(
                        float(avg_values.mean()),
                        3,
                    )
                    if not avg_values.empty
                    else None
                ),
                "MIN": (
                    round(
                        float(min_values.min()),
                        3,
                    )
                    if not min_values.empty
                    else None
                ),
                "MAX": (
                    round(
                        float(max_values.max()),
                        3,
                    )
                    if not max_values.empty
                    else None
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(summary_rows),
        width="stretch",
        hide_index=True,
    )


def _render_marker_info(
    all_series,
    marker_1,
    marker_2,
):
    """Wyświetla dane dla dwóch klikniętych markerów."""
    rows = []

    x1 = marker_1.get("x") if marker_1 else None
    x2 = marker_2.get("x") if marker_2 else None

    for series in all_series:
        data = series["df"]

        y1 = _interpolate_value(
            data,
            x1,
        )
        y2 = _interpolate_value(
            data,
            x2,
        )

        delta_y = None
        delta_t = None
        slope = None

        if y1 is not None and y2 is not None:
            delta_y = y2 - y1

            try:
                timestamp_1 = _to_naive_timestamp(x1)
                timestamp_2 = _to_naive_timestamp(x2)

                if (
                    timestamp_1 is not None
                    and timestamp_2 is not None
                ):
                    delta_t = (
                        timestamp_2 - timestamp_1
                    ).total_seconds()

                    if delta_t != 0:
                        slope = delta_y / delta_t
            except Exception:
                delta_t = None
                slope = None

        rows.append(
            {
                "Seria": series["label"],
                "M1 X": _format_dt(x1),
                "M1 Y": (
                    round(y1, 6)
                    if y1 is not None
                    else None
                ),
                "M2 X": _format_dt(x2),
                "M2 Y": (
                    round(y2, 6)
                    if y2 is not None
                    else None
                ),
                "ΔY": (
                    round(delta_y, 6)
                    if delta_y is not None
                    else None
                ),
                "Δt [s]": (
                    round(delta_t, 6)
                    if delta_t is not None
                    else None
                ),
                "ΔY/Δt": (
                    round(slope, 9)
                    if slope is not None
                    else None
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
    )


# ---------------------------------------------------------------------
# Fragment
# ---------------------------------------------------------------------


def make_chart_fragment(
    refresh_seconds,
    chart_key="main_chart",
):
    """
    Zwraca funkcję-fragment z aktualnym interwałem odświeżania.

    Jeżeli aplikacja ma jeden wykres, można używać:
        make_chart_fragment(refresh_seconds)

    Przy wielu wykresach należy podać różne chart_key.
    """

    @st.fragment(run_every=refresh_seconds)
    def _render_chart_fragment(
        all_series,
        start_time,
        end_time,
    ):
        _render_chart_body(
            all_series,
            start_time,
            end_time,
            chart_key=chart_key,
        )

    return _render_chart_fragment


# ---------------------------------------------------------------------
# Tryb markerów
# ---------------------------------------------------------------------


def _render_chart_body(
    all_series,
    start_time,
    end_time,
    chart_key="main_chart",
):
    """Treść fragmentu wykresu."""
    st.subheader("📈 Wartość w czasie")

    show_minmax_key = _widget_key(
        chart_key,
        "show_minmax",
    )
    all_axes_left_key = _widget_key(
        chart_key,
        "all_axes_left",
    )
    markers_key = _widget_key(
        chart_key,
        "markers_enabled",
    )

    if markers_key not in st.session_state:
        st.session_state[markers_key] = False

    # Są tylko trzy kolumny.
    col_opt1, col_opt2, col_opt3 = st.columns(3)

    with col_opt1:
        show_minmax = st.checkbox(
            "Pokaż zakres MIN/MAX",
            value=(len(all_series) <= 2),
            key=show_minmax_key,
        )

    with col_opt2:
        all_axes_left = st.checkbox(
            "Wszystkie osie po lewej",
            value=False,
            key=all_axes_left_key,
            help=(
                "Jeśli wyłączone: 1. seria po lewej, "
                "2. po prawej, kolejne po lewej. "
                "Jeśli włączone: wszystkie osie "
                "(od 2. serii) po lewej stronie."
            ),
        )

    with col_opt3:
        markers_enabled = st.checkbox(
            "📍 Markery klikane",
            key=markers_key,
        )

    fig = _build_figure(
        all_series,
        start_time,
        end_time,
        show_minmax,
        all_axes_left,
    )

    if markers_enabled:
        _add_marker_traces(
            fig,
            all_series,
            show_minmax,
            chart_key,
        )

    _render_summary_table(all_series)

    chart_config = {
        "doubleClick": "reset+autosize",
        "displaylogo": False,
        "scrollZoom": True,
    }

    # Nie usuwamy select2d z paska Plotly.
    # Użytkownik może aktywować Box Select z prawego górnego rogu.
    #
    # clickmode='event+select' pozwala klikać punkty bez aktywowania
    # narzędzia.
    fig.update_layout(
        dragmode="zoom",
        clickmode="event+select",
    )

    if markers_enabled:
        st.caption(
            "📍 Kliknij bezpośrednio punkt na wykresie. "
            "Pierwszy klik=M1, drugi=M2, "
            "trzeci przesuwa M1/M2."
        )
    else:
        st.caption(
            "🔍 Zwykłe przeciąganie wykonuje zoom. "
            "Aby użyć Box Select, wybierz prostokątne zaznaczenie "
            "z paska narzędzi w prawym górnym rogu."
        )

    # Jeden wykres obsługuje:
    # - bezpośrednie kliknięcie punktu,
    # - zaznaczenie prostokątem z paska Plotly.
    chart_event = st.plotly_chart(
        fig,
        width="stretch",
        config=chart_config,
        on_select="rerun",
        selection_mode=(
            "points",
            "box",
        ),
        key=_widget_key(
            chart_key,
            "chart",
        ),
    )

    selection = _get_selection(chart_event)
    points = _get_selection_points(chart_event)
    box_selections = _get_box_selections(chart_event)

    # -------------------------------------------------------------
    # Kliknięcia markerów
    # -------------------------------------------------------------
    #
    # Gdy zaznaczono Box Select, Streamlit może również zwrócić
    # punkty znajdujące się w prostokącie. Dlatego marker obsługujemy
    # tylko wtedy, gdy nie ma aktywnego zaznaczenia box.
    if markers_enabled and points and not box_selections:
        if _handle_marker_event(
            chart_event,
            chart_key,
        ):
            st.rerun(scope="fragment")

    # -------------------------------------------------------------
    # Box Select z paska Plotly
    # -------------------------------------------------------------
    #
    # Nie ma już osobnego checkboxa auto-zoom.
    # Box Select jest aktywowany bezpośrednio z paska wykresu.
    if box_selections:
        first_box = box_selections[0]

        box_x_raw = _event_value(
            first_box,
            "x",
            [],
        ) or []

        if len(box_x_raw) >= 2:
            box_x = [
                _to_python_datetime(value)
                for value in box_x_raw[:2]
            ]

            box_x = [
                value
                for value in box_x
                if value is not None
            ]

            if len(box_x) >= 2:
                if handle_zoom_box_select(box_x):
                    st.rerun(scope="app")

    # -------------------------------------------------------------
    # Informacje o markerach
    # -------------------------------------------------------------
    if markers_enabled:
        marker_1_key = _widget_key(
            chart_key,
            "marker_1",
        )
        marker_2_key = _widget_key(
            chart_key,
            "marker_2",
        )

        marker_1 = st.session_state.get(marker_1_key)
        marker_2 = st.session_state.get(marker_2_key)

        col_marker_1, col_marker_2, col_reset = st.columns(3)

        with col_marker_1:
            if marker_1:
                st.success(
                    f"M1: {_format_dt(marker_1.get('x'))}"
                )
            else:
                st.info(
                    "M1: kliknij pierwszy punkt"
                )

        with col_marker_2:
            if marker_2:
                st.success(
                    f"M2: {_format_dt(marker_2.get('x'))}"
                )
            else:
                st.info(
                    "M2: kliknij drugi punkt"
                )

        with col_reset:
            if st.button(
                "Wyczyść markery",
                key=_widget_key(
                    chart_key,
                    "reset_markers",
                ),
                width="stretch",
            ):
                _reset_markers(chart_key)
                st.rerun(scope="fragment")

        if marker_1 or marker_2:
            _render_marker_info(
                all_series,
                marker_1,
                marker_2,
            )

    # -------------------------------------------------------------
    # Opis osi
    # -------------------------------------------------------------
    num_series = len(all_series)

    if num_series > 1:
        if all_axes_left:
            st.caption(
                "Wszystkie serie mają własną, "
                "opisaną oś po lewej stronie wykresu."
            )
        elif num_series > 2:
            st.caption(
                "1. seria → oś po lewej, "
                "2. seria → oś po prawej, "
                "kolejne serie → dodatkowe osie "
                "doklejane po lewej stronie."
            )
