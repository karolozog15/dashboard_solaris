"""Inicjalizacja session_state oraz funkcje zarządzające seriami i zakresem czasu."""

import uuid
from datetime import datetime, timedelta

import streamlit as st

from config import LOCAL_TZ

QUICK_RANGES = {
    "10 minut": timedelta(minutes=10),
    "1 godzina": timedelta(hours=1),
    "1 dzień": timedelta(days=1),
    "1 tydzień": timedelta(weeks=1),
    "1 miesiąc": timedelta(days=30),
    "1 rok": timedelta(days=365),
}


def init_session_state() -> None:
    """Ustawia domyślne wartości w session_state, jeśli jeszcze nie istnieją.
    Wywoływane raz, na samym początku app.py."""

    if "series_ids" not in st.session_state:
        st.session_state.series_ids = [str(uuid.uuid4())]

    if "series_data" not in st.session_state:
        st.session_state.series_data = {}

    if "time_start_original" not in st.session_state:
        now = datetime.now(LOCAL_TZ)
        st.session_state.time_start_original = now - timedelta(hours=1)
        st.session_state.time_end_original = now

    if "time_start" not in st.session_state:
        st.session_state.time_start = st.session_state.time_start_original

    if "time_end" not in st.session_state:
        st.session_state.time_end = st.session_state.time_end_original

    if "zoom_active" not in st.session_state:
        st.session_state.zoom_active = False

    # Tryb range_mode zapamiętany DOKŁADNIE w chwili wejścia w zoom (box-select).
    # Dzięki temu "Cofnij" nie zależy od tego, co dzieje się z bieżącym
    # range_mode w międzyczasie (dodanie serii, auto-refresh, kolejne rerun'y).
    if "pre_zoom_range_mode" not in st.session_state:
        st.session_state.pre_zoom_range_mode = None

    if "last_processed_box" not in st.session_state:
        st.session_state.last_processed_box = None

    if "chart_key_version" not in st.session_state:
        st.session_state.chart_key_version = 0

    if "range_mode" not in st.session_state:
        st.session_state.range_mode = "Ostatnie dyskretne"

    if "quick_range" not in st.session_state:
        st.session_state.quick_range = "1 godzina"

    if "range_seconds" not in st.session_state:
        st.session_state.range_seconds = 0.0

    if "range_minutes" not in st.session_state:
        st.session_state.range_minutes = 10.0

    if "range_hours" not in st.session_state:
        st.session_state.range_hours = 0.0

    if "range_days" not in st.session_state:
        st.session_state.range_days = 0.0

    if "custom_start_date" not in st.session_state:
        st.session_state.custom_start_date = st.session_state.time_start_original.date()

    if "custom_start_clock" not in st.session_state:
        st.session_state.custom_start_clock = st.session_state.time_start_original.time()

    if "custom_end_date" not in st.session_state:
        st.session_state.custom_end_date = st.session_state.time_end_original.date()

    if "custom_end_clock" not in st.session_state:
        st.session_state.custom_end_clock = st.session_state.time_end_original.time()

    # UWAGA: celowo NIE inicjalizujemy tu "selected_database". Streamlit
    # ustawia wartość widgetu z klucza w session_state, jeśli klucz już
    # istnieje — z pominięciem parametru `index`. Gdybyśmy z góry wpisali
    # tu None, selectbox nigdy nie zastosowałby domyślnego DEFAULT_DB_NAME
    # ("Archives"), bo próbowałby dopasować None do listy baz. Klucz ma
    # więc powstać dopiero razem z widgetem w app.py, przy jego pierwszym
    # renderze — wtedy `index` faktycznie zadziała.

    if "_last_database" not in st.session_state:
        st.session_state._last_database = None


