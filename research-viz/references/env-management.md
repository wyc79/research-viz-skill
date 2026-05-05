# Python environment management

The skill's policy is **always ask before installing**. Detect what's missing, present a small menu, and let the user pick. Concrete commands and the pieces you'd put in the shell wrappers below.

## Detection

```bash
which python3 && python3 --version
python3 -c "import sys; print(sys.executable, sys.prefix)"
echo "VIRTUAL_ENV=${VIRTUAL_ENV:-(none)}"
ls -d ./.venv 2>/dev/null || true
ls -d ./visualizations/.venv 2>/dev/null || true
```

### Importability + version check

**Always check versions, not just presence.** Several APIs in our stack changed in non-obvious ways across releases (see "Version-sensitive APIs" below), and "the import works" doesn't mean "the kwarg I'm about to use exists." Run this before generating or editing any plot/streamlit code:

```bash
python3 - <<'PY'
import importlib, importlib.metadata as md
mods = ['pandas','numpy','matplotlib','seaborn','streamlit','altair',
        'openpyxl','scipy','statannotations','pingouin']
for m in mods:
    spec = importlib.util.find_spec(m)
    if spec is None:
        print(f"{m:<16} MISSING")
        continue
    try:
        v = md.version(m)
    except md.PackageNotFoundError:
        v = "?"
    print(f"{m:<16} {v}")
PY
```

Record the versions you saw in `info/context.md`'s **Python env** line (one short line: `streamlit 1.28.0, altair 5.1.1, statannotations 0.6.0, …`) so a future agent knows what surface they're targeting.

Only install the modules required by the subskill the user is invoking. Minimum sets:

- **parser**: `pandas`, `numpy`, `openpyxl`
- **plot_gen**: `pandas`, `numpy`, `matplotlib`, `seaborn` (+ `statannotations` only if a recipe overlays a significance bracket)
- **interactive**: `pandas`, `streamlit` (+ `altair` only if altair charts will be used)
- **significance_test**: `pandas`, `numpy`, `scipy` (+ `pingouin` if you want one-call ANOVA/post-hoc/effect sizes)

## Version-sensitive APIs — known gotchas

Before reaching for any of the kwargs / functions below, check the installed version (the snippet above prints it). When the user's version is older than the cutoff, use the **legacy form** instead — silently falling back is fine, but **do not write code that requires a newer version than what's installed**. If the user truly needs the newer surface, surface that to them and let them decide whether to upgrade rather than wedging the workspace.

| Package | API | Cutoff | Legacy form (works on older) | Modern form |
|---|---|---|---|---|
| streamlit | `st.image(use_container_width=...)` | 1.32 | `st.image(use_column_width=True)` | `st.image(width="stretch")` (1.40+) |
| streamlit | `st.dataframe(use_container_width=...)` | ~1.10 | (always available) | `width="stretch"` after 2025-12-31 |
| streamlit | `st.cache_data` | 1.18 | `@st.cache` (with `allow_output_mutation=True` on DataFrames) | `@st.cache_data` |
| streamlit | `st.scatter_chart`, `st.bar_chart(color=…)` | 1.27 | manually map to altair | native `color=` kwarg |
| streamlit | `st.column_config` | 1.23 | format the DataFrame yourself before display | `st.column_config.NumberColumn(...)` |
| altair | `alt.selection_interval()` / `alt.selection_point()` | 5.0 | `alt.selection(type="interval"|"point")` | the new top-level helpers |
| altair | `.add_params(...)` | 5.0 | `.add_selection(...)` | `.add_params(...)` |
| seaborn | `errorbar=("ci", 95)` on relplot/lineplot/etc. | 0.12 | `ci=95` | `errorbar=("ci", 95)` (the `ci` kwarg is removed in 0.14) |
| seaborn | `hue` without `legend=` on catplot family | 0.13 | seaborn auto-legend | must pass `legend=False` explicitly to suppress |
| matplotlib | `plt.cm.get_cmap('Blues')` | 3.9 (removed) | `plt.cm.get_cmap('Blues')` | `mpl.colormaps['Blues']` |
| matplotlib | `Axes.set_xticklabels` w/ rotation+ha kwargs | 3.5 | `ax.set_xticklabels(..., rotation=30, ha='right')` | same; just don't combine with `Axes.tick_params(labelrotation=...)` |
| pandas | `DataFrame.append` | 2.0 (removed) | use `pd.concat([df, other], ignore_index=True)` | `pd.concat(...)` |
| pandas | `DataFrame.applymap` | 2.1 (deprecated) | `df.applymap(f)` | `df.map(f)` |
| pandas | groupby `apply` `include_groups=False` | 2.2 | omit (default behaviour) | pass `include_groups=False` to silence the FutureWarning |
| statannotations | `Annotator.set_pvalues_and_annotate` | 0.5 | manual bracket via matplotlib | the high-level Annotator API |
| statannotations | `configure(test=None, ...)` (pre-computed p) | 0.6 | run `configure(test='t-test_welch')` and let it recompute | `configure(test=None)` + `set_pvalues_and_annotate` |
| scipy | `scipy.stats.ttest_ind(..., alternative=...)` | 1.6 | only two-sided is available; do the one-sided p adjustment yourself | the `alternative` kwarg |
| scipy | `scipy.stats.shapiro` returns named tuple | 1.9 | `stat, p = stats.shapiro(x)` (positional unpack works on both) | `.statistic` / `.pvalue` attrs |

