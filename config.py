"""Stałe konfiguracyjne aplikacji."""

from datetime import timezone, timedelta

LOCAL_TZ = timezone(timedelta(hours=1))

MAX_PLOT_POINTS = 20_000
DATA_CACHE_TTL = 300
VARIABLE_CACHE_TTL = 600
TABLE_CACHE_TTL = 600
NAZWY_TABLE = "dbo.WODA_VARIABLES"
MAX_SERIES = 8
AXIS_GAP = 0.05
MAX_DOMAIN_START = 0.45

DB_SERVER = r"ZENON14WIN\ZENON_2022"
DEFAULT_DB_NAME = "Archives"  # sugerowany wybór domyślny w selectboxie baz
DB_DRIVER = "ODBC Driver 17 for SQL Server"

VARIABLE_COLORS = [
    "#00E5FF", "#FF4B4B", "#00FF88", "#FFA500", "#A855F7", "#FFD700",
    "#FF69B4", "#00BFFF", "#7CFC00", "#FF7F50", "#40E0D0", "#DA70D6",
    "#ADFF2F", "#FF6347", "#6495ED", "#00CED1", "#FF1493", "#32CD32",
    "#BA55D3", "#1E90FF",
]


def get_series_color(index: int) -> str:
    return VARIABLE_COLORS[index % len(VARIABLE_COLORS)]
