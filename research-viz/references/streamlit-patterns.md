# Streamlit + altair patterns

The interactive subskill defaults to streamlit, with altair as a supplement for charts where streamlit's built-in helpers aren't enough.

## Multi-page apps

Streamlit's auto-discovery: any `.py` file under `streamlit/pages/` becomes a sidebar entry. Order them by prefixing with `1_…`, `2_…` if you care about ordering.

```
streamlit/
├── index.py            # landing page (run this)
└── pages/
    ├── 1_overview.py
    ├── 2_per_group_distributions.py
    └── 3_correlations.py
```

Each subpage is a standalone script; share helpers via `from scripts.helpers import utils` (you'll need to add the project root to `sys.path` at the top of each subpage, or run streamlit from the project root).

## Caching loads

Always wrap data loads in `@st.cache_data` keyed by `(path, mtime)` so the cache invalidates when the file changes:

```python
@st.cache_data(show_spinner=False)
def load_parsed(path: str, mtime: float) -> pd.DataFrame:
    return pd.read_csv(path)

df = load_parsed(str(PARSED_CSV), PARSED_CSV.stat().st_mtime)
```

`show_spinner=False` is nicer for fast loads. For slow ones, leave the spinner on.

## When to reach for altair

Use altair via `st.altair_chart(...)` when you specifically need:

- **linked brushing**: a selection in one chart filters another
- **interval selection**: drag-to-select on an axis
- **tooltips with custom fields**: streamlit's native charts have limited tooltip control

Minimum example with linked selection:

```python
import altair as alt

brush = alt.selection_interval()
left = (
    alt.Chart(df).mark_point().encode(
        x="x:Q", y="y:Q",
        color=alt.condition(brush, "category:N", alt.value("lightgray")),
    ).add_params(brush)
)
right = alt.Chart(df).mark_bar().encode(x="category:N", y="count()").transform_filter(brush)
st.altair_chart(left | right, use_container_width=True)
```

## Sampling for performance

If a chart spans the whole dataset and the dataset is big (>100k rows), sample before plotting:

```python
plot_df = df.sample(min(len(df), 50_000), random_state=0) if len(df) > 50_000 else df
```

Show a small caption explaining the sample so users aren't misled.

## Falling back to pre-rendered images

If the dataset is too large for live computation (rule of thumb: >1M rows, >200MB on disk, or any chart that takes >2s to update on each interaction), switch to a "viewer" mode:

1. Use `plot_gen.py` to pre-render variants into `plots/<topic>/`.
2. Make a streamlit page with a dropdown that selects which pre-rendered PNG to display:

```python
options = sorted((VIZ_ROOT / "plots" / "by_group").glob("*.png"))
choice = st.selectbox("variant", options, format_func=lambda p: p.stem)
st.image(str(choice), use_column_width=True)
```

> **Gotcha:** use `use_column_width=True` on `st.image`, **not** `use_container_width=True`. The latter looks like the right parameter (it's what the rest of streamlit moved to in 1.32) but it was only added to `st.image` in streamlit 1.32 — older versions still in the wild raise `TypeError: ImageMixin.image() got an unexpected keyword argument 'use_container_width'`. `use_column_width` works on every supported version (with a deprecation warning on the very newest). Same applies if you ever switch to `st.image(width="stretch")` — that's even newer.

Make the fallback explicit in `info/context.md` so a future agent knows why the page looks like an image gallery.

## Persisting widget state across pages

Use `st.session_state` for shared filters:

```python
if "min_temp" not in st.session_state:
    st.session_state.min_temp = float(df["temperature_C"].min())
st.session_state.min_temp = st.slider("min temperature", ..., key="min_temp")
```

Other pages then read `st.session_state.min_temp` directly.

## Layout

For dashboards, prefer `st.columns([1, 2])` for an asymmetric split (controls | chart) and `st.tabs([...])` for sectioned content. Avoid putting everything in expanders — they're great for "details" but bad as the primary container.
