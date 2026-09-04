# dashboard_solaris

Aplikacja **Streamlit** do wizualizacji historycznych danych pomiarowych z baz **Microsoft SQL Server**. Umożliwia wybór bazy, tabeli i zmiennej, porównywanie kilku serii danych na jednym wykresie, analizę wartości AVG/MIN/MAX oraz ponowne pobieranie danych po zaznaczeniu fragmentu wykresu.

Aplikacja została przygotowana z myślą o pracy w środowisku Windows, z wykorzystaniem uwierzytelniania Windows oraz sterownika ODBC dla SQL Server.

## Funkcje

- wybór dostępnej bazy danych z serwera SQL Server,
- przegląd tabel bazowych w wybranej bazie,
- wybór wartości `VARIABLE` z wybranej tabeli,
- mapowanie identyfikatorów zmiennych na nazwy opisowe z tabeli `dbo.WODA_VARIABLES`,
- dodawanie maksymalnie **4 serii danych** do jednego wykresu,
- możliwość pobierania serii z różnych tabel,
- wykres Plotly w ciemnym motywie z:
  - wartością średnią `AVG`,
  - opcjonalnymi wartościami `MIN` i `MAX`,
  - osobną osią Y dla każdej serii,
  - automatycznym lub ręcznym zakresem osi Y,
  - możliwością rozmieszczenia wszystkich osi Y po lewej stronie,
  - interaktywnymi podpowiedziami zawierającymi czas i wartość,
- wybór zakresu czasu w trybach:
  - ostatni zakres dyskretny: 10 minut, 1 godzina, 1 dzień, 1 tydzień, 1 miesiąc lub 1 rok,
  - ostatni zakres ciągły podany w dniach, godzinach, minutach i sekundach,
  - własny zakres daty i godziny,
- zwykły zoom Plotly bez ponownego pobierania danych,
- box-select zapisujący zaznaczenie jako nowy zakres czasu i pobierający dane ponownie,
- przycisk cofania zoomu do zakresu sprzed zaznaczenia,
- tryb dwóch markerów M1 i M2 ustawianych przez kliknięcie punktów,
- obliczanie dla markerów:
  - różnicy wartości `ΔY`,
  - różnicy czasu `Δt` w sekundach,
  - tempa zmiany `ΔY/Δt`,
- tabela podsumowania dla każdej serii,
- tabela pełnych danych zagregowanych dla każdej serii,
- ręczne odświeżanie danych,
- automatyczne odświeżanie fragmentu wykresu,
- cache Streamlit ograniczający liczbę zapytań do bazy,
- skrypt Windows `start.vbs` do uruchamiania i bezpiecznego restartowania aplikacji,
- zapis lokalnego i sieciowego adresu aplikacji w pliku `link.txt`.

## Wymagania

- Python 3.10 lub nowszy,
- dostęp do serwera **Microsoft SQL Server**,
- zainstalowany sterownik **ODBC Driver 17 for SQL Server**,
- dostęp do bazy oraz odpowiednie uprawnienia odczytu,
- środowisko Windows w przypadku korzystania ze skryptu `start.vbs`,
- uwierzytelnianie Windows obsługiwane przez `Trusted_Connection=yes`.

Biblioteki Python używane przez aplikację:

- `streamlit` — interfejs webowy i fragmenty automatycznie odświeżane,
- `pandas` — odczyt oraz przetwarzanie danych,
- `plotly` — interaktywne wykresy,
- `pyodbc` — połączenie z SQL Server,
- `numpy` — interpolacja wartości w module wykresów.

## Instalacja z dostępem do Internetu

1. Sklonuj repozytorium:

```bash
git clone https://github.com/karolozog15/dashboard_solaris.git
cd dashboard_solaris
```

2. Utwórz środowisko wirtualne:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux / macOS:

```bash
source .venv/bin/activate
```

3. Zainstaluj zależności:

```bash
pip install streamlit pandas plotly pyodbc numpy
```

## Instalacja bez dostępu do Internetu

Na komputerze z dostępem do Internetu utwórz katalog `packages` i pobierz
pakiety wraz z zależnościami:

```bash
py -m pip download -d .\packages streamlit pandas plotly pyodbc numpy
```

Następnie przenieś na komputer docelowy:

- cały katalog projektu,
- interpreter Python lub jego instalator,
- katalog `packages`,
- sterownik ODBC dla SQL Server.

Na komputerze docelowym utwórz środowisko wirtualne:

```bash
.\Python\python.exe -m venv .venv
```

Biblioteki zainstaluj wyłącznie z lokalnego katalogu:

```bash
.\.venv\Scripts\python.exe -m pip install --no-index --find-links=.\packages streamlit pandas plotly pyodbc numpy
```

Parametr `--no-index` blokuje korzystanie z internetowego PyPI, a parametr
`--find-links=.\packages` wskazuje lokalizację pakietów instalacyjnych.

## Uruchomienie

Z terminala, z aktywnego środowiska wirtualnego:

```bash
streamlit run app.py
```

