# interactive subskill

Build a streamlit app (with optional altair charts) under `streamlit/`, falling back to pre-rendered images for very large data.

Use when the user wants exploration rather than a fixed figure: "let me filter by …", "make a dashboard", "I want to brush / zoom / drill in", "show me a streamlit app".

Read this together with `../../SKILL.md` for the top-level rules.

---

## Before you build

If `visualizations/info/style_guide.md` exists, read it first and inherit the palette / typography / figure sizes from there. The streamlit pages should look like the static plots — same colors, same theme. Also check the guide's "Per-plot / per-page overrides" section: if the page name (e.g. `pages/2_species_explorer.py`) has an entry, honor it on top of the project-wide style.

The guide is a *guide, not a strict standard* — it drives new pages and any page the user asks you to update. You don't need to retrofit old pages. If the user requests a styling change during this run, record it in `style_guide.md` (project-wide or page-specific, as appropriate) so future sessions inherit it.

## Check the streamlit + altair versions first

Streamlit and altair both have notable API drift across recent versions and an "I'd assume this kwarg exists" mistake here will throw at the user's runtime, not yours. **Before generating any page**, check the installed versions and consult the table in `references/env-management.md`:

```bash
python3 -c "import streamlit, altair; print('streamlit', streamlit.__version__); print('altair', altair.__version__)"
```

Common traps to remember (full list in `env-management.md`):

- `st.image(use_container_width=…)` was only added in streamlit **1.32** — older streamlit raises `TypeError: ImageMixin.image() got an unexpected keyword argument 'use_container_width'`. Use `use_column_width=True` instead, which works on every supported version.
- `st.scatter_chart` and `st.bar_chart(color=…)` need streamlit **1.27**; on older versions, drop down to altair for the same chart.
- `st.cache_data` needs **1.18**; before that, `@st.cache(allow_output_mutation=True)` is the equivalent.
- altair selections moved from `alt.selection(type="interval")` + `.add_selection(...)` to `alt.selection_interval()` / `alt.selection_point()` + `.add_params(...)` in **5.0**.

When in doubt, write the legacy form — it works on both. Save the upgrade conversation for the user.

## Decision rule: streamlit vs. altair vs. fall-back-to-plot_gen

- **Default** is streamlit (`streamlit/index.py` + `streamlit/pages/<topic>.py`) with native streamlit widgets for filtering and `st.altair_chart(...)` for charts that benefit from altair's interactivity (selection, brushing, linked views).
- **Add altair** specifically when streamlit's built-in chart helpers are too plain and the interaction (linked brushing, selection-driven filters across charts) is the point of the page. Pure altair pages in `streamlit/pages/` are fine — they are still launched via `streamlit run streamlit/index.py`.
- **If the data is too large for live computation** (rule of thumb: > 1M rows, or > 200MB, or any chart that would take more than ~2s to render every interaction), switch to a "viewer" mode: pre-render variants with `plot_gen.py` into `plots/<topic>/`, and have the streamlit page show those PNGs with simple controls (a dropdown that picks which pre-rendered figure to display). State this fallback explicitly in `info/context.md` so a future agent knows why the page is image-based.

## How to build

Adapt `assets/scaffolding/streamlit/index.py` as the landing page. Each new "exploration topic" goes in `streamlit/pages/<n>_<topic>.py` so streamlit picks it up automatically in the sidebar. Wrap every data load in `@st.cache_data` with a hash key derived from the file path + mtime so reruns are fast. Run via `bash visualizations/interactive_page.sh` (which is just `streamlit run visualizations/streamlit/index.py` with the right env activation).

## Default informative content (the "captions are not optional" rule, applied to dashboards)

A streamlit page should never be a wall of widgets and chart with zero context. Apply Rule 4 from `references/figure-design-guidelines.md` (Rougier et al. 2014) but in dashboard form — bake in **enough default info that a stranger could open the page and understand what they're looking at**, without cluttering it:

- A short page title and one-line subtitle (`st.title` / `st.caption`) telling the reader what this page is for.
- Tooltips on widgets via the `help=` parameter of `st.selectbox` / `st.slider` / `st.multiselect` — explain what each filter does and what units it's in.
- Tooltips on chart points: prefer `st.altair_chart` with explicit `tooltip=[...]` listing all useful columns, or use `hover_data` if you fall back to plotly. For native streamlit charts, the default hover is usually OK.
- One collapsed `st.expander("Notes / data source")` with where the data came from, the cleaning strategies applied, and any known caveats (lifted from `info/context.md`).

Keep it discoverable, not in-your-face. Tooltips and expanders are perfect because they're zero-cost when the user doesn't need them.

## What to bake in (project-time)

**Bake project-specific behavior directly into the page files** — the filters, color choices, default selections, axis labels, and chart specs that the user accepted should be hardcoded in the `.py` so the user can `bash interactive_page.sh` later and land on the same dashboard. Don't depend on URL params or environment variables for the canonical setup.

If `PROJECT_PALETTE` is defined in `plot_gen.py`, import it and use it for the streamlit charts too — consistency between static and interactive views matters.

After adding a page, append a line to `info/context.md`: which page, what it filters, which CSV it reads.

## Iterating on a page from a screenshot

If the user sends a screenshot of the running streamlit page and asks for a fix ("the filter sidebar is too wide", "the chart is squashed when I select two sites", "tooltip text is unreadable"):

- **If you can see images:** look at the actual screenshot first, then interpret the feedback. Layout problems are easier to diagnose visually.
- **If you can't see images:** say so plainly, ask the user to describe the problem in component / property terms ("which widget? what value?"), or offer to exit and come back with a vision-capable model.
- Never guess. A frank "I can't see this — describe it" is the right response, not a hallucinated fix.

After applying the change, ask the user to reload the page and confirm before moving on.

## Trim before delivering

Per the SKILL.md trim rule: drop the multi-dataset selector in `index.py` if the project has a single dataset; drop the streamlit warm-up scaffolding (e.g. the schema expander) if the user doesn't want it; remove unused imports. Keep concise comments on the surviving steps.

## References

For more streamlit and altair patterns (caching, multi-page apps, altair selections, large-data fallbacks), see `../../references/streamlit-patterns.md`.

For figure-design guidelines that apply to dashboards too (palette categories, chartjunk, honest encoding, audience awareness), see `../../references/figure-design-guidelines.md` — Rougier et al. 2014's ten rules. Treat as guidelines, not gates.
