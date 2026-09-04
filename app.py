"""Punkt wejścia aplikacji Streamlit — wizualizacja danych z bazy SQL."""

from datetime import datetime, timedelta

import streamlit as st

from config import DEFAULT_DB_NAME, MAX_SERIES, LOCAL_TZ, get_series_color
from db import (
    load_databases,
    load_tables,
    load_variables,
    load_variable_names,
    load_data,
    get_variable_label,
)
from state import (
    init_session_state,
    add_series,
    remove_series,
    reset_series,
    undo_zoom,
    QUICK_RANGES,
)
from charting import make_chart_fragment

st.set_page_config(page_title="Wizualizacja bazy danych", page_icon="📈", layout="wide")

init_session_state()

st.title("📈 Dashboard - archives data")
st.caption("Wizualizacja danych archiwalnych z bazy sql")

#pobrani baz danych
try:
    available_databases = load_databases()
except Exception as e:
    st.error("Nie udało się pobrać listy baz danych z serwera.")
    st.code(str(e))
    st.stop()

if not available_databases:
    st.warning("Na serwerze nie znaleziono żadnych baz danych.")
    st.stop()

#ustawienie default
if st.session_state.get("selected_database") not in available_databases:
    st.session_state.selected_database = DEFAULT_DB_NAME if DEFAULT_DB_NAME in available_databases else available_databases[0]

#wybor bazy z listy
st.sidebar.header("⚙️ Ustawienia")
selected_database = st.sidebar.selectbox(
    "🗄️ Baza danych",
    available_databases,
    key="selected_database",
)

#reset przy zmianie bazy 
if selected_database != st.session_state._last_database:
    if st.session_state._last_database is not None:
        reset_series()
    st.session_state._last_database = selected_database

#pobranie listy tabel w danej bazie 
try:
    tables_df = load_tables(selected_database)
except Exception as e:
    st.error("Nie udało się połączyć z bazą SQL Server.")
    st.code(str(e))
    st.stop()

if tables_df.empty:
    st.warning("W wybranej bazie nie znaleziono żadnych tabel.")
    st.stop()

#pobranie nazw zmiennych jezeli w bazie jest tabela variable->Name (NAZWY_TABLE z config.py)
try:
    variable_names = load_variable_names(selected_database)
except Exception:
    variable_names = {}
    st.sidebar.warning("Nie udało się pobrać nazw zmiennych — pokazuję same ID.")


# Serie danych danej tabeli
table_options = [f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}" for row in tables_df.itertuples()]

st.sidebar.subheader("📊 Serie danych")
st.sidebar.caption("Dodaj jedną lub więcej zmiennych. Każda seria może pochodzić z innej tabeli.")
series_configs = []
series_to_remove = None