Lub bezpośrednio za pomocą interpretera środowiska:

```bash
.\.venv\Scripts\python.exe -m streamlit run .\app.py
```

Aplikacja domyślnie uruchamia się na porcie `8501` i jest dostępna lokalnie
pod adresem:

```text
http://localhost:8501
```

Aktualna wersja aplikacji korzysta z domyślnych ustawień Streamlit. Skrypt
`start.vbs` nie przekazuje parametrów `--server.address` ani `--server.port`.

## Uruchomienie przez `start.vbs`

Plik `start.vbs` pozwala uruchomić aplikację bez wyświetlania okna CMD lub
PowerShell. Skrypt należy uruchamiać z katalogu projektu lub bezpośrednio
przez dwukrotne kliknięcie.

Skrypt oczekuje następujących plików i katalogów:

```text
.venv\Scripts\python.exe
python314\python.exe
app.py
```

Podczas uruchomienia skrypt:

1. ustala własny katalog roboczy,
2. sprawdza obecność interpretera `.venv\Scripts\python.exe`,
3. sprawdza obecność `app.py`,
4. wykonuje `ipconfig` i wyszukuje adres IPv4,
5. zapisuje adres lokalny i sieciowy do `link.txt`,
6. sprawdza, czy port `8501` jest zajęty,
7. uruchamia aplikację, jeśli port jest wolny,
8. otwiera `http://localhost:8501` w przeglądarce.

Jeżeli port 8501 jest zajęty, skrypt nie kończy od razu znalezionego procesu.
Najpierw sprawdza jego nazwę, ścieżkę interpretera oraz linię polecenia.
Proces może zostać zakończony tylko wtedy, gdy:

- jest procesem `python.exe` lub `pythonw.exe`,
- używa interpretera `.venv\Scripts\python.exe` albo `python314\python.exe`,
- jego linia polecenia zawiera właściwy plik `app.py`.

Dopiero po pozytywnej weryfikacji wykonywane jest:

```text
taskkill /PID NUMER_PID /T /F
```

Jeżeli port zajmuje inna aplikacja albo nie można potwierdzić, że proces
należy do dashboardu, skrypt wyświetla ostrzeżenie i nie zabija procesu.

## Plik `link.txt`

Podczas uruchamiania `start.vbs` tworzony jest plik `link.txt`, zawierający
adres lokalny oraz wykryty adres sieciowy:

```text
WIZUALIZACJA BAZY DANYCH
======================

Local URL:
http://localhost:8501

Network URL:
http://ADRES_IP:8501
```

Adres sieciowy może być używany z innego komputera w tej samej sieci, jeżeli
pozwalają na to ustawienia zapory sieciowej oraz konfiguracja Streamlit.

## Konfiguracja

Najważniejsze ustawienia znajdują się w pliku `config.py`:

```python
LOCAL_TZ = timezone(timedelta(hours=1))
MAX_PLOT_POINTS = 10_000
DATA_CACHE_TTL = 300
VARIABLE_CACHE_TTL = 600
TABLE_CACHE_TTL = 600
NAZWY_TABLE = "dbo.WODA_VARIABLES"
MAX_SERIES = 4
AXIS_GAP = 0.05
MAX_DOMAIN_START = 0.45
DB_SERVER = r"ZENON14WIN\ZENON_2022"
DEFAULT_DB_NAME = "Archives"
DB_DRIVER = "ODBC Driver 17 for SQL Server"
```

Znaczenie najważniejszych stałych:

- `LOCAL_TZ` — stałe przesunięcie UTC+1 używane przy prezentacji czasu,
- `MAX_PLOT_POINTS` — maksymalna liczba bucketów po agregacji jednej serii,
- `MAX_SERIES` — maksymalnie 4 serie na jednym wykresie,
- `DATA_CACHE_TTL` — czas przechowywania danych pomiarowych w cache, 300 sekund,
- `VARIABLE_CACHE_TTL` — czas przechowywania list zmiennych, 600 sekund,
- `TABLE_CACHE_TTL` — czas przechowywania list baz i tabel, 600 sekund,
- `NAZWY_TABLE` — tabela mapująca `VARIABLE` na nazwę opisową,
- `AXIS_GAP` — odstęp pomiędzy dodatkowymi osiami Y,
- `MAX_DOMAIN_START` — maksymalny początek obszaru wykresu na osi X,
- `DB_SERVER` — adres serwera SQL Server,
- `DEFAULT_DB_NAME` — preferowana baza wybierana podczas startu,
- `DB_DRIVER` — nazwa sterownika ODBC.

## Jak działa pobieranie danych

Dla każdej serii aplikacja przekazuje do funkcji `load_data`:

- nazwę bazy,
- schemat tabeli,
- nazwę tabeli,
- wartość `VARIABLE`,
- początkowy timestamp Unix w sekundach,
- końcowy timestamp Unix w sekundach.

Zapytanie SQL wykorzystuje cztery etapy CTE:

