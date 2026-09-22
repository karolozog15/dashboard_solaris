"""Stałe konfiguracyjne aplikacji."""

from datetime import timezone, timedelta

LOCAL_TZ = timezone(timedelta(hours=1))		# Lokalna strefa czasowa używana w aplikacji (UTC+1)
MAX_PLOT_POINTS = 2_000			# Maksymalna liczba przedziałów, na które dzielony jest zaznaczony zakres czasu
MAX_TABLE_ROWS= 2_000
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
pan_select_icon_svg = """
<svg viewBox="0 0 1000 1000" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
    <path d="m1000 350l-187 188 0-125-250 0 0 250 125 0-188 187-187-187 125 0 0-250-250 0 0 125-188-188 186-187 0 125 252 0 0-250-125 0 187-188 188 188-125 0 0 250 250 0 0-126 187 188z"
          transform="matrix(1 0 0 -1 0 850)"
          style="fill: rgba(255, 255, 255, 0.7);" />
</svg>
"""
autozoom_icon_svg = """
<svg viewBox="0 0 1000 1000" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
    <path d="m250 850l-187 0-63 0 0-62 0-188 63 0 0 188 187 0 0 62z m688 0l-188 0 0-62 188 0 0-188 62 0 0 188 0 62-62 0z m-875-938l0 188-63 0 0-188 0-62 63 0 187 0 0 62-187 0z m875 188l0-188-188 0 0-62 188 0 62 0 0 62 0 188-62 0z m-125 188l-1 0-93-94-156 156 156 156 92-93 2 0 0 250-250 0 0-2 93-92-156-156-156 156 94 92 0 2-250 0 0-250 0 0 93 93 157-156-157-156-93 94 0 0 0-250 250 0 0 0-94 93 156 157 156-157-93-93 0 0 250 0 0 250z"
          transform="matrix(1 0 0 -1 0 850)"
          style="fill: rgba(255, 255, 255, 0.7);" />
</svg>
"""