for idx, series_id in enumerate(st.session_state.series_ids):
    with st.sidebar.expander(f"Seria {idx + 1}", expanded=(idx == 0)):

        #pobiera wczesniej zapisana rzeczy co bylo w tej serii
        stored = st.session_state.series_data.get(series_id, {})
	
	#pobiera wczesniej zapisana tabele
        default_table = stored.get("table")
        
	# Jeżeli wcześniej była wybrana tabela i nadal znajduje się na liście,
	# bierze jej indeks. Jeżeli nie, wybiera pierwszą tabelę.
        table_index = table_options.index(default_table) if default_table in table_options else 0

	#wybor z tabeli z listy
        table_choice = st.selectbox(
            "Tabela",
            table_options,
            index=table_index,
            key=f"table_{series_id}",
        )
	
        s_schema, s_table = table_choice.split(".", 1)

	#pobranie listy variables z danej tabeli
        try:
            s_variables = load_variables(selected_database, s_schema, s_table)
        except Exception as e:
            st.error("Nie udało się pobrać VARIABLE.")
            st.code(str(e))
            s_variables = []

        if not s_variables:
            st.warning(f"Tabela `{table_choice}` nie zawiera żadnych VARIABLE.")
        else:
	    #podobnie jak wczesnije pobiera infromacje wcznesniejsze i ustawiwa varibale a jak nie ma wczesniejszcych to zerowa
            default_var = stored.get("variable")
            var_index = s_variables.index(default_var) if default_var in s_variables else 0
	    
            #wybor konkertnej zminnej
            var_choice = st.selectbox(
                "Zmienna",
                s_variables,
                index=var_index,
                format_func=lambda v: get_variable_label(v, variable_names),
                key=f"var_{series_id}",
            )
	    
            #wybor jak ma byc dopasowywyan os y
            st.markdown("**Zakres osi Y**")
            y_auto = st.checkbox(
                "Automatyczny zakres Y",
                value=stored.get("y_auto",True),
                key=f"y_auto_{series_id}",
            )

            if y_auto:
                y_min = None
                y_max = None
            else:
                col_y1, col_y2 = st.columns(2)

                with col_y1:
                    y_min = st.number_input(
                        "Min Y",
                        value=float(stored.get("y_min") if stored.get("y_min") is not None else 0.0),
                        key=f"y_min_{series_id}",
                    )

                with col_y2:
                    y_max = st.number_input(
                        "Max Y",
                        value=float(stored.get("y_max") if stored.get("y_max") is not None else 100.0),
                        key=f"y_max_{series_id}",
                    )

            #Ustawienie infomracji o danej serii
            st.session_state.series_data[series_id] = {
                "table": table_choice,
                "variable": var_choice,
                "y_auto": y_auto,
                "y_min": y_min,
                "y_max": y_max,
            }
   
            #potrzebne potem do ladwaonia danych
            series_configs.append({
                "id": series_id,
                "schema": s_schema,
                "table": s_table,
                "variable": var_choice,
                "label": get_variable_label(var_choice, variable_names),
                "y_auto": y_auto,
                "y_min": y_min,
                "y_max": y_max,
            })
	
	#jak jest wiecej niz 1 seria i klkinemy przycisk to zapisujemy ktora seria usunac
        if len(st.session_state.series_ids) > 1:
            if st.button("🗑️ Usuń tę serię", key=f"remove_{series_id}"):
                series_to_remove = series_id

#usuwanie kliknietych serii
if series_to_remove is not None:
    remove_series(series_to_remove)
    st.rerun()

#maksymalna ilosc serii
if len(st.session_state.series_ids) < MAX_SERIES:
    if st.sidebar.button("➕ Dodaj kolejną serię", use_container_width=True):
        add_series(MAX_SERIES)
        st.rerun()
else:
    st.sidebar.caption(f"Osiągnięto maksymalną liczbę serii ({MAX_SERIES}).")

if not series_configs:
    st.warning("Dodaj przynajmniej jedną poprawną serię (tabela z przynajmniej jedną zmienną).")
    st.stop()


# Zakres czasu
st.sidebar.subheader("⏱️ Zakres czasu")
#informacje na panelu
st.sidebar.write(
    f"**Zapamiętany zakres:** "
    f"{st.session_state.time_start_original.strftime('%Y-%m-%d %H:%M:%S')} → "
    f"{st.session_state.time_end_original.strftime('%Y-%m-%d %H:%M:%S')}"
)
st.sidebar.write(
    f"**Aktualny zakres:** "
    f"{st.session_state.time_start.strftime('%Y-%m-%d %H:%M:%S')} → "
    f"{st.session_state.time_end.strftime('%Y-%m-%d %H:%M:%S')}"
)

if st.session_state.zoom_active:
    if st.sidebar.button("⏮️ Cofnij", use_container_width=True):
        undo_zoom()
        st.rerun()



#Fragment w html aby ikonek orygianlnych uzyc 