1. `filtered` — wybiera rekordy dla zmiennej i zakresu czasu,
2. `bounds` — wyznacza najwcześniejszy i najpóźniejszy timestamp,
3. `bucketed` — przypisuje rekordy do przedziałów czasowych,
4. `aggregated` — oblicza AVG, MIN i MAX dla każdego przedziału.

Czas jest przechowywany w bazie w dwóch kolumnach:

```text
TIMESTAMP_S   — sekundy
TIMESTAMP_MS  — milisekundy
```

Aplikacja łączy je w jedną wartość:

```text
timestamp_ms_total = TIMESTAMP_S * 1000 + TIMESTAMP_MS
```

Następnie dane są dzielone maksymalnie na `MAX_PLOT_POINTS` bucketów. Dla
każdego bucketa obliczane są:

```text
VALUE_AVG
VALUE_MIN
VALUE_MAX
```

Czas reprezentujący bucket wyznaczany jest jako środek pomiędzy jego
najwcześniejszym i najpóźniejszym rekordem. Dzięki agregacji duże zakresy
czasu nie powodują przesyłania wszystkich surowych pomiarów do aplikacji.

## Zwykły zoom i box-select

Aplikacja obsługuje dwa różne sposoby przybliżania wykresu.

### Zwykły zoom Plotly

Zwykły zoom zmienia wyłącznie widoczny fragment już pobranych danych.
Nie powoduje ponownego zapytania do SQL Servera.

### Box-select

Box-select służy do zaznaczenia prostokątnego fragmentu wykresu. Po jego
wykonaniu:

1. odczytywane są dwie granice czasu,
2. granice są porządkowane chronologicznie,
3. zaznaczenie jest zapisywane w stanie sesji,
4. aktywowany jest tryb zoomu,
5. dane są ponownie pobierane dla nowego zakresu,
6. wykres jest renderowany z większą szczegółowością.

Przycisk `⏮️ Cofnij` przywraca zakres i tryb wyboru czasu sprzed zoomu.

## Markery M1 i M2

Po włączeniu opcji `📍 Markery klikane` użytkownik może klikać bezpośrednio
punkty AVG na wykresie.

- pierwszy klik ustawia marker `M1`,
- drugi klik ustawia marker `M2`,
- trzeci klik przesuwa poprzedni `M2` na pozycję `M1`, a nowy punkt ustawia
  jako `M2`.

Dla markerów wyświetlane są:

- czas i wartość punktu,
- pionowa linia pomocnicza,
- pozioma linia pomocnicza,
- tabela różnic pomiędzy M1 i M2.

Obliczenia mają postać:

```text
ΔY = Y2 - Y1
Δt = t2 - t1
ΔY/Δt = ΔY / Δt
```

`Δt` jest wyrażone w sekundach. Jeżeli oba punkty mają ten sam czas,
`ΔY/Δt` nie jest obliczane, aby uniknąć dzielenia przez zero.

## Struktura plików

- `app.py` — główny plik aplikacji Streamlit i interfejs użytkownika,
- `db.py` — połączenie z SQL Server, zapytania i agregacja danych,
- `charting.py` — wykres Plotly, osie Y, markery, zdarzenia i tabele,
- `state.py` — `session_state`, serie, zakresy czasu i zoom,
- `config.py` — konfiguracja aplikacji, limity, cache i kolory,
- `start.vbs` — uruchamianie, wykrywanie procesu i bezpieczny restart,
- `link.txt` — plik tworzony podczas uruchomienia, zawierający adresy aplikacji.

## Obsługa cache

Funkcje pobierające dane są dekorowane przez `st.cache_data`.

Aktualne ustawienia:

| Funkcja | Czas życia | Maksymalna liczba wpisów |
|---|---:|---:|
| `load_databases` | 600 s | 1 |
| `load_tables` | 600 s | 8 |
| `load_variables` | 600 s | 64 |
| `load_variable_names` | 600 s | 8 |
| `load_data` | 300 s | 64 |

Przycisk `🔄 Odśwież teraz` wykonuje `load_data.clear()`, dlatego usuwa
cache danych pomiarowych i powoduje ich ponowne pobranie. Cache list baz,
tabel i zmiennych nie jest przez ten przycisk czyszczony.

## Uwagi dotyczące bazy danych

Aplikacja zakłada, że tabela pomiarowa zawiera co najmniej kolumny:

```text
VARIABLE
TIMESTAMP_S
TIMESTAMP_MS
VALUE
```

Dodatkowo wykorzystywane mogą być kolumny:

```text
CALCULATION
STATUS
GUID
STRVALUE
```

Jeżeli tabela mapowania istnieje, powinna zawierać:

```text
VARIABLE
NAME
```

W przypadku problemów z pobieraniem danych należy sprawdzić:

- poprawność `DB_SERVER`,
- dostępność wybranej bazy,
- obecność sterownika ODBC,
- uprawnienia użytkownika Windows,
- istnienie wymaganych kolumn,
- poprawność tabeli `dbo.WODA_VARIABLES`,
- zakres czasu wybrany w aplikacji.

## Licencja

Brak określonej licencji w repozytorium.
