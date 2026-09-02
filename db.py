"""Połączenie z SQL Server oraz wszystkie zapytania (cache'owane przez Streamlit)."""

import pandas as pd
import pyodbc
import streamlit as st

from config import (
    DB_SERVER,
    DB_DRIVER,
    NAZWY_TABLE,
    MAX_PLOT_POINTS,
    TABLE_CACHE_TTL,
    VARIABLE_CACHE_TTL,
    DATA_CACHE_TTL,
    LOCAL_TZ,
)

pyodbc.pooling = True


def quote_identifier(value) -> str:
    """Bezpieczne cytowanie nazwy schematu/tabeli."""
    return "[" + str(value).replace("]", "]]") + "]"


def get_connection(database: str | None = None):
    """Bez podania `database` łączy się na 'master' — wystarczające do
    odpytania sys.databases o listę baz dostępnych na serwerze."""
    db = database or "master"
    connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={db};"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
        "Connection Timeout=10;"
    )
    return pyodbc.connect(connection_string)


@st.cache_data(ttl=TABLE_CACHE_TTL, max_entries=1)
def load_databases() -> list[str]:
    query = """
        SELECT name
        FROM sys.databases
        WHERE database_id > 4       -- pomija master/tempdb/model/msdb
          AND state_desc = 'ONLINE'
        ORDER BY name;
    """
    conn = get_connection()
    try:
        return pd.read_sql(query, conn)["name"].tolist()
    finally:
        conn.close()


@st.cache_data(ttl=TABLE_CACHE_TTL, max_entries=8)
def load_tables(database: str) -> pd.DataFrame:
    query = """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME;
    """
    conn = get_connection(database)
    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()


@st.cache_data(ttl=VARIABLE_CACHE_TTL, max_entries=64)
def load_variables(database: str, table_schema: str, table_name: str) -> list[str]:
    full_table_name = f"{quote_identifier(table_schema)}.{quote_identifier(table_name)}"
    query = f"""
        SELECT DISTINCT VARIABLE
        FROM {full_table_name}
        WHERE VARIABLE IS NOT NULL
        ORDER BY VARIABLE;
    """
    conn = get_connection(database)
    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()
    return df["VARIABLE"].tolist()


@st.cache_data(ttl=VARIABLE_CACHE_TTL, max_entries=8)
def load_variable_names(database: str) -> dict:
    query = f"SELECT VARIABLE, NAME FROM {NAZWY_TABLE};"
    conn = get_connection(database)
    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()
    return dict(zip(df["VARIABLE"].astype(str), df["NAME"]))


def get_variable_label(variable, names_map: dict) -> str:
    name = names_map.get(str(variable))
    if name:
        return f"{name} ({variable})"
    return str(variable)


@st.cache_data(ttl=DATA_CACHE_TTL, max_entries=64, show_spinner=False)
def load_data(
    database: str,
    table_schema: str,
    table_name: str,
    variable: str,
    start_timestamp: int,
    end_timestamp: int,
) -> pd.DataFrame:
    full_table_name = f"{quote_identifier(table_schema)}.{quote_identifier(table_name)}"

    query = f"""
        WITH filtered AS (
            SELECT
                VARIABLE, CALCULATION, TIMESTAMP_S, TIMESTAMP_MS, VALUE, STATUS, GUID, STRVALUE,
                (CAST(TIMESTAMP_S AS BIGINT) * 1000 + COALESCE(CAST(TIMESTAMP_MS AS BIGINT), 0)) AS timestamp_ms_total
            FROM {full_table_name}
            WHERE VARIABLE = ?
              AND TIMESTAMP_S >= ?
              AND TIMESTAMP_S <= ?
        ),
        bounds AS (
            SELECT MIN(timestamp_ms_total) AS min_timestamp_ms, MAX(timestamp_ms_total) AS max_timestamp_ms
            FROM filtered
        ),
        bucketed AS (
            SELECT
                f.*,
                CASE
                    WHEN b.max_timestamp_ms = b.min_timestamp_ms THEN 0
                    ELSE FLOOR(
                        (f.timestamp_ms_total - b.min_timestamp_ms) * 1.0
                        / NULLIF(b.max_timestamp_ms - b.min_timestamp_ms, 0) * ?
                    )
                END AS bucket
            FROM filtered f
            CROSS JOIN bounds b
        ),
        aggregated AS (
            SELECT
                VARIABLE,
                AVG(VALUE) AS VALUE_AVG,
                MIN(VALUE) AS VALUE_MIN,
                MAX(VALUE) AS VALUE_MAX,
                MIN(timestamp_ms_total) AS bucket_min_timestamp,
                MAX(timestamp_ms_total) AS bucket_max_timestamp,
                MIN(CALCULATION) AS CALCULATION,
                MIN(STATUS) AS STATUS,
                MIN(GUID) AS GUID,
                MIN(STRVALUE) AS STRVALUE,
                bucket
            FROM bucketed
            WHERE VALUE IS NOT NULL
            GROUP BY VARIABLE, bucket
        )
        SELECT
            VARIABLE,
            CALCULATION,
            CAST((bucket_min_timestamp + bucket_max_timestamp) / 2 / 1000 AS BIGINT) AS TIMESTAMP_S,
            CAST(((bucket_min_timestamp + bucket_max_timestamp) / 2) % 1000 AS INT) AS TIMESTAMP_MS,
            VALUE_AVG, VALUE_MIN, VALUE_MAX, STATUS, GUID, STRVALUE
        FROM aggregated
        ORDER BY TIMESTAMP_S ASC, TIMESTAMP_MS ASC;
    """

    conn = get_connection(database)
    try:
        df = pd.read_sql(
            query,
            conn,
            params=[variable, int(start_timestamp), int(end_timestamp), MAX_PLOT_POINTS],
        )
    finally:
        conn.close()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "VARIABLE", "CALCULATION", "TIMESTAMP_S", "TIMESTAMP_MS",
                "VALUE_AVG", "VALUE_MIN", "VALUE_MAX", "STATUS", "GUID", "STRVALUE", "time",
            ]
        )

    df["TIMESTAMP_S"] = pd.to_numeric(df["TIMESTAMP_S"], errors="coerce")
    df["TIMESTAMP_MS"] = pd.to_numeric(df["TIMESTAMP_MS"], errors="coerce").fillna(0)

    df["time"] = pd.to_datetime(df["TIMESTAMP_S"], unit="s", errors="coerce", utc=True)
    df["time"] = df["time"] + pd.to_timedelta(df["TIMESTAMP_MS"], unit="ms")

    df["time"] = df["time"].dt.tz_convert(str(LOCAL_TZ)).dt.tz_localize(None)

    for column in ("VALUE_AVG", "VALUE_MIN", "VALUE_MAX"):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["time", "VALUE_AVG"])
    df = df.sort_values(["time", "TIMESTAMP_MS"]).reset_index(drop=True)

    return df
