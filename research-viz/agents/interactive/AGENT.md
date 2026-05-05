# interactive subskill

Build a streamlit app (with optional altair charts) under `streamlit/`, falling back to pre-rendered images for very large data.

Use when the user wants exploration rather than a fixed figure: "let me filter by …", "make a dashboard", "I want to brush / zoom / drill in", "show me a streamlit app".

Read this together with `../../SKILL.md` for the top-level rules.

---

## Before you build

If `visualizations/info/style_guide.md` exists, read it first and inherit the palette / typography / figure sizes from there. The streamlit pages should look like the static plots — same colors, same theme. Also check the guide's "Per-plot / per-page overrides" section: if the page name (e.g. `pages/2_species_explorer.py`) has an entry, honor it on top of the project-wide style.

The guide is a *guide, not a strict standard* — it drives new pages and any page the user asks you to update. You don't need to retrofit old pages. If the user requests a styling change during this run, record it in `style_guide.md` (project-wide or page-specific, as appropriate) so future sessions inherit it.

## Decision rule: streamlit vs. altair vs. fall-back-to-plot_gen

- **Default** is streamlit (`streamlit/index.py` + `streamlit/pages/<topic>.py`) with native streamlit widgets for filtering and `st.altair_chart(...)` for charts that benefit from altair's interactivity (selection, brushing, linked views).
- **Add altair** specifically when streamlit's built-in chart helpers are too plain and the interaction (linked brushing, selection-driven filters across charts) is the point of the page. Pure altair pages in `streamlit/pages/` are fine — they are still launched via `streamlit run streamlit/index.py`.
- **If the data is too large for live computation** (rule of thumb: > 1M rows, or > 200MB, or any chart that would take more than ~2s to render every interaction), switch to a "viewer" mode: pre-render variants with `plot_gen.py` into `plots/<topic>/`, and have the streamlit page show those PNGs with simple controls (a dropdown that picks which pre-rendered figure to display). State this fallback explicitly in `info/context.md` so a future agent knows why the page is image-based.

## How to build

Adapt `assets/scaffolding/streamlit/index.py` as the landing page. Each new "exploration topic" goes in `streamlit/pages/<n>_<topic>.py` so streamlit picks it up automatically in the sidebar. Wrap every data load in `@st.cache_data` with a hash key derived from the file path + mtime so reruns are fast. Run via `bash visualizations/interactive_page.sh` (which is just `streamlit run visualizations/streamlit/index.py` with the right env activation).

## What to bake in (project-time)

**Bake project-specific behavior directly into the page files** — the filters, color choices, default selections, axis labels, and chart specs that the user accepted should be hardcoded in the `.py` so the user can `bash interactive_page.sh` later and land on the same dashboard. Don't depend on URL params or environment variables for the canonical setup.

If `PROJECT_PALETTE` is defined in `plot_gen.py`, import it and use it for the streamlit charts too — consistency between static and interactive views matters.

After adding a page, append a line to `info/context.md`: which page, what it filters, which CSV it reads.

## Trim before delivering

Per the SKILL.md trim rule: drop the multi-dataset selector in `index.py` if the project has a single dataset; drop the streamlit warm-up scaffolding (e.g. the schema expander) if the user doesn't want it; remove unused imports. Keep concise comments on the surviving steps.

## References

For more streamlit and altair patterns (caching, multi-page apps, altair selections, large-data fallbacks), see `../../references/streamlit-patterns.md`.

For figure-design guidelines that apply to dashboards too (palette categories, chartjunk, honest encoding, audience awareness), see `../../references/figure-design-guidelines.md` — Rougier et al. 2014's ten rules. Treat as guidelines, not gates.