st.sidebar.markdown("**Opis funkcji:** (prawy górny róg wykresu)")
zoom_icon_svg = """
<svg viewBox="0 0 1000 1000" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
    <path d="m1000-25l-250 251c40 63 63 138 63 218 0 224-182 406-407 406-224 0-406-182-406-406s183-406 407-406c80 0 155 22 218 62l250-250 125 125z m-812 250l0 438 437 0 0-438-437 0z m62 375l313 0 0-312-313 0 0 312z"
          transform="matrix(1 0 0 -1 0 850)"
          style="fill: rgba(255, 255, 255, 0.7);" />
</svg>
"""
box_select_icon_svg = """
<svg viewBox="0 0 1000 1000" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
    <path d="m0 850l0-143 143 0 0 143-143 0z m286 0l0-143 143 0 0 143-143 0z m285 0l0-143 143 0 0 143-143 0z m286 0l0-143 143 0 0 143-143 0z m-857-286l0-143 143 0 0 143-143 0z m857 0l0-143 143 0 0 143-143 0z m-857-285l0-143 143 0 0 143-143 0z m857 0l0-143 143 0 0 143-143 0z m-857-286l0-143 143 0 0 143-143 0z m286 0l0-143 143 0 0 143-143 0z m285 0l0-143 143 0 0 143-143 0z m286 0l0-143 143 0 0 143-143 0z"
          transform="matrix(1 0 0 -1 0 850)"
          style="fill: rgba(255, 255, 255, 0.7);" />
</svg>
"""
st.sidebar.markdown(
    f"""
    <div style="display: flex; flex-direction: column; gap: 10px; font-size: 0.9rem;">
        <div style="display: flex; gap: 8px; align-items: flex-start;">
            <div style="flex-shrink: 0; margin-top: 2px;">{zoom_icon_svg}</div>
            <span><b>Zoom</b> — Szybkie przybliżenie - bez pobierania danych.</span>
        </div>
        <div style="display: flex; gap: 8px; align-items: flex-start;">
            <div style="flex-shrink: 0; margin-top: 2px;">{box_select_icon_svg}</div>
            <span>
                <b>Box select</b> — Zaznaczony fragment zostanie zapisany jako nowy
                zakres czasu i dane zostaną pobrane na nowo z bazy z większą dokładnością.
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

#Wybor trybu zakresu czasu do pobrania danych
if st.session_state.zoom_active:
    st.sidebar.info(
        "Aktualny zakres pochodzi z zoomu na wykresie. "
        "Kliknij \"⏮️ Cofnij\", aby wrócić do ostatnio zapamiętanego zakresu."
    )
    start_time = st.session_state.time_start
    end_time = st.session_state.time_end

else:
    range_mode = st.sidebar.radio(
        "Tryb wyboru zakresu",
        ["Ostatnie ciągłe", "Ostatnie dyskretne", "Własny zakres"],
        horizontal=True,
        key="range_mode",
    )

    if range_mode == "Ostatnie dyskretne":
        quick_range = st.sidebar.selectbox(
            "Zakres",
            list(QUICK_RANGES.keys()),
            index=list(QUICK_RANGES.keys()).index(st.session_state.quick_range),
            key="quick_range",
        )
        now = datetime.now(LOCAL_TZ)
        start_time = now - QUICK_RANGES[quick_range]
        end_time = now

    elif range_mode == "Ostatnie ciągłe":
        st.sidebar.caption("Podaj, ile czasu wstecz pobrać:")

        range_seconds = st.sidebar.number_input(
            "Sekundy", min_value=0.0, value=st.session_state.range_seconds,
            step=1.0, key="range_seconds",
        )
        range_minutes = st.sidebar.number_input(
            "Minuty", min_value=0.0, value=st.session_state.range_minutes,
            step=1.0, key="range_minutes",
        )
        range_hours = st.sidebar.number_input(
            "Godziny", min_value=0.0, value=st.session_state.range_hours,
            step=1.0, key="range_hours",
        )
        range_days = st.sidebar.number_input(
            "Dni", min_value=0.0, value=st.session_state.range_days,
            step=1.0, key="range_days",
        )

        now = datetime.now(LOCAL_TZ)
        delta = timedelta(seconds=range_seconds, minutes=range_minutes,
                           hours=range_hours, days=range_days)
        start_time = now - delta
        end_time = now

    else:  # Własny zakres
        st.sidebar.caption("Wybierz dokładny zakres daty i godziny:")

        start_date = st.sidebar.date_input(
            "Data od", value=st.session_state.custom_start_date, key="custom_start_date",
        )
        start_clock = st.sidebar.time_input(
            "Godzina od", value=st.session_state.custom_start_clock, key="custom_start_clock",
        )
        end_date = st.sidebar.date_input(
            "Data do", value=st.session_state.custom_end_date, key="custom_end_date",
        )
        end_clock = st.sidebar.time_input(
            "Godzina do", value=st.session_state.custom_end_clock, key="custom_end_clock",
        )

        start_time = datetime.combine(start_date, start_clock).replace(tzinfo=LOCAL_TZ)
        end_time = datetime.combine(end_date, end_clock).replace(tzinfo=LOCAL_TZ)

    st.session_state.time_start_original = start_time
    st.session_state.time_end_original = end_time
    st.session_state.time_start = start_time
    st.session_state.time_end = end_time


if start_time > end_time:
    st.sidebar.error("Data/godzina początkowa musi być wcześniejsza niż końcowa.")
    st.stop()


# Odświeżanie

st.sidebar.subheader("🔄 Odświeżanie")

auto_refresh = st.sidebar.selectbox(
    "Odświeżaj dane",
    ["Wyłączone", "1 minuta", "5 minut", "15 minut", "30 minut"],
    index=2,
)
refresh_seconds = {
    "Wyłączone": None, "1 minuta": 60, "5 minut": 300, "15 minut": 900, "30 minut": 1800,
}[auto_refresh]

if st.sidebar.button("🔄 Odśwież teraz", use_container_width=True):
    load_data.clear()
    st.rerun()


# Wczytanie danych i wykres

start_timestamp = int(start_time.timestamp())
end_timestamp = int(end_time.timestamp())

loaded_series = []
for s in series_configs:
    try:
	#wczytanie danych konkretnych serii wybranych wczesniej
        df_s = load_data(
            selected_database, s["schema"], s["table"], s["variable"],
            start_timestamp, end_timestamp,
        )
    except Exception as e:
        st.error(
            f"❌ Błąd podczas pobierania danych dla serii "
            f"„{s['label']}” ({s['schema']}.{s['table']})."
        )
        st.code(str(e))
        continue
    loaded_series.append({**s, "df": df_s})

for i, s in enumerate(loaded_series):
    s["color"] = get_series_color(i)

if not loaded_series:
    st.stop()

#do opisu nazwy serii
series_desc = "  |  ".join(
    f"`{s['schema']}.{s['table']}` → `{s['label']}`" for s in loaded_series
)
st.info(
    f"📊 **Serie:** {series_desc}  |  "
    f"⏱️ **Zakres:** `{start_time:%Y-%m-%d %H:%M:%S}` → `{end_time:%Y-%m-%d %H:%M:%S}`"
)

#rysowanie
chart_fragment = make_chart_fragment(refresh_seconds)
chart_fragment(loaded_series, start_time, end_time)

#wartrosci liczbowe w tabeli
with st.expander("📋 Pokaż dane zagregowane"):
    data_tabs = st.tabs([s["label"] for s in loaded_series])
    for tab, s in zip(data_tabs, loaded_series):
        with tab:
            if s["df"].empty:
                st.info("Brak rekordów w wybranym zakresie.")
            else:
                st.dataframe(s["df"].sort_values("time", ascending=False), use_container_width=True)
