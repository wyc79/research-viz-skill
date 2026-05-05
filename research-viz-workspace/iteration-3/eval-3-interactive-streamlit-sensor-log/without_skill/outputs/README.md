# Sensor Log Dashboard

Interactive Streamlit dashboard for `data/sensor_log.csv`.

## Files

- `app.py` — the Streamlit application
- `interactive_page.sh` — convenience launcher (creates a venv, installs deps, runs Streamlit)
- `requirements.txt` — Python dependencies (`streamlit`, `pandas`)
- `data/sensor_log.csv` — the input dataset

## Run

```bash
./interactive_page.sh
```

Then open http://localhost:8501 in your browser.

## Filters

The sidebar lets you:

- pick one or more **sites** (`east`, `north`, `south`, `west`)
- pick one or more **sensors** (`humidity`, `pressure`, `temperature`)
- restrict to readings flagged `ok=True`
- narrow the time range with a slider

The main panel shows summary metrics, a time-series line chart with one line per
*site · sensor* combination, a per-sensor average bar chart, and the raw
filtered rows in an expander.
