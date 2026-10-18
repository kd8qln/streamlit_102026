# Voyager Workbench

A session-based Streamlit workbench for experiment development, formula
development, batch calculations, and in-session table maintenance. Input and
calculated data are kept in the current app session and can be exported as CSV.
The interface does not write user-entered data or results to SQLite.

## Run

Install the project dependencies and start the app:

```bash
uv sync
uv run streamlit run streamlit_app.py
```

Place an optional splash image named `splash.png` in the project root to customize
the opening screen. In-session lookup table definitions and calculation logic are
kept in `workbench.py`, separate from the Streamlit interface.

## Test

```bash
uv run python -m unittest discover -s tests
```
