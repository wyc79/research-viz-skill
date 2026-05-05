# How to use this folder

A short human's guide to the sensor-log streamlit workspace.

This `visualizations/` folder is a project-specific recipe for `data/sensor_log.csv`. The Python files have been tailored to that single CSV — they parse the `ts` column to datetime, write a cleaned copy under `intermediate_data/`, and ship a streamlit page that filters by `site` + `sensor` and plots `value` over time. There are no agents in the loop at run time: just two shell wrappers.

`data/` is **read-only** to everything in here. All transformed outputs land in `intermediate_data/`.

All commands assume your working directory is the project root (the folder that contains `data/` and `visualizations/`).

---

## 1. Parse / clean the raw CSV

```bash
bash visualizations/parse_input.sh
```

Reads `data/sensor_log.csv`, parses the `ts` column to datetime, sorts by timestamp, and writes:

- `visualizations/intermediate_data/sensor_log__parsed.csv` — the cleaned copy (800 rows, 5 columns).
- `visualizations/intermediate_data/parsed_index.json` — manifest with `canonical_csv: "sensor_log__parsed.csv"`.

To point the wrapper at a different folder:

```bash
DATA_DIR=/path/to/other_data bash visualizations/parse_input.sh
# or
bash visualizations/parse_input.sh --data-dir /path/to/other_data
```

The cleaning logic lives in `apply_project_specific_cleaning(df)` near the top of `scripts/parser.py`. To change behaviour (different sort order, sentinel replacements, dtype coercions), edit that function and rerun the wrapper.

---

## 2. Launch the streamlit dashboard

```bash
bash visualizations/interactive_page.sh
```

Opens `http://localhost:8501` with two pages:

- **Sensor-log explorer** (`streamlit/index.py`) — landing page with schema, sample, and counts.
- **Time series** (`streamlit/pages/1_time_series.py`) — sidebar multi-selects for `site` and `sensor`, an optional `ok=True`-only toggle, and an altair line chart of `value` over `ts`. Colour encodes the site, dash encodes the sensor, tooltips show the exact value + flag for each point.

To forward extra streamlit flags:

```bash
bash visualizations/interactive_page.sh --server.port=8600
```

Or run streamlit directly:

```bash
streamlit run visualizations/streamlit/index.py
```

---

## File map

```
visualizations/
├── parse_input.sh                   shell wrapper around scripts/parser.py
├── interactive_page.sh              shell wrapper that launches streamlit
├── scripts/
│   └── parser.py                    sensor_log.csv -> sensor_log__parsed.csv + parsed_index.json
├── streamlit/
│   ├── index.py                     landing page
│   └── pages/
│       └── 1_time_series.py         site + sensor filters, value-over-time line chart
├── intermediate_data/
│   ├── parsed_index.json            manifest (canonical_csv pointer)
│   └── sensor_log__parsed.csv       cleaned single-file output
├── info/
│   ├── context.md                   continuation handoff for future sessions
│   └── how_to_use.md                this file
└── README.md
```

---

## Want behaviour to change?

- **New filter / different chart on the time-series page:** edit `streamlit/pages/1_time_series.py`. The filter widgets sit at the top of the file, the altair chart spec is right below.
- **Different cleaning / new derived column:** edit `apply_project_specific_cleaning(df)` in `scripts/parser.py`, then rerun `bash visualizations/parse_input.sh`.
- **Add another exploration page:** drop `streamlit/pages/2_<topic>.py` next to the time-series page; streamlit picks it up automatically.

The shell wrappers don't change — they just rerun whatever the Python files say to do.