def insert_time(start_time: datetime, end_time: datetime) -> None:
    """
    Zapamiętuje aktualny zakres czasu w odpowiednich widgetach,
    zależnie od aktualnie wybranego range_mode.

    Nie zmienia trybu wyboru zakresu.

    UWAGA: ta funkcja zawsze nadpisuje time_start_original/time_end_original
    przekazanymi wartościami — dlatego NIE wolno jej wołać z zakresem
    pochodzącym z zoomu (box-select), bo "zgubi" oryginalny zakres, do
    którego ma wracać przycisk "Cofnij".
    """

    if st.session_state.range_mode == "Ostatnie dyskretne":
        now = datetime.now(LOCAL_TZ)
        delta = now - start_time

        closest_name = min(
            QUICK_RANGES,
            key=lambda name: abs((QUICK_RANGES[name] - delta).total_seconds()),
        )
        st.session_state.quick_range = closest_name

    elif st.session_state.range_mode == "Ostatnie ciągłe":
        delta = end_time - start_time
        total_seconds = delta.total_seconds()

        days = int(total_seconds // 86400)
        total_seconds -= days * 86400

        hours = int(total_seconds // 3600)
        total_seconds -= hours * 3600

        minutes = int(total_seconds // 60)
        seconds = total_seconds - minutes * 60

        st.session_state.range_days = float(days)
        st.session_state.range_hours = float(hours)
        st.session_state.range_minutes = float(minutes)
        st.session_state.range_seconds = float(seconds)

    elif st.session_state.range_mode == "Własny zakres":
        st.session_state.custom_start_date = start_time.date()
        st.session_state.custom_start_clock = start_time.time()
        st.session_state.custom_end_date = end_time.date()
        st.session_state.custom_end_clock = end_time.time()

    # ZAWSZE zapamiętaj faktyczny zakres
    st.session_state.time_start_original = start_time
    st.session_state.time_end_original = end_time
    st.session_state.time_start = start_time
    st.session_state.time_end = end_time


def add_series(max_series: int) -> None:
    if len(st.session_state.series_ids) < max_series:
        # Jeśli jesteśmy w trybie zoomu, NIE wolno wołać insert_time —
        # nadpisałoby to time_start_original/time_end_original wartościami
        # z przybliżenia, psując późniejsze "Cofnij".
        if not st.session_state.zoom_active:
            current_range_mode = st.session_state.range_mode
            insert_time(st.session_state.time_start, st.session_state.time_end)
            st.session_state.range_mode = current_range_mode

        st.session_state.series_ids.append(str(uuid.uuid4()))


def remove_series(series_id: str) -> None:
    if not st.session_state.zoom_active:
        current_range_mode = st.session_state.range_mode
        insert_time(st.session_state.time_start, st.session_state.time_end)
        st.session_state.range_mode = current_range_mode

    st.session_state.series_ids = [s for s in st.session_state.series_ids if s != series_id]
    # Posprzątaj WSZYSTKIE dane należące do usuwanej serii — w tym jawny
    # magazyn series_data, nie tylko klucze widgetów.
    st.session_state.series_data.pop(series_id, None)
    st.session_state.pop(f"table_{series_id}", None)
    st.session_state.pop(f"var_{series_id}", None)


def reset_series() -> None:
    """Czyści wszystkie skonfigurowane serie — używane np. po zmianie bazy danych,
    bo wybrane wcześniej tabele/zmienne mogą nie istnieć w nowej bazie."""
    for series_id in st.session_state.series_ids:
        st.session_state.series_data.pop(series_id, None)
        st.session_state.pop(f"table_{series_id}", None)
        st.session_state.pop(f"var_{series_id}", None)
    st.session_state.series_ids = [str(uuid.uuid4())]


def handle_zoom_box_select(box_x: list) -> bool:
    """Przetwarza zaznaczenie box-select z wykresu. Zwraca True, jeśli
    zakres faktycznie się zmienił i potrzebny jest rerun."""
    if len(box_x) < 2:
        return False

    box_signature = tuple(box_x)
    if box_signature == st.session_state.last_processed_box:
        return False

    new_start = box_x[0]
    new_end = box_x[1]
    if new_start > new_end:
        new_start, new_end = new_end, new_start

    # Zapamiętaj tryb TERAZ — zanim zoom_active ukryje radio i zanim
    # jakikolwiek kolejny rerun zdąży go zmienić. Nie nadpisuj przy
    # zagnieżdżonym zoomie (zoom w zoomie).
    if not st.session_state.zoom_active:
        st.session_state.pre_zoom_range_mode = st.session_state.range_mode

    st.session_state.last_processed_box = box_signature
    st.session_state.time_start = new_start.replace(tzinfo=LOCAL_TZ)
    st.session_state.time_end = new_end.replace(tzinfo=LOCAL_TZ)
    st.session_state.zoom_active = True
    return True


def undo_zoom() -> None:
    """Przywraca dokładnie ten range_mode i zakres, który obowiązywał
    w chwili wejścia w zoom."""
    restore_mode = st.session_state.pre_zoom_range_mode or st.session_state.range_mode

    st.session_state.range_mode = restore_mode
    insert_time(st.session_state.time_start_original, st.session_state.time_end_original)
    st.session_state.range_mode = restore_mode

    st.session_state.zoom_active = False
    st.session_state.last_processed_box = None
    st.session_state.chart_key_version += 1
    st.session_state.auto_zoom_enabled = False
    st.session_state.pre_zoom_range_mode = None
