# Dashboard Solaris

Aplikacja Streamlit do przeglądania i wizualizacji archiwalnych danych pomiarowych z Microsoft SQL Server. Umożliwia porównywanie kilku zmiennych na jednym wykresie oraz analizę wybranego zakresu czasu.

## Funkcje

- wybór bazy, tabeli i zmiennej; opcjonalne wyświetlanie opisowych nazw zmiennych,
- porównanie do 4 serii danych, każdej z osobną osią Y,
- wykres wartości AVG z opcjonalnym zakresem MIN/MAX i ręcznym zakresem osi Y,
- wybór zakresu czasu: ostatniego, własnego lub zaznaczonego na wykresie,
- przybliżanie i przesuwanie wykresu bez pobierania danych; zaznaczenie fragmentu pobiera dane ponownie,
- opcjonalne markery M1 i M2 oraz podsumowanie różnicy wartości i czasu,
- podsumowanie serii i tabela danych zagregowanych,
- ręczne i okresowe odświeżanie oraz cache zapytań,
- skrypt `start.vbs` do uruchamiania aplikacji w Windows.

## Wymagania

- Python 3.10 lub nowszy,
- dostęp do Microsoft SQL Server i uprawnienia odczytu,
- ODBC Driver 17 for SQL Server,
- Windows i uwierzytelnianie Windows (`Trusted_Connection=yes`) przy połączeniu skonfigurowanym w `db.py`.

Zależności Pythona: `streamlit`, `pandas`, `plotly` i `pyodbc`.

## Instalacja i uruchomienie

```bash
git clone https://github.com/karolozog15/dashboard_solaris.git
cd dashboard_solaris
python -m venv .venv
```

Aktywuj środowisko (`.venv\Scripts\activate` w Windows lub `source .venv/bin/activate` w Linux/macOS), a następnie zainstaluj zależności i uruchom aplikację:

```bash
pip install streamlit pandas plotly pyodbc
streamlit run app.py
```

Streamlit domyślnie udostępnia aplikację pod `http://localhost:8501`.

W Windows można też uruchomić `start.vbs` z katalogu projektu. Skrypt oczekuje `.venv\Scripts\python.exe` i `app.py`, zapisuje wykryte adresy w `link.txt` i otwiera aplikację w przeglądarce. Dostęp z innych komputerów wymaga odpowiedniej konfiguracji sieciowej, Streamlit i zapory.

## Konfiguracja i dane

Ustawienia aplikacji, w tym serwer i domyślna baza SQL Server, znajdują się w `config.py`. Połączenie z bazą i zapytania są zdefiniowane w `db.py`. Aplikacja korzysta z uwierzytelniania Windows.

Tabela pomiarowa powinna zawierać kolumny `VARIABLE`, `TIMESTAMP_S`, `TIMESTAMP_MS` i `VALUE`. Opisy zmiennych są pobierane z `dbo.WODA_VARIABLES` (kolumny `VARIABLE` i `NAME`); jeśli tabela opisów jest niedostępna, aplikacja wyświetla identyfikatory zmiennych.

Dane są agregowane do maksymalnie 1 000 przedziałów na serię. Listy baz, tabel i zmiennych oraz wyniki zapytań są cache'owane; przycisk odświeżania usuwa cache danych pomiarowych.

## Pliki projektu

- `app.py` — interfejs i główny przepływ aplikacji,
- `db.py` — połączenie z SQL Server, pobieranie i agregacja danych,
- `charting.py` — wykresy, podsumowania i obsługa markerów,
- `state.py` — stan sesji, serie i zakresy czasu,
- `config.py` — ustawienia, limity i kolory,
- `controls.html` — dodatkowe sterowanie wykresem (mysz i klawisz spacji),
- `start.vbs` — uruchamianie aplikacji w Windows,
- `Dokumnetacja___Dashboard.pdf` — dodatkowa dokumentacja projektu.

## Licencja

Repozytorium nie określa licencji.