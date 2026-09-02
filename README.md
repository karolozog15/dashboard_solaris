# dashboard_solaris

Aplikacja **Streamlit** do wizualizacji danych historycznych z bazy **SQL Server**. Pozwala wybierać bazę, tabele i zmienne, a następnie porównywać kilka serii na jednym wykresie z obsługą MIN / AVG / MAX oraz zoomu po zaznaczeniu fragmentu wykresu.

## Funkcje

- wybór bazy danych dostępnej na serwerze SQL Server
- przegląd tabel i zmiennych w wybranej bazie
- dodawanie wielu serii danych z różnych tabel
- wykres **Plotly** z:
  - wartością średnią (**AVG**)
  - opcjonalnie zakresem **MIN / MAX**
  - wieloma osiami Y
- wybór zakresu czasu:
  - ostatnie ciągłe
  - ostatnie dyskretne
  - własny zakres daty i godziny
- automatyczne dopasowanie zakresu do zaznaczenia na wykresie
- ręczne odświeżanie oraz auto-refresh
- tabela z zagregowanymi danymi pod wykresem
- cache po stronie Streamlit dla lepszej wydajności

## Wymagania

- Python 3.10+ (zalecane)
- dostęp do serwera **Microsoft SQL Server**
- zainstalowany sterownik **ODBC Driver 17 for SQL Server**
- Windows / środowisko z dostępem do `pyodbc` i uwierzytelnianiem Trusted Connection

## Instalacja

1. Sklonuj repozytorium:

```bash
git clone https://github.com/karolozog15/dashboard_solaris.git
cd dashboard_solaris
```

2. Utwórz i aktywuj wirtualne środowisko:

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
pip install streamlit pandas plotly pyodbc
```

## Uruchomienie
Jeżeli wszystkie pliki w jednym katalogu wraz z `.vev` można uruchomić przez `double-click` pliku 'start.vbs'

```bash
streamlit run app.py
```

Aplikacja uruchomi się w przeglądarce i spróbuje połączyć się z bazą SQL Server skonfigurowaną w `config.py`.

## Konfiguracja

Najważniejsze ustawienia znajdują się w pliku `config.py`:

- `DB_SERVER` — adres serwera SQL Server
- `DB_DRIVER` — nazwa sterownika ODBC
- `DEFAULT_DB_NAME` — domyślnie wybrana baza
- `NAZWY_TABLE` — tabela z mapowaniem nazw zmiennych
- `MAX_PLOT_POINTS` — maksymalna liczba punktów na wykresie po agregacji
- `MAX_SERIES` — maksymalna liczba serii
- `LOCAL_TZ` — lokalna strefa czasowa aplikacji

Przykładowo tabela z nazwami zmiennych jest pobierana z:

```python
dbo.WODA_VARIABLES
```

## Jak działa aplikacja

1. Aplikacja pobiera listę dostępnych baz danych z serwera.
2. Następnie wczytuje tabele i dostępne wartości `VARIABLE`.
3. Dla wybranej serii pobiera dane z zakresu czasu.
4. Dane są agregowane do maksymalnej liczby punktów, aby wykres był płynny.
5. Plotly wyświetla serię / serie na wspólnym wykresie z osobnymi osiami Y.
6. Zaznaczenie fragmentu wykresu może zmienić zakres czasu i pobrać dane ponownie.

## Struktura plików

- `app.py` — główny plik aplikacji Streamlit
- `db.py` — połączenie z SQL Server i pobieranie danych
- `charting.py` — budowa wykresu Plotly i tabeli podsumowania
- `state.py` — logika `session_state`, serie i zoom
- `config.py` — ustawienia konfiguracyjne
- `start.vbs` — pomocniczy skrypt uruchomieniowy

## Uwagi

- Aplikacja korzysta z `Trusted_Connection=yes`, więc zakłada uwierzytelnianie Windows.
- Jeśli nie widzisz danych, sprawdź:
  - poprawność `DB_SERVER`
  - dostęp do bazy
  - czy tabela ma kolumny `VARIABLE`, `TIMESTAMP_S`, `TIMESTAMP_MS`, `VALUE`
- Przy dużych zakresach czasu dane są automatycznie agregowane, żeby zachować wydajność.

## Licencja

Brak określonej licencji w repozytorium.
