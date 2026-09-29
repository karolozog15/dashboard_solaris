# Dashboard Solaris

A Streamlit application for browsing and visualizing historical measurement data from Microsoft SQL Server. It allows you to compare multiple variables on one chart and analyze a selected time range.

## Features

- Select a database, table, and variable; optionally display descriptive variable names.
- Compare up to 4 data series, each with its own Y-axis.
- Plot AVG values with an optional MIN/MAX range and a manually configured Y-axis range.
- Choose a time range: recent, custom, or selected directly on the chart.
- Zoom and pan the chart without fetching data; selecting a chart region fetches the data again.
- Optionally add M1 and M2 markers and view a summary of the difference in values and time.
- View series summaries and a table of aggregated data.
- Manually or periodically refresh data, with query caching.
- Use the `start.vbs` script to launch the application on Windows.

## Requirements

- Python 3.10 or newer.
- Access to Microsoft SQL Server with read permissions.
- ODBC Driver 17 for SQL Server.
- Windows and Windows authentication (`Trusted_Connection=yes`) for the connection configured in `db.py`.

Python dependencies: `streamlit`, `pandas`, `plotly`, and `pyodbc`.

## Installation and Usage

```bash
git clone https://github.com/karolozog15/dashboard_solaris.git
cd dashboard_solaris
python -m venv .venv
```

Activate the environment (`.venv\\Scripts\\activate` on Windows or `source .venv/bin/activate` on Linux/macOS), then install the dependencies and run the application:

```bash
pip install streamlit pandas plotly pyodbc
streamlit run app.py
```

By default, Streamlit serves the application at `http://localhost:8501`.

On Windows, you can also run `start.vbs` from the project directory. The script expects `.venv\\Scripts\\python.exe` and `app.py`, writes the detected addresses to `link.txt`, and opens the application in a browser.

## Configuration and Data

Application settings, including the server and default SQL Server database, are located in `config.py`. The database connection and queries are defined in `db.py`. The application uses Windows authentication for the configured connection.

The measurement table should contain the columns `VARIABLE`, `TIMESTAMP_S`, `TIMESTAMP_MS`, and `VALUE`. Variable descriptions are read from `dbo.WODA_VARIABLES` (columns `VARIABLE` and `NAME`). If the descriptions table is unavailable, the application can still use the variable identifiers.

Data is aggregated into a maximum of 1,000 intervals per series. Database, table, and variable lists, as well as query results, are cached. The refresh button clears the measurement-data cache.

## Project Files

- `app.py` — user interface and main application flow.
- `db.py` — SQL Server connection, data retrieval, and aggregation.
- `charting.py` — charts, summaries, and marker handling.
- `state.py` — session state, series, and time ranges.
- `config.py` — settings, limits, and colors.
- `controls.html` — additional chart controls (mouse and space bar).
- `start.vbs` — launches the application on Windows.
- `Dokumnetacja___Dashboard.pdf` — additional project documentation.

## License

No license is specified for this repository.