The list isn't exhaustive — when you reach for a kwarg that "should exist", and the user's version is older than what you're used to, do a one-line `python3 -c "import X; print(X.__version__)"` *first* and consult the package's CHANGELOG before assuming the kwarg is valid.

### Pattern: write the version-aware branch, don't crash

```python
# Use modern API when available, fall back gracefully otherwise.
import streamlit as st
from packaging.version import Version
import importlib.metadata as md

_st_v = Version(md.version("streamlit"))
_image_kwargs = {"use_container_width": True} if _st_v >= Version("1.32") else {"use_column_width": True}
st.image(str(fig_path), **_image_kwargs)
```

Use this only when the gotcha is genuinely two-sided (older AND newer versions are both in scope). For "I just want this to run on the user's installed version," it's simpler — write the legacy form and move on.

## The four options to offer the user

### 1. Install into the current env

```bash
python3 -m pip install pandas numpy matplotlib seaborn openpyxl
```

Append `streamlit altair` for the interactive subskill. Use `--user` if you don't have permission to write to the system site-packages and there's no venv active.

### 2. Create a venv at `visualizations/.venv` and install there (recommended for reproducibility)

```bash
python3 -m venv visualizations/.venv
source visualizations/.venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install pandas numpy matplotlib seaborn openpyxl streamlit altair
```

The bundled `parse_input.sh` / `generate_plot.sh` / `interactive_page.sh` already contain a snippet that activates `visualizations/.venv` automatically if it exists:

```bash
if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    source "${VIZ_DIR}/.venv/bin/activate"
fi
```

So once the venv is created and populated, the `.sh` wrappers Just Work.

### 3. Create a fresh conda env

```bash
conda create -n research-viz python=3.11 -y
conda activate research-viz
python -m pip install pandas numpy matplotlib seaborn openpyxl streamlit altair
```

If the user goes this route, the shell wrappers won't auto-activate the conda env (we'd need to know the env name). Update the wrappers to do:

```bash
# Insert near the top of each .sh wrapper
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate <env-name>
```

Or document in `info/how_to_use.md` that the user must `conda activate <env-name>` themselves before running the wrappers.

### 4. Skip — user installs themselves

Pause and wait for the user to confirm before retrying. Do not silently fall back to a different option.

## After installing

After installing, **rerun the importability check** to confirm everything is actually importable in the env you'll execute against. Then write a one-line entry under "Python env" in `info/context.md` so future agents know which env to activate.

## Pinning

For reproducibility, after a successful install, generate a freeze:

```bash
python -m pip freeze > visualizations/requirements.txt
```

Useful when sharing the workspace.
