"""Stałe konfiguracyjne aplikacji."""

from datetime import timezone, timedelta

LOCAL_TZ = timezone(timedelta(hours=1))		# Lokalna strefa czasowa używana w aplikacji (UTC+1)
MAX_PLOT_POINTS = 10_000			# Maksymalna liczba przedziałów, na które dzielony jest zaznaczony zakres czasu
DATA_CACHE_TTL = 300				# Czas przechowywania w pamięci podręcznej pobranych danych z bazy (5 minut)
VARIABLE_CACHE_TTL = 600			# Czas przechowywania w pamięci podręcznej listy zmiennych (10 minut)
TABLE_CACHE_TTL = 600				# Czas przechowywania w pamięci podręcznej listy tabel (10 minut)
NAZWY_TABLE = "dbo.WODA_VARIABLES"		# Tabela zawierająca nazwy zmiennych używanych w aplikacji
MAX_SERIES = 4					# Maksymalna liczba serii możliwych do dodania na wykresie
AXIS_GAP = 0.05					# Odstęp pomiędzy osiami Y dla poszczególnych serii
MAX_DOMAIN_START = 0.45				# Maksymalny początek obszaru wykresu przeznaczonego na osie Y

DB_SERVER = r"ZENON14WIN\ZENON_2022"		# Adres serwera SQL Server
DEFAULT_DB_NAME = "Archives"			# Domyślnie wybierana baza danych
DB_DRIVER = "ODBC Driver 17 for SQL Server"	# Sterownik ODBC używany do połączenia z SQL Server

VARIABLE_COLORS = [
    "#00E5FF", "#FF4B4B", "#00FF88", "#FFA500", "#A855F7", "#FFD700",
    "#FF69B4", "#00BFFF", "#7CFC00", "#FF7F50", "#40E0D0", "#DA70D6",
    "#ADFF2F", "#FF6347", "#6495ED", "#00CED1", "#FF1493", "#32CD32",
    "#BA55D3", "#1E90FF",
]


def get_series_color(index: int) -> str:
    return VARIABLE_COLORS[index % len(VARIABLE_COLORS)]
